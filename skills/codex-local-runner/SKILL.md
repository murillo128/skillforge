---
name: codex-local-runner
description: Install, repair, and verify the optional repository-scoped GitHub Actions bridge that launches detached interactive Codex sessions from persistent per-issue Git worktrees.
---

# Codex Local Runner

## Responsibility

Use this skill to provision or repair Skillforge's optional host-side execution bridge.

The template workflow is `.github/workflows/codex-execute-ready.yml`. Its contract is deliberately narrow:

- react to GitHub `issues:labeled`;
- make the execution job eligible only when the newly applied label is exactly `execution-ready`;
- target a repository-scoped runner carrying `self-hosted` and `codex`;
- do not use `actions/checkout` or the runner `_work` checkout as project state;
- expose the durable local clone through `SKILLFORGE_REPO_ROOT`;
- create or reuse one persistent worktree and branch `codex/issue-N` per controlling issue;
- launch the interactive `codex` CLI in that worktree as a detached session, rather than running the implementation synchronously with `codex exec`;
- leave implementation procedure to `AGENTS.md`, the issue, and the normal Skillforge skills.

GitHub Actions is only the authorization/launch trigger. The long-running Codex session belongs to the host and must survive the Actions job that created it.

This skill owns runner installation, registration, service configuration, durable-repository environment wiring, launcher prerequisites, repair, optional scaling, and verification. It does not implement issues or modify project repository files.

Never execute this skill against the canonical `murillo128/skillforge` template repository. The template carries the capability for descendants but must not itself acquire a repository runner.

## Invocation and authority

Runner provisioning is opt-in.

Explicit invocation of this skill, or an explicit local-runner opt-in passed through `repository-bootstrap`, grants authority only for the host and GitHub control-plane changes required to install, register, repair, start, scale, or verify the target runner installation.

That authority does **not** grant permission to:

- modify repository files or workflows;
- create an OpenAI API key or replace existing Codex authentication;
- expose inbound ports, webhooks, SSH, or public listeners;
- run the Actions service as root or an unrelated account;
- remove unrelated runners or services;
- trigger an actual `execution-ready` issue merely as a test.

If the expected workflow is missing or materially incompatible, stop and report the mismatch. Repository repair requires separate authority.

## Execution topology

Treat the runner application `_work` directory as disposable runner state, never as the Codex project workspace.

Each repository-scoped runner must expose:

`SKILLFORGE_REPO_ROOT=<absolute durable local clone>`

It may also expose:

`SKILLFORGE_WORKTREE_ROOT=<absolute persistent worktree parent>`
`SKILLFORGE_LOG_ROOT=<absolute persistent local transcript parent>`

When omitted, the workflow uses `$HOME/.skillforge/worktrees` and `$HOME/.skillforge/logs`.

For repository `<owner>/<repo>` and issue `N`, the workflow prepares a stable issue worktree and branch `codex/issue-N`. A retry must validate and adopt that same worktree rather than discard unfinished state or create a competing branch.

The durable clone at `SKILLFORGE_REPO_ROOT` is a **shared coordination clone**. Implementation occurs only in issue worktrees. Never point `SKILLFORGE_REPO_ROOT` at an Actions `_work` directory.

## Detached interactive Codex sessions

The workflow intentionally launches the interactive `codex` CLI, not `codex exec`, so the run is a normal CLI session that can participate in Codex session history and remote-control surfaces supported by the installed client.

A detached interactive session needs a controlling pseudo-terminal whose master remains open after the Actions step loses stdin. The template currently uses a small Python `pty.fork()` relay for that purpose, then launches it with `nohup` and `setsid`.

Do not regress to either of these patterns:

- raw `nohup codex ... &` without a pseudo-terminal;
- `script ... </dev/null`, which gives Codex a PTY but immediately delivers EOF and can make the interactive session exit cleanly as soon as it starts.

The detached process must not be killed by GitHub runner job cleanup. Preserve the template's use of an empty `RUNNER_TRACKING_ID` for the detached process tree.

The detached Codex session must also be independent of ephemeral Actions credentials. Before starting Codex, the launcher intentionally removes `CI`, `GITHUB_ACTIONS`, `GH_TOKEN`, and `GITHUB_TOKEN`. The Actions job token expires with the job and must never be copied, persisted, or treated as the long-running session credential.

