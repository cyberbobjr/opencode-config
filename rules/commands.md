# Commandes & Démarrage

## Prérequis

- Python ≥ 3.12, [uv](https://docs.astral.sh/uv/), Node.js ≥ 20
- Docker + Docker Compose, Neo4j 5.26+, Redis 7
- Clés API : DeepSeek, OpenRouter, Firecrawl (dans `.env`)

## Installation

```bash
git clone git@github.com:cyberbobjr/news-briefing-saas.git && cd news-briefing-saas
cp .env.example .env          # → Éditer avec vos clés API
cd backend && uv venv && source .venv/bin/activate && uv sync
cd ../frontend && npm install
cd ../backend && alembic upgrade head
```

## Commandes Backend (`cd backend`)

| Commande | Action |
|----------|--------|
| `uvicorn app.main:app --reload` | Serveur dev |
| `uv run news --reload --port 8000` | Serveur dev (alias) |
| `pytest` | Tests unitaires + intégration |
| `pytest --cov=app --cov-report=term-missing` | Couverture |
| `pytest --celery` | Tests avec Celery + Redis mocké |
| `ruff check` | Lint |
| `ruff format --check` | Vérification format |
| `ruff format` | Auto-format |
| `mypy app` | Type checking |
| `alembic upgrade head` | Migrer la BDD |
| `alembic revision --autogenerate -m "message"` | Nouvelle migration |
| `uv run celery` | Démarrer worker + Beat |
| `uv run celery flower` | Monitoring Flower (http://localhost:5555) |
| `uv run celery beat -l info` | Scheduler Celery Beat seul |

## Commandes Frontend (`cd frontend`)

| Commande | Action |
|----------|--------|
| `npm run dev` | Serveur dev (Vite) |
| `npm run build` | Build prod |
| `npx vitest` | Tests unitaires |
| `npx vitest --coverage` | Couverture |
| `npx vue-tsc --noEmit` | Type check TypeScript |
| `npx eslint src` | Lint |
| `npx prettier --check src` | Vérification format |
| `npx prettier --write src` | Auto-format |
| `npx playwright test` | UI-INT |

## Kanban

| Commande | Action |
|----------|--------|
| `python .opencode/kanban/server.py` | Serveur Kanban (http://localhost:8765) |
| `python .opencode/kanban/server.py --mcp` | Mode MCP stdio + HTTP en arrière-plan |

## Docker

| Commande | Action |
|----------|--------|
| `docker compose --profile dev up -d` | Démarrer services dev (5 conteneurs) |
| `docker compose --profile prod up -d` | Démarrer services prod |
| `docker compose down` | Arrêter |
| `docker compose logs -f` | Logs en temps réel |
| `docker compose logs -f backend` | Logs backend |
| `docker compose logs -f celery-worker` | Logs workers Celery |
| `docker compose logs -f neo4j` | Logs Neo4j |
| `docker compose exec backend pytest` | Tests dans le conteneur |
| `docker compose exec backend celery -A workers.celery_app inspect active` | Inspecter tâches Celery |

## Quality Gates

### Avant chaque commit

```bash
cd backend && ruff check && ruff format --check && mypy app
cd frontend && npx eslint src && npx prettier --check src && npx vue-tsc --noEmit
```

### Avant chaque push / PR

```bash
cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80
cd frontend && npx vitest --coverage --coverage.threshold.100.branches=80
npm run test:ui-int
python scripts/audit-storybook-usage.py --exit-code  # Bloque si violations Storybook
cd frontend && npx storybook build --quiet            # Bloque si erreur Storybook
```

## Déploiement

```bash
./scripts/deploy-vps.sh
# 1. rsync vers VPS
# 2. docker compose --profile prod down && up -d --build
# 3. alembic upgrade head
# 4. Vérifier GET /api/health → 200

# Backup quotidien (cron VPS)
sqlite3 /data/newscap.db ".backup '/backups/newscap-$(date +%Y%m%d).db'"
```
