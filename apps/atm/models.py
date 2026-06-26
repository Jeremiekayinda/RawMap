"""
Modèles de l'application atm.

Gestion des distributeurs automatiques (DAB/ATM) rattachés aux agences.
"""

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from apps.atm.validators import validate_code_atm


class StatutATM(models.TextChoices):
    """Statuts opérationnels d'un distributeur automatique."""

    DISPONIBLE = 'disponible', _('Disponible')
    HORS_SERVICE = 'hors_service', _('Hors service')
    MAINTENANCE = 'maintenance', _('Maintenance')


class ATM(models.Model):
    """Distributeur automatique de billets rattaché à une agence."""

    agence = models.ForeignKey(
        'agencies.Agence',
        on_delete=models.CASCADE,
        verbose_name=_('agence'),
        related_name='atms',
    )
    nom = models.CharField(_('nom'), max_length=200)
    code_atm = models.CharField(
        _('code ATM'),
        max_length=20,
        unique=True,
        validators=[validate_code_atm],
        help_text=_('Code unique identifiant le DAB (ex. ATM-KIN-001).'),
    )
    localisation = models.PointField(
        _('localisation'),
        geography=True,
        srid=4326,
        help_text=_('Coordonnées GPS (longitude, latitude) — SRID 4326.'),
    )
    statut = models.CharField(
        _('statut'),
        max_length=15,
        choices=StatutATM.choices,
        default=StatutATM.DISPONIBLE,
        db_index=True,
    )
    cash_disponible = models.BooleanField(
        _('espèces disponibles'),
        default=True,
        help_text=_('Indique si le distributeur contient des billets.'),
    )
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('ATM')
        verbose_name_plural = _('ATM')
        ordering = ['agence', 'nom']
        indexes = [
            models.Index(fields=['statut', 'cash_disponible']),
            models.Index(fields=['code_atm']),
            models.Index(fields=['agence', 'statut']),
        ]

    def __str__(self):
        return f'{self.nom} ({self.code_atm}) — {self.agence.code}'

    def clean(self):
        """Normalise le code ATM avant validation."""
        super().clean()
        if self.code_atm:
            self.code_atm = self.code_atm.strip().upper()

    def save(self, *args, **kwargs):
        if self.code_atm:
            self.code_atm = self.code_atm.strip().upper()
        super().save(*args, **kwargs)

    @property
    def est_operational(self):
        """Indique si le DAB est utilisable par les clients."""
        return (
            self.statut == StatutATM.DISPONIBLE
            and self.cash_disponible
        )
