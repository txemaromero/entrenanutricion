import hashlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

from apps.accounts import login_attempts
from apps.accounts.emails import send_email_verification_email, send_password_reset_email
from apps.accounts.models import (
    DietPreferences,
    HealthDataAccess,
    HealthInfo,
    Role,
    User,
    UserDetails,
    UserStatus,
)
from apps.accounts.selectors import has_onboarding
from apps.accounts.tokens import blacklist_all_tokens, issue_tokens
from apps.assignments.services import recompute_user_status
from apps.core.background import run_in_background
from apps.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from apps.progress.services import record_weight

PROFILE_DETAIL_FIELDS = ("goal", "physical_activity_level", "weekly_training_days")
HEALTH_ACCESS_WINDOW = timedelta(hours=1)
# At most one reset email per address in this time, however many machines ask for it.
RESET_EMAIL_COOLDOWN_SECONDS = 120


def _create_account(**fields) -> User:
    """create_user, with the same answer as the form when two requests take the same email at once.

    The serializer checks the email first, but a double submit can pass that check twice: the
    database's unique index stops the second one, which gets `email_taken` instead of a 500.
    """
    try:
        with transaction.atomic():
            return User.objects.create_user(**fields)
    except IntegrityError as exc:
        if not User.objects.filter(email__iexact=fields["email"]).exists():
            raise
        raise serializers.ValidationError(
            {
                "email": [
                    serializers.ErrorDetail("This email is already registered.", code="email_taken")
                ]
            }
        ) from exc


def register_client(*, email, password, first_name, last_name, birth_date, gender) -> User:
    """New client who accepted the terms, the privacy policy and the use of health data."""
    now = timezone.now()
    return _create_account(
        privacy_policy_version=settings.PRIVACY_POLICY_VERSION,
        privacy_accepted_at=now,
        health_consent_at=now,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        gender=gender,
        role=Role.CLIENT,
        status=UserStatus.PENDING_ONBOARDING,
        terms_accepted_at=timezone.now(),
    )


def _ensure_client(user: User) -> None:
    if user.role != Role.CLIENT:
        raise ForbiddenError("Only clients fill in the onboarding form.", code="clients_only")


@transaction.atomic
def complete_onboarding(user: User, data: dict) -> UserDetails:
    _ensure_client(user)
    # One form at a time per account: a double submit waits here and then finds the first one.
    user = User.objects.select_for_update().get(pk=user.pk)
    if user.status != UserStatus.PENDING_ONBOARDING or has_onboarding(user):
        raise ConflictError(
            "The onboarding form has already been completed.", code="onboarding_already_completed"
        )
    data = dict(data)
    diet = data.pop("diet")
    health = data.pop("health")
    details = UserDetails.objects.create(user=user, **data)
    DietPreferences.objects.create(user=user, **diet)
    HealthInfo.objects.create(user=user, **health)
    record_weight(user, details.initial_weight_kg)

    recompute_user_status(user)
    return details


def get_onboarding(user: User) -> UserDetails:
    _ensure_client(user)
    details = (
        UserDetails.objects.select_related("user__diet_preferences", "user__health_info")
        .filter(user=user)
        .first()
    )
    if details is None:
        raise NotFoundError(
            "The onboarding form has not been completed yet.", code="onboarding_not_completed"
        )
    return details


@transaction.atomic
def update_onboarding(user: User, data: dict) -> UserDetails:
    details = get_onboarding(user)
    data = dict(data)
    diet = data.pop("diet", None)
    health = data.pop("health", None)
    for field, value in data.items():
        setattr(details, field, value)
    details.save()
    for instance, values in ((user.diet_preferences, diet), (user.health_info, health)):
        if values:
            for field, value in values.items():
                setattr(instance, field, value)
            instance.save()
    return details


