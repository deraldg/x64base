# Maintenance Script Language Policy v1

Status: policy plan, report-only.

## Rule

PowerShell scripts may be used for one-time package creation, planning, staging, and Windows-local operator convenience.

Permanent repeatable DotTalk++ maintenance workflows must be cross-platform. The preferred permanent scripting language is Python 3.12.

## Separation

- `dottalkpp/data/scripts` remains the runtime DotTalk++ script root.
- `dottalkpp/scripts/maintenance` is the external maintenance root.
- `src/maintenance` is reserved for shared native C++ MAINT/BBOX support code. Current first-wave command surfaces live in `src/cli`.
- Permanent maintenance launchers should be Python, not PowerShell.

## Why

Maintenance is part of the SDLC and must not be Windows-only. DotTalk++ can be built and maintained on multiple platforms, so repeatable maintenance procedures should be portable.

## Current Decision

The previous launcher skeleton work is retained as design/cookbook material. Any future executable maintenance launchers should be implemented as Python 3.12 scripts or later shared native DotTalk++/C++ support code after review.

## Boundary

This policy does not create executable launchers, mutate runtime scripts, alter source, run builds, rewrite HELP, create DBFs, rebuild CDX/LMDB, or replace publications.
