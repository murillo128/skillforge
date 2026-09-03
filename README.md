# Skillforge

A reusable GitHub repository template for skill-driven agentic software development.

Skillforge separates project concerns deliberately:

- `AGENTS.md` — repository-wide agent invariants and skill routing;
- `skills/` — reusable development, execution, review, GitHub, orchestration, local-runner, wiki-curation, and one-time bootstrap procedures;
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
6. deletes `skills/repository-bootstrap/` and removes its own references from `AGENTS.md` and `README.md`;
7. if explicitly requested, hands off after successful repository bootstrap to `skills/codex-local-runner/SKILL.md` to configure a local self-hosted Codex runner.

Local runner setup is **opt-in** and is not required for a valid repository bootstrap. A failed or incomplete repository bootstrap must **not** self-remove, so it can be retried safely. The canonical `murillo128/skillforge` template repository itself must retain the bootstrap skill and must never execute either its bootstrap or local-runner provisioning against itself.

After bootstrap, the new repository should no longer contain Skillforge bootstrap instructions: its README and agent instructions should describe the actual project.

## Optional local Codex executor

Skillforge includes `.github/workflows/codex-execute-ready.yml` plus `skills/codex-local-runner/SKILL.md`.

The workflow listens for GitHub issue label changes and makes its local execution job eligible only when the newly applied label is exactly `execution-ready`. It targets a repository self-hosted runner labeled `codex`, checks out the repository, and launches Codex with the controlling issue number. The normal `AGENTS.md` and issue-driven Skillforge workflow remain authoritative.

The workflow can be inherited by every repository created from the template without requiring local infrastructure. Without a matching self-hosted runner, it cannot execute code on a local machine. Runner installation is deliberately separate and must be explicitly requested during bootstrap or invoked later through `codex-local-runner`.

The runner skill installs or repairs the official GitHub Actions runner on the target machine, registers it to the exact repository, preserves the existing local Codex authentication, installs it as a persistent service, and verifies that GitHub sees it online with the expected labels. It does not create OpenAI API keys, expose inbound ports, or trigger a dummy issue as a test.

## Optional derived wiki

Skillforge includes `skills/repository-wiki-curation/SKILL.md` for maintaining a project-specific `wiki/**` from repository and GitHub evidence.

The wiki is intentionally **derived and non-normative**. Its internal structure is not prescribed by Skillforge: the curator may create and evolve whatever thematic organization best represents the project.

The curator has standing ownership of `wiki/**` only. It may publish wiki changes directly to the default branch, but only after a mandatory adversarial review and a fail-closed hard gate proving that the complete publication touches no path outside `wiki/**`.

Actionable discrepancies or unresolved decisions are not stored as a wiki backlog. The curator routes them to GitHub issues; every new issue it creates must carry `curator-detected` so its origin is visible.

The core Skillforge workflow should remain generic. Project truth belongs in the project that uses the template.
