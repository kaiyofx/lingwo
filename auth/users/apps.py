from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    def ready(self):
        try:
            from .utils import create_initial_roles
            post_migrate.connect(create_initial_roles, sender=self)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Roles creation deferred or failed (expected during migrations): %s", e)