---
description: 'Format rules and conventions for all TODO files in .github/todos/. Applies to agents and the user when reading or writing TODO entries.'
applyTo: '.github/todos/**'
---

# TODO Conventions

All TODO files in `.github/todos/` follow a shared format. Agents read and write these files to coordinate work across sessions.

## Files

| File | Purpose |
|------|---------|
| `global.todos.md` | High-level milestone status board — one row per milestone. |
| `data-engineer.todo.md` | Tasks owned by the data-engineer agent. |
| `impact-modeler.todo.md` | Tasks owned by the impact-modeler agent. |
| `analyst.todo.md` | Tasks owned by the analyst agent. |

## Priority Levels

| Label | Meaning |
|-------|---------|
| `[HIGH]` | Blocks milestone progress or a downstream agent — do this first. |
| `[MED]` | Advances the milestone but is not an immediate blocker. |
| `[LOW]` | Nice-to-have, cleanup, or exploratory task. |

## Agent-Specific TODO Format

```
# {Agent Name} TODOs

## Active
- [ ] **[HIGH]** {Task description} — milestone: {folder-name} — depends on: none | {other task ref} — added: YYYY-MM-DD

## Backlog
- [ ] **[LOW]** {Task description} — milestone: {folder-name} — added: YYYY-MM-DD

## Completed
- [x] ~~{Task description}~~ — completed: YYYY-MM-DD — commit: {40-char SHA}
```

### Rules

- One line per task.
- `Active` = tasks to work on now (HIGH or MED priority, unblocked).
- `Backlog` = LOW priority or blocked tasks.
- When a task is completed: move from Active/Backlog to `Completed`, strike through the text with `~~`, fill in the `completed` date and the commit SHA. Do **not** delete completed entries.
- When adding a new task: append to `Active` (HIGH/MED) or `Backlog` (LOW) with today's date.
- If a task creates output for another agent, add a corresponding task to that agent's TODO file with `depends on: {this task description}`.

## Global Milestone Status Format

```
# Milestones of the Project

| Milestone | Status | Owner Agent(s) | Description |
|-----------|--------|----------------|-------------|
| {folder-name} | 🔴 Not started | agent1, agent2 | One-sentence description. |
```

### Status Values

- 🔴 Not started — no work begun
- 🟡 In progress — at least one Processing Log entry exists in the milestone .md
- 🟢 Complete — all sub-tasks done, Methodology Draft is finalized
- ⏸ Blocked — waiting on an upstream dependency

### Rules

- Update the milestone row status whenever a milestone's progress changes.
- Do not add per-task rows to `global.todos.md` — keep it at the milestone level only.
