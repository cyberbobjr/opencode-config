# ADR-0001 — Stockage du kanban : fichiers JSON → SQLite local

- **Statut** : Proposée (non implémentée)
- **Date** : 2026-07-03
- **Décideurs** : Benjamin M.
- **Repo** : `.opencode/` (`cyberbobjr/opencode-config`) — premier ADR de ce dépôt.
- **Lié** : `JIRA.md` (l'intégration JIRA introduit un `sync_state` SQLite ; cet ADR unifie le stockage en amont).

## Contexte

Le serveur kanban (`.opencode/kanban/server.py`) persiste les User Stories en **72 fichiers `user-stories/*.json`** (~1,2 Mo). État actuel :

- **Emplacement** : le dossier `user-stories/` est résolu par `find_stories_dir()` **à la racine de `news-briefing-saas`** — un projet **indépendant** de `.opencode/`. Les données de l'outil polluent l'arborescence d'une autre application.
- **Versionnement** : `user-stories/` est **déjà gitignoré** dans le repo principal (0 fichier tracké). C'est donc déjà un **état local, non versionné, par machine**.
- **Accès** : ~10 fonctions / ~92 lignes touchant le filesystem — `load_all`, `load_one`, `save_one`, `delete_one`, `story_file`, `_load_from_disk`, `_disk_mtime`, `bump_version`, `_read_version`, `stats` — consommées par les **9 outils MCP**, l'**API REST**, le **dashboard** et le flux **SSE** (`/api/events` via `bump_version`).
- **Complexité accidentelle** : verrous `fcntl` par fichier, `glob("*.json")` + rescan à chaque `load_all`, et un cache maison invalidé par `version + mtime`.

Deux pressions rendent le sujet mûr **maintenant** :

1. **Découplage projets** — les données du kanban n'ont rien à faire dans le repo de `news-briefing-saas`.
2. **Intégration JIRA** (`JIRA.md`) — elle introduira une table `sync_state` en **SQLite**. Garder les stories en JSON créerait un **dual-write inter-technos** (JSON pour les stories + SQLite pour `sync_state`), non transactionnel, au moment critique « créer l'US locale sur trigger JIRA ».

## Décision

Migrer le stockage du kanban vers **une seule base SQLite locale** dans `.opencode/kanban/` (ex. `kanban.db`), **gitignorée**, **derrière le seam de stockage existant**.

1. **Base unique, locale, gitignorée.** `kanban/*.db` (+ `-wal`/`-shm`/`-journal`) au `.gitignore` de `.opencode/`. L'état kanban est **local par dev et réhydratable** (cohérent avec le modèle JIRA : JIRA = vérité partagée, kanban = espace de travail local privé).

2. **Refacto iso-comportement, borné au seam.** Réimplémenter les ~10 fonctions d'I/O au-dessus de SQLite sans changer leur signature. Les 9 outils MCP, l'API REST et le dashboard n'ont **pas** à changer.

3. **Une base, deux tables (à terme).** `stories` et (plus tard) `sync_state` (JIRA) dans **le même fichier** → la création d'US-sur-trigger devient **transactionnelle**. C'est la raison de faire cet ADR **avant** l'intégration JIRA.

4. **Script de migration one-shot.** Importer les 72 JSON existants → lignes SQLite, avec **backup** des JSON avant bascule. Réversible.

5. **`bump_version` reporté en base.** Le live-refresh du dashboard (SSE) s'appuie aujourd'hui sur `version + mtime` ; le remplacer par un compteur en table (ou `PRAGMA data_version`).

6. **Colonnes vs blob.** Champs de requête/tri (`id`, `title`, `status`, `phase`, `priority`, `updated_at`) en **colonnes indexées** ; le reste de la story (ACs, `tdd`, `qa`, `secops_report`, `history`…) en **blob JSON** dans une colonne `data`. Le mode `compact` de `list_stories` devient un simple `SELECT` de colonnes.

## Conséquences

### Positives
- **Découplage projets** : les données du kanban quittent la racine de `news-briefing-saas` pour `.opencode/`.
- **Zéro perte d'historique** : les JSON étaient déjà gitignorés — rien de versionné n'est perdu.
- **Suppression de complexité accidentelle** : plus de `fcntl`, plus de `glob`+rescan, plus de cache version/mtime — remplacés par les transactions SQLite.
- **Requêtabilité** : filtres/tri/compact en SQL au lieu de scans Python en mémoire.
- **Voie transactionnelle pour JIRA** : `stories` + `sync_state` dans une base unique.

### Négatives / risques
- **Refacto central** : borné (~92 lignes) mais consommé par tout le serveur → exige une bascule **iso-comportement** validée par tests.
- **Migration de données** : les 72 JSON existants à importer (mitigé par backup + réversibilité).
- **Ergonomie** : plus de `cat story.json` ; inspection via `sqlite3 kanban.db` ou le dashboard.
- **SSE** : `bump_version` à re-câbler proprement sur la base.

### Garde-fous
- Bascule **iso-comportement** : la suite de tests du serveur (outils MCP + REST) fait foi.
- **Backup** des JSON avant migration ; script **réversible** (export SQLite → JSON).
- Base **gitignorée** dès le premier commit — jamais de `.db` dans l'historique.

## Alternatives considérées

| Option | Description | Pour | Contre |
|--------|-------------|------|--------|
| **A — SQLite local unique dans `.opencode/`** *(retenue)* | Migrer derrière le seam, stories + sync_state à terme, gitignoré | Découplage, transactions, requêtabilité, unifie avec JIRA | Refacto central iso-comportement, migration de données |
| **B — Déplacer les JSON dans `.opencode/`** | Changer `find_stories_dir`, garder le format JSON | Coût quasi nul, corrige le mélange | Garde fcntl/glob/mtime ; dual-write inter-technos avec `sync.db` JIRA |
| **C — Statu quo** | Laisser les JSON à la racine de news-briefing-saas | 0 effort | Mélange persistant + complexité + dual-tech au moment de JIRA |

## Notes

- **Périmètre** : uniquement le stockage des stories. L'intégration JIRA (`JIRA.md`) est une épic distincte qui **s'appuiera** sur cette base.
- **Cohérence** : même philosophie que l'ADR-0002 de news-briefing-saas (« une source de vérité, des projections dérivées ») — ici, JIRA = vérité partagée, la base SQLite locale = état de travail réhydratable.
