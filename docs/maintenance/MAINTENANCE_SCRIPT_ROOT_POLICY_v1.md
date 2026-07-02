# Maintenance Script Root Policy v1

## Separation of responsibilities

- `dottalkpp\data\scripts` is for runtime scripts that DotTalk++ can run with DO / DOTSCRIPT.
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
