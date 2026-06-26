---
description: QA Command — fetches story context and launches the qa subagent via Task tool
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# QA Command — `/qa $ARGUMENTS`

Thin orchestrator wrapper that assembles context and delegates validation to the isolated `qa` subagent.

## Phase 1: Gather Context

1. Call `kanban-get-story("$ARGUMENTS")` to retrieve the full story (ACs, implementation_guide, tdd report, qa, description, stack)
2. Read the following files and extract the relevant sections:
   - `AGENTS.md` — stack info (Identité table)
   - `.opencode/rules/commands.md` — test run commands, UI-INT tool, quality gate commands

## Phase 2: Launch QA Subagent

Use the **Task tool** to launch the `qa` subagent with `subagent_type: "qa"`.

Inject the following as the Task prompt (replace placeholders with actual values):

```
story_id: $ARGUMENTS
is_orchestrated: false
# is_orchestrated: true only when called from /next-story US X.Y full-cycle orchestration.
# Dashboard-triggered runs and all standalone uses → is_orchestrated: false.

STORY JSON:
[paste the full JSON returned by kanban-get-story — including the tdd and qa fields]

PROJECT CONVENTIONS:
[paste: stack info from AGENTS.md + test/UI-INT/quality gate commands from .opencode/rules/commands.md]

Instructions:
- Validate all acceptance criteria using the test type appropriate to each AC (unit / integration / UI-INT)
- Update the story status via MCP tools (kanban-update-story) as you progress
- At the end, return the structured QA report
```

## Phase 3: Display Result

Display the QA report returned by the subagent.

## Phase 4: Advance

- If `status: failed` in the report → stop, display the detailed failure report (user decides: fix / block / force)
- If `status: passed` and called from `/next-story US X.Y` orchestrator (context says "Orchestrator context") → return the report only. The orchestrator handles `kanban-move-story` to `simplify`.
- If `status: passed` and called standalone (dashboard trigger) →
  1. Call `kanban-update-story("$ARGUMENTS", '{"agent_status": "awaiting_input"}')`
  2. Ask: "✅ QA passed — [N/N] ACs covered. Proceed to quality gates (`simplify`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "simplify", "qa")` → run `/simplify $ARGUMENTS`
  - **no** → `kanban-update-story("$ARGUMENTS", '{"agent_status": null}')` → stop. "To continue later: drag the card to `simplify` on the dashboard."
