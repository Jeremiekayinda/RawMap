"""
Administration Django — application agencies.
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _

from apps.agencies.models import Agence, Horaire, Service


class HoraireInline(admin.TabularInline):
    """Inline admin pour les horaires d'une agence."""

    model = Horaire
    extra = 1
    fields = ('jour', 'heure_ouverture', 'heure_fermeture')


@admin.register(Agence)
class AgenceAdmin(GISModelAdmin):
    """Administration des agences avec carte géographique."""

    list_display = (
        'nom',
        'code',
        'ville',
        'commune',
        'statut',
        'capacite_max',
        'telephone',
        'updated_at',
    )
    list_filter = ('statut', 'province', 'ville')
    search_fields = ('nom', 'code', 'adresse', 'commune', 'ville', 'telephone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('services',)
    inlines = [HoraireInline]
    ordering = ('nom',)

    fieldsets = (
        (_('Identification'), {
            'fields': ('nom', 'code', 'statut'),
        }),
        (_('Coordonnées'), {
            'fields': ('adresse', 'commune', 'ville', 'province', 'telephone', 'email'),
        }),
        (_('Localisation & capacité'), {
            'fields': ('localisation', 'capacite_max'),
        }),
        (_('Informations complémentaires'), {
            'fields': ('description', 'photo', 'services'),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Horaire)
class HoraireAdmin(admin.ModelAdmin):
    """Administration des horaires d'ouverture."""

    list_display = (
        'agence',
        'jour',
        'heure_ouverture',
        'heure_fermeture',
    )
    list_filter = ('jour', 'agence__ville', 'agence__statut')
    search_fields = ('agence__nom', 'agence__code')
    autocomplete_fields = ('agence',)
    ordering = ('agence', 'jour')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Administration du catalogue de services."""

    list_display = ('nom', 'description_short')
    search_fields = ('nom', 'description')
    ordering = ('nom',)

    @admin.display(description=_('description'))
    def description_short(self, obj):
        """Affiche un extrait de la description."""
        if not obj.description:
            return '—'
        return obj.description[:80] + ('…' if len(obj.description) > 80 else '')
