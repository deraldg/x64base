# AIF-119 -- PyDotTalk as a co-sourced product: what a component with no owner inherits

**Status:** charter (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-17. **AIF-119** (claimed 2026-08-17, run `COWORK-20260817-001`,
lane `pydottalk-co-sourced-product`).
Parent project: `project.pydottalk` (registered the same day in
`labtalk/registries/projects.yaml`, kind `binding_project`).
Owning lifecycle: `docs/maintenance/PYDOTTALK_SDLC_CHARTER_v0.md`.

**Sibling lanes.** **AIF-118** *Silent-Pass Guard Lane* owns the defect shape
"a check that returns the same answer for absent and fine". This lane is not a
subset of it, but three of the four defects below ARE that shape, found in the
build system rather than in a guard. Where they overlap, AIF-118 owns the shape
and this lane owns the component. **AIF-100** owns the gate estate.

## Why this is a lane and not four bug fixes

Between 2026-08-16 and 2026-08-17, four defects were found in the Python
binding. They look unrelated: a build that compiled 400 files too many, a
contract nothing harvested, a macro with two values, a build option that
selected nothing. They share one cause:

> **The binding had no owner, so it inherited whatever the nearest larger
> thing happened to do.**

Every one of them is a consequence of pydottalk being treated as a switch of the
engine build rather than as a product. None is a coding error in the ordinary
sense; each is an ownership boundary that was never drawn.

## The four instances, as evidence

| # | what | the inheritance that caused it |
| --- | --- | --- |
| 1 | `build.ps1:164` hardcodes `--target dottalkpp pydottalk`, so producing a 4-source module also built the entire CLI (~400 `cmd_*.cpp`), `dottalk_tvui.lib` and the tvision vcpkg package. The module references all three ZERO times | it was a subdirectory of the root build, so the root build's targets were its targets |
| 2 | Extracting it standalone revealed FIVE globals the parent had silently supplied: the generated `dottalk/build_vectors.hpp`, `NOMINMAX`, `CMAKE_MSVC_RUNTIME_LIBRARY`, seven feature flags, and `CMAKE_POSITION_INDEPENDENT_CODE`. Only the first two fail loudly | nobody had ever asked what the parent was providing, because nobody owned the child |
| 3 | `DOTTALK_HAS_XINDEX` emitted `=0` by the binding and `=1` PUBLIC by the `xindex` target it links, 48 against 26 on the same command lines. Last flag wins, per translation unit | the binding re-emitted a flag a linked target already owned, so it was not configuring, it was arguing |
| 4 | `DOTTALK_INDEX_MODE` LMDB, LEGACY and NONE ship a byte-identical module (665336 B, sha256 `54cb15eb...`) | the option was inherited from a build whose CLI genuinely uses the index; the binding never has |

Instances 2, 3 and 4 are AIF-118's shape. Instance 3's only symptom was a
compiler warning riding a green exit code through a 52-step build log.

## The rule this lane exists to enforce

**Co-sourced means one set of sources with two consumers.** It does not mean a
copy, a fork, a vendored tree, or a second source list. Three consequences, each
of which one of the defects above broke:

1. **The owning target is the single authority for what it exports.** A
   subproject emits only flags no target owns. (Broke: instance 3.)
2. **A subproject must enumerate what its parent provides, before extraction,
   not one compile error at a time.** Half of what a parent supplies fails
   silently. (Broke: instance 2.)
3. **An option must be shown to change the artifact, or be documented as not
   changing it.** An option that selects nothing observable is a claim of choice
   where no choice exists. (Broke: instance 4.)

## Scope

**In scope:** the binding's build, presets, packaging, Python API surface, error
contract, trust boundary, and the ownership seam between it and the engine.

**Not in scope:** engine correctness, CLI commands, DotScript, HELP. Those are
DotTalk++ SDLC. Where an engine change alters shared behaviour, this lane is
invoked by the demonstrated-dependency rule, not by default.

## Milestones

Held in the SDLC charter rather than restated here, per the house rule against
two shims that will diverge. M0 is the product boundary and is CLOSED by this
lane's first commits; M1 packaging, M2 index API, M3 execution route, M4 dead
code remain open. Related open items: OI-002, OI-003, OI-005, OI-006, OI-007.

## What is NOT claimed

- **No Windows measurement was taken.** The `lmdb.dll` question -- whether a
  future index-referencing module acquires a runtime dependency that must ship
  beside the `.pyd` -- is stated as a question. `dumpbin /dependents` settles it.
- **The house vcpkg route on Linux is unproven here.** LMDB mode was exercised
  by building liblmdb from source with a `/tmp` config shim. `wsl-lean` is the
  house route and remains maintainer-operated.
- **No claim that the binding is production-ready.** It is CRUD-only, has never
  been tested with an index, and has no packaging story. See the SDLC charter's
  measured-state section.
