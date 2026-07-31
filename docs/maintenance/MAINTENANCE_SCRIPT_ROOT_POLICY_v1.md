# Maintenance Script Root Policy v1

## Separation of responsibilities

- `dottalkpp\data\scripts` is for runtime scripts that DotTalk++ can run with DO / DOTSCRIPT.
- Canonical runtime regression and canary `.dts` files should live under `dottalkpp\data\scripts\canaries`, `dottalkpp\data\scripts\suites`, or an explicit runtime lane subfolder such as `messaging`, `metadata`, `help`, or `export`.
- `dottalkpp\data\tests` is a migration lane only. It is not the authoritative long-term runtime regression root.
- `dottalkpp\data\*.dts` at the data root should be treated as bootstrap roots, lane openers, or clearly labeled operator/demo scripts.
- `dottalkpp\scripts\maintenance` is for external maintenance PowerShell/Python/templates/cookbooks/launch sequences.
- `src\maintenance` is reserved for shared C++ native MAINT/BBOX support code. Current first-wave command surfaces live in `src\cli`.

## Script catalog requirement

Every launchable maintenance script should eventually have a catalog row containing:

- lane
- script path
- purpose
- inputs
- outputs
- mutation class
- backup requirement
- rollback requirement
- smoke test
- last green checkpoint
- next allowed gate

## Default safety

Report-only is the default. Apply/mutation scripts require explicit authorization and evidence that backup/rollback has been validated.

## Regression bootstrap rule

Every runtime regression `.dts` must bootstrap its own environment before touching tables, workspaces, relations, or ERSATZ.

Typical first executable line:

- `DO X32`
- `DO VFP`
- `DO X64`
- `DO SANDBOX`
- `DO METADATA`
- `DO MESSAGING`

Do not rely on whatever paths or areas the operator left active.
For nested scripts below `dottalkpp\data\scripts\...`, use a relative climb back to the data root such as `DO ..\..\X64`.
