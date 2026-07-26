# DD-049 X64 Header-Aware Inspection / Evidence Closure v0

Created UTC: `2026-05-28T01:45:26+00:00`

## Purpose

DD-049 repairs the evidence interpretation gap left after DD-048.

Runtime and pydottalk readback are green, but the DD-046 structural inspector used classic DBF descriptor offset logic and misread the x64/v64 header.

DD-049:

```text
detects the real x64/v64 descriptor run
accepts same-stem .dtx as an x64 memo sidecar
uses pydottalk green proof as independent evidence
closes the DD-046/DD-048 probe lane without mutating data
```

## Boundary

Allowed:

```text
read probe DBF/DTX
read DD-046/DD-048 evidence
emit reports
```

Not allowed:

```text
C++ source edits
active catalog mutation
datadict_sandbox mutation
probe catalog mutation
HELP/META/CMDHELPCHK mutation
LMDB build
```
