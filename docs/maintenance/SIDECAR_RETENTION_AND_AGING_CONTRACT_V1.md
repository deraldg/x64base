# Sidecar Retention and Aging Contract V1

Status: M0 installed
Owner: member.derald
Development source: `D:\code\ccode`
Holding root: `D:\code\ccode.sidecar`

## Purpose

The sidecar is a reversible local holding lane for files that probably do not
belong in the active development tree but should not be deleted until time and
review establish their disposition.

## Contract

1. Intake is path-specific and hash-bound. Broad moves are forbidden.
2. Only untracked or ignored files may enter by ordinary housekeeping. Moving
   a tracked file requires a separately reviewed Git operation.
3. Original source-relative paths are preserved under a named batch.
4. A review date is not deletion authority.
5. Final dispositions are restore, adopt, retain longer, archive, or explicitly
   authorized deletion.
6. Active canonical tools, governed evidence, publication artifacts, personal
   material, and unresolved security-sensitive material require their own
   disposition review and are not swept into the sidecar.
7. Sidecar material is local-only, non-authoritative, and non-publishable.

## Required records

- `D:\code\ccode.sidecar\README.md`
- `D:\code\ccode.sidecar\RETENTION_POLICY_V1.md`
- `D:\code\ccode.sidecar\SIDECAR_INTAKE.csv`
- `D:\code\ccode.sidecar\holding\<batch-id>\BATCH_MANIFEST.csv`

## M0 acceptance

M0 is complete when the control files exist, the first named batch is moved,
every destination hash matches its recorded source hash, every source path is
absent, and unrelated dirty work remains untouched.
