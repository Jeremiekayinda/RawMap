# Generated manually for RawMap — application agencies

import django.core.validators
import apps.agencies.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Service',
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
                    'nom',
                    models.CharField(max_length=100, unique=True, verbose_name='nom'),
                ),
                (
                    'description',
                    models.TextField(blank=True, verbose_name='description'),
                ),
            ],
            options={
                'verbose_name': 'service',
                'verbose_name_plural': 'services',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Agence',
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
                    'code',
                    models.CharField(
                        help_text="Code unique identifiant l'agence (ex. RB-KIN-001).",
                        max_length=20,
                        unique=True,
                        validators=[apps.agencies.validators.validate_code_agence],
                        verbose_name='code',
                    ),
                ),
                ('adresse', models.CharField(max_length=255, verbose_name='adresse')),
                ('commune', models.CharField(max_length=100, verbose_name='commune')),
                ('ville', models.CharField(max_length=100, verbose_name='ville')),
                ('province', models.CharField(max_length=100, verbose_name='province')),
                (
                    'telephone',
                    models.CharField(
                        max_length=20,
                        validators=[apps.agencies.validators.validate_telephone],
                        verbose_name='téléphone',
                    ),
                ),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
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
                    'capacite_max',
                    models.PositiveIntegerField(
                        help_text='Nombre maximum de clients simultanés.',
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            apps.agencies.validators.validate_capacite_max,
                        ],
                        verbose_name='capacité maximale',
                    ),
                ),
                (
                    'description',
                    models.TextField(blank=True, verbose_name='description'),
                ),
                (
                    'photo',
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to='agencies/photos/',
                        verbose_name='photo',
                    ),
                ),
                (
                    'statut',
                    models.CharField(
                        choices=[('actif', 'Actif'), ('inactif', 'Inactif')],
                        db_index=True,
                        default='actif',
                        max_length=10,
                        verbose_name='statut',
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
                    'services',
                    models.ManyToManyField(
                        blank=True,
                        related_name='agences',
                        to='agencies.service',
                        verbose_name='services',
                    ),
                ),
            ],
            options={
                'verbose_name': 'agence',
                'verbose_name_plural': 'agences',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Horaire',
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
                    'jour',
                    models.CharField(
                        choices=[
                            ('lundi', 'Lundi'),
                            ('mardi', 'Mardi'),
                            ('mercredi', 'Mercredi'),
                            ('jeudi', 'Jeudi'),
                            ('vendredi', 'Vendredi'),
                            ('samedi', 'Samedi'),
                            ('dimanche', 'Dimanche'),
                        ],
                        max_length=10,
                        verbose_name='jour',
                    ),
                ),
                (
                    'heure_ouverture',
                    models.TimeField(verbose_name="heure d'ouverture"),
                ),
                (
                    'heure_fermeture',
                    models.TimeField(verbose_name='heure de fermeture'),
                ),
                (
                    'agence',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='horaires',
                        to='agencies.agence',
                        verbose_name='agence',
                    ),
                ),
            ],
            options={
                'verbose_name': 'horaire',
                'verbose_name_plural': 'horaires',
                'ordering': ['agence', 'jour'],
            },
        ),
        migrations.AddIndex(
            model_name='agence',
            index=models.Index(
                fields=['statut', 'ville'],
                name='agencies_ag_statut_8a1b2c_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='agence',
            index=models.Index(fields=['code'], name='agencies_ag_code_3d4e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='agence',
            index=models.Index(
                fields=['latitude', 'longitude'],
                name='agencies_ag_lat_lon_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='horaire',
            constraint=models.UniqueConstraint(
                fields=('agence', 'jour'),
                name='unique_horaire_par_jour',
            ),
        ),
    ]
