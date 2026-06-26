# Generated manually for RawMap — application iot

import apps.iot.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('agencies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ESP32',
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
                    'numero_serie',
                    models.CharField(
                        help_text='Identifiant unique du microcontrôleur.',
                        max_length=50,
                        unique=True,
                        validators=[apps.iot.validators.validate_numero_serie],
                        verbose_name='numéro de série',
                    ),
                ),
                ('nom', models.CharField(max_length=200, verbose_name='nom')),
                (
                    'adresse_ip',
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        protocol='both',
                        verbose_name='adresse IP',
                    ),
                ),
                (
                    'firmware_version',
                    models.CharField(max_length=50, verbose_name='version firmware'),
                ),
                (
                    'statut',
                    models.CharField(
                        choices=[
                            ('actif', 'Actif'),
                            ('inactif', 'Inactif'),
                            ('maintenance', 'Maintenance'),
                        ],
                        db_index=True,
                        default='actif',
                        max_length=15,
                        verbose_name='statut',
                    ),
                ),
                (
                    'derniere_connexion',
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name='dernière connexion',
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
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='esp32s',
                        to='agencies.agence',
                        verbose_name='agence',
                    ),
                ),
            ],
            options={
                'verbose_name': 'ESP32',
                'verbose_name_plural': 'ESP32',
                'ordering': ['agence', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='Capteur',
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
                ('nom', models.CharField(max_length=100, verbose_name='nom')),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('entree', 'Entrée'),
                            ('sortie', 'Sortie'),
                        ],
                        max_length=10,
                        verbose_name='type',
                    ),
                ),
                (
                    'position',
                    models.CharField(
                        help_text='Emplacement physique du capteur (ex. Porte principale).',
                        max_length=100,
                        verbose_name='position',
                    ),
                ),
                (
                    'actif',
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        verbose_name='actif',
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
                    'esp32',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='capteurs',
                        to='iot.esp32',
                        verbose_name='ESP32',
                    ),
                ),
            ],
            options={
                'verbose_name': 'capteur',
                'verbose_name_plural': 'capteurs',
                'ordering': ['esp32', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='Passage',
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
                    'direction',
                    models.CharField(
                        choices=[('IN', 'IN'), ('OUT', 'OUT')],
                        max_length=3,
                        verbose_name='direction',
                    ),
                ),
                (
                    'timestamp',
                    models.DateTimeField(db_index=True, verbose_name='horodatage'),
                ),
                (
                    'capteur',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='passages',
                        to='iot.capteur',
                        verbose_name='capteur',
                    ),
                ),
                (
                    'esp32',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='passages',
                        to='iot.esp32',
                        verbose_name='ESP32',
                    ),
                ),
            ],
            options={
                'verbose_name': 'passage',
                'verbose_name_plural': 'passages',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='esp32',
            index=models.Index(
                fields=['statut', 'agence'],
                name='iot_esp32_statut_1a2b3c_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='esp32',
            index=models.Index(
                fields=['numero_serie'],
                name='iot_esp32_numero__4d5e6f_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='capteur',
            index=models.Index(
                fields=['esp32', 'actif'],
                name='iot_capteur_esp32_i_7g8h9i_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='capteur',
            index=models.Index(fields=['type'], name='iot_capteur_type_0j1k2l_idx'),
        ),
        migrations.AddIndex(
            model_name='passage',
            index=models.Index(
                fields=['esp32', 'timestamp'],
                name='iot_passage_esp32_t_3m4n5o_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='passage',
            index=models.Index(
                fields=['capteur', 'timestamp'],
                name='iot_passage_capteur_6p7q8r_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='passage',
            index=models.Index(
                fields=['direction', 'timestamp'],
                name='iot_passage_directi_9s0t1u_idx',
            ),
        ),
    ]
