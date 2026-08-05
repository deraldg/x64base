# Runtime baseline review v1

Run: `DOCFLUSH-20260805-001`
Gate: 2, source-to-HELP disposition (full-stack doc flush v4)
Recorded: 2026-08-05
Decision: `PASS_BASELINE_ONE_DEFERRED_ASCII_FINDING`

## Bound evidence

- Script: `fullstack_pre_refresh_runtime_v1.dts`
- Script SHA-256: `66049E12F972922CE549508B9AADB701A8A73EBB5AEC60B731D55D3D0276CA65`
- Transcript: `fullstack_pre_refresh_runtime_v1.txt` (2,969 lines)
- Transcript SHA-256: `86A53773A990C42C3A2DBAE56C31DED669993F5416DCECB4F653DC979252FACD`
- Runtime: `D:\code\ccode\dottalkpp\bin\dottalkpp.exe`
- Runtime identity: `dottalk++ v0.6 (2026-08-05, 5928e2eb dirty)`
- Runtime SHA-256: `FF5B05FAB86967DCB955430648306CC77215A79F12B364D57B1F684DFF9E7A94`
- Result: exit 0.
- Data root: `D:\code\ccode\dottalkpp\data`.

## Proven current behavior

- `CMDHELP` reports 28,368 HELP DATA line rows and 525 topics (v4: up from the
  20260722 baseline's 12,784 / 492, reflecting the contract harvest + dotref adds).
- `CMDHELPCHK` reflection structural status: PASS.
- HELP artifact rows: 14,229; blank artifact texts: 0; compact-SET errors: 0.
- Manual catalog present with all 8 expected MAN* tables.
- Misspelling recovery active (HELP GAINT -> GIANT).
- Targeted topic checks captured for this pass's changes (confirm resolved in the
  transcript): `CMDHELP BBS / NET / CANARY / CMDREL / FORMULA / EDIT / DDICT /
  EVALDIFF / BUILDVECTORS`.

## Findings

1. Deferred (cosmetic, not perfection-blocking) -- source-comment non-ASCII surfaces
   as HELP mojibake. Example: `cmd_buildvectors.cpp:21` SUMMARY carries a U+2014
   em-dash (`(AIF-044) -- the selected ...`) that renders as a 3-char garble
   (the U+2014 bytes read as CP437) in HELP output.
   The sweep found ~20+ `src/cli` files with non-ASCII in comments/contracts; the
   house-style gate only checks added lines, so this is a historical backlog. A
   dedicated source-comment ASCII sweep (`--` / `->`) is warranted as its own pass.
   Recorded on the AIF-088 worklist.
2. Informational -- `artifact_orphan_cmdkey_rows: 981` (HELP artifact keys with no
   current command-key match). Pre-existing; not gated; carry forward for the
   metadata/HELP reconciliation phases.

## Gate 2 disposition

PASS. The pre-refresh baseline is captured, exit 0, reflection PASS, manual catalog
complete, and the v4 contract/reference changes are materialized (catalog fallback
0). The one source finding (comment ASCII) is cosmetic and deferred; it does not
block the refresh. Assign any per-topic HELP miss found in the transcript to its
layer before Phase 3.

## Note (process)

`datarun.ps1` leaves the session in `dottalkpp\data`; the baseline recipe must use
ABSOLUTE paths for the transcript and summarizer (and `Set-Location` back to the
repo root before summarizing). Fold this into the flush plan's Phase 2 recipe.
