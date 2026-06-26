# UI Components — Rules

## Before implementing any component or page

1. Read the project's design system — see `AGENTS.md` for the exact location (typically `docs/design-system.md`)
2. The design system defines: available components and their APIs, CSS custom properties, typography, spacing tokens, and visual references
3. Your implementation MUST visually match the design references described in the project's design system

---

## Core Rules

### Use design system components — never native HTML elements

If the project has a design system component for an element, use it. Never use raw `<button>`, `<input>`, `<select>`, or `<textarea>` in page or layout templates.

| Instead of | Use |
|------------|-----|
| `<button>` | The design system `<Button>` component |
| `<input>` | The design system `<Input>` component |
| `<select>` | The design system `<Select>` component |
| `<textarea>` | The design system `<Textarea>` component |

If a required component does not exist in the design system: create a User Story to add it — do not fall back to native HTML in the meantime.

### Use CSS custom properties — never hardcode colors

Never hardcode hex or rgba values. Use the project's CSS custom properties (defined in the design system) for all colors, spacing, and typography.

```css
/* ❌ Never */
color: #C41E3A;
background: rgba(0, 0, 0, 0.5);

/* ✅ Always */
color: var(--primary);
background: var(--surface-overlay);
```

### Internationalisation

All UI strings must go through the project's i18n system (see `AGENTS.md` or `conventions.md` for the tool used). Never hardcode user-visible text.

---

## Storybook

Refer to `rules/conventions.md` for the Storybook story requirements that apply to all Vue components.

---

## Checklist before submitting a component

- [ ] No native `<button>`, `<input>`, `<select>`, `<textarea>` in page or layout templates
- [ ] No hardcoded color hex or rgba values — use `var(--...)` tokens
- [ ] Rendering matches the project's design references
- [ ] Dark mode supported via CSS tokens (no fixed colors)
- [ ] All user-visible strings go through the i18n system
- [ ] A Storybook story exists or has been updated for this component
