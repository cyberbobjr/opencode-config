# Command: /refine — Refinement Agent

**Story ID:** `$ARGUMENTS`

Refines story `$ARGUMENTS` by challenging its acceptance criteria from 4 angles and proposing additions through a mandatory question/answer cycle.

> ⚠️ **This command ≠ field update.**
> `/refine` launches a full dialogue cycle (4–6 questions, technical plan, persistence). It must only be invoked on explicit user request or from the workflow coordinator (`/next-story`).
> To fix AC text, add a note, or update the description without restarting the refinement: use `kanban-update-story` directly, without calling `/refine` or changing the story status.

## Core Principles

- **Refinement is a mandatory dialogue** — do NOT produce a report alone. Challenge the requirement, propose improvement paths, go further into expressed needs.
- **One question at a time** — each question uses the OpenCode `question` tool; wait for the answer before the next.
- **3 closed options max per question** (concrete choices, not empty "yes/no") — `custom: true` is available automatically via the tool.
- **Every question must have a concrete impact** on the implementation — no rhetorical questions, no questions whose answer changes nothing.
- **At least 1 question in 2 must propose a new idea** — not just challenge existing ACs, but suggest an addition the story has not anticipated.
- **If an AC remains ambiguous after the dialogue**, rewrite it until it is an unambiguous, testable assertion before advancing. "User can..." is not a testable assertion.

---

## Step 1 — Story Retrieval

Before any question:
1. Call `kanban-get-story("$ARGUMENTS")` — retrieve description, ACs, priority, phase, stack
2. Explore existing code to understand the current state (relevant modules, existing patterns)
3. Identify dependencies, architecture points, and gaps
4. Call `kanban-list-stories` with the same `phase` — read adjacent stories to detect cross-pollination opportunities
5. Check available backend routes — use the API spec command defined in `AGENTS.md` or `.opencode/rules/commands.md`. If a required route is missing or unexposed, include its creation as part of this story rather than adding a conflicting endpoint later.

---

## Step 2 — Question Cycle (MANDATORY)

Ask **4 to 6 questions** (up to 8 for complex stories). Each question uses the OpenCode `question` tool.

| Question | Lead role | Challenge objective | Ideation mission |
|----------|-----------|---------------------|-----------------|
| 1 | **Product Owner** | Business value, hidden needs | What adjacent feature could multiply value for the user? |
| 2 | **Architect** | Technical consistency, patterns | What emerging pattern would improve overall consistency? |
| 3 | **Developer** | Edge cases, implementation clarity, tests | What edge case could become a reusable utility? |
| 4 | **DevSecOps** | Attack surfaces, countermeasures | What uncovered threat deserves a dedicated protection feature? |
| 5 | **Product Owner** | Functional gaps, unexpressed needs | What need from adjacent stories should be addressed here? |
| 6 | **Architect** | Dependencies, integration, scalability | What cross-cutting optimization (cache, batch, streaming) could be anticipated? |
| 7+ | (cycle continues if needed, max 8) | | |

---

## Step 3 — Synthesis

Once all questions are answered:

1. **Summarize decisions** — each question → decision → impact on the ACs
2. **Produce revised ACs** — integrate all decisions; every AC must be a testable assertion (Given/When/Then or equivalent — no vague "user can..." phrasing)
3. **List complementary suggestions and their outcome**:

```
## Complementary suggestions

| Suggestion | Source | Status |
|------------|--------|--------|
| [proposed idea] | [role] | ✅ Adopted / ❌ Rejected / 🔍 To investigate |
```

4. **Readiness check**:
   - ✅ **Ready** → continue to Step 4
   - ⚠️ **Blockers** → list what is blocking, propose a path forward; do NOT advance until resolved

---

## Step 4 — Technical Plan

Identify the **story type** then write the adapted plan. Write **only the relevant sections** for the detected type — do not generate empty sections.

### Story type

