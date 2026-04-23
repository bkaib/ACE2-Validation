---
description: 'Repository conventions for README.md content, tone, and required metadata.'
applyTo: 'README.md'
---

# README Conventions

This file defines repository-specific rules for `README.md` so agents and contributors produce consistent, discoverable documentation.

## Required Sections (order recommended)

- Project title and one-line summary (first paragraph under the title).
- If you find a logo or icon for the project, use it in the readme's header.
- Short description (1–2 sentences) explaining purpose and scope.
- Quick Start: minimal commands to run or reproduce core functionality.
- Installation / Dependencies: how to install or create the environment.
- Usage Examples: one or two examples showing typical usage.
- Data / Inputs: list of important data sources and where to find them (do not include large data in repo).
- Outputs / Results: brief description of produced outputs or expected results.
- Provenance & Reproducibility: record key inputs, parameters, and the code commit SHA used to generate results.
- Authors / Contact: maintainers and contact email or issue link.

- DO NOT: Include sections like "LICENSE", "CONTRIBUTING", "CHANGELOG", etc. There are dedicated files for those sections.

Do NOT duplicate LICENSE, CONTRIBUTING, or CHANGELOG sections — link to those files instead.

## Resources

Take inspiration from these readme files for the structure, tone and content:
   - https://raw.githubusercontent.com/Azure-Samples/serverless-chat-langchainjs/refs/heads/main/README.md
   - https://raw.githubusercontent.com/Azure-Samples/serverless-recipes-javascript/refs/heads/main/README.md
   - https://raw.githubusercontent.com/sinedied/run-on-output/refs/heads/main/README.md
   - https://raw.githubusercontent.com/sinedied/smoke/refs/heads/main/README.md

## Tone and Style

**DOs:**
- DO: Keep the Readme concise and easy to read and understand. 
- DO: Keep sentences short (max 20–25 words when possible).
- DO: Use GFM (GitHub Flavored Markdown) for formatting, and GitHub admonition syntax (https://github.com/orgs/community/discussions/16925) where appropriate.

**DO NOTs:**
- DO NOT: use jargon or complex sentences.
- DO NOT: Overuse emojis



## Badges and Metadata

- Badges are optional; prefer a single CI badge and a package/release badge where relevant.
- Add a small metadata table (optional) listing Python version, core dependencies, and data provenance.

## Provenance Format (required for analysis/data work)

Include a short block listing:

```
Provenance:
- Data sources: <path or external URL>
- Processed with: <script or pipeline path>
- Commit: <git short SHA>
```

## Templates and Examples

Place templates under `.github/skills/create-readme/templates/README_template.md` or reference the skill `create-readme` for automated generation.

## Quick Checklist for PRs that modify README.md

- [ ] Title and one-line summary present
- [ ] Quick Start commands work (copy-paste)
- [ ] Provenance block present for analysis repos
- [ ] No duplicated license/CONTRIBUTING content

## Where to use the skill

- Use the `create-readme` skill when generating or updating READMEs to ensure these conventions are followed.
