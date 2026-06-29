---
description: Create a new feature User Story in the Backlog (Phase 7) — qualifies title, description, stack, then creates pending
argument:
  required: true
  description: "Feature description (e.g. 'Export briefings to CSV')"
---

# `/feature "$ARGUMENTS"` — New Feature Story

Creates a fully qualified User Story in the Backlog (Phase 7) with status `pending`.

---

## Phase 0: Qualification

Before creating anything, qualify the story from `$ARGUMENTS` and the codebase.

### 0.1 — Context scan

Read these sources to understand the project context:
- `AGENTS.md` — stack, conventions, tech used
- `git log --oneline -10` — recent work context
- Brief `grep` / `glob` for files relevant to the feature described in `$ARGUMENTS`

### 0.2 — Fill the qualification schema

Infer each field. Do NOT leave any field empty or generic.

| Field | Rule |
|-------|------|
| `title` | Imperative verb + subject, ≤60 chars. No "feature" prefix. (e.g. "Exporter les briefings en CSV") |
| `description` | Rich markdown format (see below). 5 sections with emojis, lists, and tables. Rendered in the Kanban modal. |
| `priority` | `P2` default. Upgrade to `P1` if the feature unblocks critical flows. `P0` only if required to ship. |
| `stack` | Subset of: `backend`, `frontend`, `database`, `devops`, `infrastructure`, `architecture`, `security`, `docs`. Infer from feature nature (UI component → frontend, new endpoint → backend, schema change → database, etc.). At least one value required. |
| `notes` | Open questions, assumptions, related User Stories, or constraints identified from the codebase scan. Empty string if none. |

**Description format** (mandatory rich markdown — 5 sections with emojis, lists, and tables):

> ⚠️ **Règles markdown impératives** — Le dashboard Kanban rend ce markdown en HTML via `marked`.
> Séparer les sections par une **ligne vide** (`\n\n`), utiliser `- ` pour les listes (pas de virgules),
> des backticks `` `comme ceci` `` pour les chemins et identifiants, et `**gras**` pour les mots-clés.

```
## 📋 User Story

**En tant que** [rôle], **je veux** [fonctionnalité], **afin de** [bénéfice].

## 🎯 Contexte

- **Problème actuel** : [ce qui manque ou dysfonctionne aujourd'hui]
- **Solution envisagée** : [ce que la feature apportera]
- **Utilisateurs impactés** : [qui bénéficiera de la fonctionnalité]

## 🔧 Portée Technique

| Couche         | Impact                                            |
|----------------|---------------------------------------------------|
| Backend        | [endpoints, services, workers — ou "Aucun"]       |
| Frontend       | [vues, composants, stores — ou "Aucun"]            |
| Base de données| [migrations, nouveaux modèles — ou "Aucune"]      |

## 📁 Fichiers Pressentis

- `backend/app/routes/...` — [rôle pressenti]
- `frontend/src/views/...` — [rôle pressenti]

## ❓ Questions Ouvertes

- [Question 1 à résoudre pendant le refine]
- [Question 2 le cas échéant]
```

> ⚠️ When writing the JSON string value, use `\n\n` between sections and `\n` between heading and body. The description is rendered as markdown in the Kanban dashboard. Never leave a section empty — write "Aucun" if not applicable.

### 0.3 — Show preview and confirm

Display the qualified story as a preview block:

```
📋 Story Preview
─────────────────────────────────────────────
title       : [title]
priority    : [P0/P1/P2]
stack       : [backend, frontend, ...]
notes       : [notes or "none"]

description :
  ## 📋 User Story
  **En tant que** [rôle], **je veux** [fonctionnalité], **afin de** [bénéfice].

  ## 🎯 Contexte
  - **Problème actuel** : [...]
  - **Solution envisagée** : [...]
  - **Utilisateurs impactés** : [...]

  ## 🔧 Portée Technique
  | Couche | Impact |
  | Backend | [...] |
  | Frontend | [...] |

  ## 📁 Fichiers Pressentis
  - `path/to/file.py` — [rôle]

  ## ❓ Questions Ouvertes
  - [...]
─────────────────────────────────────────────
```

Ask: **"Create this story? [yes / edit]"**
- **yes** → proceed to Phase 1
- **edit** → show each field one by one, accept corrections, then proceed

---

## Phase 1: Creation

1. Call `kanban-create-story(title="[qualified title]", priority="[priority]", phase=7)`
   → This returns the new story with its ID (e.g. `US 7.1`)
2. Immediately call `kanban-update-story("US 7.X", '{"_actor": "feature", "description": "[description]", "stack": [stack], "notes": "[notes]"}')`
3. Display the confirmation:

```
✅ US 7.X — "[title]" added to backlog
   stack: [backend, frontend, ...]
   priority: [P2]

Next steps:
  /refine US 7.X      — clarify ACs and build the technical plan
  /next-story         — pick it up when prioritized
```

---

## Reminders

- ✅ `stack` must always be filled — it's displayed on the Kanban card
- ✅ Description must follow the 5-section rich markdown format (emojis, lists, tables) — NOT plain text
- ✅ Title must be specific enough to understand what the feature does without reading the description
- ✅ Every section must be filled — write "Aucun" if not applicable, never leave empty
- ❌ Do not start implementation — this command only creates the backlog entry
