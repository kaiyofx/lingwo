from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
# from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import ABSUser

# from ..permissions import OAuthOrJWT
from ..serializers import UserProfileSerializer
from django.utils.translation import gettext_lazy as _
from ..models import AuthType, EventType
from django.contrib.auth import get_user_model


User = get_user_model()


class ProfileView(APIView):
    """
    Profile View (/me/ and /<int:username>/).
    """

    authentication_classes = [JWTAuthentication]

    permission_classes = [AllowAny]

    def get_object(self, username=None):
        """get user object by username or request.user"""
        if username:
            try:
                return User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def get(self, request, username=None, *args, **kwargs):
        target_user = self.get_object(username)

        if not target_user:
            return Response(
                {"detail": _("User with this email does not exist.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_owner = request.user.is_authenticated and request.user.pk == target_user.pk

        serializer = UserProfileSerializer(target_user, is_owner=is_owner)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, username=None, *args, **kwargs):
        if not request.user.is_authenticated or (
            username and request.user.username != username
        ):
            return Response(
                {"detail": _("You do not have permission to edit this profile.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, username=None, *args, **kwargs):
        if not request.user.is_authenticated or (
            username and request.user.username != username
        ):
            return Response(
                {"detail": _("You do not have permission to delete this profile.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        user: ABSUser = request.user
        if user.is_deleted:
            return Response(
                {"detail": "User is already marked for deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.soft_delete()
        return Response(
            {
                "detail": "User marked for deletion. You have 60 days to restore your account."
            },
            status=status.HTTP_202_ACCEPTED,
        )
