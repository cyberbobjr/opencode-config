---
description: Coordinates the user story workflow — refinement, TDD implementation, QA, quality gates, commit
argument:
  optional: true
  description: "Sub-command: status (default), dashboard, US X.Y (e.g. 'US 1.3'), refine, secops-tm, implement, secops-cr, qa, simplify, commit, done, block, notes"
---

# Next Story — Workflow Coordinator

> Requires the Kanban server: `python .opencode/kanban/server.py`
>
> All drag-and-drop actions on the Kanban dashboard route through `/next-story` with the matching sub-command.
>
> **Invocation**:
> - `/next-story` → Project status + next story
> - `/next-story US 1.3` → Full cycle (refinement → TDD → SecOps → QA → quality gates → commit)
> - `/next-story refine US 1.3` → Refinement + threat model, then stop *(drag → refining)*
> - `/next-story secops-tm US 1.3` → Threat model only, then advance to tdd *(drag → secops_tm)*
> - `/next-story implement US 1.3` → TDD → SecOps CR → QA → simplify → commit *(drag → tdd)*
> - `/next-story secops-cr US 1.3` → Code review only, then advance to qa *(drag → secops_cr)*
> - `/next-story qa US 1.3` → QA validation, then advance to simplify *(drag → qa)*
> - `/next-story simplify US 1.3` → Quality gates only + move to `commit_ready` *(drag → simplify)*
> - `/next-story commit US 1.3` → Quick commit + done *(drag → commit_ready)*
> - `/next-story done US 1.3` → Mark as completed without commit
> - `/next-story block US 1.3` → Block the story
> - `/next-story notes US 1.3` → Add a note to the story
> - `/feature "description"` → Create and implement a new feature (Backlog Phase 7)
> - `/fix "description"` → Create and fix a bug (Backlog Phase 7)
> - `/change "description"` → Create a change User Story with impact analysis (Backlog Phase 7)
> - `/refine US X.Y` → Dedicated Refinement Agent (challenges ACs)
> - `/tdd US X.Y` → TDD Agent (red-green-refactor)
> - `/qa US X.Y` → QA Agent (AC validation through tests)
> - `/simplify` → Quality / reuse / efficiency review
> - `/secops US X.Y` → DevSecOps Agent (threat-model or code-review)

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

### `/next-story dashboard` — HTML Dashboard

1. Open http://localhost:8765/ in the browser
2. If the server is not running: prompt to run `python .opencode/kanban/server.py`

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

### `/next-story refine US X.Y` — Refinement only *(drag → refining)*

1. Check status via `kanban-get-story("US X.Y")`
   - If not yet `refining`: call `kanban-move-story("US X.Y", "refining")`
   - If already `refining`: continue directly (dashboard or MCP already did the move)
2. Delegate to `/refine US X.Y`
   > ⚠️ **Orchestrator context**: after /refine completes, do NOT ask about advancing — next-story handles the move to `secops_tm`.
3. Call `kanban-move-story("US X.Y", "secops_tm")`
4. Display the report and stop

### `/next-story secops-tm US X.Y` — Threat model only *(drag → secops_tm)*

Used when the dashboard moves a card to the `secops_tm` column (refinement already done).

1. Check status via `kanban-get-story("US X.Y")`
   - If not yet `secops_tm`: call `kanban-move-story("US X.Y", "secops_tm")`
   - If already `secops_tm`: continue directly
2. Run `/secops "US X.Y" mode=threat-model`
   > ⚠️ **Orchestrator context**: after /secops completes, do NOT ask about advancing — next-story handles the move to `tdd`.
3. If `review_required: true` → display Security Brief and **[STOP]** — wait for user validation
4. Call `kanban-move-story("US X.Y", "tdd")`
5. Display summary — story is ready for implementation

### `/next-story implement US X.Y` — Implementation only (Steps 2→5) *(drag → tdd)*

1. Check the story status via `kanban-get-story("US X.Y")`
2. If not yet refined (status `pending` or `refining`): "This story must be refined first."
3. If already `tdd`: continue directly (dashboard already did the move)
   Otherwise: call `kanban-move-story("US X.Y", "tdd")`
4. Proceed with steps 2→3→4→5 (TDD → SecOps CR → QA → quality gates → commit)
5. The QA→TDD corrective loop is active

### `/next-story secops-cr US X.Y` — Code review only *(drag → secops_cr)*

Used when the dashboard moves a card to the `secops_cr` column (TDD already passed).

1. Check status via `kanban-get-story("US X.Y")`
   - If not yet `secops_cr`: call `kanban-move-story("US X.Y", "secops_cr")`
   - If already `secops_cr`: continue directly
2. Run `/secops "US X.Y" mode=code-review`
   > ⚠️ **Orchestrator context**: after /secops completes, do NOT ask about advancing — next-story handles the move to `qa`.
3. If critical issues found → **[STOP]** ask user how to proceed (fix or force-pass)
4. Call `kanban-move-story("US X.Y", "qa")`
5. [AUTO] continue with `/next-story qa US X.Y`

### `/next-story qa US X.Y` — QA validation only *(drag → qa)*

Used when the dashboard moves a card to the `qa` column.

1. Check status via `kanban-get-story("US X.Y")`
   - If not yet `qa`: call `kanban-move-story("US X.Y", "qa")`
   - If already `qa`: continue directly
2. Call `kanban-update-story("US X.Y", '{"qa": {"status": "in_progress"}}')`
3. Delegate to `/qa US X.Y`
   > ⚠️ **Orchestrator context**: after /qa completes, do NOT ask about advancing — next-story handles the move to `simplify`.
4. **Branch based on result:**
   - QA PASSED → `kanban-update-story` qa.status=passed → `kanban-move-story("US X.Y", "simplify")` → [AUTO] `/next-story simplify US X.Y`
   - QA FAILED → display failures → **[STOP]** ask: fix (back to TDD) / block / force-pass

### `/next-story simplify US X.Y` — Quality Gates (triggered from dashboard) *(drag → simplify)*

Run quality gates for the story and move it to `commit_ready` when all pass.
Used when the dashboard moves a card to the `simplify` column.

1. Retrieve context via `kanban-get-story("US X.Y")`
2. Run the commands listed in `.opencode/rules/commands.md` section "Quality Gates" → "Avant chaque push / PR"
3. Run `/simplify US X.Y` — passes the story ID so the report is written to the story
   > ⚠️ **Orchestrator context**: after /simplify completes, do NOT ask about advancing — next-story moves to `commit_ready` and displays the summary.
4. Fix any issues found
5. Call `kanban-move-story("US X.Y", "commit_ready", "simplify")`
6. Display summary — the story is ready for commit

---

### `/next-story commit US X.Y` — Quick commit

1. Verify that quality gates pass
2. Propose a conventional commit message
3. `git add . && /commit`
4. `kanban-move-story("US X.Y", "completed", "commit")`

### `/next-story done US X.Y` — Mark as completed without commit

1. `kanban-move-story("US X.Y", "completed", "dashboard")`
2. Display the next story

### `/next-story block US X.Y` — Block a story

1. `kanban-move-story("US X.Y", "blocked")`
2. Ask: "Add a note explaining the blocker?"

### `/next-story notes US X.Y` — Add a note

1. Call `kanban-get-story("US X.Y")` to retrieve the story
2. Ask for the note
3. Call `kanban-update-story("US X.Y", '{"_actor": "user", "notes": "the note"}')`

---

The full workflow in `.opencode/rules/workflow.md` (section "Cycle d'une Story") describes the optimal cycle. The fastest path remains:

```
/next-story US X.Y
```
