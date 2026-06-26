from django.apps import AppConfig


class IotConfig(AppConfig):
    """Configuration de l'application IoT (capteurs ESP32)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.iot'
    verbose_name = 'IoT'
