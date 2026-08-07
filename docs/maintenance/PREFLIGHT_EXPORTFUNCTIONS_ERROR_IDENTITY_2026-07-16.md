# Source-Mutation Preflight + Output-Contract Design -- EXPORTFUNCTIONS error identity

Status: **PROVEN. Design approved; five-file patch applied; maintainer rebuilt and ran the
acceptance proof.** `EXPORTFUNCTIONS MD docs` -> localized `EXPORTFUNCTIONS failed:` (en-US
and es) + `ERROR_STATUS` = severity error / facility io (0x6) / number 1 / HRESULT 0xC0060001
/ Message "I/O write failed."; positive control succeeds and clears. ERRORSTOP halt remains
out of scope (unproven, by design). Retain the console at
`labtalk/proofs/runs/20260716_exportfunctions_error_identity_v1.txt`.
Date: 2026-07-16T18:34:34Z.
Owning lane: Messaging Normalization (AIF-018); pairs with ERRORSTOP intake row.
Author: Claude Cowork. Scope authorized by maintainer via Codex handoff
`docs/agents/HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md`.

## 1. Required Contract Preflight (SOURCE_MUTATION_CONTRACT_GATE_SEED_V1)

```text
Source target:
  include/xbase_error_codes.hpp        (add one canonical io error code)
  src/cli/command_output.hpp/.cpp      (add emit_error/emit_warning primitive)
  src/cli/cmd_export_functions.cpp     (adopt at the two failure sites)
  src/cli/cmd_error_status.cpp         (ADDED after first proof: ERROR_STATUS uses a
                                        LOCAL error_to_string() that does not delegate to
                                        the header to_string(), so the new io code showed
                                        "Unknown or unmapped..." instead of "I/O write
                                        failed." Add the io case. Broader delegate refactor
                                        of that stale local copy -- which is also missing
                                        several CLI codes -- is deferred to its own patch.)

Owning subsystem:
  xbase error model (codes/context) + CLI output routing (cmdout) + EXPORTFUNCTIONS command.

Contracts read:
  docs/contracts/README.md
  docs/contracts/CONTRACT_REGISTRY_V1.md
  docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md  (ERRORSTOP design row L48; messaging-normalization row L49)
  docs/maintenance/MESSAGING_NORMALIZATION_LANE_PLAN_V1.md  (messages-vs-data boundary; RUNTIME:/COMMAND: owner rule)
  source: include/xbase_error_codes.hpp, include/xbase_error_context.hpp,
          src/cli/command_output.{hpp,cpp}, src/cli/cmd_error_status.cpp,
          src/cli/cmd_export_functions.cpp, @dottalk.usage block in cmd_export_functions.cpp

Contract evidence states:
  No PROMOTED contract owns the error-code table, set_last_error/ERROR_STATUS, or cmdout output.
  Adjacent registered contracts: "Language and Region Seams" (docs/LANGUAGE_AND_REGION_SEAMS_v1.md,
  design-intended+source) and "Value/Locale/Collation" (design-intended) -- neither governs error codes.
  Governing constraints are INTAKE-STAGE (ERRORSTOP + messaging rows) plus source annotations.
  Per the gate: "no applicable registered contract found" -> constrained by intake + annotations,
  NOT unconstrained.

Constraints that apply:
  - Messages-vs-data boundary (AIF-018): diagnostics localize; result payload does not.
    EXPORTFUNCTIONS failure text is a diagnostic -> localized is correct.
  - ERRORSTOP design (intake L48): failure sites record the code via the existing
    xbase_error_context.hpp thread-local; ERRORSTOP reads get_last_error().get_severity().
    => the failure site must set_last_error(code), which it does not today.
  - Do not use E_UNKNOWN to green a gate. Do not replace localized detail with the
    English to_string(code). Do not emit duplicate error lines.
  - HRESULT-style code layout is a stable-ABI concern (xbase_error_codes.hpp header comment):
    new codes must use make_code(severity, facility, number) and keep the io facility (0x0006).

Proposed behavioral effect:
  A failing EXPORTFUNCTIONS emits its LOCALIZED diagnostic AND records a canonical
  io error code, so `ERROR_STATUS` reports severity=error / facility=io / a nonzero
  number / message, and a future SET ERRORSTOP can halt on it. No user-visible line
  changes today (same localized text); the new fact is the recorded error state.

Required source/test/HELP/metadata updates:
  - New error constant + its to_string/symbol (+ reverse-lookup if present) entries.
  - New cmdout primitive declared/defined.
  - EXPORTFUNCTIONS two failure sites adopt it.
  - No HELP/USAGE/syntax/alias/no-arg change (behavioral display unchanged) -> no CMDHELP drift expected.
  - Proof transcript retained under labtalk/proofs/runs/.

Proof plan:
  Acceptance triple for EXPORTFUNCTIONS write failure (safe, non-destructive):
   1. localized message renders (verify under en-US + one non-en locale);
   2. ERROR_STATUS reports the canonical io failure (facility=io, number=1, message);
   3. [ERRORSTOP halt is OUT OF SCOPE this patch] -- proven later when SET ERRORSTOP lands.
  Failure is forced with a target that reliably fails to open WITHOUT deleting anything,
  e.g. `EXPORTFUNCTIONS MD <an-existing-directory-path>` (ofstream open fails -> "Unable to
  open output file"); confirm NO output file is created. Retain the launcher-console stream.

Known contract drift or uncertainty:
  - `cmdout::print_error(cmd, code)` currently prints English to_string(code) and does NOT
    call set_last_error -- a latent trap. This patch does NOT refactor it or its (zero) callers;
    flagged for the lane-wide reconciliation.
  - Whether xbase_error_codes.hpp has a from-symbol/parse table needing a matching entry --
    to be confirmed at edit time (only to_string + symbol switches were seen; grep before editing).
```

