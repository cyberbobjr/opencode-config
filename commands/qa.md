---
description: QA Agent — validates the acceptance criteria of a user story through integration and E2E tests
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
---

# QA Agent — `/qa $ARGUMENTS`

**Story ID:** `$ARGUMENTS`

Validates that all acceptance criteria (ACs) of story `$ARGUMENTS` are covered by integration or E2E tests.

## Input Protocol

The orchestrator agent (or the user) must provide the following as input:

| Info | Source |
|------|--------|
| `story_id` | `$ARGUMENTS` |
| `ac` (acceptance criteria) | MCP tool `kanban-get-story` (from `user-stories/*.json`) |
| `tdd_report` | TDD report from the previous agent (modified files, status) |
| `context` | Project: stack, conventions |

## Output Protocol

At the end, produce this structured report to the orchestrator agent:

```markdown
# QA Report — US X.Y
**status**: passed | failed
**ac_covered**: X/Y (validated ACs / total)
**tests**: N written, N passed, N failed

**Validated ACs**:
  ✅ AC 1: "POST /api/auth/register" → test_register_returns_verification
  ✅ AC 2: "POST /api/auth/login" → test_login_returns_tokens
  ...

**Failed ACs** (ONLY if status=failed):
  ✗ AC 3: "POST /api/auth/refresh renews the token"
    test_failing  : test_refresh_returns_valid_token
    assertion     : assert response.status_code == 200 → got 401
    file          : backend/tests/test_auth.py:42
    cause         : middleware checks expiration before refresh

  ✗ AC 7: "JWT Middleware blocks unauthenticated endpoints"
    test_failing  : test_middleware_blocks_unauthenticated
    assertion     : assert response.status_code == 401 → got 200
    file          : <backend>/dependencies.<ext>:15
    cause         : endpoint is missing the authentication middleware

**notes**: observations, fragilities, suggestions
```

⚠️ **Each failed AC MUST include**: `ac_id`, `title`, `test_failing`, `assertion` (received value vs expected), `file:line`, `cause` — this diagnosis is passed entirely to TDD in corrective mode.

You must also update the story via the Kanban server MCP tools:

```bash
# At the start of validation:
# Call: kanban-update-story("US X.Y", '{"qa": {"status": "in_progress"}}')

# At the end of validation (success):
# Call: kanban-update-story("US X.Y", '{"qa": {"status": "passed", "ac_covered": "8/8", "notes": "All ACs validated"}}')

# At the end of validation (failure):
# Call: kanban-update-story("US X.Y", '{"qa": {"status": "failed", "ac_covered": "6/8", "notes": "ACs 3 and 7 not covered"}}')
```

## Internal Workflow

### 1. Initialization

1. Mark `qa.status = in_progress` via `kanban-update-story("US X.Y", '{"_actor": "qa", "qa": {"status": "in_progress"}}')`
2. Read the ACs via `kanban-get-story("US X.Y")` (from `user-stories/*.json`)
3. Re-read the implementation files (created/modified during the TDD step)
4. Read the TDD report to understand what was implemented

### 2. Map each AC → test

For each acceptance criterion, determine the required test type:

| AC Type | Test Type | Tool |
|---------|-----------|------|
| API endpoint (POST/GET/PUT/DELETE) | API integration | HTTP test client + stack test tool (see `AGENTS.md`) |
| Data validation | Unit | stack test tool |
| Business behavior | Integration | stack test tool + test DB |
| Frontend display rule | Component | frontend test tool (see `AGENTS.md`) |
| Complete user journey | E2E | E2E test tool (see `AGENTS.md`) |
| Background worker / queue | Integration | stack test tool + broker mock |

For each AC, write a test that:
1. **Explicitly verifies the behavior described in the AC**
2. Tests the nominal case (success) AND the error case (failure) where applicable
3. Includes a clear assertion of the expected result

### 3. Write and run tests

Refer to `AGENTS.md` for the project-specific test run commands per stack.

Each test must include a comment indicating which AC it covers:
```python
# AC: "POST /api/auth/register returns a verification message"
async def test_register_returns_verification_message(client):
    ...
```

### 4. AC coverage report

Build the complete AC → test mapping:

| AC | Covered | Test | File |
|----|---------|------|------|
| `POST /api/auth/register` → verification message | ✅ | `test_register_returns_verification_message` | `tests/test_auth.py:15` |
| `POST /api/auth/login` → JWT + refresh | ✅ | `test_login_returns_tokens` | `tests/test_auth.py:28` |
| ... | ❌ | `test_refresh...` fails | `tests/test_auth.py:42` |

**For each failed AC**, capture the complete diagnosis to pass to TDD:

```python
ac_id        = "AC 3"
title        = "POST /api/auth/refresh renews the token"
test_failing = "test_refresh_returns_valid_token"
assertion    = "assert response.status_code == 200 → got 401"
file         = "backend/tests/test_auth.py:42"
cause        = "middleware checks expiration before refresh"
```

### 5. Report

1. **Check each AC** based on its result — retrieve the full list via `kanban-get-story("$ARGUMENTS")`, then update `acceptance_criteria` preserving each entry's text and id:
   ```python
   # Example: ACs 1, 2, 4 pass; AC 3 fails
   kanban-update-story("$ARGUMENTS", '{"_actor": "qa", "acceptance_criteria": [
     {"id": 1, "text": "...", "checked": true},
     {"id": 2, "text": "...", "checked": true},
     {"id": 3, "text": "...", "checked": false},
     {"id": 4, "text": "...", "checked": true}
   ]}')
   ```
   Rule: `checked: true` if and only if the test covering that AC passes.

2. Mark `qa.status = passed` or `failed` via:
   ```python
   # Success (all ACs green):
   kanban-update-story("$ARGUMENTS", '{"_actor": "qa", "qa": {"status": "passed", "ac_covered": "8/8", "notes": "All ACs validated", "ac_failures": []}}')

   # Failure (includes detailed diagnostics for corrective TDD):
   kanban-update-story("$ARGUMENTS", '{"_actor": "qa", "qa": {"status": "failed", "ac_covered": "6/8", "notes": "ACs 3, 7 failed", "ac_failures": [{"ac_id": "AC 3", "title": "...", "test_failing": "...", "assertion": "...", "file": "...", "cause": "..."}]}}')
   ```
   The `ac_failures` are used by `/tdd` in `fix-failing-acs` mode to automatically resume.

3. **Pipeline auto-advance:**
   - If `passed` → `kanban-move-story("$ARGUMENTS", "simplify", "qa")` — automatic move to quality gates
   - If `failed` → stop and display the detailed failure report (user decides: fix, block, or force)
4. Return the structured report to the orchestrator agent (see format above)
5. **If the report contains failed ACs**, ensure the complete diagnosis (file, line, assertion) is usable by TDD in `fix-failing-acs` mode

## Pipeline — Next Steps

After QA passes, the orchestrator **must** continue with:

1. **Simplify** (`/simplify US X.Y`) — reuse/quality/efficiency review of the diff
2. **Commit** — only after Simplify passes

> ⚠️ Do NOT skip Simplify after QA. It is a mandatory step before commit.

## Reminders

- ❌ Never modify `user-stories/*.json` files directly — use the MCP tools (`kanban-update-story`)
- ❌ Do not modify production code — QA tests only validate
- ❌ Do not delete existing tests — only add
- ✅ QA tests complement TDD tests: they validate ACs end-to-end
- ✅ For frontend stories, prefer component tests and E2E tests (see `AGENTS.md` for tools)
- ✅ If an AC is already covered by a TDD test, note it without duplicating
