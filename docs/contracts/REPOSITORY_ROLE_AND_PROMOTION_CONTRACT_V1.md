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
| `D:\dev\x64base-site` | `codex/lean-sites-publish` | Website source tree | `codex/lean-sites-publish` only |
| `github.com/deraldg/x64base` | `main` | Public snapshot | not an authoring authority |

`D:\code\ccode` defines active development truth. `C:\x64base` is a controlled
publication worktree built from a reviewed public baseline plus explicitly
selected development material. GitHub `main` is the public result, not a source
from which active development is reconstructed wholesale.

## ONE REMOTE, FOUR UNRELATED HISTORIES

**Every tree above pushes to the SAME repository, `github.com/deraldg/x64base`.
They are not forks or copies of one another: they are ORPHAN BRANCHES with NO
COMMON ANCESTOR.** Proven by root commit, `git rev-list --max-parents=0 <ref>`:

| Root commit | Project | Local tree | Branches |
| --- | --- | --- | --- |
| `7c56022a1` | Public C++ engine | `C:\x64base` (STAGING) | `main`, and the `ai-portal-*`, `ci/*`, `copilot/*` topics |
| `ee49498b1` | Development tree | `D:\code\ccode` | `development` |
| `6ee42f04c` | Website | `D:\dev\x64base-site` | `codex/lean-sites-publish` -- the ONLY site branch on the remote |
| `572f33cd5` | Built site output | publisher worktree | `gh-pages` |

**Read the first row carefully: `C:\x64base` IS the staging worktree, and the
history it carries IS the public engine's.** Staging is a ROLE, not a separate
project -- the sterilization rules exist precisely because that tree writes
directly onto the published history. The other two roots never touch it.

`git merge-base origin/main origin/codex/lean-sites-publish` returns nothing.

**CONSEQUENCES, each of which has already cost someone time:**

1. **A BRANCH NAME IDENTIFIES NOTHING HERE. Compare ROOT COMMITS before
   comparing anything else.** `git log A..B` and `git diff` both run happily
   across unrelated histories and produce confident, meaningless numbers.
2. **`main` IS THE ENGINE'S BRANCH, NOT THE WEBSITE'S.** `origin/HEAD` resolves
   to it because it is the public repository's front page. **Do not repoint
   `origin/HEAD`** to make some other tree's branch the default.
3. **THE SAME NAME CAN MEAN TWO DIFFERENT PROJECTS IN ONE WORKING DIRECTORY.**
   In `D:\dev\x64base-site`, local `main` is an abandoned SITE branch (never
   pushed, no upstream) while `origin/main` is the ENGINE. A comparison against
   one, described using the other's name, is the failure this section exists to
   prevent -- it happened on 2026-09-02.
4. The `codex/` prefix on the website branch is an AUTHORSHIP artifact: Codex
   scaffolded the site and named the branch. It encodes no workflow meaning.

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
10. **A TAG MAY BE PUSHED FROM `D:\\code\\ccode` ONLY UNDER FOUR CONDITIONS,
    AND `repository_role_guard.py` CHECKS ALL FOUR.** It must be an ANNOTATED
    tag; its target must ALREADY BE PUBLISHED on `refs/remotes/origin/development`;
    the remote must not already carry that tag name; and the role must not be a
    branch-cut. Deletion of any ref stays refused. Cutting a GitHub RELEASE is
    outside this rule -- a release is a publication act and goes through the
    staging workflow.

    The safety property is the second condition: **a tag can never be the thing
    that publishes a commit.** It may only name history that is already on the
    declared branch's remote, so it adds a name and no content.

    **THIS RULE WAS WRONG TWICE IN ONE HOUR AND BOTH ARE RECORDED, because the
    failure mode is the subject.** The first draft said a tag from here is a
    harmless marker; `git push origin v0.6.0` was then BLOCKED, because the
    guard refused every ref outside `refs/heads/*` and had done so all along --
    the policy lived in the tool and this document had filled its own silence
    with the opposite. The second draft said no tag may ever be pushed, and the
    owner ruled the guard should be narrowed instead. **A CONTRACT THAT
    CONTRADICTS ITS OWN ENFORCEMENT IS THE DEFECT THIS PROJECT KEEPS FINDING**
    -- a usage contract describing behaviour the code stopped having. Which is
    why the narrowing and this rule shipped in ONE commit, with tests.

## Tag Convention

**Added 2026-08-30, because the contract's silence was being read as an answer.**
Rules 3 and 4 govern `refs/heads/*` and this document said NOTHING about
`refs/tags/*`. That silence is not permission and it is not prohibition; it was
a gap, and a gap in a contract gets filled by whoever guesses next.

**MEASURED BEFORE WRITING THIS.** Ten tags exist in FOUR naming styles --
`alpha-v3`, `alpha-5.0`, `v4.2-alpha`, `v0.5.0` -- with no document naming a
rule. That is the same defect the R-number register was created to end: a
sequence several people numbered independently while nothing declared the
convention. The newest tag is `homegrown-cnx-20251112`; the newest
version-series tag is `v0.5.0`, dated 2025-09-06.

1. **`vMAJOR.MINOR.PATCH` is the canonical series.** The other three styles are
   history and stay where they are; nothing is renamed, because a tag someone
   may have cloned against is an identity and renaming it is worse than an
   inconsistent set.
2. **The version comes from the version authority, not from a person.**
   `CMakeLists.txt`'s `project(... VERSION ...)` is the single declaration that
   `check-version-coherence` already enforces on every commit. A tag whose
   number disagrees with it is a second answer to a settled question.
3. **Tags are ANNOTATED, never lightweight.** A snapshot with no message is a
   date and a hash, which is what the log already gives you. The message says
   what the tree could do at that commit and what was still open.
4. **A tag is cut from a CLEAN tree that is level with `origin/development`.**
   A tag on unpushed or dirty state names a commit nobody else can fetch.
   RULE 10 ENFORCES THIS MECHANICALLY: the guard requires the tag's target to
   be reachable from `origin/<declared branch>`, so a tag on unpushed work is
   refused rather than merely discouraged.
5. **A tag is never moved once pushed.** If it named the wrong commit, cut a new
   one and say why in its message. The same rule the AIF and R sequences carry:
   an identity that changes meaning is worse than a gap. RULE 10 ENFORCES THIS
   TOO: a push whose remote already carries the tag name is refused. Re-cutting
   a tag that was never pushed is untouched by this and is how `v0.6.0` was
   moved off the commit carrying rule 10's first, wrong draft.

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
