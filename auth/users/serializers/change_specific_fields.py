from rest_framework.serializers import Serializer, CharField, ValidationError, EmailField
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone
from ..models import ABSUser

User = get_user_model()


class RequestUsernameChangeSerializer(Serializer):
    new_username = CharField(max_length=ABSUser._meta.get_field("username").max_length)

    def validate_new_username(self, value):
        user: ABSUser = self.context["request"].user

        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError(_("Пользователь с таким именем пользователя уже существует."))

        if user.last_username_change:
            time_since_change = timezone.now() - user.last_username_change
            if time_since_change < timedelta(days=30):
                days_left = (timedelta(days=30) - time_since_change).days + 1
                raise ValidationError(
                    _(
                        "Имя пользователя можно менять только раз в 30 дней. Пожалуйста, подождите еще {}."
                    ).format(days_left)
                )

        if user.username.lower() == value.lower():
            raise ValidationError(
                _("Новое имя пользователя не может совпадать с текущим.")
            )

        return value


class RequestEmailChangeSerializer(Serializer):
    new_email = EmailField(max_length=ABSUser._meta.get_field("email").max_length)

    def validate_new_email(self, value):
        user: ABSUser = self.context["request"].user

        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError(_("Пользователь с таким адресом электронной почты уже существует."))

        if user.last_email_change:
            time_since_change = timezone.now() - user.last_email_change
            if time_since_change < timedelta(minutes=30):
                minutes_left = (timedelta(minutes=30) - time_since_change).seconds // 60
                raise ValidationError(
                    _(
                        "Адрес электронной почты можно менять только раз в 30 дней. Пожалуйста, подождите еще {}."
                    ).format(minutes_left)
                )

        if user.email.lower() == value.lower():
            raise ValidationError(
                _("Новое электронное письмо не может совпадать с текущим.")
            )

        return value

class OTPSerializer(Serializer):
    otp_code = CharField(max_length=6, min_length=6)
