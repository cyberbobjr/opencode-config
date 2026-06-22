---
description: Create a change request User Story in the Backlog (Phase 7) — no implementation
argument:
  required: true
  description: "Change description (e.g. 'Migrate from SQLite to PostgreSQL')"
---

# `/change "description"` — Change Request Story

Creates a change request User Story in the Backlog (Phase 7) and stops. Use `/refine US X.Y` when ready to analyse the impact and define ACs, then `/next-story` to implement.

## Steps

1. Call `kanban-create-story(title="$ARGUMENTS", priority="P2", phase=7)`
2. Display the generated ID to the user (e.g. `US 7.3`)
3. **Done** — the story is in the backlog with status `pending`

## Reminders

- ✅ Priority defaults to `P2` (adjustable via the modal or during refinement)
- ✅ Use `/refine US X.Y` to explore impact, identify affected stories, and define ACs
- ✅ All impacted stories should be listed in the description during refinement
- ✅ Use `/next-story` or the Kanban board to pick it up for implementation
