"""
Tests unitaires — application atm.
"""

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.agencies.models import Agence, StatutAgence
from apps.atm.models import ATM, StatutATM
from apps.atm.services import ATMService
from apps.atm.validators import validate_code_atm


class ATMModelTests(TestCase):
    """Tests du modèle ATM."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence Gombe',
            code='RB-KIN-010',
            adresse='1 Avenue Test',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='gombe@rawbank.cd',
            localisation=Point(15.32, -4.32, srid=4326),
            capacite_max=50,
            statut=StatutAgence.ACTIF,
        )
        self.atm_data = {
            'agence': self.agence,
            'nom': 'DAB Gombe Entrée',
            'code_atm': 'ATM-KIN-001',
            'localisation': Point(15.3201, -4.3201, srid=4326),
            'statut': StatutATM.DISPONIBLE,
            'cash_disponible': True,
            'description': 'DAB situé à l\'entrée principale',
        }

    def test_create_atm(self):
        atm = ATM.objects.create(**self.atm_data)
        self.assertIn('ATM-KIN-001', str(atm))
        self.assertIn('RB-KIN-010', str(atm))
        self.assertTrue(atm.est_operational)

    def test_code_atm_normalise_en_majuscules(self):
        data = {**self.atm_data, 'code_atm': 'atm-kin-002', 'nom': 'DAB 2'}
        atm = ATM.objects.create(**data)
        self.assertEqual(atm.code_atm, 'ATM-KIN-002')

    def test_code_atm_unique(self):
        ATM.objects.create(**self.atm_data)
        with self.assertRaises(Exception):
            ATM.objects.create(**{**self.atm_data, 'nom': 'Doublon'})

    def test_agence_peut_avoir_plusieurs_atm(self):
        ATM.objects.create(**self.atm_data)
        ATM.objects.create(**{
            **self.atm_data,
            'nom': 'DAB Gombe Sortie',
            'code_atm': 'ATM-KIN-003',
        })
        self.assertEqual(self.agence.atms.count(), 2)

    def test_est_operational_false_si_maintenance(self):
        atm = ATM.objects.create(**{
            **self.atm_data,
            'statut': StatutATM.MAINTENANCE,
        })
        self.assertFalse(atm.est_operational)

    def test_est_operational_false_si_sans_cash(self):
        atm = ATM.objects.create(**{
            **self.atm_data,
            'cash_disponible': False,
        })
        self.assertFalse(atm.est_operational)


class ValidatorsTests(TestCase):
    """Tests des validateurs métier."""

    def test_validate_code_atm_valide(self):
        validate_code_atm('ATM-KIN-001')

    def test_validate_code_atm_invalide(self):
        with self.assertRaises(ValidationError):
            validate_code_atm('xx')


class ATMServiceTests(TestCase):
    """Tests de la couche service."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence Limete',
            code='RB-KIN-020',
            adresse='2 Avenue Test',
            commune='Limete',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345679',
            email='limete@rawbank.cd',
            localisation=Point(15.35, -4.35, srid=4326),
            capacite_max=30,
        )
        self.atm_disponible = ATM.objects.create(
            agence=self.agence,
            nom='DAB Limete 1',
            code_atm='ATM-LIM-001',
            localisation=Point(15.3501, -4.3501, srid=4326),
            statut=StatutATM.DISPONIBLE,
            cash_disponible=True,
        )
        ATM.objects.create(
            agence=self.agence,
            nom='DAB Limete 2',
            code_atm='ATM-LIM-002',
            localisation=Point(15.3502, -4.3502, srid=4326),
            statut=StatutATM.HORS_SERVICE,
            cash_disponible=False,
        )

    def test_list_by_agence(self):
        atms = ATMService.list_by_agence(self.agence.pk)
        self.assertEqual(atms.count(), 2)

    def test_list_disponibles(self):
        disponibles = ATMService.list_disponibles()
        self.assertEqual(disponibles.count(), 1)
        self.assertEqual(disponibles.first().code_atm, 'ATM-LIM-001')

    def test_get_by_code(self):
        atm = ATMService.get_by_code('atm-lim-001')
        self.assertEqual(atm.nom, 'DAB Limete 1')

    def test_set_statut(self):
        ATMService.set_statut(self.atm_disponible, StatutATM.MAINTENANCE)
        self.atm_disponible.refresh_from_db()
        self.assertEqual(self.atm_disponible.statut, StatutATM.MAINTENANCE)

    def test_set_cash_disponible(self):
        ATMService.set_cash_disponible(self.atm_disponible, False)
        self.atm_disponible.refresh_from_db()
        self.assertFalse(self.atm_disponible.cash_disponible)

    def test_count_by_agence(self):
        self.assertEqual(ATMService.count_by_agence(self.agence.pk), 2)