## 2. Output-Contract Design (the reviewable decision)

The problem is that today there are two disjoint primitives:

- `cmdout::print_message(MessageId, vars)` -> localized text, records **nothing**.
- `cmdout::print_error(cmd, code)` -> English `to_string(code)`, records **nothing**
  (does not even call `set_last_error`).

Neither satisfies the acceptance triple. The contract must let a failure site emit a
**localized** diagnostic AND record a **canonical code**, in one call, one visible line.

### 2a. Error identity (add to `include/xbase_error_codes.hpp`)

The `io` facility (0x0006) exists with a string mapping but **no code constants**. Add:

```cpp
// IO
constexpr code e_io_write_failed() noexcept
{
    return make_code(severity::error, facility::io, 0x0001);
}
```

plus matching arms in `to_string` (`"I/O write failed."`) and `symbol`
(`"E_IO_WRITE_FAILED"`), and any reverse/parse table if one exists. The
"unsupported format" path reuses the existing `e_invalid_argument()` (general/0x0002)
-- an argument error, not I/O. No `E_UNKNOWN`.

### 2b. Emission primitive (add to `src/cli/command_output.{hpp,cpp}`)

```cpp
// Emit a localized diagnostic AND record the canonical error/warning code so
// ERROR_STATUS and (future) ERRORSTOP observe the failure. One visible localized
// line; the English to_string(code) is NEVER shown to the user (it only appears
// inside ERROR_STATUS's own Message field, which is expected there).
void emit_error(dottalk::helpdata::MessageId id,
                xbase::error::code ec,
                const std::unordered_map<std::string, std::string>& vars = {});
void emit_warning(dottalk::helpdata::MessageId id,
                  xbase::error::code ec,
                  const std::unordered_map<std::string, std::string>& vars = {});
```

```cpp
void emit_error(MessageId id, xbase::error::code ec, const Vars& vars) {
    print_message(id, vars);              // localized display (unchanged path)
    xbase::error::set_last_error(ec);     // recorded state for ERROR_STATUS/ERRORSTOP
}
```

This directly answers Codex's three constraints: code + localized message emit
**together**, **no duplicate line** (only the localized line prints), and the
localized detail is **not** replaced by an English generic.

### 2c. EXPORTFUNCTIONS adoption (`src/cli/cmd_export_functions.cpp`, two sites only)

```cpp
// unsupported format:
cli::cmdout::emit_error(MessageId::ExportFunctionsUnsupportedFormatText,
                        xbase::error::e_invalid_argument(), {{"format", format}});
// write failure:
cli::cmdout::emit_error(MessageId::ExportFunctionsFailedText,
                        xbase::error::e_io_write_failed(), {{"detail", error}});
```

Optional hygiene (flagged, not required for the failure proof): clear the error on
the success path (`ExportFunctionsExportedText`) so a stale code does not linger for
a later standalone `ERROR_STATUS`. Recommend clearing on success.

## 3. Explicit scope boundary

IN scope (this patch): the io error identity, the `emit_error`/`emit_warning`
primitive, EXPORTFUNCTIONS adoption at its two failure sites, and the identity +
localized-emission + `ERROR_STATUS` proof.

OUT of scope (each its own later reviewed patch): wiring `SET ERRORSTOP`; the
registry-wide `print_error`/`print_warning` sweep; active Messaging DBF/CDX/LMDB
synchronization; refactoring the legacy `print_error(cmd, code)`; and AIF-022
script-runner comment-prefix repair (kept entirely separate).

## 4. Checkpoint

Source is not yet mutated. Requesting a nod on 2a (the `e_io_write_failed`
identity) and 2b (the `emit_error` primitive as the lane's failure-emission
contract) before I apply the three-file patch and run the acceptance proof.
