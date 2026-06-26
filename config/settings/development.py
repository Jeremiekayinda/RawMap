"""
Paramètres spécifiques à l'environnement de développement.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Affichage détaillé des erreurs en développement
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# DRF : rendu HTML activé pour faciliter le débogage
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
