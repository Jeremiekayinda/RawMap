"""
Permissions DRF pour la couche API (v1).

Authentification JWT à implémenter ultérieurement — accès public pour l'instant.
"""

from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser


class PublicAPIAccess(BasePermission):
    """
    Autorise l'accès public à l'API v1.

    À remplacer par des permissions granulaires lors de l'intégration JWT.
    """

    def has_permission(self, request, view):
        return True


# Alias explicite pour les ViewSets en lecture seule
AllowAnyReadOnly = AllowAny

# Simulateur d'affluence — réservé au staff admin
SimulatorStaffOnly = IsAdminUser
