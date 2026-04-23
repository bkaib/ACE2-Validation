---
name: generate-code
description: "Generate precise, file-targeted code from a plan. Use when asked to 'generate code for a plan', 'write the implementation code', 'produce code from the plan', 'codegen for step N', or 'create implementation markdown'. Reads a .github/plans/<name>.plan.md, generates code for each step with exact file paths and edit instructions, and saves to .github/implementation/<name>.implementation.md. Keywords: codegen, generate code, implementation, plan to code, edit instructions, diffs."
---

# Generate Code Skill

Read a plan from `.github/plans/<plan-name>.plan.md` and generate complete, tested code for each step. Output is saved to `.github/implementation/<plan-name>.implementation.md` with exact file paths, line references, and checkboxed tasks ready for the implementation agent.

## When to Use This Skill

- "Generate code for the plan `<plan-name>`."
- "Write implementation code for step 3 of the plan."
- "Produce the implementation markdown from the plan."
- "Codegen for `feature/data-pipeline-agent`."
- "Create the implementation file from the plan."

## Prerequisites

- A completed plan file at `.github/plans/<plan-name>.plan.md`.
- Access to the full repository to read existing code, imports, and conventions.
- Web access for checking library APIs, type signatures, and examples when generating code that uses external packages.
- Use model: Claude Opus 4.6 for the coding to leverage its strong code generation and understanding of context.

## Step-by-Step Workflow

### Step 1 — Load and Parse the Plan

1. Read `.github/plans/<plan-name>.plan.md`.
2. Extract the ordered list of steps and their checkbox items.
3. Identify the branch strategy and note the base branch.
4. Read all files listed in the plan's **Files touched** sections to understand current state.

### Step 2 — For Each Step, Generate Code

Process steps **in order**. For each step:

#### 2a — Gather Context

- Read the files that this step will create or modify.
- Read related files (imports, config, tests) to understand interfaces.
- If the step uses an external library, look up the API to ensure correctness.
- Review `config/paths.py` for any path constants needed.

#### 2b — Generate Edit Instructions

For each checkbox item in the step, produce one of:

**For new files** — full file content:

````markdown
**Create file**: `path/to/new_file.py`

```python
# Full file content here
```
````

**For modifications to existing files** — targeted edits with context:

````markdown
**Edit file**: `path/to/existing_file.py`

Replace lines N–M:
```python
# old code (for reference)
```
With:
```python
# new code
```
````

**For deletions**:

````markdown
**Delete file**: `path/to/obsolete_file.py`
````

#### 2c — Generate Verification Code

For each step, produce the exact command(s) to verify correctness:

````markdown
**Verification**:
```bash
# Run this to verify step N
python -m pytest tests/test_module.py -v
# or
python scripts/preprocessing/some_script.py --help
```
Expected: <describe expected output>
````

### Step 3 — Assemble the Implementation File

Write `.github/implementation/<plan-name>.implementation.md` with this structure:

````markdown
# Implementation: <plan-name>

**Source plan**: `.github/plans/<plan-name>.plan.md`
**Generated**: <date>
**Branch**: `feature/<plan-name>`

---

## Step N — <Short Title>

> <Brief description from the plan>

### N.1 — <Task description>

- [ ] **Implementation**

**<Create|Edit|Delete> file**: `exact/path/to/file.py`

```python
# Complete code or edit instructions
```

### N.2 — <Task description>

- [ ] **Implementation**

**Edit file**: `exact/path/to/other_file.py`

Replace lines 15–22:
```python
# old code
```
With:
```python
# new code
```

### Step N — Verification

- [ ] **Run verification**

```bash
verification command
```

Expected: <expected output>

---
````

### Step 4 — Cross-Check Quality

Before saving, verify:

1. **Every checkbox from the plan has a corresponding implementation section.**
2. **Every file path is exact and relative to the project root.**
3. **Every edit references the current file content** (not stale or assumed content).
4. **Imports are complete** — no missing imports in generated code.
5. **Code follows project conventions**: `snake_case`, `black` formatting, `isort` order, type hints where helpful.
6. **`config.paths` is used** for all data paths — no hardcoded absolute paths.
7. **Logging uses `config.custom_logging`** — no bare `print()` statements.
8. **New dependencies are noted** at the top of the implementation file.

### Step 5 — Present Summary to User

After saving the file, present a brief summary:

```
Implementation file saved to .github/implementation/<plan-name>.implementation.md

Steps generated: N
Total tasks: M checkboxes
New dependencies: <list or "none">
Files created: <count>
Files modified: <count>

Ready for the implementation agent (@implementation).
```

## Handling Large Plans

If a plan has more than 5 steps:

1. Generate code for **all steps** in one pass to ensure cross-step consistency.
2. Use a **summary header** at the top of the implementation file listing all steps and their status.
3. Each step section should be **self-contained** — include enough context that the implementation agent can process it without reading earlier steps.

## Output Artifacts

- `.github/implementation/<plan-name>.implementation.md` — the primary deliverable.

## References

- Upstream input: `.github/skills/planning/SKILL.md`
- Downstream consumer: `.github/agents/implementation.agent.md`
- Project conventions: `.github/copilot-instructions.md`
- Path helper: `config/paths.py`
- Logging: `config/custom_logging.py`
