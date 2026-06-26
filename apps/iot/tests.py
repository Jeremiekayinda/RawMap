"""
Tests unitaires — application iot.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.agencies.models import Agence
from apps.iot.models import (
    Capteur,
    DirectionPassage,
    ESP32,
    Passage,
    StatutESP32,
    TypeCapteur,
)
from apps.iot.services import CapteurService, ESP32Service, PassageService
from apps.iot.validators import validate_numero_serie


class IoTTestMixin:
    """Fixtures communes pour les tests IoT."""

    @classmethod
    def create_agence(cls):
        return Agence.objects.create(
            nom='Agence Test IoT',
            code='RB-IOT-001',
            adresse='1 Rue Capteur',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='iot@rawbank.cd',
            latitude=-4.32, longitude=15.32,
            capacite_max=50,
        )

    @classmethod
    def create_esp32(cls, agence, numero_serie='ESP32-KIN-00001'):
        return ESP32.objects.create(
            agence=agence,
            numero_serie=numero_serie,
            nom='ESP32 Porte principale',
            firmware_version='1.0.0',
            statut=StatutESP32.ACTIF,
        )

    @classmethod
    def create_capteur(cls, esp32, nom='Capteur Entrée', type_capteur=TypeCapteur.ENTREE):
        return Capteur.objects.create(
            esp32=esp32,
            nom=nom,
            type=type_capteur,
            position='Porte principale',
            actif=True,
        )


class ESP32ModelTests(IoTTestMixin, TestCase):
    """Tests du modèle ESP32."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)

    def test_create_esp32(self):
        self.assertIn('ESP32-KIN-00001', str(self.esp32))
        self.assertIn('RB-IOT-001', str(self.esp32))

    def test_numero_serie_normalise(self):
        esp32 = ESP32.objects.create(
            agence=self.agence,
            numero_serie='esp32-kin-00002',
            nom='ESP32 2',
            firmware_version='1.0.1',
        )
        self.assertEqual(esp32.numero_serie, 'ESP32-KIN-00002')

    def test_agence_peut_avoir_plusieurs_esp32(self):
        self.create_esp32(self.agence, 'ESP32-KIN-00003')
        self.assertEqual(self.agence.esp32s.count(), 2)


