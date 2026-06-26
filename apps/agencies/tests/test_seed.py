"""
Tests de la commande seed_rawmap.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.affluence.models import Affluence
from apps.agencies.models import Agence, Horaire, Service
from apps.atm.models import ATM


class SeedRawmapCommandTests(TestCase):
    def test_seed_creates_expected_data(self):
        out = StringIO()
        call_command('seed_rawmap', stdout=out)

        self.assertEqual(Agence.objects.count(), 20)
        self.assertEqual(ATM.objects.count(), 40)
        self.assertEqual(Horaire.objects.count(), 120)
        self.assertEqual(Service.objects.count(), 5)
        self.assertEqual(Affluence.objects.count(), 20)
        self.assertIn('[OK] 20 agences créées', out.getvalue())

    def test_seed_is_idempotent(self):
        call_command('seed_rawmap', stdout=StringIO())
        out = StringIO()
        call_command('seed_rawmap', stdout=out)

        self.assertEqual(Agence.objects.count(), 20)
        self.assertEqual(ATM.objects.count(), 40)
        self.assertIn('[OK] 0 agences créées', out.getvalue())
        self.assertIn('déjà peuplée', out.getvalue())
