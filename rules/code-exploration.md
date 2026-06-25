# Code Exploration Policy

Always use jCodemunch-MCP tools for code navigation. Never fall back to Read, Grep, Glob, or Bash for code exploration.

## Start Any Session

1. `resolve_repo { "path": "." }` — confirm the project is indexed. If not: `index_folder { "path": "." }`
2. `suggest_queries` — when the repo is unfamiliar

## Finding Code

- symbol by name → `search_symbols` (add `kind=`, `language=`, `file_pattern=` to narrow)
- string, comment, config value → `search_text` (supports regex, `context_lines`)
- database columns → `search_columns`

## Reading Code

- before opening any file → `get_file_outline` first
- one or more symbols → `get_symbol_source`
- symbol + its imports → `get_context_bundle`
- specific line range only → `get_file_content` (last resort)

## Repo Structure

- `get_repo_outline` → dirs, languages, symbol counts
- `get_file_tree` → file layout, filter with `path_prefix`

## Relationships & Impact

| Besoin | Outil |
|--------|-------|
| Ce qui importe ce fichier | `find_importers` |
| Où ce nom est utilisé | `find_references` |
| Cet identifiant est-il utilisé | `check_references` |
| Graphe de dépendances | `get_dependency_graph` |
| Ce qui casse si je change X | `get_blast_radius` (+ `include_depth_scores=true`) |
| Symboles changés depuis le dernier commit | `get_changed_symbols` |
| Code mort / inaccessible | `find_dead_code` |
| Symboles les plus importants | `get_symbol_importance` |
| Index à jour ? | `check_freshness` |
| Hiérarchie de classes | `get_class_hierarchy` |
| Symboles liés | `get_related_symbols` |
| Diff deux snapshots | `get_symbol_diff` |

## Retrieval avec budget token

- `get_ranked_context` (query + token_budget) — meilleur contexte pour une tâche
- `get_context_bundle` (+ token_budget=) — bundle borné

**Après avoir édité un fichier :** `index_file { "path": "/abs/path/to/file" }` pour maintenir l'index.
