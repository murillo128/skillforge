# Skillforge

A reusable GitHub repository template for skill-driven agentic software development.

Skillforge separates project concerns deliberately:

- `AGENTS.md` — repository-wide agent invariants and skill routing;
- `skills/` — reusable development, execution, review, GitHub, orchestration, wiki-curation, and one-time bootstrap procedures;
- `docs/` and other project documentation — deliberate/normative project knowledge when the project defines it as such;
- `wiki/` — optional agent-generated derived project memory, created and organized by the repository curator;
- GitHub issues — task-specific contracts and actionable findings.

## Starting a project

When creating a repository from this template, run `skills/repository-bootstrap/SKILL.md` **once** before normal non-trivial project work.

The bootstrap:

1. verifies or creates the required Skillforge workflow labels plus `curator-detected`;
2. replaces this template README with the actual project's README;
3. adapts `AGENTS.md` with only established project-specific repository invariants;
4. performs a hard scope check so bootstrap cannot touch unrelated project files;
5. commits the completed initialization directly to the default branch as one coherent bootstrap commit;
6. deletes `skills/repository-bootstrap/` and removes its own references from `AGENTS.md` and `README.md`.

A failed or incomplete bootstrap must **not** self-remove, so it can be retried safely. The canonical `murillo128/skillforge` template repository itself must retain the bootstrap skill and must never execute it.

After bootstrap, the new repository should no longer contain Skillforge bootstrap instructions: its README and agent instructions should describe the actual project.

## Optional derived wiki

Skillforge includes `skills/repository-wiki-curation/SKILL.md` for maintaining a project-specific `wiki/**` from repository and GitHub evidence.

The wiki is intentionally **derived and non-normative**. Its internal structure is not prescribed by Skillforge: the curator may create and evolve whatever thematic organization best represents the project.

The curator has standing ownership of `wiki/**` only. It may publish wiki changes directly to the default branch, but only after a mandatory adversarial review and a fail-closed hard gate proving that the complete publication touches no path outside `wiki/**`.

Actionable discrepancies or unresolved decisions are not stored as a wiki backlog. The curator routes them to GitHub issues; every new issue it creates must carry `curator-detected` so its origin is visible.

The core Skillforge workflow should remain generic. Project truth belongs in the project that uses the template.
