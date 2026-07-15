# DD-004 Next Actions v0

Status update, 2026-07-14: the requested design-only continuation now exists at
`docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`. That plan is
the current cross-SDLC authority; this file remains the DD-004 intake record.

## Immediate safe next step

Execute Pass 0 of the design-only profile-gating plan. Do not edit CMake or
source yet. Produce a current, machine-readable census covering:

- build inclusion/exclusion;
- command registration visibility;
- HELP topic visibility;
- schema/sample data visibility;
- runtime content-pack loading;
- script registry role classification;
- package allow-list and provenance fields; project licensing: To be determined.

## Candidate future implementation sequence

1. Keep the now-normalized `DOTTALK_WITH_TV` name; the old DD-004 snapshot's
   `DOTTALK_WITH_TVISION` mismatch is no longer present in current presets.
2. Replace recursive-glob edition membership with explicit component targets;
   do not rely on a compile definition alone.
3. Add current component classifications before excluding `src/edu` or
   educational/student extension sources.
4. Split command registration by component and record a stable component ID.
5. Apply the same component ID to HELP, functions, scripts, dictionaries, and
   data packaging.
6. Add dictionary catalog fields for `component_id`, `profile_visibility`,
   `overlay_pack`, `build_gate`, and `runtime_gate`. Project licensing: To be
   determined.
7. Prove LEAN and PROFESSIONAL profiles before promoting full EDUCATIONAL
   overlay packaging.
8. Keep engine index mode (`NONE | LEGACY | LMDB`) independent of product
   edition.

## Do not do yet

- Do not remove education files.
- Do not rename commands.
- Do not mutate HELP data.
- Do not change public command behavior without a guarded compatibility plan.
