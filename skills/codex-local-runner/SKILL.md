---
name: codex-local-runner
description: Install, repair, and verify an optional repository-scoped GitHub Actions self-hosted runner that executes Skillforge issues locally with Codex when they enter execution-ready.
---

# Codex Local Runner

## Responsibility

Use this skill to provision or repair the **optional host-side execution bridge** used by Skillforge's local Codex workflow.

The template workflow is `.github/workflows/codex-execute-ready.yml`. Its contract is deliberately narrow:

- it reacts to the GitHub `issues:labeled` event;
- the execution job is eligible only when the newly applied label is exactly `execution-ready`;
- it targets a runner carrying `self-hosted` and `codex`;
- it checks out the repository and launches Codex with the controlling issue number;
- `AGENTS.md`, the issue, and the normal Skillforge skills remain the procedural authority for the implementation itself.

This skill owns **runner installation, registration, service configuration, environment wiring, repair, and verification**. It does not implement issues, redesign the workflow, or modify project files.

Never execute this skill against the canonical `murillo128/skillforge` template repository. The template carries the capability for descendants but must not itself acquire a repository runner.

## Invocation and authority

Runner provisioning is opt-in.

Explicit invocation of this skill, or an explicit local-runner opt-in passed through `repository-bootstrap`, grants authority to make only the host and GitHub control-plane changes required to install, register, repair, start, or verify the target runner.

That authority does **not** grant permission to:

- modify repository files or workflows;
- create an OpenAI API key or replace the user's existing Codex authentication;
- expose inbound ports, webhooks, SSH, or other public listeners;
- run the Actions service as root or another unrelated account;
- remove unrelated runners or services;
- trigger an actual `execution-ready` issue merely as a test.

If the expected workflow is missing or materially incompatible, stop and report the mismatch. Repairing repository content belongs to the normal repository workflow and requires separate authority.

## Security boundary

A self-hosted runner executes repository workflow code on the local machine. Treat that as privileged infrastructure.

- Prefer a **repository-scoped** runner for this capability. Do not broaden it to organization or enterprise scope merely for convenience.
- Run the service as the same non-root OS user whose local Codex CLI is already authenticated.
- Never copy Codex credentials to a service account and never create an OpenAI API key just for the runner.
- Obtain GitHub runner registration/removal tokens only when needed. They are temporary secrets: do not print, log, commit, or persist them.
- Do not open inbound network ports. The GitHub Actions runner connects outbound to GitHub.
- Do not weaken host security, disable authentication controls, or make the runner directory writable by unrelated users.
- GitHub recommends particular caution with self-hosted runners on public repositories. Before registering one for a public repository, inspect the repository workflows and stop if an untrusted event such as a fork/PR-controlled workflow can target `self-hosted`, `codex`, or an equivalent runner selector.
- An externally authored issue is still untrusted input. The local executor is allowed to start only through the repository's authorized transition to `execution-ready`; do not add broader issue-opened or comment-driven triggers as part of setup.

## Preconditions

Before changing the host, establish all of the following:

1. the exact target repository and its default branch;
2. that the target is not the canonical Skillforge template;
3. that `.github/workflows/codex-execute-ready.yml` exists and its execution job requires the freshly applied label `execution-ready` and runner labels `self-hosted` plus `codex`;
4. repository visibility and the public-repository safety check above;
5. OS, architecture, hostname, current user, service manager, and available disk space;
6. availability and versions of Git, the GitHub CLI or another secure GitHub admin transport, and the Codex CLI;
7. current GitHub authentication and repository-admin capability sufficient to register a repository runner;
8. existing local Actions runner directories/services and existing repository runner registrations.

Prefer `gh` for the GitHub control plane when it is already authenticated. A repository registration token can be obtained through the repository Actions runners registration-token endpoint; it requires repository administration permission and expires quickly.

If no available authenticated transport can obtain the registration token, stop and report the exact authentication/permission blocker rather than asking the user to paste a token into repository files or shell scripts.

## Idempotent provisioning procedure

### 1. Identify the intended runner

Use a stable unique name derived from the machine and repository, for example:

`<hostname>-codex-<repo-name>`

Use a dedicated runner application directory outside the repository worktree. A reasonable default on Linux/macOS is:

`$HOME/actions-runner/<owner>-<repo>`

On Windows, use an appropriate persistent runner directory such as:

`C:\actions-runner\<owner>-<repo>`

Do not share one runner application directory between independent registrations.

### 2. Reuse a correct existing installation

Inspect both the local host and GitHub before installing anything.

If a local service and GitHub registration already match the target repository, intended runner name, and `codex` label, repair/start them as needed instead of creating a duplicate.

If GitHub shows a runner with the intended name but the corresponding local installation cannot be identified safely, do not delete or replace it blindly. Report the ambiguity or choose a distinct stable runner name.

Only remove a stale registration when ownership by the local installation is established. Obtain a fresh removal token at removal time rather than storing one.

