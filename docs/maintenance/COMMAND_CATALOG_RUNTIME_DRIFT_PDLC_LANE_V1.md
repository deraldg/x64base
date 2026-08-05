# Command Catalog / Runtime Drift Reconciliation PDLC Lane v1

Status: repair lane opened; first finding registered (R-APPEND-BLANK), review-needed.
Ticket: AIF-088 (claim with `python tools/coordination/session_coordinator.py claim-aif`
to write coordination/aif/AIF-088.claim; 088 is the next free number as of 2026-08-04).
Owner: member.derald.
Steward: member.ai.claude.cowork, until reassigned by the owner.
Parent projects: `project.x64base.runtime`, `project.labtalk.pdlc`,
`project.ai_friendly`.

## Purpose

Reconcile what the command catalog and HELP DOCUMENT with what the runtime parser
actually ACCEPTS, one command family at a time. The catalog is generated from
`src/cli/shell_commands.cpp` plus parsed `@dottalk.usage` blocks; when a command's
documented syntax and its runtime parser disagree, the catalog confidently
describes behavior the engine does not have. This lane owns the PDLC for closing
those seams: decide the truth (fix the parser or fix the doc), then add a
regression that asserts it, so the drift cannot silently re-open.

This is the authored-vs-executed thesis applied to the engine's own self-
description: state that is authored (the catalog) drifts; state that is derived
(a dry run against the engine) cannot. The lane's detection gate is exactly that
derivation.

## Current Truth

Runtime / source anchors:

- `src/cli/cmd_append.cpp` (the `APPEND` parser)
- `src/cli/cmd_append_blank.cpp` (the separately registered `APPEND_BLANK`)
- `src/cli/shell_commands.cpp` (central command registry the catalog is built from)
- `src/cli/expr/function_catalog.cpp` (function-surface sibling)

Catalog / HELP anchors:

- `content/docs/dottalk/command-catalog.mdx` (x64base-site; source-derived)
- `content/docs/dottalk/function-catalog.mdx`
- runtime `HELP` / `CMDHELP` output, and `CMDHELPCHK` reflection

Reconciliation-guard anchors (already in the tree):

