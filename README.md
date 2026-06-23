# opencode-config

A ready-to-use configuration template for [OpenCode](https://opencode.ai) that gives your AI coding agent a **structured, trackable development pipeline**.

At its core: a Kanban server that works simultaneously as a **web dashboard**, a **REST API**, and an **MCP server** — letting the agent read and update project state, while letting the developer steer from a drag-and-drop UI.

---

## What this gives you

- **A Kanban board** connected to your agent via MCP — stories move through columns as the agent works
- **A bidirectional bridge** — dragging a card on the dashboard injects a slash command into the OpenCode TUI
- **Slash commands** for every stage of the development cycle (refinement, TDD, security review, QA, commit)
- **Isolated sub-agents** for TDD, QA, SecOps code review, and code simplification — each runs in its own context with injected story data
- **A structured pipeline** that enforces TDD, SecOps review, and QA validation before any commit
- **Story qualification** — `/fix`, `/feature`, `/change` scan the codebase and produce a normalized story draft before persisting

---

## Repository structure

```
.opencode/
├── opencode.json          — MCP server configuration (consumed by OpenCode)
├── package.json           — Node dependencies (optional tooling)
│
├── commands/              — Slash commands (prompts injected into OpenCode's main agent)
│   ├── next-story.md      — Workflow coordinator: full cycle or individual steps
│   ├── refine.md          — Refinement: 8–12 questions, 4 roles (PO/Architect/Dev/DevSecOps)
│   ├── tdd.md             — Thin wrapper → launches tdd subagent via Task tool
│   ├── secops.md          — Threat model (inline) + code review wrapper → launches secops-cr subagent
│   ├── qa.md              — Thin wrapper → launches qa subagent via Task tool
│   ├── simplify.md        — Launches 3 simplify sub-agents in parallel via Task tool
│   ├── architect.md       — Architecture design (question/answer cycle)
│   ├── review-pr.md       — GitHub PR review and response
│   ├── commit.md          — Conventional commit helper
│   ├── feature.md         — Create a new feature story with qualification phase
│   ├── fix.md             — Create a bug story with qualification phase
│   └── change.md          — Create a change story with impact analysis
│
├── agents/                — Sub-agents (mode: subagent, isolated context, own permissions)
│   ├── tdd.md             — RED/GREEN/REFACTOR cycle, writes tests first, then code
│   ├── qa.md              — AC validation through integration and E2E tests
│   ├── secops-cr.md       — OWASP code review (read+bash only, non-invasive)
│   ├── code-simplify-reuse.md
│   ├── code-simplify-quality.md
│   └── code-simplify-efficiency.md
│
└── kanban/                — Kanban MCP server + Vue dashboard
    ├── server.py          — Main server (FastAPI + FastMCP, serves dist/)
    ├── requirements.txt
    ├── migrate.py         — Schema migration for existing stories
    ├── dist/              — Built Vue app (served by FastAPI at /)
    │   ├── index.html
    │   └── assets/        — Hashed JS + CSS bundles
    └── frontend/          — Vue 3 source (edit here, then npm run build)
        ├── package.json
        ├── vite.config.js
        ├── tailwind.config.js
        └── src/
            ├── App.vue
            ├── api.js
            ├── constants.js
            └── components/
                ├── KanbanBoard.vue
                ├── SimpleView.vue
                ├── FocusView.vue
                ├── JournalView.vue
                ├── ListView.vue
                ├── StoryModal.vue
                ├── KanbanCard.vue
                ├── StatsBar.vue
                └── MarkdownContent.vue
```

Story data lives **outside** this repo, in `user-stories/*.json` at the project root — one JSON file per story, served by the Kanban server.

---

## Quick start

### 1. Install Python dependencies

```bash
pip install -r .opencode/kanban/requirements.txt
```

### 2. Build the dashboard (first time only)

The `dist/` folder is committed and ready to use. To rebuild after modifying the Vue frontend:

```bash
cd .opencode/kanban/frontend
npm install   # first time only
npm run build # output → ../dist/
```

For hot-reload development (proxy to backend at `:8765`):

```bash
npm run dev   # Vite dev server at http://localhost:5173
```

### 3. Start the Kanban server

OpenCode automatically starts the server via MCP. You can also run it manually:

```bash
# Dashboard + MCP (standard mode)
python .opencode/kanban/server.py --mcp

# Debug mode — logs every MCP call with parameters
python .opencode/kanban/server.py --mcp --debug
```

Dashboard: `http://localhost:8765`

> **Important**: let OpenCode start the server — it binds both MCP (stdio) and HTTP (port 8765) in the same process. Running a second instance creates two separate processes with desynchronized state.

### 4. Configure OpenCode

The `opencode.json` at the root of this repo already wires the Kanban server as an MCP provider:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "kanban": {
      "type": "local",
      "command": ["python", ".opencode/kanban/server.py", "--mcp", "--debug"],
      "enabled": true
    }
  }
}
```

Copy it to your project root (or merge with your existing `opencode.json`).

### 5. Add your project conventions

Commands reference `AGENTS.md` at the project root for stack-specific details (test runner, lint commands, file paths, design system). Create one if you don't have it — see the [AGENTS.md template](#agentsmd-template) section below.

---

## The pipeline

Every user story follows a fixed sequence of stages. The agent tracks its own position; the developer can observe or override from the dashboard.

```
pending → refining → secops_tm → tdd → secops_cr → qa → simplify → commit_ready → completed
```

| Stage | What happens |
|-------|-------------|
| `pending` | Story is waiting — not yet refined |
| `refining` | `/refine` challenges the ACs through an 8–12 question dialogue |
| `secops_tm` | `/secops mode=threat-model` identifies attack surfaces before coding |
| `tdd` | `tdd` subagent implements the story with Red → Green → Refactor |
| `secops_cr` | `secops-cr` subagent audits the diff against an OWASP checklist |
| `qa` | `qa` subagent validates every AC with integration or E2E tests |
| `simplify` | 3 sub-agents review for quality, reuse, and efficiency in parallel |
| `commit_ready` | User approves the commit message |
| `completed` | Story committed and done |

Start the full cycle with:

```
/next-story US X.Y
```

Or drive individual steps from the dashboard by dragging cards between columns — the server injects the right command into OpenCode automatically.

---

## Three interaction modes

The same pipeline can be driven three ways, with different levels of automation:

### 1. `/next-story US X.Y` — Fully automatic

The pipeline runs end-to-end with minimal interruptions:
- Sub-agents execute in sequence, each receives story context via Task tool injection
- **2 fixed stop points**: after refinement (before coding) and before commit
- **1 conditional stop**: if QA fails — user decides how to proceed
- Sub-agents do not ask about advancing to the next stage

### 2. Manual commands — Single step

`/tdd US X.Y`, `/qa US X.Y`, `/secops US X.Y mode=code-review`, etc.

Each command runs one stage, then asks:
> "✅ Done — proceed to [next stage]? [yes / no]"

This gives granular control when you want to inspect results between stages.

### 3. Drag-and-drop on the dashboard

Every column move routes through `/next-story` with the matching sub-command:

| Column dragged to | Command injected |
|-------------------|-----------------|
| `refining` | `/next-story refine US X.Y` |
| `secops_tm` | `/next-story secops-tm US X.Y` |
| `tdd` | `/next-story implement US X.Y` |
| `secops_cr` | `/next-story secops-cr US X.Y` |
| `qa` | `/next-story qa US X.Y` |
| `simplify` | `/next-story simplify US X.Y` |
| `commit_ready` | `/next-story commit US X.Y` |

---

## Dashboard views

The dashboard at `http://localhost:8765` has five views, toggled from the header:

