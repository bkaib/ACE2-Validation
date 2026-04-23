---
name: design-agent-system
description: Design and scaffold an agent-based system for any project. Use when asked to "build an agent system", "create agents for my project", "design a multi-agent pipeline", "suggest agents for my workflow", or "set up GitHub Copilot agents". Guides the user through scoping agents, defining their roles and skills, selecting which to build, and producing a concrete implementation to-do list. Keywords: agent, multi-agent, agent system, pipeline, copilot agent, agent design, agent workflow.
---

# design-agent-system

Guide the user through designing and implementing a tailored agent-based system for their project. The skill is project-agnostic: it reads the repository context, proposes a minimal set of agents (≤ 3), defines their roles and skills, and produces an actionable implementation plan.

## When to Use This Skill

- "Let's build an agent system for this project."
- "Create agents for my workflow."
- "Suggest GitHub Copilot agents for my pipeline."
- "Design a multi-agent setup for this repo."
- "What agents do I need for this project?"

## Step-by-Step Workflow

### Step 1 — Understand the project

Read the project README and any high-level documentation (e.g. `milestones/`, `docs/`, `copilot-instructions.md`) to extract:

- **Goal**: What is the project trying to achieve?
- **Domain**: What kind of work does it involve (e.g. data engineering, ML, web dev, scientific analysis)?
- **Pipeline stages**: What distinct phases of work exist (e.g. ingestion → cleaning → analysis → reporting)?
- **Constraints**: Platform, tools, languages, and existing conventions.

If no README exists, ask the user to describe the project goal in 2–3 sentences before continuing.

### Step 2 — Identify the work stages

From the project context, map the full pipeline into **logical work stages**. Examples by domain:

| Domain | Typical stages |
|--------|---------------|
| Data science / analysis | Ingest → Clean/preprocess → Analyse → Visualise/report |
| ML / AI | Data prep → Feature engineering → Train → Evaluate → Deploy |
| Web application | Design → Frontend → Backend → Test → Deploy |
| Scientific research | Literature → Data collection → Processing → Statistics → Write-up |
| DevOps / platform | Provision → Configure → Deploy → Monitor → Incident response |

Do not force a template — derive stages from the actual project.

### Step 3 — Propose ≤ 3 agents

Group the stages into at most **3 coherent agents**. Each agent should:

- Own a distinct, non-overlapping slice of the pipeline.
- Be useful on its own, even if the others are not created.
- Have a clear, one-sentence purpose.

For each proposed agent, present:

```
## Agent N: <Name>

**Role**: <One-sentence description of what this agent does in the pipeline.>

**Owns these pipeline stages**: <Stage A>, <Stage B>

**Suggested skills**:
- <Skill 1>: <Why it's needed>
- <Skill 2>: <Why it's needed>
- ...

**Example prompts a user would give this agent**:
- "<example prompt 1>"
- "<example prompt 2>"
```

Keep descriptions concrete and tied to the actual project.

DO: propose to use more agents if three is not enough to cover the distinct stages of work.

### Step 4 — Ask the user which agents to create

After presenting the proposals, ask:

> "Which of these agents would you like to create? You can choose one, several, or all. If you'd like to adjust a name, role, or skill list before we proceed, let me know."

Wait for the user's selection before continuing.

### Step 5 — Produce an implementation to-do list

For each selected agent, generate a numbered, actionable to-do list. Tailor the steps to the project's conventions (directory layout, existing skill files, `.github/agents/` structure). A generic template:

```
### Agent: <Name>

- [ ] 1. Create `.github/agents/<agent-name>.md` with frontmatter (`name`, `description`, `tools`, `model`).
- [ ] 2. Write the agent body: define its goal, constraints, and workflow.
- [ ] 3. For each required skill:
         a. Create `.github/skills/<skill-name>/SKILL.md`.
         b. Add supporting `scripts/`, `references/`, or `templates/` as needed.
- [ ] 4. Register the agent in `.github/copilot-instructions.md` (if project-wide awareness is needed).
- [ ] 5. Test the agent with the example prompts from Step 3.
- [ ] 6. Iterate: refine agent instructions based on test results.
```

Add project-specific steps where relevant (e.g. installing packages, configuring tool permissions, adding MCP servers).

### Step 6 — Save the Suggested Agents and To-dos

Save your suggestions in a `.github/plans/agent-system.md` file for the user to reference as they implement the agents.


## Key Principles

- **Minimal footprint**: Propose only agents the project genuinely needs. Fewer, focused agents outperform many vague ones.
- **Non-overlapping roles**: Each agent should own a slice of work that the others do not touch.
- **Skills over monoliths**: Prefer composing agents from reusable skills rather than embedding all logic in the agent file itself.
- **Progressive disclosure**: Reveal the to-do list only after the user has chosen which agents to create.
- **Project-first**: All agent names, skills, and descriptions must reference the actual project domain and tools — never use generic placeholders.

## Output Artifacts

- Agent proposals (Markdown, presented inline in chat).
- `.github/agents/<agent-name>.md` files for each selected agent.
- `.github/skills/<skill-name>/SKILL.md` files for each new skill.
- Optional: updated `.github/copilot-instructions.md` if cross-agent coordination is needed.

## References

- See `.github/instructions/agent.instructions.md` for the agent file format and required frontmatter fields.
- See `.github/instructions/agent-skills.instructions.md` for the skill file format and bundling conventions.
- See `.github/skills/create-readme/SKILL.md` for a worked example of a well-formed skill.
