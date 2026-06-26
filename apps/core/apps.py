from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application core (pages publiques, utilitaires transverses)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'
