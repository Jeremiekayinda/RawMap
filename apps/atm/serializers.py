"""
Serializers DRF pour l'application atm.

Prêts pour l'exposition API — aucune route configurée à ce stade.
"""

from rest_framework import serializers

from apps.atm.models import ATM


class ATMSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ATM."""

    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True,
    )
    agence_nom = serializers.CharField(
        source='agence.nom',
        read_only=True,
    )
    agence_code = serializers.CharField(
        source='agence.code',
        read_only=True,
    )
    latitude = serializers.FloatField(
        source='localisation.y',
        read_only=True,
    )
    longitude = serializers.FloatField(
        source='localisation.x',
        read_only=True,
    )
    est_operational = serializers.BooleanField(read_only=True)

    class Meta:
        model = ATM
        fields = [
            'id',
            'agence',
            'agence_nom',
            'agence_code',
            'nom',
            'code_atm',
            'localisation',
            'latitude',
            'longitude',
            'statut',
            'statut_display',
            'cash_disponible',
            'est_operational',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code_atm(self, value):
        return value.strip().upper()