| View | Key | Description |
|------|-----|-------------|
| **Kanban** | `Kanban` | Full 10-column board — one column per pipeline status. Drag cards between columns to trigger the matching command in OpenCode. |
| **Rapide** | `Rapide` | 5 meta-columns (Backlog / En cours / Validation / Prêt / Terminé). A cross-column drop moves the story to the default target status of the destination group. |
| **Focus** | `Focus` | Shows the active story (most recently moved, non-pending/done) as a pipeline progress bar with each step highlighted. Useful for monitoring a story currently being processed. |
| **Journal** | `Journal` | Global activity timeline — all history entries from all stories, grouped by date, in reverse-chronological order. |
| **Liste** | `Liste` | Sortable table of all stories (ID, title, status, priority, stack). |

Every view shares the same search bar (filters by ID, title, or stack tag) and opens the same edit modal on click.

### Edit modal

The modal has four tabs:

| Tab | Content | Editable? |
|-----|---------|-----------|
| **Spécification** | Title, priority, status, stack tags, description, acceptance criteria | ✅ |
| **Raffinement** | Refinement decisions, implementation guide | Read-only (agent-generated, rendered as Markdown) |
| **Avancement** | Notes, TDD section (status / tests / coverage / summary), QA section, SecOps report, Simplify summary | Mixed — notes editable, agent reports read-only |
| **Historique** | Append-only audit trail for this story | Read-only |

