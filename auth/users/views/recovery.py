from ..models import ABSUser
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from ..models import AuthType, EventType


class RestoreUserView(APIView):
    """
    Endpoint for restoring a deleted user.
    """

    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get("username_or_email")
        password = request.data.get("password")

        if not username_or_email or not password:
            return Response(
                {"detail": _("Please provide username/email and password.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            user = ABSUser.objects.get(
                models.Q(username=username_or_email) | models.Q(email=username_or_email)
            )
        except ABSUser.DoesNotExist:
            return Response(
                {"detail": _("Invalid credentials or user not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_deleted:
            return Response(
                {"detail": _("Account is not marked for deletion.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.deleted_at:
            return Response(
                {"detail": _("Account deletion date not found.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        time_limit = user.deleted_at + timedelta(days=60)
        if timezone.now() > time_limit:
            return Response(
                {
                    "detail": _("The 60-day recovery window has expired. The account is permanently deleted.")
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        authenticated_user = authenticate(
            request, username=user.username, password=password
        )

        if authenticated_user is not None:
            user.restore()
            return Response(
                {"detail": _("Account successfully restored. Please login.")},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": _("Invalid password.")}, status=status.HTTP_401_UNAUTHORIZED
            )
