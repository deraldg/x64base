# DD-061 Active Data Dictionary Consumer / Read API Plan v0

Created UTC: `2026-05-28T03:45:45+00:00`

## Purpose

DD-061 defines the first read-only consumer/API plan for the active Data Dictionary catalog after DD-060 closed the promotion cycle.

It plans:

```text
DotTalk++ DDICT read surfaces
pydottalk read helper surfaces
query patterns over active catalog tables
read-only boundaries
future phases for prototype and runtime command planning
```

## Boundary

Allowed:

```text
read DD-060/DD-059 reports
inspect active artifact evidence
emit read API plans
emit candidate read-only API skeleton as a report artifact
```

Not allowed:

```text
active catalog mutation
source edits
runtime command registration
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
