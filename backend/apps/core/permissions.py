"""Role-based DRF permission classes. Every API view declares one of these explicitly."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import STAFF_ROLES, Role


def user_role(request) -> str | None:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    return user.role


class HasRole(BasePermission):
    roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        return user_role(request) in self.roles


class IsClient(HasRole):
    roles = (Role.CLIENT,)


class IsAdmin(HasRole):
    roles = (Role.ADMIN,)


class IsTrainerOrAdmin(HasRole):
    roles = (Role.TRAINER, Role.ADMIN)


class IsNutritionistOrAdmin(HasRole):
    roles = (Role.NUTRITIONIST, Role.ADMIN)


class IsStaff(HasRole):
    roles = STAFF_ROLES


class ReadStaffWrite(BasePermission):
    """Any staff member can read; only `write_roles` can modify."""

    write_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        role = user_role(request)
        if request.method in SAFE_METHODS:
            return role in STAFF_ROLES
        return role in self.write_roles


class AuthenticatedReadNutritionistWrite(BasePermission):
    """Food library: every signed-in user (clients too) reads it; nutritionists and admins edit."""

    def has_permission(self, request, view) -> bool:
        role = user_role(request)
        if request.method in SAFE_METHODS:
            return role is not None
        return role in (Role.NUTRITIONIST, Role.ADMIN)


class StaffReadTrainerWrite(ReadStaffWrite):
    write_roles = (Role.TRAINER, Role.ADMIN)


class StaffReadNutritionistWrite(ReadStaffWrite):
    write_roles = (Role.NUTRITIONIST, Role.ADMIN)


class StaffReadAdminWrite(ReadStaffWrite):
    write_roles = (Role.ADMIN,)


class IsOwner(BasePermission):
    """Object-level: the object belongs to the requesting user (`obj.user`)."""

    def has_object_permission(self, request, view, obj) -> bool:
        return getattr(obj, "user_id", None) == request.user.id
