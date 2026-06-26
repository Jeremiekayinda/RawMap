"""
Serializers DRF pour l'application affluence.

Prêts pour l'exposition API — aucune route configurée à ce stade.
"""

from rest_framework import serializers

from apps.affluence.models import Affluence, HistoriqueAffluence


class AffluenceSerializer(serializers.ModelSerializer):
    """Serializer pour l'état d'affluence en temps réel."""

    niveau_display = serializers.CharField(
        source='get_niveau_display',
        read_only=True,
    )
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    agence_code = serializers.CharField(source='agence.code', read_only=True)
    capacite_max = serializers.IntegerField(
        source='agence.capacite_max',
        read_only=True,
    )

    class Meta:
        model = Affluence
        fields = [
            'id',
            'agence',
            'agence_nom',
            'agence_code',
            'capacite_max',
            'personnes_presentes',
            'taux_occupation',
            'niveau',
            'niveau_display',
            'derniere_mise_a_jour',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'taux_occupation',
            'niveau',
            'derniere_mise_a_jour',
            'created_at',
            'updated_at',
        ]


class HistoriqueAffluenceSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique d'affluence."""

    niveau_display = serializers.CharField(
        source='get_niveau_display',
        read_only=True,
    )
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    agence_code = serializers.CharField(source='agence.code', read_only=True)

    class Meta:
        model = HistoriqueAffluence
        fields = [
            'id',
            'agence',
            'agence_nom',
            'agence_code',
            'personnes_presentes',
            'taux_occupation',
            'niveau',
            'niveau_display',
            'created_at',
        ]
        read_only_fields = fields


class AffluenceUpdateSerializer(serializers.Serializer):
    """Serializer d'entrée pour la mise à jour d'affluence."""

    personnes_presentes = serializers.IntegerField(min_value=0)
