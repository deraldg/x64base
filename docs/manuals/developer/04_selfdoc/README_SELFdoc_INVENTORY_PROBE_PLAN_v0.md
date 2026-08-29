# SelfDoc inventory/probe plan v0 - script only

This package creates the planning/control artifact:

```text
selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md
```

Apply from the DotTalk++ repo root:

```powershell
cd D:\code\ccode\dottalkpp
Expand-Archive .\selfdoc_inventory_probe_plan_v0_script_only_PATHFIX.zip -DestinationPath . -Force
.\apply_selfdoc_inventory_probe_plan_v0.ps1
```

If the zip is somewhere else, use its full path:

```powershell
cd D:\code\ccode\dottalkpp
Expand-Archive C:\path\to\selfdoc_inventory_probe_plan_v0_script_only_PATHFIX.zip -DestinationPath . -Force
.\apply_selfdoc_inventory_probe_plan_v0.ps1
```

## Boundaries

This patch does not:

```text
move files
write DBFs
edit source
modify CMDHELPCHK
rebuild HELP DATA
repair source contracts
promote loose scripts
implement probes
```

## Notes

If the plan already exists and differs, the script writes a backup:

```text
selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md.bak_selfdoc_inventory_probe_plan_v0
```

Do not run this from `D:\code\ccode`; run it from `D:\code\ccode\dottalkpp`.
