from django.apps import AppConfig


class AtmConfig(AppConfig):
    """Configuration de l'application de gestion des DAB (ATM)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.atm'
    verbose_name = 'DAB (ATM)'
