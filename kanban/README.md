# Kanban Server

A single server that simultaneously exposes:
- a **web dashboard** (drag-and-drop Kanban, list view, edit modal)
- a **REST API** (story CRUD, SSE live-refresh)
- an **MCP server** (tools consumed by OpenCode agents)
- an **OpenCode bridge** (injects commands into the active TUI when a card changes column)

---

## Getting Started

```bash
# Dashboard only (port 8765)
python .opencode/kanban/server.py

# MCP mode (stdio server + dashboard in background)
python .opencode/kanban/server.py --mcp

# Debug mode — logs every MCP call with parameters and result to stderr + kanban.log
python .opencode/kanban/server.py --debug
python .opencode/kanban/server.py --mcp --debug
```

Dependencies:

```bash
pip install -r .opencode/kanban/requirements.txt
# fastapi  uvicorn  mcp
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCODE_SERVER_URL` | `http://localhost:4096` | OpenCode server URL |
| `OPENCODE_TRIGGER_ENABLED` | `1` | Disable the bridge: set to `0` |
| `KANBAN_DEBUG` | `0` | Enable MCP debug logging: set to `1` |

`--debug` and `KANBAN_DEBUG=1` are equivalent and can be combined.

---

## Architecture

```
server.py
├── Storage           → user-stories/*.json  (one file per story)
├── REST API          → FastAPI  :8765
├── Dashboard         → templates/dashboard.html + static/app.js
├── MCP tools         → FastMCP "kanban-stories"
└── OpenCode bridge   → POST /tui/clear-prompt → append-prompt → submit-prompt
```

### Flow when a card is dragged in the dashboard

```
Drag → PUT /api/stories/{sid}
     → apply_update()  →  diff + history entry
     → save_one()      →  bump SSE version
     → STATUS_COMMANDS →  trigger_opencode()
                          └→ _tui_type_and_submit("/cmd args")
                               POST /tui/clear-prompt
                               POST /tui/append-prompt
                               POST /tui/submit-prompt
```

### Flow when an agent calls an MCP tool

```
Agent → kanban-update-story / kanban-move-story
      → apply_update() / move_story()
      → save_one()  →  bump SSE version
      → (no OpenCode trigger — agents move themselves)
```

---

## Kanban Columns and Triggered Commands

When a card is **dragged** to a column via the dashboard, the server automatically injects the corresponding command into OpenCode:

| Column | `status` | Injected command |
|--------|----------|-----------------|
| Pending | `pending` | — |
| Refinement | `refining` | `/next-story refine {sid}` |
| SecOps (TM) | `secops_tm` | `/secops "{sid}" mode=threat-model` |
| TDD | `tdd` | `/tdd {sid}` |
| SecOps (CR) | `secops_cr` | `/secops "{sid}" mode=code-review` |
| QA | `qa` | `/qa {sid}` |
| Simplify | `simplify` | `/next-story simplify {sid}` |
| Commit Ready | `commit_ready` | `/next-story commit {sid}` |
| Done | `completed` | — |
| Blocked | `blocked` | — |

> Moves made by agents via MCP **do not trigger** these commands — agents advance themselves through the pipeline.

---

## MCP Tools

The server exposes 7 tools under the server name **`kanban-stories`**.  
All return a JSON string.

---

### `kanban-get-story`

Retrieves the full story.

```
story_id  str   Story ID (e.g. "US 1.3")
```

```json
// Returns: full story or {"error": "Story US X.Y not found"}
{
  "id": "US 1.3",
  "title": "...",
  "status": "tdd",
  "stack": ["backend", "database"],
  "acceptance_criteria": [{"id": 1, "text": "...", "checked": false}],
  "tdd": {"status": "in_progress", "tests": 0, "coverage": "0%", "notes": ""},
  "qa":  {"status": "pending", "ac_covered": "0/0", "notes": ""},
  "implementation_guide": { ... },
  "secops_report": { ... },
  "history": [ ... ]
}
```

---

### `kanban-list-stories`