Agent-generated fields (TDD notes, SecOps report, Simplify comments, refinement decisions) render as **formatted Markdown** instead of plain text.

---

## Commands vs Agents

OpenCode distinguishes two concepts:

| | Commands | Agents |
|--|----------|--------|
| Defined in | `commands/*.md` | `agents/*.md` |
| Context | Injected into the **main agent** | **Isolated** — own context window |
| Invocation | `/command-name` by the user | Task tool (`subagent_type`) by a command |
| `question` tool | ✅ Available | ❌ Not available |
| Permissions | Inherits from main agent | Defined in agent frontmatter |
| Use case | Orchestration, interactive Q&A | Execution with isolated, injected context |

**What this means in practice:**

- `refine.md` and `secops.md` (threat-model) stay as **commands** — they need the `question` tool for interactive Q&A
- `tdd.md`, `qa.md`, `secops.md` (code-review) are **thin wrappers**: they gather context (story JSON + AGENTS.md), then launch their matching sub-agent via Task tool
- Sub-agents receive all context in the Task tool prompt — they don't read `$ARGUMENTS` directly

---

## Bidirectional communication

The Kanban server is the **shared state** between the developer and the agent.

```
Developer (dashboard)         Agent (OpenCode)
       │                             │
       │  drag card → column         │
       │──────────────────────────▶  │
       │   POST /tui/submit-prompt   │
       │   → /next-story refine US X │
       │                             │
       │                    MCP call │
       │  ◀──────────────────────────│
       │  kanban-move-story(US X, tdd)│
       │  kanban-update-story(...)   │
       │                             │
       │  SSE: data: refresh         │
       │──────────────────────────▶  │
       │  (dashboard re-renders)     │
```

Key rule: **moves made by the agent do not trigger dashboard commands** (agents advance themselves). Only human drags trigger command injection.

---

## MCP tools

The Kanban server exposes 7 tools:

| Tool | Description |
|------|-------------|
| `kanban-get-story` | Read a full story with all fields |
| `kanban-list-stories` | List stories, filtered by status or phase |
| `kanban-update-story` | Partially update a story (TDD results, ACs, implementation guide…) |
| `kanban-move-story` | Move a story to a new column + log the change |
| `kanban-create-story` | Create a new story — always sets `status: pending` |
| `kanban-get-next-pending` | Get the highest-priority pending story |
| `kanban-get-stats` | Get global pipeline counts |

See [`kanban/README.md`](kanban/README.md) for the full schema, merge rules, and debug logging reference.

The server also exposes additional REST endpoints consumed by the dashboard:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `PATCH` | `/api/stories/{sid}/move` | Move a story to a new status (body: `{ status, actor }`) |
| `GET` | `/api/history` | Aggregated history across all stories, sorted by timestamp desc |
| `POST` | `/api/reorder` | Reorder cards within a column (body: `{ status, order: [ids] }`) |
| `GET` | `/api/events` | SSE stream — sends `data: refresh` on every story change |

---

## Commands reference

All commands are stack-agnostic. They reference `AGENTS.md` in your project root for tool names, file paths, and conventions.

