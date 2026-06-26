"""
Point d'entrée des paramètres Django.

Par défaut, charge la configuration de développement.
Pour la production : DJANGO_SETTINGS_MODULE=config.settings.production
"""

from .development import *  # noqa: F401, F403
