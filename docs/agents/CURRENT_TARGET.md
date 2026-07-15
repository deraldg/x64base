# Current Target

Status: **active — review branch prepared**.
Updated: 2026-07-15.
Public baseline audited: `b9d480215c036178ba99b5109a8a2489ee89b215` on `main`.
Review branch: `ai-portal-consistency-20260715`.

## Authority Restatement

```text
D:\code\ccode              authoritative development source and runtime truth
C:\x64base                 disposable curated publication staging
github.com/deraldg/x64base public snapshot
```

`C:\x64base` is a promotion gate generated from the public baseline plus the
reviewed paths selected from development. It is not a backup, a second source
authority, or the place for original implementation work.

## Current Task

Reconcile the public AI-facing state after the 2026-07-15 cold-clone fixes were
published to `main`.

The correction is documentation-only and addresses:

1. stale publication-pending statements;
2. an obsolete current objective and staging HEAD;
3. a duplicate AI intake ID;
4. dashboard buckets that disagree with the intake queue;
5. development-only edition proof being described without a public-source
   qualifier;
6. multiple competing onboarding orders.

No runtime behavior, build configuration, source code, HELP data, fixtures,
indexes, generated catalogs, or branch history is changed by this task.

## Entry State

Public `main` contains four commits after the prior `2675cdcd` baseline:

| Commit | Public effect |
| --- | --- |
| `fcac7f3b` | Added the build front door, promotion model, contracts, proof records, and staging tooling. |
| `730434d2` | Corrected `BUILDING.md` to describe only presets present on public `main`. |
| `46e02159` | Published the self-contained cold-clone launcher and MCC databuild corrections. |
| `b9d48021` | Corrected the printed DotScript annotation from invalid `<-` syntax to `&&`. |

The full cold-clone path is public and certified for `pro-md`:

```text
clone -> configure/build -> datarun -> MCC databuild -> LMDB -> ordered query
```

The larger product/index edition system remains implemented and proven in the
authoritative development lane but is not yet present as public edition presets
on `main`. `BUILDING.md` is the public authority for what a fresh clone can run.

## Previous Target — Resolved

The previous target was to restore `C:\x64base` to clean staging, prove the MCC
databuild lane, and publish the first clean correction set. That work was
completed on 2026-07-14 and followed by the cold-clone publication on
2026-07-15.

The old recorded staging HEAD `a625ea1d` and the old “first clean PR” steps are
historical state, not current instructions. Their detailed evidence remains in:

- `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md`
- `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md`

## Do Not Touch

- Do not clean, reset, or broadly stage `D:\code\ccode`; a dirty development tree
  is normal and is not a release-risk signal.
- Do not make original runtime/source changes in `C:\x64base` or on GitHub.
- Do not mutate DBF/CNX/CDX/LMDB data, HELP tables, metadata catalogs, generated
  catalogs, publications, fixtures, backups, or archives unless a task names
  that mutation explicitly.
- Do not create, switch, rename, delete, or force-update branches without
  explicit maintainer authorization.
- Do not describe development-only source as present on public `main`.

## Proof Required for This Target

- Compare the correction branch against `main`; only the declared AI-facing
  Markdown/YAML state files may change.
- Confirm every historical closeout remains historical; publication outcomes are
  appended rather than rewriting the original session account.
- Confirm `AI_README.md`, `AI_PORTAL.md`, and `labtalk/ai_portal/README.md` point
  to one canonical onboarding order.
- Confirm every `AIF-*` intake ID is unique.
- Confirm dashboard bucket summaries agree with the intake queue.
- Confirm edition statements distinguish authoritative-development proof from
  public-source availability.

## Next Gate

Review and merge the documentation-only correction branch. After merge, reconcile
the same state in authoritative development if it is not already present there.
The next runtime assignment is not implied by this document; it begins only when
the maintainer assigns it and the applicable contract preflight is complete.
