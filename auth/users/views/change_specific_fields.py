from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from ..serializers.change_specific_fields import (
    RequestUsernameChangeSerializer,
    OTPSerializer,
    RequestEmailChangeSerializer,
)
from ..otp_utils import generate_and_send_otp, verify_otp
from django.utils import timezone
from ..models import AuthType, ABSUser


class RequestUsernameChangeView(APIView):
    """Request username change. Sends OTP to the user's current email."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RequestUsernameChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")
        new_username = validated_data["new_username"]
        user = request.user

        user.requested_username = new_username
        user.save()

        if generate_and_send_otp(user.email, AuthType.USERNAME_CHANGE):
            return Response(
                {"message": _("Code sent to your email to confirm username change.")},
                status=status.HTTP_200_OK,
            )
        else:
            user.requested_username = None
            user.save()
            return Response(
                {"error": _("Failed to send OTP. Try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConfirmUsernameChangeView(APIView):
    """Confirm username change with OTP."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")
        otp_code = validated_data["otp_code"]
        user: ABSUser = request.user

        if not user.requested_username:
            return Response(
                {"error": _("No username change request pending.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp(user.email, otp_code, AuthType.USERNAME_CHANGE):
            return Response(
                {"error": _("Invalid OTP code.")}, status=status.HTTP_400_BAD_REQUEST
            )

        new_username = user.requested_username

        user.username = new_username
        user.last_username_change = timezone.now()
        user.requested_username = None
        user.save()

        return Response(
            {"message": _("Username successfully updated to {}.").format(new_username)},
            status=status.HTTP_200_OK,
        )


class RequestEmailChangeView(APIView):
    """Request email change. Sends OTP to the new email address."""

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = RequestEmailChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")

        new_email = validated_data["new_email"]
        user: ABSUser = request.user

        user.requested_email = new_email
        user.save()

        if generate_and_send_otp(new_email, AuthType.EMAIL_CHANGE):
            return Response(
                {
                    "message": _(
                        "Verification code sent to the new email address. Please check your inbox."
                    )
                },
                status=status.HTTP_200_OK,
            )
        else:
            user.requested_email = None
            user.save()
            return Response(
                {"error": _("Failed to send OTP to the new email. Try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConfirmEmailChangeView(APIView):
    """Confirm email change with OTP."""

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")

        otp_code = validated_data["otp_code"]
        user = request.user

        if not user.requested_email:
            return Response(
                {"error": _("No email change request pending.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_email = user.requested_email
        if not verify_otp(new_email, otp_code, AuthType.EMAIL_CHANGE):
            return Response(
                {"error": _("Invalid OTP code.")}, status=status.HTTP_400_BAD_REQUEST
            )

        user.email = new_email
        user.last_email_change = timezone.now()
        user.requested_email = None
        user.save()

        return Response(
            {"message": _("Email successfully updated to {}.").format(new_email)},
            status=status.HTTP_200_OK,
        )
