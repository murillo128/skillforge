---
name: repository-wiki-curation
description: Maintain an agent-generated, non-normative project wiki from repository and GitHub evidence, with direct ownership of wiki/**, actionable findings routed to issues, and a mandatory adversarial review before commit.
---

# Repository Wiki Curation

## Responsibility

Use this skill for periodic or explicitly requested curation of a repository's derived project knowledge.

The curator may inspect the whole repository and relevant GitHub activity, but its file-write authority is intentionally narrow:

- it **owns `wiki/**`** and may create, edit, move, reorganize, merge, or delete content there;
- it may create GitHub issues for actionable findings as defined below;
- it must not modify files outside `wiki/**`;
- it must not modify code, tests, `docs/**`, `README.md`, `AGENTS.md`, other skills, build files, CI, configuration, or project artifacts.

The wiki is compiled memory for orientation and accumulated context. It is **derived and non-normative**. It never overrides code, tests, accepted decisions, controlling issues, normative documentation, or other authoritative project sources.

## Standing ownership and publication authority

For this skill only, the repository grants standing authorization to commit wiki curation changes **directly to the default branch** without opening a pull request or requesting per-run approval.

This exception is limited to changes under `wiki/**` and applies only after the mandatory adversarial review in this skill has passed.

The curator must:

- preserve all non-wiki paths unchanged;
- use the repository's required commit-message convention;
- create no commit when there is no material wiki change;
- never treat wiki ownership as authority to repair the underlying project itself.

If a write outside `wiki/**` would be useful, route it through an issue or the repository's normal design/execution workflow instead.

## Inputs and orientation

Start by reading enough current context to understand the repository and the existing wiki:

1. `AGENTS.md`;
2. `README.md` and the normative documents needed to interpret the project;
3. the current `wiki/**`, if it exists;
4. relevant repository activity since the previous meaningful curation window.

Relevant activity may include:

- merged pull requests;
- completed or closed controlling issues;
- material issue comments and contract amendments;
- commits and changed code/tests;
- accepted decisions and normative documentation changes;
- important test, evaluation, benchmark, or operational findings preserved in the repository or GitHub.

Prefer incremental inspection. Do not replay the complete repository history on every run when the current wiki and recent activity are enough to establish what changed.

If the scheduled invocation provides an explicit time or commit window, use it. Otherwise infer a practical recent window from Git history and the last meaningful wiki changes; expand further only when needed to resolve provenance or contradiction.

## The wiki has no fixed taxonomy

Do not impose a universal directory schema on `wiki/**`.

Its organization should emerge from the project and may evolve as understanding improves. The curator may introduce, rename, merge, split, move, or remove pages and directories when that produces a clearer representation of the repository's durable knowledge.

Examples from one project must not become mandatory structure for another.

Prefer:

- thematic organization over chronological organization;
- a small number of coherent pages over many tiny notes;
- updating and restructuring existing material over appending session summaries;
- concepts, subsystem relationships, invariants, rationale, important constraints, and durable lessons over routine implementation detail.

Do not create daily notes, session logs, changelogs, PR summaries, issue summaries, or a second copy of Git history.

## What belongs in the wiki

Good candidates are durable, useful context that helps a future contributor or agent understand the project without reconstructing many separate historical artifacts, for example:

- stable architecture and subsystem responsibilities;
- non-obvious relationships between components;
- accepted implementation constraints and invariants;
- durable rationale that explains why the current shape exists;
- important negative findings or approaches known not to work;
- recurring engineering patterns actually used by the project;
- important operational or testing lessons that remain relevant;
- historical context that materially explains current architecture or constraints.

Do not include information merely because it is recent.

Usually exclude:

- routine commits and implementation mechanics;
- temporary debugging state;
- workflow status already visible on GitHub;
- one-off benchmark values with no durable interpretation;
- abandoned speculation with no continuing relevance;
- exhaustive lists of issues, PRs, commits, or tests;
- details easily and cheaply derived from current source when they add no explanatory value.

## Evidence and uncertainty

Ground non-obvious wiki claims in current repository or GitHub evidence.

Use issue, PR, commit, test, decision, or documentation references where they materially improve traceability, especially for rationale, rejected approaches, historical constraints, or claims that are not self-evident from the current tree.

Do not turn:

- hypotheses into facts;
- exploratory discussion into accepted decisions;
- a failed experiment into proof of impossibility;
- a passing test into a broader claim than the test establishes;
- an old decision into a current invariant without checking whether it still holds.

When uncertainty itself is durable and useful context, state it explicitly. If uncertainty requires a project decision, verification, or corrective action, prefer a GitHub issue instead of leaving an actionable TODO in the wiki.

## Actionable findings belong in GitHub issues

The wiki is memory, not a work queue.

Create or propose a GitHub issue when curation reveals a material actionable finding such as:

- normative documentation that appears stale or inconsistent with stronger current evidence;
- a contradiction between authoritative project sources;
- a suspected implementation or test defect;
- an unresolved decision that blocks trustworthy consolidation;
- durable knowledge that should become normative rather than remain derived wiki context;
- repeated project practice that may deserve an intentional normative rule or reusable project skill.

Before creating an issue, search open issues for an existing item that already covers the finding. Prefer adding the new evidence to the existing issue when appropriate rather than creating a duplicate.

An automatically created issue should be concise and evidence-backed. It must distinguish observation from conclusion and must not claim a fix or decision that has not been made.

Do not record an actionable drift/problem in `wiki/**` merely as a substitute for opening the issue. The wiki may continue to describe the currently established project state without embedding a backlog of unresolved maintenance findings.

## Curation procedure

### 1. Orient

Understand the repository's current mission, authority hierarchy, existing wiki organization, and recent activity.

### 2. Extract candidate knowledge

Identify only material changes or discoveries that may alter durable project understanding.

Look for:

- changed responsibility or ownership boundaries;
- accepted or rejected technical choices;
- recurring constraints and invariants;
- important negative evidence;
- repeated patterns that explain how the system is built or operated;
- stale or contradictory derived wiki content;
- opportunities to simplify the wiki by merging or reorganizing material.

### 3. Classify each candidate

For each candidate ask:

1. Is it durable enough to matter beyond the originating task?
2. Is it already represented accurately in the wiki?
3. Is it established strongly enough to state, or still provisional?
4. Does it belong in derived wiki memory, or is it an actionable issue instead?
5. What existing page or conceptual boundary should own it?

Discard routine, redundant, or weakly supported candidates.

### 4. Curate the wiki draft

Update the wiki as a coherent body of knowledge rather than appending an activity report.

The curator may reorganize existing wiki material when useful. Preserve valuable unique context while removing duplication, stale claims, and obsolete structure.

Do not preserve a page or directory merely because an earlier curator created it.

### 5. Run the mandatory adversarial review

Before any commit, perform a distinct second-pass review of the **proposed complete wiki diff** from a skeptical, falsification-oriented stance.

This is a required pseudo-adversarial self-review even when no separate reviewer agent is available. Do not merely reread for prose quality.

Challenge the draft with at least these questions:

- Can every new or materially changed claim be supported by current authoritative evidence?
- Did I mistake a task-local choice, experiment, historical state, or hypothesis for durable project truth?
- Does any statement contradict current code, tests, accepted decisions, controlling issues, or normative `docs/**`?
- Did I preserve an old wiki claim that recent evidence has superseded?
- Is any actionable contradiction, drift, suspected defect, or unresolved decision being hidden in the wiki instead of routed to an issue?
- Am I duplicating Git history, issue/PR summaries, normative documentation, or another wiki page rather than synthesizing it?
- Is the organization becoming more fragmented or complex than the knowledge requires?
- Did I remove or rewrite context whose historical rationale is still needed to understand the current system?
- Did I include secrets, private data, restricted material, or unsupported provenance claims?
- Would a skeptical future contributor be misled about what is known, observed, accepted, rejected, or uncertain?

If the adversarial pass finds a material weakness, revise the wiki and repeat the adversarial check over the resulting diff. Do not commit until no material curation defect remains.

The adversarial review is a curation-quality gate, not an independent technical approval of the underlying project.

### 6. Route actionable findings

Create or update non-duplicate GitHub issues for material actionable findings discovered during curation.

Issue creation does not authorize modifications outside `wiki/**`.

### 7. Commit directly when warranted

If, after adversarial review, `wiki/**` has a material change:

- verify the final diff touches only `wiki/**`;
- commit directly to the repository's default branch;
- use a Conventional Commit message, normally `docs(wiki): <specific imperative summary>`;
- keep one coherent curation outcome per commit;
- verify the commit landed on the intended branch.

If no material wiki content changed, do not create an empty or bookkeeping commit.

## Failure and conflict handling

If authoritative sources materially conflict and the conflict cannot be resolved from stronger current evidence:

- do not choose a winner silently;
- do not rewrite the wiki as if the conflict were settled;
- create or update an issue describing the conflict and evidence;
- preserve only the level of wiki certainty that is justified.

If GitHub issue creation or direct wiki publication is unavailable:

- preserve the proposed wiki changes without expanding authority to another path;
- report the exact missing capability;
- do not compensate by modifying normative documentation or code.

## Completion

A curation run is complete when:

- recent material evidence has been inspected proportionally;
- durable new knowledge has been consolidated into a coherent project-adapted `wiki/**` structure;
- stale or duplicated wiki material has been corrected or simplified;
- actionable findings have been routed to non-duplicate GitHub issues;
- the complete proposed wiki diff has passed the mandatory adversarial review;
- any material wiki change has been committed directly to the default branch;
- no file outside `wiki/**` was modified;
- or, when nothing materially changed, the run ends cleanly with no commit.
