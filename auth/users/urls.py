from django.urls import path, include
from .views import (
    # RequestCodeView,
    VerifyCodeView,
    CompleteRegistrationView,
    ProfileView,
    RestoreUserView,
    RequestUsernameChangeView,
    ConfirmUsernameChangeView,
    RequestEmailChangeView,
    ConfirmEmailChangeView,
    TokenRevokeAdminView,
)
from .views import SendOTPView

urlpatterns = [
    # path(
    #     "register/request-code/",
    #     RequestCodeView.as_view(),
    #     name="register-request-code",
    # ),
    # verify otp code
    path(
        "register/verify-code/", VerifyCodeView.as_view(), name="register-verify-code"
    ),
    # complete registration
    path(
        "register/complete/",
        CompleteRegistrationView.as_view(),
        name="register-complete",
    ),
    path("otp/send/", SendOTPView.as_view(), name="send-otp"),
    # path("profile/", ProfileView.as_view(), name="user-profile"),
    path("profiles/me/", ProfileView.as_view(), name="my_profile"),
    path('accounts/', include('django.contrib.auth.urls')),
    path("profiles/<str:username>/", ProfileView.as_view(), name="user_profile_detail"),
    path('profile/restore/', RestoreUserView.as_view(), name='profile-restore'),
    path('profile/username/request/', RequestUsernameChangeView.as_view(), name='request_username_change'),
    path('profile/username/confirm/', ConfirmUsernameChangeView.as_view(), name='confirm_username_change'),
    path('profile/email/request/', RequestEmailChangeView.as_view(), name='request_email_change'),
    path('profile/email/confirm/', ConfirmEmailChangeView.as_view(), name='confirm_email_change'),
    path(
        "api/admin/revoke-tokens/<str:username>/", 
        TokenRevokeAdminView.as_view(), 
        name="admin_revoke_tokens"
    ),
]
