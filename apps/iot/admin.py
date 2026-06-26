"""
Administration Django — application iot.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.iot.models import Capteur, ESP32, Passage


class CapteurInline(admin.TabularInline):
    """Inline admin pour les capteurs d'un ESP32."""

    model = Capteur
    extra = 1
    fields = ('nom', 'type', 'position', 'actif')


@admin.register(ESP32)
class ESP32Admin(admin.ModelAdmin):
    """Administration des dispositifs ESP32."""

    list_display = (
        'nom',
        'numero_serie',
        'agence',
        'statut',
        'firmware_version',
        'adresse_ip',
        'derniere_connexion',
        'updated_at',
    )
    list_filter = ('statut', 'agence', 'agence__ville', 'agence__province')
    search_fields = (
        'nom',
        'numero_serie',
        'adresse_ip',
        'agence__nom',
        'agence__code',
    )
    readonly_fields = ('created_at', 'updated_at', 'derniere_connexion')
    autocomplete_fields = ('agence',)
    inlines = [CapteurInline]
    ordering = ('agence', 'nom')

    fieldsets = (
        (_('Identification'), {
            'fields': ('agence', 'nom', 'numero_serie', 'statut'),
        }),
        (_('Connexion'), {
            'fields': ('adresse_ip', 'firmware_version', 'derniere_connexion'),
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Capteur)
class CapteurAdmin(admin.ModelAdmin):
    """Administration des capteurs de passage."""

    list_display = (
        'nom',
        'esp32',
        'type',
        'position',
        'actif',
        'updated_at',
    )
    list_filter = ('type', 'actif', 'esp32', 'esp32__agence')
    search_fields = (
        'nom',
        'position',
        'esp32__nom',
        'esp32__numero_serie',
    )
    autocomplete_fields = ('esp32',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('esp32', 'nom')


@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    """Administration des passages enregistrés."""

    list_display = (
        'timestamp',
        'esp32',
        'capteur',
        'direction',
    )
    list_filter = (
        'direction',
        'esp32',
        'esp32__agence',
        'capteur__type',
    )
    search_fields = (
        'esp32__numero_serie',
        'esp32__nom',
        'capteur__nom',
    )
    autocomplete_fields = ('esp32', 'capteur')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
