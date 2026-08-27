# Skillforge

A reusable GitHub repository template for skill-driven agentic software development.

Skillforge separates three kinds of project knowledge:

- `AGENTS.md` — repository-wide agent invariants and skill routing;
- `skills/` — reusable development, execution, review, GitHub, and orchestration procedures;
- GitHub issues and project documentation — task-specific contracts and durable project knowledge.

## Starting a project

When creating a repository from this template:

1. **Replace or rewrite this `README.md`** so it describes the new project's actual mission, scope, architecture, setup, and user-facing documentation. Do not leave the Skillforge template README as the project's README.
2. Adapt the `Project-specific additions` section of `AGENTS.md` with only the repository-wide invariants the new project genuinely needs.
3. Add project-specific or domain-specific skills only when a procedure is genuinely reusable; keep task-specific instructions in controlling GitHub issues.

The core Skillforge workflow should remain generic. Project truth belongs in the project that uses the template.