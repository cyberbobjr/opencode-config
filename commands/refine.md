# Command: /refine — Refinement Agent

**Story ID:** `$ARGUMENTS`

Refines story `$ARGUMENTS` by challenging its acceptance criteria from 4 angles AND proposing additional ideas through a mandatory question/answer cycle.

> ⚠️ **This command ≠ field update.**
> `/refine` launches a full dialogue cycle (8–12 questions, technical plan, persistence). It must only be invoked on explicit user request or from the workflow coordinator (`/next-story`).
> To fix AC text, add a note, or update the description without restarting the refinement process: use `kanban-update-story` directly, without calling `/refine` or changing the story status.

## Core Principles

- **Refinement is a mandatory dialogue** — you do NOT produce a report alone. You challenge the requirement, propose improvement paths, and go further into the expressed needs.
- **You are also an explorer, not just a challenger** — before challenging, you identify what the story does NOT say and propose ideas that increase value.
- **MANDATORY use of the `question` tool** from OpenCode for each question. No free text, no lists in a message.
- **One question at a time** — each question uses the `question` tool, wait for the answer before the next.

## Steps

### 0. Story retrieval

Before any question:
- Call the MCP tool `kanban-get-story "US X.Y"` to retrieve the full story (description, existing ACs, priority, phase)
- Explore the existing code to understand the current state
- Identify dependencies, architecture points, and gaps
- Call `kanban-list-stories` with the same `phase` to read adjacent stories and detect opportunities

### 2. Exploration & Ideation (MANDATORY)

Before challenging existing ACs, generate **3 to 5 additional ideas** the story could cover that the ACs have not anticipated. These ideas come from 4 systematic sources:

| Source | Question to ask yourself |
|--------|--------------------------|
| **Adjacent stories** | What neighboring features could cross-pollinate this one? Is there a recurring pattern between adjacent stories that is missing here? |
| **Blind spots** | What does the story assume without stating? What happens in undocumented edge cases? |
| **User expectations** | If I were the end user, what related feature would I be surprised not to find here? |
| **Technical opportunities** | Is there a technical quick win that would multiply the value of this story without major effort? |

**Format:** Present these ideas as a structured block at the start of the dialogue:

```
## Additional ideas identified

Before challenging the existing ACs, here are areas the story does not yet cover:

1. **[Idea 1 title]** — [short description, why it adds value]
2. **[Idea 2 title]** — [short description, why it adds value]
3. **[Idea 3 title]** — [short description, why it adds value]
4. **[Idea 4 title]** — [short description, why it adds value]

I will now challenge the existing ACs and incorporate some of these ideas into the questions.
```

You do not need to validate this list immediately — it serves as raw material to enrich the 4-role questions. Each role will carry its own ideas into its dedicated questions.

### 3. Question cycle (MANDATORY)

Ask **8 to 12 questions** alternating the 4 roles. Each question uses the OpenCode `question` tool.

Rules for each question:
- **3 closed options max** (concrete choices, not empty "yes/no")
- **1 "Other" field available** automatically via `custom: true` in the `question` tool
- **Each question must challenge the requirement**, propose additional improvement paths, or go further than the initial statement
- **At least 1 question in 2 must include a new idea** (not just challenging ACs — propose a concrete addition)
- **No rhetorical questions** — every question must have a concrete impact on the implementation

Role alternation:

| Question | Lead role | Main objective | Ideation mission |
|----------|-----------|----------------|-----------------|
| 1 | **Product Owner** | Challenge business value, detect hidden needs | What adjacent feature could multiply the value delivered to the user? |
| 2 | **Architect** | Challenge technical consistency, propose patterns | What emerging pattern (or adjacent to another story) would improve overall consistency? |
| 3 | **Developer** | Clarify implementation, edge cases, tests | What edge case could become a reusable utility feature? |
| 4 | **DevSecOps** | Identify attack surfaces, propose countermeasures | What uncovered threat would deserve a dedicated protection feature? |
| 5 | **Product Owner** | Dig into functional gaps, alternatives | What unexpressed need (gathered from adjacent stories) should be addressed here? |
| 6 | **Architect** | Validate dependencies, integration, scalability | What cross-cutting optimization (cache, batch, streaming) could be anticipated in this story? |
| 7 | **Developer** | Challenge thresholds, performance, maintainability | What tooling or helper would be worth sharing with another story? |
| 8 | **DevSecOps** | Check secrets, timeouts, rate limiting | What audit / monitoring omitted from the ACs could prevent a future incident? |
| 9+ | (cycle continues if needed) | | |

### 4. Synthesis

Once all questions are answered:
1. **Summarize the decisions made** — each question → decision → impact on the ACs
2. **Produce the revised ACs** — integrate all decisions into an updated version of the ACs
3. **List the complementary suggestions proposed and their outcome**:

```
## Complementary suggestions

| Suggestion | Source | Status |
|------------|--------|--------|
| [proposed idea] | [role that raised it] | ✅ Adopted / ❌ Rejected / 🔍 To investigate |
```

4. **Assess the readiness level**:
   - ✅ **Ready** → continue to step 5
   - ⚠️ **Blockers** → list what is blocking and propose a path forward

---

