---
description: Create a bugfix User Story in the Backlog (Phase 7) — no implementation
argument:
  required: true
  description: "Bug description (e.g. 'Refresh token expires too early')"
---

# `/fix "description"` — Bugfix Story

Creates a bugfix User Story in the Backlog (Phase 7) and stops. Use `/refine US X.Y` when ready to clarify the bug and define ACs, then `/next-story` to implement.

## Steps

1. Call `kanban-create-story(title="$ARGUMENTS", priority="P1", phase=7)`
2. Display the generated ID to the user (e.g. `US 7.2`)
3. **Done** — the story is in the backlog with status `pending`

## Reminders

- ✅ Priority defaults to `P1` (adjustable via the modal or during refinement)
- ✅ Use `/refine US X.Y` to clarify reproduction steps, scope, and define ACs
- ✅ Use `/next-story` or the Kanban board to pick it up for implementation
