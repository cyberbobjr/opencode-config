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
| `description` | Change request format (see below). Three parts, each on its own line. |
| `priority` | `P2` default. Upgrade to `P1` if it unblocks critical stories. `P0` if it's a prerequisite for release. |
| `stack` | Changes often touch multiple layers — list all impacted stacks. At least one value required. |
| `notes` | **Required for changes**: list of impacted stories (US X.Y) and impacted files/modules found during the scan. Note any breaking changes or backward-compatibility risks. |

**Description format** (mandatory, 3 parts):
```
**Motivation:** [Why this change is needed — the problem it solves or the opportunity it captures.]
**Périmètre:** [What is changing — modules, files, interfaces, contracts, data schemas.]
**Risques:** [Breaking changes, backward compatibility concerns, rollback strategy needed.]
```

### 0.3 — Show preview and confirm

Display the qualified story as a preview block:

```
🔄 Change Story Preview
─────────────────────────────────
title       : [Change — ...]
description : **Motivation:** ...
              **Périmètre:** ...
              **Risques:** ...
priority    : [P0/P1/P2]
stack       : [backend, database, ...]
notes       : Impacted stories: US X.Y, US X.Z
              Impacted files: path/to/file.py, ...
─────────────────────────────────
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
- ✅ Description must use the 3-part change request format (Motivation / Périmètre / Risques)
- ✅ `stack` often spans multiple layers for change requests — be thorough
- ✅ The refinement step (`/refine`) will deepen the impact analysis — don't try to be exhaustive here
- ❌ Do not implement the change — this command only creates the backlog entry
