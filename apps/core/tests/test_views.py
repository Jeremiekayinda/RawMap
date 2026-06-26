"""
Tests de l'application core.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.agencies.models import Agence


class HomePageTests(TestCase):
    """Tests de la page d'accueil (carte — accès authentifié)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='homeuser',
            password='TestPass123!',
        )

    def test_home_requires_login(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_home_page_returns_200_when_authenticated(self):
        self.client.login(username='homeuser', password='TestPass123!')
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_contains_project_name(self):
        self.client.login(username='homeuser', password='TestPass123!')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'RawMap')


class AgencyDetailPageTests(TestCase):
    """Tests de la page de détail d'une agence."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='detailuser',
            password='TestPass123!',
        )
        self.agence = Agence.objects.create(
            nom='Agence Détail Test',
            code='RB-DET-001',
            adresse='10 Rue Détail',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='detail@rawbank.cd',
            latitude=-4.32, longitude=15.32,
            capacite_max=50,
        )

    def test_agency_detail_requires_login(self):
        url = reverse('core:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_agency_detail_returns_200(self):
        self.client.login(username='detailuser', password='TestPass123!')
        url = reverse('core:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_agency_detail_contains_agency_name(self):
        self.client.login(username='detailuser', password='TestPass123!')
        url = reverse('core:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Agence Détail Test')
        self.assertContains(response, 'Itinéraire')

    def test_agency_detail_not_found(self):
        self.client.login(username='detailuser', password='TestPass123!')
        url = reverse('core:agency-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
