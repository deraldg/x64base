# Cascade ERP Gate 0 Housekeeping V1

    status      : active admission ledger; local only
    lane        : AIF-105
    owner       : member.derald
    steward     : member.ai.codex.local
    updated_utc : 2026-08-10T00:00:00Z

## Purpose

Define what must be reviewed, admitted, regenerated, retained locally, or
deferred before Cascade ERP or its case-study teaching surface can be called
clean-checkout durable. This ledger authorizes no Git staging, deletion,
promotion, publication, or database mutation.

## Housekeeping decisions

| Surface | Current state | Housekeeping disposition | Gate |
| --- | --- | --- | --- |
| `coordination/aif/AIF-105.claim` | local, untracked | Admit with the AIF-105 slice after claim/row reconciliation. | Claim file and intake row agree. |
| AIF-105 charter and this ledger | local, untracked | Admit as governing design records. | ASCII, links, owner/steward/coworker, and truth states reviewed. |
| AIF-105 intake and project rows | tracked files, locally modified | Admit only with the exact AIF-105 slice. | Claim validator and YAML parse pass. |
| Historical migration `AIF-058` labels | collision with AI roles taxonomy | Quarantine as a legacy label; use no new AIF number without the atomic allocator. | No active Cascade record claims AIF-058. |
| Cascade README, manifest, checksums, schema, seed, dump, queries, and 34 CSVs | local, untracked | Review as the sealed V1 admission package. | Checksums, row counts, schema rebuild, rights, and provenance pass. |
| `cascade_precision_mfg_erp.sqlite` | local, ignored carrier | Keep untracked and reconstruct from admitted schema/seed inputs. | Rebuilt carrier matches the accepted semantic/schema/data digest policy. |
| Neutral logical schema | not yet accepted | Generate a candidate, review every semantic mapping, then admit one versioned authority. | SQLite and x64base are projections of the same accepted contract. |
| Mirror generator and tests | local, untracked | Review for admission after portability, stale-output, and semantic tests are added. | Determinism and known-bad tests pass in a clean temporary root. |
| PowerShell mirror runner | local, untracked | Retain as a convenience wrapper only; move proof logic to cross-platform Python before admission. | Wrapper delegates; proof logic is tested and platform-neutral. |
| Generated contract, 43 schema JSON files, view CSVs, and build script | local, untracked derivatives | Regenerate from admitted inputs; decide tracked-versus-build-output policy after deterministic diff proof. | Two runs are byte-identical and stale extras fail. |
| 43 x64base DBFs and sidecars | local runtime outputs | Do not admit as source authority. | Rebuild into an empty target and verify headers, values, NULLs, indexes, relations, and views. |
| Three structural mirror transcripts | local, untracked | Preserve the latest as review evidence; classify earlier attempts as superseded before any admission. | Receipt says structural only and cites exact binary/input identities. |
| Primary 16-case registry | registry tracked; 15 content files untracked | Review ownership and provenance, then admit the intended 16-file canonical corpus. | Fresh checkout contains every registry target. |
| Secondary 22-file case tree | local, untracked divergent catalog | Keep out of runtime discovery; classify unique legacy cases as intake candidates or archive them after owner review. | No cwd-dependent runtime authority remains. |
| `launch-common.ps1` | local, untracked dependency of tracked launcher | Review and admit with launcher ownership, or remove the dependency through a separately proven launcher change. | Fresh checkout launcher works from supported cwd values. |
| LabTalk Cascade portal section | tracked files, locally modified | Keep candidate/structural wording until captured proof and registry work are complete. | Portal cannot display PASS merely because it launched a process. |
| x64base-site case/story pages | separate website checkout | No housekeeping mutation in this lane. | Publication consumes only reviewed export records and a source digest. |

## Immediate Gate 0 checklist

1. Review the exact untracked source/package/case/launcher paths with the owner.
2. Stage or commit nothing implicitly; use named paths only after review.
3. Rebuild the SQLite carrier from admitted inputs in a temporary directory.
4. Prove the expected carrier and package digests.
5. Prove that every canonical case registry target exists in a clean checkout.
6. Prove that the normal launcher has no untracked dependency.
7. Run YAML, AIF-claim, portal-path, ASCII, and generated-output drift checks.
8. Record the accepted, deferred, superseded, and local-only sets in the AIF-105
   closeout before any runtime, UI, or publication truth state advances.

## Current boundary

The local system contains valuable implementation candidates and observed
structural evidence. None of the untracked surfaces above is durable repository
evidence. This housekeeping pass changes labels and records admission decisions;
it does not admit the files or upgrade their proof state.
