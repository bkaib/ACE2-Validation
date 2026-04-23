---
description: 'Session-start briefing protocol for all agents. At the beginning of every work session, agents scan the TODO files and present a prioritized task summary before doing any work.'
applyTo: '**'
---

# Session-Start Briefing Protocol

If the user asks for /briefing, briefing or summary of todos the agent should follow this protocol to scan the TODO files and present a concise briefing before starting work on any tasks.

## Step 1 — Identify the Active Agent

Determine which agent role is active: `data-engineer`, `impact-modeler`, or `analyst`.

## Step 2 — Scan TODO Files

Read the following files:
- `.github/todos/global.todos.md` — milestone status overview
- `.github/todos/{agent-name}.todo.md` — agent-specific active and backlog tasks

## Step 3 — Present the Briefing

Print a concise briefing in this format:

```
## Session Briefing — {Agent Name} — {YYYY-MM-DD}

**Milestone overview** (from global.todos.md):
- 🔴/🟡/🟢/⏸ {milestone name}: {status}
...

**Open tasks**:
- HIGH: {count}
- MED:  {count}
- LOW:  {count}

**Top 3 recommended tasks** (HIGH-first, then MED, skip blocked):
1. [{priority}] {task description} — milestone: {name}
2. [{priority}] {task description} — milestone: {name}
3. [{priority}] {task description} — milestone: {name}

**Blocked tasks** (dependencies not yet met):
- {task} — waiting on: {dependency}

**Recommended first action**: {single sentence describing what to do next and why}
```

## Step 4 — Confirm and Proceed

After presenting the briefing, ask the user: **"Shall I proceed with the top recommended task, or do you want to pick a different one?"**

Only start work after the user confirms (or after an explicit instruction to proceed is already given in the prompt).

## Notes

- If `.github/todos/{agent}.todo.md` has no Active tasks, say so and recommend pulling a task from Backlog.
- If `global.todos.md` shows a milestone as `⏸ Blocked`, flag it clearly — do not waste time on tasks that depend on it.
- Keep the briefing under 20 lines. Do not paste the full TODO file; summarize it.
