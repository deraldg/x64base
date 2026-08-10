# DotScript Regression Lane

This directory is the curated home for manual DotScript regression assets.

## Canonical Layout

- `core/`
  Current MCC regression entrypoints. Start here.
- `focused/`
  Targeted read-only shakedowns for one command family or behavior.
- `metadata/`
  Manual metadata-lane proofs that still need an operator-selected metadata root.
- `datadict/`
  Data-dictionary readback smokes.
- `legacy/`
  Older exhaustive harnesses preserved for forensic comparison.
- `quarantine/`
  Files removed from the active surface because they are obsolete, environment-specific,
  transcript-contaminated, or not executable DotScript.

## Policy

- Files under `docs/` are historical proof packages, candidates, templates, and generated
  artifacts. They are not the canonical regression suite.
- Promote only scripts that are executable against the current command surface.
- Keep environment setup explicit:
  `DO X64`, `DO X32`, `DO SANDBOX`, or `DO metadata` as appropriate.
- If a script depends on a disposable lane or mutation rights, keep it out of `core/`.

## First-Pass Canonical Set

- `core/MCC_TIER1_CORE_SURFACE_AND_INDEX_SAFE_V1.DTS`
- `core/MCC_TIER2_OBSERVATION_CANARIES_V1.DTS`
- `core/MCC_TIER3_SANDBOX_MUTATION_CANARIES_V1.DTS`
- `focused/ERSATZ_REL_ENUM_BROWSER.dts`
- `focused/SET_CASE_NEAR_SHAKEDOWN_V1.DTS`
- `focused/SOUNDEX_PREDICATE_SHAKEDOWN_V1.DTS`
- `focused/Workspace Relation SaveLoad Smoke Test DTSHEMA 2 live path.dts`
- `metadata/METADATA_CONTINUATION_SMOKE_v2.dts`
- `metadata/METADATA_LOGICAL_SMOKE_v0.dts`
- `metadata/SYSTEM_METADATA_SEED_v2.dts`
- `metadata/SYSTEM_METADATA_VALIDATE_v0.dts`
- `datadict/datadict_smoke.dts`

## Notes

- `SYSTEM_METADATA_BOOLEAN_FIX.dts` was quarantined because its target
  `system_metadata_boolean_fix_v0` is not present in the current repo roots.
- The older exhaustive MCC scripts were preserved in `legacy/`, but the tiered scripts are
  the canonical manual lane going forward.
