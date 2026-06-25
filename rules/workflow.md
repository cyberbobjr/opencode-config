# Workflow OpenCode

## Commandes Disponibles

| Commande | Usage |
|----------|-------|
| `/refine` | Challenge les critères d'acceptation avant implémentation |
| `/architect` | Discuter et valider l'architecture d'une feature |
| `/implement-plan` | Exécuter un plan d'implémentation validé |
| `/feature "..."` | Crée une US dans le Backlog et implémente la fonctionnalité |
| `/fix "..."` | Crée une US de bugfix et corrige le bug |
| `/change "..."` | Crée une US de modification avec analyse d'impact |
| `/simplify` | Revue de code automatique post-implémentation |
| `/commit` | Commit conventionnel automatique après validation |
| `/review-pr` | Revue de PR GitHub, correction des retours |
| `/next-story` | Workflow complet : raffinement → implémentation → quality gates → commit |

## Lancer le Serveur Kanban

```bash
python .opencode/kanban/server.py
# Dashboard : http://localhost:8765/
# API REST  : http://localhost:8765/api/stories
# MCP tools disponibles dans OpenCode quand configuré
```

Les données des user stories sont dans `user-stories/*.json`.

## Cycle d'une Story (6 étapes)

```
Étape 0 : Choisir la story
  ▸ /next-story                        → Affiche la prochaine story en attente
  ▸ kanban-get-story("US X.Y")         → Lire les AC dans user-stories/*.json

Étape 1 : Raffinement + Threat Model
  ▸ kanban-move-story("US X.Y", "refining")
  ▸ /refine US X.Y                     → Agent raffinement (4 angles)
  ▸ /architect                         → Valider l'architecture
  ▸ /secops US X.Y mode=threat-model   → Surfaces d'attaque
  ▸ kanban-update-story(...)           → Mettre à jour AC + description
  ▸ kanban-move-story("US X.Y", "tdd")

Étape 2 : Implémentation TDD
  ▸ kanban-update-story("US X.Y", '{"tdd": {"status": "in_progress"}}')
  ▸ TDD : test → échouer → implémenter → passer → refactor
  ▸ kanban-update-story("US X.Y", '{"tdd": {"status": "passed", "tests": N, "coverage": "X%"}}')
  ▸ kanban-move-story("US X.Y", "secops_cr")

Étape 2b : SecOps Code Review
  ▸ /secops US X.Y mode=code-review    → Audit sécurité du diff
  ▸ Corriger les problèmes critiques
  ▸ kanban-move-story("US X.Y", "qa")

Étape 3 : Quality Gates + QA
  ▸ cd backend && ruff check && ruff format --check && mypy app
  ▸ cd frontend && npx eslint src && npx prettier --check src && npx vue-tsc --noEmit
  ▸ pytest && npx vitest
  ▸ /qa US X.Y                         → Valide les AC
  ▸ kanban-update-story("US X.Y", '{"qa": {"status": "passed", ...}}')
  ▸ kanban-move-story("US X.Y", "simplify")
  ▸ /simplify                          → 3 sous-agents review le code
  ▸ kanban-move-story("US X.Y", "commit_ready")

Étape 4 : Commit
  ▸ git add . && git diff --cached
  ▸ /commit                            → Message conventionnel + commit
  ▸ kanban-move-story("US X.Y", "completed")
```