| Command | Purpose |
|---------|---------|
| `/next-story` | Show project status and next pending story |
| `/next-story US X.Y` | Run the full pipeline for a story (2 stop points) |
| `/refine US X.Y` | Challenge ACs through a structured dialogue (4 roles, 8–12 questions via `question` tool) |
| `/tdd US X.Y` | Assemble story context → launch `tdd` subagent → handle advance |
| `/secops US X.Y` | Threat model (inline, interactive) or code review (launches `secops-cr` subagent) |
| `/qa US X.Y` | Assemble story context → launch `qa` subagent → handle advance |
| `/simplify [US X.Y]` | Launch 3 simplify sub-agents in parallel, fix findings, optionally persist report |
| `/architect` | Design a feature before implementing (question/answer cycle) |
| `/review-pr [number]` | Fetch GitHub PR comments, classify, fix, reply |
| `/commit` | Propose and create a conventional commit |
| `/feature "..."` | Qualify (scan + title + description + stack) → preview → create pending story |
| `/fix "..."` | Qualify bug (scan + "Fix — " title + Bug/Contexte/Attendu + stack) → create pending |
| `/change "..."` | Qualify change (impact scan + Motivation/Périmètre/Risques + stack) → create pending |

---

## Story creation and qualification

`/fix`, `/feature`, and `/change` run a **qualification phase** before creating the story:

1. **Context scan** — grep the codebase, check `kanban-list-stories` (for `/change`), read `AGENTS.md`
2. **Fill the schema**:

| Field | Rule |
|-------|------|
| `title` | Normalized, ≤60 chars, type-specific format (see below) |
| `description` | Type-specific template (see below) |
| `priority` | P1 for bugs, P2 for features/changes — adjustable |
| `stack` | Inferred from codebase scan — always filled |
| `notes` | Reproduction context, impacted stories, open questions |

3. **Preview + confirm** — one confirmation block before persisting
4. **Create** — `kanban-create-story` (title, priority, phase) then `kanban-update-story` (description, stack, notes)

**Title formats:**

| Command | Format | Example |
|---------|--------|---------|
| `/feature` | Imperative verb + subject | `"Exporter les briefings en CSV"` |
| `/fix` | `"Fix — [bug description]"` | `"Fix — refresh token expiré prématurément"` |
| `/change` | `"Change — [what changes]"` | `"Change — migration SQLite vers PostgreSQL"` |

**Description templates:**

- `/feature` → `"En tant que [role], je veux [feature], afin de [benefit]."`
- `/fix` → `"**Bug:** [...]. **Contexte:** [...]. **Attendu:** [...]."` (3 parts)
- `/change` → `"**Motivation:** [...]. **Périmètre:** [...]. **Risques:** [...]."` (3 parts)

---

## AGENTS.md template

Commands expect a `AGENTS.md` at your project root with at least:

```markdown
## Dev Commands

### Backend (`cd backend`)
| Command | Action |
|---------|--------|
| `<test command>` | Run tests |
| `<lint command>` | Lint |
| `<typecheck command>` | Type check |

### Frontend (`cd frontend`)
| Command | Action |
|---------|--------|
| `<test command>` | Run tests |
| `<lint command>` | Lint |

## Quality Gates

### Before each commit
```bash
<backend lint + typecheck>
<frontend lint + typecheck>
```

### Before each push / PR
```bash
<backend tests with coverage>
<frontend tests with coverage>
<E2E tests>
```
```

---

## Story JSON schema

Each story is stored as `user-stories/us-X-Y.json`:

```jsonc
{
  "id": "US 1.3",
  "phase": 1,
  "phase_name": "...",
  "title": "...",
  "description": "...",       // filled by /feature, /fix, /change or /refine
  "status": "pending",
  "priority": "P0",           // P0 | P1 | P2
  "stack": ["backend"],       // filled by /feature, /fix, /change or /refine
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "tdd": {"status": "pending", "tests": 0, "coverage": "0%", "notes": ""},
  "qa":  {"status": "pending", "ac_covered": "0/0", "notes": "", "ac_failures": []},
  "implementation_guide": {}, // filled by /refine
  "refine_decisions": [],     // filled by /refine
  "secops_report": {},        // filled by /secops (both modes)
  "simplify_report": {},      // filled by /simplify
  "notes": "",
  "history": []               // append-only audit trail
}
```

---

## License

MIT — use, fork, adapt freely.
