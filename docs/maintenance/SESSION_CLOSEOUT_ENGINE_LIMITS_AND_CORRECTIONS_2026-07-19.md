---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260719-BF1
  recorded_at_utc: 2026-07-26T05:25:45Z
  agent:
    provider: not_exposed
    product: not_exposed
    model: not_exposed
    access_mode: human_operated_tool
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 156980512
  authorization:
    requested_by: maintainer
    scope: >
      Envelope reconstructed 2026-07-28 during AI-portal audit backfill
      (AIPR-20260728-002). AI-authored, human-committed (introducing commit
      156980512, 2026-07-26); original session/agent identity was not recorded and is
      marked not_exposed; access_mode human_operated_tool per
      AI_REPORT_AUDIT_CONTRACT_V1.md.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_ENGINE_LIMITS_AND_CORRECTIONS_2026-07-19.md
    kind: session_closeout
---

# Session Closeout — Engine limits raise + two corrections (2026-07-19)

```yaml
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260719-005
  recorded_at_utc: 2026-07-19T21:53:52Z
  agent:
    provider: not_exposed
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  project:
    id: project.x64base.runtime
    root: D:\code\ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 8ee746dee21c14b02eaf0398034b15634132a33f
  authorization:
    requested_by: maintainer
    scope: >
      Raise selected engine limits (work areas, x64 name ceilings, record-size
      guardrails) and fix two defects the shakedown surfaced. Original changes
      only in D:\code\ccode on the existing branch; no branch created/switched;
      not applied to C:\x64base or GitHub.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_ENGINE_LIMITS_AND_CORRECTIONS_2026-07-19.md
    kind: session_closeout
```

Date: 2026-07-19.
Owning lifecycle: DotTalk++ SDLC.
SDLC lane: implementation → proof.
Truth state: source-defined + runtime-proven.
Proof state: build + transcript.

## One-line summary

Doubled the work-area ceiling (256→512) and the x64 table/field name ceilings
(128→256), added explicit record-size guardrails (16 MiB hard ceiling + 64 KiB
soft advisory), then fixed two defects the shakedown found — a stale warning
number and a `CLOSE ALL` that closed only the current area — all built green and
proven by four teed canaries.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Work-area ceiling | `include/xbase.hpp` | `MAX_AREA` 256 → **512** (array auto-sizes; indices are `int`). |
| Record-size guardrails | `include/xbase.hpp` | New `X64_MAX_RECORD_SIZE` = 16 MiB, `X64_RECORD_SIZE_ADVISORY` = 64 KiB. |
| Name ceilings | `include/xbase_64.hpp` | `X64_TABLE/FIELD_NAME_LENGTH_MAX` 128 → **256**; defaults held at 128; `x64_*_name_fits` repointed at the ceiling. |
| Record hard guard (create) | `src/xbase/dbf_create.cpp` | Reject an x64 record wider than `X64_MAX_RECORD_SIZE` before writing. |
| Record hard guard (open) | `src/xbase/dbf_file.cpp` | `checked_record_buffer_size_` refuses to allocate for a record over the ceiling. |
| Record soft advisory + name-warning fix | `src/cli/cmd_create.cpp` | `CREATE: note:` when fixed record > 64 KiB (`print_note`); **correction:** name-too-long warning now displays `X64_FIELD_NAME_LENGTH_MAX` (256), not the effective default (128). |
| CLOSE ALL fix | `src/cli/cmd_close.cpp` | **Correction:** `CLOSE ALL` now closes **every** open work area (new `close_one_area`, looped over `shell_engine()` slots, `filename()` open-truth); single-area path unchanged; `@dottalk.usage` note updated. |
| Regression canaries | `dottalkpp/data/scripts/limits/limits_max_area_shakedown.dts`, `limits_name_length_shakedown.dts`, `limits_record_advisory_shakedown.dts`, `limits_close_all_shakedown.dts`, `README_LIMITS_SHAKEDOWN.md` | Self-contained shakedowns; retained as the `LIMITS` baseline. |

## Verified (proof performed this session)

Build: `cmake --build .\build --config Release` — green (all six edited units
compiled: `xbase.hpp`/`xbase_64.hpp` headers, `dbf_create.cpp`, `dbf_file.cpp`,
`cmd_create.cpp`, `cmd_close.cpp`).

