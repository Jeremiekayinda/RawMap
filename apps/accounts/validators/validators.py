"""
Validateurs pour l'application accounts.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TELEPHONE_REGEX = re.compile(r'^(\+\d{1,3}|0)\d{8,14}$')


def validate_telephone(value: str) -> None:
    """Valide le format du numéro de téléphone (international ou local)."""
    if not TELEPHONE_REGEX.match(value.strip()):
        raise ValidationError(
            _('Numéro de téléphone invalide. Exemples : +243812345678, 0812345678.'),
            code='invalid_telephone',
        )
