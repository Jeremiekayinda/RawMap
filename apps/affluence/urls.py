"""
URLs de l'application affluence — dashboard simulateur.
"""

from django.urls import path

from apps.affluence.views import SimulatorDashboardView

app_name = 'affluence'

urlpatterns = [
    path('simulator/', SimulatorDashboardView.as_view(), name='simulator'),
]
