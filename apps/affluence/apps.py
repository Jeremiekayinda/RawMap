from django.apps import AppConfig


class AffluenceConfig(AppConfig):
    """Configuration de l'application de suivi de l'affluence."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.affluence'
    verbose_name = 'Affluence'
