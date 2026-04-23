from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import NotFound
from ..serializers import OTPTokenObtainSerializer, OTPSendSerializer, TelegramAuthSerializer
from ..models import ABSUser, AuthType, UserRoles
from ..otp_utils import generate_and_send_otp
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated
import hashlib
import hmac
import logging


logger = logging.getLogger(__name__)


def _build_data_check_string(validated_data: dict) -> str:
    lines: list[str] = []
    for key, value in sorted(validated_data.items()):
        if key == "hash" or value in (None, ""):
            continue
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _verify_telegram_signature(validated_data: dict) -> bool:
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    data_check_string = _build_data_check_string(validated_data)
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_hash, str(validated_data["hash"]))


def _unique_username(base: str) -> str:
    normalized = (base or "telegram_user").strip().lower().replace(" ", "_")
    candidate = normalized[:40] or "telegram_user"
    if not ABSUser.objects.filter(username__iexact=candidate).exists():
        return candidate

    suffix = 1
    while True:
        suffix_text = f"_{suffix}"
        truncated_base = candidate[: 40 - len(suffix_text)]
        next_candidate = f"{truncated_base}{suffix_text}"
        if not ABSUser.objects.filter(username__iexact=next_candidate).exists():
            return next_candidate
        suffix += 1


def _unique_email(telegram_id: int) -> str:
    candidate = f"tg_{telegram_id}@telegram.local"
    if not ABSUser.objects.filter(email__iexact=candidate).exists():
        return candidate

    suffix = 1
    while True:
        next_candidate = f"tg_{telegram_id}_{suffix}@telegram.local"
        if not ABSUser.objects.filter(email__iexact=next_candidate).exists():
            return next_candidate
        suffix += 1


class OTPTokenObtainPairView(TokenObtainPairView):
    serializer_class = OTPTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = OTPSendSerializer

    @staticmethod
    def generate_and_send_otp(email: str, auth_type: AuthType) -> Response:
        if not isinstance(email, str):
            raise TypeError("Expected email to be a string.")
        return generate_and_send_otp(email, auth_type)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")
        email = validated_data.get("email")
        username = validated_data.get("username")
        auth_type: AuthType = validated_data["auth_type"]
        target_email = email

        if auth_type == AuthType.LOGIN:
            # --- LOGIN ---
            query = Q()
            if email:
                query |= Q(email__iexact=email)
            if username:
                query |= Q(username_iexact=username)

            try:
                user = ABSUser.objects.get(query)
            except ABSUser.DoesNotExist:
                raise NotFound(detail="User with these credentials does not exist.")
            target_email = user.email
        if not target_email:
            raise Exception("Target email is missing after validation.")

        return self.generate_and_send_otp(target_email, auth_type)


class LogoutView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated) 

    def post(self, request, *args, **kwargs):
        """
        Принимает refresh token в теле запроса и заносит его в черный список.
        """
        try:
            refresh_token = request.data["refresh"] 

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

        except KeyError:
            return Response(
                {"detail": "Refresh token must be provided in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An unexpected error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TelegramTokenObtainView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TelegramAuthSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not _verify_telegram_signature(validated_data):
            return Response(
                {"detail": "Invalid Telegram signature."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        telegram_id = int(validated_data["id"])
        telegram_username = str(validated_data.get("username") or "")
        user = ABSUser.objects.filter(telegram_id=telegram_id).first()

        if user is None:
            username_hint = telegram_username or f"tg_{telegram_id}"
            user = ABSUser.objects.create(
                username=_unique_username(username_hint),
                email=_unique_email(telegram_id),
                role_id=UserRoles.CLIENT,
                telegram_id=telegram_id,
                telegram_username=telegram_username or None,
                is_active=True,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
        else:
            if telegram_username and user.telegram_username != telegram_username:
                user.telegram_username = telegram_username
                user.save(update_fields=["telegram_username"])

        if not user.is_active:
            return Response(
                {"detail": "User account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh_token = OTPTokenObtainSerializer.get_token(user)
        return Response(
            {
                "refresh": str(refresh_token),
                "access": str(refresh_token.access_token),
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )