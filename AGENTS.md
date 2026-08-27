# AGENTS.md

Repository-wide instructions for ChatGPT, Codex, and other development agents.

## Mission and scope

The project's durable mission and product/domain scope belong in `README.md` and the repository documentation that explicitly owns them.

Agents must not broaden the project, invent adjacent goals, or promote exploratory discussion into settled scope without an explicit repository or issue-level decision.

This file owns repository-wide agent invariants and routes work to reusable skills. It should remain compact. Do not duplicate detailed procedures here when a skill already owns them.

## Load context progressively

For non-trivial work, start with:

1. `AGENTS.md`;
2. the controlling GitHub issue.

Then load only the context needed for the current role and task:

- exact accepted decision/specification/plan sections referenced by the issue;
- relevant source, tests, build files, configuration, fixtures, artifacts, and evidence;
- the one workflow skill that owns the current action;
- additional utility or domain skills only when the active action actually requires them.

Do not preload every repository document, every skill, complete issue/PR histories, or whole evidence/result directories.

On resume, verify branch, `HEAD`, worktree state, the controlling issue's current state label, and new material issue or PR discussion since the last handoff. Reuse already-inspected facts while their source identity remains unchanged instead of replaying history.

## Source-of-truth hierarchy

Unless project-specific documentation explicitly defines a stricter hierarchy, use this order:

1. Tests, formal checks, evaluation outputs, and captured evidence establish **observed behavior**.
2. Accepted specifications, decision records, architecture documents, and other explicitly normative repository documents establish **durable intended behavior** within their declared scope.
3. The controlling GitHub issue establishes the **bounded execution contract** for the active task.
4. Pull requests, checks, reviews, commits, and Git history preserve implementation and reproducible evidence.
5. Roadmaps, epics, and planning documents establish planning/dependency status only to the extent they explicitly claim authority.
6. Exploratory notes, research documents, drafts, and brainstorming preserve hypotheses and context but are not requirements unless explicitly adopted.
7. Chat discussion is provisional until intentionally recorded in an authoritative repository or GitHub source.

When authoritative sources materially conflict, do not silently choose one. Document or surface the conflict and return to the appropriate design/decision authority.

Do not promote an `OPEN`, `SPECULATIVE`, exploratory, or otherwise provisional statement into an implementation requirement without an explicit decision.

## Skill-driven workflow

Skills define reusable **procedure**, not project state or product truth. Issues define task-specific contracts. Repository documents define durable project knowledge. Keep those responsibilities separate.

Load skills lazily by role:

- design authority: `skills/design-github-issue/SKILL.md`;
- main executor: `skills/spec-driven-codex-loop/SKILL.md`;
- Git and GitHub mutation/publication: `skills/codex-github-operations/SKILL.md`;
- independent checkpoint/final technical review: `skills/codex-independent-review/SKILL.md`;
- multi-issue orchestration: `skills/codex-issue-orchestrator/SKILL.md`.

Do not read a role skill merely because it exists. The executor does not need the full design or reviewer procedure; the reviewer does not need the executor procedure; the orchestrator must preserve each child issue's normal execution contract rather than replacing it.

`AGENTS.md` owns repository-wide invariants and routing. Each skill owns its reusable procedure. The controlling issue owns task-specific scope, inputs, commands, gates, and acceptance criteria. Avoid copying the same rule into all three places.

## Workflow state

For non-trivial controlling issues, use exactly one current workflow-state label:

- `execution-ready`
- `in-progress`
- `design-required`
- `investigation-required`
- `blocked`
- `completed`

The label is authoritative for current workflow state. Issue-body readiness and historical comments do not override it.

Use state-only label transitions without adding comments whose sole purpose is to announce the transition. Preserve comments for material technical findings, contract amendments, checkpoint targets/verdicts, blockers, or handoffs.

`completed` is a post-acceptance/post-merge state. An implementation executor stops at a ready-for-review handoff and must not treat CI success or an independent technical `PASS` as merge authorization.

## Design and execution discipline

For non-trivial changes:

- design the controlling issue so a fresh executor can work without hidden chat reasoning;
- implement the smallest coherent outcome that satisfies the issue;
- preserve behavior outside scope;
- validate with repository-native checks appropriate to the risk;
- retain enough evidence to support the claims being made;
- use independent review at issue-declared material checkpoints;
- stop or return to design when evidence invalidates the contract or a material decision is missing.

Do not invent project-wide roadmaps, phases, schemas, frameworks, ontologies, or process machinery merely because they might be useful later. Introduce persistent structure only when the current task or an explicit project decision requires it.

Do not mechanically implement every reviewer suggestion. Review findings must be judged by the controlling contract, materiality, and repository invariants.

## Durable knowledge and documentation

Update durable repository documents only when the durable knowledge they own changes.

Examples:

- architecture/accepted technical choices -> the repository's decision or architecture documentation;
- stable subsystem responsibilities and boundaries -> the documentation that owns code structure/design;
- reusable development procedure -> the appropriate skill;
- task-local decisions, evidence, or blockers -> the controlling issue/PR/evidence artifact;
- roadmap/dependency status -> the repository's planning source, when one exists.

Do not edit durable docs merely to mirror GitHub workflow state, individual commits, or chronological session history.

When repeated successful work exposes a genuinely reusable procedure, prefer extracting or improving a skill instead of accumulating ad-hoc instructions across issues.

## Evidence and artifacts

Keep evidence proportional to the claim.

Commit source, tests, configuration, small deterministic fixtures, concise reports, and compact evidence that materially helps inspection or reproduction.

Large generated outputs, binaries, model weights, datasets, caches, traces, bulky logs, or other expensive artifacts should stay outside Git unless the project explicitly requires them and redistribution is permitted.

Never publish secrets, credentials, private data, or artifacts without the necessary rights.

Do not mix GitHub bookkeeping into technical evidence unless that metadata is itself a technical input to the system under test.

## Git and GitHub behavior

- Keep changes scoped; avoid unrelated cleanup or formatting.
- Use explicit paths when staging or publishing changes.
- Commit messages should describe one intentional outcome.
- Do not force-push or rewrite shared valid history without explicit user authorization.
- Direct commits to the default branch require explicit user instruction; otherwise use a feature branch and pull request.
- A Codex implementation workflow ends at a **ready-for-review** pull request and handoff.
- Executors and independent reviewers must not merge or enable auto-merge on their own authority.
- Merge requires a later explicit user-facing instruction after review finds no material blocker.

## Project-specific additions

Repositories created from this template should add only the domain-specific invariants that genuinely apply to that project, for example:

- language/runtime and coding constraints;
- ownership, lifetime, concurrency, or security invariants;
- required build/test/evaluation paths;
- external dependency or licensing constraints;
- hardware/runtime execution requirements;
- project-specific correctness or performance hard failures;
- explicit planning/epic authority when the project uses one.

Keep these additions declarative and repository-wide. Put reusable procedures in skills and task-specific detail in issues rather than growing this file into a second workflow manual.
