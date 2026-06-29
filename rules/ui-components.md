# UI Components & Frontend Development

> Le **stack frontend exact** (framework, gestion d'état, i18n, CSS) et le
> **catalogue de composants** du projet sont décrits dans `AGENTS.md` et le
> design system du projet. Ce fichier ne contient que les principes génériques.

## Before implementing any component or page

1. Read the project's design system — see `AGENTS.md` for the exact location (e.g. a `docs/design-system.md` and/or a machine-readable component registry)
2. The design system defines: available components and their APIs, CSS custom properties, typography, spacing tokens, and visual references
3. Your implementation MUST visually match the design references described in the project's design system
4. Before creating a new component, **search the component registry / catalog first** — reuse or extend an existing one rather than duplicating

---

## Conventions Frontend

> Valeurs concrètes (framework, état, routing, i18n, CSS) dans `AGENTS.md`.

| Principe | Détail |
|----------|--------|
| Composants | Un composant par fichier, nommage cohérent avec l'idiome du framework |
| Fichiers | Cohésifs et courts ; organiser par domaine/feature |
| État | Centralisé dans des stores, un store par domaine |
| Appels API | Encapsulés dans une couche `api/` dédiée, jamais inline dans les vues |
| Routes | Déclaratives et lazy-loaded quand le framework le permet |
| i18n | Toutes les chaînes visibles passent par le système d'internationalisation |
| CSS | Utiliser les tokens du design system, jamais de valeurs en dur |
| Design system | Catalogue de composants + tokens — voir `AGENTS.md` pour l'emplacement |

---

## CSS Custom Properties

Never hardcode hex or rgba values. Use the project's CSS custom properties (defined in the design system) for all colors, spacing, and typography.

```css
/* ❌ Never */
color: #1a73e8;
background: rgba(0, 0, 0, 0.5);

/* ✅ Always */
color: var(--primary);
background: var(--surface-overlay);
```

---

## Internationalisation

All UI strings must go through the project's i18n system. Never hardcode user-visible text. See `AGENTS.md` for the i18n library and the location of translation files.

---

## Component Stories — Règle Impérative

Si le projet utilise un explorateur de composants (ex. Storybook), **tout composant
doit avoir une story associée**. Cette règle s'applique à **chaque modification**
du dossier de composants.

| Opération | Action obligatoire |
|-----------|-------------------|
| Composant créé | Créer la story correspondante dans le même dossier |
| Composant modifié (props, slots, états) | Mettre à jour la story en conséquence |
| Composant supprimé | Supprimer la story |

### Contenu minimal d'une story

Au moins un état « nominal » + un état « vide » ou « erreur » si applicable.
Voir `AGENTS.md` / le design system pour le format exact (framework et outil).

### Critère QA obligatoire

Après toute modification de composant, le quality gate doit inclure le build de
l'explorateur de composants (commande exacte dans `AGENTS.md`). Un build en échec
**bloque** le passage en `commit_ready`.

---

## Utilisation Exclusive des Composants du Design System

> ⚠️ **Règle impérative** — Les vues, layouts et composants composites doivent
> utiliser **uniquement les composants du design system** pour les éléments
> d'interface, jamais des primitives HTML brutes.

| Règle | Détail |
|-------|--------|
| **Interdiction** | `<input>`, `<select>`, `<button>`, `<textarea>` bruts sont **interdits** hors de la couche de primitives du design system |
| **Détection** | Une règle de lint dédiée bloque ces violations (erreur bloquante) — voir `AGENTS.md` pour son nom |
| **Composants manquants** | Si un composant n'existe pas pour un besoin UI → créer une US dédiée, ne pas utiliser de HTML natif en attendant |
| **Composants composites** | Doivent eux-mêmes être construits à partir des primitives du design system |

### Catalogue de composants

Le catalogue complet (primitives, molécules, composants composites, admin, etc.)
est maintenu dans le **design system / registre de composants du projet** — voir
`AGENTS.md`. Ne pas dupliquer ce catalogue ici : il dériverait du registre, qui
est la source de vérité (et souvent lu automatiquement par l'agent TDD).

### Composants manquants — Process

Si vous avez besoin d'un élément d'interface qui n'a pas d'équivalent dans le design system :

1. **Ne pas utiliser de HTML natif** — la règle de lint le bloque
2. **Créer une US** dans le Backlog pour le composant manquant (`US X.Y — Créer composant <Nom>`)
3. **Utiliser un composant existant** qui s'en approche le plus en attendant
4. La nouvelle US doit inclure le composant, sa story, ses tests unitaires, et ses tests UI-INT si applicable
5. Une fois l'US terminée, migrer les usages existants vers le nouveau composant

### Quality Gates

Lancer le linter sur le code frontend (commande exacte dans `AGENTS.md`) — il bloque les violations.

---

## Checklist before submitting a component

- [ ] No native `<button>`, `<input>`, `<select>`, `<textarea>` in page or layout templates
- [ ] No hardcoded color hex or rgba values — use `var(--...)` tokens
- [ ] Rendering matches the project's design references
- [ ] Dark mode supported via CSS tokens (no fixed colors)
- [ ] All user-visible strings go through the i18n system
- [ ] A story exists or has been updated for this component (if the project uses a component explorer)
