"""
Validateurs métier pour l'application affluence.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_personnes_presentes(value):
    """Vérifie que le nombre de personnes présentes est valide."""
    if value < 0:
        raise ValidationError(
            _('Le nombre de personnes présentes ne peut pas être négatif.'),
            code='personnes_negatives',
        )


def validate_personnes_capacite(personnes_presentes, capacite_max):
    """
    Vérifie que le nombre de personnes ne dépasse pas la capacité maximale.
    """
    validate_personnes_presentes(personnes_presentes)
    if personnes_presentes > capacite_max:
        raise ValidationError(
            _(
                'Le nombre de personnes (%(count)s) dépasse la capacité '
                'maximale de l\'agence (%(max)s).'
            ),
            params={'count': personnes_presentes, 'max': capacite_max},
            code='capacite_depassee',
        )
