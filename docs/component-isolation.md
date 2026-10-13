# Component-aware validation and integration

## Contract and defaults

Keep one repository, but select validation and invalidate evidence by declared
input/dependency domains instead of by repository-wide commit identity alone.
This is an optional optimization, not a reduction of merge authority, independent
review, required checks, or integration acceptance. Without a valid accepted map,
use the existing conservative reconciliation and validation procedure.

`.skillforge/components.json` is a version-1 JSON object containing `components`
and optional `global_paths`. Each component declares `paths`, `depends_on`, and
`checks`. `A.depends_on: [B]` means changes to B also require A's validation.
Paths are exact repository-relative filenames or directory prefixes ending `/`;
there are no globs, exclusions, or ignored/unowned paths. Multiple matching owners
are unioned. Unknown paths and global inputs require full validation. Malformed
manifests, duplicate keys, missing dependencies and cycles fail closed.

The template map covers its existing epic, cleanup and runner regressions. It is
not a generated application's architecture. During project initialization, retain
these infrastructure owners only where applicable and explicitly add the actual
product's components, test/fixture/generator inputs, dependency edges and native
check mappings. Do not guess boundaries or claim a directory layout proves
independence. Missing application coverage means full native application CI, not
just Skillforge's infrastructure tests. Removing the manifest disables selection.

Changes to `AGENTS.md`, the manifest, the planner and its tests, this contract, or
any workflow are always global. Projects must also declare shared lockfiles,
compiler/toolchain settings, schemas, code generators, fixtures, runtime service
contracts and configuration as component inputs or globals. Runtime dependencies
count even when they do not appear as imports. Add a shared acceptance component
with dependencies on its participants when a joint invariant can be broken by
otherwise disjoint edits. A shared downstream consumer is an overlap, not proof
of independence. No path-only tool can discover missing semantic dependencies.

## CI selection

Use the planner and manifest from the accepted base, never the PR's proposed
policy to exempt that same PR. A policy change runs full validation and needs
explicit review of its changed coverage. `.github/scripts/component_impact.py`
uses complete NUL-delimited Git diffs without rename collapsing or API pagination.
Its `plan` command takes exact base and tested candidate commit SHAs. For a PR,
compare its actual test-merge commit to its base; for a merge group use the group's
base and tested head; for a push compare `before` to the pushed commit. A PR diff
alone is not the combined integration candidate.

The template's `offline-regressions` job retains its existing check name and
always starts on PRs, pushes to main, merge groups and manual dispatch. Individual
suites run only when selected; planner contract tests always run. Bootstrap or
unavailable base policy selects every native suite. Invalid plans fail rather
than producing an empty green job. Unknown check identifiers must be added to the
accepted workflow registry, never silently dropped. Workflow changes are global.
A manual dispatch runs the full suite. Cancellation supersedes only an older run
of the same PR, never other PRs or main's accepted results.

The check's log/summary records the exact diff, components and applicable checks.
A skipped non-applicable step is not a passed test. Every selected test must
finish successfully; pending/failing/cancelled required checks still forbid
merge. Branch/ruleset-required checks and issue-specific acceptance are additional
constraints, not replaced by this selector. Do not configure a path-skipped
workflow as the only required check. Application CI can consume the same plan,
but must supply its own complete check registry and full-validation fallback.

## Forward base drift without an unnecessary rebase

The executor/auditor may retain an unchanged published PR head when only its
base advances independently. Record the base used by the completed evidence as
`old_base`; fetch `new_base` and the unchanged exact `head`. Run the accepted-base
planner's `drift` command with these SHAs and an explicit `environment-key` that
identifies the real toolchain, dependency resolution, test command/configuration,
fixtures and relevant external inputs. Example command (replace the variables
with captured immutable values):

```sh
python3 /trusted/component_impact.py --repo . drift \
  --old-base "$OLD_BASE" --new-base "$NEW_BASE" --head "$HEAD_SHA" \
  --environment-key "$VALIDATED_ENVIRONMENT_KEY"
```

