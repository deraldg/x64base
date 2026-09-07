// @dottalk.file v1
// subsystem: docs
// layer: contract
// project: project.x64base.runtime
// lane: AIF-156
// owner: member.derald
// status: review-needed

# THE CLOSE-OUT CONTRACT -- HOUSEKEEPING AND GOOD-NEIGHBOUR

`AI_TIER1_SEED_V1.md` section 5 states the invariant: **a task is not done
until the housekeeping is finished, and housekeeping here is a governed
state-reconciliation cycle, not tidying prose.** This file is what that cycle
IS.

Four checks. Each is a MEASUREMENT you run, not a habit you claim.

## 1. Nothing of yours is uncommitted

    git --no-optional-locks status -uall

**Name every modified file as yours or somebody else's.** If you cannot, you do
not know what you changed, and the summary you are about to write is fiction.
`-uall` is required: this clone sets `status.showUntrackedFiles=no`, so a bare
`git status` reports NOTHING for a file you just created.

## 2. Say what the other session owns, and that you left it alone

This tree is worked concurrently. List the dirty files that are NOT yours and
record that you neither staged nor edited them.

**A concurrent session cannot see your restraint unless you write it down.**
The next person reading `git status` sees 28 modified files and no way to tell
which of them a careful agent deliberately did not touch.

## 3. Report the residue you created

Fixtures, captures, scratch directories, granted permissions, environment
variables, catalog rows. **You often cannot delete it** -- a device shell
cannot remove files -- and that does not excuse leaving it unnamed. Reporting
residue you cannot remove IS the deliverable.

## 4. Write the state a next session needs

Specifically: anything **time-boxed** (a grant that lapses), anything living
only in an **environment variable** (it does not travel with the repo), and
anything **green here that would be red on a clean clone**.

---

## WHY THIS IS A CONTRACT AND NOT A COURTESY

**TIDYING FINDS DEFECTS, and that is the argument for doing it as a measured
pass rather than a wave at the end.**

Worked example, 2026-09-07 (`AI_SESSION_HOUSEKEEPING_20260907_V1.md`): step 3
turned up a 56-byte table-buffer journal beside a table that had just been
erased. `ERASE` had printed `Deleted: 1, Failed: 0`, and `cmd_erase.cpp`
contains no mention of `.tbj` at all -- it sweeps `.cdx`, `.dtx` and the LMDB
environment across three roots and has never known about the WAL sidecar. The
spec recreates that table every run, so a stale journal now sits beside a fresh
same-named one.

Nobody was looking for that. It was found by asking *what did I leave behind*
and then actually looking.

It is also the house's oldest defect shape wearing a fourth verb: **a count is
a fact about a loop until something declares what it should be.** `Deleted: 1`
is true of the loop and false of the table. `WORKSPACE WRITEBACK` learned it on
a manifest, `WORKSPACE PURGE` on re-purge idempotence, `REBUILD` on a per-tag
OK line over a single container rebuild.

## WHAT A CLOSE-OUT IS NOT

- **Not a rollup of the chat.** The chat is never the record (seed section 5).
  Evidence not captured when it was produced is not proven.
- **Not an assertion that things are clean.** "I tidied up" is a claim. The
  four checks produce findings, and a close-out with no findings should say so
  having looked, not by omission.
- **Not permission to delete.** Residue is REPORTED. Removing another
  session's artifacts, or 212 MB of accumulated scratch, is the owner's call.
