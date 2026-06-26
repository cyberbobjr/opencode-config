# Commands & Project Setup

> **Project-specific commands are in `AGENTS.md`** at the project root.
> Read it before running anything. The sections below describe the expected categories and generic patterns.

---

## Setup

Read `AGENTS.md` for:
- Prerequisites (runtime versions, tools)
- Installation steps
- Required environment variables and their purpose (copy `.env.example` → `.env`)

---

## Backend

Typical commands (actual values in `AGENTS.md`):

| Category | What to look for |
|----------|-----------------|
| Dev server | Hot-reload development server |
| Tests | Unit + integration test runner with coverage |
| Lint | Code linter (fail on errors) |
| Format check | Formatter in check mode (no changes) |
| Type check | Static type checker |
| Migration apply | Apply pending schema migrations to the dev DB |
| Migration create | Generate a new migration from model changes |
| Background workers | Start task queue workers (if applicable) |

---

## Frontend

Typical commands (actual values in `AGENTS.md`):

| Category | What to look for |
|----------|-----------------|
| Dev server | Vite / webpack dev server with HMR |
| Build | Production bundle |
| Unit tests | Component and utility tests with coverage |
| Type check | TypeScript compiler in no-emit mode |
| Lint | ESLint (fail on errors) |
| Format check | Prettier in check mode |
| UI-INT tests | Playwright end-to-end / UI integration tests |

---

## API Discovery

Read `AGENTS.md` for the command that lists available routes (typically `curl localhost:<port>/openapi.json`). Always check before creating a new endpoint to avoid conflicts.

---

## Kanban

```bash
python .opencode/kanban/server.py          # Dashboard at http://localhost:8765/
python .opencode/kanban/server.py --mcp    # MCP stdio mode + HTTP in background
```

---

## Docker / Infrastructure

Read `AGENTS.md` for Docker Compose profiles and service names. Generic patterns:

```bash
docker compose --profile dev up -d   # Start dev services
docker compose down                  # Stop all
docker compose logs -f               # Stream logs
docker compose exec <service> <cmd>  # Run command in container
```

---

## Quality Gates

### Before each commit

Run the full lint + type check + format check sequence for each layer. See `AGENTS.md` for the exact commands. Also:
- Apply any pending schema migrations if the story touches the database
- Verify no migration is pending: use the detection command from `AGENTS.md` (do NOT apply migrations blindly in QA)

### Before each push / PR

Run the full test suite with coverage for all layers. Minimum threshold: **80%** line coverage. See `AGENTS.md` for the exact test runner commands.

---

## Deployment

Read `AGENTS.md` for the deployment procedure (scripts, targets, health check endpoint).
