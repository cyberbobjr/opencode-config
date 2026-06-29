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

**Opportunistic SOLID detection during existing code analysis:**

For each file inspected, identify SOLID violations (direct DB instantiation in a service,
business logic in a route, external client without a wrapper, etc.).

**If the violation is in a file already in this story's `files_modify`:**
→ Integrate the refactoring directly. Annotate `"change": "feature X + SOLID refacto: [pattern]"`.

**If the violation is in a file OUTSIDE this story's scope:**

1. First check if a `[REFACTO SOLID]` story covering this module already exists:
   ```
   kanban-list-stories → filter by title containing "[REFACTO SOLID]" + module concerned
   ```

2a. **Existing story found** → enrich its description via `kanban-update-story`:
    add the file and violation identified. Do not create a duplicate.

2b. **No existing story** → create a new story:
    ```
    kanban-create-story({
      "title": "[REFACTO SOLID] <Layer or module> — <main violation>",
      "description": "## Context\nSOLID violation identified during refine of [story_id].\n\n## Files concerned\n- `[path/file.py]`: [violation description]\n\n## Target refactoring\n[SOLID pattern to apply: session injection, service extraction, etc.]",
      "type": "architecture",
      "stack": ["backend"],
      "priority": "low"
    })
    ```

**Granularity rule:** Group violations by application layer, not by file.
- ✅ `[REFACTO SOLID] Routes layer — session injection` (covers N routes)
- ❌ `[REFACTO SOLID] app/routes/sources.py` + `[REFACTO SOLID] app/routes/briefings.py`
  (too atomic, pollutes the backlog)

⚠️ Never widen the current story's `files_modify` to pull in a refactoring
of files unrelated to the feature — scope must stay coherent.

---

## Step 2 — Question Cycle (MANDATORY)

Before the first question, signal that user interaction is needed:
```
kanban-update-story("$ARGUMENTS", '{"agent_status": "awaiting_input"}')
```

### UI Wireframe (frontend / fullstack stories only)

**If the story type is `frontend` or `fullstack`**, generate an HTML wireframe and open it **before Q1** so the visual layout anchors the dialogue.

