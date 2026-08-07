# LabTalk Repository Boundary: Consumer Rule v1

Scope: where LabTalk stops and `x64base` / `DotTalk++` remain authoritative.

## Core Rule

LabTalk is a consumer layer.

It may consume:

- `DotTalk++` runtime behavior
- runtime transcripts and proofs
- documentation and manuals
- data specimens, labs, assignments, and campus registries
- launcher workflows and portal navigation

It must not silently become the authority for:

- engine behavior
- cursor truth
- relation truth
- index/order truth
- locking truth
- table semantics

## What Stays In `x64base`

The following continue to belong with the engine/runtime tree:

- `src/gui/core`
- `src/gui/wx`
- `src/tv`
- `src/cli`
- `src/xbase`
- `src/xindex`

This includes Arctic GUI/TUI work. Arctic is a runtime workbench surface, not a
separate truth system.

## What Belongs In `labtalk`

The following belong to LabTalk as campus/consumer assets:

- portal code
- registries
- labs
- proofs
- assignments
- campus reports
- public teaching overlays

Examples:

- `portal/`
- `registries/`
- `labs/`
- `proofs/`
- `reports/`

## DotTalk++ Naming Rule

For now, `DotTalk++` remains the best runtime/article/manual identity for the
command shell and runtime surfaces.

That means:

- runtime articles can continue under the `DotTalk++` name
- source ownership still stays primarily with `x64base`
- LabTalk references `DotTalk++` as one major campus building, not as a campus
  replacement

## Working Decision Test

Ask:

1. Is this engine/runtime truth?
2. Is this a GUI/TUI/workbench view over runtime truth?
3. Is this a campus/portal/proof/teaching consumer?

Classification:

- `1` or `2` -> `x64base`
- `3` -> `labtalk`

## Current Intent

LabTalk should stay light, honest, and consumer-oriented:

- sequence learning
- present proofs
- launch tools
- explain systems

It should not absorb core runtime ownership just because it can see or launch
the runtime.
