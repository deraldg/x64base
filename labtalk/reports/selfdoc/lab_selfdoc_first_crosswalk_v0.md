# LabTalk SelfDoc First Crosswalk v0

Generated: 2026-10-07T18:32:42

Boundary: report-only; no HELP DATA, DBF metadata, CMDHELPCHK, source, or manual publication mutation.

## Runtime Script

- D:/code/ccode/labtalk/labs/self_documenting_systems/cmdhelp_cmdhelpchk_selfdoc_v0.dts

## Command Set

- CMDHELP
- CMDHELPCHK

## Source Usage Contract Crosswalk

| Command | Source | Evidence |
| --- | --- | --- |
| CMDHELP | src/cli/cmdhelp.cpp | L7: // owner: member.derald; L10: // @dottalk.usage v1; L11: // owner: DOT/CMDHELP; L12: // command: CMDHELP; L19: // usage-access: CMDHELP USAGE; COMMANDSHELP USAGE; L1646: if (u == "COMMAND-OWNED @DOTTALK.USAGE V1 SUMMARY.") return true; |
| CMDHELPCHK | src/cli/command_helpchk.cpp | L7: // owner: member.derald; L12: // @dottalk.usage v1; L13: // owner: DOT/CMDHELPCHK; L14: // command: CMDHELPCHK; L20: // usage-access: CMDHELPCHK USAGE |

## Contracts Scanner Summary

```text
root=D:\code\ccode
contract_like_docs=209
source_contract_annotation_files=51
source_usage_marker_files=317
registry_rows=35
likely_unregistered_contract_docs=179
registered_but_not_discovered=15
```
