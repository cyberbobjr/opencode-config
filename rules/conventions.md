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
| Graphiti | Tout accès Neo4j passe par `services/graphiti_adapter.py` |
| Async | Privilégier async/await partout |
| Configuration | pydantic-settings, lue depuis `.env` |

## Frontend (Vue 3 / TypeScript)

| Règle | Valeur |
|-------|--------|
| API | Composition API + `<script setup lang="ts">` |
| Nommage composants | PascalCase, un composant par fichier |
| Nommage fichiers | PascalCase `.vue`, camelCase `.ts` |
| State | Pinia stores, un store par domaine |
| Appels API | Axios client dans `api/` |
| Routes | Vue Router, lazy-loaded |
| i18n | `vue-i18n`, fichiers JSON dans `locales/` |
| CSS | TailwindCSS utility-first |
| Design system | Tokens définis dans `docs/design-system.md` + rendu dans `docs/designs/d-hybrid.html` |
| Storybook | `.stories.ts` obligatoire pour chaque composant `.vue` — créer/modifier/supprimer en miroir |

## Storybook — Règle Impérative

Tout composant Vue doit avoir une story associée. Cette règle s'applique à **chaque modification** du dossier `frontend/src/components/`.

| Opération | Action obligatoire |
|-----------|-------------------|
| Composant créé (`NomComp.vue`) | Créer `NomComp.stories.ts` dans le même dossier |
| Composant modifié (props, slots, états) | Mettre à jour `NomComp.stories.ts` en conséquence |
| Composant supprimé | Supprimer `NomComp.stories.ts` |

### Contenu minimal d'une story

```ts
import type { Meta, StoryObj } from "@storybook/vue3-vite"
import NomComp from "./NomComp.vue"

const meta: Meta<typeof NomComp> = {
  title: "NomComp",
  component: NomComp,
  tags: ["autodocs"],
}
export default meta

type Story = StoryObj<typeof NomComp>

// Au moins un état "nominal" + un état "vide" ou "erreur" si applicable
export const Default: Story = { args: { /* props minimales */ } }
```

### Critère QA obligatoire

Après toute modification de composant, le quality gate doit inclure :

```bash
cd frontend && npx storybook build --quiet
```

Un build Storybook en échec **bloque** le passage en `commit_ready`.

---

## Storybook — Utilisation Exclusive des Composants

> ⚠️ **Règle impérative** — Tous les fichiers `.vue` (views, layouts, components hors `components/ui/`) doivent utiliser **uniquement les composants Storybook** pour les éléments d'interface : `<Input>`, `<Select>`, `<Button>`, `<Textbox>`, etc.

### Règles

| Règle | Détail |
|-------|--------|
| **Interdiction** | `<input>`, `<select>`, `<button>`, `<textarea>` sont **interdits** dans tout fichier `.vue` hors de `components/ui/` |
| **Détection** | La règle ESLint `newscap/no-raw-html-elements` bloque ces violations (erreur bloquante) |
| **Audit** | Le script `scripts/audit-storybook-usage.py` génère un rapport de toutes les violations |
| **Composants manquants** | Si un composant Storybook n'existe pas pour un besoin UI → créer une US dédiée dans le catalogue, ne pas utiliser de HTML natif en attendant |
| **Composants composites** | Les composants composites (CountryThemeSelector, DeliveryTimeSelector, DetailLevelSelector, ChipInput, etc.) doivent utiliser les primitives Storybook |

### Catalogue Storybook disponible

| Élément natif | Composant Storybook |
|---------------|-------------------|
| `<input>` | `<Input>` |
| `<select>` | `<Select>` |
| `<button>` | `<Button>` |
| `<textarea>` | `<Textbox>` |

### Composants manquants — Process

Si vous avez besoin d'un élément d'interface qui n'a pas d'équivalent Storybook :

1. **Ne pas utiliser de HTML natif** — la règle ESLint le bloque
2. **Créer une US** dans le Backlog pour le composant manquant (`US X.Y — Créer composant <Nom>`)
3. **Utiliser un composant existant** qui s'en approche le plus (ex: `<Textbox>` pour un textarea sophistiqué)
4. La nouvelle US doit inclure : `*.vue`, `*.stories.ts`, `__tests__/*.test.ts`, et `*.e2e.ts` si applicable
5. Une fois le catalogue complété, toute migration de page existante peut utiliser le nouveau composant

### Quality Gates

```bash
cd frontend && npx eslint src                # Bloque les violations
python scripts/audit-storybook-usage.py --exit-code  # Vérification complémentaire
```

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
