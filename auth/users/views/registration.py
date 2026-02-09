from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.translation import gettext_lazy as _
from django.core.cache import caches
from ..serializers import VerifyCodeSerializer, CompleteRegistrationSerializer
from ..otp_utils import verify_otp, REG_TOKEN_TIMEOUT
from ..models import AuthType, ABSUser
import uuid
from typing import cast


class VerifyCodeView(APIView):
    """
    Шаг 2: Проверяет OTP. Если код верен, выдает временный токен регистрации.
    """

    permission_classes = [AllowAny]
    serializer_class = VerifyCodeSerializer
    
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        if not isinstance(validated_data, dict):
            raise TypeError(
                "Expected serializer.validated_data or validated_data to be a dictionary."
            )

        otp_received = validated_data["otp"]
        email = validated_data["email"]

        otp_cache = caches["otp_cache"]
        reg_token_cache = caches["reg_token_cache"]

        otp_stored = otp_cache.get(email)

        if not otp_stored:
            return Response(
                {"error": _("Code expired or not found. Please request a new code.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verify = verify_otp(email, otp_received, AuthType.SIGNUP)
        if not verify:
            return Response(
                {"error": _("Invalid code.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reg_token = str(uuid.uuid4())

        reg_token_cache.set(reg_token, email, timeout=REG_TOKEN_TIMEOUT)

        return Response(
            {
                "message": _("Code verified."),
                "registration_token": reg_token,
                "expires_in_seconds": REG_TOKEN_TIMEOUT,
            },
            status=status.HTTP_200_OK,
        )


class CompleteRegistrationView(APIView):
    """
    3 STEP: Complete registration with token.
    """

    permission_classes = [AllowAny]
    serializer_class = CompleteRegistrationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # reg_token = validated_data.pop('registration_token')
        # password = validated_data.pop('password')
        # username = validated_data.pop('username')

        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")
        reg_token = validated_data.pop("registration_token")
        password = validated_data.pop("password")
        username = validated_data.pop("username")

        reg_token_cache = caches["reg_token_cache"]

        email = reg_token_cache.get(reg_token)

        if not email:
            return Response(
                {"error": _("Token expired or not found. Please request a new code.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = ABSUser.objects.create_user(
                username=username, email=email, password=password, **validated_data
            )
            reg_token_cache.delete(reg_token)

            return Response(
                {"message": _("Registration completed!"), "user_id": user.username},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": _("Error during registration:") + str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
