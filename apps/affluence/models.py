"""
Modèles de l'application affluence.

Suivi en temps réel de l'affluence et historique par agence.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.affluence.validators import validate_personnes_presentes


class NiveauAffluence(models.TextChoices):
    """Niveaux d'alerte basés sur le taux d'occupation."""

    VERT = 'vert', _('Vert')
    ORANGE = 'orange', _('Orange')
    ROUGE = 'rouge', _('Rouge')


class Affluence(models.Model):
    """État d'affluence en temps réel d'une agence."""

    agence = models.OneToOneField(
        'agencies.Agence',
        on_delete=models.CASCADE,
        verbose_name=_('agence'),
        related_name='affluence',
    )
    personnes_presentes = models.PositiveIntegerField(
        _('personnes présentes'),
        default=0,
        validators=[validate_personnes_presentes],
    )
    taux_occupation = models.DecimalField(
        _('taux d\'occupation (%)'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Calculé automatiquement : (personnes / capacité) × 100.'),
    )
    niveau = models.CharField(
        _('niveau'),
        max_length=10,
        choices=NiveauAffluence.choices,
        default=NiveauAffluence.VERT,
        db_index=True,
    )
    derniere_mise_a_jour = models.DateTimeField(
        _('dernière mise à jour'),
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('affluence')
        verbose_name_plural = _('affluences')
        ordering = ['agence__nom']
        indexes = [
            models.Index(fields=['niveau']),
            models.Index(fields=['derniere_mise_a_jour']),
        ]

    def __str__(self):
        return (
            f'{self.agence.nom} — {self.personnes_presentes} pers. '
            f'({self.taux_occupation}% — {self.get_niveau_display()})'
        )


class HistoriqueAffluence(models.Model):
    """Historique des snapshots d'affluence par agence."""

    agence = models.ForeignKey(
        'agencies.Agence',
        on_delete=models.CASCADE,
        verbose_name=_('agence'),
        related_name='historique_affluence',
    )
    personnes_presentes = models.PositiveIntegerField(
        _('personnes présentes'),
        validators=[validate_personnes_presentes],
    )
    taux_occupation = models.DecimalField(
        _('taux d\'occupation (%)'),
        max_digits=5,
        decimal_places=2,
    )
    niveau = models.CharField(
        _('niveau'),
        max_length=10,
        choices=NiveauAffluence.choices,
        db_index=True,
    )
    created_at = models.DateTimeField(_('enregistré le'), auto_now_add=True)

    class Meta:
        verbose_name = _('historique d\'affluence')
        verbose_name_plural = _('historiques d\'affluence')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agence', 'created_at']),
            models.Index(fields=['niveau', 'created_at']),
        ]

    def __str__(self):
        return (
            f'{self.agence.code} — {self.created_at:%Y-%m-%d %H:%M} — '
            f'{self.personnes_presentes} pers. ({self.get_niveau_display()})'
        )
