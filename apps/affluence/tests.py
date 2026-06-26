"""
Tests unitaires — application affluence.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.affluence.models import Affluence, HistoriqueAffluence, NiveauAffluence
from apps.affluence.services import AffluenceService, AffluenceSimulatorError, AffluenceSimulatorService
from apps.affluence.validators import validate_personnes_presentes, validate_personnes_capacite
from apps.agencies.models import Agence


class AffluenceTestMixin:
    """Fixtures communes pour les tests d'affluence."""

    @classmethod
    def create_agence(cls, capacite_max=100, code='RB-AFF-001'):
        return Agence.objects.create(
            nom='Agence Affluence Test',
            code=code,
            adresse='1 Rue Affluence',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='affluence@rawbank.cd',
            latitude=-4.32, longitude=15.32,
            capacite_max=capacite_max,
        )


class CalculateOccupancyRateTests(TestCase):
    """Tests du calcul du taux d'occupation."""

    def test_taux_zero_personne(self):
        taux = AffluenceService.calculate_occupancy_rate(0, 100)
        self.assertEqual(taux, Decimal('0.00'))

    def test_taux_moitie_capacite(self):
        taux = AffluenceService.calculate_occupancy_rate(50, 100)
        self.assertEqual(taux, Decimal('50.00'))

    def test_taux_depassement_capacite(self):
        taux = AffluenceService.calculate_occupancy_rate(150, 100)
        self.assertEqual(taux, Decimal('150.00'))

    def test_capacite_zero_invalide(self):
        with self.assertRaises(ValueError):
            AffluenceService.calculate_occupancy_rate(10, 0)


class CalculateLevelTests(TestCase):
    """Tests du calcul du niveau d'alerte."""

    def test_niveau_vert_limite_basse(self):
        self.assertEqual(
            AffluenceService.calculate_level(Decimal('0')),
            NiveauAffluence.VERT,
        )

    def test_niveau_vert_limite_haute(self):
        self.assertEqual(
            AffluenceService.calculate_level(Decimal('40')),
            NiveauAffluence.VERT,
        )

    def test_niveau_orange_limite_basse(self):
        self.assertEqual(
            AffluenceService.calculate_level(Decimal('41')),
            NiveauAffluence.ORANGE,
        )

    def test_niveau_orange_limite_haute(self):
        self.assertEqual(
            AffluenceService.calculate_level(Decimal('70')),
            NiveauAffluence.ORANGE,
        )

    def test_niveau_rouge(self):
        self.assertEqual(
            AffluenceService.calculate_level(Decimal('71')),
            NiveauAffluence.ROUGE,
        )


class AffluenceServiceTests(AffluenceTestMixin, TestCase):
    """Tests de la mise à jour d'affluence et de l'historique."""

    def setUp(self):
        self.agence = self.create_agence(capacite_max=100)

    def test_update_affluence_cree_enregistrement(self):
        affluence = AffluenceService.update_affluence(self.agence, 30)
        self.assertEqual(affluence.personnes_presentes, 30)
        self.assertEqual(affluence.taux_occupation, Decimal('30.00'))
        self.assertEqual(affluence.niveau, NiveauAffluence.VERT)
        self.assertIsNotNone(affluence.derniere_mise_a_jour)

    def test_update_affluence_cree_historique(self):
        AffluenceService.update_affluence(self.agence, 30)
        self.assertEqual(HistoriqueAffluence.objects.count(), 1)

    def test_update_affluence_mise_a_jour_existant(self):
        AffluenceService.update_affluence(self.agence, 30)
        affluence = AffluenceService.update_affluence(self.agence, 75)
        self.assertEqual(Affluence.objects.count(), 1)
        self.assertEqual(affluence.personnes_presentes, 75)
        self.assertEqual(affluence.taux_occupation, Decimal('75.00'))
        self.assertEqual(affluence.niveau, NiveauAffluence.ROUGE)
        self.assertEqual(HistoriqueAffluence.objects.count(), 2)

    def test_create_history(self):
        historique = AffluenceService.create_history(
            agence=self.agence,
            personnes_presentes=50,
            taux_occupation=Decimal('50.00'),
            niveau=NiveauAffluence.ORANGE,
        )
        self.assertIn(self.agence.code, str(historique))

    def test_get_affluence(self):
        AffluenceService.update_affluence(self.agence, 20)
        affluence = AffluenceService.get_affluence(self.agence)
        self.assertIsNotNone(affluence)
        self.assertEqual(affluence.personnes_presentes, 20)

    def test_get_historique(self):
        AffluenceService.update_affluence(self.agence, 10)
        AffluenceService.update_affluence(self.agence, 20)
        historique = AffluenceService.get_historique(self.agence)
        self.assertEqual(len(historique), 2)


class AffluenceModelTests(AffluenceTestMixin, TestCase):
    """Tests des modèles."""

    def setUp(self):
        self.agence = self.create_agence()

    def test_str_affluence(self):
        affluence = AffluenceService.update_affluence(self.agence, 40)
        self.assertIn('40 pers.', str(affluence))
        self.assertIn('Faible', str(affluence))


class ValidatorsTests(TestCase):
    """Tests des validateurs."""

    def test_validate_personnes_presentes_valide(self):
        validate_personnes_presentes(0)
        validate_personnes_presentes(100)

    def test_validate_personnes_presentes_invalide(self):
        with self.assertRaises(ValidationError):
            validate_personnes_presentes(-1)

    def test_validate_personnes_capacite(self):
        validate_personnes_capacite(50, 100)
        with self.assertRaises(ValidationError):
            validate_personnes_capacite(101, 100)


class AffluenceSimulatorServiceTests(AffluenceTestMixin, TestCase):
    """Tests du simulateur d'affluence temporaire."""

    def setUp(self):
        self.agence = self.create_agence(capacite_max=10)

    def test_entry_incremente(self):
        affluence = AffluenceSimulatorService.entry(self.agence)
        self.assertEqual(affluence.personnes_presentes, 1)

    def test_exit_decremente(self):
        AffluenceSimulatorService.entry(self.agence)
        affluence = AffluenceSimulatorService.exit(self.agence)
        self.assertEqual(affluence.personnes_presentes, 0)

    def test_reset(self):
        AffluenceSimulatorService.entry(self.agence)
        affluence = AffluenceSimulatorService.reset(self.agence)
        self.assertEqual(affluence.personnes_presentes, 0)

    def test_entry_capacite_max(self):
        AffluenceService.update_affluence(self.agence, 10)
        with self.assertRaises(AffluenceSimulatorError):
            AffluenceSimulatorService.entry(self.agence)

    def test_exit_negatif_interdit(self):
        with self.assertRaises(AffluenceSimulatorError):
            AffluenceSimulatorService.exit(self.agence)

    def test_entry_cree_historique(self):
        AffluenceSimulatorService.entry(self.agence)
        from apps.affluence.models import HistoriqueAffluence
        self.assertEqual(HistoriqueAffluence.objects.count(), 1)
