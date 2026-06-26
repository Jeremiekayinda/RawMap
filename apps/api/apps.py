from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration de l'application API REST (DRF)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    verbose_name = 'API REST'
