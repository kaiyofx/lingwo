# from oauth2_provider.views.base import TokenView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from .otp_utils import verify_otp
from .models import ABSUser
from django.db.models import Q

User = ABSUser()


def find_user(
    user_email: str | None = None, username: str | None = None
) -> ABSUser | Response:
    print(user_email, username)
    if not (user_email or username):
        return Response(
            {"error": "Отсутствует OTP или имя пользователя."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    query = Q()
    if user_email:
        query |= Q(email__iexact=user_email)
    if username:
        query |= Q(username__iexact=username)
    user = ABSUser.objects.filter(query).first()
    # user = SilqUser.objects.get(email=user_email, username=username)
    if not user:
        return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
    return user


def create_initial_roles(sender, **kwargs):
    if not kwargs.get("interactive", True):
        return

    from .models import Role, UserRoles

    roles_data = {
        UserRoles.ADMIN: "Admin",
        UserRoles.CLIENT: "Client",
    }

    for pk, name in roles_data.items():
        Role.objects.get_or_create(pk=pk, defaults={"name": name})
