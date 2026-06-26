"""
Administration Django — application affluence.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.affluence.models import Affluence, HistoriqueAffluence


@admin.register(Affluence)
class AffluenceAdmin(admin.ModelAdmin):
    """Administration de l'affluence en temps réel."""

    list_display = (
        'agence',
        'personnes_presentes',
        'taux_occupation',
        'niveau',
        'derniere_mise_a_jour',
        'updated_at',
    )
    list_filter = ('niveau', 'agence__ville', 'agence__province')
    search_fields = (
        'agence__nom',
        'agence__code',
        'agence__ville',
    )
    readonly_fields = (
        'taux_occupation',
        'niveau',
        'derniere_mise_a_jour',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('agence',)
    ordering = ('agence__nom',)

    fieldsets = (
        (_('Agence'), {
            'fields': ('agence',),
        }),
        (_('Affluence'), {
            'fields': (
                'personnes_presentes',
                'taux_occupation',
                'niveau',
                'derniere_mise_a_jour',
            ),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(HistoriqueAffluence)
class HistoriqueAffluenceAdmin(admin.ModelAdmin):
    """Administration de l'historique d'affluence."""

    list_display = (
        'agence',
        'personnes_presentes',
        'taux_occupation',
        'niveau',
        'created_at',
    )
    list_filter = ('niveau', 'agence', 'agence__ville')
    search_fields = (
        'agence__nom',
        'agence__code',
    )
    readonly_fields = (
        'agence',
        'personnes_presentes',
        'taux_occupation',
        'niveau',
        'created_at',
    )
    autocomplete_fields = ('agence',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
