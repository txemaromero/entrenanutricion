from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts import views

router = DefaultRouter(trailing_slash=False)
router.register("users", views.UserViewSet, basename="user")

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="auth-register"),
    path("auth/login", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/email-exists", views.EmailExistsView.as_view(), name="auth-email-exists"),
    path(
        "auth/password-reset",
        views.PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password-reset/confirm",
        views.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/verify-email", views.VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "me/verify-email/resend",
        views.ResendEmailVerificationView.as_view(),
        name="me-verify-email-resend",
    ),
    path("me", views.MeView.as_view(), name="me"),
    path("me/profile", views.MeProfileView.as_view(), name="me-profile"),
    path("me/password", views.MePasswordView.as_view(), name="me-password"),
    path("me/photo", views.MePhotoView.as_view(), name="me-photo"),
    path("me/onboarding", views.OnboardingView.as_view(), name="me-onboarding"),
    path("me/consent", views.MeConsentView.as_view(), name="me-consent"),
    path("me/export", views.MeExportView.as_view(), name="me-export"),
    path("me/account", views.MeAccountView.as_view(), name="me-account"),
    path(
        "users/<int:pk>/health-data-accesses",
        views.HealthDataAccessListView.as_view(),
        name="user-health-data-accesses",
    ),
    *router.urls,
]
