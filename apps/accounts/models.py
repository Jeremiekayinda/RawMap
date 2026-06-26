"""
Modèles de l'application accounts.

Extension du modèle User Django via un profil (téléphone, photo).
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators.validators import validate_telephone


class Profile(models.Model):
    """Profil utilisateur RawMap — complète le modèle User natif."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('utilisateur'),
    )
    telephone = models.CharField(
        _('téléphone'),
        max_length=20,
        blank=True,
        validators=[validate_telephone],
    )
    photo = models.ImageField(
        _('photo'),
        upload_to='accounts/photos/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('profil')
        verbose_name_plural = _('profils')

    def __str__(self):
        return f'Profil de {self.user.get_username()}'
