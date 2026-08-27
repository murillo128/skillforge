# Skillforge

A reusable GitHub repository template for skill-driven agentic software development.

Skillforge separates project concerns deliberately:

- `AGENTS.md` — repository-wide agent invariants and skill routing;
- `skills/` — reusable development, execution, review, GitHub, orchestration, and wiki-curation procedures;
- `docs/` and other project documentation — deliberate/normative project knowledge when the project defines it as such;
- `wiki/` — optional agent-generated derived project memory, created and organized by the repository curator;
- GitHub issues — task-specific contracts and actionable findings.

## Starting a project

When creating a repository from this template:

1. **Replace or rewrite this `README.md`** so it describes the new project's actual mission, scope, architecture, setup, and user-facing documentation. Do not leave the Skillforge template README as the project's README.
2. Adapt the `Project-specific additions` section of `AGENTS.md` with only the repository-wide invariants the new project genuinely needs.
3. Add project-specific or domain-specific skills only when a procedure is genuinely reusable; keep task-specific instructions in controlling GitHub issues.
4. If enabling periodic repository wiki curation, ensure the GitHub label `curator-detected` exists and configure a separate scheduled curator task for that repository.

## Optional derived wiki

Skillforge includes `skills/repository-wiki-curation/SKILL.md` for maintaining a project-specific `wiki/**` from repository and GitHub evidence.

The wiki is intentionally **derived and non-normative**. Its internal structure is not prescribed by Skillforge: the curator may create and evolve whatever thematic organization best represents the project.

The curator has standing ownership of `wiki/**` only. It may publish wiki changes directly to the default branch, but only after a mandatory adversarial review and a fail-closed hard gate proving that the complete publication touches no path outside `wiki/**`.

Actionable discrepancies or unresolved decisions are not stored as a wiki backlog. The curator routes them to GitHub issues; every new issue it creates must carry `curator-detected` so its origin is visible.

The core Skillforge workflow should remain generic. Project truth belongs in the project that uses the template.
