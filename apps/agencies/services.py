"""
Couche service pour l'application agencies.

Centralise la logique métier et les requêtes complexes.
"""

from django.db.models import Count, Prefetch, Q, QuerySet

from apps.agencies.models import Agence, Horaire, Service, StatutAgence
from apps.agencies.utils.geo import haversine_km
from apps.atm.models import StatutATM


class AgenceService:
    """Services métier liés aux agences bancaires."""

    @staticmethod
    def get_queryset_base() -> QuerySet[Agence]:
        """QuerySet de base avec relations pré-chargées."""
        return Agence.objects.prefetch_related(
            Prefetch('horaires', queryset=Horaire.objects.order_by('jour')),
            'services',
        ).annotate(
            atm_disponibles_count=Count(
                'atms',
                filter=Q(
                    atms__statut=StatutATM.DISPONIBLE,
                    atms__cash_disponible=True,
                ),
            ),
        )

    @classmethod
    def list_actives(cls) -> QuerySet[Agence]:
        """Retourne toutes les agences actives."""
        return cls.get_queryset_base().filter(statut=StatutAgence.ACTIF)

    @classmethod
    def get_by_code(cls, code: str) -> Agence | None:
        """Récupère une agence par son code unique."""
        normalized_code = code.strip().upper()
        return cls.get_queryset_base().filter(code=normalized_code).first()

    @classmethod
    def get_by_id(cls, agence_id: int) -> Agence | None:
        """Récupère une agence par son identifiant."""
        return cls.get_queryset_base().filter(pk=agence_id).first()

    @classmethod
    def search_by_ville(cls, ville: str, actives_only: bool = True) -> QuerySet[Agence]:
        """Recherche des agences par ville (insensible à la casse)."""
        queryset = cls.get_queryset_base().filter(ville__icontains=ville.strip())
        if actives_only:
            queryset = queryset.filter(statut=StatutAgence.ACTIF)
        return queryset

    @classmethod
    def find_nearby(
        cls,
        longitude: float,
        latitude: float,
        radius_km: float = 5.0,
        actives_only: bool = True,
    ) -> list[Agence]:
        """
        Recherche les agences dans un rayon donné (km) autour d'un point GPS.

        MVP : calcul Haversine en Python (sans PostGIS).
        """
        queryset = cls.get_queryset_base()
        if actives_only:
            queryset = queryset.filter(statut=StatutAgence.ACTIF)

        results = []
        for agence in queryset:
            distance_km = haversine_km(
                latitude,
                longitude,
                float(agence.latitude),
                float(agence.longitude),
            )
            if distance_km <= radius_km:
                agence.distance = distance_km * 1000  # mètres pour l'API
                results.append(agence)

        results.sort(key=lambda item: item.distance)
        return results

    @staticmethod
    def set_statut(agence: Agence, statut: str) -> Agence:
        """Met à jour le statut d'une agence."""
        agence.statut = statut
        agence.save(update_fields=['statut', 'updated_at'])
        return agence

    @staticmethod
    def attach_services(agence: Agence, services: list[Service]) -> Agence:
        """Associe une liste de services à une agence."""
        agence.services.set(services)
        return agence


class ServiceCatalogue:
    """Services métier liés au catalogue de services bancaires."""

    @staticmethod
    def list_all() -> QuerySet[Service]:
        """Retourne tous les services disponibles."""
        return Service.objects.all().order_by('nom')

    @staticmethod
    def get_or_none(service_id: int) -> Service | None:
        """Récupère un service par identifiant."""
        return Service.objects.filter(pk=service_id).first()
