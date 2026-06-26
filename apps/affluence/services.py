"""
Couche service pour l'application affluence.

Centralise le calcul et la mise à jour de l'affluence en temps réel.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.affluence.models import Affluence, HistoriqueAffluence, NiveauAffluence
from apps.affluence.validators import validate_personnes_presentes


class AffluenceService:
    """Services métier pour le suivi d'affluence en temps réel."""

    @staticmethod
    def calculate_occupancy_rate(
        personnes_presentes: int,
        capacite_max: int,
    ) -> Decimal:
        """
        Calcule le taux d'occupation en pourcentage.

        Formule : (personnes_presentes / capacite_max) × 100
        """
        if capacite_max <= 0:
            raise ValueError('La capacité maximale de l\'agence doit être supérieure à 0.')

        taux = (Decimal(personnes_presentes) / Decimal(capacite_max)) * Decimal('100')
        return taux.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_level(taux_occupation: Decimal) -> str:
        """
        Détermine le niveau d'alerte selon le taux d'occupation.

        - 0 à 40 %   → Faible (vert)
        - 41 à 70 %  → Moyenne (orange)
        - > 70 %     → Forte (rouge)
        """
        taux = Decimal(taux_occupation)
        if taux <= Decimal('40'):
            return NiveauAffluence.VERT
        if taux <= Decimal('70'):
            return NiveauAffluence.ORANGE
        return NiveauAffluence.ROUGE

    @classmethod
    def create_history(
        cls,
        agence,
        personnes_presentes: int,
        taux_occupation: Decimal,
        niveau: str,
    ) -> HistoriqueAffluence:
        """Enregistre un snapshot dans l'historique d'affluence."""
        return HistoriqueAffluence.objects.create(
            agence=agence,
            personnes_presentes=personnes_presentes,
            taux_occupation=taux_occupation,
            niveau=niveau,
        )

    @classmethod
    @transaction.atomic
    def update_affluence(cls, agence, personnes_presentes: int) -> Affluence:
        """
        Met à jour l'affluence en temps réel d'une agence.

        Recalcule le taux d'occupation, le niveau d'alerte et
        enregistre automatiquement un historique.
        """
        validate_personnes_presentes(personnes_presentes)

        taux_occupation = cls.calculate_occupancy_rate(
            personnes_presentes,
            agence.capacite_max,
        )
        niveau = cls.calculate_level(taux_occupation)
        maintenant = timezone.now()

        affluence, _created = Affluence.objects.get_or_create(
            agence=agence,
            defaults={
                'personnes_presentes': personnes_presentes,
                'taux_occupation': taux_occupation,
                'niveau': niveau,
                'derniere_mise_a_jour': maintenant,
            },
        )

        if not _created:
            affluence.personnes_presentes = personnes_presentes
            affluence.taux_occupation = taux_occupation
            affluence.niveau = niveau
            affluence.derniere_mise_a_jour = maintenant
            affluence.save(update_fields=[
                'personnes_presentes',
                'taux_occupation',
                'niveau',
                'derniere_mise_a_jour',
                'updated_at',
            ])

        cls.create_history(
            agence=agence,
            personnes_presentes=personnes_presentes,
            taux_occupation=taux_occupation,
            niveau=niveau,
        )

        return affluence

    @staticmethod
    def get_affluence(agence) -> Affluence | None:
        """Retourne l'état d'affluence courant d'une agence."""
        return Affluence.objects.filter(agence=agence).select_related('agence').first()

    @staticmethod
    def get_historique(agence, limit: int = 100):
        """Retourne l'historique d'affluence d'une agence."""
        return (
            HistoriqueAffluence.objects
            .filter(agence=agence)
            .select_related('agence')
            .order_by('-created_at')[:limit]
        )


class AffluenceSimulatorError(Exception):
    """Erreur métier levée par le simulateur d'affluence temporaire."""


class AffluenceSimulatorService:
    """
    Simulateur temporaire d'entrées/sorties clients.

    Délègue la persistance à AffluenceService — remplaçable par les ESP32
    sans modifier la logique métier centrale.
    """

    @staticmethod
    def _get_current_count(agence) -> int:
        """Retourne le nombre actuel de personnes présentes."""
        affluence = AffluenceService.get_affluence(agence)
        return affluence.personnes_presentes if affluence else 0

    @classmethod
    def entry(cls, agence) -> Affluence:
        """
        Simule l'entrée d'un client (+1).

        Raises:
            AffluenceSimulatorError: si la capacité maximale est atteinte.
        """
        from apps.affluence.validators import validate_personnes_capacite

        current = cls._get_current_count(agence)
        new_count = current + 1

        try:
            validate_personnes_capacite(new_count, agence.capacite_max)
        except ValidationError as exc:
            raise AffluenceSimulatorError(exc.messages[0]) from exc

        return AffluenceService.update_affluence(agence, new_count)

    @classmethod
    def exit(cls, agence) -> Affluence:
        """
        Simule la sortie d'un client (-1).

        Raises:
            AffluenceSimulatorError: si le compteur est déjà à zéro.
        """
        current = cls._get_current_count(agence)
        if current <= 0:
            raise AffluenceSimulatorError(
                'Le nombre de personnes ne peut pas être négatif.',
            )
        return AffluenceService.update_affluence(agence, current - 1)

    @classmethod
    def reset(cls, agence) -> Affluence:
        """Réinitialise le compteur à zéro personne."""
        return AffluenceService.update_affluence(agence, 0)
