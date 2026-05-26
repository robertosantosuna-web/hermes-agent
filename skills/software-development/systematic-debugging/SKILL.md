---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**
- **"Let me try the same tool again" (when it already failed 2+ times without diagnosing why)**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

### Special: Repeated Tool Failure

When a tool fails more than once on the same operation:

1. **FIRST failure:** Note the error. Try once more with adjusted parameters.
2. **SECOND failure:** STOP using that tool. Diagnose: is the tool available? Are preconditions met? Is there an environmental issue?
3. **THIRD attempt with same tool:** NEVER. Switch to a different approach entirely.

**Example:** If `curl localhost:9222/json` fails twice, do NOT try a third CDP call. Diagnose: is Edge running? Is CDP flag set? If no → use desktop-control or ask user.

**Real session anti-pattern (2026-05-22):** Repeated 4+ failed CDP/browser-tool attempts on 99Freelas without diagnosing why (Edge not running, Cloudflare Turnstile, wrong env vars). The same `browser_navigate` was called twice after first failure (code 101), and CDP was attempted 3+ times without verifying Edge was actually running with `--remote-debugging-port`. The user called this out: "Você nao esta mapeando as falhas e continua repetindo erros." After stopping and diagnosing: (1) Edge wasn't running, (2) Wayland env vars (DISPLAY, XAUTHORITY, WAYLAND_DISPLAY, XDG_RUNTIME_DIR) were missing, (3) Cloudflare blocks fresh Edge instances without user cookies. The fix was checking preconditions FIRST before each tool attempt.

**Concrete checklist before EACH browser/CDP call:**
1. Is the browser running? `pgrep -a "chrome|brave|msedge"`
2. Which CDP port is active? `curl -s --max-time 2 http://localhost:9222/json` AND `curl -s --max-time 2 http://localhost:9223/json` — ports can differ from config
3. Are Wayland env vars set? `echo $DISPLAY $XAUTHORITY $WAYLAND_DISPLAY`
4. Does the target page have Cloudflare? (check for `challenges.cloudflare.com` in CDP page list)
If any check fails → use desktop-control daemon OR ask user, do NOT retry the same tool.

**CDP port mismatch:** The configured CDP port (e.g. 9223) may differ from the actual browser debug port (e.g. 9222). Check ALL common ports. When `browser_cdp` fails, manually list pages on each port via `curl localhost:9222/json` and `curl localhost:9223/json` to find and use the correct one via terminal scripts.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |
| "Let me deploy and test" (without verifying locally) | Deploying without confirming the fix works locally wastes 3-5 min per attempt. Test with CDP or curl BEFORE deploying. |
| "I fixed the symptom, let's see" (>2 deploys without root cause) | Each symptom-only deploy is a wasted cycle. After 2 symptom fixes, STOP and find root cause. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

### Session References

- `references/root-cause-examples-2026-05-22.md` — 99Freelas browser automation debugging
- `references/mindcoach-chat-debug-2026-05-25.md` — 21-deploy chat debugging, ES module silent failure, CDP via terminal, dual-channel redundancy

### Cron Timing Gap Pattern

When a cron job polls for messages and a message arrives between runs:
- **Symptom:** Message sent at 15:34:29, cron ran at 15:34:18 → 11s gap → 1min wait
- **Fix:** Sub-minute polling, OR push-based trigger (WebSocket → auto-responder), OR dual-channel where at least one channel responds instantly
- **Pattern:** Always pair polling systems with a push fallback. Long-poll ≠ real-time.

### Dual-Channel Redundancy Pattern

For multi-component web apps with unreliable connections (mobile, tunnels):
- Send messages via ALL available channels simultaneously (WebSocket + REST API)
- Respond via ALL channels (WebSocket broadcast + REST API POST)
- Frontend uses fastest response, ignores duplicates
- This eliminates single-point-of-failure debugging — if one channel works, user sees response

## Real-World Impact

**Trigger:** User frustration signals ("não fica repetindo erros", "mapeia tudo que faz", "antes de gastar token à toa"), OR you've attempted 2+ fixes without success, OR the system has 3+ layers.

**BEFORE Phase 1, create a structured audit map:**

1. List every component boundary in the system (CDN → SW → nginx → API → bridge → agent)
2. For each component, record: what version is deployed? What does it expect? What does it produce?
3. Create a version timeline table showing what was deployed when and what broke
4. Only after the map is complete, proceed to Phase 1

**Format:** Markdown document with a timeline table and component diagram. Save to project directory. This IS the investigation — not optional prep.

**Real session example (2026-05-25):** MindCoach chat was broken through 21 Cloud Run deploys. Root cause was a duplicate function declaration in an ES module that prevented the entire module from loading (silent failure — no console error visible without CDP). Without the map, each deploy fixed a different symptom while the real bug (present since v1) persisted. The map revealed: the response was always being sent and received by the bridge, but the frontend JS never executed. The fix took 5 minutes once the map identified the failing component.

### Multi-Component Web App Checklist

When debugging a web app with Cloud Run + nginx + Service Worker + ES modules + WebSocket:

1. **Check Service Worker interference:** `performance.getEntriesByType('resource').filter(r => r.name.includes('main.js')).map(r => r.transferSize)` — if 0, SW is serving cached empty response
2. **Unregister SW and clear caches before retesting:** `navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister())); caches.keys().then(keys => keys.forEach(k => caches.delete(k)))`
3. **Check ES module load:** Use dynamic import in try-catch via CDP — `import('/core/main.js')` — to reveal syntax errors that prevent module execution
4. **Verify module exports exist:** `typeof window.exportedFunction` after module should load
5. **Check each import chain link:** Verify every imported file returns HTTP 200 and valid JS
6. **CDP debugging when browser tools unavailable:** Use Python + `websockets` library to connect to CDP port directly and call `Runtime.evaluate`

### Silent ES Module Failures

ES modules fail SILENTLY when they have syntax errors. The browser does NOT log to console in many cases. Symptoms:
- Module exports are all `undefined`
- No console errors visible
- The `<script type="module">` tag exists but nothing executes

**Detection:** Use CDP `Runtime.evaluate` with dynamic import:
```javascript
import('/path/to/module.js').then(m => console.log('OK', Object.keys(m))).catch(e => console.error('FAIL', e.message))
```

**Common causes:** Duplicate function declarations, missing exports from imported modules, circular imports.

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common
- **Worst case observed:** 21 deploys to fix a JS syntax error present since v1. Systematic CDP debugging found it in 5 minutes.

**No shortcuts. No guessing. Systematic always wins.**
