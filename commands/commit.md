---
description: Analyze staged changes and propose a conventional commit message
argument:
  optional: true
  description: Additional context/instructions to guide commit message generation
---

# Commit

> **Invocation**: `/commit` or `/commit "additional context for message generation"`

## Mission

Analyze the staged changes (`git diff --cached`), propose a conventional commit message, and commit on the current branch after user confirmation.

## Required steps

### 1. Analyze staged changes

Run:
- `git diff --cached` — inspect all staged changes
- `git status` — verify nothing is missing or suspicious
- `git log --oneline -10` — reference recent messages for style consistency

### 2. Generate a commit message

Follow conventional commits format:
```
<type>(<scope>): <description>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature, new endpoint, new component |
| `fix` | Bug fix, crash, incorrect behavior |
| `refactor` | Restructuring without behavior change |
| `perf` | Performance optimization |
| `docs` | Documentation, README, AGENTS.md, CLAUDE.md |
| `test` | Adding or modifying tests only |
| `chore` | CI, tooling, dependencies, cleanup, config |
| `style` | Formatting, linting, whitespace (no logic change) |

Rules:
- Description in **English** always
- Imperative verb form (present tense)
- Max 72 characters for subject line
- No trailing period
- If an argument is provided, use it as additional context/instructions to guide the auto-generation of the commit message (e.g., `/commit "focus on the database migration aspect"` will steer the message toward migration-related scope and description)
- **For large commits (≥15 files or mixed concerns)**: add a detailed body with one bullet per logical change, each prefixed by its conventional-commit type (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `style:`). Group related changes under the same bullet. Example:
  ```
  feat: add structure_bailly.py (LLM-based structuring script)
  feat: replace LexiconPopin with reworked StrongPopin
  test: expand StrongPopin tests and share route tests
  chore: remove unused imports, update lockfile
  ```

### 3. Propose to user

```
Proposed commit:
  <type>(<scope>): <description>

Staged files:
  M  path/to/file1.py
  A  path/to/new.py

Confirm? [y/n]
```

### 4. Execute

If user confirms:
- `git commit -m "<message>"` on the current branch
- Display the commit hash

If user declines, ask if they want to edit the message or cancel.

## Security rules

- ❌ **Never** commit `.env`, `credentials.*`, `*.key`, `*.pem`
- ❌ **Never** `git push` without explicit request
- ❌ **Never** `git commit --amend` on a pushed commit unless explicitly asked
- ✅ If the pre-commit hook fails, fix and create a NEW commit (no amend)
