# Generated manually for RawMap — application affluence

import apps.affluence.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('agencies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Affluence',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'personnes_presentes',
                    models.PositiveIntegerField(
                        default=0,
                        validators=[apps.affluence.validators.validate_personnes_presentes],
                        verbose_name='personnes présentes',
                    ),
                ),
                (
                    'taux_occupation',
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text='Calculé automatiquement : (personnes / capacité) × 100.',
                        max_digits=5,
                        verbose_name="taux d'occupation (%)",
                    ),
                ),
                (
                    'niveau',
                    models.CharField(
                        choices=[
                            ('vert', 'Vert'),
                            ('orange', 'Orange'),
                            ('rouge', 'Rouge'),
                        ],
                        db_index=True,
                        default='vert',
                        max_length=10,
                        verbose_name='niveau',
                    ),
                ),
                (
                    'derniere_mise_a_jour',
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name='dernière mise à jour',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='créé le'),
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True, verbose_name='modifié le'),
                ),
                (
                    'agence',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='affluence',
                        to='agencies.agence',
                        verbose_name='agence',
                    ),
                ),
            ],
            options={
                'verbose_name': 'affluence',
                'verbose_name_plural': 'affluences',
                'ordering': ['agence__nom'],
            },
        ),
        migrations.CreateModel(
            name='HistoriqueAffluence',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'personnes_presentes',
                    models.PositiveIntegerField(
                        validators=[apps.affluence.validators.validate_personnes_presentes],
                        verbose_name='personnes présentes',
                    ),
                ),
                (
                    'taux_occupation',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        verbose_name="taux d'occupation (%)",
                    ),
                ),
                (
                    'niveau',
                    models.CharField(
                        choices=[
                            ('vert', 'Vert'),
                            ('orange', 'Orange'),
                            ('rouge', 'Rouge'),
                        ],
                        db_index=True,
                        max_length=10,
                        verbose_name='niveau',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='enregistré le'),
                ),
                (
                    'agence',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='historique_affluence',
                        to='agencies.agence',
                        verbose_name='agence',
                    ),
                ),
            ],
            options={
                'verbose_name': "historique d'affluence",
                'verbose_name_plural': "historiques d'affluence",
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='affluence',
            index=models.Index(fields=['niveau'], name='affluence_a_niveau_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='affluence',
            index=models.Index(
                fields=['derniere_mise_a_jour'],
                name='affluence_a_dernier_4d5e6f_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='historiqueaffluence',
            index=models.Index(
                fields=['agence', 'created_at'],
                name='affluence_h_agence__7g8h9i_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='historiqueaffluence',
            index=models.Index(
                fields=['niveau', 'created_at'],
                name='affluence_h_niveau_0j1k2l_idx',
            ),
        ),
    ]
