---
description: 'Guidelines for creating custom agents (agent.md / .agent files) for this repository. Based on https://awesome-copilot.github.com/learning-hub/building-custom-agents/'
applyTo: '.github/agents/**'
---

# Custom Agent Instruction Guidelines

This file describes repository-specific guidelines for authoring custom agents and their instruction files (here called "agent files"). It follows the general conventions in [.github/instructions/instructions.instructions.md] and adapts recommendations from the Copilot Learning Hub: Building Custom Agents.

## Purpose

- Help contributors create clear, portable, and secure custom agents.
- Ensure agents are discoverable and safe to run in this project.

## Required Frontmatter

All agent files must include YAML frontmatter with at least:

```yaml
---
name: 'agent-name'
description: 'Brief but precise description of the agent’s capabilities and triggers. You can use a list of keywords and example user prompts to clarify when to use this agent.'
model: The GPT Model to use for the task (e.g., gpt-4, gpt-3.5-turbo)
tools: A list of allowed tool identifiers (e.g., ['readFile', 'runInTerminal'])
---
```

- `name`: lowercase, hyphens, ≤ 64 chars.
- `description`: clear capabilities and triggers (this is used for discovery).
- `keywords`: comma-separated list of relevant keywords for discovery.
- `model`: the GPT model to use for the task (e.g., gpt-4, gpt-3.5-turbo).
- `tools`: list of allowed tool identifiers (keep the list minimal and explicit).

## Body Structure

Recommended sections inside an agent instruction file:

- `# Title` — short human-readable title.
- `## Overview` — a 1–3 sentence summary of intent and scope of the agent
- `## Role and Expertise of the Agent` — a brief description of the agent's persona. **Note: define the representative emoji for this agent's headers here.**
- `## When to Use This Agent` — explicit triggers and example user requests.
- `## Workflow` — step-by-step behavior the agent should follow. **Note: instruct the agent to use checkboxes for multi-step tracking.**
- `## Safety & Limits` — allowed/forbidden actions, data handling rules.
- `## Outputs` — expected artifacts the agent will produce.
- `## References` — links to scripts, templates, or external docs.

## Output Formatting Standards

All agents defined in this repository must adhere to the **Readable Interaction Format** defined in [.github/copilot-instructions.md]:
1. **Contextual Emojis**: Use exactly one emoji in H1 and H2 headers related to the agent's domain.
2. **Task Tracking**: Use markdown checkboxes (`- [ ]`, `- [x]`) for all plans and progress logs.
3. **Conciseness**: Prioritize scannability over length.

## Discovery and Keywords

The `description` and first heading are used for automatic discovery. Include likely user keywords and short example prompts, e.g.: "Use when asked: 'debug failing tests', 'diagnose build error'".

## Tools and Permissions

- Explicitly enumerate only the tools the agent needs (e.g., `runInTerminal`, `readFile`, `git`, `fetch`).
- Do not include network or credentials-capable tools unless necessary; document any network calls in `Prerequisites`.
- Warn and require explicit confirmation for destructive actions (branch deletion, force-push, file deletion).

## Security and Privacy

- Agents must never exfiltrate secrets; do not embed credentials in agent files or scripts.
- If an agent needs to access secrets (tokens, API keys), document how the caller supplies them (env vars, credential helpers) and require explicit user consent.
- Limit file-system scopes in the agent description (e.g., only `scripts/` and `.github/` folders) when possible.

## Testing and Validation

- Include a short checklist for validating agent behavior (example test commands, expected outputs).
- Prefer including small, deterministic helper scripts under `scripts/` in the agent folder and reference them in the agent file.

## Examples

Minimal frontmatter + outline:

```markdown
---
name: debug-mode
description: "Systematically reproduce and fix failing tests. Use when tests fail or CI reports errors."
keywords: "debug, tests, CI, errors"  
model: gpt-4
tools: ['read/problems','execute/runTests','edit/editFiles','execute/runInTerminal']
---

# Debug Mode

## Overview
Reproduce failing tests, collect logs, propose minimal fixes, and run verification tests.

## Role and Expertise of the Agent
You're a senior software engineer with expertise in debugging complex test failures. You systematically analyze test outputs and propose minimal, targeted fixes to resolve issues while preserving existing functionality. You prioritize reproducibility and clarity in your debugging process.

## When to use this agent
- "My tests fail on CI"
- "Help debug failing unit tests"

## Workflow
1. Run failing tests and capture output.
2. Search for usage of failing symbols.
3. Propose a minimal patch and run tests again.

## Safety & Limits
- Only modify files under `src/` and `tests/`.
- Do not access secrets or make network calls.
- Always ask for user confirmation before making changes.

## Outputs
- A concise report of test failures and proposed fixes. 
- A patch file with the proposed code changes.

## References
- See `scripts/debug-helper.sh` for a helper script to run tests and capture output.

```

## Where to store agent resources

- Mandatory: Create the agent in `.github/agents/<agent-name>.agent.md`.
- (Optional): Use `./.github/agents/<agent-name>/references/` for long-form docs.
- (Optional): Use `./.github/agents/<agent-name>/scripts/` for helper scripts; mark scripts executable and include `--help` output.

## Maintenance

- Keep agent `description` and `tools` up to date with actual behavior.
- Periodically review agents for stale privileges or unfollowed references.

## References

- Building custom agents: https://awesome-copilot.github.com/learning-hub/building-custom-agents/