Lists all stories with optional filters.

```
status  str  (optional) filter by status  e.g. "tdd"
phase   str  (optional) filter by phase   e.g. "1"
```

Returns a JSON array of stories.

---

### `kanban-update-story`

Partially updates a story. Pass only the fields to modify.

```
story_id  str   Story ID
changes   str   Partial JSON of fields to update
```

Merge rules:
- `tdd`, `qa`, `secops_report` → **merge** (existing keys not mentioned are preserved)
- `acceptance_criteria`, `refine_decisions`, `stack` → **full list replacement**
- `history` → **ignored** (append-only, managed by the server)
- `_actor` → extracted before merge, used in the history entry

```jsonc
// Example: mark TDD as passed
kanban-update-story("US 1.3", '{
  "_actor": "tdd",
  "tdd": {
    "status": "passed",
    "tests": 14,
    "coverage": "88%",
    "notes": "All tests green"
  }
}')
```

```jsonc
// Example: persist refinement result
kanban-update-story("US 1.3", '{
  "_actor": "refine",
  "description": "...",
  "stack": ["backend", "database"],
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "implementation_guide": { ... }
}')
```

**Recommended `_actor` values**: `refine` · `secops-tm` · `tdd` · `secops-cr` · `qa` · `simplify` · `commit` · `user`

---

### `kanban-move-story`

Moves a story to a new column and logs the status change.

```
story_id    str   Story ID
new_status  str   Target status (see column table above)
actor       str   (optional, default "agent") Author of the move
```

Valid statuses: `pending` · `refining` · `secops_tm` · `tdd` · `secops_cr` · `qa` · `simplify` · `commit_ready` · `completed` · `blocked`

```jsonc
// Example: TDD done → security review
kanban-move-story("US 1.3", "secops_cr", "tdd")
```

---

### `kanban-create-story`

Creates a new story with default values.

```
title     str   Story title
priority  str   (optional, default "P2")  P0 · P1 · P2 · Future
phase     int   (optional, default 7)     1–7
```

The ID is auto-generated (`US {phase}.{n}`). The story is created directly in `refining` status.

---

### `kanban-get-next-pending`

Returns the next `pending` story to process (P0 priority first, lowest phase on tie). Phase 6 stories are excluded.

Returns `{"message": "ALL_DONE"}` if no stories are pending.

---

### `kanban-get-stats`

Returns global project statistics.

```json
{
  "pending": 3,
  "refining": 1,
  "secops_tm": 0,
  "tdd": 2,
  "secops_cr": 0,
  "qa": 1,
  "simplify": 0,
  "commit_ready": 0,
  "completed": 12,
  "blocked": 1,
  "tdd_counts": {"passed": 10, "failed": 1, "in_progress": 2, "pending": 7},
  "qa_counts":  {"passed": 9,  "failed": 0, "in_progress": 1, "pending": 10}
}
```

---

## REST API (internal dashboard)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard HTML |
| `GET` | `/api/stories` | List (filters `?status=` `?phase=`) |
| `GET` | `/api/stories/{sid}` | Single story |
| `PUT` | `/api/stories/{sid}` | Update + OpenCode trigger |
| `POST` | `/api/stories` | Create |
| `DELETE` | `/api/stories/{sid}` | Delete |
| `POST` | `/api/reorder` | Reorder cards within a column |
| `GET` | `/api/events` | SSE — sends `data: refresh` on every change |
| `GET` | `/api/stats` | Global statistics |
| `GET` | `/api/debug` | Last 50 trigger events (diagnostics) |

The `?no_trigger=1` parameter on `PUT` disables the OpenCode bridge for that call.

---

## Story Schema

