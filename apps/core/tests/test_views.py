"""
Tests de l'application core.
"""

from django.contrib.gis.geos import Point
from django.test import Client, TestCase
from django.urls import reverse

from apps.agencies.models import Agence


class HomePageTests(TestCase):
    """Tests structurels de la page d'accueil (sans logique métier)."""

    def setUp(self):
        self.client = Client()

    def test_home_page_returns_200(self):
        """La page d'accueil doit répondre avec un statut HTTP 200."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_contains_project_name(self):
        """La page d'accueil doit afficher le nom du projet."""
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'RawMap')


class AgencyDetailPageTests(TestCase):
    """Tests de la page de détail d'une agence."""

    def setUp(self):
        self.client = Client()
        self.agence = Agence.objects.create(
            nom='Agence Détail Test',
            code='RB-DET-001',
            adresse='10 Rue Détail',
            commune='Gombe',
            ville='Kinshasa',
            province='Kinshasa',
            telephone='0812345678',
            email='detail@rawbank.cd',
            localisation=Point(15.32, -4.32, srid=4326),
            capacite_max=50,
        )

    def test_agency_detail_returns_200(self):
        url = reverse('core:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_agency_detail_contains_agency_name(self):
        url = reverse('core:agency-detail', kwargs={'pk': self.agence.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Agence Détail Test')
        self.assertContains(response, 'Itinéraire')

    def test_agency_detail_not_found(self):
        url = reverse('core:agency-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