@transaction.atomic
def update_profile(user: User, data: dict) -> User:
    """Update names, language, current weight (new WeightRecord) and sport goals of `user`."""
    for field in ("first_name", "last_name", "language"):
        if field in data:
            setattr(user, field, data[field])
    user.save()

    detail_changes = {key: data[key] for key in PROFILE_DETAIL_FIELDS if key in data}
    if detail_changes or "current_weight_kg" in data:
        details = UserDetails.objects.filter(user=user).first()
        if details is None:
            raise ConflictError(
                "Sport information is available once the onboarding form is completed.",
                code="onboarding_not_completed",
            )
        for field, value in detail_changes.items():
            setattr(details, field, value)
        details.save()
        if "current_weight_kg" in data:
            record_weight(user, data["current_weight_kg"])
    return user


def change_password(user: User, new_password: str, remember: bool = False) -> dict[str, str]:
    """Set the new password, log out every other session and return fresh tokens."""
    user.set_password(new_password)
    user.password_changed_at = timezone.now()
    user.save(update_fields=["password", "password_changed_at", "updated_at"])
    blacklist_all_tokens(user)
    login_attempts.clear(user.email)
    return issue_tokens(user, remember=remember)


def request_password_reset(email: str, language: str) -> None:
    """Email a single-use reset link to an active account. Unknown emails are silently ignored."""
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None:
        return
    # The limit per IP does not protect a mailbox from many machines. The answer stays the same.
    digest = hashlib.sha256(user.email.lower().encode()).hexdigest()
    if not cache.add(f"reset-email-sent:{digest}", 1, timeout=RESET_EMAIL_COOLDOWN_SECONDS):
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    # Sent after answering: waiting for the mail server only for existing accounts would reveal them.
    run_in_background(send_password_reset_email, user, link, language)


def reset_password(user: User, new_password: str) -> None:
    """Set the new password (which invalidates the link) and close every open session.

    The link arrived by email, so the address is verified too.
    """
    user.set_password(new_password)
    user.password_changed_at = timezone.now()
    fields = ["password", "password_changed_at", "updated_at"]
    if user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        fields.append("email_verified_at")
    user.save(update_fields=fields)
    blacklist_all_tokens(user)
    login_attempts.clear(user.email)  # a paused account is free again with its new password


# --- Email verification (phase 12) ---------------------------------------------------------------

EMAIL_VERIFICATION_SALT = "entrenanutricion.email-verification"


def email_verification_token(user: User) -> str:
    """Signed, timestamped token naming the account and its address."""
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=EMAIL_VERIFICATION_SALT)


def send_email_verification(user: User, language: str) -> bool:
    link = f"{settings.FRONTEND_URL}/verify-email?token={email_verification_token(user)}"
    return send_email_verification_email(user, link, language)


def resend_email_verification(user: User, language: str) -> None:
    if user.email_verified_at is not None:
        raise ConflictError("The email is already verified.", code="email_already_verified")
    send_email_verification(user, language)


def verify_email(token: str) -> User:
    """Confirm the address of the token's account (again is fine: nothing changes)."""
    try:
        data = signing.loads(
            token, salt=EMAIL_VERIFICATION_SALT, max_age=settings.EMAIL_VERIFICATION_MAX_AGE
        )
    except signing.SignatureExpired as exc:
        raise DomainError("The link has expired.", code="verification_link_expired") from exc
    except signing.BadSignature as exc:
        raise DomainError("The link is not valid.", code="verification_link_invalid") from exc
    user = User.objects.filter(pk=data.get("uid"), email=data.get("email"), is_active=True).first()
    if user is None:
        raise DomainError("The link is not valid.", code="verification_link_invalid")
    if user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at", "updated_at"])
    return user


def set_profile_photo(user: User, photo) -> User:
    user.profile_photo = photo
    user.save()
    return user


def remove_profile_photo(user: User) -> User:
    user.profile_photo = None
    user.save()
    return user


# --- User management (admin) ---------------------------------------------------------------------


def create_user(*, email, password, first_name, last_name, birth_date, gender, role) -> User:
    """Clients start in pending_onboarding (they fill the form on first login); staff is active.

    The administrator typed the address, so it is not verified again.
    """
    return _create_account(
        email_verified_at=timezone.now(),
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        gender=gender,
        role=role,
    )


