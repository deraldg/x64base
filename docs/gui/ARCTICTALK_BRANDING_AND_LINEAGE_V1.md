# ArcticTalk Branding and Lineage v1

Status: active naming contract.

## Purpose

This note fixes the naming rule for the DotTalk++ front-end family so GUI, TUI,
help, and maintenance work do not drift.

## Canonical Rule

`ArcticTalk` is the public umbrella brand for the DotTalk++ front-end family.

Under that umbrella, `Foxtalk`, `foxhelp`, and FoxPro-style command vocabulary
remain valid subsystem names, compatibility lanes, and historical references.

## Why This Is Intentional

DotTalk++ preserves classic xBase and FoxPro command language for educational,
historical, and compatibility reasons.

That does **not** mean DotTalk++ is a FoxPro clone.

The project is free to:

- preserve classic command names and familiar syntax,
- document legacy behavior where it still matters,
- diverge where x64base or DotTalk++ architecture requires it,
- add original workspace, browser, help, messaging, and GUI concepts.

## Naming Policy

Use these rules in forward-facing docs and UI surfaces:

| Name | Use |
| --- | --- |
| ArcticTalk | Public-facing front-end/workbench umbrella |
| Foxtalk | TUI lineage, shell-bridge, menu taxonomy, and legacy compatibility lane |
| foxhelp | Legacy/help-family naming that still belongs under the Arctic umbrella |
| DotTalk++ | Runtime/command shell/database product authority |
| x64base | Core database/engine family and architectural foundation |

## What To Avoid

Do not describe DotTalk++ or ArcticTalk as:

- a FoxPro clone,
- a separate database engine,
- a fork with different cursor/index/relation truth than DotTalk++,
- a product that replaces x64base runtime authority.

Do not revive `TurboTalk` as a forward-facing product name.

## Working Interpretation

The clean mental model is:

- `DotTalk++` owns runtime truth,
- `x64base` supplies core engine/library behavior,
- `ArcticTalk` is the public front-end umbrella,
- `Foxtalk` and related fox-prefixed lanes remain legitimate historical and
  compatibility names inside that umbrella.

## Documentation Consequence

When a document or UI surface must choose between brand and lineage:

- use `ArcticTalk` for the public umbrella,
- keep `Foxtalk` where the subsystem, source lane, or compatibility story is
  specifically about the fox-derived TUI/help lineage,
- explicitly say when DotTalk++ behavior is compatible, adapted, or intentionally
  different from classic FoxPro behavior.
