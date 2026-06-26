"""
Tests unitaires — application agencies.
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.agencies.models import Agence, Horaire, JourSemaine, Service, StatutAgence
from apps.agencies.services import AgenceService, ServiceCatalogue
from apps.agencies.validators import (
    validate_capacite_max,
    validate_code_agence,
    validate_horaires,
    validate_telephone,
)


class AgenceModelTests(TestCase):
    """Tests du modèle Agence."""

    def setUp(self):
        self.agence_data = {
            'nom': 'Agence Gombe',
            'code': 'RB-KIN-001',
            'adresse': '12 Avenue de la Paix',
            'commune': 'Gombe',
            'ville': 'Kinshasa',
            'province': 'Kinshasa',
            'telephone': '+243812345678',
            'email': 'gombe@rawbank.cd',
            'latitude': -4.3217, 'longitude': 15.3222,
            'capacite_max': 50,
            'description': 'Agence principale Gombe',
            'statut': StatutAgence.ACTIF,
        }

    def test_create_agence(self):
        agence = Agence.objects.create(**self.agence_data)
        self.assertEqual(str(agence), 'Agence Gombe (RB-KIN-001)')
        self.assertEqual(agence.statut, StatutAgence.ACTIF)
        self.assertIsNotNone(agence.created_at)

    def test_code_normalise_en_majuscules(self):
        data = {**self.agence_data, 'code': 'rb-kin-002'}
        agence = Agence.objects.create(**data)
        self.assertEqual(agence.code, 'RB-KIN-002')

    def test_code_unique(self):
        Agence.objects.create(**self.agence_data)
        with self.assertRaises(Exception):
            Agence.objects.create(**{**self.agence_data, 'code': 'RB-KIN-001'})


class HoraireModelTests(TestCase):
    """Tests du modèle Horaire."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence Test',
            code='RB-TEST-001',
            adresse='1 Rue Test',
            commune='Commune',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='test@rawbank.cd',
            latitude=-4.3, longitude=15.3,
            capacite_max=30,
        )

    def test_create_horaire(self):
        horaire = Horaire.objects.create(
            agence=self.agence,
            jour=JourSemaine.LUNDI,
            heure_ouverture='08:00',
            heure_fermeture='16:00',
        )
        self.assertIn('Lundi', str(horaire))
        self.assertIn('RB-TEST-001', str(horaire))

    def test_horaire_fermeture_avant_ouverture_invalide(self):
        horaire = Horaire(
            agence=self.agence,
            jour=JourSemaine.MARDI,
            heure_ouverture='16:00',
            heure_fermeture='08:00',
        )
        with self.assertRaises(ValidationError):
            horaire.save()

    def test_horaire_unique_par_jour(self):
        Horaire.objects.create(
            agence=self.agence,
            jour=JourSemaine.LUNDI,
            heure_ouverture='08:00',
            heure_fermeture='16:00',
        )
        with self.assertRaises(Exception):
            Horaire.objects.create(
                agence=self.agence,
                jour=JourSemaine.LUNDI,
                heure_ouverture='09:00',
                heure_fermeture='17:00',
            )


class ServiceModelTests(TestCase):
    """Tests du modèle Service et relation ManyToMany."""

    def test_service_str(self):
        service = Service.objects.create(
            nom='Retrait espèces',
            description='Retrait au guichet',
        )
        self.assertEqual(str(service), 'Retrait espèces')

    def test_agence_services_many_to_many(self):
        agence = Agence.objects.create(
            nom='Agence Test',
            code='RB-TEST-002',
            adresse='2 Rue Test',
            commune='Commune',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345679',
            email='test2@rawbank.cd',
            latitude=-4.3, longitude=15.3,
            capacite_max=20,
        )
        service_a = Service.objects.create(nom='Virement')
        service_b = Service.objects.create(nom='Dépôt')
        agence.services.set([service_a, service_b])
        self.assertEqual(agence.services.count(), 2)
        self.assertIn(agence, service_a.agences.all())


class ValidatorsTests(TestCase):
    """Tests des validateurs métier."""

    def test_validate_telephone_valide(self):
        validate_telephone('+243812345678')
        validate_telephone('0812345678')

    def test_validate_telephone_invalide(self):
        with self.assertRaises(ValidationError):
            validate_telephone('123')

    def test_validate_code_agence_valide(self):
        validate_code_agence('RB-KIN-001')

    def test_validate_code_agence_invalide(self):
        with self.assertRaises(ValidationError):
            validate_code_agence('ab')

    def test_validate_capacite_max(self):
        validate_capacite_max(100)
        with self.assertRaises(ValidationError):
            validate_capacite_max(50_000)

    def test_validate_horaires(self):
        from datetime import time

        validate_horaires(time(8, 0), time(16, 0))
        with self.assertRaises(ValidationError):
            validate_horaires(time(16, 0), time(8, 0))


class AgenceServiceTests(TestCase):
    """Tests de la couche service."""

    def setUp(self):
        self.agence_active = Agence.objects.create(
            nom='Agence Active',
            code='RB-ACT-001',
            adresse='10 Rue A',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0811111111',
            email='active@rawbank.cd',
            latitude=-4.32, longitude=15.32,
            capacite_max=40,
            statut=StatutAgence.ACTIF,
        )
        Agence.objects.create(
            nom='Agence Inactive',
            code='RB-INA-001',
            adresse='20 Rue B',
            commune='Limete',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0822222222',
            email='inactive@rawbank.cd',
            latitude=-4.35, longitude=15.35,
            capacite_max=20,
            statut=StatutAgence.INACTIF,
        )

    def test_list_actives(self):
        actives = AgenceService.list_actives()
        self.assertEqual(actives.count(), 1)
        self.assertEqual(actives.first().code, 'RB-ACT-001')

    def test_get_by_code(self):
        agence = AgenceService.get_by_code('rb-act-001')
        self.assertEqual(agence.nom, 'Agence Active')

    def test_search_by_ville(self):
        resultats = AgenceService.search_by_ville('Kinshasa', actives_only=False)
        self.assertEqual(resultats.count(), 2)

    def test_set_statut(self):
        AgenceService.set_statut(self.agence_active, StatutAgence.INACTIF)
        self.agence_active.refresh_from_db()
        self.assertEqual(self.agence_active.statut, StatutAgence.INACTIF)


class ServiceCatalogueTests(TestCase):
    """Tests du catalogue de services."""

    def test_list_all(self):
        Service.objects.create(nom='Change')
        Service.objects.create(nom='Crédit')
        services = ServiceCatalogue.list_all()
        self.assertEqual(services.count(), 2)
