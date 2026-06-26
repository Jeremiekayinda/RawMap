from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration de l'application tableau de bord."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Tableau de bord'
