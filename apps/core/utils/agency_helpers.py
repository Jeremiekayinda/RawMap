"""
Utilitaires transverses de l'application core.
"""

from datetime import datetime

from apps.agencies.models import JourSemaine

JOUR_ORDER = {choice[0]: index for index, choice in enumerate(JourSemaine.choices)}

# Aligné sur JavaScript : index 0 = dimanche
JOURS_SEMAINE = [
    'dimanche',
    'lundi',
    'mardi',
    'mercredi',
    'jeudi',
    'vendredi',
    'samedi',
]


def sort_horaires(horaires):
    """Trie les horaires du lundi au dimanche."""
    return sorted(horaires, key=lambda h: JOUR_ORDER.get(h.jour, 99))


def is_agency_open(agence):
    """
    Détermine si l'agence est actuellement ouverte selon ses horaires.

    Returns:
        True  — ouverte
        False — fermée
        None  — horaires non renseignés
    """
    horaires = list(agence.horaires.all())
    if not horaires:
        return None

    today = JOURS_SEMAINE[(datetime.now().weekday() + 1) % 7]
    horaire = next((h for h in horaires if h.jour == today), None)
    if horaire is None:
        return False

    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    open_minutes = horaire.heure_ouverture.hour * 60 + horaire.heure_ouverture.minute
    close_minutes = horaire.heure_fermeture.hour * 60 + horaire.heure_fermeture.minute

    return open_minutes <= current_minutes < close_minutes
