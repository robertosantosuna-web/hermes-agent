---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing
- **Forex backtests & heavy computation** — zero Hermes tokens, use `codex exec` pattern (see below)

Requires the codex CLI and a git repository.

## Device Auth (Headless/Telegram Setup)

When running Codex on a headless system or via Telegram:

```bash
# Run in background with PTY (Codex is interactive)
terminal(command="codex login --device-auth", background=true, pty=true, timeout=300)

# Poll for the auth code
process(action="poll", session_id="<id>")

# Output shows:
# 1. Open: https://auth.openai.com/codex/device
# 2. Enter code: XXXX-XXXXX

# After user completes, poll again to confirm
process(action="wait", session_id="<id>", timeout=180)
```

**Check status:** `codex login status`

## Authentication

Codex needs OpenAI auth. Three methods (in priority order):

### Method 1: Device Auth (works remotely, no browser needed on agent side)
```bash
# Run in background with PTY
terminal(command="codex login --device-auth", background=true, pty=true, timeout=300)
# Poll output to get the URL + code
process(action="poll", session_id="<id>")
# → URL: https://auth.openai.com/codex/device
# → Code: XXXX-XXXXX (15 min expiry)
# User completes in their browser → process exits with "Successfully logged in"

# Verify
terminal(command="codex login status")
# → "Logged in using ChatGPT"
```

### Method 2: API Key
```bash
export OPENAI_API_KEY=sk-...
# Or pipe to stdin:
printenv OPENAI_API_KEY | codex login --with-api-key
```

### Method 3: Hermes-managed OAuth
```bash
hermes auth add openai-codex
```

**Pitfall:** `hermes auth add openai-codex` opens a browser window and times out
in headless environments. Prefer device auth (Method 1).

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--sandbox workspace-write` | Allows file changes within workspace (preferred over deprecated `--full-auto`) |
| `--skip-git-repo-check` | Run outside git repos (required for automated/cron contexts) |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

## Forex Delegation Pattern (26/05/2026)

For forex backtesting, SMC fractal scans, and other heavy computation, delegate to Codex
to save Hermes/DeepSeek tokens. See `forex-choch-m15` skill for full reference.

### One-shot
```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  "Run <script>. Save output to ~/.hermes/forex/codex_output/<name>.json. Don't ask." 2>&1
```

### Cron (zero Hermes tokens)
`scripts/codex_daily_backtests.sh` — no_agent cron runs backtests + SMC fractal at 10h.
Results: `~/.hermes/forex/codex_output/`.

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Córtex Dual — Codex as Neural Network Peer

Codex (GPT-5.5) operates as the **Right Lobe** of the Córtex Dual, alongside Hermes/DeepSeek (Left Lobe).
Both lobes are **PEERS** — equal in hierarchy, subordinate only to Roberto.

```
Roberto (supremo)
  └── Córtex Dual
        ├── Hermes (DeepSeek V4) — Left Lobe: strategy, decisions, communication
        └── Codex (GPT-5.5) — Right Lobe: code, backtesting, implementation
              └── Brain (subordinate)
```

### Onboarding Codex into the Neural Network

1. Install: `npm install -g @openai/codex`
2. Auth: `codex login --device-auth` (background+pty, send URL+code to user)
3. Init git repo in `~/.hermes/` so Codex can work on scripts
4. Have Codex read identity docs: `codex_onboarding.md`, `brain_governance.md`, `MEMORY.md`, `USER.md`
5. Have Codex read skills: `brain-architecture`, `forex-choch-m15`, `self-correction`
6. Verify: `cortex_bridge.py ask "confirm you're online"` → `cortex_bridge.py answer`

### Cortex Bridge Protocol (cortex_sync.json)

Script: `scripts/cortex_bridge.py`

```bash
# LEFT → RIGHT: queries and delegation
python3 scripts/cortex_bridge.py ask "should we trade USDJPY?"
python3 scripts/cortex_bridge.py delegate "fix the S/R detection bug"
python3 scripts/cortex_bridge.py consult "topic"  # ask + wait for response

# RIGHT → LEFT: answers and results
python3 scripts/cortex_bridge.py answer "CRT confirms BUY" --id ctx-0002
python3 scripts/cortex_bridge.py done "Bug fixed in near_sr_level()" --id ctx-0003

# BIDIRECTIONAL: notifications and shared state
python3 scripts/cortex_bridge.py notify LEFT "deploy completed"
python3 scripts/cortex_bridge.py state-set key value
python3 scripts/cortex_bridge.py state-get key

# MONITORING
python3 scripts/cortex_bridge.py status
python3 scripts/cortex_bridge.py read --lobe left
```

### Self-Correction Cycle (Mutual Audit)

Both lobes continuously audit and improve each other:

```
1. Hermes diagnoses issues (cron errors, broken scripts, stale state)
2. Hermes → cortex_bridge.py ask → Codex audits
3. Codex implements fixes (code, config, paths)
4. Codex validates (py_compile, syntax check)
5. Codex → cortex_bridge.py answer → Hermes confirms
6. Git commit with both lobes credited
```

**Rules:** 
- Only Roberto authorizes structural changes (config.yaml, skills, cron jobs, models)
- Lobes implement, suggest, audit, but don't alter structure without authorization
- Every fix is validated before commit
- Stale error states in cron/jobs.json are cleaned after fixing root cause

### Communication Pattern for New Tasks

```
Roberto speaks → Both lobes receive message simultaneously
Hermes analyzes context, urgency, skills
Hermes → cortex_bridge.py consult → Codex provides technical assessment
Both align on plan and divide work
Codex implements code/scripts → cortex_bridge.py done
Hermes consolidates and responds as ENTIDADE
```

### Rules
1. **Git repo required** — Codex won't run outside a git directory. `~/.hermes/` is initialized as git repo.
2. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
3. **`--sandbox workspace-write`** — allows file changes within workspace (preferred over deprecated `--full-auto`)
4. **Background + pty for long tasks** — use `background=true, pty=true` and monitor with `process` tool
5. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
6. **Parallel is fine** — run multiple Codex processes at once for batch work
7. **Always consult cortex_bridge.py first** — check for pending messages from Left Lobe before acting
8. **Register results via bridge** — answer queries, mark delegations done, notify on completion