1. Write a self-contained HTML file to `/tmp/wireframe-$ARGUMENTS.html` using this template — fill in the `<div class="screen">` with the UI elements inferred from the description and ACs:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Wireframe — STORY_ID</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f0f0f0; padding: 24px; color: #333; }
  h1 { font-size: 12px; color: #999; margin-bottom: 20px; font-weight: normal; text-transform: uppercase; letter-spacing: 1px; }
  .screen { background: white; border: 2px solid #bbb; border-radius: 8px; width: 390px; min-height: 600px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.12); }
  .navbar { background: #e0e0e0; height: 52px; display: flex; align-items: center; padding: 0 16px; gap: 12px; }
  .navbar .title { font-weight: 600; font-size: 16px; color: #555; flex: 1; }
  .navbar .action { background: #ccc; border-radius: 4px; padding: 6px 12px; font-size: 12px; color: #666; }
  .body { padding: 16px; }
  .section-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; margin-top: 16px; }
  .card { background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; padding: 14px; margin-bottom: 10px; }
  .field-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
  .field { border: 1px solid #ccc; border-radius: 4px; padding: 10px; background: #fafafa; color: #bbb; font-size: 13px; margin-bottom: 10px; }
  .btn { background: #ccc; border-radius: 4px; padding: 10px 18px; font-size: 13px; color: #666; display: inline-block; margin: 4px 4px 4px 0; cursor: default; }
  .btn.primary { background: #777; color: white; }
  .btn.danger { background: #e0a0a0; color: #800; }
  .tag { background: #e4e4e4; border-radius: 10px; padding: 3px 10px; font-size: 11px; color: #777; display: inline-block; margin: 2px; }
  .row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
  .placeholder { background: #e8e8e8; border-radius: 3px; height: 13px; }
  .placeholder.short { width: 55%; }
  .placeholder.long { width: 90%; }
  .divider { border-top: 1px solid #eee; margin: 14px 0; }
  .hint { font-size: 11px; color: #bbb; font-style: italic; margin-top: 6px; }
  .badge { background: #ddd; border-radius: 10px; padding: 2px 8px; font-size: 11px; color: #666; }
  .empty { text-align: center; color: #ccc; font-size: 13px; padding: 32px 0; }
</style>
</head>
<body>
<h1>Wireframe · STORY_ID · STORY_TITLE</h1>
<div class="screen">
  <!-- Build the UI using the classes above.
       Represent every element mentioned in the ACs.
       Label all buttons, fields, and sections.
       Use .placeholder divs for list content (news items, cards, etc.).
       No real icons, no brand colors — gray-box only. -->
</div>
</body>
</html>
```

2. Open the file in the browser:
   ```bash
   open /tmp/wireframe-$ARGUMENTS.html
   ```

3. **Attach the wireframe to the story** immediately after opening it:
   ```
   kanban-attach-mockup("$ARGUMENTS",
     source_path="/tmp/wireframe-$ARGUMENTS.html",
     description="Wireframe initial — [one-line layout description]")
   ```
   The tool returns `{"mockup": {"version": N, "path": "mockups/...", ...}}`.
   Note the version number — it will be used in the Q1 reference and in Step 5.

4. Reference it at the start of **Q1**:
    > *"I've opened a wireframe in your browser (`wireframe-$ARGUMENTS.html`) and attached it to the story (v{N} — viewable at `/api/stories/$ARGUMENTS/mockups/{N}`). It represents my initial interpretation of the screen: [short layout description]. My first question is about..."*

**If the wireframe is revised during the dialogue** (e.g., after Q1 answers reveal a different layout), regenerate the HTML, overwrite the file, reopen it, and call `kanban-attach-mockup` again — a new version (`v{N+1}`) is created automatically.

**Rules for the HTML:**
- **Gray-box only** — no brand colors, no icons — every interactive element must be a labeled text box
- **Represent all ACs** — every UI element mentioned in an acceptance criterion must appear
- **Mobile-first (390 px)** unless the story explicitly targets desktop or a specific breakpoint
- **Use `.placeholder` divs for list content** — don't invent real content
- **No external dependencies** — fully self-contained, no CDN, no JS

> ⚠️ **Ce wireframe est une maquette grise — il ne représente PAS le code à écrire.**
> Les classes `.btn`, `.field`, `.card` et les éléments `<div>` sont des représentations visuelles uniquement.
> Le TDD agent qui implémentera cette story doit utiliser **exclusivement les composants Storybook**
> (`<Button>`, `<Input>`, `<Select>`, `<Textbox>`, etc.) — les éléments HTML natifs (`<button>`, `<input>`,
> `<select>`, `<textarea>`) sont **interdits** dans tout `.vue` hors de `components/ui/`.
> Ce wireframe communique le **layout et les intentions UX**, pas la stack technique.

---

Ask **4 to 6 questions** (up to 8 for complex stories). Each question uses the OpenCode `question` tool.

| Question | Lead role | Challenge objective | Ideation mission |
|----------|-----------|---------------------|-----------------|
| 1 | **Product Owner** | Business value, hidden needs | What adjacent feature could multiply value for the user? |
| 2 | **Architect** | Technical consistency, patterns | What emerging pattern would improve overall consistency? |
| 3 | **Developer** | Edge cases, implementation clarity, tests, test placement (unit vs integration) | What edge case could become a reusable utility? Identify if the logic is pure (→ `tests/unit/`) or coupled to HTTP/DB (→ `tests/integration/`). If both, propose a decoupling to make business logic unit-testable. |
| 4 | **DevSecOps** | Attack surfaces, countermeasures | What uncovered threat deserves a dedicated protection feature? |
| 5 | **Product Owner** | Functional gaps, unexpressed needs | What need from adjacent stories should be addressed here? |
| 6 | **Architect** | Dependencies, integration, scalability | What cross-cutting optimization (cache, batch, streaming) could be anticipated? |
| 7+ | (cycle continues if needed, max 8) | | |

---

### User-Driven Capture (post-personas)

Une fois le cycle des rôles terminé, demander explicitement à l'utilisateur s'il a identifié des points non couverts par les personas avant de passer à la synthèse.

1. Poser cette question via l'outil `question` :
   > *"Avant la synthèse : avez-vous d'autres points à intégrer dans cette user story qui n'auraient pas été identifiés par les personas ?"*
   - Options : `Non, les personas ont tout couvert` / `Oui, j'ai des points à ajouter`
   - `custom: true` est disponible automatiquement pour détailler
2. **Si l'utilisateur répond « Oui »** — pour chaque point apporté :
   - **Dans le périmètre de la story** → intégrer dans les ACs (réécrit en assertion testable) et/ou le `implementation_guide`
   - **Hors périmètre mais pertinent** → créer ou enrichir une story adjacente via `kanban-create-story` / `kanban-update-story` (ne pas élargir le scope de la story courante)
   - **Hors scope ou déjà couvert** → rejeter avec justification
   - Consigner chaque décision dans `refine_decisions` lors de la persistance (Step 5)
3. **Si l'utilisateur répond « Non »** → enchaîner directement sur la synthèse.

> Cette étape capte l'intention et la connaissance métier de l'utilisateur qui dépassent le cadre des 4 personas. Elle ne remplace pas les questions des rôles — elle les complète.

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

**AC Quality Gate — 3 non-negotiable rules before persisting:**

| Rule | Question to ask | ❌ Anti-pattern | ✅ Valid pattern |
|-------|---------------------|----------------|-----------------|
| **Behavioral** | Does the AC describe what the system *does* (observable results) and not *how*? | `_validate_fields() rejects category "astrology"` | `Submitting a source with an unknown category returns 422` |
| **Black-Box** | Can the AC be validated without knowing the internal architecture, function names, or hidden state? | `ALLOWED_CATEGORIES contains exactly 15 entries` | `Any category outside the official list is rejected on submission` |
| **Business Validation** | Does the AC guarantee a user need or a global contract, independently of technology? | `celery_app.conf.task_acks_late is True` | `A failed message is automatically retransmitted without loss` |

If an AC fails any of these 3 rules → rewrite it before moving forward.

---

## Step 4 — Technical Plan

Identify the **story type** then write the adapted plan. Write **only the relevant sections** for the detected type — do not generate empty sections.

### Story type

| Domain | Signal |
|--------|--------|
| `backend` | API endpoints, services, background workers, ORM models |
| `frontend` | UI components, state stores, pages, CSS/styling |
| `database` | Migrations, schemas, indexes, SQL queries |
| `devops` | Dockerfile, docker-compose, CI/CD scripts, Makefile, Celery queue wiring |
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
  - Implementation sequence: model → service (session injected as parameter)
              → route (≤ 10 lines, Depends())
              → tests/unit/ (pure logic, mocks)
              → tests/integration/ (HTTP endpoints)
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
- If the story introduces new Celery background workers, steps MUST include:
  - Declare all queues used by new tasks (via `queue=` in `@celery_app.task`)
  - Verify `celery_cli.py` and `docker-compose.yml` worker startup commands consume every declared queue via the `-Q` flag
  - If a new queue is introduced, verify no other task module was already using it to avoid unintended cross-consumption
- Constraints: imposed patterns, what NOT to do, performance thresholds
- **SOLID (new code only — no retroactive rewrite)**:
  If the story creates a new service or modifies an existing one:
  - Inject the DB session as a parameter (no `get_async_session_factory()()`
    in the service body)
  - Define an explicit interface if the component will be mocked in a unit test
  - Consume shared clients (Firecrawl, LLM, Redis, Neo4j) via
    `app/services/*.py` — never directly in routes or workers
- 🔁 **Cross-cutting services check**: If the story uses a shared infrastructure client (Firecrawl, LLM, DB, Redis, Neo4j, email), verify it is consumed through a **dedicated service wrapper** (`app/services/*.py`), not via ad-hoc instantiation. Cross-reference existing consumers with `grep` to detect inconsistent patterns before writing code. If 2+ modules instantiate the same client independently, create/extend a shared service in this story.

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
      "unit": "tests/unit/test_<module>.py — pytestmark = pytest.mark.unit — pure functions, 0 I/O, mocks for external dependencies. Test: [what deserves a unit test]",
      "integration": "tests/integration/test_<feature>_api.py — pytestmark = pytest.mark.integration — httpx.AsyncClient + ASGITransport + real test SQLite DB. Minimum: 1 success + 1 4xx error + edge cases",
      "e2e": "frontend/src/<feature>.ui-int.ts — Playwright + page.route() — or null if no frontend",
      "coverage_target": 80,
      "critical_cases": ["Edge case 1 that must never regress", "Edge case 2"]
    },
    "constraints": "What not to do, imposed patterns, performance thresholds",
    "mockup_ref": "v1 — /api/stories/$ARGUMENTS/mockups/1 (or null if no wireframe was generated)"
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
- [ ] No AC references an internal function name, constant, private class,
      or implementation detail
- [ ] Every AC can be validated black-box via the HTTP API or user interface
      — without access to source code
- [ ] The underlying business need is identifiable by reading the AC without
      technical knowledge of the project
- [ ] `approach` is specific enough that two developers would implement it the same way
- [ ] If new Celery queues are declared → `celery_cli.py` and `docker-compose.yml` worker commands include them in `-Q`
- [ ] If the story type is `frontend` or `fullstack` → a wireframe was generated, attached via `kanban-attach-mockup`, and `implementation_guide.mockup_ref` is set

If any item fails: revise before advancing.

---

**Advance to threat model:**

First, signal that the autonomous work is done:
```
kanban-update-story("$ARGUMENTS", '{"agent_status": null}')
```

- **Called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → call `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` and return the report. The orchestrator continues.
- **Called standalone** →
  1. Call `kanban-update-story("$ARGUMENTS", '{"agent_status": "awaiting_input"}')`
  2. Ask: "✅ Refinement complete — [N] ACs validated. Proceed to threat model (`secops_tm`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` → run `/secops "$ARGUMENTS" mode=threat-model`
  - **no** → `kanban-update-story("$ARGUMENTS", '{"agent_status": null}')` → stop. "To continue later: drag the card to `secops_tm` on the dashboard."

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

**Celery / Background Workers (⚠️ MANDATORY for any story that creates or modifies background workers):**
- Is every `queue=` declared in a `@celery_app.task` decorator consumed by the worker startup command (`-Q` flag in `celery_cli.py`, `docker-compose.yml`)?
- If adding a new queue name, would changing the existing `-Q` list break another queue's tasks?
- Does an integration test exercise the task through the actual Redis queue (not just `task_always_eager=True`) to catch queue mismatch?

**Admin:**
- Do destructive actions require confirmation / soft-delete?
- Is an audit log needed?

**General:**
- Does the story introduce a new dependency? Are there known CVEs?
- Are LLM templates (prompts) protected against injection?
- Is the principle of least privilege respected?
- 🔁 **Shared service audit**: If the story touches a client already used elsewhere (Firecrawl, SMTP, Neo4j, Redis, LLM), check that all consumers use a single service wrapper. Ad-hoc instantiation in multiple files = inconsistency risk + config drift.
