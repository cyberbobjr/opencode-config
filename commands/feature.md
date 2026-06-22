---
description: Create a new feature User Story in the Backlog (Phase 7) — no implementation
argument:
  required: true
  description: "Feature description (e.g. 'Export briefings to CSV')"
---

# `/feature "description"` — New Feature Story

Creates a User Story in the Backlog (Phase 7) and stops. Use `/refine US X.Y` when ready to refine it, then `/next-story` to implement it.

## Steps

1. Call `kanban-create-story(title="$ARGUMENTS", priority="P2", phase=7)`
2. Display the generated ID to the user (e.g. `US 7.1`)
3. **Done** — the story is in the backlog with status `pending`

## Reminders

- ✅ Priority defaults to `P2` (adjustable via the modal or during refinement)
- ✅ Use `/refine US X.Y` to run the refinement cycle when you're ready
- ✅ Use `/next-story` or the Kanban board to pick it up for implementation
