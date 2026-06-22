---
description: Fix a bug as a User Story (Backlog Phase 7)
argument:
  required: true
  description: "Bug description (e.g. 'Refresh token expires too early')"
---

# `/fix "description"` — Bugfix

Creates a bugfix User Story in the Backlog (Phase 7) and runs the full cycle: lightweight refinement → TDD → QA → quality gates → commit.

## Workflow

### 1. Create the User Story

1. Call the MCP tool `kanban-create-story(title, priority="P1", phase=7)` to create the story in `user-stories/*.json`
   - The title must reflect the bug
2. Display the generated ID to the user (e.g. `US 7.1`)

### 2. Lightweight Refinement

1. Call `kanban-move-story("US 7.N", "refining")`
2. Ask 2–3 targeted questions to clarify the bug (reproduction steps, scope, priority)
3. Define acceptance criteria with the user
4. Persist via `kanban-update-story("US 7.N", '{"acceptance_criteria": [...], "description": "...", "refine_decisions": [{"question": "...", "decision": "...", "justification": "..."}]}')`
5. Call `kanban-move-story("US 7.N", "secops_tm")`
6. **[STOP]** Ask: "Proceed to implementation?"

### 3. TDD Implementation → QA → Commit

1. Delegate to `/tdd US 7.N`
2. Delegate to `/qa US 7.N`
3. Quality gates + `/simplify`
4. `/commit` + `kanban-move-story("US 7.N", "completed")`

## Reminders

- ✅ One bugfix = one User Story in `user-stories/*.json`
- ✅ Priority defaults to `P1` (adjustable)
- ✅ Refinement is lighter than for a feature