| Domain | Signal |
|--------|--------|
| `backend` | API endpoints, services, background workers, ORM models |
| `frontend` | UI components, state stores, pages, CSS/styling |
| `database` | Migrations, schemas, indexes, SQL queries |
| `devops` | Dockerfile, docker-compose, CI/CD scripts, Makefile |
| `infrastructure` | Env vars, nginx/caddy configs, third-party services, secrets |
| `architecture` | Inter-module refactoring, cross-cutting patterns, restructuring |
| `bugfix` | Correction of existing behavior — limited and precise scope |
| `security` | Auth, permissions, encryption, rate limiting, audit |
| `docs` | README, guides, docstrings, OpenAPI descriptions |

### Plan per type

**For `backend`:**
- Files to create/modify (exact paths)
- Data model: new fields, migration needed (yes/no)
- API contracts: `METHOD /path` — auth required — request schema — response schema — error codes
- Background workers: task name, queue, retry policy if applicable
- Implementation sequence: model → service → route → tests
- **Integration tests — ⚠️ MANDATORY** — every new API endpoint must include:
  - Minimum 1 happy-path integration test (expected 2xx)
  - Minimum 1 error-case test (invalid input → 4xx)
  - Edge case tests: duplicate, missing auth, non-admin access, not-found
  - Tests use `httpx.AsyncClient` with `ASGITransport` (FastAPI TestClient pattern)
  - Auth tokens created via DB fixture + `AuthService.create_access_token()`, NOT via the register endpoint (avoids rate limiters)

**For `frontend`:**
- UI components to create/modify (exact paths)
- State store: state added, actions, getters
- API calls: consumed endpoint, loading/error handling
- Design system: CSS tokens and reference components (see `AGENTS.md`)
- Sequence: store → component → page → tests
- **E2E tests (Playwright + mock API via `page.route()`) — ⚠️ MANDATORY**
  - Every AC covering a page or user flow must be tagged `[UI-INT]`
  - Minimum 1 nominal test + boundary tests (validation error, empty states, timeouts)
  - Mock API must cover all backend calls in the tested scenario

**For `database`:**
- Schema before / after (columns, types, constraints, indexes)
- Migration script: use the tool defined in `AGENTS.md` for this stack
- Verification command: use the DB introspection command defined in `AGENTS.md` (stack-specific)
- Impact on existing queries
- Rollback strategy

**For `devops` / `infrastructure`:**
- Config files to create/modify (Dockerfile, compose, CI yml)
- Added environment variables (name, type, example value)
- Impacted external services
- Deployment / validation procedure

**For `architecture` / `refactoring`:**
- Exact scope: touched modules, modified interfaces
- Target pattern vs current pattern
- Progressive migration plan (steps without breaking tests)
- Maintained contracts (public API, interface, schema)

**For `bugfix`:**
- Bug reproduction: exact steps, stacktrace or log
- Root cause identified: file, line, failing logic
- Proposed fix: minimal diff — touch only what is needed
- Regression test to write

**For `security`:**
- Attack surface: vector, exposed data
- Countermeasure: precise implementation (middleware, decorator, validation)
- Security tests: abuse cases to cover

**For `docs`:**
- Files to create/modify
- Target audience and expected level of detail
- Required code examples or diagrams

**Common fields (always present):**
- Files to create / modify / delete (exhaustive list with exact paths — no stubs like `src/...`)
- New dependencies (package + version + reason) — or "none"
- Ordered implementation steps — each step must map to ≤ 1 file or 1 test fixture
- If `database` is in scope, steps MUST include:
  - Apply migration: use the command from `AGENTS.md` / `.opencode/rules/commands.md`
  - Verify migration applied: use the DB introspection command for this stack (see `AGENTS.md`)
  - Verify rollback: run downgrade then upgrade (or equivalent per stack)
- Constraints: imposed patterns, what NOT to do, performance thresholds

---

## Step 5 — Persistence

Persist everything in a single `kanban-update-story` call.

> **Note:** The `"stack"` field must mirror exactly the content of `implementation_guide.scope` — this is what the dashboard displays as card categories.

> ⚠️ **Description must be valid Markdown** — rendered in the Kanban modal. Use `\n\n` between sections and `\n` between a heading and its body.

