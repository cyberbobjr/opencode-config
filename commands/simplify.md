---
description: Review changed files for reuse, quality, and efficiency. Fix issues found.
---

Review all changed files for reuse, quality, and efficiency. Fix any issues found.

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

When done, briefly summarize what was fixed (or confirm the code was already clean).
