"""
URLconf de test pour le module api.

Permet de tester l'API sans modifier config/urls.py.
"""

from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('apps.api.urls')),
]
