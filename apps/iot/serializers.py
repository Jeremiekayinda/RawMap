"""
Serializers DRF pour l'application iot.

Prêts pour la réception des données ESP32 — aucune route configurée à ce stade.
"""

from rest_framework import serializers

from apps.iot.models import Capteur, DirectionPassage, ESP32, Passage
from apps.iot.validators import (
    validate_capteur_passage_coherence,
    validate_direction_capteur,
)


class ESP32Serializer(serializers.ModelSerializer):
    """Serializer pour le modèle ESP32."""

    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True,
    )
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    agence_code = serializers.CharField(source='agence.code', read_only=True)

    class Meta:
        model = ESP32
        fields = [
            'id',
            'agence',
            'agence_nom',
            'agence_code',
            'numero_serie',
            'nom',
            'adresse_ip',
            'firmware_version',
            'statut',
            'statut_display',
            'derniere_connexion',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'derniere_connexion', 'created_at', 'updated_at']


class CapteurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Capteur."""

    type_display = serializers.CharField(source='get_type_display', read_only=True)
    esp32_nom = serializers.CharField(source='esp32.nom', read_only=True)

    class Meta:
        model = Capteur
        fields = [
            'id',
            'esp32',
            'esp32_nom',
            'nom',
            'type',
            'type_display',
            'position',
            'actif',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PassageSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement d'un passage IoT."""

    direction_display = serializers.CharField(
        source='get_direction_display',
        read_only=True,
    )
    capteur_nom = serializers.CharField(source='capteur.nom', read_only=True)

    class Meta:
        model = Passage
        fields = [
            'id',
            'esp32',
            'capteur',
            'capteur_nom',
            'direction',
            'direction_display',
            'timestamp',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        esp32 = attrs.get('esp32', getattr(self.instance, 'esp32', None))
        capteur = attrs.get('capteur', getattr(self.instance, 'capteur', None))
        direction = attrs.get(
            'direction',
            getattr(self.instance, 'direction', None),
        )

        if esp32 and capteur:
            validate_capteur_passage_coherence(esp32, capteur)
        if capteur and direction:
            validate_direction_capteur(capteur, direction)
        return attrs


class PassageCreateSerializer(serializers.Serializer):
    """
    Serializer d'entrée pour les payloads ESP32.

    Format simplifié pour la réception des données capteurs.
    """

    numero_serie = serializers.CharField(max_length=50)
    capteur_id = serializers.IntegerField()
    direction = serializers.ChoiceField(choices=DirectionPassage.choices)
    timestamp = serializers.DateTimeField(required=False)
