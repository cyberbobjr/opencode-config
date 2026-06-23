---
description: DevSecOps Agent — security review in two modes (threat-model + code-review)
argument:
  required: true
  description: "Story ID (e.g. 'US 1.3')"
options:
  mode:
    description: "Review mode: threat-model (during refinement) or code-review (after TDD)"
    default: "code-review"
---

# SecOps Agent — `/secops $ARGUMENTS`

**Received arguments:** `$ARGUMENTS`
(story ID = first value in quotes or before `mode=` ; mode = value after `mode=`, default `code-review`)

Security review at two points in the cycle:

| Mode | Timing | Objective |
|------|--------|-----------|
| `threat-model` | During refinement | Identify attack surfaces before writing code |
| `code-review` | After TDD, before QA | Audit the implemented code against an OWASP checklist |

---

## Mode: threat-model

Challenges the story from a **DevSecOps** angle:
anticipate security risks before they are coded.

### 1. Initialization

1. Read the ACs via `kanban-get-story("US X.Y")` from `user-stories/*.json`
2. Read the refinement report (`/refine`) for context
3. Identify sensitive surfaces

### 2. Sensitive surface detection

Determine whether the story touches one or more of these domains:

| Domain | Examples |
|--------|----------|
| Authentication | login, register, refresh token, password reset, OAuth |
| Authorization | roles, permissions, admin, team management, onboarding |
| Personal data | email, name, profile, preferences, news profile |
| Payment | payment processor, subscription, pricing, checkout, webhook |
| Upload | file, image, CSV import |
| External API | third-party APIs, SMTP, incoming webhooks |
| Administration | admin panel, resources, users, jobs, logs, configuration |
| Database | SQL queries, migration, encrypted data, graph queries |
| LLM pipeline | raw texts, prompt templates, AI-generated content |

### 3. Threat modeling questions

For each identified surface, use the `question` tool to validate critical points.
**Only ask questions relevant to the detected surfaces** — ask nothing if no sensitive surface is found.

**Auth:**
- Who can access this endpoint? Is there a privilege escalation risk?
- Are tokens protected (httpOnly, expiration, refresh rotation)?
- Is rate limiting planned for sensitive endpoints (login, register)?

**Authorization:**
- Are role checks done server-side (not just UI)?
- Are admin endpoints protected by an admin role middleware?

**Personal data:**
- What PII data is transmitted or persisted?
- Could logs expose sensitive data?
- Is at-rest encryption needed?

**Payment:**
- Is the payment webhook authenticated by payload signature?
- Are amounts always verified server-side (never trust the client)?
- Is the transaction history write-protected?

**Upload:**
- Is type/size validation done server-side (not just frontend)?
- Is the file stored outside the webroot?
- Are filenames sanitized (path traversal)?

**External API:**
- Are API keys in env vars, never in code?
- Is there retry with exponential backoff without replay risk?
- Is a timeout configured to avoid worker starvation?

**Administration:**
- Do destructive actions (DELETE, deactivation) require confirmation?
- Is there an audit log for admin actions?

**LLM pipeline:**
- Are user prompts sanitized before being injected into the LLM prompt (prompt injection)?
- Are texts scraped from external sources filtered?
- Does AI-generated content contain unauthorized personal data?

### 4. Report — Security Brief

```markdown
# Security Brief — US X.Y
**surfaces**: [list of sensitive domains detected, or "none"]
**risks**: [if surfaces detected, the identified risks]
**recommendations**: [concrete actions before implementation]
**review_required**: true | false
```

- `review_required: false` → the coordinator proceeds to implementation
- `review_required: true` → the coordinator must obtain risk validation before coding

### 5. Persistence and auto-advance

Persist the results in the story via MCP:
```python
kanban-update-story("[story_id]", '{"_actor": "secops-tm", "secops_report": {"mode": "threat-model", "surfaces": ["..."], "risks": ["..."], "recommendations": ["..."], "review_required": true/false}}')
```

**Advance to implementation:**
- If `review_required: true` → stop and display the Security Brief (user validates before continuing)
- If `review_required: false` and **called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → return the report and stop. The orchestrator handles the move to `tdd`.
- If `review_required: false` and **called standalone** → ask:
  > "✅ Threat model — no blocking risk. Proceed to TDD implementation? [yes / no]"
  - **yes** → `kanban-move-story("[story_id]", "tdd", "secops-tm")`
  - **no** → stop. "To continue later: drag to `tdd` or run `/next-story implement [story_id]`"

---

## Mode: code-review

Thin wrapper that assembles context and delegates the audit to the isolated `secops-cr` subagent.

### Phase 1: Gather Context

1. Run `git diff HEAD` and capture the full output
2. Call `kanban-get-story("[story_id]")` to retrieve the full story (stack, implementation_guide)
3. Read `AGENTS.md` — extract: stack info, backend/frontend paths, dependency audit command

### Phase 2: Launch SecOps-CR Subagent

Use the **Task tool** to launch the `secops-cr` subagent with `subagent_type: "secops-cr"`.

Inject the following as the Task prompt (replace placeholders with actual values):

```
story_id: [story_id]
is_orchestrated: false

STORY JSON:
[paste the full JSON returned by kanban-get-story]

GIT DIFF:
[paste the full output of git diff HEAD]

AGENTS.MD CONVENTIONS:
[paste the relevant AGENTS.md sections: stack, backend/frontend paths, dependency audit command]

Instructions:
- Audit the modified code against the OWASP checklist
- Update the story secops_report via MCP tools (kanban-update-story)
- At the end, return the structured SecOps CR report
```

> **Note:** If this command is called from `/next-story` with the explicit annotation "Orchestrator context", set `is_orchestrated: true` in the prompt so the subagent does not ask about advancing.

### Phase 3: Display Result

Display the SecOps CR report returned by the subagent.

### Phase 4: Advance

- If `status: failed` → stop and display the issues (user fixes before continuing)
- If `passed` or `skipped` and **called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → return the report. The orchestrator handles the move to `qa`.
- If `passed` or `skipped` and **called standalone** → ask:
  > "✅ SecOps code review — [passed/skipped]. Proceed to QA validation? [yes / no]"
  - **yes** → `kanban-move-story("[story_id]", "qa", "secops-cr")` → run `/qa [story_id]`
  - **no** → stop. "To continue later: drag to `qa` or run `/next-story qa [story_id]`"

## Reminders

- ❌ Do not modify production code — the review is non-invasive
- ❌ Do not ask unnecessary questions in threat-model mode (only for detected surfaces)
- ✅ In code-review mode, clearly distinguish real issues from false positives
- ✅ Flag pre-existing issues (present before the story) in `notes`, not in `issues`
- ✅ If a critical issue is out of scope for the story, flag it and recommend a dedicated User Story
