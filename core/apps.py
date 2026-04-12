from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """initialte the signal when ready"""
        import core.signals.users
        import core.signals.course
