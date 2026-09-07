// @dottalk.file v1
// subsystem: docs
// layer: finding
// project: project.x64base.runtime
// lane: AIF-156
// owner: member.derald
// status: review-needed

# HOUSEKEEPING, 2026-09-07 -- AND THE DEFECT IT FOUND

    Head    : b58fef3e6
    Commits : nine, all green, all review-needed
    Author  : member.ai.claude.cowork

Written because a tidy-up found something, which is the usual reason a
housekeeping note is worth keeping rather than performing.

## 1. ERASE REPORTS COMPLETE SUCCESS AND LEAVES THE WAL SIDECAR

`PKPOLICY` ends with `ERASE TABLE PKPOL CONFIRM`. It printed:

    ERASE: deleting 1 file(s) for table: PKPOL
      Deleted: PKPOL.dbf
    ERASE complete. Deleted: 1, Failed: 0

and left a 56-byte table-buffer journal beside it -- `PKPOL.dbf.tbj` under the
sandbox DBF root.  <!-- cite-check:ignore -->

`grep -n "tbj" src/cli/cmd_erase.cpp` returns **NOTHING**. ERASE sweeps
same-stem `.cdx`, `.dtx` and the LMDB environment across the DBF, INDEXES and
LMDB roots, and has never known about the TBJ1 journal at all.

**WHY THIS IS MORE THAN UNTIDINESS.** `PKPOLICY` recreates `PKPOL.dbf` from
scratch on every run, so a STALE journal now sits beside a FRESH same-named
table. That is the residue-replay shape, and it is the same family as the
finding that a `.__fldbak` scratch file sorted ahead of its real table and took
area 0.

**NOT MEASURED, and it must not be assumed either way:** whether the TBJ1 layer
would actually replay an orphaned journal against a new table of the same name.
What IS measured is that the file survives an erase reporting complete success.

**IT IS THE COUNT DISCIPLINE IN A FOURTH VERB.** `WORKSPACE WRITEBACK` taught
that *a count is a fact about a loop until something declares what it should
be*; `WORKSPACE PURGE` re-learned it on re-purge idempotence; `REBUILD` reports
OK once per tag over a single container rebuild. Here `Deleted: 1` is true of
the loop and false of the table.

Not fixed in this session: it is CLI-tree code and wants its own go, a build
and a run.

## 2. GOOD-NEIGHBOUR -- identity DATA is tracked while identity SOURCE is being edited

Commit `2fa18b88b` tracked the ten `SYS*` identity tables in the runtime identity
metadata directory, on an owner ruling. At that moment the
concurrent session had `src/cli/cmd_user.cpp`, `src/identity/identity_admin.cpp`,
`src/identity/identity_bootstrap.cpp`, `src/identity/identity_dbf_store.cpp` and
six identity headers dirty -- **the code that writes those
tables is under active change while their bytes are now version-controlled.**

Two couplings that did not exist before that commit:

- **A schema change now has a data half.** Add or reorder a column and the
  tracked DBFs go stale; `USER SAVE` rewrites them into a diff.
- **`USER SAVE` is now a tracked-file mutation.** Running it shows ten modified
  files in `git status`.

Nothing is broken. The person holding identity source should know before their
next commit.

## 3. A CREDENTIAL COLUMN THAT IS EMPTY TODAY

`SYSUSER.dbf` carries a `CRED` column. It was verified empty before staging --
zero hash-shaped runs in the record area, consistent with the login banner's
own "bootstrap: no password set". **The moment anyone runs `USER PASSWD` that
column holds a credential hash and every clone gets it**, and
`include/identity/identity_admin.hpp` documents the hash as local
obfuscation-grade, non-cryptographic and explicitly not for hostile networks --
which makes publishing it worse rather than safer.

Nothing in the tree will notice the transition: no gate reads DBF field
contents, and the file changing is indistinguishable from any other identity
edit. Raised for an open-item number.

## 4. SCRATCH ACCUMULATION -- reported, not actioned

The runtime TMP root holds **212 MB** in **329 `wscat_run_*` directories**, one
per bracketed regression run since the L2 catalog bracket landed. It is
gitignored (`.gitignore` line 72), so there is no tracking cost -- disk only,
and nothing prunes it. If it should be pruned, the bracket is the natural place
to do it from, keeping the last N runs.

## 5. WHAT WAS DELIBERATELY NOT TOUCHED

- `.gitignore` -- standing rule.
- `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` -- agents do not write to it.
- The publication staging tree -- never without instruction.
- The concurrent session's 28 modified files: none staged, none touched.
- The four `_pre_*_backup_*` directories beside the identity tables. Migration
  residue, excluded from the tracking commit on purpose: a backup tracked
  beside the thing it backs up is how a restore later reads the wrong file.

## 6. STATE A NEXT SESSION NEEDS

- **`member.ai.regression` holds `host.shell`, granted +24h from ~14:00 on
  2026-09-07.** After it lapses `REGRESSION PKDURABLE` reports an unrun
  measurement rather than a pass -- the correct resting state, not a
  regression. Re-grant with `USER GRANT host.shell TO member.ai.regression`
  followed by `USER SAVE`.
- **`DOTTALK_ALLOW_HOST_COMMANDS=1` is required in the environment as well as
  the grant.** For `host.*` the resolver folds the host-command policy in as a
  final, independent stage. The grant travels with the repo; the variable does
  not. Measured the same day: with the grant stored,
  `USER CAN host.shell FOR member.ai.regression` still read
  `DENY (denied by runtime security policy (final))` until it was set.
