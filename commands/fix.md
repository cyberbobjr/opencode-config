---
description: Create a bugfix User Story in the Backlog (Phase 7) — qualifies title, description, stack, then creates pending
argument:
  required: true
  description: "Bug description (e.g. 'Refresh token expires too early')"
---

# `/fix "$ARGUMENTS"` — Bugfix Story

Creates a fully qualified bugfix User Story in the Backlog (Phase 7) with status `pending`.

---

## Phase 0: Qualification

Before creating anything, qualify the story from `$ARGUMENTS` and the codebase.

### 0.1 — Context scan

Search for relevant code:
- `grep` / `glob` for files, functions, or modules related to the bug described in `$ARGUMENTS`
- `git log --oneline -5` to check if this was recently modified
- `AGENTS.md` — stack and conventions

### 0.2 — Fill the qualification schema

Infer each field. Do NOT leave any field empty or generic.

| Field | Rule |
|-------|------|
| `title` | `"Fix — [concise bug description]"` pattern. ≤60 chars. Specific enough to identify the bug. (e.g. "Fix — refresh token expiré prématurément") |
| `description` | Rich markdown bug report format (see below). 5 sections with emojis, lists, and tables. |
| `priority` | `P1` default for bugs. Use `P0` if production-breaking or blocking. `P2` for minor cosmetic issues. |
| `stack` | Infer from the impacted component/file found in the scan. At least one value required. |
| `notes` | Reproduction context: conditions, environment, frequency. File path and line if identified. Related User Story if relevant. |

**Description format** (mandatory rich markdown — 5 sections with emojis, lists, and tables):

> ⚠️ **Règles markdown impératives** — Le dashboard Kanban rend ce markdown en HTML via `marked`.
> Séparer les sections par une **ligne vide** (`\n\n`), utiliser `- ` pour les listes (pas de virgules),
> des backticks `` `comme ceci` `` pour les chemins et identifiants, et `**gras**` pour les mots-clés.

```
## 🐛 Bug

[Description du comportement cassé — symptôme observable, message d'erreur.]

## 🔍 Contexte

- **Route / Composant** : `GET /api/...` ou `ComponentName.vue`
- **Condition déclenchante** : [quand / comment le bug se manifeste]
- **Fréquence** : [systématique / intermittent / edge case]
- **Environnement** : [dev / staging / prod]

## ✅ Comportement Attendu

[Ce que le comportement correct devrait être — contraste avec le bug ci-dessus.]

## 📁 Fichiers Impactés

| Fichier                | Rôle                                  |
|------------------------|---------------------------------------|
| `backend/app/...`      | [cause racine probable]               |
| `backend/tests/...`    | [test à ajouter / corriger]           |

## 🔬 Reproduction

1. [Étape 1 — ex: "Créer un profil avec les paramètres X"]
2. [Étape 2 — ex: "Appeler l'endpoint Y"]
3. [Résultat observé — ex: "Erreur 500 / KeyError"]
```

> ⚠️ When writing the JSON string value, use `\n\n` between sections and `\n` between heading and body. The description is rendered as markdown in the Kanban dashboard. Never leave a section empty — write "Aucun" if not applicable.

### 0.3 — Show preview and confirm

Display the qualified story as a preview block:

```
🐛 Bug Story Preview
─────────────────────────────────────────────
title       : [Fix — ...]
priority    : [P0/P1/P2]
stack       : [backend, ...]
notes       : [reproduction context or "none"]

description :
  ## 🐛 Bug
  [symptôme observable]

  ## 🔍 Contexte
  - **Route / Composant** : [...]
  - **Fréquence** : [...]

  ## ✅ Comportement Attendu
  [comportement correct]

  ## 📁 Fichiers Impactés
  | Fichier | Rôle |
  | `path/to/file.py` | [cause racine] |

  ## 🔬 Reproduction
  1. [étape 1]
  2. [résultat observé]
─────────────────────────────────────────────
```

Ask: **"Create this story? [yes / edit]"**
- **yes** → proceed to Phase 1
- **edit** → show each field one by one, accept corrections, then proceed

---

## Phase 1: Creation

1. Call `kanban-create-story(title="[qualified title]", priority="[priority]", phase=7)`
   → This returns the new story with its ID (e.g. `US 7.2`)
2. Immediately call `kanban-update-story("US 7.X", '{"_actor": "fix", "description": "[description]", "stack": [stack], "notes": "[notes]"}')`
3. Display the confirmation:

```
✅ US 7.X — "[title]" added to backlog
   stack: [backend, ...]
   priority: [P1]

Next steps:
  /refine US 7.X      — clarify reproduction steps, scope, and define ACs
  /next-story         — pick it up when prioritized
```

---

## Reminders

- ✅ `stack` must always be filled — infer it from the impacted component
- ✅ Description must use the 5-section rich markdown format (emojis, lists, tables) — NOT plain text
- ✅ `notes` should include any reproduction steps or file paths found during the scan
- ✅ Priority `P1` is the default for all bugs — only deviate with justification
- ✅ Every section must be filled — write "Aucun" if not applicable, never leave empty
- ❌ Do not fix the bug here — this command only creates the backlog entry
