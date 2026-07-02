# MAINT Native Command Source Plan v1

MDO-323 records the first-wave source plan for the native MAINT command.

## Doctrine

- MAINT is a native C++ DotTalk++/x64base maintenance/SDLC inspection surface.
- BBOX is the educational Blackbox model: data in, processing, information out.
- Python 3.12 may support portable helper/report tooling.
- PowerShell remains temporary package/scaffolding only.
- Runtime DotTalk scripts remain under dottalkpp/data/scripts.
- External maintenance cookbooks and helper tooling live under dottalkpp/scripts/maintenance.

## First-wave MAINT command intent

MAINT starts read-only. It should report lanes, cookbooks, status, and boundaries. It must not run mutation workflows.

Planned first-wave commands:

- MAINT
- MAINT USAGE
- MAINT STATUS
- MAINT LANES
- MAINT COOKBOOK
- MAINT BOUNDARY
- MAINT BBOX

## BBOX lessons carried forward

- The canonical DOTREF header is include/dotref.hpp.
- src/help/dotref.hpp was duplicate/noncanonical drift and caused a false trail.
- HELP rebuild was not the DOTREF fix.
- Raw HELP DBF append was not used.
- CMDHELPCHK should remain report-only until explicit mutation authorization.

## Boundary

This plan creates no C++ source, no registration, no build, no HELP mutation, no CMDHELPCHK mutation, and no DBF/CDX/LMDB work.
