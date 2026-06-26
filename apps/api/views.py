"""
Vues DRF pour la couche API REST v1.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agencies.services import AgenceService
from apps.affluence.models import Affluence
from apps.affluence.services import (
    AffluenceSimulatorError,
    AffluenceSimulatorService,
    AffluenceService,
)
from apps.api.permissions import AllowAnyReadOnly, SimulatorStaffOnly
from apps.api.serializers import (
    AffluenceListSerializer,
    AgenceListSerializer,
    AgenceNearbySerializer,
    ATMListSerializer,
    IoTUpdateSerializer,
)
from apps.atm.services import ATMService
from apps.iot.services import ESP32Service


class AgenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour les agences bancaires.

    Endpoints :
        GET /api/v1/agencies/          — Liste des agences actives
        GET /api/v1/agencies/<id>/     — Détail d'une agence
        GET /api/v1/agencies/nearby/   — Agences à proximité (PostGIS)
    """

    serializer_class = AgenceListSerializer
    permission_classes = [AllowAnyReadOnly]

    def get_queryset(self):
        """Retourne les agences actives avec relations pré-chargées."""
        return AgenceService.list_actives()

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        GET /api/v1/agencies/nearby/

        Recherche les agences dans un rayon autour d'un point GPS.

        Paramètres query :
            latitude  (float, requis) — Latitude WGS84
            longitude (float, requis) — Longitude WGS84
            radius    (float, optionnel) — Rayon en km (défaut : 5)
        """
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius = request.query_params.get('radius', '5')

        if latitude is None or longitude is None:
            return Response(
                {
                    'detail': (
                        'Les paramètres « latitude » et « longitude » '
                        'sont obligatoires.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Paramètres géographiques invalides.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if radius <= 0:
            return Response(
                {'detail': 'Le rayon doit être supérieur à 0.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agences = AgenceService.find_nearby(
            longitude=longitude,
            latitude=latitude,
            radius_km=radius,
            actives_only=True,
        )
        serializer = AgenceNearbySerializer(agences, many=True)
        return Response(serializer.data)


class ATMViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour les distributeurs automatiques (DAB).

    Endpoints :
        GET /api/v1/atms/      — Liste des DAB
        GET /api/v1/atms/<id>/ — Détail d'un DAB
    """

    serializer_class = ATMListSerializer
    permission_classes = [AllowAnyReadOnly]

    def get_queryset(self):
        """Retourne tous les DAB avec agence pré-chargée."""
        return ATMService.list_all()


class AffluenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour l'affluence en temps réel.

    Endpoints :
        GET /api/v1/affluence/              — Liste de toutes les affluences
        GET /api/v1/affluence/<agency_id>/  — Affluence d'une agence
    """

    serializer_class = AffluenceListSerializer
    permission_classes = [AllowAnyReadOnly]
    lookup_field = 'agence_id'
    lookup_url_kwarg = 'agency_id'

    def get_queryset(self):
        """Retourne les états d'affluence avec agence pré-chargée."""
        return Affluence.objects.select_related('agence').order_by('agence__nom')


class IoTUpdateView(APIView):
    """
    Endpoint de réception des données ESP32 pour mise à jour de l'affluence.

    Endpoint :
        POST /api/v1/iot/update/

    Payload JSON :
        {
            "esp32_serial": "ESP32-001",
            "agency_id": 1,
            "people_count": 18,
            "timestamp": "2026-06-26T10:30:00Z"
        }

    Réponse succès (200) :
        {
            "status": "success",
            "message": "Affluence updated successfully."
        }
    """

    permission_classes = [AllowAnyReadOnly]

    def post(self, request):
        """Traite un payload IoT et met à jour l'affluence de l'agence."""
        serializer = IoTUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        esp32_serial = data['esp32_serial']
        agency_id = data['agency_id']
        people_count = data['people_count']

        esp32 = ESP32Service.get_by_numero_serie(esp32_serial)
        if esp32 is None:
            return Response(
                {
                    'status': 'error',
                    'message': f'ESP32 introuvable : {esp32_serial}.',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if esp32.agence_id != agency_id:
            return Response(
                {
                    'status': 'error',
                    'message': (
                        'L\'ESP32 ne correspond pas à l\'agence indiquée.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        AffluenceService.update_affluence(esp32.agence, people_count)
        ESP32Service.enregistrer_connexion(esp32)

        return Response(
            {
                'status': 'success',
                'message': 'Affluence updated successfully.',
            },
            status=status.HTTP_200_OK,
        )


class SimulatorBaseView(APIView):
    """
    Vue de base pour le simulateur d'affluence temporaire.

    Vérifie l'existence de l'agence et délègue à AffluenceSimulatorService.
    """

    permission_classes = [SimulatorStaffOnly]

    def perform_action(self, agence):
        """Surcharger dans chaque sous-classe pour définir l'action."""
        raise NotImplementedError

    def post(self, request, agency_id):
        """Exécute une action du simulateur pour l'agence donnée."""
        agence = AgenceService.get_by_id(agency_id)
        if agence is None:
            return Response(
                {
                    'status': 'error',
                    'message': f'Agence introuvable (id={agency_id}).',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            affluence = self.perform_action(agence)
        except AffluenceSimulatorError as exc:
            return Response(
                {'status': 'error', 'message': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AffluenceListSerializer(affluence)
        return Response(
            {
                'status': 'success',
                'message': 'Affluence mise à jour avec succès.',
                'affluence': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class SimulatorEntryView(SimulatorBaseView):
    """
    POST /api/v1/simulator/entry/<agency_id>/

    Simule l'entrée d'un client (+1 personne).
    """

    def perform_action(self, agence):
        return AffluenceSimulatorService.entry(agence)


class SimulatorExitView(SimulatorBaseView):
    """
    POST /api/v1/simulator/exit/<agency_id>/

    Simule la sortie d'un client (-1 personne).
    """

    def perform_action(self, agence):
        return AffluenceSimulatorService.exit(agence)


class SimulatorResetView(SimulatorBaseView):
    """
    POST /api/v1/simulator/reset/<agency_id>/

    Réinitialise le compteur à 0 personne.
    """

    def perform_action(self, agence):
        return AffluenceSimulatorService.reset(agence)
