"""
Validateurs métier pour l'application iot.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

NUMERO_SERIE_REGEX = re.compile(r'^[A-Z0-9][A-Z0-9\-_]{4,49}$')

# Correspondance type capteur → direction attendue
DIRECTION_PAR_TYPE = {
    'entree': 'IN',
    'sortie': 'OUT',
}


def validate_numero_serie(value):
    """
    Valide le numéro de série d'un dispositif ESP32.

    Accepte 5 à 50 caractères alphanumériques, tirets ou underscores.
    """
    normalized = value.strip().upper()
    if not NUMERO_SERIE_REGEX.match(normalized):
        raise ValidationError(
            _(
                'Numéro de série invalide. Utilisez 5 à 50 caractères '
                '(lettres majuscules, chiffres, tirets, underscores).'
            ),
            code='invalid_numero_serie',
        )


def validate_capteur_passage_coherence(esp32, capteur):
    """
    Vérifie que le capteur appartient bien à l'ESP32 du passage.
    """
    if capteur.esp32_id != esp32.pk:
        raise ValidationError(
            _('Le capteur sélectionné n\'appartient pas à cet ESP32.'),
            code='capteur_esp32_incoherent',
        )


def validate_direction_capteur(capteur, direction):
    """
    Vérifie la cohérence entre le type de capteur et la direction du passage.

    Capteur Entrée → direction IN
    Capteur Sortie → direction OUT
    """
    expected = DIRECTION_PAR_TYPE.get(capteur.type)
    if expected and direction != expected:
        raise ValidationError(
            _(
                'Direction incohérente : un capteur de type « %(type)s » '
                'doit enregistrer une direction %(direction)s.'
            ),
            params={
                'type': capteur.get_type_display(),
                'direction': expected,
            },
            code='direction_capteur_incoherente',
        )
