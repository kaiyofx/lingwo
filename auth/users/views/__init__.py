from .registration import VerifyCodeView, CompleteRegistrationView
from .authentication import OTPTokenObtainPairView, SendOTPView, LogoutView
from .profile import ProfileView
from .recovery import RestoreUserView
from .change_specific_fields import RequestUsernameChangeView, ConfirmUsernameChangeView, RequestEmailChangeView, ConfirmEmailChangeView
from .admin_view import TokenRevokeAdminView
from .well_know import JwksView