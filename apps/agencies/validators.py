"""
Validateurs métier pour l'application agencies.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Format international simplifié (+243...) ou local (0...)
TELEPHONE_REGEX = re.compile(r'^(\+\d{1,3}|0)\d{8,14}$')

# Code agence : lettres, chiffres et tirets
CODE_AGENCE_REGEX = re.compile(r'^[A-Z0-9][A-Z0-9\-]{2,19}$')

CAPACITE_MAX = 10_000


def validate_telephone(value):
    """
    Valide le format du numéro de téléphone.

    Accepte les formats internationaux (+243...) et locaux (0...).
    """
    if not TELEPHONE_REGEX.match(value):
        raise ValidationError(
            _('Numéro de téléphone invalide. Exemples : +243812345678, 0812345678.'),
            code='invalid_telephone',
        )


def validate_code_agence(value):
    """
    Valide le code unique d'une agence.

    Doit contenir 3 à 20 caractères alphanumériques majuscules ou tirets.
    """
    normalized = value.strip().upper()
    if not CODE_AGENCE_REGEX.match(normalized):
        raise ValidationError(
            _(
                'Code agence invalide. Utilisez 3 à 20 caractères '
                '(lettres majuscules, chiffres, tirets).'
            ),
            code='invalid_code_agence',
        )


def validate_capacite_max(value):
    """Limite la capacité maximale à une valeur raisonnable."""
    if value > CAPACITE_MAX:
        raise ValidationError(
            _('La capacité maximale ne peut pas dépasser %(max)s personnes.'),
            params={'max': CAPACITE_MAX},
            code='capacite_trop_elevee',
        )


def validate_horaires(heure_ouverture, heure_fermeture):
    """
    Vérifie que l'heure de fermeture est postérieure à l'heure d'ouverture.
    """
    if heure_fermeture <= heure_ouverture:
        raise ValidationError(
            _(
                'L\'heure de fermeture doit être postérieure '
                'à l\'heure d\'ouverture.'
            ),
            code='horaires_invalides',
        )
