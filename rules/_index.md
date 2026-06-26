# Rules Disponibles — Chargement à la Demande

> **IMPORTANT** : Ces règles ne sont PAS chargées automatiquement.
> Utilise l'outil Read pour charger uniquement les fichiers pertinents à la tâche en cours.
> Ne charge jamais toutes les rules par défaut — évalue la tâche d'abord.

## Règle de chargement

Au début de chaque session, identifie la nature de la tâche et charge UNIQUEMENT les règles utiles :

| Fichier | Charger quand... |
|---------|-----------------|
| `.opencode/rules/ui-components.md` | Travail sur `.vue`, CSS, design system, composants UI, Button/Input/Select, tokens CSS, typographie |
| `.opencode/rules/conventions.md` | Conventions code Python/TypeScript, Storybook stories, format kanban Markdown, règles Git |
| `.opencode/rules/commands.md` | Commandes à exécuter, installation, tests, déploiement, quality gates, Docker, Celery |
| `.opencode/rules/workflow.md` | Stories kanban, `/refine`, `/implement`, TDD, QA, `/commit`, `/next-story`, cycle de story |
| `.opencode/rules/architecture.md` | Guardrails architecturaux — où trouver les décisions projet (AGENTS.md, docs/) et ce qu'il ne faut pas faire |
| `.opencode/rules/code-exploration.md` | Navigation de code, recherche de symboles, `find_importers`, `search_symbols`, exploration |

## Exemples de correspondance

- *"ajoute un composant Select"* → charger `ui-components.md` + `conventions.md`
- *"implémente la US 7-32"* → charger `workflow.md` + selon le type de la story
- *"comment lancer les tests ?"* → charger `commands.md`
- *"où est défini le service de scraping ?"* → charger `code-exploration.md`
- *"refactor le worker Celery"* → charger `architecture.md` + `conventions.md`
