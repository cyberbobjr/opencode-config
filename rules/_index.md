# Rules Disponibles — Chargement à la Demande

> **IMPORTANT** : Ces règles ne sont PAS chargées automatiquement.
> Utilise l'outil Read pour charger uniquement les fichiers pertinents à la tâche en cours.
> Ne charge jamais toutes les rules par défaut — évalue la tâche d'abord.

> Ces règles sont **génériques et réutilisables** entre projets. Tout ce qui est
> spécifique à un projet (stack, commandes, catalogue de composants, design system)
> vit dans `AGENTS.md` à la racine du projet — les règles y défèrent systématiquement.

## Règle de chargement

Au début de chaque session, identifie la nature de la tâche et charge UNIQUEMENT les règles utiles :

| Fichier | Charger quand... |
|---------|-----------------|
| `.opencode/rules/ui-components.md` | Travail sur l'UI : composants, CSS, design system, conventions frontend, catalogue de composants, stories |
| `.opencode/rules/conventions.md` | Conventions de code (backend / frontend), règles Git, format kanban Markdown |
| `.opencode/rules/commands.md` | Commandes à exécuter : installation, tests, lint, migrations, déploiement, quality gates, infra |
| `.opencode/rules/workflow.md` | Stories kanban, `/refine`, `/implement`, TDD, QA, `/commit`, `/next-story`, cycle de story |
| `.opencode/rules/architecture.md` | Guardrails architecturaux — où trouver les décisions projet (`AGENTS.md`, `docs/`) et ce qu'il ne faut pas faire |
| `.opencode/rules/code-exploration.md` | Navigation de code, recherche de symboles, importeurs, blast radius, exploration |

## Exemples de correspondance

- *"ajoute un composant de formulaire"* → charger `ui-components.md`
- *"implémente la US X.Y"* → charger `workflow.md` + `ui-components.md` (si frontend) ou `workflow.md` + `conventions.md` (si backend)
- *"comment lancer les tests ?"* → charger `commands.md`
- *"où est défini le service X ?"* → charger `code-exploration.md`
- *"refactor un worker / une tâche de fond"* → charger `architecture.md` + `conventions.md`
- *"écris un message de commit"* → charger `conventions.md`
