---
description: Create a change request User Story in the Backlog (Phase 7) — qualifies title, description, stack, impact, then creates pending
argument:
  required: true
  description: "Change description (e.g. 'Migrate from SQLite to PostgreSQL')"
---

# `/change "$ARGUMENTS"` — Change Request Story

Creates a fully qualified change request User Story in the Backlog (Phase 7) with status `pending`.

---

## Phase 0: Qualification

Before creating anything, qualify the story from `$ARGUMENTS` and the codebase.

### 0.1 — Context scan (impact analysis)

This is the most important scan of the three commands — changes affect existing code.

- Call `kanban-list-stories` to find related User Stories in the same area
- `grep` / `glob` for files, modules, or patterns impacted by the change described in `$ARGUMENTS`
- Check `AGENTS.md` for the affected stack conventions

### 0.2 — Fill the qualification schema

Infer each field. Do NOT leave any field empty or generic.

| Field | Rule |
|-------|------|
| `title` | `"Change — [what changes]"` pattern. ≤60 chars. Specific about what is changing. (e.g. "Change — migration SQLite vers PostgreSQL") |
| `description` | Rich markdown change request format (see below). 4 sections with emojis, lists, and tables. |
| `priority` | `P2` default. Upgrade to `P1` if it unblocks critical stories. `P0` if it's a prerequisite for release. |
| `stack` | Changes often touch multiple layers — list all impacted stacks. At least one value required. |
| `notes` | **Required for changes**: list of impacted stories (US X.Y) and impacted files/modules found during the scan. Note any breaking changes or backward-compatibility risks. |

**Description format** (mandatory rich markdown — 4 sections with emojis, lists, and tables):

> ⚠️ **Règles markdown impératives** — Le dashboard Kanban rend ce markdown en HTML via `marked`.
> Séparer les sections par une **ligne vide** (`\n\n`), utiliser `- ` pour les listes (pas de virgules),
> des backticks `` `comme ceci` `` pour les chemins et identifiants, et `**gras**` pour les mots-clés.

```
## 🎯 Motivation

[Pourquoi ce changement est nécessaire — le problème qu'il résout ou l'opportunité qu'il capture.]

## 📐 Périmètre

| Module / Fichier               | Changement                                            |
|--------------------------------|-------------------------------------------------------|
| `backend/app/models/...`       | [description du changement de schéma ou contrat]      |
| `backend/app/routes/...`       | [description du changement d'endpoint]                |
| `frontend/src/...`             | [description du changement d'UI]                      |

## ⚠️ Risques

- **Breaking changes** : [oui/non — détail si oui]
- **Rétrocompatibilité** : [impact sur les données / API existantes]
- **Rollback** : [comment revenir en arrière si problème]
- **Migration de données** : [nécessaire ou non — quelles étapes]

## 📊 Stories Impactées

| Story   | Impact                                    |
|---------|-------------------------------------------|
| US X.Y  | [bloquée / à retester / à adapter]        |
| US X.Z  | [bloquée / à retester / à adapter]        |
```

> ⚠️ When writing the JSON string value, use `\n\n` between sections and `\n` between heading and body. The description is rendered as markdown in the Kanban dashboard. Never leave a section empty — write "Aucun" if not applicable.

### 0.3 — Show preview and confirm

Display the qualified story as a preview block:

```
🔄 Change Story Preview
─────────────────────────────────────────────
title       : [Change — ...]
priority    : [P0/P1/P2]
stack       : [backend, database, ...]
notes       : Impacted stories: US X.Y, US X.Z
              Impacted files: path/to/file.py, ...

description :
  ## 🎯 Motivation
  [pourquoi ce changement]

  ## 📐 Périmètre
  | Module | Changement |
  | `path/to/file.py` | [description] |

  ## ⚠️ Risques
  - **Breaking changes** : [...]
  - **Rollback** : [...]

  ## 📊 Stories Impactées
  | Story | Impact |
  | US X.Y | [impact] |
─────────────────────────────────────────────
```

Ask: **"Create this story? [yes / edit]"**
- **yes** → proceed to Phase 1
- **edit** → show each field one by one, accept corrections, then proceed

---

## Phase 1: Creation

1. Call `kanban-create-story(title="[qualified title]", priority="[priority]", phase=7)`
   → This returns the new story with its ID (e.g. `US 7.3`)
2. Immediately call `kanban-update-story("US 7.X", '{"_actor": "change", "description": "[description]", "stack": [stack], "notes": "[notes with impact list]"}')`
3. Display the confirmation:

```
✅ US 7.X — "[title]" added to backlog
   stack: [backend, database, ...]
   priority: [P2]
   impacted: [list of related stories if found]

Next steps:
  /refine US 7.X      — explore full impact, identify all affected stories, define ACs
  /next-story         — pick it up when prioritized
```

---

## Reminders

- ✅ `notes` must list impacted User Stories and files found during the scan
- ✅ Description must use the 4-section rich markdown format (emojis, lists, tables) — NOT plain text
- ✅ `stack` often spans multiple layers for change requests — be thorough
- ✅ Every section must be filled — write "Aucun" if not applicable, never leave empty
- ✅ The refinement step (`/refine`) will deepen the impact analysis — don't try to be exhaustive here
- ❌ Do not implement the change — this command only creates the backlog entry
