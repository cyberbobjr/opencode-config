---
description: Project status view and full-cycle story orchestrator (refine → secops-tm → tdd → secops-cr → qa → simplify → commit). Individual steps are triggered directly by the Kanban dashboard on card drag.
argument:
  optional: true
  description: "US X.Y for full cycle, blank for project status"
---

# Next Story — Status & Full-Cycle Orchestrator

> **Invocation**:
> - `/next-story` → Project status + next story to process
> - `/next-story US X.Y` → Full cycle (refinement → TDD → SecOps → QA → quality gates → commit)
>
> All other steps (refine, secops-tm, tdd, secops-cr, qa, simplify, commit) are **triggered directly** by the Kanban dashboard when cards are dragged between columns.

## General Rules

- ✅ **Read `AGENTS.md`** for project conventions and quality gates — detailed commands in `.opencode/rules/commands.md`
- ✅ **Read the design system reference** (`docs/design-system.md`, tokens résumés dans `.opencode/rules/conventions.md`) before any frontend implementation
- ✅ **Use the Kanban server MCP tools** (`kanban-get-story`, `kanban-list-stories`, `kanban-update-story`, `kanban-move-story`, `kanban-create-story`, `kanban-get-next-pending`, `kanban-get-stats`) — all story data lives in `user-stories/*.json` served by the server
- ✅ **Delegate refinement to `/refine US X.Y`** — do not do it yourself
- ❌ **Never modify `user-stories/*.json` files directly** — use the MCP tools
- ❌ **Do not start implementation** before refinement is validated
- ❌ **Never implement a frontend component** without checking the design system

### Modifying a story ≠ Refining a story

> ⚠️ This distinction is critical — confusing the two moves stories into the wrong state.

| Situation | Correct action | What NOT to do |
|-----------|---------------|----------------|
| Fixing AC text | `kanban-update-story` only — status stays unchanged | ❌ `kanban-move-story → refining` |
| Adding / removing ACs | `kanban-update-story` only — status stays unchanged | ❌ `kanban-move-story → refining` |
| Updating description, notes | `kanban-update-story` only — status stays unchanged | ❌ `kanban-move-story → refining` |
| Launching a real refinement | `kanban-move-story → refining` **then** `/refine US X.Y` | — |

**Absolute rule:** `kanban-move-story` is only justified to **advance** through the pipeline (or on explicit user request). Any field update (ACs, description, notes, stack…) uses `kanban-update-story` without touching the `status`.

---

## Sub-command Behavior

### `/next-story` (default) — Status + next story

1. Call the `kanban-get-stats` MCP tool for global stats
2. Call `kanban-get-next-pending` for the next story
3. Display the result and ask if the user wants to start

### `/next-story US X.Y` — Full cycle

Execute each step **actively and sequentially**.

- **Auto-advance**: after steps 2, 2b (SecOps), and 3 (when PASSED), continue without asking
- **2 stop points**: after refinement (before coding) and before commit
- **1 conditional stop point**: when QA fails — the user decides what to do
- **Corrective loop**: if QA fails, TDD resumes with the failure context

---

**Step 1 — Refinement + Threat Model**

1. Check status via `kanban-get-story("US X.Y")`.
   - **If already `refining`** (triggered from the dashboard): **skip directly to step 2** — do not call `kanban-move-story` again, the dashboard already did it
   - **Otherwise**: call `kanban-move-story("US X.Y", "refining")` then proceed to step 2
2. Delegate to `/refine US X.Y` — apply `.opencode/commands/refine.md`:
   > ⚠️ **Orchestrator context**: after /refine completes, do NOT ask about advancing — next-story handles the move to `secops_tm`.
   - Mandatory question/answer cycle via the OpenCode `question` tool
   - 8 to 12 questions alternating the 4 roles (PO, Architect, Dev, DevSecOps)
   - Each question challenges the requirement, proposes improvements, goes further
3. Retrieve the refinement report (decisions + revised ACs)
4. Call `kanban-move-story("US X.Y", "secops_tm")` — move to security review
5. Run `/secops "US X.Y" mode=threat-model` — attack surface identification
   > ⚠️ **Orchestrator context**: after /secops completes, do NOT ask about advancing — next-story handles the move to `tdd`.
