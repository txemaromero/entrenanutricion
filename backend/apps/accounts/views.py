import contextlib

import django_filters
from django.contrib.auth import authenticate
from django.db.models import Prefetch
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers, status, viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.accounts import login_attempts, services
from apps.accounts.cookies import clear_refresh_cookie, refresh_from_request, set_refresh_cookie
from apps.accounts.emails import language_from_header
from apps.accounts.export import export_user_data
from apps.accounts.models import HealthDataAccess, Role, User
from apps.accounts.serializers import (
    AccessTokenSerializer,
    AccountDeleteSerializer,
    ConsentSerializer,
    EmailExistsQuerySerializer,
    EmailVerifiedSerializer,
    HealthDataAccessSerializer,
    LoginSerializer,
    MeSerializer,
    OnboardingSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PhotoUploadSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
    email_is_taken,
)
from apps.accounts.tokens import (
    REMEMBER_CLAIM,
    SessionRefreshToken,
    SessionTokenRefreshSerializer,
    issue_tokens,
)
from apps.core.exceptions import DomainError
from apps.core.permissions import IsAdmin, IsClient, StaffReadAdminWrite
from apps.nutrition.models import UserNutritionPlan
from apps.training.models import UserTrainingPlan

AuthResponseSerializer = inline_serializer(
    "AuthResponse",
    fields={
        "access": serializers.CharField(),
        "user": MeSerializer(),
    },
)


def me_payload(user: User, request) -> dict:
    user = User.objects.select_related("details").get(pk=user.pk)
    return MeSerializer(user, context={"request": request}).data


def session_response(tokens: dict, user: dict | None = None, status_code: int = 200) -> Response:
    """Access token (and user) in the body, refresh token in the httpOnly cookie."""
    body = {"access": tokens["access"]}
    if user is not None:
        body["user"] = user
    response = Response(body, status=status_code)
    set_refresh_cookie(response, tokens["refresh"])
    return response


class ScopedThrottleMixin:
    throttle_classes = [ScopedRateThrottle]


# --- Auth ----------------------------------------------------------------------------------------


