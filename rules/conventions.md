# Conventions de Code

> Les **valeurs concrètes** (formateur et ses options, gestionnaire de paquets,
> version de langage, frameworks) sont dans `AGENTS.md` à la racine du projet.
> Ci-dessous : les **principes** qui s'appliquent quel que soit le stack.

## Backend

| Principe | Détail |
|----------|--------|
| Formatage | Un formateur unique et déterministe, configuré au niveau du repo (voir `AGENTS.md`) |
| Typage | Annotations de types présentes sur toutes les signatures publiques et les modèles de données |
| Imports | Ordre normalisé (stdlib → tiers → local), trié automatiquement |
| Nommage | Suivre l'idiome du langage (voir `AGENTS.md`) ; noms descriptifs, pas d'abréviations obscures |
| Organisation | 1 modèle = 1 fichier dans `models/` ; fichiers cohésifs et courts |
| Routes / contrôleurs | 1 endpoint = 1 fonction ; préfixe d'API cohérent (voir `AGENTS.md`) |
| Logique métier | Dans `services/`, **jamais** dans les routes ou les contrôleurs |
| Tâches de fond | Infrastructure (queue/worker) dans `workers/`, logique métier déléguée à `services/` |
| Concurrence | Suivre le modèle du framework (async/await ou threads) de façon cohérente |
| Configuration | Lue depuis l'environnement / `.env` via un loader validé, jamais en dur dans le code |

---

## Tests

| Principe | Détail |
|----------|--------|
| Fidélité des mocks | Un mock d'une dépendance externe (SDK, API, client) doit reproduire la **forme et le type réels** de sa valeur de retour, pas une version simplifiée plus pratique. Mocker un `dict` là où la dépendance renvoie un objet typé crée un faux sentiment de sécurité : le test passe, le code casse en production. |
| Extracteur unique | Quand une donnée externe peut prendre plusieurs formes (objet typé, dict, variantes de schéma), centraliser sa lecture dans **un seul** accesseur robuste. Deux extracteurs divergents pour la même donnée sont un piège DRY : l'un est corrigé, l'autre reste buggé. |
| Test de régression | Tout bug corrigé doit s'accompagner d'un test qui **reproduit la forme exacte** ayant causé l'échec (ici : l'objet typé sans `.get`), pas seulement le cas nominal. |

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

- `path/to/component` — raison
- `path/to/route` — raison

## Tests

- N tests — couverture X%
```

### Règles impératives

1. **Séparer les sections par une ligne vide** — `\n` seul → espace ; `\n\n` → paragraphe
2. **`## ` pour les titres** — jamais de texte nu comme `Fichiers impactés :`
3. **`- ` pour les listes** — jamais de virgules sur une ligne
4. **Ne jamais tout mettre sur une seule ligne** — toujours au moins un titre `## ` + paragraphe
5. **Chemins en backtick** — `` `path/to/file` ``