```python
kanban-update-story("$ARGUMENTS", '{
  "_actor": "refine",
  "description": "## User Story\n**As a** [role], I want [feature], so that [benefit].\n\n## Context\n[Refined context after dialogue — what the story covers and why.]\n\n## Key decisions\n- [Decision 1 from refinement]\n- [Decision 2 from refinement]",
  "stack": ["backend", "database"],
  "acceptance_criteria": [
    {"id": 1, "text": "AC 1 as a testable assertion [UI-INT]", "checked": false},
    {"id": 2, "text": "AC 2 as a testable assertion", "checked": false}
  ],
  "refine_decisions": [
    "Decision 1 made during refinement",
    "Decision 2 made during refinement"
  ],
  "implementation_guide": {
    "type": "backend | frontend | fullstack | database | devops | infrastructure | architecture | bugfix | security | docs",
    "scope": ["backend", "database"],
    "approach": "Description of the chosen technical approach — specific enough that two developers would implement it the same way",
    "files_create": [
      {"path": "exact/path/file.py", "role": "Role of the file"}
    ],
    "files_modify": [
      {"path": "exact/path/file.py", "change": "What changes and why"}
    ],
    "files_delete": [
      {"path": "exact/path/file.py", "reason": "Why deleted"}
    ],
    "data_model": "Data schema if applicable — empty otherwise",
    "api_contracts": [],
    "devops_changes": [],
    "dependencies": [],
    "steps": [
      "1. First step (1 file or 1 test fixture)",
      "2. Second step"
    ],
    "test_strategy": {
      "unit": "What to unit-test and with which tool — or null if not applicable",
      "integration": "Which endpoints/services to integration-test — tool, auth fixture approach, minimum cases",
      "e2e": "Which user flows to cover with Playwright — nominal + boundary cases, mocked routes — or null if not applicable",
      "coverage_target": 80,
      "critical_cases": ["Edge case 1 that must not regress", "Edge case 2"]
    },
    "constraints": "What not to do, imposed patterns, performance thresholds"
  }
}')
```

### Implementation guide quality gate

**Before calling `kanban-move-story` to advance**, verify every item:

- [ ] `files_create` and `files_modify` have exact paths (no `src/...` stubs)
- [ ] `steps` are granular enough that each maps to ≤ 1 file or 1 test fixture
- [ ] `test_strategy` has content in every relevant field — not a generic sentence
- [ ] `critical_cases` lists at least the edge cases identified during the dialogue
- [ ] Every AC is a testable assertion — no "user can..." phrasing
- [ ] `approach` is specific enough that two developers would implement it the same way

If any item fails: revise before advancing.

---

**Advance to threat model:**
- **Called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → call `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` and return the report. The orchestrator continues.
- **Called standalone** → ask:
  > "✅ Refinement complete — [N] ACs validated. Proceed to threat model (`secops_tm`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` → run `/secops "$ARGUMENTS" mode=threat-model`
  - **no** → stop. "To continue later: drag the card to `secops_tm` on the dashboard."

---

## DevSecOps Reference

When wearing the DevSecOps hat, draw from these questions based on the story:

**Authentication / Authorization:**
- Should this endpoint be protected by the authentication middleware?
- Is there a privilege escalation risk? Are checks server-side (not just UI)?
- Is the refresh token rotated on each use?

**Data:**
- Does the story handle personal data (PII)? Is encryption needed?
- Could logs expose sensitive data?
- Is at-rest encryption needed?

**API / Webhooks:**
- Are external API keys in env vars, never hardcoded?
- Are incoming webhooks authenticated (signature, IP whitelist)?
- Is rate limiting planned?

**Database migrations (⚠️ MANDATORY for any story with `database` in scope):**
- How will the migration be applied to the existing dev database?
- What verification confirms the migration was applied successfully?
- Is there a rollback strategy if the migration fails?
- Does the test suite validate the migration against a pre-existing DB (not just `create_all` on a fresh DB)?

**Admin:**
- Do destructive actions require confirmation / soft-delete?
- Is an audit log needed?

**General:**
- Does the story introduce a new dependency? Are there known CVEs?
- Are LLM templates (prompts) protected against injection?
- Is the principle of least privilege respected?
