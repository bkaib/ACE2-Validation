---
name: planning
description: "Create a modular, git-branch-aware plan from a user task. Use when asked to 'plan a task', 'create a plan', 'break this into steps', 'design a roadmap', or 'plan the implementation'. Produces a .github/plans/<plan-name>.plan.md with checkboxed steps, each mapped to one git commit. Keywords: plan, roadmap, steps, task breakdown, git branch, commit plan, modular, architecture."
---

# Planning Skill

Create a detailed, modular plan to achieve a user-defined task. Each step in the plan maps to exactly one git commit on a dedicated feature branch. The plan is saved as `.github/plans/<plan-name>.plan.md` and is designed to be consumed downstream by the `generate-code` skill and the `implementation` agent.

## When to Use This Skill

- "Plan how to implement feature X."
- "Break this task into steps."
- "Create a plan for adding bias correction."
- "Design a roadmap for the data pipeline."
- "Plan the refactoring of the preprocessing module."
- if "\planning" is mentioned in the chat.

## Prerequisites

- Access to the full repository (files, structure, dependencies).
- Web access for researching libraries, APIs, best practices, and domain-specific methods referenced in the task.
- Understanding of the project's conventions (see `.github/copilot-instructions.md`).
- Use model: Claude Opus 4.6 for the planning to leverage its strong reasoning and structured output capabilities.
- Use the copilot agent mode.

## Step-by-Step Workflow

### Step 1 — Understand the Task

1. Parse the user's prompt to extract the **goal**, **scope**, and **constraints**.
2. Read relevant project files: `config/paths.py`, `environment.yml`, existing scripts, and any referenced modules.
3. If the task references external libraries, APIs, or scientific methods, **search the web** for current documentation, best practices, and known pitfalls.
4. Identify which existing code and data paths are affected.

### Step 2 — Research and Context Gathering

1. Search the codebase for related implementations, utilities, and patterns.
2. Search the web for:
   - Best practices and reference implementations for the approach.
   - Library documentation for any new dependencies.
   - Relevant scientific literature or method descriptions (if applicable).
3. Identify risks, edge cases, and dependencies between sub-tasks.
4. Note any new dependencies that must be added to `environment.yml`.

### Step 3 — Decompose into Modular Steps

Break the task into **ordered, atomic, reproducible steps** where each step:

- Results in exactly **one git commit**.
- Is independently testable (unit test, script run, or manual verification).
- Has a clear, verifiable outcome.
- Does not exceed a reasonable scope for a single commit (prefer small, focused changes).

Group steps by logical phase (e.g., scaffold → core logic → integration → testing → documentation).

### Step 4 — Define Branch Strategy

Determine the branch structure:

```
Base branch: <current-branch>
Feature branch: feature/<plan-name>
  Step 1 → commit on feature/<plan-name>
  Step 2 → commit on feature/<plan-name>
  ...
```

For large plans with independent sub-features, propose child branches:

```
Feature parent: feature/<plan-name>
  Child: feature/<plan-name>/step-1-name
  Child: feature/<plan-name>/step-2-name
```

### Step 5 — Write the Plan File

Produce `.github/plans/<plan-name>.plan.md` with this structure:

```markdown
## Plan: <plan-name>

<One-paragraph summary of the goal and approach.>

### Branch Strategy

- Base branch: `<base>`
- Feature branch: `feature/<plan-name>`

---

### Step N — <Short Title>

<Brief description of what this step accomplishes and why.>

- [ ] N.1 <Specific, actionable task>
- [ ] N.2 <Specific, actionable task>
- [ ] N.3 ...

**Verification**: <How to confirm this step is complete — test command, expected output, or manual check.>

**Files touched**: <List of files created or modified.>

---
```

Each checkbox item must be concrete enough for the `generate-code` skill to produce exact file edits.

### Step 6 — Present and Iterate

1. Present the plan to the user in chat.
2. Ask for feedback: "Does this plan cover the scope? Should any step be split, merged, or reordered?"
3. Incorporate feedback and update the plan file.
4. Save the final version to `.github/plans/<plan-name>.plan.md`.

## Plan Quality Checklist

Before finalizing, verify:

- [ ] Every step has at least one checkbox todo.
- [ ] Every step has a **Verification** section.
- [ ] Every step has a **Files touched** section.
- [ ] Steps are ordered so each step can be committed and tested independently.
- [ ] No step depends on uncommitted work from a later step.
- [ ] New dependencies are noted (for `environment.yml`).
- [ ] The plan references exact file paths from `config.paths` (no hardcoded absolute paths).
- [ ] Web research findings are cited where relevant (library docs, methods).

## Output Artifacts

- `.github/plans/<plan-name>.plan.md` — the primary deliverable.

## References

- Project conventions: `.github/copilot-instructions.md`
- Path helper: `config/paths.py`
- Agent guidelines: `.github/instructions/agent.instructions.md`
- Downstream consumers: `.github/skills/generate-code/SKILL.md`, `.github/agents/implementation.agent.md`
