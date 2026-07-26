---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260716-004
  recorded_at_utc: 2026-07-16T18:52:00Z
  agent:
    provider: Anthropic
    product: Claude Cowork
    model: claude-opus-4-8
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: implement and prove the canonical EXPORTFUNCTIONS I/O error identity and the cmdout failure-emission contract (emit_error), scoped strictly upstream of SET ERRORSTOP
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_EXPORTFUNCTIONS_ERROR_IDENTITY_2026-07-16.md
    kind: session_closeout
---

# Session Closeout — EXPORTFUNCTIONS error identity + cmdout failure-emission contract

Date: 2026-07-16.
Owning lifecycle: DotTalk++ SDLC.
SDLC lane: implementation + proof (Messaging Normalization / AIF-018; first ERRORSTOP-sink slice).
Truth state: source-defined, runtime-proven.
Proof state: build (green) + durable acceptance transcript.

Predecessor: `SESSION_CLOSEOUT_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md` (AIF-021)
set the boundaries this slice followed: settle the error identity and localized-emission
output contract, prove `ERROR_STATUS`, and keep `SET ERRORSTOP`, active DBF sync, and the
broader sweep out of scope.

## One-line summary

Added the first canonical `io` error code and a `cmdout` failure-emission primitive that
records the code while printing the localized diagnostic, adopted both at `EXPORTFUNCTIONS`,
and proved the identity + localized emission + `ERROR_STATUS` triple live — leaving
`SET ERRORSTOP` wiring for its own later patch.

## Source-mutation contract preflight

Recorded before mutation (expanded once, in-session, when the proof revealed a fifth file):
`docs/maintenance/PREFLIGHT_EXPORTFUNCTIONS_ERROR_IDENTITY_2026-07-16.md`.
No PROMOTED contract owns the error-code table, `set_last_error`/`ERROR_STATUS`, or `cmdout`
output; constraints came from the intake-stage ERRORSTOP + messaging rows and source
annotations. Preserved the HRESULT-style code layout (stable-ABI header comment). No HELP/
USAGE/syntax/alias/no-arg change — display text is unchanged; the new fact is recorded error
state — so no CMDHELP drift.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Canonical error identity | `include/xbase_error_codes.hpp` | Added `e_io_write_failed()` = `make_code(error, io, 0x0001)` — the first constant on the pre-existing `io` facility (0x0006) — plus its `to_string` ("I/O write failed.") and `symbol` ("E_IO_WRITE_FAILED") arms. |
| Failure-emission contract | `src/cli/command_output.{hpp,cpp}` | Added `emit_error`/`emit_warning(MessageId, xbase::error::code, vars)` = localized `print_message` + `xbase::error::set_last_error`. One localized line; the English `to_string(code)` is never the user-facing line. Added the `xbase_error_context.hpp` include. This is the lane's answer to "emit a severity/error code and a localized MessageId together" without duplicate lines or English-generic replacement. |
| Command adoption | `src/cli/cmd_export_functions.cpp` | Two failure sites now `emit_error`: write failure -> `e_io_write_failed()`, unsupported format -> existing `e_invalid_argument()`. Success path calls `clear_last_error()`. Added the context include. |
| ERROR_STATUS message mapping | `src/cli/cmd_error_status.cpp` | Mapped the io code in the command's **local** `error_to_string` (it reimplements the header mapper; the first proof surfaced "Unknown or unmapped" because of that duplication). Added a code comment flagging the local copy as a stale partial to collapse into the header mapper in a dedicated follow-up. |

## Verified (proof performed this session)

Maintainer rebuilt (`cmake --build ./build --config Release`, clean) and ran the acceptance
proof through the exact rebuilt Release executable. Retain the launcher console at
`labtalk/proofs/runs/20260716_exportfunctions_error_identity_v1.txt`.

Acceptance triple (each leg observed in the transcript):

