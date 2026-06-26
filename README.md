# RawMap

Application Web professionnelle permettant aux clients de **Rawbank** de localiser les agences et DAB (ATM), de connaître leur disponibilité et leur niveau d'affluence grâce à un système IoT basé sur ESP32.

> **Phase actuelle :** MVP fonctionnel — PostgreSQL standard (sans PostGIS/GDAL). La géolocalisation utilise `latitude`/`longitude` et un calcul Haversine côté serveur.

---

## Présentation

RawMap est structuré comme une application Django modulaire, prête à accueillir les développements futurs :

- Gestion des comptes utilisateurs (`accounts`)
- Localisation géographique des agences (`agencies`) via champs `latitude` / `longitude`
- Gestion des DAB (`atm`)
- Suivi de l'affluence (`affluence`)
- Intégration IoT ESP32 (`iot`)
- Notifications (`notifications`)
- Tableau de bord (`dashboard`)
- Couche API REST (`api`) — configuration DRF en place, endpoints à venir
- Utilitaires transverses et pages publiques (`core`)

---

## Technologies

| Composant | Technologie |
|-----------|-------------|
| Langage | Python 3.13+ |
| Framework Web | Django 6.x |
| API | Django REST Framework |
| Géolocalisation | DecimalField lat/lng + Haversine (PostGIS optionnel ultérieurement) |
| Base de données | PostgreSQL |
| Cartographie (frontend) | Leaflet.js *(phases suivantes)* |
| Interface | Bootstrap 5, HTML5, CSS3, JavaScript ES6 |
| Configuration | python-dotenv |

---

## Prérequis

- Python 3.13 ou supérieur
- PostgreSQL 14+ (extension PostGIS **non requise** pour le MVP)

---

## Installation

### 1. Cloner le dépôt et se placer à la racine

```bash
cd RawMap
```

### 2. Créer et activer l'environnement virtuel

**Windows (PowerShell) :**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS :**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` avec vos paramètres (base de données, clé secrète, etc.).

---

## Création de la base PostgreSQL

Se connecter à PostgreSQL en tant que superutilisateur :

```sql
CREATE USER rawmap_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE rawmap OWNER rawmap_user;
GRANT ALL PRIVILEGES ON DATABASE rawmap TO rawmap_user;
```

---

## PostGIS (optionnel — production future)

Pour réactiver GeoDjango et PostGIS plus tard :

1. Installer GDAL/GEOS ([OSGeo4W](https://trac.osgeo.org/osgeo4w/) sur Windows)
2. Activer l'extension dans PostgreSQL :

```sql
\c rawmap
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. Configurer `USE_GEODJANGO=True`, `django.contrib.gis` et `postgis` dans `config/settings/base.py`

---

## Lancement du serveur

Appliquer les migrations Django :

```bash
python manage.py migrate
```

Lancer le serveur de développement :

```bash
python manage.py runserver
```

Accéder à l'application : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

Interface d'administration : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Structure du projet

```
RawMap/
├── config/                     # Projet Django (settings, urls, wsgi)
│   └── settings/
│       ├── base.py             # Paramètres communs
│       ├── development.py      # Développement
│       └── production.py       # Production
├── apps/                       # Applications métier
│   ├── accounts/               # Comptes utilisateurs
│   ├── agencies/               # Agences bancaires (lat/lng)
│   ├── atm/                    # DAB (ATM)
│   ├── affluence/              # Niveaux d'affluence
│   ├── iot/                    # Capteurs ESP32
│   ├── notifications/          # Notifications
│   ├── dashboard/              # Tableau de bord
│   ├── api/                    # Couche API REST (DRF)
│   └── core/                   # Pages publiques, utilitaires
├── static/                     # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                  # Templates Django
│   ├── base.html
│   └── core/
├── media/                      # Fichiers uploadés
├── docs/                       # Documentation technique
├── requirements/               # Dépendances Python
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

Chaque application contient les dossiers préparés pour les phases suivantes :

`services/`, `utils/`, `validators/`, `permissions/`, `serializers/`, `signals/`, `management/`, `tests/` *(selon pertinence)*.

---

## Environnements

| Variable | Description |
|----------|-------------|
| `DJANGO_SETTINGS_MODULE=config.settings` | Développement (par défaut) |
| `DJANGO_SETTINGS_MODULE=config.settings.production` | Production |

---

## Fonctionnalités implémentées

- Modèles de données (agences, DAB, capteurs IoT, affluence)
- Endpoints API REST v1
- Cartographie Leaflet.js
- Simulateur d'affluence (staff)
- Page détail agence avec historique Chart.js

---

## Licence

Projet interne Rawbank — tous droits réservés.
