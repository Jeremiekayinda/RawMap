"""
Tests unitaires — API REST v1.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.agencies.models import Agence, StatutAgence
from apps.affluence.models import Affluence, NiveauAffluence
from apps.affluence.services import AffluenceService
from apps.affluence.services import AffluenceService
from apps.atm.models import ATM, StatutATM
from apps.iot.models import ESP32, StatutESP32


@override_settings(ROOT_URLCONF='apps.api.test_urls')
class AgenceAPITests(APITestCase):
    """Tests des endpoints /api/v1/agencies/."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence API Test',
            code='RB-API-001',
            adresse='1 Rue API',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='api@rawbank.cd',
            localisation=Point(15.32, -4.32, srid=4326),
            capacite_max=100,
            statut=StatutAgence.ACTIF,
        )

    def test_list_agencies(self):
        """GET /api/v1/agencies/ retourne la liste des agences actives."""
        response = self.client.get(reverse('api-v1:agency-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_agency(self):
        """GET /api/v1/agencies/<id>/ retourne le détail d'une agence."""
        url = reverse('api-v1:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'RB-API-001')

    def test_nearby_agencies(self):
        """GET /api/v1/agencies/nearby/ retourne les agences proches."""
        url = reverse('api-v1:agency-nearby')
        response = self.client.get(url, {
            'latitude': '-4.32',
            'longitude': '15.32',
            'radius': '10',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_nearby_missing_params(self):
        """GET /api/v1/agencies/nearby/ sans paramètres retourne 400."""
        url = reverse('api-v1:agency-nearby')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(ROOT_URLCONF='apps.api.test_urls')
class ATMAPITests(APITestCase):
    """Tests des endpoints /api/v1/atms/."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence ATM API',
            code='RB-API-002',
            adresse='2 Rue API',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345679',
            email='atm@rawbank.cd',
            localisation=Point(15.33, -4.33, srid=4326),
            capacite_max=50,
        )
        self.atm = ATM.objects.create(
            agence=self.agence,
            nom='DAB API',
            code_atm='ATM-API-001',
            localisation=Point(15.3301, -4.3301, srid=4326),
            statut=StatutATM.DISPONIBLE,
            cash_disponible=True,
        )

    def test_list_atms(self):
        """GET /api/v1/atms/ retourne la liste des DAB."""
        response = self.client.get(reverse('api-v1:atm-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_atm(self):
        """GET /api/v1/atms/<id>/ retourne le détail d'un DAB."""
        url = reverse('api-v1:atm-detail', kwargs={'pk': self.atm.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code_atm'], 'ATM-API-001')


@override_settings(ROOT_URLCONF='apps.api.test_urls')
class AffluenceAPITests(APITestCase):
    """Tests des endpoints /api/v1/affluence/."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence Affluence API',
            code='RB-API-003',
            adresse='3 Rue API',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345680',
            email='aff@rawbank.cd',
            localisation=Point(15.34, -4.34, srid=4326),
            capacite_max=100,
        )
        AffluenceService.update_affluence(self.agence, 40)

    def test_list_affluence(self):
        """GET /api/v1/affluence/ retourne la liste des affluences."""
        response = self.client.get(reverse('api-v1:affluence-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_affluence_by_agency(self):
        """GET /api/v1/affluence/<agency_id>/ retourne l'affluence d'une agence."""
        url = reverse(
            'api-v1:affluence-detail',
            kwargs={'agency_id': self.agence.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['personnes_presentes'], 40)
        self.assertEqual(response.data['niveau'], NiveauAffluence.VERT)


@override_settings(ROOT_URLCONF='apps.api.test_urls')
class IoTUpdateAPITests(APITestCase):
    """Tests de l'endpoint POST /api/v1/iot/update/."""

    def setUp(self):
        self.agence = Agence.objects.create(
            nom='Agence IoT API',
            code='RB-API-004',
            adresse='4 Rue API',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345681',
            email='iot@rawbank.cd',
            localisation=Point(15.35, -4.35, srid=4326),
            capacite_max=100,
        )
        self.esp32 = ESP32.objects.create(
            agence=self.agence,
            numero_serie='ESP32-001',
            nom='ESP32 Test API',
            firmware_version='1.0.0',
            statut=StatutESP32.ACTIF,
        )

    def test_iot_update_success(self):
        """POST /api/v1/iot/update/ met à jour l'affluence avec succès."""
        url = reverse('api-v1:iot-update')
        payload = {
            'esp32_serial': 'ESP32-001',
            'agency_id': self.agence.pk,
            'people_count': 18,
            'timestamp': '2026-06-26T10:30:00Z',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(
            response.data['message'],
            'Affluence updated successfully.',
        )

        affluence = Affluence.objects.get(agence=self.agence)
        self.assertEqual(affluence.personnes_presentes, 18)
        self.assertEqual(affluence.taux_occupation, Decimal('18.00'))

    def test_iot_update_esp32_not_found(self):
        """POST /api/v1/iot/update/ retourne 404 si l'ESP32 est inconnu."""
        url = reverse('api-v1:iot-update')
        payload = {
            'esp32_serial': 'ESP32-UNKNOWN',
            'agency_id': self.agence.pk,
            'people_count': 10,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_iot_update_wrong_agency(self):
        """POST /api/v1/iot/update/ retourne 400 si l'ESP32 n'appartient pas à l'agence."""
        url = reverse('api-v1:iot-update')
        payload = {
            'esp32_serial': 'ESP32-001',
            'agency_id': 9999,
            'people_count': 10,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_iot_update_invalid_payload(self):
        """POST /api/v1/iot/update/ retourne 400 pour un payload invalide."""
        url = reverse('api-v1:iot-update')
        response = self.client.post(url, {'people_count': -1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(ROOT_URLCONF='apps.api.test_urls')
class SimulatorAPITests(APITestCase):
    """Tests des endpoints simulateur d'affluence."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True,
        )
        self.client.force_authenticate(user=self.staff_user)
        self.agence = Agence.objects.create(
            nom='Agence Simulateur',
            code='RB-SIM-001',
            adresse='1 Rue Sim',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345690',
            email='sim@rawbank.cd',
            localisation=Point(15.32, -4.32, srid=4326),
            capacite_max=5,
        )

    def test_simulator_entry(self):
        url = reverse('api-v1:simulator-entry', kwargs={'agency_id': self.agence.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['affluence']['personnes_presentes'], 1)

    def test_simulator_exit(self):
        AffluenceService.update_affluence(self.agence, 2)
        url = reverse('api-v1:simulator-exit', kwargs={'agency_id': self.agence.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['affluence']['personnes_presentes'], 1)

    def test_simulator_reset(self):
        AffluenceService.update_affluence(self.agence, 3)
        url = reverse('api-v1:simulator-reset', kwargs={'agency_id': self.agence.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['affluence']['personnes_presentes'], 0)

    def test_simulator_entry_capacite_depassee(self):
        AffluenceService.update_affluence(self.agence, 5)
        url = reverse('api-v1:simulator-entry', kwargs={'agency_id': self.agence.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simulator_requires_staff(self):
        self.client.force_authenticate(user=None)
        url = reverse('api-v1:simulator-entry', kwargs={'agency_id': self.agence.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
