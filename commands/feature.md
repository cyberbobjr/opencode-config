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
| `description` | Markdown format (see below). Rendered in the Kanban modal — must be valid markdown with `\n\n` between sections. |
| `priority` | `P2` default. Upgrade to `P1` if the feature unblocks critical flows. `P0` only if required to ship. |
| `stack` | Subset of: `backend`, `frontend`, `database`, `devops`, `infrastructure`, `architecture`, `security`, `docs`. Infer from feature nature (UI component → frontend, new endpoint → backend, schema change → database, etc.). At least one value required. |
| `notes` | Open questions, assumptions, related User Stories, or constraints identified from the codebase scan. Empty string if none. |

**Description format** (mandatory markdown, 2 sections):
```
## User Story
**En tant que** [rôle], je veux **[fonctionnalité]**, afin de **[bénéfice]**.

## Contexte
[Pourquoi cette fonctionnalité est nécessaire, quel problème elle résout, quelles hypothèses ont été faites.]
```

> ⚠️ When writing the JSON string value, use `\n\n` between sections and `\n` between heading and body. The description is rendered as markdown in the Kanban dashboard.

### 0.3 — Show preview and confirm

Display the qualified story as a preview block:

```
📋 Story Preview
─────────────────────────────────
title       : [title]
description :
  ## User Story
  En tant que [rôle], je veux [fonctionnalité], afin de [bénéfice].
  ## Contexte
  [context]
priority    : [P0/P1/P2]
stack       : [backend, frontend, ...]
notes       : [notes or "none"]
─────────────────────────────────
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
- ✅ Description must follow the "En tant que" user story format
- ✅ Title must be specific enough to understand what the feature does without reading the description
- ❌ Do not start implementation — this command only creates the backlog entry
