# Centropuertas v2

Application de gestion des rapports d'intervention (*partes de
trabajo*) pour les techniciens Centropuertas : saisie du temps de
travail, heures supplémentaires, indemnités, historique, tableaux de
bord (technicien et admin), export PDF/Excel.

## Stack

- [Streamlit](https://streamlit.io) — interface web.
- [Turso](https://turso.tech) (libSQL) — base de données partagée entre
  postes (voir `database.py` : pas de SQLite local en production).
- Python 3.12+

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

Copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml`
et renseigner `TURSO_URL` / `TURSO_AUTH_TOKEN` (voir ce fichier pour le
détail — jamais versionné).

## Lancer l'app

```
streamlit run app.py
```

## Tests et qualité de code

```
pytest
ruff check .
black --check .
```

## Structure du projet

| Chemin | Rôle |
|---|---|
| `app.py` | Point d'entrée, routage entre sections, auth, sidebar. |
| `auth.py` | Authentification (login/logout, hash des mots de passe). |
| `database.py` | Tout l'accès aux données (Turso). |
| `locales.py` | Traductions multi-langue. |
| `pages_app/` | Un module par écran (dashboard, historial, ajustes...). |
| `utils/` | Fonctions pures réutilisées (calculos, export PDF/Excel, PWA, styling). |
| `assets/` | Logo de l'application. |
| `static/` | Fichiers servis tels quels (manifest PWA, service worker, icônes). |
| `data/` | Artefacts locaux uniquement (voir `data/README.md`) — jamais lus par l'app. |
| `scripts/` | Scripts d'exploitation (migration vers Turso). |
| `tests/` | Tests unitaires (pytest). |

## Déploiement

Configuré pour Streamlit Community Cloud (voir les commentaires dans
`.streamlit/config.toml`).

## Migration vers Turso

`scripts/import_to_turso.ps1` importe une base SQLite locale
(`data/db/centropuertas.db`) vers Turso — utilisé uniquement pour la
mise en place initiale ou une restauration, pas dans le flux normal.
À lancer soi-même dans un terminal (le script contient des secrets qui
ne doivent jamais transiter par un assistant IA — voir son en-tête).
