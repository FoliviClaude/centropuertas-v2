# Centropuertas v2

Application interne Streamlit de gestion des rapports d'intervention
(*partes de trabajo*) pour les techniciens Centropuertas.

## Commandes

```
streamlit run app.py          # lancer l'app
pytest                        # tests unitaires (utils/, à étendre)
ruff check .                  # lint
black --check .               # formatage
pip install -r requirements-dev.txt   # dépendances (runtime + dev)
```

## Architecture

- `app.py` — point d'entrée, routage entre sections, auth, sidebar.
  Responsabilités limitées à ça : la logique de chaque écran vit dans
  `pages_app/`, l'accès aux données dans `database.py`,
  l'authentification dans `auth.py`, les traductions dans `locales.py`.
- `database.py` — **tout** l'accès aux données passe par ce module.
  Backend = **Turso (libSQL distant)**, jamais de SQLite local en
  runtime — plusieurs techniciens partagent la même base en temps réel.
- `pages_app/` — un module par écran (dashboard, dashboard_admin,
  historial, nuevo_parte, ajustes, referencias).
- `utils/` — fonctions réutilisées : `calculos.py` (pur, sans
  Streamlit ni SQL — voir `tests/test_calculos.py`), `pdf_export.py`,
  `excel_export.py`, `pwa.py`, `styling.py`.
- `data/` — artefacts locaux uniquement, jamais lus par l'app (voir
  `data/README.md`) : `db/` (copie SQLite + jeton Turso pour
  `scripts/import_to_turso.ps1`), `backups/` (dumps SQL), `exports/`
  (CSV/JSON ponctuels — `technicians.*` peut contenir des hash de mots
  de passe, ne jamais committer ni lire à la légère).

## Conventions du projet

- Docstrings et commentaires en français, expliquant le POURQUOI (pas
  juste le quoi) — garder ce style dans les nouveaux fichiers.
- Résolution de chemins toujours via
  `Path(__file__).resolve().parent` (voir `app.py`,
  `utils/pdf_export.py`) — jamais de chemin relatif au cwd.
- Identifiants toujours via `st.secrets`
  (`.streamlit/secrets.toml`, non versionné — copier
  `.streamlit/secrets.toml.example`), jamais codés en dur.
- Mots de passe : uniquement hachés + salés (voir `database.py`),
  jamais en clair.
- `scripts/import_to_turso.ps1` manipule des secrets et est fait pour
  être lancé par l'utilisateur lui-même dans un terminal, pas via un
  assistant IA (voir l'en-tête du script).
