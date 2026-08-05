# Gate 4 refresh validation v1

Run: `DOCFLUSH-20260805-001`
Gate: 4, execute HELP refresh + same-pass validation (full-stack doc flush v4)
Recorded: 2026-08-05
Decision: `PASS_ONE_DEFERRED_ASCII_DRIFT`

## Authorized mutation executed

- `CMDHELP BUILD LEGACY` -> wrote 461 command rows, 2363 arg rows.
- `CMDHELP BUILD . D:\code\ccode\src` -> re-mined the primary HELP DATA store.
- Backup taken before the build (`dottalkpp/data/help.bak-<stamp>`); rollback = restore that dir.
- No manual publication (Phase 6) or metadata import (Phase 5) bundled.

## Bound evidence (post-build capture)

- Script: `fullstack_post_refresh_runtime_v1.dts` (mirror of the Phase 2 baseline script)
- Transcript: `fullstack_post_refresh_runtime_v1.txt` (2,969 lines)
- Transcript SHA-256 (prefix): `5c12bcddafbc66e8`
- Runtime: `dottalkpp/bin/dottalkpp.exe`, identity `dottalk++ v0.6 (2026-08-05, 5928e2eb dirty)`
- Runtime SHA-256 (prefix): `b58385acc7d72cbe` (rebuilt since the Phase 2 exe; same source commit)
- Invocation: `./datarun.ps1 -CommandLines (Get-Content "<ABSOLUTE>.dts")` (the `--script`
  pass-through does not survive datarun; see the plan's retired-footgun note).

## Pre/post diff (Phase 2 baseline -> post-refresh)

| Metric | Pre (Phase 2) | Post (Phase 4) | Delta |
| --- | --- | --- | --- |
| HELP DATA line rows | 28,368 | 28,368 | 0 |
| HELP DATA topics | 525 | 525 | 0 |
| DOTREF source rows | 895 | 895 | 0 |
| FOXREF source rows | (n/a captured) | 665 | -- |
| REGISTRY source rows | 461 | 461 | 0 |
| orphan CMDKEY rows | 981 | 978 | -3 |
| Structural checks | PASS | PASS | -- |
| MAN* tables present | 8/8 | 8/8 | 0 |

The primary HELP DATA store was already current (the correction-iteration build had
brought it current), so the re-mine was idempotent -- exactly the near-zero diff the
Gate 3 package predicted. The `-3` orphan-CMDKEY drop is the only primary-store change.

## LEGACY store (the real delta this build carried)

`CMDHELP BUILD LEGACY` rewrote `commands.dbf` (461 rows) and `cmd_args.dbf` (2363 rows).
The foxref reconciliation is now reflected in the legacy/FOXHELP surface:

- FOXHELP no longer lists the five browser duplicates (`SIMPLEBROWSER/SB/SMARTBROWSER/
  SMART/SM` are DOT-native only now).
- `NORMALIZE` appears once (the foxref duplicate is gone).

This is why the LEGACY build was required, not merely provenance: foxref feeds LEGACY.

## Targeted topics (all resolve)

`CMDHELP BBS / NET / CANARY / CMDREL / FORMULA / EDIT / DDICT / EVALDIFF / BUILDVECTORS`
all return content. Multi-home topics render every home: `CMDREL` -> DOT+FOX,
`FORMULA` and `EDIT` -> DOT+FOX+EDU. `DOT|EDIT` carries the `@dottalk.external`
contract reference. Zero "No help found" in the targeted section.

## Recorded drift (deferred, non-blocking)

- Source-comment non-ASCII surfaces as HELP mojibake. Post-build HELP for
  `DOT|BUILDVECTORS` SUMMARY renders a U+2014 em-dash from `cmd_buildvectors.cpp:21`
  as a garble in the transcript (`(AIF-044) <garble> the selected ...`). This is the
  concrete, now-in-HELP-DATA proof of the class recorded on the AIF-088 worklist
  (`task.source_comment_ascii_sweep`). A one-time source ASCII sweep clears it; not
  a refresh blocker.

## Gate 4 disposition

PASS. Current and legacy outputs are distinguished (primary store idempotent; legacy
rebuilt with the foxref dedup reflected). Reader surfaces agree; the only drift is the
deferred source-ASCII mojibake, already ticketed. A green HELP build implies no manual
or metadata promotion. Phases 5 (metadata candidates) and 6 (manual candidate) remain
separate reviewed gates.