@transaction.atomic
def update_user(user: User, data: dict, actor: User) -> User:
    data = dict(data)
    photo = data.pop("photo", None)
    role = data.pop("role", None)
    if role is not None and role != user.role:
        if user.pk == actor.pk:
            raise ConflictError("You cannot change your own role.", code="cannot_change_own_role")
        user.role = role
        user.save(update_fields=["role", "updated_at"])
    update_profile(user, data)
    if photo is not None:
        set_profile_photo(user, photo)

    recompute_user_status(user)
    return user


@transaction.atomic
def remember_language(user: User, language: str) -> None:
    """Keep the language of the app (the emails are written in it)."""
    if language != user.language:
        user.language = language
        user.save(update_fields=["language", "updated_at"])


def record_health_data_access(staff: User, client: User) -> None:
    """Log that `staff` was shown the health data of `client`: who, whom and when (no values).

    At most one row per professional, client and hour: screens reload their data on every visit,
    and what matters is that the access happened. It does not depend on the current role of the
    account: changing it must not be a way of reading those data without leaving a trace.
    """
    record_health_data_accesses(staff, [client])


def record_health_data_accesses(staff: User, clients) -> None:
    """The same for every client a list screen showed at once, in two queries."""
    clients = {client.pk: client for client in clients if client.pk != staff.pk}
    if not clients:
        return
    since = timezone.now() - HEALTH_ACCESS_WINDOW
    logged = set(
        HealthDataAccess.objects.filter(
            client_id__in=clients, staff=staff, created_at__gte=since
        ).values_list("client_id", flat=True)
    )
    name = (staff.get_full_name() or staff.email)[:150]
    HealthDataAccess.objects.bulk_create(
        HealthDataAccess(client=client, staff=staff, staff_role=staff.role, staff_name=name)
        for pk, client in clients.items()
        if pk not in logged
    )


def deactivate_user(user: User, actor: User) -> None:
    """Logical delete: keeps the history for traceability and closes every session."""
    if user.pk == actor.pk:
        raise ConflictError("You cannot delete your own account.", code="cannot_delete_self")
    user.is_active = False
    user.status = UserStatus.INACTIVE
    user.deactivated_at = timezone.now()
    user.save(update_fields=["is_active", "status", "deactivated_at", "updated_at"])
    blacklist_all_tokens(user)


# --- Data protection (GDPR) ------------------------------------------------------------------------


def record_consent(user: User, health_data: bool) -> User:
    """Accept the current privacy policy; clients must also consent to the use of health data."""
    if user.role == Role.CLIENT and not health_data and user.health_consent_at is None:
        raise DomainError(
            "Clients must consent to the use of their health data.",
            code="health_consent_required",
        )
    now = timezone.now()
    user.privacy_policy_version = settings.PRIVACY_POLICY_VERSION
    user.privacy_accepted_at = now
    fields = ["privacy_policy_version", "privacy_accepted_at", "updated_at"]
    if health_data:
        user.health_consent_at = now
        fields.append("health_consent_at")
    user.save(update_fields=fields)
    return user


@transaction.atomic
def delete_own_account(user: User) -> None:
    """Right to erasure: the client's account and every personal record go (database cascade)."""
    if user.role != Role.CLIENT:
        raise ForbiddenError(
            "Staff accounts are deleted by an administrator.", code="staff_account_managed"
        )
    blacklist_all_tokens(user)
    user.delete()


def purge_inactive_accounts(days: int, now=None) -> int:
    """Delete for good the accounts deactivated more than `days` days ago."""
    cutoff = (now or timezone.now()) - timedelta(days=days)
    expired = User.objects.filter(is_active=False, deactivated_at__lt=cutoff)
    count = expired.count()
    for user in expired:
        blacklist_all_tokens(user)
        user.delete()  # one by one, so stored files are removed by the signals
    return count
