# CORRECTION: the transcript beside this file is a FALSE GREEN

    applies to : workspace_writeback_proof_teed_20260812T174605Z.log
    filed      : 2026-08-12 (same day the log was produced)
    filed by   : member.ai.claude.cowork
    lane       : AIF-070 (coworker), writeback arm
    status     : the log is RETRACTED as evidence, and DELIBERATELY NOT DELETED

## What the log claims

Six `WORKSPACE WRITEBACK` markers (WB_T1..WB_T6) reading `.T.` on a Linux
build, presented as runtime proof that the regression passed on that platform.

## Why it does not support that claim

The spec wrote to one directory and read from another.

- `WORKSPACE WRITEBACK TO <rel>`, `ERASE DIR <rel>` and `FILE(<rel>)` resolved
  their relative token against the **process CWD**.
- `SET PATH DBF <rel>` resolved the same token against the **DATA root**.

Both spellings in the spec are the identical string `DBF/wbregress`. They name
the same directory only when cwd happens to equal DATA -- which is exactly what
`datarun.ps1` arranges, and why this went unnoticed.

That run was made from a cwd that is NOT the DATA root. Its writeback landed in
`dottalkpp/DBF/wbregress`. Its assertions opened `dottalkpp/data/DBF/wbregress`
-- a directory still populated by the maintainer's EARLIER Windows runs. The
markers read correct-looking values out of somebody else's output and reported
green.

**Nothing in that log is a statement about the code it was run to test.**

## How it was caught

Not by inspection. The stale directory was later deleted as litter, and the
same spec, on the same binary, at the same cwd, went red -- including three
markers that had been green an hour before. Nothing about the arms had changed;
only the accidental input had gone away.

## The shape worth keeping

The spec's own header warned about this exact failure -- "a leftover wbregress
makes WRITEBACK refuse on collision while the reads below happily consume the
PREVIOUS run's files -- a stale false green, the worst kind" -- and added an
`ERASE DIR` pre-clean to prevent it. The pre-clean ran. It reported success. It
cleaned the CWD-relative directory while the reads consumed the DATA-relative
one, because the guard resolved paths the same wrong way the thing it guarded
did.

A guard that shares its subject's bug does not fail loudly. It agrees. Two
components agreeing is not evidence that either is right, and "they match" is
not a specification.

## Disposition

- The log is **kept, unedited**. It is the evidence for this correction; a
  deleted false green teaches nothing and leaves the closeout's retraction
  unsupported.
- Superseded by `workspace_writeback_pathfix_proof_20260812T195516Z.log`
  (13/13 markers, after all four surfaces were routed through
  `paths::resolve_in_slot`), whose new arms were each additionally shown to
  FAIL under targeted mutation before any green was accepted.
- The Windows transcript from the same day is NOT retracted -- it ran with
  cwd = DATA, so its four resolutions agreed and the run was self-consistent.
  It is, however, scoped to the pre-fix source.
