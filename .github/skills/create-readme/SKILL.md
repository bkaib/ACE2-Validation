---
name: create-readme
description: "Create a README.md file for the project. Use when asked to generate or update a project's README, produce README templates, or enforce repository README conventions. Keywords: README, readme, documentation, project overview, README template."
---

# create-readme 

The goal is to create a concise, well-structured, easy to understand README.md file for the project. This involves reviewing the entire project and workspace.

## When to Use This Skill

- Requests to "generate a README" or "create project README".
- Update or improve an existing `README.md` to match repo conventions.
- Create a concise project overview, quick start, and provenance section.
- Produce a README template or example to copy into the repo.

## Prerequisites

- Access to the repository files (so the agent can inspect project layout).
- If available, project metadata (author, license, primary entrypoint, data sources).

## Conventions and Templates

- Repository-level README conventions live in `.github/instructions/readme.instructions.md` — follow those rules when producing output.
- Place reusable README templates in `templates/README_template.md` inside this skill (optional).

## Step-by-step Workflow

1. Review repository structure and key files (e.g., `scripts/`, `config/`, `notebooks/`, `data/`, `README.md` if present).
2. Extract metadata: project name, short description, license (link to `LICENSE` file), quick start commands, dependencies, and provenance (data sources, commit SHA).
3. Choose sections based on repository type (library, scripts, data analysis): minimal recommended sections are Project Summary, Quick Start, Installation, Usage, Data, Results, Contact/Authors.
4. Fill the README template and generate a concise first draft (≤ 500 words for summary, keep sections scannable).
5. Present the draft to the user and offer variants (short, detailed, badge-inclusive).

## Example Prompts

- "Create a README.md for this repo focusing on usage and quick start."
- "Update the README to include provenance metadata and example commands." 

## Output Artifacts

- `README.md` draft (Markdown) — primary deliverable.
- Optional `README_template.md` (starter template) saved under `templates/` for reuse.

## References

- See `.github/instructions/readme.instructions.md` for repo-specific rules and required sections.
