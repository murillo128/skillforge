---
name: codex-local-runner
description: Install, repair, and verify optional repository-scoped GitHub Actions self-hosted runners that execute Skillforge issues locally with Codex from persistent per-issue Git worktrees.
---

# Codex Local Runner

## Responsibility

Use this skill to provision or repair the **optional host-side execution bridge** used by Skillforge's local Codex workflow.

The template workflow is `.github/workflows/codex-execute-ready.yml`. Its contract is deliberately narrow:

- it reacts to the GitHub `issues:labeled` event;
- the execution job is eligible only when the newly applied label is exactly `execution-ready`;
- it targets a runner carrying `self-hosted` and `codex`;
- it does **not** use `actions/checkout` or execute Codex from the runner's `_work` checkout;
- the runner exposes the repository's durable local clone through `SKILLFORGE_REPO_ROOT`;
- the workflow creates or reuses a dedicated persistent Git worktree for the controlling issue and launches Codex with that worktree as its workspace;
- `AGENTS.md`, the issue, and the normal Skillforge skills remain the procedural authority for the implementation itself.

This skill owns **runner installation, registration, service configuration, persistent-repository environment wiring, repair, scaling, and verification**. It does not implement issues, redesign project behavior, or modify project repository files.

Never execute this skill against the canonical `murillo128/skillforge` template repository. The template carries the capability for descendants but must not itself acquire a repository runner.

## Invocation and authority

Runner provisioning is opt-in.

Explicit invocation of this skill, or an explicit local-runner opt-in passed through `repository-bootstrap`, grants authority to make only the host and GitHub control-plane changes required to install, register, repair, start, scale, or verify the target runner set.

That authority does **not** grant permission to:

- modify repository files or workflows;
- create an OpenAI API key or replace the user's existing Codex authentication;
- expose inbound ports, webhooks, SSH, or other public listeners;
- run the Actions service as root or another unrelated account;
- remove unrelated runners or services;
- trigger an actual `execution-ready` issue merely as a test.

If the expected workflow is missing or materially incompatible, stop and report the mismatch. Repairing repository content belongs to the normal repository workflow and requires separate authority.

## Execution topology

Treat GitHub Actions only as the scheduler/trigger. The runner application's `_work` directory is **not** the project workspace.

Each repository-scoped runner must be configured with:

- `SKILLFORGE_REPO_ROOT=<absolute path to the durable local clone>`;
- optionally `SKILLFORGE_WORKTREE_ROOT=<absolute persistent worktree parent>`.

When `SKILLFORGE_WORKTREE_ROOT` is absent, the workflow uses `$HOME/.skillforge/worktrees`.

For repository `<owner>/<repo>` and issue `N`, the workflow uses a stable issue worktree under the configured worktree parent and branch `codex/issue-N`. A retry may adopt that same worktree after validating its branch rather than discarding unfinished local state.

The durable clone at `SKILLFORGE_REPO_ROOT` is a **shared coordination clone**. Issue implementation must occur in issue worktrees. Do not configure the runner to point `SKILLFORGE_REPO_ROOT` at its own `_work` directory.

### Parallel execution

One GitHub Actions self-hosted runner application accepts one job at a time. Git worktrees isolate repository state, but multiple issues execute concurrently only when the host has multiple registered runner application instances available.

When the user explicitly requests `N` parallel local workers:

- install or reuse `N` independent runner application directories and services for the same repository;
- give every instance a unique stable runner name;
- keep the `codex` custom label on every instance;
- configure every instance with the same `SKILLFORGE_REPO_ROOT` and normally the same `SKILLFORGE_WORKTREE_ROOT`;
- never share one runner application directory between multiple services;
- run all instances as the same intended non-root Codex-authenticated user unless the user explicitly defines a different safe account model.

The workflow's per-issue concurrency group prevents duplicate simultaneous executions of the same controlling issue while still allowing distinct issues to be scheduled on different runner instances.

If no parallel-worker count was requested, provision one runner instance by default rather than inventing capacity.

## Security boundary

A self-hosted runner executes repository workflow code on the local machine. Treat that as privileged infrastructure.

- Prefer **repository-scoped** runners for this capability. Do not broaden them to organization or enterprise scope merely for convenience.
- Run services as the same non-root OS user whose local Codex CLI is already authenticated.
- Never copy Codex credentials to a service account and never create an OpenAI API key just for the runner.
- Obtain GitHub runner registration/removal tokens only when needed. They are temporary secrets: do not print, log, commit, or persist them.
- Do not open inbound network ports. GitHub Actions runners connect outbound to GitHub.
- Do not weaken host security, disable authentication controls, or make runner/worktree directories writable by unrelated users.
- GitHub recommends particular caution with self-hosted runners on public repositories. Before registering one for a public repository, inspect repository workflows and stop if an untrusted event such as a fork/PR-controlled workflow can target `self-hosted`, `codex`, or an equivalent selector.
- An externally authored issue is still untrusted input. The local executor may start only through the repository's authorized transition to `execution-ready`; do not add broader issue-opened or comment-driven triggers as part of setup.

