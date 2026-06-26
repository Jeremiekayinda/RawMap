"""
Couche service pour l'application iot.

Centralise la réception des données ESP32 et le calcul de l'affluence.
"""

from datetime import datetime

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.iot.models import (
    Capteur,
    DirectionPassage,
    ESP32,
    Passage,
    StatutESP32,
)
from apps.iot.validators import (
    validate_capteur_passage_coherence,
    validate_direction_capteur,
)


class ESP32Service:
    """Services métier liés aux dispositifs ESP32."""

    @staticmethod
    def get_queryset_base() -> QuerySet[ESP32]:
        """QuerySet de base avec agence pré-chargée."""
        return ESP32.objects.select_related('agence').prefetch_related('capteurs')

    @classmethod
    def list_by_agence(cls, agence_id: int) -> QuerySet[ESP32]:
        """Retourne les ESP32 rattachés à une agence."""
        return cls.get_queryset_base().filter(agence_id=agence_id).order_by('nom')

    @classmethod
    def list_actifs(cls) -> QuerySet[ESP32]:
        """Retourne les ESP32 actifs."""
        return cls.get_queryset_base().filter(statut=StatutESP32.ACTIF)

    @classmethod
    def get_by_numero_serie(cls, numero_serie: str) -> ESP32 | None:
        """Récupère un ESP32 par son numéro de série."""
        normalized = numero_serie.strip().upper()
        return cls.get_queryset_base().filter(numero_serie=normalized).first()

    @staticmethod
    def enregistrer_connexion(esp32: ESP32, adresse_ip: str | None = None) -> ESP32:
        """Met à jour la dernière connexion (heartbeat ESP32)."""
        esp32.derniere_connexion = timezone.now()
        update_fields = ['derniere_connexion', 'updated_at']
        if adresse_ip:
            esp32.adresse_ip = adresse_ip
            update_fields.append('adresse_ip')
        esp32.save(update_fields=update_fields)
        return esp32

    @staticmethod
    def set_statut(esp32: ESP32, statut: str) -> ESP32:
        """Met à jour le statut opérationnel d'un ESP32."""
        esp32.statut = statut
        esp32.save(update_fields=['statut', 'updated_at'])
        return esp32


class CapteurService:
    """Services métier liés aux capteurs."""

    @staticmethod
    def get_queryset_base() -> QuerySet[Capteur]:
        """QuerySet de base avec ESP32 pré-chargé."""
        return Capteur.objects.select_related('esp32', 'esp32__agence')

    @classmethod
    def list_by_esp32(cls, esp32_id: int, actifs_only: bool = True) -> QuerySet[Capteur]:
        """Retourne les capteurs d'un ESP32."""
        queryset = cls.get_queryset_base().filter(esp32_id=esp32_id)
        if actifs_only:
            queryset = queryset.filter(actif=True)
        return queryset.order_by('nom')

    @classmethod
    def get_by_id(cls, capteur_id: int) -> Capteur | None:
        """Récupère un capteur par identifiant."""
        return cls.get_queryset_base().filter(pk=capteur_id).first()


class PassageService:
    """Services métier pour l'enregistrement et l'analyse des passages."""

    @staticmethod
    def get_queryset_base() -> QuerySet[Passage]:
        """QuerySet de base avec relations pré-chargées."""
        return Passage.objects.select_related('esp32', 'capteur', 'esp32__agence')

    @classmethod
    def enregistrer_passage(
        cls,
        esp32: ESP32,
        capteur: Capteur,
        direction: str,
        timestamp: datetime | None = None,
    ) -> Passage:
        """
        Enregistre un passage détecté par un capteur ESP32.

        Valide la cohérence ESP32/capteur/direction avant persistance.
        """
        validate_capteur_passage_coherence(esp32, capteur)
        validate_direction_capteur(capteur, direction)

        passage = Passage.objects.create(
            esp32=esp32,
            capteur=capteur,
            direction=direction,
            timestamp=timestamp or timezone.now(),
        )
        ESP32Service.enregistrer_connexion(esp32)
        return passage

    @classmethod
    def enregistrer_depuis_payload(
        cls,
        numero_serie: str,
        capteur_id: int,
        direction: str,
        timestamp: datetime | None = None,
    ) -> Passage:
        """Enregistre un passage à partir d'un payload ESP32 simplifié."""
        esp32 = ESP32Service.get_by_numero_serie(numero_serie)
        if esp32 is None:
            raise ValueError(f'ESP32 introuvable : {numero_serie}')

        capteur = CapteurService.get_by_id(capteur_id)
        if capteur is None:
            raise ValueError(f'Capteur introuvable : {capteur_id}')

        return cls.enregistrer_passage(esp32, capteur, direction, timestamp)

    @classmethod
    def list_by_esp32(
        cls,
        esp32_id: int,
        debut: datetime | None = None,
        fin: datetime | None = None,
    ) -> QuerySet[Passage]:
        """Retourne les passages d'un ESP32 sur une période."""
        queryset = cls.get_queryset_base().filter(esp32_id=esp32_id)
        if debut:
            queryset = queryset.filter(timestamp__gte=debut)
        if fin:
            queryset = queryset.filter(timestamp__lte=fin)
        return queryset.order_by('-timestamp')

    @classmethod
    def calculer_affluence(
        cls,
        esp32_id: int,
        debut: datetime,
        fin: datetime,
    ) -> dict:
        """
        Calcule l'affluence nette sur une période donnée.

        Retourne les comptages IN, OUT et la différence (présence nette).
        """
        passages = cls.list_by_esp32(esp32_id, debut, fin)
        stats = passages.aggregate(
            entrees=Count('id', filter=Q(direction=DirectionPassage.IN)),
            sorties=Count('id', filter=Q(direction=DirectionPassage.OUT)),
        )
        entrees = stats['entrees'] or 0
        sorties = stats['sorties'] or 0
        return {
            'esp32_id': esp32_id,
            'debut': debut,
            'fin': fin,
            'entrees': entrees,
            'sorties': sorties,
            'affluence_nette': entrees - sorties,
        }

    @classmethod
    def calculer_affluence_agence(
        cls,
        agence_id: int,
        debut: datetime,
        fin: datetime,
    ) -> dict:
        """Calcule l'affluence agrégée pour tous les ESP32 d'une agence."""
        passages = cls.get_queryset_base().filter(
            esp32__agence_id=agence_id,
            timestamp__gte=debut,
            timestamp__lte=fin,
        )
        stats = passages.aggregate(
            entrees=Count('id', filter=Q(direction=DirectionPassage.IN)),
            sorties=Count('id', filter=Q(direction=DirectionPassage.OUT)),
        )
        entrees = stats['entrees'] or 0
        sorties = stats['sorties'] or 0
        return {
            'agence_id': agence_id,
            'debut': debut,
            'fin': fin,
            'entrees': entrees,
            'sorties': sorties,
            'affluence_nette': entrees - sorties,
        }

    @classmethod
    def derniers_passages(cls, esp32_id: int, limit: int = 50) -> QuerySet[Passage]:
        """Retourne les derniers passages enregistrés pour un ESP32."""
        return (
            cls.get_queryset_base()
            .filter(esp32_id=esp32_id)
            .order_by('-timestamp')[:limit]
        )
