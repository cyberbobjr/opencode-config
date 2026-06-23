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

Audits the modified code against an automated security checklist.

### 1. Initialization

1. Run `git diff HEAD --name-only` to identify modified files
2. If no diff → skip, return `status: skipped`
3. Identify the impacted stack: backend, frontend, database (see `AGENTS.md` for project tech stack)

### 2. Per-file analysis

For each modified file, run the relevant checks via `rg`, `grep`, and manual inspection.

#### Backend

- [ ] **Secrets** — no hardcoded secret (API key, password, token, secret)
- [ ] **Input validation** — all user parameters go through schema validation (ORM/validator)
- [ ] **SQL injection** — no string concatenation in queries (parameterized ORM/driver)
- [ ] **Auth** — new endpoints carry the auth middleware (except login/register/webhook)
- [ ] **CSRF** — mutations (POST/PUT/DELETE) are protected
- [ ] **CORS** — no wildcard `*` in production
- [ ] **Error handling** — no stack trace returned to the client
- [ ] **Rate limiting** — new public endpoints are covered
- [ ] **Graph/NoSQL** — no injection (parameterized queries via driver)

#### Frontend

- [ ] **Secrets** — no token/secret in the frontend bundle (env variables only, see `AGENTS.md`)
- [ ] **XSS** — no unsanitized raw HTML binding, no dangerous interpolation
- [ ] **Token storage** — no localStorage storage (httpOnly cookie only)
- [ ] **Input validation** — client-side validation before submission (complementary to backend)

#### Dependencies

- [ ] **Dependency audit** — no new HIGH/CRITICAL vulnerability (see `AGENTS.md` for the audit command per stack)

### 3. Automated checks (to run)

```bash
# 3.1 Secrets in the diff (critical patterns — generic, adapt patterns as needed)
git diff HEAD -- ':(exclude)*.env.example' ':(exclude).env' ':(exclude)*.md' | \
  grep -inP '(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*['"'"'"](sk-|eyJ|AKIA|gh[ps]_|xox[bpar]|ghp_)' && \
  echo "⚠️  SECRETS DETECTED IN DIFF" || true

# 3.2 Check auth middleware on new route endpoints
# Adapt paths and decorator/middleware name to your project (see AGENTS.md)
# Example pattern:
# changed_routes=$(git diff HEAD --name-only -- '<backend>/routes*' '<backend>/api*')
# Check new endpoints lack the authentication decorator/middleware

# 3.3 Dependency audit if package manifest modified
# Adapt command to your stack (see AGENTS.md): npm audit, pip audit, cargo audit, etc.
# Example: git diff HEAD --name-only | grep -q 'package.json' && npm audit --audit-level=high || true

# 3.4 Unsanitized raw HTML binding in frontend
# Adapt pattern to your framework (see AGENTS.md)
# Vue: grep for v-html; React: grep for dangerouslySetInnerHTML; Angular: grep for [innerHTML]
git diff HEAD -- '*.ts' '*.vue' '*.js' '*.tsx' '*.jsx' | grep '^+' | \
  grep -P 'v-html|dangerouslySetInnerHTML|\[innerHTML\]' && \
  echo "⚠️  Raw HTML binding detected — verify content is sanitized" || true

# 3.5 Token storage in localStorage/sessionStorage
git diff HEAD -- '*.ts' '*.vue' '*.js' '*.tsx' '*.jsx' | grep '^+' | \
  grep -P 'localStorage|sessionStorage' | grep -iP 'token|session|auth' && \
  echo "⚠️  Token storage in localStorage detected" || true
```

### 4. Report

```markdown
# SecOps Report — US X.Y
**mode**: code-review
**status**: passed | failed | skipped
**files_audited**: [N files]

**Backend**:
  ✅ Secrets — none hardcoded
  ✅ Input validation — schema validation present
  ⚠️ Auth — endpoint POST /api/admin/import_csv without auth middleware
  ...

**Frontend**:
  ✅ XSS — no dangerous raw HTML binding
  ...

**Dependencies**:
  ✅ Dependency audit — clean
  ...

**issues**: [ONLY if status=failed]
  - CRITICAL: endpoint POST /api/admin/import_csv without auth middleware
    → file: <backend>/routes/admin.<ext>:25
    → risk: unauthenticated execution
    → fix: add authentication and admin role middleware
  - ...

**notes**: [observations, false positives, non-blocking alerts]
```

### 5. Persistence and auto-advance

Persist the results in the story via MCP:
```python
kanban-update-story("[story_id]", '{"_actor": "secops-cr", "secops_report": {"mode": "code-review", "status": "passed|failed|skipped", "files_audited": 5, "issues": [...], "notes": "..."}}')
```

Statuses:
- `passed` — no security issues
- `failed` — at least one critical issue (must be fixed before QA)
- `skipped` — no code to audit (documentation story, config, CI)

**Advance to QA:**
- If `failed` → stop and display the issues (user fixes before continuing)
- If `passed` or `skipped` and **called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → return the report and stop. The orchestrator handles the move to `qa`.
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