The report requires forward ancestry, a unique PR merge base, a known non-global
PR scope, clean old/new synthetic Git merge trees, disjoint transitively affected
domains (including common consumers), and identical relevant input fingerprints.
Git 2.38+ is needed for `merge-tree --write-tree`; unavailable Git objects or merge
support are not equivalence evidence. Custom merge drivers are rejected rather than executed, and replacement refs are ignored. The command creates Git tree objects only;
it does not check out files, rebase, push, merge a PR, change labels or fabricate
checks. `reuse_eligible: true` is a scope/input proof, not a technical PASS.

For an eligible report, retain the implementation head and its unchanged technical
review; attach the report and existing evidence identities to the normal handoff
or audit record. Refresh the actual applicable CI/check/status set for the current
candidate. Evidence may be reused only for the named unchanged input domain,
matching environment and successful trusted original execution. Record both the
original tested revision/run and the current candidate tree/fingerprint. Never
relocate an old green status onto another SHA, reuse a failed/pending run, or waive
a required current-target check. Full-system/non-hermetic checks are not reusable
unless all their inputs really belong to the proven domain; otherwise rerun them.

If the report is ineligible, unavailable, or uncertain, follow the existing
executor-owned reconciliation path and revalidate affected checks. A changed head,
manual conflict resolution, changed dependency/contract, changed policy or changed
test environment invalidates the corresponding review/evidence. Do not reuse a
verdict merely because `patch-id` or modified filenames look similar. Forward
drift without a technical defect remains reconciliation, not a fabricated FAIL.

## Final merge, races and scheduling

Re-read head, base, ownership, branch rules and applicable checks immediately
before merge. Further base movement requires a fresh report against that tip;
head movement requires fresh exact-target review. Never weaken strict up-to-date
requirements, required checks, rulesets or the no-bypass gate. When GitHub requires
an updated branch, reconcile it and reuse only input-equivalent build artifacts
through normal current-candidate checks, not a stale CI status.

An expected-head guard on GitHub's merge API does **not** compare-and-swap the base.
Where exact-current-base eligibility is required, use a repository-supported merge
queue or an existing integration-writer lease covering all base writers through
the final check and publication. An advisory agent-only lock does not cover human
or external writers. Without such a supported final publication boundary, do not
use an optimistic report to claim atomic safety; retain the conservative merge
path. This capability does not provision a queue, introduce direct-main authority,
or relax branch protection. Never retry a lost ref lease by overwriting new work.

The epic scheduler keeps its existing persisted DAG, dependency completion rules,
parallelism limit and mutex semantics. At initial design/scheduling, create mutexes
for actual conflicting writes or exclusive shared resources, not for repository
membership, a shared base SHA, or read-only dependencies alone. A component graph
supplements issue contracts; it does not regenerate a canonical DAG or remove
already accepted mutexes. Keep independent work concurrent and serialize only the
short final integration section where the supported publication method requires it.

## Fingerprints, evidence and validation

The `fingerprint` command requires an exact revision, component and environment
key. Its versioned hash includes the component and transitive dependency inputs,
file paths, blob identities, executable/symlink/submodule modes, accepted manifest,
global/unmapped tracked inputs and environment key. It excludes the unrelated
commit SHA, so an independent merge need not invalidate a content-addressed build
cache. Untracked state, network services and mutable dependencies are not magically
captured: pin them, include their identities, or do not cache/reuse that task.
Untrusted PRs must not write trusted cache entries. Caches accelerate execution;
they are not a substitute for a fresh required check or independent review.

Run `python3 -m unittest discover -s .github/scripts -p 'test_component_impact.py' -v`
for the focused contract. The tests use real temporary Git histories to distinguish
independent edits, dependencies, shared consumers, merge conflicts, rewritten base
history, complete large diffs, renames/deletions and input/environment/mode changes.
They also cover missing/malformed manifests, unknown paths, schema errors and CI
check selection. Existing suites remain the owners of runner, cleanup and epic
behavior; these tests do not claim to benchmark agents or production throughput.
