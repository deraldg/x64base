# DD-001 Engine Boundary and Profile Plan v0

## Boundary doctrine

x64base must remain buildable and operable as an engine. DotTalk++ must remain usable as a professional data/runtime layer. LabTalk, student examples, case studies, media and storyboards belong in optional overlays.

## Proposed profile vocabulary

### ENGINE

Core storage/data engine and metadata-capable structures. No visible student artifacts. No dependency on LabTalk/cases/media/storyboards.

### PROFESSIONAL

DotTalk++ runtime with commands, HELP, data dictionary, metadata browsing, scripting, reporting, validation, import/export, relations and diagnostics. Educational material is absent or hidden unless explicitly enabled.

### EDUCATIONAL

Adds LabTalk, case catalog, student examples, teaching notes, media anchors and guided explanations.

## Current source-level audit observation

The top-level CMake includes a `DOTTALK_WITH_EDUCATION` option. A text scan in this package found references in the top-level CMake summary area, but not an obvious enforcement path excluding `src/edu`, `include/edu`, `include/labtalk`, or student command extensions from normal recursive source inclusion. This should be treated as a boundary-audit item, not as a source defect diagnosis until locally verified in the build tree.

## Dictionary implication

Every dictionary row that could expose educational material should carry a visibility/profile field such as:

```text
visibility_profile = ENGINE | PROFESSIONAL | EDUCATIONAL | DEV_ONLY | MAINTENANCE
```

The default public dictionary should not show EDUCATIONAL rows in engine/professional profile.