### 3. Obtain the official runner package dynamically

Do not hard-code an Actions runner version into this skill or into project state.

Resolve the current official GitHub Actions runner release for the detected OS and architecture, select the matching release asset, and use the official package/install instructions. Prefer the exact setup commands GitHub exposes for the repository when available.

Verify the downloaded package using the integrity information published with the official release when available. Never download runner binaries from third-party mirrors.

Install only dependencies genuinely required by the current official runner on the detected platform.

### 4. Obtain a temporary registration token

With an authenticated GitHub CLI, the repository-scoped operation is conceptually:

```bash
REGISTRATION_TOKEN="$(
  gh api --method POST \
    "repos/${OWNER}/${REPO}/actions/runners/registration-token" \
    --jq .token
)"
```

Do not echo the variable, enable shell tracing around it, write it to disk, or include it in logs.

Use the equivalent secure authenticated operation when `gh` is not the selected control-plane transport.

### 5. Configure the runner

Configure the official runner application unattended for the exact repository, with:

- URL `https://github.com/<owner>/<repo>`;
- the stable runner name;
- custom label `codex`;
- the normal default self-hosted labels retained;
- persistent, non-ephemeral operation;
- the normal `_work` workspace unless the host has an established safer location.

On Unix-like platforms, use the current runner's `config.sh`; on Windows, use `config.cmd`. Inspect the installed runner's current help when platform-specific flags differ rather than guessing obsolete flags.

Do **not** use `--ephemeral` for this capability.

### 6. Preserve the authenticated Codex environment

The runner service must execute as the same non-root user whose Codex CLI is already usable.

Verify at minimum:

- the service account's `HOME` resolves to that user's home;
- `codex` is reachable from the service environment;
- `git` and any required GitHub CLI are reachable;
- the user's existing Codex authentication remains readable by that user and is not copied elsewhere.

Services often receive a smaller `PATH` than an interactive shell. If `codex` is not visible to the service, expose the already-installed executable through a narrow supported service environment configuration. Prefer the runner application's supported environment mechanism or a service-manager override over installing a second unrelated Codex copy.

After changing service environment, restart the runner before verification.

### 7. Install and start the persistent service

Use the official runner service mechanism for the detected platform.

For Linux with systemd, the configured runner provides `svc.sh`; install the service for the intended non-root user, start it, and verify its status. macOS and Windows should use the corresponding official runner service mechanism.

The service must start automatically after reboot and must not require an interactive shell to reconnect to GitHub.

Administrative elevation may be used only for the narrow system operation required to install/manage the service. The runner process itself must remain under the intended non-root user.

### 8. Verify without executing an issue

Verification must establish both local and GitHub state:

- the runner service is active;
- the runner process is running as the intended user;
- GitHub lists the runner for the exact repository;
- the runner status is `online`;
- its labels include `self-hosted` and `codex`;
- the service environment can resolve the installed Codex CLI;
- `codex --version` succeeds under the service user/environment;
- the repository workflow still targets `[self-hosted, codex]` and only the `execution-ready` label transition makes its execution job eligible.

Do not add or remove `execution-ready`, open a dummy issue, or launch a model request solely to prove the runner installation. The first real controlling issue is the end-to-end execution test.

## Repair behavior

Prefer repair over replacement.

- Offline but correctly registered: inspect service state, logs, network reachability, user environment, and runner compatibility; repair and restart.
- Local runner exists but registration is gone: re-register the same installation only after confirming no active conflicting service/job.
- Registration exists but local install is stale: remove/re-register only when ownership is unambiguous.
- Wrong labels: reconfigure through the supported runner registration procedure; do not edit GitHub state by inventing undocumented metadata.
- Codex missing from service `PATH`: repair the service environment rather than re-installing Codex unnecessarily.
- Authentication unavailable: stop and report the exact GitHub or Codex authentication blocker. Do not synthesize credentials.

Never disturb an active runner job while repairing another issue unless the user explicitly authorizes interruption.

## Bootstrap integration

`repository-bootstrap` may offer this capability as an **optional post-bootstrap handoff**.

The repository bootstrap itself must remain independent:

- it does not install a runner by default;
- absence of a runner does not make repository bootstrap incomplete;
- its repository-file hard gate is not widened for runner setup;
- after the bootstrap commit has been published and verified, an explicit opt-in may invoke this skill against the newly initialized repository;
- if runner setup then fails, report that host-side failure separately; the already verified repository bootstrap remains complete and this persistent skill can be retried later.

## Completion report

Report only the operational facts needed to understand the resulting infrastructure:

- target repository;
- runner name;
- install directory;
- service identity and running/stopped status;
- detected Codex version;
- GitHub runner online/offline status;
- runner labels;
- whether setup reused, repaired, or created the installation;
- any real remaining authentication, permission, workflow, or host blocker.

Do not include registration tokens, authentication files, secret values, or verbose service logs in the completion report.
