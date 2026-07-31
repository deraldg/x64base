# Repository Role and Promotion Contract v1

Status: source-defined, mechanically guarded.
Declared by: x64base maintainer.
Effective: 2026-07-27.
Owner: `member.derald`.

## Purpose

Prevent development work, sterilized publication staging, and the public
snapshot from being mistaken for interchangeable Git worktrees or branches.

## Canonical Roles

| Location | Required branch | Role | Permitted remote branch |
| --- | --- | --- | --- |
| `D:\code\ccode` | `development` | Sole development and authoring authority | `development` only |
| `C:\x64base` | `main` | Sterilized publication staging | `main` only |
| `github.com/deraldg/x64base` | `main` | Public snapshot | not an authoring authority |

`D:\code\ccode` defines active development truth. `C:\x64base` is a controlled
publication worktree built from a reviewed public baseline plus explicitly
selected development material. GitHub `main` is the public result, not a source
from which active development is reconstructed wholesale.

## Non-Negotiable Rules

1. Original work is authored only in `D:\code\ccode`.
2. `C:\x64base` is not a development workspace, backup, or peer authority.
3. A push made from `D:\code\ccode` may update only
   `refs/heads/development`.
4. A push that updates `refs/heads/main` may originate only from the sterilized
   staging workflow rooted at `C:\x64base`.
5. Never push `development` to `main`, including an explicit refspec such as
   `development:main`.
6. Never merge the `development` branch into `main`.
7. A temporary source-promotion branch, when explicitly authorized, is created
   from `main` in the sterilized staging workflow. It receives only the reviewed
   source slice, is cold-clone tested, and is merged into staging `main`.
   It is not the `development` branch and must not contain unrelated development
   history. The managed hook remains fail-closed on non-`main` staging branches
   unless the operator explicitly sets `X64BASE_ALLOW_STAGING_BRANCH=1` for an
   authorized `promotion/*` branch.
8. Publication remains selective. Data and documentation projections follow
   `PROMOTE.manifest`; source promotion follows the reviewed, main-based source
   lane. Neither lane authorizes a blanket copy or development-to-main merge.
9. Branch creation, commit, push, merge, reset, cleaning, or publication still
   requires explicit maintainer authorization for the current task.

## Required Preflight

Before any commit or push, record and verify:

```text
resolved repository root:
current branch:
intended remote:
intended remote ref:
promotion lane:
maintainer authorization:
```

Run:

```powershell
python tools\staging\repository_role_guard.py
python tools\staging\prepush_gate.py
```

Install the repository-managed commit and push hooks with:

```powershell
python tools\staging\repository_role_guard.py --install-hooks
```

The push hook evaluates the actual ref updates supplied by Git. It rejects
`development -> main`, rejects a `main` push from the development worktree, and
rejects a `development` push from staging. A hook is a guardrail, not
authorization; Git's `--no-verify` can bypass local hooks and must not be used
to evade this contract.

## Evidence and Limits

- The human-readable rule is carried by `AGENTS.md`, `AI_README.md`,
  `AI_PORTAL.md`, and the development authority seed.
- `tools/staging/repository_role_guard.py` provides path, branch, and push-ref
  enforcement.
- `tools/staging/prepush_gate.py` provides change-set enforcement and installs
  both managed hooks through the repository-role guard.
- The guard can prevent wrong-root and wrong-ref operations. It cannot determine
  whether content was genuinely reviewed, so the manifest, drift audit,
  staging proof, and maintainer review remain required.

## Supersession

This contract supersedes repository-role statements that describe
`C:\x64base` as a backup, ordinary mirror, disposable worktree, or development
source. Historical reports remain evidence of what was believed at their date,
not current operating instructions.

When another document conflicts with this contract, stop and follow this
contract plus `AI_README.md`. Report the conflicting document as drift.
