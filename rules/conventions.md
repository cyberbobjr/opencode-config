# Conventions de Code

## Backend (Python / FastAPI)

| Règle | Valeur |
|-------|--------|
| Formateur | ruff (line-length=100) |
| Type hints | Toujours présents (Pydantic v2, params fonctions) |
| Imports | `isort` via ruff (stdlib → tiers → local) |
| Nommage | snake_case variables/fonctions, PascalCase classes |
| Fichier | 1 modèle = 1 fichier dans `models/` |
| Routes | 1 endpoint = 1 fonction, préfixe `/api/` |
| Services | Logique métier dans `services/`, pas dans les routes |
| Tâches Celery | Infrastructure dans `workers/`, logique métier dans `services/` |
| Async | Privilégier async/await partout |
| Configuration | pydantic-settings, lue depuis `.env` |

---

## Git

| Règle | Valeur |
|-------|--------|
| Format | Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`) |
| Branches | `main` (stable), `feat/*`, `fix/*`, `refactor/*` |
| Commits | Atomiques — un commit = une modification logique |
| Messages | En anglais (`feat: add JWT auth middleware`) |
| Outil | Utiliser `/commit` — propose le message et commit après validation |

## Kanban — Champs texte des User Stories

> **OBLIGATOIRE** — Tous les champs texte écrits via `kanban-update-story` sont rendus en **Markdown**.
> Écrire du texte brut produit un bloc illisible (`\n` simples collapsés en espaces par CommonMark).

### Champs concernés

| Champ JSON | Onglet modal | Auteur typique |
|---|---|---|
| `notes` (top-level) | Progress → Notes | agent `refine` |
| `tdd.notes` | Progress → TDD Summary | agent `tdd` |
| `qa.notes` | Progress → QA | agent `qa` |
| `secops_report.notes` | Progress → SecOps | agent `secops` |
| `simplify_comments` | Progress → Simplify | agent `simplify` |
| `description` | Specification | tout agent |
| `implementation_guide` | Refinement | agent `refine` |

### Format attendu

```markdown
## Résumé

Description courte.

## Fichiers modifiés

- `frontend/src/components/MyComp.vue` — raison
- `backend/app/routes/auth.py` — raison

## Tests

- 27 tests backend + 111 tests frontend — couverture 98%
```

### Règles impératives

1. **Séparer les sections par une ligne vide** — `\n` seul → espace ; `\n\n` → paragraphe
2. **`## ` pour les titres** — jamais de texte nu comme `Fichiers impactés :`
3. **`- ` pour les listes** — jamais de virgules sur une ligne
4. **Ne jamais tout mettre sur une seule ligne** — toujours au moins un titre `## ` + paragraphe
5. **Chemins en backtick** — `` `frontend/src/api/client.ts` ``
