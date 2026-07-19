# Promotion Model Seed v1 — Dev is Authority, Staging Is Recoverable

Status: **active; recovery amendment applied 2026-07-18** — governs the dev ->
staging -> github relationship.
Created: 2026-07-14.
Companion to: `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` (which declares the chain;
this seed declares how the chain is *mechanically* maintained).

## The problem this solves

Two failure modes kept recurring:

1. **Staging gets wiped by AI.** `C:\x64base` is treated by agents as scratch
   and is frequently reset or cleaned. If it were precious, that would lose
   work.
2. **The public baseline was treated as if GitHub were its only necessary
   recovery source.** That missed public-package files absent from development
   and uncommitted staging work awaiting reconciliation.
3. **The `.gitignore` was being asked to do two jobs.** People reached for it
   both to say "never version this" and to say "this doesn't publish yet."
   Those are different questions and one file cannot answer both.

## The model

```text
D:\code\ccode      THE git repository. Source of truth. Full history. Holds
                   everything, including lanes not yet published.
       |
       |  .gitignore         deny-list: never version this (LMDB, *.exe,
       |                      sidecars, scratch). Universal.
       |
       |  PROMOTE.manifest    allow-list: of the clean files, THESE publish.
       |                      Selective. Small, because staging holds little.
       v
C:\x64base         RECOVERABLE staging. A build output, not a second authority.
                   = verified public baseline + preserved dirty and ignored
                   layers + an authorized development overlay. Regenerated
                   only from a hash-bound recovery escrow.
       |
       |  offline recovery mirror
       v
C:\code\ccode      Local recovery copy of the escrow. Not development authority
                   and not a place for original source work.
       |
       |  git commit + push   (a reviewed human step)
       v
github.com/deraldg/x64base    public snapshot
```

## Two filters, never merged

| Filter | Question | Shape | Scope |
| --- | --- | --- | --- |
| `.gitignore` | "Should this be version-controlled anywhere?" | deny-list | universal |
| `PROMOTE.manifest` | "Of the clean files, does this publish now?" | allow-list | selective |

A file can be **git-tracked in development but absent from the manifest** — a
lane that is versioned but not yet published (sandbox, messaging, metadata,
selfdoc, datadict, ...). That is normal and intended. Do not add a lane to the
manifest to "tidy up"; add it when it is genuinely ready to publish, with its
own environment.

Why the manifest is an allow-list and not a "stageignore" deny-list: staging
holds far less than development. A deny-list would be "everything except..." —
enormous and fragile. An allow-list of what publishes is short and honest.

## The manifest does NOT carry engine source

`PROMOTE.manifest` publishes the **curated, stable data and documentation
projection**: fixtures, the databuild lane, docs, portal seeds, tools. It does
**not** carry `src/`, `include/`, `CMakeLists.txt`, `CMakePresets.json`, or
`vcpkg.json`.

This is deliberate, and it is a safety boundary, not an oversight:

- `rebuild-staging.ps1` overlays development's **current file state** onto a
  clone of `main`. Development's working tree is the messy authority — it can
  hold hundreds of uncommitted, experimental changes at any moment. Overlaying
  `src/` from there would push half-finished engine source to `main`.
- Source must be **coherent and build-tested** to publish. A build system is
  all-or-nothing: presets, `CMakeLists.txt`, and the `src/` guards they depend
  on must travel **together** or the clone will not build. An overlay of "dev's
  current source" cannot guarantee that.

Therefore engine source and build configuration reach `main` the normal way:
**a git branch off `main`, the coherent changeset applied, a cold-clone build
to certify, then merge.** The manifest is for the projection; git is for the
engine.

Consequence for documentation: a doc that *describes* source (like
`BUILDING.md`) travels through the manifest, but the source it describes travels
through git. They can therefore fall out of step — the doc can reach `main`
before the source it documents. Always ground a published doc against what is
actually on the publication target (`main`), proven by a cold clone, not against
development. See `LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` -> "Publishing
documentation".

## Does development need a git state?

**Yes.** github/main holds only the *promoted subset*. The unpublished lanes
exist only in development. If development's working tree is lost and it has no
history, those lanes are gone and github can restore only the sample repo —
which inverts the authority chain (authority restored from snapshot).

Development is the one authority that must be durable. Version it and back it
up. Staging does not become a second authority, but its exact committed baseline
and any dirty or ignored layer must be escrowed before destructive
regeneration. GitHub is a public recovery source, not the only recovery source.

## Regenerating staging

```powershell
# after creating and verifying the public-baseline escrow:
.\tools\staging\rebuild-staging.ps1 -Fresh -Execute `
  -RecoveryManifest <public_baseline_escrow_manifest.json>
```

That verifies the offline bundle, tar snapshot, baseline/public-only ledgers,
dirty/ignored-state preservation, and publication plan; confirms that staging
and the fetched `origin/main` still match the escrowed commit; restores both
local layers;
then overlays every file matched by `PROMOTE.manifest` from development. The
`.gitignore` deny-list remains a hard guard. Commit and push stay a separately
reviewed human step.

## Rules for an AI working this chain

- Do not treat `C:\x64base` as authority or as a place to make original changes.
  If original or unreconciled work is found there, preserve and disposition it
  before regeneration; do not erase it merely because the lane is staging.
- Do not run `-Fresh -Execute` without the matching public-baseline escrow. The
  rebuild tool must fail closed when the escrow is absent, stale, or incomplete.
- Keep `C:\code\ccode` as a labeled recovery mirror only. Its existence does
  not change `D:\code\ccode` authority or authorize bidirectional source edits.
- Do not merge the two filters. If asked to "make X not publish," decide whether
  it means "never version" (`.gitignore`) or "not yet published" (remove from
  `PROMOTE.manifest`).
- To publish new work: commit it in development, add its paths to
  `PROMOTE.manifest`, run `rebuild-staging.ps1`, review the diff, commit and push
  from staging.
- Wiping or resetting staging is safe and expected. Wiping development is not;
  development is authority.
