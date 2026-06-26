# Generated manually for RawMap — application atm

import apps.atm.validators
import apps.agencies.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('agencies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ATM',
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
                ('nom', models.CharField(max_length=200, verbose_name='nom')),
                (
                    'code_atm',
                    models.CharField(
                        help_text='Code unique identifiant le DAB (ex. ATM-KIN-001).',
                        max_length=20,
                        unique=True,
                        validators=[apps.atm.validators.validate_code_atm],
                        verbose_name='code ATM',
                    ),
                ),
                (
                    'latitude',
                    models.DecimalField(
                        decimal_places=6,
                        help_text='Latitude WGS84 (ex. -4.321700).',
                        max_digits=9,
                        validators=[apps.agencies.validators.validate_latitude],
                        verbose_name='latitude',
                    ),
                ),
                (
                    'longitude',
                    models.DecimalField(
                        decimal_places=6,
                        help_text='Longitude WGS84 (ex. 15.322200).',
                        max_digits=9,
                        validators=[apps.agencies.validators.validate_longitude],
                        verbose_name='longitude',
                    ),
                ),
                (
                    'statut',
                    models.CharField(
                        choices=[
                            ('disponible', 'Disponible'),
                            ('hors_service', 'Hors service'),
                            ('maintenance', 'Maintenance'),
                        ],
                        db_index=True,
                        default='disponible',
                        max_length=15,
                        verbose_name='statut',
                    ),
                ),
                (
                    'cash_disponible',
                    models.BooleanField(
                        default=True,
                        help_text='Indique si le distributeur contient des billets.',
                        verbose_name='espèces disponibles',
                    ),
                ),
                (
                    'description',
                    models.TextField(blank=True, verbose_name='description'),
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
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='atms',
                        to='agencies.agence',
                        verbose_name='agence',
                    ),
                ),
            ],
            options={
                'verbose_name': 'ATM',
                'verbose_name_plural': 'ATM',
                'ordering': ['agence', 'nom'],
            },
        ),
        migrations.AddIndex(
            model_name='atm',
            index=models.Index(
                fields=['statut', 'cash_disponible'],
                name='atm_atm_statut_1a2b3c_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='atm',
            index=models.Index(fields=['code_atm'], name='atm_atm_code_at_4d5e6f_idx'),
        ),
        migrations.AddIndex(
            model_name='atm',
            index=models.Index(
                fields=['agence', 'statut'],
                name='atm_atm_agence__7g8h9i_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='atm',
            index=models.Index(
                fields=['latitude', 'longitude'],
                name='atm_atm_lat_lon_idx',
            ),
        ),
    ]
