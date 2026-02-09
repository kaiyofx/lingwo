from django.core.cache import caches
from django.core.mail import send_mail
from django.core.cache import caches
from django.conf import settings
import random
import logging
from pathlib import Path
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from .models import ABSUser, AuthType
from datetime import timedelta
from django.utils import timezone
import threading

otp_cache = caches["otp_cache"]


MAX_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 10


def verify_otp(email, otp_code, auth_type: AuthType) -> bool:
    """verify the OTP code and handle lockout mechanism."""
    stored_data = otp_cache.get(email)
    if not stored_data:
        return False
    lockout_until = stored_data.get("lockout_until")
    if lockout_until and timezone.now() < lockout_until:
        return False

    stored_otp_code = stored_data.get("code")
    stored_otp_type = stored_data.get("type")
    attempts = stored_data.get("attempts", 0)

    if (stored_otp_code == otp_code) and (stored_otp_type == auth_type):
        otp_cache.delete(email)
        return True
    attempts += 1
    stored_data["attempts"] = attempts

    if attempts >= MAX_ATTEMPTS:
        lockout_time = timezone.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        stored_data["lockout_until"] = lockout_time
        stored_data["attempts"] = 0
        otp_cache.set(email, stored_data, timeout=LOCKOUT_DURATION_MINUTES * 60)

    else:
        otp_cache.set(email, stored_data)

    return False


BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

OTP_TIMEOUT = settings.OTP_TIMEOUT
REG_TOKEN_TIMEOUT = settings.REG_TOKEN_TIMEOUT


def send_otp_email_task(email: str, otp_code: int, otp_timeout: int):
    """task for sending OTP emails asynchronously."""
    subject: str = _("Ваш код для регистрации")
    message: str = (
        _("Ваш код:")
        + " " + str(otp_code)
        + _(f"\nОн действителен {otp_timeout//60} минут.")
    )
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, email_from, recipient_list)


def generate_and_send_otp(email: str, auth_type: AuthType) -> Response:
    """Генерирует, сохраняет в кэше и отправляет OTP."""

    if auth_type == AuthType.LOGIN:
        if not ABSUser.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": _("Пользователь с таким адресом электронной почты не существует.")},
                status=status.HTTP_404_NOT_FOUND,
            )
        user = ABSUser.objects.get(email__iexact=email)
        if not user.otp:
            return Response(
                {"error": _("OTP не включен для этого пользователя.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    otp_code = random.randint(100000, 999999)

    otp_cache.set(
        email, {"code": str(otp_code), "type": auth_type}, timeout=OTP_TIMEOUT
    )

    try:
        thread = threading.Thread(
            target=send_otp_email_task,
            args=(email, otp_code, OTP_TIMEOUT)
        )
        thread.start()
        return Response(
            {"message": _("Код отправлен. Пожалуйста, проверьте свою электронную почту для подтверждения.")},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(f"error: {e}")
        return Response(
            {"error": _("Внутренняя ошибка сервера. Пожалуйста, повторите попытку позже.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
