# Full-stack documentation flush v4 -- next-push continuation

Run: `DOCFLUSH-20260805-001`
Lane: `full_stack_documentation`
Recorded: 2026-08-05
Steward: `member.ai.claude.cowork`
Owner: `member.derald`
Status: **Phases 0.5 -> 4 + catalog derivative COMPLETE and committed; paused for the next push.**

## Done this push (clone-verifiable on `development`)

- Phase 0.5 contract coverage: `source_census` 100%; `command_catalog_sync check`
  fallback 0 (DDICT normalized to `// @dottalk.usage`).
- Phase 1 reference crosswalk + Gate 1 disposition:
  `PHASE1_GATE1_REFERENCE_DISPOSITION_RECORD_V1.md` (deferred items -> AIF-088).
- Phase 2 pre-refresh baseline + Gate 2 review: `RUNTIME_BASELINE_REVIEW_V1.md`
  (commit `c4c3a6bd9`). Reflection PASS, manual 8/8, 28,368 line rows / 525 topics.
- Phase 3 authorized HELP refresh package: `help_refresh/HELP_REFRESH_PACKAGE_V1.md`.
- Phase 4 build + Gate 4 validation: `help_refresh/GATE4_REFRESH_VALIDATION_V1.md`
  (commit `0225103fb`). LEGACY rebuilt with the foxref dedup reflected; primary
  HELP DATA idempotent; reflection PASS.
- Website catalog derivative: `command-catalog.mdx` regenerated, DDICT now curated,
  fallback 0 (site repo commit `568de1ae6` on `codex/lean-sites-publish`).

## Current engine/doc state (start-of-next-push facts to re-measure, not trust)

- HELP DATA store current with source: `CMDHELP` 28,368 line rows / 525 topics;
  DOTREF 895, FOXREF 665, REGISTRY 461; `CMDHELPCHK` structural PASS; blank
  artifact texts 0; artifact_orphan_cmdkey_rows 978.
- Runtime identity at capture: `dottalk++ v0.6 (2026-08-05, 5928e2eb dirty)`.

## Resume here (next push)

1. **Phase 5 Metadata (candidate-only)**: run `metacollect`; store SYSFUNC/SYSARGS
   compare + candidate CSVs as candidates; update SelfDoc provenance. Do NOT import
   candidates into live metadata without a separate reviewed gate.
2. **Phase 6 Manual candidate**: `tools/manualgen/manualgen.py --manual developer`
   inventory -> validate -> export-manifest -> build-dry-run (candidate only).
3. **AIF-088 (deferred cleanup lane)**: source-comment ASCII sweep (em-dash -> `--`;
   the `cmd_buildvectors.cpp:21` mojibake proven in the Phase 2/4 HELP output),
   EXAMPLE + SQLHELP duplicate registrations, PSHELL duplicate contract, and the
   crosswalk registry-scan comment-strip fix.
4. **AIF-067 (deferred)**: dotref-automation M2/M3.

## Retired footguns / recipes (carry into the next push)

- Replay an existing `.dts` with `./datarun.ps1 -CommandLines (Get-Content "<ABS>.dts")`;
  `-Script` / exe `--script` pass-through does NOT work through datarun.
- Use ABSOLUTE paths everywhere; datarun pushes cwd to the data root.
- `command_catalog_sync.py` needs Python 3.12 on the host: `py -3.12 ...`.
- A dotref.hpp change requires `CMDHELP BUILD LEGACY` then `CMDHELP BUILD . <ABS src>`
  (foxref feeds LEGACY). Back up `dottalkpp/data/help` first; the daemon locks the
  store (Stop-ScheduledTask `DotTalkBBSD`).
- Sandbox agents: no git, no build; prepare host commands.

## Side note (parked, NOT part of this push)

The AI Systems Integration detour is parked under AIF-086 with stewardship
recorded; see `docs/maintenance/SESSION_CLOSEOUT_AI_SYSTEMS_INTEGRATION_SDLC_2026-08-05_CLAUDE_STEWARD_M2.md`.
It is a separate lane and does not gate the full-stack push.