Four teed `DOTSCRIPT TRACE` transcripts (`tmp/limits/*.log`), decisive lines:

- **max_area** — `SELECT 256/300/511` selected; `SELECT 512` → `SELECT: out of range (valid 0..511).`; `ERROR_STATUS` → OK. No crash, no litter.
- **name_length** — 130-char field name stored as authoritative x64 name (was blocked at the old 128); 260-char warning now reads *"exceeds current x64 logical field-name length **256**"* (the corrected number); all throwaways erased.
- **record_advisory** — `CREATE: note: fixed record width 69633 bytes exceeds 65536 bytes; consider memo (M) fields…`; `RECWIDE` created (record length 69633); control record got no note.
- **close_all** — tables opened in areas 5/260/400; after `CLOSE ALL`, all three `ERASE` reported `Deleted: 1, Failed: 0` (the fix; previously 5 and 260 stranded).

Honesty notes: the **16 MiB hard ceiling is not reachable from `CREATE`** (parser
caps X64 `C` at 4096 → ~512 KiB max record) — it is a programmatic/corrupt-DBF
backstop, still needing a unit test / crafted fixture. `DOTSCRIPT TRACE` does not
join `;` continuations (the interactive/datarun path does); the wide `CREATE` was
single-lined to survive TRACE.

## AI-facing docs updated (AIF-006 gate)

Intake queue row **AIF-026** added (this work). This closeout indexed in the
dashboard Session Log. No CURRENT_TARGET development-focus change (limits work is
an implementation increment within the existing runtime lane, not a lane pivot).

## Published

Not committed, not promoted. All edits are uncommitted in `D:\code\ccode` on
`homegrown-cnx-20251112-branch` atop `8ee746de`. Commit + `C:\x64base` staging +
GitHub remain the maintainer's deliberate next step.

## Still open — for the next session

Follow-ups completed later this session (dev, **build-pending** — see AIF-027 and
`RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md`):

- ✅ `LIMITS` regression suite wired — `src/cli/cmd_regression.cpp` (spec array 8→9) + `dottalkpp/data/scripts/limits/limits_all_shakedown.dts` (nested-DOTSCRIPT driver). `REGRESSION RUN LIMITS`.
- ✅ DOTSCRIPT now joins `;` continuations — `src/cli/cmd_dotscript.cpp` uses the shared `read_script_command`, which gained an optional consumed-lines counter (`src/cli/script_reader.{hpp,cpp}`) so trace line numbers stay accurate. Matches the interactive path.
- ✅ 16 MiB hard-guard unit test — `src/tests/test_x64_record_limit.cpp` + `src/tests/CMakeLists.txt` (drives `create_dbf` past the ceiling, the path the CLI parser can't reach).
- ✅ Stranded strays `AREA10.dbf`/`AREA300.dbf` removed.

Genuinely still open:

- **Commit + promote** once reviewed (targeted `git add`, not `-A`). Full changeset now: `include/xbase.hpp`, `include/xbase_64.hpp`, `src/xbase/dbf_create.cpp`, `src/xbase/dbf_file.cpp`, `src/cli/cmd_create.cpp`, `src/cli/cmd_close.cpp`, `src/cli/cmd_regression.cpp`, `src/cli/cmd_dotscript.cpp`, `src/cli/script_reader.{hpp,cpp}`, `src/tests/{test_x64_record_limit.cpp,CMakeLists.txt}`, plus `dottalkpp/data/scripts/limits/**` and the closeout/intake/lane docs.
- **Rebuild + re-prove the follow-ups**: `REGRESSION RUN LIMITS` drives all four canaries; a multi-line `;` `CREATE` survives DOTSCRIPT TRACE; `ctest -R dottalkpp_x64_record_limit_test` is green.
- **RECNO64 lane** — end-to-end 64-bit record-number widening (the `recno()`/`recLength()`/`cpr()` saturation audit) remains planned, not implemented. Lane at `RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md`.

## Provenance pointers

- Canaries + retention model: `dottalkpp/data/scripts/limits/README_LIMITS_SHAKEDOWN.md`
- Teed transcripts: `tmp/limits/{max_area,name_length,record_advisory,close_all}.log`
- Prior day commit (baseline): `8ee746de` (catalog drift tooling, ACID beta-1, governance)
