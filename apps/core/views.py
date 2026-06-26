"""
Vues de l'application core.

Pages authentifiées : accueil (carte) et détail d'agence.
"""

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.agencies.models import Agence
from apps.affluence.services import AffluenceService
from apps.atm.models import ATM
from apps.core.utils.agency_helpers import is_agency_open, sort_horaires


@login_required(login_url='/login/')
def home(request):
    """
    Page d'accueil avec carte Leaflet des agences Rawbank.
    """
    context = {
        'page_title': 'RawMap — Localisation des agences et DAB Rawbank',
    }
    return render(request, 'core/home.html', context)


@login_required(login_url='/login/')
def agency_detail(request, pk):
    """
    Page de détail d'une agence bancaire.

    Affiche les informations complètes, l'affluence en temps réel,
    les horaires, services, DAB et l'historique d'affluence.
    """
    agence = get_object_or_404(
        Agence.objects.prefetch_related('horaires', 'services'),
        pk=pk,
    )

    affluence = AffluenceService.get_affluence(agence)
    atms = ATM.objects.filter(agence=agence).order_by('nom')
    horaires = sort_horaires(agence.horaires.all())
    is_open = is_agency_open(agence)

    historique = list(
        agence.historique_affluence.order_by('created_at')[:30]
    )

    chart_data = {
        'labels': [
            entry.created_at.strftime('%d/%m %H:%M')
            for entry in historique
        ],
        'personnes': [entry.personnes_presentes for entry in historique],
        'taux': [float(entry.taux_occupation) for entry in historique],
    }

    adresse_complete = ', '.join(
        part for part in [agence.adresse, agence.commune, agence.ville, agence.province]
        if part
    )

    latitude = float(agence.latitude)
    longitude = float(agence.longitude)

    context = {
        'page_title': f'{agence.nom} — RawMap',
        'agence': agence,
        'adresse_complete': adresse_complete,
        'affluence': affluence,
        'atms': atms,
        'horaires': horaires,
        'is_open': is_open,
        'latitude': latitude,
        'longitude': longitude,
        'google_maps_url': (
            f'https://www.google.com/maps/dir/?api=1'
            f'&destination={latitude},{longitude}'
        ),
        'chart_data_json': json.dumps(chart_data),
        'has_historique': bool(historique),
    }
    return render(request, 'core/agency_detail.html', context)