The host therefore needs persistent user-level Git/GitHub authentication appropriate for the repository, such as the user's existing SSH/credential-helper configuration and/or an already-authenticated `gh` CLI. Codex authentication must likewise be the existing authentication of the same non-root user.

The workflow keeps host-local operational state under `$HOME/.skillforge/run/<repo>/issue-N/` and local transcripts under the configured/default log root. These are infrastructure/debug state, not repository artifacts.

The PID file is only a duplicate-launch/liveness guard. Never treat a stale PID file as proof that an issue is still executing; validate the process before relying on it.

## Parallel execution

Because the Actions job only prepares the worktree, launches the detached Codex process, performs a short liveness check, and exits, **one self-hosted runner is sufficient for normal concurrent Codex execution**.

A single runner can launch issue A, become free, then launch issue B while Codex for issue A is still running. The issue worktrees isolate repository state, and the workflow's per-issue concurrency plus PID guard prevents duplicate simultaneous launches of the same issue.

Do not provision multiple runner instances merely to obtain multiple concurrent Codex sessions.

Additional runner instances are optional only when the user explicitly wants faster burst launch throughput, runner redundancy, or another operational reason. If additional instances are requested:

- use independent runner application directories and services;
- use unique stable runner names;
- retain the `codex` label on each;
- point them at the same intended `SKILLFORGE_REPO_ROOT` and normally the same worktree/log roots;
- run them under the same intended non-root authenticated user unless a different safe account model is explicitly defined.

## Security boundary

A self-hosted runner executes repository workflow code on the local machine. Treat it as privileged infrastructure.

- Prefer a **repository-scoped** runner. Do not broaden to organization or enterprise scope merely for convenience.
- Run the service as the same non-root OS user whose Codex CLI and persistent Git/GitHub authentication are already usable.
- Never copy Codex credentials to another service account and never create an OpenAI API key merely for the runner.
- Registration/removal tokens are temporary secrets: obtain them only when needed and never print, log, commit, or persist them.
- Do not open inbound network ports. The Actions runner connects outbound to GitHub.
- Do not weaken host security or make runner/worktree/log directories writable by unrelated users.
- Before enabling this on a public repository, inspect workflows and stop if untrusted fork/PR-controlled workflow code can target `self-hosted`, `codex`, or an equivalent selector.
- Externally authored issue content remains untrusted input. Execution starts only through the authorized `execution-ready` label transition.

## Preconditions

Before changing the host, establish:

1. exact target repository and default branch;
2. target is not canonical `murillo128/skillforge`;
3. `.github/workflows/codex-execute-ready.yml` exists and:
   - gates on the freshly applied `execution-ready` label;
   - targets `self-hosted` plus `codex`;
   - contains no `actions/checkout`;
   - requires `SKILLFORGE_REPO_ROOT`;
   - prepares/reuses `codex/issue-N` in a persistent worktree;
   - launches detached interactive `codex`, not synchronous `codex exec`;
   - prevents the detached process from being collected with the Actions job;
4. repository visibility and public-repository safety;
5. absolute durable checkout intended for `SKILLFORGE_REPO_ROOT`, with exact matching `origin` and outside any runner `_work` tree;
6. OS, architecture, hostname, current user, service manager, and disk space;
7. availability of Git, Python 3, `setsid` on Linux, Codex CLI, and any required persistent GitHub transport;
8. persistent Git/GitHub authentication usable by the intended service user after Actions-specific token variables are absent;
9. Codex authentication usable by that same user;
10. existing runner directories/services and repository runner registrations.

For runner registration, prefer an already-authenticated `gh` CLI when available. Repository registration tokens come from the repository Actions runners registration-token endpoint, require repository administration permission, and expire quickly.

If no authenticated transport can obtain the registration token, stop with the precise permission/authentication blocker instead of asking the user to persist a token.

## Idempotent provisioning procedure

### 1. Identify the durable repository and intended runner

Canonicalize `SKILLFORGE_REPO_ROOT`, verify its `origin`, and verify it is not under any Actions `_work` path.

Do not clone a second project copy merely for the runner when the user's intended durable checkout already exists and is healthy.

