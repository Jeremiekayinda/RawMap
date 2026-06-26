from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration de l'application de notifications."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'
