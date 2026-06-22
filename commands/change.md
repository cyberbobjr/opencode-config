---
description: Create a User Story for a change request with impact analysis
argument:
  required: true
  description: "Change description (e.g. 'Migrate from SQLite to PostgreSQL')"
---

# `/change "description"` — Change Request

Creates a change User Story in the Backlog (Phase 7) and runs the full cycle: impact analysis + refinement → TDD → QA → quality gates → commit.

## Workflow

### 1. Create the User Story

1. Call the MCP tool `kanban-create-story(title, priority="P2", phase=7)` to create the story in `user-stories/*.json`
2. Display the generated ID to the user (e.g. `US 7.1`)

### 2. Impact Analysis + Refinement

1. Call `kanban-move-story("US 7.N", "refining")`
2. Explore the existing codebase to identify the impact of the change
3. Delegate to `/refine US 7.N` with the impact analysis context
4. Acceptance criteria are defined during refinement and persisted in the JSON
5. Call `kanban-move-story("US 7.N", "secops_tm")`
6. **[STOP]** Ask: "Proceed to implementation?"

### 3. TDD Implementation → QA → Commit

1. Delegate to `/tdd US 7.N`
2. Delegate to `/qa US 7.N`
3. Quality gates + `/simplify`
4. `/commit` + `kanban-move-story("US 7.N", "completed")`

## Reminders

- ✅ One change = one User Story in `user-stories/*.json`
- ✅ Impact analysis is mandatory before implementation
- ✅ All impacted stories must be listed in the description