class RegisterView(ScopedThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "register"

    @extend_schema(request=RegisterSerializer, responses={201: AuthResponseSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("terms_accepted")
        data.pop("health_data_consent")
        user = services.register_client(**data)
        language = language_from_header(request.headers.get("Accept-Language"))
        services.remember_language(user, language)
        services.send_email_verification(user, language)
        return session_response(issue_tokens(user), me_payload(user, request), 201)


class LoginView(ScopedThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses={200: AuthResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        ip = BaseThrottle().get_ident(request)
        login_attempts.ensure_allowed(email, ip)
        user = authenticate(request, email=email, password=serializer.validated_data["password"])
        if user is None:
            login_attempts.record_failure(email, ip)
            raise DomainError(
                "The email or password is incorrect.",
                code="invalid_credentials",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        login_attempts.clear(email)
        services.remember_language(
            user, language_from_header(request.headers.get("Accept-Language"))
        )
        tokens = issue_tokens(user, remember=serializer.validated_data["remember_me"])
        return session_response(tokens, me_payload(user, request))


class RefreshView(ScopedThrottleMixin, APIView):
    """New access token from the refresh cookie, which is rotated (the old one is blacklisted)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "session"

    def get_authenticate_header(self, request):
        # Keeps 401 (not 403) for a missing or invalid session.
        return 'Bearer realm="api"'

    @extend_schema(request=None, responses=AccessTokenSerializer)
    def post(self, request):
        token = refresh_from_request(request)
        if not token:
            raise NotAuthenticated("There is no session to refresh.")
        serializer = SessionTokenRefreshSerializer(data={"refresh": token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        return session_response(serializer.validated_data)


class LogoutView(ScopedThrottleMixin, APIView):
    """Blacklist the session's refresh token and delete the cookie (always 204)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "session"

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        token = refresh_from_request(request)
        if token:
            # An expired or already blacklisted token means the session is over anyway.
            with contextlib.suppress(TokenError):
                SessionRefreshToken(token).blacklist()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class EmailExistsView(ScopedThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "email_exists"

    @extend_schema(
        parameters=[OpenApiParameter("email", str, required=True)],
        responses=inline_serializer("EmailExists", fields={"exists": serializers.BooleanField()}),
    )
    def get(self, request):
        query = EmailExistsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response({"exists": email_is_taken(query.validated_data["email"])})


class PasswordResetRequestView(ScopedThrottleMixin, APIView):
    """Always 204, whether or not the email exists, so accounts cannot be discovered."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetRequestSerializer, responses={204: None})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(
            serializer.validated_data["email"],
            language_from_header(request.headers.get("Accept-Language")),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(ScopedThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetConfirmSerializer, responses={204: None})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(
            serializer.validated_data["user"], serializer.validated_data["new_password"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailView(ScopedThrottleMixin, APIView):
    """Open link of the verification email (works signed in or not)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "email_verification"

    @extend_schema(request=VerifyEmailSerializer, responses=EmailVerifiedSerializer)
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.verify_email(serializer.validated_data["token"])
        return Response({"email_verified": True})


class ResendEmailVerificationView(ScopedThrottleMixin, APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "email_verification_resend"

    @extend_schema(request=None, responses={202: None})
    def post(self, request):
        services.resend_email_verification(
            request.user, language_from_header(request.headers.get("Accept-Language"))
        )
        return Response(status=status.HTTP_202_ACCEPTED)


# --- Current user --------------------------------------------------------------------------------


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(me_payload(request.user, request))


class MeConsentView(APIView):
    """Accept the current privacy policy (and, for clients, the use of health data)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ConsentSerializer, responses=MeSerializer)
    def post(self, request):
        serializer = ConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.record_consent(request.user, serializer.validated_data["health_data"])
        return Response(me_payload(request.user, request))


class MeExportView(ScopedThrottleMixin, APIView):
    """Download every personal record of the user (GDPR access and portability)."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "data_export"

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        response = Response(export_user_data(request.user, request))
        stamp = timezone.localdate().strftime("%Y%m%d")
        response["Content-Disposition"] = (
            f'attachment; filename="entrenanutricion-datos-{stamp}.json"'
        )
        return response


class MeAccountView(ScopedThrottleMixin, APIView):
    """Right to erasure: a client deletes the account and all its data (password required)."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "password"

    @extend_schema(request=AccountDeleteSerializer, responses={204: None})
    def delete(self, request):
        serializer = AccountDeleteSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        services.delete_own_account(request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ProfileUpdateSerializer, responses=MeSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_profile(request.user, serializer.validated_data)
        return Response(me_payload(request.user, request))


class MePasswordView(ScopedThrottleMixin, APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "password"

    @extend_schema(request=PasswordChangeSerializer, responses=AccessTokenSerializer)
    def put(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        # The access token carries the "remember" claim of the session: keep it.
        remember = bool(request.auth and request.auth.get(REMEMBER_CLAIM))
        tokens = services.change_password(
            request.user, serializer.validated_data["new_password"], remember=remember
        )
        return session_response(tokens)


class MePhotoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request={"multipart/form-data": PhotoUploadSerializer}, responses=MeSerializer)
    def put(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.set_profile_photo(request.user, serializer.validated_data["photo"])
        return Response(me_payload(request.user, request))

    @extend_schema(responses=MeSerializer)
    def delete(self, request):
        services.remove_profile_photo(request.user)
        return Response(me_payload(request.user, request))


class OnboardingView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=OnboardingSerializer)
    def get(self, request):
        return Response(OnboardingSerializer(services.get_onboarding(request.user)).data)

    @extend_schema(request=OnboardingSerializer, responses={201: OnboardingSerializer})
    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        details = services.complete_onboarding(request.user, serializer.validated_data)
        return Response(OnboardingSerializer(details).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=OnboardingSerializer, responses=OnboardingSerializer)
    def put(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        details = services.update_onboarding(request.user, serializer.validated_data)
        return Response(OnboardingSerializer(details).data)


# --- User management -----------------------------------------------------------------------------


class UserFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=Role.choices)

    class Meta:
        model = User
        fields = ["role"]


def with_current_plans(queryset):
    """Prefetch the current training/nutrition assignments as `current_training/_nutrition`."""
    return queryset.prefetch_related(
        Prefetch(
            "training_plans",
            queryset=UserTrainingPlan.objects.filter(is_current=True).select_related("plan"),
            to_attr="current_training",
        ),
        Prefetch(
            "nutrition_plans",
            queryset=UserNutritionPlan.objects.filter(is_current=True).select_related("plan"),
            to_attr="current_nutrition",
        ),
    )


class UserViewSet(viewsets.ModelViewSet):
    """Trainers and nutritionists read the active clients; admins read and manage every user."""

    permission_classes = [StaffReadAdminWrite]
    filterset_class = UserFilter
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "date_joined"]
    ordering = ["last_name", "first_name", "id"]

    def get_queryset(self):
        queryset = with_current_plans(User.objects.filter(is_active=True))
        # Colleagues' personal data is not needed to prepare plans (a 404, like anything foreign).
        if getattr(self.request.user, "role", None) != Role.ADMIN:
            queryset = queryset.filter(role=Role.CLIENT)
        if self.action != "list":
            queryset = queryset.select_related(
                "details", "diet_preferences", "health_info"
            ).prefetch_related("weight_records")
        return queryset

    def get_serializer_class(self):
        return UserListSerializer if self.action == "list" else UserDetailSerializer

    def _detail_response(self, user, status_code=status.HTTP_200_OK):
        return self._show(self.get_queryset().get(pk=user.pk), status_code)

    def _show(self, user, status_code=status.HTTP_200_OK):
        """The full profile; showing a client's health answers is logged (who, whom, when)."""
        data = self.get_serializer(user).data
        if data.get("onboarding") is not None:
            services.record_health_data_access(self.request.user, user)
        return Response(data, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        return self._show(self.get_object())

    @extend_schema(request=UserCreateSerializer, responses={201: UserDetailSerializer})
    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(**serializer.validated_data)
        return self._detail_response(user, status.HTTP_201_CREATED)

    @extend_schema(request=UserUpdateSerializer, responses=UserDetailSerializer)
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_user(user, serializer.validated_data, actor=request.user)
        return self._detail_response(user)

    @extend_schema(request=UserUpdateSerializer, responses=UserDetailSerializer)
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        services.deactivate_user(instance, actor=self.request.user)


class HealthDataAccessListView(generics.ListAPIView):
    """Admins: who of the team was shown a client's health answers, and when (newest first)."""

    permission_classes = [IsAdmin]
    serializer_class = HealthDataAccessSerializer
    filter_backends = []  # newest first, paginated: nothing to search nor sort

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # OpenAPI schema generation
            return HealthDataAccess.objects.none()
        # Deactivated accounts too: the log is kept until the account is deleted for good.
        client = generics.get_object_or_404(User, pk=self.kwargs["pk"])
        return client.health_data_accesses.all()
