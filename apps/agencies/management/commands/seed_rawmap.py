"""
Commande de peuplement automatique des données RawMap.

Usage : python manage.py seed_rawmap
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.affluence.models import Affluence
from apps.affluence.services import AffluenceService
from apps.agencies.management.seed_data import (
    AFFLUENCE_PERSONNES,
    AGENCES_KINSHASA,
    HEURES_SAMEDI,
    HEURES_SEMAINE,
    JOURS_OUVERTURE,
    SERVICES,
)
from apps.agencies.models import Agence, Horaire, JourSemaine, Service
from apps.atm.models import ATM, StatutATM


class Command(BaseCommand):
    help = 'Peuple la base avec 20 agences Rawbank à Kinshasa (ATM, horaires, affluence).'

    def handle(self, *args, **options):
        stats = {
            'agences': 0,
            'atms': 0,
            'horaires': 0,
            'services': 0,
            'affluences': 0,
        }

        with transaction.atomic():
            service_objects = self._ensure_service_catalog()
            for index, data in enumerate(AGENCES_KINSHASA):
                agence, created = self._ensure_agence(data)
                if created:
                    stats['agences'] += 1

                stats['horaires'] += self._ensure_horaires(agence)
                stats['services'] += self._link_agence_services(agence, service_objects)
                stats['atms'] += self._ensure_atms(agence, index)
                stats['affluences'] += self._ensure_affluence(
                    agence,
                    AFFLUENCE_PERSONNES[index],
                )

        self._print_summary(stats)

    def _ensure_service_catalog(self) -> list[Service]:
        services = []
        for nom, description in SERVICES:
            service, _ = Service.objects.get_or_create(
                nom=nom,
                defaults={'description': description},
            )
            services.append(service)
        return services

    def _ensure_agence(self, data: dict) -> tuple[Agence, bool]:
        slug = data['commune'].lower().replace(' ', '-')
        defaults = {
            'nom': data['nom'],
            'adresse': data['adresse'],
            'commune': data['commune'],
            'ville': 'Kinshasa',
            'province': 'Kinshasa',
            'telephone': data['telephone'],
            'email': f'agence-{slug}@rawbank.cd',
            'latitude': Decimal(str(data['latitude'])),
            'longitude': Decimal(str(data['longitude'])),
            'capacite_max': data['capacite_max'],
            'statut': data['statut'],
            'description': f"Agence Rawbank située dans la commune de {data['commune']}.",
        }
        return Agence.objects.get_or_create(code=data['code'], defaults=defaults)

    def _ensure_horaires(self, agence: Agence) -> int:
        created_count = 0
        for jour in JOURS_OUVERTURE:
            ouverture, fermeture = (
                HEURES_SAMEDI if jour == JourSemaine.SAMEDI else HEURES_SEMAINE
            )
            _, created = Horaire.objects.get_or_create(
                agence=agence,
                jour=jour,
                defaults={
                    'heure_ouverture': ouverture,
                    'heure_fermeture': fermeture,
                },
            )
            if created:
                created_count += 1
        return created_count

    def _link_agence_services(self, agence: Agence, services: list[Service]) -> int:
        linked = 0
        for service in services:
            if not agence.services.filter(pk=service.pk).exists():
                agence.services.add(service)
                linked += 1
        return linked

    def _ensure_atms(self, agence: Agence, index: int) -> int:
        created_count = 0
        base_lat = float(agence.latitude)
        base_lng = float(agence.longitude)
        offsets = [
            (0.0008, 0.0005),
            (-0.0006, 0.0009),
        ]

        for atm_index, (lat_off, lng_off) in enumerate(offsets, start=1):
            suffix = chr(64 + atm_index)  # A, B
            code = f"ATM-KIN-{index + 1:03d}-{suffix}"
            _, created = ATM.objects.get_or_create(
                code_atm=code,
                defaults={
                    'agence': agence,
                    'nom': f"DAB {agence.commune} {atm_index}",
                    'latitude': Decimal(str(round(base_lat + lat_off, 6))),
                    'longitude': Decimal(str(round(base_lng + lng_off, 6))),
                    'statut': StatutATM.DISPONIBLE,
                    'cash_disponible': True,
                    'description': f"Distributeur automatique — {agence.commune}",
                },
            )
            if created:
                created_count += 1
        return created_count

    def _ensure_affluence(self, agence: Agence, personnes_presentes: int) -> int:
        taux = AffluenceService.calculate_occupancy_rate(
            personnes_presentes,
            agence.capacite_max,
        )
        niveau = AffluenceService.calculate_level(taux)
        _, created = Affluence.objects.get_or_create(
            agence=agence,
            defaults={
                'personnes_presentes': personnes_presentes,
                'taux_occupation': taux,
                'niveau': niveau,
                'derniere_mise_a_jour': timezone.now(),
            },
        )
        return 1 if created else 0

    def _print_summary(self, stats: dict) -> None:
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Peuplement RawMap terminé :'))
        self.stdout.write(self.style.SUCCESS(f"  [OK] {stats['agences']} agences créées"))
        self.stdout.write(self.style.SUCCESS(f"  [OK] {stats['atms']} ATM créés"))
        self.stdout.write(self.style.SUCCESS(f"  [OK] {stats['horaires']} horaires créés"))
        self.stdout.write(
            self.style.SUCCESS(f"  [OK] {stats['services']} services associés"),
        )
        self.stdout.write(
            self.style.SUCCESS(f"  [OK] {stats['affluences']} états d'affluence créés"),
        )
        self.stdout.write('')

        if all(value == 0 for value in stats.values()):
            self.stdout.write(
                self.style.WARNING(
                    'Aucune nouvelle donnée : la base est déjà peuplée.',
                ),
            )
