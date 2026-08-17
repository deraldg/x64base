# PyDotTalk SDLC Charter v0

Status: draft charter, review-needed
Created: 2026-08-17
Owner: member.derald
Scope: the `pydottalk` Python extension module as a product in its own right
Parent doctrine: `DOTTALKPP_SDLC_CHARTER_v0.md`, `SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`
Trust boundary: `docs/contracts/PYTHON_BINDING_TRUST_CONTRACT_V1.md`
AIF lane: NOT YET CLAIMED. Claim with
`python tools/coordination/session_coordinator.py claim-aif`, then record the
number here and in `coordination/aif/`.

## Purpose

PyDotTalk has been treated as a build switch of the engine. It is not one. It is
a **separate but co-sourced product**: a distinct deliverable, with a distinct
artifact, a distinct audience, and a distinct failure surface, that happens to
compile the same source files as the engine rather than a copy of them.

The absence of this charter had a measurable cost. Two defects found on
2026-08-17 exist only because nobody owned the binding as a product:

- `proof.build.parent_provided_globals` -- the module was a subdirectory of the
  root build, so producing a four-source module also built `dottalkpp.exe`, the
  Turbo Vision library and the tvision vcpkg package. It referenced none of them.
- `proof.build.macro_defined_twice_disagreeing` -- the binding and the library it
  links emitted opposite values of `DOTTALK_HAS_XINDEX` on the same command line.

Both are ownership failures rather than coding failures. A component with no
owner inherits whatever the nearest larger thing happens to do.

## The co-sourced rule

This is the load-bearing clause of the charter.

```text
Co-sourced means ONE set of sources with TWO consumers.
It does not mean a copy, a fork, a vendored tree, or a second source list.
```

`bindings/pydottalk/CMakeLists.txt` builds `xbase`, `memo` and `xindex` by
`add_subdirectory` against `DOTTALK_ROOT`. It deliberately does NOT restate their
source lists, because those directories glob their own sources and a second
hand-kept copy would drift silently: a file added to `src/xbase` would reach the
CLI and not the binding, and nothing would say so.

Consequences that follow, and they are not optional:

- The engine owns struct layout, ABI, and every macro the engine headers branch
  on. The binding consumes them and must never contradict them.
- Where a linked target already exports a definition PUBLIC, that target is the
  single authority. The binding emits only flags no target owns. This is the rule
  the `DOTTALK_HAS_XINDEX` defect broke.
- An engine change that alters shared behaviour invokes this charter's gates too,
  by the demonstrated-dependency rule in the parent doctrine.

## Ownership boundary

| Area | Owner |
|---|---|
| DBF/x64/VFP formats, memo, indexes, locks, buffers | DotTalk++ SDLC |
| `xbase` / `memo` / `xindex` source, struct layout, ABI | DotTalk++ SDLC |
| Engine feature macros (`DOTTALK_*`) | DotTalk++ SDLC |
| Python API surface, naming, and its camelCase/snake_case pairing | PyDotTalk SDLC |
| Exception and error contract seen from Python | PyDotTalk SDLC |
| `bindings/pydottalk/CMakeLists.txt`, its presets, `build_pydottalk.ps1` | PyDotTalk SDLC |
| Interpreter support, ABI tag, wheel and distribution shape | PyDotTalk SDLC |
| Trust boundary and what the module refuses to do | PyDotTalk SDLC, per the trust contract |
| CLI commands, DotScript, HELP/CMDHELP | DotTalk++ SDLC, NOT this charter |

The last row matters. The binding is a **data** surface. Command-shell execution
from Python is an open decision (OI-005) precisely because routing it through the
module would drag the ~400-TU CLI back in and give the module its own per-process
identity and catalog state that nobody logged into.

## What the product actually is today, measured

Recorded honestly so the charter does not open by overstating its subject.

- **CRUD only.** `module.cpp` binds `open`, `close`, `gotoRec`, `top`, `bottom`,
  `skip`, `readCurrent`, `writeCurrent`, `appendBlank`, `deleteCurrent`,
  `fields`, `get`, `set`. There is no `setOrder`, no `seek`, no tag surface.
- **Indexing has never been tested through the binding.** Verified against the AI
  portal on 2026-08-17: `labtalk/ai_portal/` names pydottalk exactly once, as a
  closeout filename; the four `launcher_pydottalk` proof runs are 356-389 bytes
  with zero index hits; the single registered pydottalk proof is APPEND BLANK.
- **`DOTTALK_INDEX_MODE` currently buys nothing at runtime.** All three modes ship
  a byte-identical module. See `proof.build.index_mode_changes_nothing_shipped`
  and OI-007.
- **It builds standalone and lean**, on Windows/MSVC and on Linux/ELF, and is not
  pinned to one Python version despite the `cp312` house default.
- **It has no packaging story.** No wheel, no `pyproject.toml`, no declared
  interpreter support range, no versioning policy. `version()` reports `0.4.0`
  from a source constant.

## Lifecycle gates

Selected by deliverable, per the parent doctrine's scope-calibration rule. The
default scope for a binding change is this column, not the whole assembly.

| Gate | When it applies |
|---|---|
| Standalone configure in all three index modes | any change to the binding's cmake or presets |
| Clean build with ZERO new compiler diagnostics | every change. A warning in a green build is a finding, not noise |
| ctest smokes green | every change to `module.cpp` or the linked libraries |
| Import test on the produced artifact | every change. A zero exit code is not proof an artifact exists or loads |
| Artifact identity recorded (size + sha256) | any change claiming to alter what ships |
| Trust contract re-read | any change that widens what the module can do |
| Engine-side proof | any change that touches `src/xbase`, `src/memo`, `src/xindex` |
| Portal proof registered | any measurement that contradicts a previous claim |

The third and fourth rows exist because both were violated this year: a build
reported success with no artifact present, and a redefinition warning rode a
green exit code for the entire life of the LEGACY mode.

## Milestones

Numbered, not dated. Each closes with a registered proof.

- **M0 -- product boundary.** This charter, the `projects.yaml` registration, the
  AIF lane. Establishes that the binding has an owner.
- **M1 -- packaging.** Decide the interpreter support range, the versioning
  policy, and whether a wheel is produced. Today the artifact is a loose `.pyd`
  whose ABI tag is decided by whichever interpreter cmake resolved.
- **M2 -- index API.** The first `setOrder`/`seek` binding. Closes OI-007 and
  makes `DOTTALK_INDEX_MODE` meaningful; expected to make `lean-none` fail to
  link, which is the desired signal, and to settle the `lmdb.dll` question on
  Windows.
- **M3 -- execution route.** Resolve OI-005. Prior art favours subprocess
  `dottalkpp.exe --script` over linking the shell.
- **M4 -- dead code.** Resolve OI-002, `src/bindings/`, which is a second
  `pydottalk` definition that already misled one session.

## Open questions this charter does not answer

- Whether PyDotTalk is ever published outside the tree. The trust contract's
  "trusted, caller-is-boundary" posture is sound INSIDE the repository and is
  explicitly named as one of the three edges where trusted stops.
- Whether the binding tracks engine versions or carries its own.
- Whether `pycrud` and `DB_Converter`, both registered projects that already name
  pydottalk as a lane, become downstream consumers with a stability expectation.

## Review status

Authored by an AI session under maintainer direction on 2026-08-17 and marked
review-needed per house convention. Not promoted to `C:\x64base` or to the public
repository; those are separate steps.