## Preconditions

Before changing the host, establish all of the following:

1. the exact target repository and its default branch;
2. that the target is not the canonical Skillforge template;
3. that `.github/workflows/codex-execute-ready.yml` exists and:
   - requires the freshly applied label `execution-ready`;
   - targets `self-hosted` plus `codex`;
   - does not use `actions/checkout`;
   - requires `SKILLFORGE_REPO_ROOT`;
   - prepares a dedicated issue worktree before launching Codex;
4. repository visibility and the public-repository safety check above;
5. the absolute durable local checkout that should become `SKILLFORGE_REPO_ROOT`;
6. that this checkout resolves to the exact target repository and is not inside any Actions runner `_work` tree;
7. OS, architecture, hostname, current user, service manager, and available disk space;
8. availability and versions of Git, the GitHub CLI or another secure GitHub admin transport, and the Codex CLI;
9. current GitHub authentication and repository-admin capability sufficient to register repository runners;
10. existing local Actions runner directories/services and existing repository runner registrations.

Prefer `gh` for the GitHub control plane when it is already authenticated. A repository registration token can be obtained through the repository Actions runners registration-token endpoint; it requires repository administration permission and expires quickly.

If no authenticated transport can obtain the registration token, stop and report the exact authentication/permission blocker rather than asking the user to paste a token into repository files or shell scripts.

## Idempotent provisioning procedure

### 1. Identify the persistent repository and intended runners

Resolve `SKILLFORGE_REPO_ROOT` to an absolute canonical path and verify its `origin` is the exact target repository.

Do not clone a second project copy merely for the Actions runner if the user's intended durable checkout already exists and is healthy. If no suitable durable clone exists, creating one requires explicit authority because that is project-host state beyond runner registration.

Use stable unique runner names derived from the machine, repository, and worker index, for example:

- `<hostname>-codex-<repo-name>` for one worker;
- `<hostname>-codex-<repo-name>-01`, `-02`, ... when parallel workers were explicitly requested.

Use one dedicated runner application directory per registration. Reasonable defaults on Linux/macOS are `$HOME/actions-runner/<owner>-<repo>` for one worker or `$HOME/actions-runner/<owner>-<repo>-NN` for several. Use equivalent persistent paths on Windows.

### 2. Reuse correct existing installations

Inspect both the local host and GitHub before installing anything.

If local services and GitHub registrations already match the target repository, intended runner names, `codex` label, service user, and required environment, repair/start them as needed instead of creating duplicates.

If GitHub shows a runner with an intended name but the corresponding local installation cannot be identified safely, do not delete or replace it blindly. Report the ambiguity or choose a distinct stable runner name.

Only remove a stale registration when ownership by the local installation is established. Obtain a fresh removal token at removal time rather than storing one.

### 3. Obtain the official runner package dynamically

Do not hard-code an Actions runner version into this skill or project state.

Resolve the current official GitHub Actions runner release for the detected OS and architecture, select the matching release asset, and use the official package/install instructions. Prefer the exact setup commands GitHub exposes for the repository when available.

Verify the downloaded package using integrity information published with the official release when available. Never download runner binaries from third-party mirrors.

Install only dependencies genuinely required by the current official runner on the detected platform.

### 4. Obtain temporary registration tokens

With an authenticated GitHub CLI, obtain each repository-scoped registration token at registration time from:

`repos/<owner>/<repo>/actions/runners/registration-token`.

Do not echo tokens, enable shell tracing around them, write them to disk, or include them in logs. Obtain fresh tokens as necessary instead of persisting them.

### 5. Configure each runner

Configure each official runner application unattended for the exact repository with:

- URL `https://github.com/<owner>/<repo>`;
- its unique stable runner name;
- custom label `codex`;
- the normal default self-hosted labels retained;
- persistent, non-ephemeral operation;
- its normal `_work` workspace, which remains runner-internal and is not used as the Codex project checkout.

On Unix-like platforms use the current runner's `config.sh`; on Windows use `config.cmd`. Inspect current help when platform-specific flags differ rather than guessing obsolete flags. Do **not** use `--ephemeral` for this capability.

### 6. Configure the persistent project environment

