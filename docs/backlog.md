# Backlog — opencode-config

> Backlog **propre à ce projet** (`cyberbobjr/opencode-config`). Rien à voir avec le backlog produit de news-briefing-saas (le kanban MCP `user-stories/*.json`). IDs locaux `OC-xxx`.
>
> Statuts : `pending` · `in-progress` · `done` · `blocked`.

---

## OC-001 — Migrer le stockage du kanban : JSON → SQLite local

- **Statut** : pending
- **Priorité** : haute (bloque OC-002)
- **ADR** : [`docs/adr/0001-stockage-kanban-json-vers-sqlite-local.md`](adr/0001-stockage-kanban-json-vers-sqlite-local.md)

Migrer le stockage des stories de `user-stories/*.json` (posés à la racine de news-briefing-saas, déjà gitignorés) vers **une base SQLite locale unique** dans `.opencode/kanban/`, derrière le seam de stockage existant (~10 fonctions / 92 lignes dans `kanban/server.py`), **iso-comportement**.

**Motivation** : (1) découpler les données du kanban de l'arborescence news-briefing-saas ; (2) supprimer la complexité accidentelle (verrous `fcntl`, `glob`-scan à chaque load, cache version/mtime) ; (3) préparer l'unification transactionnelle avec le `sync_state` de OC-002 — **à faire AVANT** l'intégration JIRA pour éviter un dual-write inter-technos.

**Critères d'acceptation**
- [ ] Les 72 stories JSON existantes migrées vers SQLite sans perte, via un script one-shot avec **backup** préalable des JSON.
- [ ] Script de migration **réversible** (export SQLite → JSON).
- [ ] Les 9 outils MCP et l'API REST fonctionnent à l'identique (iso-comportement), validé par les tests du serveur.
- [ ] Dashboard + live-refresh SSE (`/api/events`) fonctionnels : `bump_version` re-câblé sur la base (compteur en table ou `PRAGMA data_version`).
- [ ] Schéma : colonnes indexées (`id`, `title`, `status`, `phase`, `priority`, `updated_at`) + blob JSON `data` pour le reste (ACs, `tdd`, `qa`, `secops_report`, `history`).
- [ ] Le mode `compact` de `list_stories` devient un `SELECT` de colonnes.
- [ ] `fcntl`, `glob`-scan et cache version/mtime supprimés.
- [ ] Base (`kanban/*.db` + wal/shm/journal) gitignorée, jamais dans l'historique git.

---

## OC-002 — Intégration JIRA ↔ Kanban (pull assigné + enrichissement commentaires)

- **Statut** : pending
- **Priorité** : moyenne
- **Dépend de** : OC-001 (le `sync_state` JIRA vit dans la même base SQLite)
- **Spec** : [`JIRA.md`](../JIRA.md)

JIRA = source de vérité (statut piloté manuellement par le dev) ; le kanban garde son statut de pipeline local, **pull** les tickets assignés au dev arrivés au statut déclencheur paramétrable, et **write-back en commentaires uniquement** — jamais de transition de statut. Sans webhook (polling REST), désactivable par config.

**Découpage** (cf. « Ordre recommandé » de `JIRA.md`)
- [ ] OC-002a — `jira_client.py` : GET sprint + GET search (filtre `assignee`) + POST comment (retry/backoff).
- [ ] OC-002b — `sync_state` (table SQLite dans la base OC-001) : lecture/écriture.
- [ ] OC-002c — Full sync au démarrage (lecture seule, aucun write).
- [ ] OC-002d — `--dry-run` : valider la détection du statut déclencheur sans écrire.
- [ ] OC-002e — Création d'US locale idempotente sur trigger (`JIRA_PULL_TRIGGER_STATUS`).
- [ ] OC-002f — Write-back commentaires namespacés (TDD, QA, SecOps).

**Hors périmètre v1** : écriture de champs JIRA (description/ACs), rôle lead/dev, toute transition de statut (reste manuel côté dev).
