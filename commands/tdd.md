---
description: TDD Command — fetches story context, determines mode, and launches the tdd subagent via Task tool
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# TDD Command — `/tdd $ARGUMENTS`

Thin orchestrator wrapper that assembles context, determines the correct mode, and delegates implementation to the isolated `tdd` subagent.

## Phase 1: Gather Context

1. Call `kanban-get-story("$ARGUMENTS")` to retrieve the full story (ACs, implementation_guide, qa, description, stack)
2. Read the following files and extract the relevant sections:
   - `AGENTS.md` — stack info (Identité table)
   - `.opencode/rules/commands.md` — test run commands, quality gate commands
   - `.opencode/rules/conventions.md` — design system reference (if `implementation_guide.scope` contains `frontend`)

## Phase 2: Determine Mode

Inspect the story's `qa` field:

- If `story.qa.status == "failed"` and `story.qa.failures` is present → **`mode: fix-failing-acs`**, inject `ac_failing` from `story.qa.failures`
- Otherwise → **`mode: full-cycle`**

## Phase 3: Launch TDD Subagent

Use the **Task tool** to launch the `tdd` subagent with `subagent_type: "tdd"`.

Inject the following as the Task prompt (replace placeholders with actual values):

```
story_id: $ARGUMENTS
mode: [full-cycle | fix-failing-acs — determined in Phase 2]
is_orchestrated: false
# is_orchestrated: true only when called from /next-story US X.Y full-cycle orchestration.
# Dashboard-triggered runs and all standalone uses → is_orchestrated: false.

STORY JSON:
[paste the full JSON returned by kanban-get-story]

PROJECT CONVENTIONS:
[paste: stack info from AGENTS.md + test/quality gate commands from .opencode/rules/commands.md + design system ref from .opencode/rules/conventions.md if implementation_guide.scope contains "frontend"]

[only in fix-failing-acs mode — omit entirely otherwise:]
FAILING ACS:
[paste story.qa.failures — list of failed ACs with diagnosis]
```

## Phase 4: Display Result

Display the TDD report returned by the subagent.

## Phase 5: Advance

- If `status: failed` → stop, display the failure details with 3 options:
  1. Fix the implementation → re-run `/tdd $ARGUMENTS` after fixing
  2. Fix the tests if ACs were updated → re-run `/tdd $ARGUMENTS`
  3. Block the story → drag to `blocked` on the dashboard
- If `status: passed` and called from `/next-story US X.Y` orchestrator (context says "Orchestrator context") → return the report only. The orchestrator handles `kanban-move-story` to `secops_cr`.
- If `status: passed` and called standalone (dashboard trigger) → ask:
  > "✅ TDD passed — [N] tests, [coverage]. Proceed to security code review (`secops_cr`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_cr", "tdd")` → run `/secops "$ARGUMENTS" mode=code-review`
  - **no** → stop. "To continue later: drag the card to `secops_cr` on the dashboard."
