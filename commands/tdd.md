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
3. **Capture the test baseline** — run the full test suite NOW, before any code is written, and record which tests are currently failing:

   **Backend** (always run even for frontend-only stories — shared fixtures can regress):
   ```bash
    cd backend && uv run pytest tests/unit/ tests/integration/ --tb=no -q 2>&1 | tail -30
   ```
   Capture: total passing, total failing, and the exact list of `FAILED` / `ERROR` test node IDs.

   **Frontend** (if `implementation_guide.scope` contains `frontend`):
   ```bash
   npm --prefix frontend run test:unit -- --reporter=verbose 2>&1 | tail -20
   ```
   Capture: total passing, total failing, and the list of failing test names.

   Save the output — it will be injected into the subagent as `BASELINE` so it can distinguish pre-existing failures from regressions it caused.

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

TEST STRUCTURE:
- tests/unit/        → pytestmark = pytest.mark.unit    — 0 I/O, pure logic, mocks
- tests/integration/ → pytestmark = pytest.mark.integration — AsyncClient + real test SQLite DB
- Every new test file MUST be placed in one of these two directories
- Unit test command      : uv run pytest tests/unit/ -m unit -q
- Integration test command: uv run pytest tests/integration/ -m integration -q
- Full test command      : uv run pytest tests/unit/ tests/integration/ -q

BASELINE (captured before any implementation — used for regression detection):
[paste the full output of the baseline test runs from Phase 1 — backend + frontend if applicable.
 Include: total counts AND the exact FAILED/ERROR test node IDs.]

[include only if implementation_guide.mockup_ref is set AND scope contains "frontend":]
WIREFRAME REFERENCE — READ LAYOUT ONLY, DO NOT COPY CODE:
A wireframe was generated during refinement: [paste implementation_guide.mockup_ref]
⚠️ The wireframe HTML uses gray-box placeholder classes (.btn, .field, .card) and raw
HTML elements (<div>, <button>, <input>) that are FORBIDDEN in real .vue files.
Use the wireframe ONLY to understand layout intent, component positioning, and UX flow.
For implementation, use exclusively the Storybook components from the catalog:
  <Button> instead of <button> / <div class="btn">
  <Input>  instead of <input>  / <div class="field">
  <Select> instead of <select>
  <Textbox> instead of <textarea>
If a needed UI element has no Storybook equivalent → create a backlog story for it,
use the closest existing component as a fallback, and NEVER use raw HTML elements.

[include if implementation_guide.files_create or files_modify contains workers/*.py:]
CELERY TASK REGISTRATION:
If the story creates or modifies a Celery task file (workers/*.py), add a test
that validates every @celery_app.task is registered via workers/__init__.py.

```python
# Place this test in tests/integration/test_<module>_task.py
# (marker: pytestmark = pytest.mark.integration)
def test_task_registered():
    from workers.celery_app import celery_app
    assert "workers.mymodule.my_task" in celery_app.tasks
```
Without this, calling .delay() sends a message that the worker discards as
"unregistered task" — silent data loss.

[include if implementation_guide contains "api_contracts" or any endpoint definition:]
INTEGRATION TESTS — FULL CHAIN VALIDATION:
Every API endpoint that triggers a background operation or writes to the DB
MUST have tests that validate the complete request→response chain through the
real FastAPI router (httpx.AsyncClient + ASGITransport).

For endpoints that dispatch Celery tasks:
- Mock .delay() but verify the ARGUMENTS passed (not just "was called")
- Add a test that verifies the mock's arguments match what the GET endpoint
  expects (e.g., POST /run-pipeline passes the same run_id that GET reads)
  ```python
  # Bad — only checks dispatch happened:
  mock_task.delay.assert_called_once()
  
  # Good — validates data coupling between POST and GET:
  mock_task.delay.assert_called_once_with(source_id, run_id=ANY)
  _, kwargs = mock_task.delay.call_args
  run_id = kwargs.get("run_id")
  # Then verify GET /pipeline-runs/{run_id} returns 200
  ```

For config/key/value validation:
- Test BOTH dotted keys (``litellm.timeout``) AND top-level keys
  (``feature_flags``) — the validation code path differs for each
- Test round-trip: write → read back → verify structure preserved

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
- If `status: passed` and called standalone (dashboard trigger) →
  1. Call `kanban-update-story("$ARGUMENTS", '{"agent_status": "awaiting_input"}')`
  2. Ask: "✅ TDD passed — [N] tests, [coverage]. Proceed to security code review (`secops_cr`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_cr", "tdd")` → run `/secops "$ARGUMENTS" mode=code-review`
  - **no** → `kanban-update-story("$ARGUMENTS", '{"agent_status": null}')` → stop. "To continue later: drag the card to `secops_cr` on the dashboard."