- `tools/fullstack_docs/refcheck_v1.py`, `tools/fullstack_docs/normcheck_v1.py`
  (the registry/SYSCMD/SYSFUNC/*ref catalog drift guards run by the pre-push gate)
- `tools/dbf/crud.py` `--emit --ram` (the fsram dry-run harness that first caught
  R-APPEND-BLANK)

Observed drift (registered findings):

- R-APPEND-BLANK. The catalog documents command `APPEND_BLANK` with syntax
  "APPEND BLANK", but the runtime `APPEND` parser REJECTS the `BLANK` token and
  prints usage. Mechanism: `APPEND` and `APPEND_BLANK` are two registrations, and
  the tokenizer routes the line "APPEND BLANK" to `APPEND` with argument `BLANK`
  (which `APPEND` treats as an invalid count) rather than to the `APPEND_BLANK`
  command. The hazard is the silence after the rejection: with the cursor on the
  last row, follow-up `REPLACE`s mutate THAT record -- a clobber, not an error.
  Bare `APPEND` is correct (`mem_proof.dts`). Evidence:
  `labtalk/proofs/runs/20260804_append_blank_catalog_drift_ram.txt`; proof
  `proof.engine.append_blank_catalog_drift` (runtime_observed, build 64a0136d).

## PDLC Scope

### Analyze

The drift is real and safety-relevant (silent clobber, not a hard error). It is a
REPL-surface disagreement only: the C++ binding `DbArea::appendBlank()` works, so
no storage-layer defect is implied. The catalog is generated, so the fix must land
at one of the two authorities -- the parser or the registration/usage the catalog
is built from -- not by hand-editing the generated `.mdx`.

Prior art (R-APPEND-BLANK). This drift was recognized before. `tools/fix-append-blank.ps1`
(dated 2025-08-22, UNTRACKED at the tools root -- an AIF-062-class invisible artifact)
attempted a FIX RUNTIME by injecting a `cmd_APPEND_BLANK` wrapper into
`src/cli/cmd_append.cpp` that forwards to `cmd_APPEND`. The drift is still live on
build 64a0136d (this lane's proof), so that fix either never landed or was
incomplete -- and reading it locates the real seam. A `cmd_APPEND_BLANK` handler
already exists (`src/cli/cmd_append_blank.cpp`); a handler is NOT the fix. The
tokenizer in `src/cli/shell_commands.cpp` routes the two-word line "APPEND BLANK" to
`cmd_APPEND` with argument `BLANK` -- which `cmd_APPEND` rejects -- and never to the
blank handler. So FIX RUNTIME must change the DISPATCH (route "APPEND BLANK" to the
blank handler) OR make `cmd_APPEND` treat a leading `BLANK` token as the no-op the
catalog names; the 2025 wrapper forwarded the unstripped `BLANK` straight back into
`cmd_APPEND`, so it could not have worked even if applied. DO NOT run the 2025
script: it assumes `src/cli` lives under `tools/` (it would throw `Missing`) and it
force-deletes a build dir rooted at `tools/` -- both wrong for the current tree. It
is evidence of a dropped thread, not a usable tool.

### Design

Per finding, choose exactly one reconciliation and make it the asserted truth:

- FIX RUNTIME: teach the parser to accept the documented token (e.g. `APPEND`
  accepts `BLANK` as a no-op alias for bare `APPEND`), matching the catalog.
- FIX DOC: correct the registration / `@dottalk.usage` so the generated catalog
  and HELP no longer advertise the unsupported syntax.

Default lean for R-APPEND-BLANK: FIX RUNTIME (accept `BLANK`), because
`APPEND_BLANK` is already a registered command and the classic-xBase spelling
"APPEND BLANK" is what users and the catalog both expect. Owner decides.

### Code

- R1 = R-APPEND-BLANK: apply the chosen reconciliation in `cmd_append.cpp` (or the
  registration), then add a regression asserting the chosen truth (documented
  syntax accepted, or usage no longer claims it).
- Additional findings (R2..Rn) register here as sibling repairs as the drift gate
  surfaces them. We should expect a few: the catalog has 236 command keys and 63
  functions, and only a handful have been dry-run against the engine so far.

### Test / Debug

- Detection gate (general): a small drift canary that takes documented mutation
  syntaxes and executes each in an fsram RAM table (`crud.py --emit --ram` is the
  working prototype), asserting the runtime accepts what the catalog documents.
  Zero disk footprint; the table evaporates on `VDISK UNMOUNT`.
- Per-fix regression: registered under the DotTalk++ regression runner before
  promotion, asserting the reconciled truth for that command.
- `refcheck` / `normcheck` remain the standing catalog-drift guards at commit time.

### Document

Update together for each fix: the `@dottalk.usage` block in the owning `cmd_*.cpp`,
the harvested HELP/CMDHELP, the regenerated command catalog on the site, the
finding row here, and the proof ledger entry.

### Maintain

Do not hand-edit the generated catalog `.mdx` to paper over a drift -- that re-opens
the seam on the next harvest. The fix lives at the parser or the registration, and
the regression is what keeps it closed.

## Scope Calibration

operating_mode: active repair lane.
change_class: command-surface behavior and generated-catalog/HELP reconciliation.
build_target: `dottalkpp` runtime.
product_profile: DEVELOPMENT first; the catalog is a published surface, so a
corrected doc is publication-relevant once proven.
index_profile: not applicable (command-surface lane, no table/index change).
scope_reason: touches the command parser and the source-derived catalog/HELP that
describes it; a wrong fix (hand-editing generated output) would silently regress.
minimum_gate_set: analyze/design record, the chosen reconciliation, a per-command
regression asserting the truth, refcheck/normcheck clean, and a proof-ledger row.
deferred_gates_and_residual_risk: a full 236-command / 63-function sweep is not in
scope for v1; findings accrue as the drift canary is run over a few commands at a
time.

## Next Gate

1. Owner claims the AIF number and picks FIX RUNTIME vs FIX DOC for R-APPEND-BLANK.
2. Land the chosen reconciliation + its regression.
3. Run the drift canary over a few more mutation commands (candidates: `REPLACE`,
   `DELETE`, `RECALL`, `PACK`, `INSERT`) and register any siblings as R2..Rn here.
