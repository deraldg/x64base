# BBOX DOTREF Integration Plan v1

Status: BBOX_DOTREF_PROOF_RECONCILED_GREEN

## Purpose

Record the reconciled compiled DOTREF state for BBOX after runtime, CMDHELP, canonical-header, and operator-accepted router proof were closed.

## Current Proven State

- BBOX runtime path is closed by MDO-312.
- BBOX CMDHELP path is closed by MDO-315.
- BBOX DOTREF canonical-header reconciliation is closed by later DOTREF repair/reconciliation work.
- BBOX DOTHELP and HELP /DOT proof are closed by later operator-accepted runtime smoke.
- Raw HELP DBF append is forbidden for this lane.
- DOTHELP BBOX and HELP /DOT BBOX are green on the reconciled canonical DOTREF path.

## Candidate DOTREF Topic

Topic: BBOX

Syntax: BBOX [USAGE|MODEL|LANES|COMMENTS|HELP|MANUALGEN|DATADICT|MESSAGING|MAINT]

Summary: Teach and inspect the Blackbox model: data enters a processing system and information comes out.

## Canonical Header Note

The canonical live DOTREF header is:

- `include\dotref.hpp`

The older `src\help\dotref.hpp` path was duplicate/noncanonical drift.

## Continuity Note

Historical planning in this lane treated DOTREF proof as future work.

Current continuity rule:

- preserve the historical planning record
- do not keep describing BBOX DOTREF visibility as still pending
- treat runtime, CMDHELP/current HELP DATA, DOTREF/router, and CMDHELPCHK as separate proof layers even when all are green