1. **Localized emission** — `EXPORTFUNCTIONS MD docs` (targeting the existing `docs\`
   directory, which cannot be opened as a file) printed `EXPORTFUNCTIONS failed: Unable to
   open output file: docs` under en-US and `EXPORTFUNCTIONS falló: ...` under `SET LANGUAGE es`.
2. **ERROR_STATUS reports the canonical failure** — after the failure, `ERROR_STATUS` showed
   Severity error / Facility io (0x6) / Number 1 / HRESULT 0xC0060001 / Message
   "I/O write failed." (identical under es).
3. **Positive control** — default `EXPORTFUNCTIONS` wrote `.\data\docs\functions.md` and
   `ERROR_STATUS` returned to success/OK, confirming the success-path `clear_last_error()`.
   No output file was created at `docs`.

Explicitly NOT proven (out of scope, by design): `SET ERRORSTOP` halt behavior. No command
loop was changed; DotScript stop-on-error is a separate later patch.

Note on an earlier polluted attempt (pre-rebuild): a first run had inline `&& REM` comments
left on the command lines; DotTalk takes the whole line as the path, so it wrote a junk file
and the es failure was reached only by an illegal-filename accident. That attempt is reported
history, not the retained proof. The clean rebuilt run above is the proof. Housekeeping: a
stray file named `docs        && REM ...` from that attempt should be removed from
`D:\code\ccode`.

## AI-facing docs updated (AIF-006 gate)

- `docs/maintenance/MESSAGING_NORMALIZATION_LANE_PLAN_V1.md` — added the "First ERRORSTOP-sink
  vertical slice — EXPORTFUNCTIONS error identity (PROVEN)" progress entry (lane-state truth).
- `docs/maintenance/PREFLIGHT_EXPORTFUNCTIONS_ERROR_IDENTITY_2026-07-16.md` — status advanced
  to PROVEN; source-target list expanded to include `cmd_error_status.cpp` before that file
  was edited.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` — Session Log row added for this slice.

## Published

- Not promoted to `C:\x64base`, not projected to staging, not pushed to GitHub. All work is in
  authoritative development (`D:\code\ccode`) on `homegrown-cnx-20251112-branch` (working tree
  dirty over baseline `1ce8f45d`).

## Still open — for the next session

- **`SET ERRORSTOP` (its own reviewed patch).** The sink and acceptance triple are now settled,
  so the DotScript-loop change can be built and proven against exactly this `EXPORTFUNCTIONS`
  failure: `clear_last_error()` before each line, break when
  `get_last_error().get_severity() == error` (or `>= warning` under WARN). Default OFF.
- **Registry-wide adoption.** Only after ERRORSTOP: walk fail-capable commands onto
  `emit_error`/`emit_warning` with canonical codes. Most codes still need identities
  (the `io`/`cli`/`dbf64` tables are sparse); add them as adoption demands, never `E_UNKNOWN`
  to green a gate.
- **Collapse the duplicated mapper.** `cmd_error_status.cpp`'s local `error_to_string` is a
  stale partial copy of `xbase::error::to_string()` (missing several CLI codes); collapse it
  into the header mapper in a dedicated patch so `ERROR_STATUS` surfaces every canonical code.
- **Legacy `print_error(cmd, code)`** still prints English `to_string(code)` and records
  nothing — a latent trap with zero current callers; reconcile lane-wide.

## Provenance pointers

- Preflight/design: `docs/maintenance/PREFLIGHT_EXPORTFUNCTIONS_ERROR_IDENTITY_2026-07-16.md`
- Lane charter + progress log: `docs/maintenance/MESSAGING_NORMALIZATION_LANE_PLAN_V1.md`
- Boundaries followed: `docs/agents/HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md` (AIF-021),
  intake rows in `docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md` (ERRORSTOP design; messaging normalization)
- Retained proof: `labtalk/proofs/runs/20260716_exportfunctions_error_identity_v1.txt`
