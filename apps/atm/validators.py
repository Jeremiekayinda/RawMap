"""
Validateurs métier pour l'application atm.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Code ATM : lettres, chiffres et tirets (ex. ATM-KIN-001)
CODE_ATM_REGEX = re.compile(r'^[A-Z0-9][A-Z0-9\-]{2,19}$')


def validate_code_atm(value):
    """
    Valide le code unique d'un distributeur automatique.

    Doit contenir 3 à 20 caractères alphanumériques majuscules ou tirets.
    """
    normalized = value.strip().upper()
    if not CODE_ATM_REGEX.match(normalized):
        raise ValidationError(
            _(
                'Code ATM invalide. Utilisez 3 à 20 caractères '
                '(lettres majuscules, chiffres, tirets).'
            ),
            code='invalid_code_atm',
        )
