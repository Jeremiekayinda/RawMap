"""
Serializers DRF pour l'application agencies.

Prêts pour l'exposition API — aucune route configurée à ce stade.
"""

from rest_framework import serializers

from apps.agencies.models import Agence, Horaire, Service
from apps.agencies.validators import validate_horaires


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Service."""

    class Meta:
        model = Service
        fields = ['id', 'nom', 'description']
        read_only_fields = ['id']


class HoraireSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Horaire."""

    jour_display = serializers.CharField(
        source='get_jour_display',
        read_only=True,
    )

    class Meta:
        model = Horaire
        fields = [
            'id',
            'agence',
            'jour',
            'jour_display',
            'heure_ouverture',
            'heure_fermeture',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        heure_ouverture = attrs.get(
            'heure_ouverture',
            getattr(self.instance, 'heure_ouverture', None),
        )
        heure_fermeture = attrs.get(
            'heure_fermeture',
            getattr(self.instance, 'heure_fermeture', None),
        )
        if heure_ouverture and heure_fermeture:
            validate_horaires(heure_ouverture, heure_fermeture)
        return attrs


class AgenceSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Agence avec relations imbriquées."""

    horaires = HoraireSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    service_ids = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='services',
    )
    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True,
    )
    atm_disponibles_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Agence
        fields = [
            'id',
            'nom',
            'code',
            'adresse',
            'commune',
            'ville',
            'province',
            'telephone',
            'email',
            'latitude',
            'longitude',
            'capacite_max',
            'description',
            'photo',
            'statut',
            'statut_display',
            'atm_disponibles_count',
            'services',
            'service_ids',
            'horaires',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.strip().upper()
