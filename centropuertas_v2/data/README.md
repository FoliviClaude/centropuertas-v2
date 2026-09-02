# data/

Rien ici n'est lu par l'application en production — le backend est
Turso (base distante, voir `database.py`). Ce dossier ne contient que
des artefacts locaux, tous exclus de git (`.gitignore`).

- **`db/`** — copie SQLite locale (`centropuertas.db` + `.db-wal` /
  `.db-shm`) et `turso_token.txt`, utilisés par
  `scripts/import_to_turso.ps1` pour la mise en place initiale ou une
  restauration de la base Turso. Pas touché par l'app en fonctionnement
  normal.
- **`backups/`** — dumps SQL (`dump_centropuertas.sql`).
- **`exports/`** — exports CSV/JSON ponctuels des tables.
  ⚠️ `technicians.csv` / `technicians.json` peuvent contenir des hash
  et sels de mots de passe : à ne jamais partager ni committer.
