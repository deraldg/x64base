# Native Maintenance App Policy Addendum

The official maintenance program is a native C++ application surface. External scripts support maintenance, but they do not define the maintenance app.

## Permanent surfaces

- MAINT: current C++ maintenance/SDLC inspection and control surface in first-wave read-only form.
- BBOX: current C++ educational Blackbox model command.

## Support tooling

- Python 3.12: portable external helper scripts and report-only launchers.
- PowerShell: temporary package/staging scaffolding only.

## Directory rules

- Keep source code in src.
- Keep runtime DotTalk++ scripts in dottalkpp/data/scripts.
- Keep external maintenance tooling and cookbooks in dottalkpp/scripts/maintenance.