class CapteurModelTests(IoTTestMixin, TestCase):
    """Tests du modèle Capteur."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)
        self.capteur_entree = self.create_capteur(self.esp32)

    def test_create_capteur(self):
        self.assertIn('Entrée', str(self.capteur_entree))
        self.assertEqual(self.esp32.capteurs.count(), 1)

    def test_esp32_peut_avoir_plusieurs_capteurs(self):
        self.create_capteur(
            self.esp32,
            nom='Capteur Sortie',
            type_capteur=TypeCapteur.SORTIE,
        )
        self.assertEqual(self.esp32.capteurs.count(), 2)


class PassageModelTests(IoTTestMixin, TestCase):
    """Tests du modèle Passage."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)
        self.capteur_entree = self.create_capteur(self.esp32)
        self.capteur_sortie = self.create_capteur(
            self.esp32,
            nom='Capteur Sortie',
            type_capteur=TypeCapteur.SORTIE,
        )

    def test_enregistrer_passage_entree(self):
        passage = Passage.objects.create(
            esp32=self.esp32,
            capteur=self.capteur_entree,
            direction=DirectionPassage.IN,
            timestamp=timezone.now(),
        )
        self.assertIn('IN', str(passage))

    def test_passage_capteur_incoherent_invalide(self):
        autre_esp32 = self.create_esp32(self.agence, 'ESP32-KIN-99999')
        passage = Passage(
            esp32=autre_esp32,
            capteur=self.capteur_entree,
            direction=DirectionPassage.IN,
            timestamp=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            passage.save()

    def test_passage_direction_incoherente_invalide(self):
        passage = Passage(
            esp32=self.esp32,
            capteur=self.capteur_entree,
            direction=DirectionPassage.OUT,
            timestamp=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            passage.save()


class ValidatorsTests(TestCase):
    """Tests des validateurs métier."""

    def test_validate_numero_serie_valide(self):
        validate_numero_serie('ESP32-KIN-00001')

    def test_validate_numero_serie_invalide(self):
        with self.assertRaises(ValidationError):
            validate_numero_serie('abc')


class PassageServiceTests(IoTTestMixin, TestCase):
    """Tests de la couche service pour les passages et l'affluence."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)
        self.capteur_entree = self.create_capteur(self.esp32)
        self.capteur_sortie = self.create_capteur(
            self.esp32,
            nom='Capteur Sortie',
            type_capteur=TypeCapteur.SORTIE,
        )
        self.maintenant = timezone.now()

    def test_enregistrer_passage(self):
        passage = PassageService.enregistrer_passage(
            self.esp32,
            self.capteur_entree,
            DirectionPassage.IN,
        )
        self.assertIsNotNone(passage.pk)
        self.esp32.refresh_from_db()
        self.assertIsNotNone(self.esp32.derniere_connexion)

    def test_enregistrer_depuis_payload(self):
        passage = PassageService.enregistrer_depuis_payload(
            numero_serie='esp32-kin-00001',
            capteur_id=self.capteur_entree.pk,
            direction=DirectionPassage.IN,
        )
        self.assertEqual(passage.direction, DirectionPassage.IN)

    def test_calculer_affluence(self):
        PassageService.enregistrer_passage(
            self.esp32, self.capteur_entree, DirectionPassage.IN,
        )
        PassageService.enregistrer_passage(
            self.esp32, self.capteur_entree, DirectionPassage.IN,
        )
        PassageService.enregistrer_passage(
            self.esp32, self.capteur_sortie, DirectionPassage.OUT,
        )
        debut = self.maintenant - timedelta(hours=1)
        fin = self.maintenant + timedelta(hours=1)
        resultat = PassageService.calculer_affluence(self.esp32.pk, debut, fin)
        self.assertEqual(resultat['entrees'], 2)
        self.assertEqual(resultat['sorties'], 1)
        self.assertEqual(resultat['affluence_nette'], 1)

    def test_calculer_affluence_agence(self):
        PassageService.enregistrer_passage(
            self.esp32, self.capteur_entree, DirectionPassage.IN,
        )
        debut = self.maintenant - timedelta(hours=1)
        fin = self.maintenant + timedelta(hours=1)
        resultat = PassageService.calculer_affluence_agence(
            self.agence.pk, debut, fin,
        )
        self.assertEqual(resultat['entrees'], 1)
        self.assertEqual(resultat['affluence_nette'], 1)


class ESP32ServiceTests(IoTTestMixin, TestCase):
    """Tests de la couche service ESP32."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)

    def test_get_by_numero_serie(self):
        esp32 = ESP32Service.get_by_numero_serie('esp32-kin-00001')
        self.assertEqual(esp32.pk, self.esp32.pk)

    def test_list_by_agence(self):
        self.assertEqual(ESP32Service.list_by_agence(self.agence.pk).count(), 1)

    def test_enregistrer_connexion(self):
        ESP32Service.enregistrer_connexion(self.esp32, '192.168.1.50')
        self.esp32.refresh_from_db()
        self.assertEqual(self.esp32.adresse_ip, '192.168.1.50')


class CapteurServiceTests(IoTTestMixin, TestCase):
    """Tests de la couche service Capteur."""

    def setUp(self):
        self.agence = self.create_agence()
        self.esp32 = self.create_esp32(self.agence)
        self.create_capteur(self.esp32)

    def test_list_by_esp32(self):
        capteurs = CapteurService.list_by_esp32(self.esp32.pk)
        self.assertEqual(capteurs.count(), 1)
