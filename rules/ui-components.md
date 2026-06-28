# UI Components & Frontend Development

## Before implementing any component or page

1. Read the project's design system — see `AGENTS.md` for the exact location (typically `docs/design-system.md`)
2. The design system defines: available components and their APIs, CSS custom properties, typography, spacing tokens, and visual references
3. Your implementation MUST visually match the design references described in the project's design system

---

## Conventions Frontend (Vue 3 / TypeScript)

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

---

## CSS Custom Properties

Never hardcode hex or rgba values. Use the project's CSS custom properties (defined in the design system) for all colors, spacing, and typography.

```css
/* ❌ Never */
color: #C41E3A;
background: rgba(0, 0, 0, 0.5);

/* ✅ Always */
color: var(--primary);
background: var(--surface-overlay);
```

---

## Internationalisation

All UI strings must go through `vue-i18n`. Never hardcode user-visible text. Translation files in `frontend/src/locales/`.

---

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

## Utilisation Exclusive des Composants Storybook

> ⚠️ **Règle impérative** — Tous les fichiers `.vue` (views, layouts, components hors `components/ui/`) doivent utiliser **uniquement les composants Storybook** pour les éléments d'interface.

| Règle | Détail |
|-------|--------|
| **Interdiction** | `<input>`, `<select>`, `<button>`, `<textarea>` sont **interdits** dans tout fichier `.vue` hors de `components/ui/` |
| **Détection** | La règle ESLint `newscap/no-raw-html-elements` bloque ces violations (erreur bloquante) |
| **Composants manquants** | Si un composant Storybook n'existe pas pour un besoin UI → créer une US dédiée, ne pas utiliser de HTML natif en attendant |
| **Composants composites** | Les composants composites (CountryThemeSelector, DeliveryTimeSelector, DetailLevelSelector, ChipInput, etc.) doivent utiliser les primitives Storybook |

### Catalogue Storybook disponible

#### Primitives (atoms) — `components/ui/`

| Usage | Composant | Props clés |
|-------|-----------|-----------|
| Champ texte | `<Input>` | `v-model`, `type`, `error`, `disabled` |
| Liste déroulante | `<Select>` | `v-model`, `options`, `error` |
| Bouton | `<Button>` | `variant` (primary/secondary/ghost/danger), `size` (s/m/l), `loading`, `label` |
| Zone de texte | `<Textarea>` | `v-model`, `rows`, `error` |
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
| Message de champ | `<FieldMessage>` | `type` (error/hint/success) |

#### Molécules — `components/ui/`

| Usage | Composant | Props clés |
|-------|-----------|-----------|
| Mot de passe | `<PasswordField>` | `v-model`, `label`, `error`, `show-strength-indicator` |
| Bannière | `<Alert>` | `variant` (success/error/warning/info), `dismissible` |
| Fil d'Ariane | `<Breadcrumb>` | `items` |
| Champ avec label + erreur | `<FormField>` | `label`, `error`, `required`, slot default |
| Navigation par onglets | `<Tabs>` | `tabs`, `modelValue` |
| État vide | `<EmptyState>` | `title`, `description`, `icon`, slot `action` |

#### Composants composites — `components/`

| Usage | Composant |
|-------|-----------|
| Saisie de tags | `<ChipInput>` |
| Sélecteur pays/thème | `<CountryThemeSelector>` |
| Horaire de livraison | `<DeliveryTimeSelector>` |
| Niveau de détail | `<DetailLevelSelector>` |
| Sélecteur de profil | `<ProfileSelector>` |
| Nom du profil | `<ProfileNameSection>` |
| Barre de progression wizard | `<WizardProgressBar>` |
| Briefing dashboard | `<DashboardBriefing>` |
| Modal upgrade | `<UpgradeModal>` |
| Modal version | `<VersionModal>` |

#### Composants admin — `components/admin/`

| Usage | Composant |
|-------|-----------|
| Tableau des sources | `<SourceDataTable>` |
| Dialogue formulaire source | `<SourceFormDialog>` |
| Dialogue actions utilisateur | `<UserActionsDialog>` |
| Onglets détail utilisateur | `<UserDetailTabs>` |
| Tableau des utilisateurs | `<UserDataTable>` |

#### Composants pipeline — `components/pipeline/`

| Usage | Composant |
|-------|-----------|
| Timeline pipeline | `<PipelineTimeline>` |
| Liste articles scrapés | `<ScrapedArticleList>` |

#### Landing page — `components/`

| Usage | Composant |
|-------|-----------|
| Navbar landing | `<LandingNavbar>` |
| Hero section | `<LandingHero>` |
| Footer landing | `<LandingFooter>` |
| Section fonctionnalités | `<FeaturesSection>` |
| Carte fonctionnalité | `<FeatureCard>` |
| Mockup animé briefing | `<AnimatedBriefingMockup>` |
| Bande de confiance | `<TrustStrip>` |
| Section tarifs | `<PricingSection>` |

#### Layout & Navigation — `components/`

| Usage | Composant |
|-------|-----------|
| Navbar dashboard | `<DashboardNavbar>` |
| Sidebar dashboard | `<DashboardSidebar>` |

> ⚠️ Les éléments HTML natifs `<input>`, `<select>`, `<button>`, `<textarea>` sont **interdits**
> dans tout `.vue` hors de `components/ui/`.

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
```

---

## Checklist before submitting a component

- [ ] No native `<button>`, `<input>`, `<select>`, `<textarea>` in page or layout templates
- [ ] No hardcoded color hex or rgba values — use `var(--...)` tokens
- [ ] Rendering matches the project's design references
- [ ] Dark mode supported via CSS tokens (no fixed colors)
- [ ] All user-visible strings go through the i18n system
- [ ] A Storybook story exists or has been updated for this component
