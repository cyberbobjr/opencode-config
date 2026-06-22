# opencode-config

A ready-to-use configuration template for [OpenCode](https://opencode.ai) that gives your AI coding agent a **structured, trackable development pipeline**.

At its core: a Kanban server that works simultaneously as a **web dashboard**, a **REST API**, and an **MCP server** — letting the agent read and update project state, while letting the developer steer from a drag-and-drop UI.

---

## What this gives you

- **A Kanban board** connected to your agent via MCP — stories move through columns as the agent works
- **A bidirectional bridge** — dragging a card on the dashboard injects a slash command into the OpenCode TUI
- **Slash commands** for every stage of the development cycle (refinement, TDD, security review, QA, commit)
- **Sub-agents** for code quality, reuse, and efficiency review
- **A structured pipeline** that enforces TDD, SecOps review, and QA validation before any commit

---

## Repository structure

```
.opencode/
├── opencode.json          — MCP server configuration (consumed by OpenCode)
├── package.json           — Node dependencies (optional tooling)
│
├── commands/              — Slash commands available in OpenCode
│   ├── next-story.md      — Workflow coordinator: full cycle or individual steps
│   ├── refine.md          — Refinement agent (8–12 questions, 4 roles)
│   ├── tdd.md             — TDD agent (red → green → refactor)
│   ├── secops.md          — DevSecOps agent (threat model + code review)
│   ├── qa.md              — QA agent (AC validation through tests)
│   ├── architect.md       — Architecture design (question/answer cycle)
│   ├── simplify.md        — Code quality review (3 sub-agents)
│   ├── review-pr.md       — GitHub PR review and response
│   ├── commit.md          — Conventional commit helper
│   ├── feature.md         — Create a new feature story (backlog only)
│   ├── fix.md             — Create a bug story (backlog only)
│   └── change.md          — Create a change story (backlog only)
│
├── agents/                — Reusable sub-agents (called by commands)
│   ├── code-simplify-quality.md
│   ├── code-simplify-reuse.md
│   └── code-simplify-efficiency.md
│
└── kanban/                — Kanban MCP server
    ├── server.py          — Main server (FastAPI + FastMCP)
    ├── requirements.txt
    ├── migrate.py         — Schema migration for existing stories
    ├── templates/
    │   └── dashboard.html
    └── static/
        └── app.js
```

Story data lives **outside** this repo, in `user-stories/*.json` at the project root — one JSON file per story, served by the Kanban server.

---

## Quick start

### 1. Install Python dependencies

```bash
pip install -r .opencode/kanban/requirements.txt
```

### 2. Start the Kanban server

```bash
# Dashboard + MCP (standard mode)
python .opencode/kanban/server.py --mcp

# Debug mode — logs every MCP call with parameters
python .opencode/kanban/server.py --mcp --debug
```

Dashboard: `http://localhost:8765`

### 3. Configure OpenCode

The `opencode.json` at the root of this repo already wires the Kanban server as an MCP provider:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "kanban": {
      "type": "local",
      "command": ["python", ".opencode/kanban/server.py", "--mcp"],
      "enabled": true
    }
  }
}
```

Copy it to your project root (or merge with your existing `opencode.json`).

### 4. Add your project conventions

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
| `tdd` | `/tdd` implements the story with Red → Green → Refactor |
| `secops_cr` | `/secops mode=code-review` audits the diff against an OWASP checklist |
| `qa` | `/qa` validates every AC with integration or E2E tests |
| `simplify` | 3 sub-agents review for quality, reuse, and efficiency |
| `commit_ready` | User approves the commit message |
| `completed` | Story committed and done |

Start the full cycle with:

```
/next-story US X.Y
```

Or drive individual steps from the dashboard by dragging cards between columns — the server injects the right command into OpenCode automatically.

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

The Kanban server exposes 7 tools under the name `kanban-stories`:

| Tool | Description |
|------|-------------|
| `kanban-get-story` | Read a full story with all fields |
| `kanban-list-stories` | List stories, filtered by status or phase |
| `kanban-update-story` | Partially update a story (TDD results, ACs, implementation guide…) |
| `kanban-move-story` | Move a story to a new column + log the change |
| `kanban-create-story` | Create a new story (used by `/feature`, `/fix`, `/change`) |
| `kanban-get-next-pending` | Get the highest-priority pending story |
| `kanban-get-stats` | Get global pipeline counts |

See [`kanban/README.md`](kanban/README.md) for the full schema, merge rules, and debug logging reference.

---

## Commands reference

All commands are stack-agnostic. They reference `AGENTS.md` in your project root for tool names, file paths, and conventions.

| Command | Purpose |
|---------|---------|
| `/next-story` | Show project status and next pending story |
| `/next-story US X.Y` | Run the full cycle for a story |
| `/refine US X.Y` | Challenge ACs through a structured dialogue (4 roles, 8–12 questions) |
| `/tdd US X.Y` | Implement with TDD (delegates to the story's `implementation_guide`) |
| `/secops US X.Y` | Security review — threat model or code review mode |
| `/qa US X.Y` | Validate every AC with tests |
| `/architect` | Design a feature before implementing (question/answer cycle) |
| `/simplify` | Code quality review by 3 sub-agents |
| `/review-pr [number]` | Fetch GitHub PR comments, classify, fix, reply |
| `/commit` | Propose and create a conventional commit |
| `/feature "..."` | Create a new feature story in the backlog (no implementation) |
| `/fix "..."` | Create a bug story in the backlog (no implementation) |
| `/change "..."` | Create a change story in the backlog (no implementation) |

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
  "title": "...",
  "status": "pending",
  "priority": "P0",
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "tdd": {"status": "pending", "tests": 0, "coverage": "0%"},
  "qa":  {"status": "pending", "ac_covered": "0/0"},
  "implementation_guide": {},   // filled by /refine
  "secops_report": {},          // filled by /secops
  "history": []                 // append-only audit trail
}
```

---

## License

MIT — use, fork, adapt freely.
