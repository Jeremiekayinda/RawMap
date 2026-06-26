"""
Serializers DRF pour la couche API (v1).

Réutilise les serializers métier et expose les payloads spécifiques à l'API.
"""

from rest_framework import serializers

from apps.agencies.serializers import AgenceSerializer
from apps.affluence.serializers import AffluenceSerializer
from apps.atm.serializers import ATMSerializer


class AgenceListSerializer(AgenceSerializer):
    """Serializer de liste/détail pour les agences bancaires."""

    class Meta(AgenceSerializer.Meta):
        read_only_fields = AgenceSerializer.Meta.read_only_fields


class AgenceNearbySerializer(AgenceSerializer):
    """Serializer enrichi pour la recherche géographique d'agences."""

    distance = serializers.FloatField(
        read_only=True,
        help_text='Distance en mètres par rapport au point de recherche.',
    )

    class Meta(AgenceSerializer.Meta):
        fields = AgenceSerializer.Meta.fields + ['distance']
        read_only_fields = AgenceSerializer.Meta.read_only_fields


class ATMListSerializer(ATMSerializer):
    """Serializer de liste/détail pour les distributeurs automatiques."""

    class Meta(ATMSerializer.Meta):
        read_only_fields = ATMSerializer.Meta.read_only_fields


class AffluenceListSerializer(AffluenceSerializer):
    """Serializer pour l'affluence en temps réel."""

    class Meta(AffluenceSerializer.Meta):
        read_only_fields = AffluenceSerializer.Meta.read_only_fields


class IoTUpdateSerializer(serializers.Serializer):
    """
    Payload d'entrée pour la mise à jour IoT → affluence.

    Exemple :
        {
            "esp32_serial": "ESP32-001",
            "agency_id": 1,
            "people_count": 18,
            "timestamp": "2026-06-26T10:30:00Z"
        }
    """

    esp32_serial = serializers.CharField(max_length=50)
    agency_id = serializers.IntegerField(min_value=1)
    people_count = serializers.IntegerField(min_value=0)
    timestamp = serializers.DateTimeField(required=False)
