# Repository Boundaries: Runtime, GUI, and LabTalk v1

Scope: canonical boundary for `x64base`, `DotTalk++`, Arctic GUI/TUI work, and
Laboratory Campus / LabTalk.

## Purpose

This note records the current repository split so source ownership does not
drift while new public GitHub homes are being established.

Current public repositories:

- `deraldg/x64base`
- `deraldg/dottalkpp`
- `deraldg/labtalk`

At this stage, `dottalkpp` is still treated as a product/runtime identity
inside the broader `x64base` source tree. The separate `deraldg/dottalkpp`
repository exists, but source ownership is not being forced there yet.

## Authority Rule

The engine and command shell remain the source of truth.

- GUI work must conform to `x64base` / `DotTalk++`.
- GUI code may present runtime state, but must not invent separate cursor,
  relation, index, locking, or table semantics.
- LabTalk may consume runtime truth, documentation, proofs, and launchers, but
  must not silently redefine runtime behavior.

## Repository Ownership

### `deraldg/x64base`

Owns:

- core engine and runtime behavior
- `DotTalk++` command shell behavior
- shared command/session/cursor/index/relation state
- Arctic GUI/TUI workbench code
- runtime-facing Python and wx/Tk bridge code that depends on engine truth
- shared runtime documentation and developer governance

Examples in the current tree:

- `src/gui/core`
- `src/gui/wx`
- `src/tv`
- `src/cli`
- `src/xbase`
- `src/xindex`
- `include`

Rule:

- if the code changes runtime truth or presents runtime truth directly, it stays
  under `x64base`

### `deraldg/labtalk`

Owns:

- Laboratory Campus / LabTalk portal
- campus registries
- labs, assignments, proofs, and curriculum overlays
- consumer-facing launchers and orchestration
- documentation and planning for the campus as a learning layer
- above-runtime staging for product, publication, AI coordination, and
  cross-repository planning that consumes x64base/DotTalk++ truth

Examples in the current tree:

- `labtalk/portal`
- `labtalk/registries`
- `labtalk/labs`
- `labtalk/proofs`
- `labtalk/reports`

Current staging workspace:

- `C:\labtalk`

Rule:

- if it is a consumer, teaching surface, launcher, registry, or proof/campus
  overlay, it belongs to `labtalk`
- if it coordinates product/publication/AI/cross-repo work above runtime scope,
  stage it in `C:\labtalk` before promotion

### `deraldg/dottalkpp`

Current rule:

- use `DotTalk++` as the runtime/article/manual identity
- do not force a separate source split yet
- use it for runtime-facing articles, command-shell manuals, and product-level
  explanation until the long-term source boundary is clearer

## GUI Rule

Arctic already has a home under `src`, and that remains correct.

- Arctic GUI/TUI source stays in `x64base`
- wxWidgets and Python/Tk front ends must reuse engine/runtime services when
  possible
- front ends are orthogonal views over the same backend truth

This means the GUI is not an independent product line with its own semantics.
It is a workbench lane over `DotTalk++` and `x64base`.

## LabTalk Portal Rule

The LabTalk portal is a consumer of `DotTalk++` and related systems.

Therefore:

- the portal belongs in `labtalk`
- portal actions may launch runtime work, proofs, docs, and labs
- portal code must not become the authority for engine behavior

## Practical Working Rule

When deciding where new work belongs, ask:

1. Does it change engine/runtime truth?
2. Does it present runtime truth directly as a GUI/TUI/workbench surface?
3. Is it a teaching/campus/portal/proof overlay that consumes runtime truth?

Classification:

- `1` or `2` -> `x64base`
- `3` -> `labtalk`

## Temporary Policy

Until the split is curated further:

- keep runtime articles under the `DotTalk++` name
- keep Arctic source under `src`
- keep LabTalk portal and campus assets under `labtalk`
- use `C:\labtalk` as the local staging area for above-runtime LabTalk scope
- do not publish raw dev debris into the new public repos

## Status

This is the current canonical boundary note and should be updated before any
large repository split or relocation of GUI/LabTalk assets.