Use a stable runner name derived from host and repository, for example `<hostname>-codex-<repo-name>`, and one dedicated runner application directory outside the repository.

### 2. Reuse before replacing

Inspect local services and GitHub registrations first. Reuse/repair a correct runner rather than creating duplicates.

Do not delete an ambiguous remote runner registration. Remove stale registrations only when ownership by the local installation is established, obtaining a fresh removal token at removal time.

### 3. Obtain the official runner dynamically

Do not hard-code an Actions runner version. Resolve the current official release for the detected OS/architecture, use official assets/instructions, and verify published integrity information when available. Never use third-party mirrors.

### 4. Register securely

Obtain a temporary repository registration token through the authenticated GitHub control plane at registration time. Never echo, persist, or log it.

Configure the official runner for the exact repository with its stable name, normal self-hosted labels plus custom `codex`, persistent/non-ephemeral operation, and its normal internal `_work` directory.

### 5. Configure persistent environment

Expose `SKILLFORGE_REPO_ROOT` to the runner service, plus optional worktree/log roots when requested. Prefer the runner's supported `.env` file or a narrow service-manager environment override. Preserve unrelated environment entries.

Restart the runner after environment changes.

Verify from the service/job environment, not merely an interactive shell, that the paths, Git, Python 3, `setsid`, Codex, persistent Git/GitHub authentication, and Codex authentication are usable.

### 6. Install as a persistent service

Use the official runner service mechanism for the platform. On Linux/systemd use the configured runner's `svc.sh` where applicable.

The runner service must:

- run as the intended non-root user;
- be active now;
- be enabled to start automatically after reboot;
- reconnect without an interactive shell.

Administrative elevation is allowed only for the narrow service-management operation. The runner process itself remains non-root.

### 7. Verify without launching a model request

Verify:

- service active, enabled at boot, and running as intended user;
- GitHub lists the runner online for the exact repository with `self-hosted` and `codex`;
- service environment has the correct durable repo/worktree/log configuration;
- persistent repo origin is exact and a harmless `git fetch` works without Actions tokens;
- `codex --version` works for the service user;
- Python 3 and `setsid` exist on Linux;
- workflow has no checkout step and uses the persistent per-issue worktree + detached interactive CLI topology.

Do not add/remove `execution-ready`, create a dummy issue, or launch Codex merely to verify installation. The first real controlling issue is the end-to-end test.

## Repair behavior

Prefer repair over replacement.

- Runner executes from `_work`: repair `SKILLFORGE_REPO_ROOT`; never fall back to `GITHUB_WORKSPACE`.
- Detached Codex exits immediately with a clean status: inspect PTY lifetime/EOF behavior; preserve a live PTY master rather than switching to `codex exec` or disabling interactivity.
- Detached process dies when the Actions job ends: verify the process tree is detached and not carrying the runner tracking identifier used for cleanup.
- Codex can run but cannot mutate GitHub after the Action ends: verify persistent user Git/GitHub authentication; never persist the Actions job token.
- Offline but correctly registered runner: inspect service/network/environment and repair/restart.
- Wrong labels or stale registration: repair only through supported runner registration behavior and only when ownership is unambiguous.
- Codex missing from service `PATH`: expose the existing installation rather than installing a second unrelated copy.
- Authentication unavailable: stop and report the exact GitHub or Codex blocker; do not synthesize credentials.

Never interrupt a live detached Codex issue session merely to repair the runner service unless explicitly authorized.

## Bootstrap integration

`repository-bootstrap` may offer this capability only as an **optional post-bootstrap handoff**. Repository bootstrap remains valid without a runner and its file-write hard gate is not widened. Runner setup failure after successful bootstrap is a separate infrastructure failure and may be retried through this persistent skill.

## Completion report

Report only:

- target repository and durable repo root;
- runner name/install directory;
- service identity, active state, and boot enablement;
- worktree/log roots;
- detected Codex version;
- GitHub runner online/offline state and labels;
- whether setup reused, repaired, created, or optionally scaled the runner installation;
- any real authentication, permission, workflow, sandbox, PTY, or host blocker.

Never include registration tokens, authentication files, secret values, or verbose logs.