### 5. Technical Plan — The HOW (MANDATORY)

After the AC synthesis, first identify the **story type**, then write the adapted plan.

#### 5a. Type identification

Determine the impacted domain(s) — a story can cover several:

| Domain | Signal in code / story |
|--------|------------------------|
| `backend` | API endpoints, services, background workers, ORM models |
| `frontend` | UI components, state stores, pages, CSS/styling |
| `database` | Migrations, schemas, indexes, SQL/graph queries |
| `devops` | Dockerfile, docker-compose, CI/CD scripts (GitHub Actions), Makefile |
| `infrastructure` | Env vars, nginx/caddy configs, third-party services, secrets |
| `architecture` | Inter-module refactoring, cross-cutting patterns, restructuring |
| `bugfix` | Correction of existing behavior — limited and precise scope |
| `security` | Auth, permissions, encryption, rate limiting, audit |
| `docs` | README, guides, docstrings, OpenAPI descriptions |

#### 5b. Plan adapted to the type

Write **only the relevant sections** for the detected type. Do not generate empty sections.

---

**For `backend`:**
- Files to create/modify (exact paths)
- Data model: new fields, migration needed (yes/no)
- API contracts: `METHOD /path` — auth required — request schema — response schema — error codes
- Background workers: task name, queue, retry policy if applicable
- Implementation sequence: model → service → route → tests

**For `frontend`:**
- UI components to create/modify (exact paths)
- State store: state added, actions, getters
- API calls: consumed endpoint, loading/error handling
- Design system: CSS tokens and reference components (see `AGENTS.md`)
- Sequence: store → component → page → tests

**For `database`:**
- Schema before / after (columns, types, constraints, indexes)
- Migration script (tool per stack, see `AGENTS.md`)
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

---

**Common fields (always present):**
- Files to create / modify / delete (exhaustive list with paths)
- New dependencies (package + version + reason) — or "none"
- Ordered implementation sequence (numbered steps)
- Constraints: imposed patterns, what NOT to do, performance thresholds

---

### 6. Persistence

At the end of refinement, persist EVERYTHING in a single call.

> **Note:** The `"stack"` field must mirror exactly the content of `implementation_guide.scope` — this is what the dashboard displays as card categories.

> ⚠️ **Description must be valid markdown** — rendered in the Kanban modal. Use `\n\n` between sections and `\n` between a heading and its body. Minimum expected structure:
> ```
> ## User Story
> **En tant que** [rôle], je veux [fonctionnalité], afin de [bénéfice].
>
> ## Contexte
> [Refined context after dialogue — what the story covers and why.]
>
> ## Décisions clés
> - [Decision 1 from refinement]
> - [Decision 2 from refinement]
> ```

```python
kanban-update-story("$ARGUMENTS", '{
  "_actor": "refine",
  "description": "## User Story\n**En tant que** [rôle], je veux [fonctionnalité], afin de [bénéfice].\n\n## Contexte\n[Refined context after dialogue.]\n\n## Décisions clés\n- [Decision 1]\n- [Decision 2]",
  "stack": ["backend", "database"],
  "acceptance_criteria": [
    {"id": 1, "text": "Revised AC 1", "checked": false},
    {"id": 2, "text": "Revised AC 2", "checked": false}
  ],
  "refine_decisions": [
    "Decision 1 made during refinement",
    "Decision 2 made during refinement"
  ],
  "implementation_guide": {
    "type": "backend | frontend | fullstack | database | devops | infrastructure | architecture | bugfix | security | docs",
    "scope": ["backend", "database"],
    "approach": "Description of the chosen technical approach",
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
      "1. First step",
      "2. Second step"
    ],
    "test_strategy": "What to test, which test type (unit/integration/e2e/smoke), which tool",
    "constraints": "What not to do, imposed patterns, performance thresholds"
  }
}')
```

**Advance to threat model:**
- **Called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → call `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` and return the report. The orchestrator continues.
- **Called standalone** → ask:
  > "✅ Refinement complete — [N] ACs validated. Proceed to threat model (`secops_tm`)? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "secops_tm", "refine")` → run `/secops "$ARGUMENTS" mode=threat-model`
  - **no** → stop. "To continue later: drag to `secops_tm` or run `/next-story secops-tm $ARGUMENTS`"

## Anti-patterns

❌ **Don't**: List 8 questions in a single text message
✅ **Do**: Use the `question` tool each time, one question per call

❌ **Don't**: Ask yes/no questions with no proposal
✅ **Do**: "Option A, Option B, Option C — which do you prefer?"

❌ **Don't**: Accept the first answer without challenging
✅ **Do**: If the answer is vague, follow up with a sub-question to clarify

❌ **Don't**: Only challenge ACs without proposing any additions
✅ **Do**: Each role proposes at least one new idea the ACs had not anticipated

❌ **Don't**: Ignore adjacent stories that could cross-pollinate this one
✅ **Do**: Read stories from the same phase and direct dependencies before asking any question

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

**Admin:**
- Do destructive actions require confirmation / soft-delete?
- Is an audit log needed?

**General:**
- Does the story introduce a new dependency? Are there known CVEs?
- Are LLM templates (prompts) protected against injection?
- Is the principle of least privilege respected?
