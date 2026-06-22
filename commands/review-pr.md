---
description: Analyze GitHub PR comments/reviews, classify by relevance/reliability, propose actions, fix, commit/push, then reply
argument:
  optional: true
  description: PR number or URL (e.g. 9, https://github.com/owner/repo/pull/9)
---

# Review PR

> **Invocation**: `/review-pr` or `/review-pr <number|URL>`

## Mission

Fetch comments and reviews from a GitHub Pull Request, classify them by relevance and reliability, and produce an actionable synthesis. Then propose interactive choices: fix all, fix critical only, or answer questions. Never post replies before corrections are committed and pushed.

## Required steps

### 1. Fetch PR data

If no argument is provided, use the current PR (latest created or linked to current branch).

Run in parallel via `gh`:

```bash
gh pr view <num> --json title,body,comments,reviews
gh api repos/<owner>/<repo>/pulls/<num>/comments
gh api repos/<owner>/<repo>/issues/<num>/comments
```

### 2. Analyze each comment

For each comment, determine:

| Criterion | Questions |
|-----------|-----------|
| **Relevance** | Does the comment flag a potential bug (🔴 Critical), an operational risk (🟡 Medium), or a cosmetic detail (🟢 Low)? |
| **Reliability** | Is the diagnosis verifiable/reproducible (🟢 High), speculative (🔶 Medium), or unfounded (🔴 Low)? |

Classification rules:
- **High Reliability**: Comment cites a specific line, the issue is reproducible by reading the code
- **Medium Reliability**: The issue is plausible but needs verification
- **Low Reliability**: Comment is vague, hypothetical, or incorrect
- **Critical Relevance**: Crash, data loss, security flaw, functional regression
- **Medium Relevance**: Operational risk, unexpected behavior, perf regression
- **Low Relevance**: Style, comment, documentation, cosmetic refactor

Also classify by type:
- **bug** — functional defect or regression
- **refactor** — code improvement without functional change
- **question** — request for clarification, not a correction
- **nit** — style, conventions, minor preference
- **security** — vulnerability or security risk
- **performance** — necessary optimization
- **praise** — approval (no action needed)

### 3. Build the summary table

```
## Comment Summary — MR #[num]

| # | Type | File | Comment | Reliability | Relevance | Priority |
|---|------|------|---------|-------------|-----------|----------|
| 1 | bug | `path/file.py:12` | 1-2 sentence summary | 🟢 High | 🔴 Critical | critical |
| 2 | question | `path/file.ts:5` | 1-2 sentence summary | 🟢 High | 🟢 Low | — |
| 3 | nit | `path/file.vue:8` | 1-2 sentence summary | 🟢 High | 🟢 Low | low |
```

Priority mapping:
- **critical** = `security` or `bug` with Critical Relevance and runtime impact
- **high** = `bug` Medium Relevance, `performance`
- **medium** = `refactor`
- **low** = `nit`
- **—** = `question`, `praise`

### 4. Propose options

After the table, ask the user exactly these 3 choices:

> **What do you want to do?**
>
> 1. **Fix all** — Address all comments (questions → reply without code change, others → fix)
> 2. **Critical only** — Fix only critical or high comments, reply to questions without code change
> 3. **Answer questions** — Reply ONLY to `question` and `praise`, no code changes at all

Wait for the answer before continuing.

### 5. Execution

#### If option 1 or 2 (fixes)

For each comment to fix:
1. Read the file and understand the context
2. Apply the change
3. Verify lint/typecheck/tests if relevant

Once all fixes are done:
1. `git add -A && git commit -m "address review comments from PR #<num>"`
2. `git push`
3. Verify CI passes: `gh pr checks <num> --watch`

#### If option 3 (replies only)

Skip directly to step 6 without modifying any file, without commit, without push.

### 6. Reply to each comment

For each PR comment (including questions and praise), post a reply in **English** via:

```bash
cat > /tmp/reply.json << 'ENDJSON'
{"body": "Your reply text addressing the comment directly."}
ENDJSON
gh api repos/<owner>/<repo>/pulls/<num>/comments/<comment_id>/replies --input /tmp/reply.json
```

Shell escaping: if the body contains backticks, `$()`, or other special characters, use the temporary JSON file as shown above.

Each reply must:
- Reference the specific comment
- For fixes: explain what was changed
- For questions: give a direct answer
- Mark as resolved if applicable

### 7. List unaddressed comments (option 2 only)

If option 2 was chosen, list the unaddressed comments in a dedicated section.

## Rules

- 🔍 Use `gh` for all GitHub queries
- 📊 Always 3 relevance levels (Critical / Medium / Low)
- 🎯 Each comment must have a clear recommendation (fix / investigate / ignore)
- 🇬🇧 Summary, recommendations, and individual replies: **English always**
- ⏳ **Never post replies before commit/push** — replies come AFTER fixes
- ✅ Always verify lint/typecheck/tests after each fix
- 📝 Commit message: `"address review comments from PR #<num>"`