6. If `review_required: true` → display Security Brief, **[STOP]** request validation before continuing
7. Call `kanban-move-story("US X.Y", "tdd")` — ready for implementation
8. **[STOP]** Ask: "Proceed to TDD implementation?" — if yes → Step 2, otherwise STOP

---

**Step 2 — TDD Implementation**

1. Announce: `🧪 Starting TDD cycle for US X.Y...`
2. Call `kanban-update-story("US X.Y", '{"tdd": {"status": "in_progress"}}')`
3. Delegate to `/tdd US X.Y` (fully apply `.opencode/commands/tdd.md`):
   > ⚠️ **Orchestrator context**: after /tdd completes, do NOT ask about advancing — next-story handles the move to `secops_cr`.
   - RED: write the tests (they fail)
   - GREEN: implement the minimum code
   - REFACTOR: clean up without breaking tests
   - Quality gates: run the commands defined in `.opencode/rules/commands.md` (section "Quality Gates") for the impacted stack
4. Summary: call `kanban-update-story(...)` with TDD results
5. Display the TDD report (tests, coverage, files)
6. **Branch based on result:**

   ```
    TDD PASSED → [AUTO] kanban-move-story("US X.Y", "secops_cr")
      → Security review: `/secops "US X.Y" mode=code-review`
         > ⚠️ **Orchestrator context**: after /secops mode=code-review completes, do NOT ask about advancing — next-story handles the move to `qa`.
      → SecOps PASSED → [AUTO] kanban-move-story("US X.Y", "qa") → Step 3 (QA)
      → SecOps FAILED → [STOP] Ask:
        "What do you want to do?
         1. Fix the security issues (back to Step 2)
         2. Force-pass to QA (risks documented)"

    TDD FAILED → [STOP] Ask:
     "What do you want to do?
       1. Fix manually (restart a cycle)
       2. Block the story (kanban-move-story block)
       3. Force-pass to QA"
   ```

---

**Step 3 — QA Validation**

1. Announce: `🔍 Starting QA agent for US X.Y...`
2. Call `kanban-update-story("US X.Y", '{"qa": {"status": "in_progress"}}')`
3. Delegate to `/qa US X.Y` (fully apply `.opencode/commands/qa.md`)
   > ⚠️ **Orchestrator context**: after /qa completes, do NOT ask about advancing — next-story handles the move to `simplify`.
4. Retrieve the QA report (status, ac_covered, tests, failures)
5. **Branch based on result:**

   ```
    QA PASSED (all ACs green)
      → Call kanban-update-story with qa.status=passed
      → kanban-move-story("US X.Y", "simplify")
      → Display QA report
      → [AUTO] → Step 4

    QA FAILED (at least one red AC)
      → Call kanban-update-story with qa.status=failed
      → Display detailed QA report (failed ACs with test, error, file:line)
      → [STOP] Ask:
        "What do you want to do?
         1. Fix — back to Step 2 (TDD fix-failing-acs mode, context passed)
         2. Block — kanban-move-story block + STOP
         3. Force — force qa-done passed → [AUTO] Step 4"
   ```

---

**Step 4 — Quality Gates**

1. Run the commands listed in `.opencode/rules/commands.md` section "Quality Gates" → "Avant chaque push / PR"
2. Run `/simplify US X.Y` — passes the story ID so the report is written to the story
   > ⚠️ **Orchestrator context**: after /simplify completes, do NOT ask about advancing — next-story moves to `commit_ready` and asks about the commit.
3. Fix any issues found
4. Call `kanban-move-story("US X.Y", "commit_ready", "simplify")`
5. **[STOP]** Ask: "Approve the commit?" — if yes → Step 5, otherwise STOP

---

**Step 5 — Commit**

1. Propose a conventional commit message
2. After validation: `git add .` then `git commit -m "..."` (or `/commit`)
3. Call `kanban-move-story("US X.Y", "completed", "commit")`
4. Display the next available story
