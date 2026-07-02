# Native C++ Maintenance App Policy Correction v1

## Doctrine

The official DotTalk++ maintenance application surface is native C++, consistent with the rest of the DotTalk++ / x64base application family.

## Corrected roles

- **MAINT** is the current native C++ maintenance/developer control surface in first-wave read-only form.
- **BBOX / Blackbox** is the current native C++ educational surface for the classic data -> processing -> information model.
- **Python 3.12** is allowed for portable external helper/report tooling and repeatable scans, but it is not the main maintenance application.
- **PowerShell** is acceptable for temporary MDO package creation/staging on Windows, but it is not part of the permanent maintenance workflow.
- **DotTalk++ runtime scripts** under `dottalkpp/data/scripts` remain runtime scripts and must not be treated as the external maintenance-script root.

## Root policy

- `src/maintenance` is reserved for shared native C++ maintenance support code.
- `src/cli/cmd_maint.cpp` and `src/cli/cmd_bbox.cpp` are the current first-wave command-file surfaces.
- `dottalkpp/scripts/maintenance` is the external maintenance tooling and cookbook root.
- `dottalkpp/data/scripts` remains the runtime DotScript root.

## Boundary

This policy correction does not authorize source edits, executable launcher creation, HELP/CMDHELPCHK mutation, DBF/CDX/LMDB creation, build execution, or publication updates.
