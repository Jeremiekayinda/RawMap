"""
Modèles de l'application iot.

Gestion des dispositifs ESP32, capteurs et enregistrement des passages
pour le calcul de l'affluence.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.iot.validators import (
    validate_capteur_passage_coherence,
    validate_direction_capteur,
    validate_numero_serie,
)


class StatutESP32(models.TextChoices):
    """Statuts opérationnels d'un dispositif ESP32."""

    ACTIF = 'actif', _('Actif')
    INACTIF = 'inactif', _('Inactif')
    MAINTENANCE = 'maintenance', _('Maintenance')


class TypeCapteur(models.TextChoices):
    """Type de capteur de passage."""

    ENTREE = 'entree', _('Entrée')
    SORTIE = 'sortie', _('Sortie')


class DirectionPassage(models.TextChoices):
    """Direction d'un passage enregistré."""

    IN = 'IN', _('IN')
    OUT = 'OUT', _('OUT')


class ESP32(models.Model):
    """Dispositif ESP32 installé dans une agence pour la détection de passages."""

    agence = models.ForeignKey(
        'agencies.Agence',
        on_delete=models.CASCADE,
        verbose_name=_('agence'),
        related_name='esp32s',
    )
    numero_serie = models.CharField(
        _('numéro de série'),
        max_length=50,
        unique=True,
        validators=[validate_numero_serie],
        help_text=_('Identifiant unique du microcontrôleur.'),
    )
    nom = models.CharField(_('nom'), max_length=200)
    adresse_ip = models.GenericIPAddressField(
        _('adresse IP'),
        blank=True,
        null=True,
        protocol='both',
    )
    firmware_version = models.CharField(
        _('version firmware'),
        max_length=50,
    )
    statut = models.CharField(
        _('statut'),
        max_length=15,
        choices=StatutESP32.choices,
        default=StatutESP32.ACTIF,
        db_index=True,
    )
    derniere_connexion = models.DateTimeField(
        _('dernière connexion'),
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('ESP32')
        verbose_name_plural = _('ESP32')
        ordering = ['agence', 'nom']
        indexes = [
            models.Index(fields=['statut', 'agence']),
            models.Index(fields=['numero_serie']),
        ]

    def __str__(self):
        return f'{self.nom} ({self.numero_serie}) — {self.agence.code}'

    def save(self, *args, **kwargs):
        if self.numero_serie:
            self.numero_serie = self.numero_serie.strip().upper()
        super().save(*args, **kwargs)


class Capteur(models.Model):
    """Capteur de passage rattaché à un dispositif ESP32."""

    esp32 = models.ForeignKey(
        ESP32,
        on_delete=models.CASCADE,
        verbose_name=_('ESP32'),
        related_name='capteurs',
    )
    nom = models.CharField(_('nom'), max_length=100)
    type = models.CharField(
        _('type'),
        max_length=10,
        choices=TypeCapteur.choices,
    )
    position = models.CharField(
        _('position'),
        max_length=100,
        help_text=_('Emplacement physique du capteur (ex. Porte principale).'),
    )
    actif = models.BooleanField(_('actif'), default=True, db_index=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('capteur')
        verbose_name_plural = _('capteurs')
        ordering = ['esp32', 'nom']
        indexes = [
            models.Index(fields=['esp32', 'actif']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f'{self.nom} ({self.get_type_display()}) — {self.esp32.numero_serie}'


class Passage(models.Model):
    """Enregistrement d'un passage détecté par un capteur ESP32."""

    esp32 = models.ForeignKey(
        ESP32,
        on_delete=models.CASCADE,
        verbose_name=_('ESP32'),
        related_name='passages',
    )
    capteur = models.ForeignKey(
        Capteur,
        on_delete=models.CASCADE,
        verbose_name=_('capteur'),
        related_name='passages',
    )
    direction = models.CharField(
        _('direction'),
        max_length=3,
        choices=DirectionPassage.choices,
    )
    timestamp = models.DateTimeField(
        _('horodatage'),
        db_index=True,
    )

    class Meta:
        verbose_name = _('passage')
        verbose_name_plural = _('passages')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['esp32', 'timestamp']),
            models.Index(fields=['capteur', 'timestamp']),
            models.Index(fields=['direction', 'timestamp']),
        ]

    def __str__(self):
        return (
            f'{self.get_direction_display()} — '
            f'{self.capteur.nom} @ {self.timestamp:%Y-%m-%d %H:%M:%S}'
        )

    def clean(self):
        """Valide la cohérence entre ESP32, capteur et direction."""
        from django.core.exceptions import ValidationError

        super().clean()
        errors = {}

        if self.esp32_id and self.capteur_id:
            try:
                validate_capteur_passage_coherence(self.esp32, self.capteur)
            except ValidationError as exc:
                errors['capteur'] = exc.messages

        if self.capteur_id and self.direction:
            try:
                validate_direction_capteur(self.capteur, self.direction)
            except ValidationError as exc:
                errors['direction'] = exc.messages

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
