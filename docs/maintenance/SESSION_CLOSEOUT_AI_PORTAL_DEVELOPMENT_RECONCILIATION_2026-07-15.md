# Session Closeout — AI Portal Development Reconciliation (2026-07-15)

Status: **development reconciled; disposable staging projected and verified; reviewed commit/push pending.**

## Purpose

Bring the public AI Portal corrections from `main` back into authoritative
development without treating the public snapshot as authority and without
overwriting newer local lane state. Then project the reconciled result through
`C:\x64base` using the declared development -> staging -> GitHub flow.

## Baselines inspected

| Surface | State at inspection |
| --- | --- |
| Authoritative development | `D:\code\ccode`, branch `homegrown-cnx-20251112-branch`, HEAD `fecc3951ef1144301a0da7b0e948911de5d4ba68`, dirty working tree preserved |
| Public GitHub main | `fa7c04dcea07a2f0b5a027fba7bc953651cd83df` |
| Disposable staging before first rebuild | `b9d480215c036178ba99b5109a8a2489ee89b215`, three public commits behind |

## Why a direct copy was rejected

The public consistency audit correctly resolved the duplicate AIF-014 by using
AIF-017 for manual drift. While that public-only work was happening,
authoritative development advanced:

- AIF-017 became the Pinocchio stress-test lane.
- AIF-018 became the Messaging Normalization lane.
- Pinocchio Phase 1 passed at 1M STUDENTS / 5.5M ENROLL and gained a closeout.

Copying the public queue back wholesale would therefore erase newer development
facts and create a new duplicate identifier.

## Reconciled result

- AIF-014 remains the xbase/xindex proof lane.
- AIF-015 distinguishes proven development editions from the older public build
  surface pending Path A.
- AIF-016 records the completed cold-clone publication in `46e02159` and
  `b9d48021`.
- AIF-017 remains Pinocchio.
- AIF-018 remains Messaging Normalization.
- AIF-019 is the developer-manual edition-drift candidate.
- `AI_README.md` is the single canonical startup path and no longer freezes a
  transient development branch name.
- Historical closeouts preserve their session-close state and carry append-only
  publication/reconciliation updates.
- Dashboard and current-target records now describe the same lane state.

## First staging rebuild and correction

The maintainer ran:

```powershell
.\tools\staging\rebuild-staging.ps1 -Fresh -Execute
```

It correctly fetched public `fa7c04dc`, cleaned the disposable tree, and
overlaid 210 manifest files. Because development had not yet been reconciled,
that first overlay reintroduced the stale static branch pointer, duplicate
AIF-014, and pending-publication text. No staging commit was made. The diff was
used as the reconciliation map.

The prohibited-artifact filename scan on that first overlay returned `NONE`.
The rebuild also removed the untracked website mirror and `TEST64.dbf`, as the
`-Fresh` clean contract specifies.

## Final staging projection

After development reconciliation, staging was rebuilt again from public `main`
plus the corrected manifest overlay. The rebuild overlaid 212 files (41.73 MB)
and remained on `main` based on public `fa7c04dc`.

Verification passed:

- no static `homegrown-*` branch instruction;
- exactly one each of AIF-001 through AIF-019;
- AIF-016 publication complete;
- public consistency closeout present with the development update;
- no `.cdx.d`, LMDB, `.mdb`, `og/`, or `.exe` paths in the staging candidate
  set;
- development and staging SHA-256 hashes match for all ten reconciled portal
  files;
- no staging commit or push was performed.

The real staging delta also carries the already-manifested Pinocchio plan,
scripts, Phase 1 closeout, and related contract-intake findings. Review that
published scope together with the portal reconciliation before committing.

## Publication boundary

This closeout does not authorize an automatic staging commit or push. Those
remain the reviewed maintainer step after the final diff and leak scan.

## Separate website drift

The live quickstart correctly documents clone -> build -> databuild -> run ->
ordered query. Two website-source corrections remain separate from this repo
projection: public `main` must be described as the canonical public baseline,
not the internal development authority, and project licensing wording must be
exactly `To be determined.`
