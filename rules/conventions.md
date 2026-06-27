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
| Design system | Tokens and component catalog defined in the project's design system — see `AGENTS.md` for the exact location |
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
| **Détection** | La règle ESLint `newscap/no-raw-html-elements` bloque ces violations (erreur bloquante) — à configurer dans le projet cible |
| **Audit** | _(optionnel — projet-spécifique)_ Un script `scripts/audit-storybook-usage.py` peut être ajouté pour générer un rapport de violations |
| **Composants manquants** | Si un composant Storybook n'existe pas pour un besoin UI → créer une US dédiée dans le catalogue, ne pas utiliser de HTML natif en attendant |
| **Composants composites** | Les composants composites (CountryThemeSelector, DeliveryTimeSelector, DetailLevelSelector, ChipInput, etc.) doivent utiliser les primitives Storybook |

### Catalogue Storybook disponible

#### Primitives (atoms) — `components/ui/`

| Usage | Composant | Props clés |
|-------|-----------|-----------|
| Champ texte | `<Input>` | `v-model`, `type`, `error`, `disabled` |
| Liste déroulante | `<Select>` | `v-model`, `options`, `error` |
| Bouton | `<Button>` | `variant` (primary/secondary/ghost/danger), `size` (s/m/l), `loading`, `label` |
| Zone de texte | `<Textarea>` | `v-model`, `rows`, `error` |
| Mot de passe | `<PasswordField>` | `v-model`, `label`, `error`, `show-strength-indicator` |
| Cases à cocher | `<CheckboxGroup>` | `v-model`, `options` |
| Boutons radio | `<RadioGroup>` | `v-model`, `options` |
| Interrupteur | `<ToggleSwitch>` | `v-model`, `label` |
| Pastille statut | `<Badge>` | `variant` (success/error/warning/info/neutral), `label` |
| Étiquette | `<Tag>` | `label`, `removable` |
| Carte | `<Card>` | slot default, `padding` |
| Icône | `<Icon>` | `name`, `size` |
| Chargement inline | `<Spinner>` | `size` |
| Squelette chargement | `<Skeleton>` | `width`, `height`, `rounded` |
| Barre progression | `<ProgressBar>` | `value` (0-100), `color` |
| Notification flottante | `<Toast>` | `variant`, `message`, `duration` |
| Conteneur toasts | `<Toaster>` | (singleton, pas de props) |

#### Molécules (à créer — US backlog)

| Usage | Composant | US |
|-------|-----------|-----|
| Bannière erreur/succès/warning | `<Alert>` | US 7.55 |
| Fil d'Ariane | `<Breadcrumb>` | US 7.56 |
| Champ avec label + erreur | `<FormField>` | US 7.57 |
| Navigation par onglets | `<Tabs>` | US 7.58 |
| État vide | `<EmptyState>` | US 7.59 |

> ⚠️ Les éléments HTML natifs `<input>`, `<select>`, `<button>`, `<textarea>` sont **interdits**
> dans tout `.vue` hors de `components/ui/`. Les molécules ci-dessus sont également interdites
> tant que leur US n'est pas terminée — utiliser le composant primitif le plus proche en attendant.

### Composants manquants — Process

Si vous avez besoin d'un élément d'interface qui n'a pas d'équivalent Storybook :

1. **Ne pas utiliser de HTML natif** — la règle ESLint le bloque
2. **Créer une US** dans le Backlog pour le composant manquant (`US X.Y — Créer composant <Nom>`)
3. **Utiliser un composant existant** qui s'en approche le plus en attendant
4. La nouvelle US doit inclure : `*.vue`, `*.stories.ts`, `__tests__/*.test.ts`, et `*.ui-int.ts` si applicable
5. Une fois l'US terminée, migrer les usages existants vers le nouveau composant

### Quality Gates

```bash
cd frontend && npx eslint src                # Bloque les violations
# python scripts/audit-storybook-usage.py --exit-code  # À ajouter dans le projet cible
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
