"""
Administration Django — application atm.
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _

from apps.atm.models import ATM


@admin.register(ATM)
class ATMAdmin(GISModelAdmin):
    """Administration des distributeurs automatiques."""

    list_display = (
        'nom',
        'code_atm',
        'agence',
        'statut',
        'cash_disponible',
        'updated_at',
    )
    list_filter = (
        'statut',
        'cash_disponible',
        'agence',
        'agence__ville',
        'agence__province',
    )
    search_fields = (
        'nom',
        'code_atm',
        'agence__nom',
        'agence__code',
        'description',
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('agence',)
    ordering = ('agence', 'nom')

    fieldsets = (
        (_('Identification'), {
            'fields': ('agence', 'nom', 'code_atm', 'statut', 'cash_disponible'),
        }),
        (_('Localisation'), {
            'fields': ('localisation',),
        }),
        (_('Informations complémentaires'), {
            'fields': ('description',),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
