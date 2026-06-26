---
description: Review changed files for reuse, quality, and efficiency. Fix issues found. Optionally writes a simplify_report to the Kanban story.
argument:
  optional: true
  description: "Story ID to update after review, e.g. 'US 1.3'. If omitted, report is shown in chat only."
---

Review all changed files for reuse, quality, and efficiency. Fix any issues found.

The argument (if provided) is the story ID to update: `/simplify US 1.3`

## Phase 1: Identify Changes

Run `git diff` (or `git diff HEAD` if there are staged changes) to see what changed. If there are no git changes, review the most recently modified files that the user mentioned or that you edited earlier in this conversation.

## Phase 2: Launch Three Review Agents in Parallel

Use the Task tool to launch all three agents concurrently in a single message:

- code-simplify-reuse: Review for reuse — duplicated functions, inline logic that could use existing utilities
- code-simplify-quality: Review for quality — redundant state, parameter sprawl, copy-paste, leaky abstractions, nested conditionals, unnecessary comments, dead code
- code-simplify-efficiency: Review for efficiency — unnecessary work, missed concurrency, hot-path bloat, memory issues

Pass each agent the full diff so it has the complete context.

## Phase 3: Fix Issues

Wait for all three agents to complete. Aggregate their findings and fix each issue directly. If a finding is a false positive or not worth addressing, note it and move on — do not argue with the finding, just skip it.

When done, compile the results:
- `issues_found`: total number of issues across all three agents
- `issues_fixed`: number of issues actually fixed (false positives excluded)
- Per-agent summary (one sentence each): what was found / confirmed clean

## Phase 4: Persist Report to Story (MANDATORY if story ID provided)

**This phase is required whenever a story ID was passed as argument — including when called via the `/next-story` orchestrator.** Never skip to Phase 5 without writing the report first.

Call `kanban-update-story` with:

```json
{
  "_actor": "simplify",
  "simplify_comments": "<1-2 sentences summarising what was simplified or 'RAS' if code was already clean>",
  "simplify_report": {
    "status": "fixed",
    "issues_found": <total>,
    "issues_fixed": <fixed>,
    "agents": {
      "reuse": "<one-line summary>",
      "quality": "<one-line summary>",
      "efficiency": "<one-line summary>"
    },
    "notes": "<overall 1-2 sentence summary of what changed or that the code was already clean>"
  }
}
```

Use `"status": "passed"` when no issues were found, `"status": "fixed"` when issues were found and fixed, `"status": "skipped"` if there were no relevant files to review.

## Phase 5: Advance to Commit

After the report is written:
- **Called via `/next-story` orchestrator** (the calling context explicitly says "Orchestrator context") → call `kanban-move-story("$ARGUMENTS", "commit_ready", "simplify")` and return the report. The orchestrator handles the commit confirmation.
- **Called standalone** → ask:
  > "✅ Simplify complete — [N] issues found, [N] fixed. Move to `commit_ready` and commit? [yes / no]"
  - **yes** → `kanban-move-story("$ARGUMENTS", "commit_ready", "simplify")` → propose a conventional commit message → stage and commit
  - **no** → stop. "To commit later: drag the card to `commit_ready` on the dashboard."
