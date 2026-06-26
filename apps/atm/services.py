"""
Couche service pour l'application atm.

Centralise la logique métier et les requêtes complexes.
"""

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import QuerySet

from apps.atm.models import ATM, StatutATM


class ATMService:
    """Services métier liés aux distributeurs automatiques."""

    @staticmethod
    def get_queryset_base() -> QuerySet[ATM]:
        """QuerySet de base avec agence pré-chargée."""
        return ATM.objects.select_related('agence')

    @classmethod
    def list_all(cls) -> QuerySet[ATM]:
        """Retourne tous les DAB."""
        return cls.get_queryset_base().order_by('agence', 'nom')

    @classmethod
    def list_by_agence(cls, agence_id: int) -> QuerySet[ATM]:
        """Retourne les DAB rattachés à une agence."""
        return cls.get_queryset_base().filter(agence_id=agence_id).order_by('nom')

    @classmethod
    def list_disponibles(cls) -> QuerySet[ATM]:
        """Retourne les DAB disponibles avec espèces."""
        return cls.get_queryset_base().filter(
            statut=StatutATM.DISPONIBLE,
            cash_disponible=True,
        ).order_by('agence', 'nom')

    @classmethod
    def get_by_code(cls, code_atm: str) -> ATM | None:
        """Récupère un DAB par son code unique."""
        normalized_code = code_atm.strip().upper()
        return cls.get_queryset_base().filter(code_atm=normalized_code).first()

    @classmethod
    def get_by_id(cls, atm_id: int) -> ATM | None:
        """Récupère un DAB par son identifiant."""
        return cls.get_queryset_base().filter(pk=atm_id).first()

    @classmethod
    def find_nearby(
        cls,
        longitude: float,
        latitude: float,
        radius_km: float = 2.0,
        disponibles_only: bool = True,
    ) -> QuerySet[ATM]:
        """
        Recherche les DAB dans un rayon donné (km) autour d'un point GPS.
        """
        point = Point(longitude, latitude, srid=4326)
        queryset = (
            cls.get_queryset_base()
            .filter(localisation__distance_lte=(point, D(km=radius_km)))
            .annotate(distance=Distance('localisation', point))
            .order_by('distance')
        )
        if disponibles_only:
            queryset = queryset.filter(
                statut=StatutATM.DISPONIBLE,
                cash_disponible=True,
            )
        return queryset

    @staticmethod
    def set_statut(atm: ATM, statut: str) -> ATM:
        """Met à jour le statut opérationnel d'un DAB."""
        atm.statut = statut
        atm.save(update_fields=['statut', 'updated_at'])
        return atm

    @staticmethod
    def set_cash_disponible(atm: ATM, disponible: bool) -> ATM:
        """Met à jour la disponibilité des espèces."""
        atm.cash_disponible = disponible
        atm.save(update_fields=['cash_disponible', 'updated_at'])
        return atm

    @classmethod
    def count_by_agence(cls, agence_id: int) -> int:
        """Compte le nombre de DAB rattachés à une agence."""
        return cls.get_queryset_base().filter(agence_id=agence_id).count()
