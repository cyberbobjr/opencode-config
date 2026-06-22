---
description: Create and implement a new feature as a User Story (Backlog Phase 7)
argument:
  required: true
  description: "Feature description (e.g. 'Export briefings to CSV')"
---

# `/feature "description"` — New Feature

Creates a User Story in the Backlog (Phase 7) and runs the full cycle: refinement → TDD → QA → quality gates → commit.

## Workflow

### 1. Create the User Story

1. Call the MCP tool `kanban-create-story(title, priority="P2", phase=7)` to create the story in `user-stories/*.json`
2. Display the generated ID to the user (e.g. `US 7.1`)

### 2. Refinement

1. Delegate to `/refine US 7.N` (Refinement Agent)
2. The user defines acceptance criteria during the challenge session
3. Validated ACs are persisted via `kanban-update-story("US 7.N", ...)` by the refinement agent
4. **[STOP]** Ask: "Proceed to TDD implementation?" — if yes → Step 3

### 3. TDD Implementation → QA → Quality Gates → Commit

1. Delegate to `/tdd US 7.N`
2. Delegate to `/qa US 7.N`
3. Quality gates + `/simplify`
4. `/commit` + `kanban-move-story("US 7.N", "completed")`

## Reminders

- ✅ One new feature = one User Story in `user-stories/*.json`
- ✅ The cycle is identical to planned stories
- ✅ Priority defaults to `P2` (adjustable during refinement)
