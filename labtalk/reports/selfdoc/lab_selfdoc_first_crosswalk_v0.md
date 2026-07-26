# LabTalk SelfDoc First Crosswalk v0

Generated: 2026-07-04T07:50:57

Boundary: report-only; no HELP DATA, DBF metadata, CMDHELPCHK, source, or manual publication mutation.

## Runtime Script

- D:/code/ccode/labtalk/labs/self_documenting_systems/cmdhelp_cmdhelpchk_selfdoc_v0.dts

## Command Set

- CMDHELP
- CMDHELPCHK

## Source Usage Contract Crosswalk

| Command | Source | Evidence |
| --- | --- | --- |
| CMDHELP | src/cli/cmdhelp.cpp | L1: // @dottalk.usage v1; L2: // owner: DOT/CMDHELP; L3: // command: CMDHELP; L9: // usage-access: CMDHELP USAGE; L1358: if (u == "COMMAND-OWNED @DOTTALK.USAGE V1 SUMMARY.") return true; |
| CMDHELPCHK | src/cli/command_helpchk.cpp | L3: // @dottalk.usage v1; L4: // owner: DOT/CMDHELPCHK; L5: // command: CMDHELPCHK; L11: // usage-access: CMDHELPCHK USAGE |

## Contracts Scanner Summary

```text
root=D:\code\ccode
contract_like_docs=148
source_contract_annotation_files=38
source_usage_marker_files=262
registry_rows=22
likely_unregistered_contract_docs=134
registered_but_not_discovered=10
```
