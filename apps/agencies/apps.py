from django.apps import AppConfig


class AgenciesConfig(AppConfig):
    """Configuration de l'application de gestion des agences bancaires."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agencies'
    verbose_name = 'Agences'
