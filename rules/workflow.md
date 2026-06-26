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

## Format Markdown obligatoire — champs texte

> ⚠️ **S'applique à TOUTES les étapes ci-dessous** (création, refinement, TDD, QA, SecOps, Simplify).

Tous les champs texte écrits via `kanban-update-story` sont rendus en Markdown dans le dashboard.
Écrire du texte brut produit un bloc illisible (`\n` simples collapsés en espaces par CommonMark).

**Règles impératives :**
1. Séparer les sections par une **ligne vide** (`\n\n`) — un seul `\n` → espace dans le rendu
2. Titres avec `## ` — jamais de texte nu comme `Résumé :`
3. Listes avec `- ` — jamais de virgules sur une ligne
4. Chemins en backtick — `` `frontend/src/api/client.ts` ``

```markdown
## Résumé

Description courte du problème ou de la fonctionnalité.

## Contexte

- Point clé 1
- Point clé 2

## Critères d'acceptation

- `fichier.ts` — raison de la modification
```

---

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
  ▸ kanban-update-story(...)           → Mettre à jour AC + description  ← FORMAT MARKDOWN
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
  ▸ Run lint + type check + format check (see .opencode/rules/commands.md for commands)
  ▸ Run full test suite for all layers (see .opencode/rules/commands.md)
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
