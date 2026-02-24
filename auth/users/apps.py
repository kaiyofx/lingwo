from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    def ready(self):
        from .utils import create_initial_roles
        post_migrate.connect(create_initial_roles, sender=self)