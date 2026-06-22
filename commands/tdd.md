---
description: TDD Agent — implements a user story with Test-Driven Development (red → green → refactor)
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# TDD Agent — `/tdd $ARGUMENTS`

**Story ID:** `$ARGUMENTS`

Implements story `$ARGUMENTS` with the **Red → Green → Refactor** cycle.

## Input Protocol

The orchestrator agent (or the user) must provide the following as input:

| Info | Source | Description |
|------|--------|-------------|
| `story_id` | `$ARGUMENTS` | e.g. "US 1.3" |
| `mode` | Orchestrator | `full-cycle` (default) or `fix-failing-acs` (when QA failed) |
| `ac` | MCP `kanban-get-story` | Acceptance criteria from `user-stories/*.json` |
| `implementation_guide` | MCP `kanban-get-story` | **Technical plan from refinement** — files, schema, API contracts, sequence (field `implementation_guide`) |
| `context` | Project | stack conventions from `AGENTS.md` |
| `design_system` (if frontend) | Design system reference (see `AGENTS.md`) | CSS tokens, palette, typography |
| `ac_failing` (if mode=fix) | QA report | List of failed ACs with diagnosis: `ac_id`, `title`, `test_failing`, `error`, `file`, `line` |

## Output Protocol

At the end, produce this structured report to the orchestrator agent:

```markdown
# TDD Report — US X.Y
**status**: passed | failed
**tests**: N created, N passed, N failed
**coverage**: XX%
**files**: list of modified/created files
**notes**: blockers, remarks, uncovered edge cases
```

You must also update the story via the Kanban server MCP tools:

```bash
# At the start of implementation:
# Call: kanban-update-story("US X.Y", '{"tdd": {"status": "in_progress"}}')

# At the end of implementation (success):
# Call: kanban-update-story("US X.Y", '{"tdd": {"status": "passed", "tests": 10, "coverage": "92%", "notes": "All unit tests pass"}}')

# At the end of implementation (failure):
# Call: kanban-update-story("US X.Y", '{"tdd": {"status": "failed", "tests": 5, "coverage": "40%", "notes": "Database connection not mocking correctly"}}')
```

> MCP tools are available once the Kanban server is running (`python .opencode/kanban/server.py`). Use `kanban-get-story` to read the ACs and `kanban-update-story` to persist TDD results.

## Internal Workflow

### 0. Mode selection

**If `mode = fix-failing-acs`** (corrective mode after QA failure):

1. Mark `tdd.status = in_progress` via `kanban-update-story("US X.Y", '{"_actor": "tdd", "tdd": {"status": "in_progress"}}')`
2. Read the `ac_failing` list provided by the orchestrator (failed ACs + diagnosis)
3. Ignore already-green ACs — only work on these
4. Go directly to step **2. RED** with the failed ACs only
5. **Absolute rule**: do NOT modify code for already-validated ACs

**If `mode = full-cycle`** (default, first implementation):

Continue normally to step 1 below.

---

### 1. Initialization

1. Mark `tdd.status = in_progress` via `kanban-update-story("$ARGUMENTS", '{"_actor": "tdd", "tdd": {"status": "in_progress"}}')`
2. Read the full story via `kanban-get-story("$ARGUMENTS")` — retrieve ACs, `implementation_guide`, description
3. Read `AGENTS.md` for project conventions
4. **Determine the work type** from `implementation_guide.type` (or infer from ACs if absent):
   - `backend` | `frontend` | `fullstack` | `database` | `devops` | `infrastructure` | `architecture` | `bugfix` | `security` | `docs`
5. **If `implementation_guide` is present and non-empty** — use it as a blueprint:
   - `steps` → implementation sequence to follow
   - `files_create` / `files_modify` / `files_delete` → exact scope
   - `test_strategy` → type of tests to write
   - `constraints` → rules not to break
   - Type-specific sections (`data_model`, `api_contracts`, `devops_changes`…)
6. **If `implementation_guide` is absent** — explore the existing code to infer the approach
7. **If type includes `frontend`** — read the design system reference defined in `AGENTS.md`
8. Announce the plan: list the files you will create/modify before starting

### 2. RED — Write the failing tests

Adapt the test type to the story domain:

| Story type | Test type | Tool |
|------------|-----------|------|
| `backend` — business logic | Unit | stack test tool (see `AGENTS.md`) |
| `backend` — API endpoint | Integration | stack test tool + HTTP test client |
| `backend` — background worker | Integration | stack test tool + broker mock |
| `frontend` — component | Component | frontend test tool (see `AGENTS.md`) |
| `frontend` — page / flow | E2E | E2E test tool (see `AGENTS.md`) |
| `database` — migration | DB integration | stack test tool + test DB |
| `devops` / `infrastructure` | Smoke test | bash script or stack test tool |
| `architecture` — refactoring | Existing tests (must not break) | per stack |
| `bugfix` | Regression test | per stack |
| `security` | Abuse / penetration test | per stack |
| `docs` | No RED/GREEN test | manual verification |

General rules:
- Write the test **before** the production code — it must fail (`red`)
- One test per scenario (nominal + edge cases)
- Naming: `test_<feature>_<scenario>` (e.g. `test_auth_register_success`)
- Mock external dependencies (message brokers, graph databases, SMTP, payment services, third-party APIs)
- **In fix mode**: read the QA error (file, line, message) to guide the correction

### 3. GREEN — Implement the minimum code

Write just enough to make the tests pass:
- Do not over-engineer (YAGNI) — implement exactly what the test requires
- Follow project conventions (naming, structure, patterns from `AGENTS.md`)
- Follow the `implementation_guide.steps` sequence if available

### 4. REFACTOR — Clean up without breaking

Once tests are green:
- Refactor if needed — remove duplication, improve readability
- Do not change observable behavior — tests must still pass
- For `architecture` / `refactoring`: this is the main step — verify that zero existing tests regress

### 5. Quality Gates

Run **only the relevant checks** for the story type. Refer to `AGENTS.md` for the project-specific commands.

General categories to cover:

- **Backend** — lint, type check, unit + integration tests
- **Frontend** — lint, type check, component tests, E2E
- **DevOps / Infrastructure** — validate config syntax, verify images build
- **Database (migration)** — check migration consistency, apply on test DB, verify rollback
- **Docs** — verify links are not broken, code examples compile

For `bugfix` and `security`: run the gates for the impacted stack.

Fix all issues before moving to the next step.

### 6. Report

1. Mark `tdd.status = passed` (or `failed`) via:
   ```bash
   kanban-update-story("$ARGUMENTS", '{"_actor": "tdd", "tdd": {"status": "passed", "tests": 10, "coverage": "92%", "notes": "All tests pass"}}')
   ```
2. **Pipeline auto-advance:**
   - If `passed` → `kanban-move-story("$ARGUMENTS", "secops_cr", "tdd")` — automatic move to security review
   - If `failed` → stop and display the failure report (user decides what to do next)
3. Return the structured report to the orchestrator agent

## Reminders

- ❌ Never modify `user-stories/*.json` files directly — use the MCP tools (`kanban-update-story`)
- ❌ Do not add code comments unless necessary
- ✅ Follow project conventions (AGENTS.md)
- ✅ For frontend, strictly follow the design system
- ✅ If blocked, return `status: failed` with notes explaining the blocker