For every runner instance, expose at least:

`SKILLFORGE_REPO_ROOT=<canonical durable project checkout>`

Optionally expose:

`SKILLFORGE_WORKTREE_ROOT=<canonical persistent worktree parent>`

Prefer the runner application's supported `.env` file or an equivalent narrow service-manager environment mechanism. Do not put these host paths into the repository workflow itself: the template must remain portable across machines.

The runner application reads its environment when it starts, so restart the runner after changing this configuration.

Verify from the service/job environment, not merely an interactive shell, that:

- `SKILLFORGE_REPO_ROOT` is present and points at the intended repository;
- the persistent repo's `origin` is the exact GitHub repository;
- the worktree parent is writable by the runner user;
- `codex`, `git`, and any required GitHub CLI are reachable;
- the user's existing Codex authentication remains usable and has not been copied elsewhere.

### 7. Preserve the authenticated Codex environment

The runner service must execute as the same non-root user whose Codex CLI is already usable.

Verify the service account's `HOME`, `PATH`, Git configuration, SSH/credential helper behavior where relevant, and Codex authentication. Services often receive a smaller `PATH` than an interactive shell. If `codex` is not visible, expose the already-installed executable through the runner/service environment rather than installing an unrelated second copy.

Do not create an OpenAI API key merely to make automation work.

### 8. Install and start persistent services

Use the official runner service mechanism for the detected platform.

For Linux with systemd, the configured runner provides `svc.sh`; install each service for the intended non-root user, start it, and verify status. macOS and Windows should use the corresponding official runner service mechanism.

Every configured worker must start automatically after reboot and must not require an interactive shell to reconnect to GitHub.

Administrative elevation may be used only for the narrow system operation required to install/manage services. Runner processes themselves remain under the intended non-root user.

### 9. Verify without executing an issue

Verification must establish local, repository, and GitHub state:

- every intended runner service is active and runs as the intended user;
- GitHub lists the expected runner registrations for the exact repository;
- every intended runner is `online` and carries `self-hosted` plus `codex`;
- each service inherits the correct `SKILLFORGE_REPO_ROOT` and optional worktree root;
- `codex --version` succeeds under the service user/environment;
- the repository workflow has no `actions/checkout` step;
- only the `execution-ready` label transition makes the execution job eligible;
- the workflow prepares `codex/issue-N` in a persistent per-issue worktree and launches Codex with that worktree as its workspace.

Do not add/remove `execution-ready`, open a dummy issue, or launch a model request solely to prove installation. The first real controlling issue is the end-to-end execution test.

## Repair behavior

Prefer repair over replacement.

- Runner executes from `_work`: configure `SKILLFORGE_REPO_ROOT` in that runner's persistent environment, restart it, and verify the current workflow no longer uses `actions/checkout`.
- Offline but correctly registered: inspect service state, logs, network reachability, user environment, and runner compatibility; repair and restart.
- Local runner exists but registration is gone: re-register the same installation only after confirming no active conflicting service/job.
- Registration exists but local install is stale: remove/re-register only when ownership is unambiguous.
- Wrong labels: reconfigure through the supported runner registration procedure; do not invent undocumented metadata.
- Codex missing from service `PATH`: repair the service environment rather than reinstall Codex unnecessarily.
- `SKILLFORGE_REPO_ROOT` wrong or missing: repair environment and restart; never silently fall back to `GITHUB_WORKSPACE`.
- Authentication unavailable: stop and report the exact GitHub or Codex authentication blocker. Do not synthesize credentials.

Never disturb an active runner job while repairing another issue unless the user explicitly authorizes interruption.

## Bootstrap integration

`repository-bootstrap` may offer this capability as an **optional post-bootstrap handoff**.

The repository bootstrap itself remains independent:

- it does not install a runner by default;
- absence of a runner does not make repository bootstrap incomplete;
- its repository-file hard gate is not widened for runner setup;
- after the bootstrap commit has been published and verified, an explicit opt-in may invoke this skill against the newly initialized repository;
- if runner setup then fails, report that host-side failure separately; the already verified repository bootstrap remains complete and this persistent skill can be retried later.

## Completion report

Report only the operational facts needed to understand the resulting infrastructure:

- target repository and persistent repo root;
- runner names and worker count;
- runner install directories;
- service identities and statuses;
- worktree root;
- detected Codex version;
- GitHub runner online/offline statuses and labels;
- whether setup reused, repaired, created, or scaled the installation;
- any real remaining authentication, permission, workflow, sandbox, or host blocker.

Do not include registration tokens, authentication files, secret values, or verbose service logs in the completion report.
