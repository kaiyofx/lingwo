from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# --- Roles ---
class UserRoles(models.IntegerChoices):
    ADMIN = 1, _("Admin")
    CLIENT = 2, _("Client")


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    class Meta:
        db_table = 'role'
        managed = False
    def __str__(self):
        return self.name


# --- custom model ---
class ABSUser(AbstractUser):
    first_name = None
    last_name = None
    username = models.CharField(_("username"), max_length=40, blank=False, unique=True)
    email = models.EmailField(_("email"), max_length=254, blank=False, unique=True)
    otp = models.BooleanField(_("Code"), default=False, db_column="OTP")
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    otp_only = models.BooleanField(_("otp only"), default=False, db_column="OTP_only")
    is_deleted = models.BooleanField(_("deleted"), default=False)
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    lockout_time = models.DateTimeField(null=True, blank=True)

    role = models.ForeignKey(Role, on_delete=models.PROTECT, default=UserRoles.CLIENT) # pyright: ignore[reportArgumentType]

    last_username_change = models.DateTimeField(
        null=True, blank=True, verbose_name="Date of last username change"
    )
    requested_username = models.CharField(
        max_length=150, unique=False, null=True, blank=True
    )

    requested_email = models.EmailField(
        max_length=254, unique=False, null=True, blank=True
    )
    last_email_change = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_("The groups this user belongs to."),
        related_name="silq_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="silq_user_permissions_set",
        related_query_name="user",
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def is_admin_user(self):
        return self.role.pk == UserRoles.ADMIN

    def soft_delete(self):
        """Отмечает пользователя как удаленного и фиксирует время."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False  # Дополнительно деактивируем пользователя
        self.save()

    def restore(self):
        """Восстанавливает пользователя."""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save()

    def is_deletable(self):
        """Проверяет, прошло ли 60 дней для окончательного удаления."""
        if not self.deleted_at:
            return False
        # Проверяем, прошло ли 60 дней
        time_limit = timezone.now() - timezone.timedelta(days=60)
        return self.deleted_at < time_limit

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = 'users'
        managed = False

    def __str__(self):
        return self.email


class AuthType(models.IntegerChoices):
    LOGIN = 1, _("Login")
    SIGNUP = 2, _("Signup")
    RESET_PASSWORD = 3, _("Reset Password")
    USERNAME_CHANGE = 4, _("Username Change")
    EMAIL_CHANGE = 5, _("Email Change")
    LOGOUT = 6, _("Logout")


class EventType(models.IntegerChoices):
    VIEW_PROFILE = 7, _("View Profile")
    EDIT_PROFILE = 8, _("Edit Profile")
    DELETE_PROFILE = 9, _("Delete Profile")
    RESTORE_PROFILE = 10, _("Restore Profile")


class AdminEventType(models.IntegerChoices):
    REVOKE_TOKENS = 11, _("Revoke Tokens")
