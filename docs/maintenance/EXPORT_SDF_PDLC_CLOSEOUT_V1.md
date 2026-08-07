# EXPORT SDF PDLC Closeout v1

Status: closed development slice.
Ticket: AIF-069.
Owner: member.derald.
Steward: member.ai.codex.
Date: 2026-07-27.

## Scope

This PDLC slice adds `EXPORT ... SDF` as a fixed-width, schema-aligned output
format. It reuses the existing `TUPTALK PUSH ROW` row semantics so fixed-width
record construction has one source implementation.

Closed here:

- `EXPORT TO <file> SDF` writes fixed-width rows with no header row.
- Missing `.sdf` extension is appended for SDF output.
- CSV and PIPE export behavior remains in place.
- `TUPTALK PUSH ROW` and `EXPORT SDF` share `cli::fixed_width::build_schema_aligned_row`.
- HELP/DOTREF usage text exposes `CSV|PIPE|SDF`.
- A focused `REGRESSION RUN EXPORT_SDF` proof exists.

Not closed here:

- SDF import/readback.
- A full external SDF interoperability suite.
- Traditional xBase memo/index compatibility.
- Physical index rebuild policy for exported data.

## Authority Chain

Runtime/source anchors:

- `src/cli/cmd_export.cpp`
- `include/cli/fixed_width_row.hpp`
- `src/cli/cmd_tuptalk.cpp`
- `src/help/helpdata_messages.cpp`
- `include/dotref.hpp`
- `src/cli/cmd_regression.cpp`
- `dottalkpp/data/scripts/export/export_sdf_regression.dts`

Portal and closeout anchors:

- `docs/maintenance/SESSION_CLOSEOUT_EXPORT_SDF_PDLC_2026-07-27.md`
- `labtalk/proofs/runs/20260727_export_sdf_regression.txt`
- `labtalk/registries/ai_portal_tasks.yaml`
- `labtalk/registries/ai_runs.yaml`
- `labtalk/registries/proofs.yaml`

## PDLC Record

### Analyze

`cmd_export.cpp` already supported CSV and pipe-delimited output. The missing
flat fixed-width export format was SDF. The runtime already had a fixed-width
row builder in `TUPTALK PUSH ROW`, so the right reuse point was the row
formatter, not a second hand-coded exporter.

### Design

The design is a narrow additive format:

- Parse `SDF` as an `ExportFormat`.
- Preserve CSV/PIPE header behavior.
- Write SDF as records only, one schema-width row per DBF record.
- Align numeric, float, and currency fields to the right.
- Align all other fields to the left.
- Trim trailing spaces from stored field values before padding.
- Use the same helper from `TUPTALK PUSH ROW` and `EXPORT SDF`.

### Code

Implementation files:

- `include/cli/fixed_width_row.hpp` introduces the shared row formatter.
- `src/cli/cmd_export.cpp` adds `SDF` parsing, extension handling, and row writes.
- `src/cli/cmd_tuptalk.cpp` delegates `PUSH ROW` to the shared helper.
- `src/help/helpdata_messages.cpp` updates `EXPORT` usage text.
- `include/dotref.hpp` updates the quick command reference.
- `src/cli/cmd_regression.cpp` registers the focused regression script.
- `dottalkpp/data/scripts/export/export_sdf_regression.dts` exercises the format.

### Test / Debug

Build proof:

```powershell
cmake --build D:\code\ccode\build --target dottalkpp --config Debug
```

Runtime proof:

```powershell
.\datarun.ps1 -CommandLines "REGRESSION RUN EXPORT_SDF"
```

Observed output:

- `REGRESSION: running EXPORT_SDF`
- `Exported 2 records to tmp\export_sdf_regression.sdf`
- Row 1: `AB    7  12.3T`, length 14
- Row 2: `WXYZ123  -4.5F`, length 14

The generated temporary SDF proof output was inspected and then removed from the
runtime temp directory.

### Document

The slice is documented in:

- This PDLC closeout.
- `docs/maintenance/SESSION_CLOSEOUT_EXPORT_SDF_PDLC_2026-07-27.md`
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`
- Portal task/run/proof registries.
- Runtime HELP/DOTREF usage text.

### Maintain

Future gates should stay separate unless explicitly pulled into scope:

- Add SDF import/readback proof if SDF becomes a round-trip contract.
- Add an in-engine file assertion command if regression scripts need to verify
  exact file bytes without external inspection.
- Decide whether SDF belongs in the historical database migration lane as a
  COBOL/fixed-record bridge.
- Keep x32 traditional index/memo compatibility in AIF-068, not implied by SDF.

## Closure Decision

AIF-069 is closed as a runtime-observed development slice for SDF export. The
feature is build-proven, regression-proven, documented in command help, and
registered in the AI Portal. Broader flat-file import/export strategy remains
open by explicit future gates.
