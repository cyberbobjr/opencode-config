# Composants UI — Règles absolues

## Référence visuelle (TOUJOURS consulter en premier)

Avant d'implémenter tout composant ou page, ouvre et consulte le fichier de référence :
- `docs/designs/d-hybrid.html` — rendu complet dashboard + landing (design retenu)
- `docs/designs/landing.html` — landing page seule
- `docs/designs/interface-mockup.html` — mockup interface détaillé

Ton implémentation Vue DOIT produire un rendu visuellement identique à ces références.

---

## Composants disponibles — API exacte

Importe toujours depuis `@/components/ui/`. Ne jamais créer un élément HTML natif
si un composant ui/ existe.

### Button
```vue
import Button from '@/components/ui/Button.vue'

<!-- Taille par défaut : toujours "m" sauf raison explicite -->
<Button variant="primary" size="m">Sauvegarder</Button>
<Button variant="outline" size="m">Annuler</Button>
<Button variant="ghost" size="m">Ignorer</Button>
<Button variant="upgrade" size="l">Passer à Pro</Button>
```
- `variant`: `primary | outline | ghost | upgrade`
- `size`: `xs | sm | m | l | xl` — défaut `m` (padding 10px/20px)
- **INTERDIT** : `<button>` natif dans les templates de pages ou de composants
- **INTERDIT** : `size="xs"` ou `size="sm"` pour des CTA ou actions principales

### Input
```vue
import Input from '@/components/ui/Input.vue'

<Input v-model="email" type="email" size="md" placeholder="..." />
```
- `size`: `sm | md | lg` — défaut `md`
- `type`: `text | email | password | search`
- **INTERDIT** : `<input>` natif dans les templates

### Tag
```vue
import Tag from '@/components/ui/Tag.vue'

<Tag variant="primary">Géopolitique</Tag>
<Tag variant="blue">Économie</Tag>
<Tag variant="warning">Technologie</Tag>
<Tag variant="teal">Climat</Tag>
```
- `variant`: `primary | blue | warning | teal`
- `size`: `sm | md` — défaut `sm` (10px uppercase)

### Card
```vue
import Card from '@/components/ui/Card.vue'
<Card>...</Card>
```

### Badge
```vue
import Badge from '@/components/ui/Badge.vue'
<Badge>94%</Badge>
```

### Select
```vue
import Select from '@/components/ui/Select.vue'
<Select v-model="value" :options="options" />
```

### Textarea
```vue
import Textarea from '@/components/ui/Textarea.vue'
<Textarea v-model="text" :autoResize="true" />
```

### Autres disponibles
`ProgressBar`, `Spinner`, `Toast`, `Toaster`, `ToggleSwitch`, `Skeleton`,
`RadioGroup`, `CheckboxGroup`, `PasswordField`, `Icon`

---

## Tokens CSS — obligatoires

Ne jamais hardcoder de couleur hex ou rgba. Utiliser exclusivement les variables CSS :

```css
/* Couleurs */
var(--bg)            /* fond page */
var(--surface)       /* cartes */
var(--surface-alt)   /* hover, strips */
var(--ink)           /* texte principal */
var(--ink-secondary) /* texte secondaire */
var(--ink-muted)     /* labels, timestamps — jamais sous 18px */
var(--border)        /* bordures */
var(--border-light)  /* séparateurs */
var(--primary)       /* rouge — actions principales */
var(--primary-hover)
var(--primary-soft)
var(--blue)          /* économie */
var(--blue-soft)
var(--teal)          /* succès */
var(--teal-soft)
var(--success)       /* confiance ≥80% */
var(--warning)       /* confiance 50-79% */
var(--error)         /* confiance <50% */

/* Espacement */
var(--space-xs)   /* 8px */
var(--space-sm)   /* 12px */
var(--space-md)   /* 16px */
var(--space-lg)   /* 24px */
var(--space-xl)   /* 28px */
var(--space-2xl)  /* 32px */
var(--space-3xl)  /* 48px */
```

---

## Typographie

| Usage | Police | Taille |
|-------|--------|--------|
| Titres articles | `font-serif` (Newsreader) | 17–40px |
| Corps texte | `font-sans` (Inter) | 13–14px |
| Données, scores | `font-mono` (JetBrains Mono) | 11–12px |
| Navigation, labels | `font-sans` uppercase + tracking | 10–13px |

---

## Anti-patterns — STRICTEMENT INTERDITS

```vue
<!-- ❌ Bouton natif -->
<button class="px-3 py-1 bg-red-500">...</button>

<!-- ✅ -->
<Button variant="primary" size="m">...</Button>

<!-- ❌ Couleur hardcodée -->
<div style="color: #C41E3A">...</div>
<div class="text-red-600">...</div>

<!-- ✅ -->
<div style="color: var(--primary)">...</div>

<!-- ❌ Input natif -->
<input type="email" class="border rounded p-2" />

<!-- ✅ -->
<Input type="email" size="md" v-model="email" />

<!-- ❌ Taille de bouton arbitraire pour un CTA -->
<Button size="xs">S'inscrire</Button>

<!-- ✅ -->
<Button size="m" variant="primary">S'inscrire</Button>
```

---

## Checklist avant de soumettre un composant

- [ ] Aucun `<button>`, `<input>`, `<select>`, `<textarea>` natif dans les templates
- [ ] Aucune couleur hex ou rgba hardcodée (utiliser `var(--...)`)
- [ ] Les boutons CTA et actions principales utilisent `size="m"` minimum
- [ ] Le rendu correspond à la référence visuelle `.opencode/d-hybrid.html`
- [ ] Le thème sombre est supporté (toutes les couleurs via tokens CSS)
- [ ] Le texte UI passe par `vue-i18n` (pas de chaînes hardcodées)
