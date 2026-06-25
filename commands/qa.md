---
description: QA Command — fetches story context and launches the qa subagent via Task tool
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# QA Command — `/qa $ARGUMENTS`

Thin orchestrator wrapper that assembles context and delegates validation to the isolated `qa` subagent.

## Phase 1: Gather Context

1. Call `kanban-get-story("$ARGUMENTS")` to retrieve the full story (ACs, implementation_guide, tdd report, description)
2. Read the following files and extract the relevant sections:
   - `AGENTS.md` — stack info (Identité table)
   - `.opencode/rules/commands.md` — test run commands, E2E tool (`npx playwright test`), quality gate commands

## Phase 2: Launch QA Subagent

Use the **Task tool** to launch the `qa` subagent with `subagent_type: "qa"`.

Inject the following as the Task prompt (replace placeholders with actual values):

```
story_id: $ARGUMENTS
is_orchestrated: false

STORY JSON:
[paste the full JSON returned by kanban-get-story]

PROJECT CONVENTIONS:
[paste: stack info from AGENTS.md + test/E2E/quality gate commands from .opencode/rules/commands.md]

Instructions:
- Validate all acceptance criteria for this story through integration and E2E tests
- Update the story status via MCP tools (kanban-update-story) as you progress
- At the end, return the structured QA report
```

> **Note:** If this command is called from `/next-story` with the explicit annotation "Orchestrator context", set `is_orchestrated: true` in the prompt so the subagent does not ask about advancing.

## Phase 3: Display Result

Display the QA report returned by the subagent.

## Phase 4: Advance

- If `status: failed` in the report → stop, display the detailed failure report (user decides: fix / block / force)
- If `status: passed` and this was called via `/next-story` orchestrator (context says "Orchestrator context") → return the report only. The orchestrator handles `kanban-move-story` to `simplify`.
- If `status: passed` and called standalone → ask:
  > "✅ QA passed — [N/N] ACs covered. Proceed to quality gates (`simplify`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "simplify", "qa")` → run `/simplify $ARGUMENTS`
  - **no** → stop. "To continue later: drag to `simplify` or run `/next-story simplify $ARGUMENTS`"
