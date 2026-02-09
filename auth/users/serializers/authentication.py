from rest_framework.serializers import (
    Serializer,
    CharField,
    EmailField,
    ChoiceField,
    ValidationError,
)
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, Token
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import timedelta
from typing import cast
from ..models import ABSUser, AuthType
from ..otp_utils import verify_otp
from ..utils import find_user
from rest_framework.response import Response

User = get_user_model()


class OTPSendSerializer(Serializer):
    """
    OTP Serializer for requesting OTP code.
    """

    email = EmailField(
        required=False,
        max_length=ABSUser._meta.get_field("email").max_length,
        label="Email address for OTP",
    )

    username = CharField(
        required=False,
        max_length=ABSUser._meta.get_field("username").max_length,
        label="Username for OTP",
    )

    auth_type = ChoiceField(
        choices=AuthType.choices,
        default=AuthType.LOGIN,
        write_only=True,
    )

    def validate(self, attrs):
        auth_type = attrs.get("auth_type")
        email = attrs.get("email")
        username = attrs.get("username")

        if auth_type == AuthType.SIGNUP:
            # --- SIGNUP LOGIC  ---
            if not email:
                raise ValidationError(
                    {"email": _("Для регистрации требуется электронная почта.")}, code="required"
                )

            if ABSUser.objects.filter(email__iexact=email).exists():
                raise ValidationError(
                    {"email": _("Пользователь с таким адресом электронной почты уже существует.")}, code="unique"
                )
            attrs.pop("username", None)

        elif auth_type == AuthType.LOGIN:
            # --- LOGIN LOGIC ---
            if not (email or username):
                raise ValidationError(
                    _("Для входа в систему необходимо указать адрес электронной почты или имя пользователя."),
                    code="required",
                )

        else:
            raise ValidationError(
                "Недопустимый тип аутентификации.", code="invalid_auth_type"
            )

        return attrs


class OTPTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Serializer for obtaining JWT tokens with OTP or password.
    """

    user_email = EmailField(
        required=False, max_length=ABSUser._meta.get_field("email").max_length, allow_blank=True
    )
    otp_code = CharField(max_length=6, min_length=6, required=False)
    username = CharField(
        required=False, max_length=ABSUser._meta.get_field("username").max_length, allow_blank=True
    )
    password = CharField(write_only=True, required=False, allow_blank=True)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].required = False
            self.fields['username'].allow_blank = True
            
        if 'password' in self.fields:
            self.fields['password'].required = False
            self.fields['password'].allow_blank = True
            self.fields['password'].write_only = True
            
        if 'user_email' in self.fields:
            self.fields['user_email'].required = False
            self.fields['user_email'].allow_blank = True

    @classmethod
    # @audit_log_action(
    #     event_type=AuthType.LOGIN,
    #     success_msg="User successfully authenticated and tokens issued.",
    #     failure_msg="Authentication attempt failed (invalid credentials, lockout, etc.).",
    # )
    def get_token(cls, user) -> Token:
        """
        get token for user method
        """
        token = super().get_token(user)
        silq_user = cast(ABSUser, user)
        token["role"] = silq_user.role.pk
        token["email"] = silq_user.email
        token['username'] = silq_user.username
        return token

    def validate(self, attrs):
        user_email = attrs.get("user_email")
        username = attrs.get("username")
        otp_code = attrs.get("otp_code")
        password = attrs.get("password")
        user = find_user(user_email, username)

        if not isinstance(user, ABSUser) or user is None:
            if isinstance(user, Response) and user.data:
                error_message = user.data.get("error", "Неизвестная ошибка проверки.")
                raise ValidationError({"detail": error_message})
            raise ValidationError({"detail": _("Неверные учетные данные.")})

        if user.lockout_time and user.lockout_time > timezone.now():
            raise ValidationError({"detail": "Учетная запись заблокирована. Попробуйте еще раз позже."})
        if user.failed_login_attempts >= 5:
            user.lockout_time = timezone.now() + timedelta(minutes=15)
            user.save()
            raise ValidationError(
                {
                    "detail": _("Слишком много неудачных попыток входа в систему. Попробуйте позже.")
                }
            )

        authenticated_user = user
        if not user.otp:
            if not password:
                raise ValidationError(_("Для стандартного входа в систему требуется пароль."))
            authenticated_user = authenticate(
                username=user.username, password=password, user_email=user.email
            )
            if authenticated_user is None or not authenticated_user.is_active:
                raise ValidationError({"detail": _("Неверные учетные данные.")})

        # OTP
        else:
            if not verify_otp(user.email, otp_code, AuthType.LOGIN):
                raise ValidationError({"otp_code": _("Недействительный или просроченный OTP.")})

            # OTP + password
            if not user.otp_only:
                if not password:
                    raise ValidationError(
                        {
                            "password": _("Для двухфакторной аутентификации требуется пароль..")
                        }
                    )
                if not user.check_password(password):
                    raise ValidationError({"detail": _("Неверные учетные данные.")})
            authenticated_user = user
        self.user = authenticated_user

        refresh: RefreshToken = cast(RefreshToken, self.get_token(self.user))

        data = {}
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        user.failed_login_attempts = 0
        user.lockout_time = None
        user.save()
        return data
