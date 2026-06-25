---
description: TDD Command — fetches story context and launches the tdd subagent via Task tool
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# TDD Command — `/tdd $ARGUMENTS`

Thin orchestrator wrapper that assembles context and delegates implementation to the isolated `tdd` subagent.

## Phase 1: Gather Context

1. Call `kanban-get-story("$ARGUMENTS")` to retrieve the full story (ACs, implementation_guide, description, stack)
2. Read the following files and extract the relevant sections:
   - `AGENTS.md` — stack info (Identité table)
   - `.opencode/rules/commands.md` — test run commands, quality gate commands
   - `.opencode/rules/conventions.md` — design system reference (points to `docs/design-system.md`)

## Phase 2: Launch TDD Subagent

Use the **Task tool** to launch the `tdd` subagent with `subagent_type: "tdd"`.

Inject the following as the Task prompt (replace placeholders with actual values):

```
story_id: $ARGUMENTS
mode: full-cycle
is_orchestrated: false

STORY JSON:
[paste the full JSON returned by kanban-get-story]

PROJECT CONVENTIONS:
[paste: stack info from AGENTS.md + test/quality gate commands from .opencode/rules/commands.md + design system ref from .opencode/rules/conventions.md if frontend]

Instructions:
- Run the full Red-Green-Refactor cycle for this story
- Update the story status via MCP tools (kanban-update-story) as you progress
- At the end, return the structured TDD report
```

> **Note:** If this command is called from `/next-story` with the explicit annotation "Orchestrator context", set `is_orchestrated: true` in the prompt so the subagent does not ask about advancing.

## Phase 3: Display Result

Display the TDD report returned by the subagent.

## Phase 4: Advance

- If `status: failed` in the report → stop, display the failure details
- If `status: passed` and this was called via `/next-story` orchestrator (context says "Orchestrator context") → return the report only. The orchestrator handles `kanban-move-story` to `secops_cr`.
- If `status: passed` and called standalone → ask:
  > "✅ TDD passed — [N] tests, [coverage]. Proceed to security code review (`secops_cr`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_cr", "tdd")` → run `/secops "$ARGUMENTS" mode=code-review`
  - **no** → stop. "To continue later: drag to `secops_cr` or run `/next-story secops-cr $ARGUMENTS`"
