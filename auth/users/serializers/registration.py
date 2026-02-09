from rest_framework.serializers import Serializer, EmailField, CharField, ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ..models import ABSUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# =======================================================
# step 2: verifying OTP code serializer
# =======================================================
class VerifyCodeSerializer(Serializer):
    email = EmailField(
        max_length=ABSUser._meta.get_field("email").max_length, required=True
    )
    otp = CharField(max_length=6, min_length=6)


# =======================================================
# Step 3: complete registration serializer
# =======================================================
class CompleteRegistrationSerializer(Serializer):
    registration_token = CharField(max_length=64)

    username = CharField(
        max_length=ABSUser._meta.get_field("username").max_length,
    )
    password = CharField(min_length=4, write_only=True)

    def validate_username(self, value):
        """Check unique username"""
        if User.objects.filter(username=value).exists():
            raise ValidationError(_("Пользователь с таким именем пользователя уже существует."))
        return value

    def create(self, validated_data):
        pass