```jsonc
{
  "id":           "US 1.3",
  "phase":        1,
  "phase_name":   "Backend Foundations",
  "title":        "...",
  "description":  "...",
  "priority":     "P0 | P1 | P2 | Future",
  "status":       "pending | refining | secops_tm | tdd | secops_cr | qa | simplify | commit_ready | completed | blocked",
  "order":        0,               // position within the column
  "stack":        ["backend", "database"],  // impacted domains
  "acceptance_criteria": [
    {"id": 1, "text": "...", "checked": false}
  ],
  "tdd": {
    "status":   "pending | in_progress | passed | failed",
    "tests":    14,
    "coverage": "88%",
    "notes":    "..."
  },
  "qa": {
    "status":     "pending | in_progress | passed | failed",
    "ac_covered": "7/8",
    "notes":      "...",
    "ac_failures": []   // populated by /qa on failure
  },
  "implementation_guide": {   // populated by /refine
    "type":         "backend | frontend | database | devops | ...",
    "scope":        ["backend"],
    "approach":     "...",
    "files_create": [],
    "files_modify": [],
    "files_delete": [],
    "steps":        ["1. ...", "2. ..."],
    "test_strategy": "...",
    "constraints":  "..."
  },
  "secops_report": {   // populated by /secops
    "mode":           "threat-model | code-review",
    "status":         "passed | failed | skipped",
    "review_required": false,
    "issues":         [],
    "comments":       "..."
  },
  "refine_decisions":  [],    // decisions from refinement
  "notes":             "...",
  "simplify_comments": "...", // observations from the simplify stage
  "history": [                // audit trail — append-only
    {
      "ts":      "2026-06-21T18:30:00",
      "by":      "refine",
      "changes": ["status: pending → secops_tm", "AC: 0 → 6"]
    }
  ],
  "created_at": "2026-06-21",
  "updated_at": "2026-06-21"
}
```

---

## Change History

Every call to `kanban-update-story` or `kanban-move-story` automatically produces an entry in `history`. The `_actor` field identifies the author in the log:

| Context | `_actor` |
|---------|----------|
| Dragging a card in the dashboard | `dashboard` |
| `/refine` agent | `refine` |
| `/secops` agent — threat-model mode | `secops-tm` |
| `/tdd` agent | `tdd` |
| `/secops` agent — code-review mode | `secops-cr` |
| `/qa` agent | `qa` |
| `/next-story simplify` agent | `simplify` |
| `/next-story commit` agent | `commit` |
| MCP call without `_actor` | `agent` |

History is displayed in the dashboard edit modal (read-only, last 15 entries).

---

## Debug Logging

When debug mode is active, every MCP tool call emits two lines to **stderr** and **`kanban.log`**:

```
[MCP] ▶ <tool>   <input params>
[MCP] ◀ <tool>   <result summary>
```

Examples:

```
[MCP] ▶ update_story  story_id='US 1.3'  actor='tdd'  fields=['tdd']
[MCP] ◀ update_story  status='tdd'  tdd='in_progress→passed'  qa='pending'  history_len=5

[MCP] ▶ move_story  story_id='US 1.3'  new_status='secops_cr'  actor='tdd'
[MCP] ◀ move_story  old_status='tdd'  new_status='secops_cr'  changed=True

[MCP] ▶ list_stories  status='tdd'  phase='(all)'
[MCP] ◀ list_stories  count=2  ids=['US 1.3', 'US 2.1']

[MCP] ▶ get_next_pending
[MCP] ◀ get_next_pending  story_id='US 1.1'  priority='P0'  phase=1  pending_total=4
```

In MCP mode (`--mcp`), stdout is reserved for the JSON-RPC protocol. Debug output goes to **stderr only**, which keeps the two channels separate. To capture debug logs from an MCP session:

```bash
KANBAN_DEBUG=1 python .opencode/kanban/server.py --mcp 2>mcp-debug.log
```

---

## Files

```
.opencode/kanban/
├── server.py          — main server (this file)
├── requirements.txt   — Python dependencies
├── migrate.py         — schema migration tool for existing stories
├── kanban.log         — runtime logs + MCP debug events  [gitignored]
├── templates/
│   └── dashboard.html — web interface (inline CSS)
└── static/
    └── app.js         — client logic (SortableJS, SSE, modal)
```
