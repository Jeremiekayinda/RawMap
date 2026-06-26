"""
Permissions et mixins — application accounts.

Les visiteurs anonymes accèdent à la carte et aux agences (pages publiques).
Les fonctionnalités authentifiées (signalements, notifications, favoris)
seront protégées via AuthenticatedUserRequired.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


class AuthenticatedUserRequired(LoginRequiredMixin):
    """
    Mixin pour les vues réservées aux utilisateurs connectés.

    Usage futur : signalements, notifications, favoris.
    """

    login_url = '/login/'


authenticated_user_required = login_required(login_url='/login/')
