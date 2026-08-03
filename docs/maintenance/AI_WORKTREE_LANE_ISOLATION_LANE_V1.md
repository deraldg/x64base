# Worktree Lane Isolation -- Stop Sessions Sharing One Working Tree (Lane V1)

**Status:** design-intended -- helper not built. **Lane:** AIF-084.
**Owning project:** `project.x64base.runtime`. **Evidence class:** `design-intended`.
**Companion:** AIF-064 (registry fragments) removes the *guaranteed* conflict; this removes
the *working-tree* one. Neither alone is sufficient.

## The problem, measured

On 2026-08-02 a Cowork session worked for several hours against `development`, then found
that **191 commits had landed** from parallel work while it held a stale picture. Its
prepared commit scripts were built on a repository that no longer existed. Three of four
queued operations turned out to be already done by someone else.

Nothing was lost, but only because the guards happened to fail closed. The near-misses were
real: an obsolete script was one keystroke from committing a redundant 546-file archive, and
a broad `git add` at the wrong moment would have recorded the deletion of 8 LFS files.

Root cause is simple and structural: **every session works in the same directory on the same
branch.** `D:\code\ccode` is one working tree, and each agent, each Codex run, each Cowork
session edits it directly.

## Already half-solved, and only partly abandoned

`git worktree list` shows the idea was already tried, and a naming convention already
chosen (`D:\code\ccode.worktrees\`):

```
D:/code/ccode.worktrees/agents-examine-dottalkpp-source-code   [agents/examine-...]
C:/Users/deral/.codex/visualizations/.../x64base-main-hardening [main]
```

**Correction, and it matters for how this lane is justified.** A first draft of this document
said both were stale (`prunable`). That was wrong, and wrong for an instructive reason: it was
read from the Cowork Linux sandbox, which cannot see `C:` at all, so git reported the Codex
worktree prunable purely because its path was unreachable *from there*. Checked properly, the
`D:` worktree is **live and populated** -- a real branch with a full tree in it.

So the honest position is narrower than "the tool was tried and abandoned":

- The convention exists and at least one worktree is genuinely in use.
- What is missing is that using it is **manual and optional**, so most sessions still land in
  the shared tree by default.

**The problem is not missing tooling -- it is that the isolated path is not the default path.**
When starting work costs one extra decision, the shared tree wins.

*(Method note: `prunable` observed from the sandbox is not evidence about the maintainer's
machine. The two views have different filesystems. This is the same failure shape as reading a
stale header comment and concluding a subsystem does not exist -- see AIF-062.)*

## Design

### The shape

```
D:\code\ccode                       <- development, the integration tree. Maintainer only.
D:\code\ccode.worktrees\
    AIF-084-worktree-lanes\         <- branch lane/AIF-084, one session lives here
    AIF-061-memo-wal\               <- branch lane/AIF-061
```

One `.git`, many working directories. Objects are shared, so a worktree costs a checkout,
not a clone. Two sessions physically cannot edit the same file.

### `new-lane.ps1` -- the helper (the actual deliverable)

```
new-lane.ps1 -Lane AIF-084 -Slug worktree-lanes [-From development]
```

Must do all of this in one step, because any step left to the operator is a step that gets
skipped:

1. **Refuse a lane number already in use.** Scan the intake queue and registries. Lane
   collision is a real failure here -- AIF-047 was claimed by three parallel sessions in turn
   before the traceability lane caught it.
2. `git worktree add -b lane/AIF-084 <path> <from>`.
3. Drop a `LANE.md` in the new worktree root: lane id, branch, base commit, created-at, and
   the finish command. A session that starts there knows what it is without being told.
4. Print the `cd` line and the finish command.
5. Never touch the integration tree.

### `finish-lane.ps1` -- the other half

The failure mode of worktrees is **abandonment** -- a lane opened, worked, and never closed,
until stale records accumulate and `git worktree list` stops being informative. The existing
`agents/examine-dottalkpp-source-code` worktree has been open long enough that nobody would
now be sure whether closing it is safe. So the closing step has to be as cheap as the opening
one, and it has to be safe enough to run without thinking.

```
finish-lane.ps1 -Lane AIF-084 [-Merge] [-Keep]
```

- refuse if the worktree has uncommitted changes (report them; do not discard)
- optionally merge `lane/AIF-084` into `development` in the integration tree
- `git worktree remove`, `git worktree prune`
- leave the branch unless `-Delete`

### Where the Hot Potato lock actually belongs

AIF-059 designed an advisory "who may commit next" lock. Worktrees change what it is for:

| Collision | Fixed by |
|---|---|
| Two sessions editing the same files | **worktrees** -- structurally impossible |
| Two sessions merging/pushing at once | **the lock** -- still needed |

The lock was being asked to prevent both, using care and convention, which is why it kept
failing. It only ever needed to cover the merge step, and that is a much smaller, much more
enforceable scope.

## What this does NOT solve

- **Shared append-only files.** Two sessions on separate worktrees still both append to
  `AI_INTERACTION_INTAKE_QUEUE_V1.md`. Worktrees make this *worse* by enabling more
  parallelism into the same bottleneck. AIF-064 converts the registries to `.d` fragments;
  the intake queue is still a flat markdown table and remains a hotspot.
- **The lane-number allocator.** Step 1 above is a check, not a reservation. Two sessions
  starting within seconds could still pick the same number. A `lanes.d/` reservation
  directory would fix it properly -- deliberately out of scope here.
- **The `tools\*.zip` pointer/attribute mismatch.** Eight files are committed as LFS pointer
  blobs while `.gitattributes` declares `*.zip binary` -- no `filter=lfs`. Nothing converts
  pointer to content on checkout, so they show as deleted, and **every new worktree inherits
  the same eight phantom deletions**. (An earlier draft blamed a missing git-lfs install; that
  was read from the agent sandbox rather than the maintainer's machine, and was wrong -- the
  attribute is the cause, so `git lfs checkout` would not help either.) Resolve the repository
  shape before adopting worktrees, or the isolation simply multiplies the noise. See
  `D:\code\fix-lfs.ps1`.

## Acceptance

Not done until:

1. Two worktrees exist simultaneously, both with edits, and `git status` in each shows only
   its own changes.
2. `finish-lane.ps1` refuses a worktree with uncommitted work, and says what is uncommitted.
3. `new-lane.ps1` refuses a taken lane number.
4. A merge from a lane branch into `development` lands cleanly with no working-tree collision.
5. `git worktree list` shows no `prunable` entries after a finish -- checked **on the
   maintainer's machine**, not from an agent sandbox, since the two see different filesystems.

Only then does `proof.worktree.lane_isolation` go to `runtime_observed`. Creating one worktree
successfully proves nothing: that already happened, and the mechanism still did not become the
default. What has to be shown is the **pair** working -- open and close -- because the closing
step is the one that decides whether this survives contact with a busy week.

## Ties

- `docs/ai-friendly/AI_GITLOCK_HOT_POTATO_LANE_V1.md` (AIF-059) -- scope narrowed by this.
- AIF-064 registry fragments -- the other half of the collision problem.
- `D:\code\fix-lfs.ps1` -- prerequisite.
- `docs/ai-friendly/AGENCY_MODEL_V1.md` -- "serialized when shared"; this is that principle
  applied to the working tree instead of to records.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
