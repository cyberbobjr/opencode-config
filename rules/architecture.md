# Architecture Rules

## Before any architectural change

1. Read `AGENTS.md` at the project root — it contains the stack identity table, key tech choices, and project-specific commands
2. Read `docs/SPECIFICATIONS.md` for the full product and architecture spec
3. Explore existing patterns in the relevant source files before introducing new abstractions
4. Never introduce a new dependency without: checking if an existing package already covers the need, justifying the choice, and updating `AGENTS.md`

## Guardrails

- **No cross-layer imports** — services import from models, routes import from services, never the reverse
- **No business logic in routes** — routes are thin controllers; logic belongs in `services/`
- **Schema changes require a migration** — never mutate the database schema directly; use the migration tool defined in `AGENTS.md`
- **No breaking API changes** — a breaking change requires a new versioned endpoint, not modifying an existing one

## Where to find project-specific decisions

| Resource | Purpose |
|----------|---------|
| `AGENTS.md` | Stack identity, tech choices, key commands (single source of truth) |
| `docs/SPECIFICATIONS.md` | Full product and architecture spec |
| `docs/CODEMAPS/` | Module maps and dependency graphs (if present) |
| `.opencode/rules/commands.md` | Project-specific CLI commands (tests, migrations, audits) |
| `.opencode/rules/conventions.md` | Code style and naming conventions per layer |

## Before adding a new API endpoint

- Run the API spec command from `AGENTS.md` to inspect existing routes — avoid conflicts and duplicates
- Follow the existing route structure, naming conventions, and auth middleware patterns

## Before adding a new database model or migration

- Check existing models to avoid duplication
- Plan and write the migration before writing application code
- Verify rollback strategy
- Check impact on existing queries and indexes
