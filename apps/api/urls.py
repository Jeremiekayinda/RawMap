"""
Routes API REST v1 — application api.

Montage recommandé dans config/urls.py :
    path('api/v1/', include('apps.api.urls')),
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.views import (
    AffluenceViewSet,
    AgenceViewSet,
    ATMViewSet,
    IoTUpdateView,
    SimulatorEntryView,
    SimulatorExitView,
    SimulatorResetView,
)

app_name = 'api-v1'

router = DefaultRouter()
router.register('agencies', AgenceViewSet, basename='agency')
router.register('atms', ATMViewSet, basename='atm')
router.register('affluence', AffluenceViewSet, basename='affluence')

urlpatterns = [
    path('iot/update/', IoTUpdateView.as_view(), name='iot-update'),
    path(
        'simulator/entry/<int:agency_id>/',
        SimulatorEntryView.as_view(),
        name='simulator-entry',
    ),
    path(
        'simulator/exit/<int:agency_id>/',
        SimulatorExitView.as_view(),
        name='simulator-exit',
    ),
    path(
        'simulator/reset/<int:agency_id>/',
        SimulatorResetView.as_view(),
        name='simulator-reset',
    ),
    path('', include(router.urls)),
]
