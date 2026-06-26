"""
Modèles de l'application agencies.

Gestion des agences bancaires Rawbank, de leurs horaires et services.

Note MVP : coordonnées stockées en latitude/longitude (DecimalField).
Migration future possible vers PointField PostGIS sans changer la logique métier.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from apps.agencies.validators import (
    validate_capacite_max,
    validate_code_agence,
    validate_horaires,
    validate_latitude,
    validate_longitude,
    validate_telephone,
)


class StatutAgence(models.TextChoices):
    """Statuts possibles d'une agence."""

    ACTIF = 'actif', _('Actif')
    INACTIF = 'inactif', _('Inactif')


class JourSemaine(models.TextChoices):
    """Jours de la semaine pour les horaires d'ouverture."""

    LUNDI = 'lundi', _('Lundi')
    MARDI = 'mardi', _('Mardi')
    MERCREDI = 'mercredi', _('Mercredi')
    JEUDI = 'jeudi', _('Jeudi')
    VENDREDI = 'vendredi', _('Vendredi')
    SAMEDI = 'samedi', _('Samedi')
    DIMANCHE = 'dimanche', _('Dimanche')


class Service(models.Model):
    """Service proposé par une ou plusieurs agences."""

    nom = models.CharField(
        _('nom'),
        max_length=100,
        unique=True,
    )
    description = models.TextField(
        _('description'),
        blank=True,
    )

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Agence(models.Model):
    """Agence bancaire Rawbank avec localisation géographique."""

    nom = models.CharField(_('nom'), max_length=200)
    code = models.CharField(
        _('code'),
        max_length=20,
        unique=True,
        validators=[validate_code_agence],
        help_text=_('Code unique identifiant l\'agence (ex. RB-KIN-001).'),
    )
    adresse = models.CharField(_('adresse'), max_length=255)
    commune = models.CharField(_('commune'), max_length=100)
    ville = models.CharField(_('ville'), max_length=100)
    province = models.CharField(_('province'), max_length=100)
    telephone = models.CharField(
        _('téléphone'),
        max_length=20,
        validators=[validate_telephone],
    )
    email = models.EmailField(_('email'))
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        validators=[validate_latitude],
        help_text=_('Latitude WGS84 (ex. -4.321700).'),
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        validators=[validate_longitude],
        help_text=_('Longitude WGS84 (ex. 15.322200).'),
    )
    capacite_max = models.PositiveIntegerField(
        _('capacité maximale'),
        validators=[MinValueValidator(1), validate_capacite_max],
        help_text=_('Nombre maximum de clients simultanés.'),
    )
    description = models.TextField(_('description'), blank=True)
    photo = models.ImageField(
        _('photo'),
        upload_to='agencies/photos/',
        blank=True,
        null=True,
    )
    statut = models.CharField(
        _('statut'),
        max_length=10,
        choices=StatutAgence.choices,
        default=StatutAgence.ACTIF,
        db_index=True,
    )
    services = models.ManyToManyField(
        Service,
        verbose_name=_('services'),
        related_name='agences',
        blank=True,
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('agence')
        verbose_name_plural = _('agences')
        ordering = ['nom']
        indexes = [
            models.Index(fields=['statut', 'ville']),
            models.Index(fields=['code']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f'{self.nom} ({self.code})'

    def clean(self):
        """Normalise le code agence avant validation."""
        super().clean()
        if self.code:
            self.code = self.code.strip().upper()

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class Horaire(models.Model):
    """Horaire d'ouverture d'une agence pour un jour donné."""

    agence = models.ForeignKey(
        Agence,
        on_delete=models.CASCADE,
        verbose_name=_('agence'),
        related_name='horaires',
    )
    jour = models.CharField(
        _('jour'),
        max_length=10,
        choices=JourSemaine.choices,
    )
    heure_ouverture = models.TimeField(_('heure d\'ouverture'))
    heure_fermeture = models.TimeField(_('heure de fermeture'))

    class Meta:
        verbose_name = _('horaire')
        verbose_name_plural = _('horaires')
        ordering = ['agence', 'jour']
        constraints = [
            models.UniqueConstraint(
                fields=['agence', 'jour'],
                name='unique_horaire_par_jour',
            ),
        ]

    def __str__(self):
        return (
            f'{self.agence.code} — {self.get_jour_display()} '
            f'({self.heure_ouverture:%H:%M} - {self.heure_fermeture:%H:%M})'
        )

    def clean(self):
        """Validation métier des plages horaires."""
        from django.core.exceptions import ValidationError

        super().clean()
        if self.heure_ouverture and self.heure_fermeture:
            try:
                validate_horaires(self.heure_ouverture, self.heure_fermeture)
            except ValidationError as exc:
                raise ValidationError({'heure_fermeture': exc.messages}) from exc

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
