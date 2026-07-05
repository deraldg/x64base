# Lab: Self-Documenting Systems - Comments to Contracts to HELP v0

Status: first runnable lab

Audience: developer, maintainer, advanced student

## Purpose

This lab proves the smallest LabTalk path for the SelfDoc lane:

1. Runtime HELP can explain `CMDHELP` and `CMDHELPCHK`.
2. `CMDHELPCHK` can show its validation surface.
3. Existing comments/contracts material can be crosswalked without mutating HELP,
   metadata DBFs, source files, or manual publication files.

## Narrow Command Set

- `CMDHELP`
- `CMDHELPCHK`

## Runnable Artifacts

- DotTalk script: `cmdhelp_cmdhelpchk_selfdoc_v0.dts`
- Lab runner: `run_selfdoc_first_lab.ps1`
- Generated crosswalk: `D:/code/ccode/labtalk/reports/selfdoc/lab_selfdoc_first_crosswalk_v0.md`

## Evidence Rule

This lab is report-only. It reads runtime HELP output, source usage-contract
headers, and the contracts scanner summary. It does not rebuild HELP DATA, modify
`CMDHELPCHK`, repair contracts, move files, or publish manual content.

## First Gate

Closed when LabTalk captures a portal transcript for
`runtime.selfdoc.comments_to_contracts.first_lab` and the transcript points to
the generated crosswalk report.

## Next Gate

Review the first proof artifact, then expand the crosswalk to one additional
documentation command only after the evidence roles remain clear.
