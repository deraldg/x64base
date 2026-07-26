# DD-030 Script Boundary Disposition / Maintenance Package Classification v0

Status: report-only design and tool package  
Created UTC: 2026-05-27T19:01:46.559641+00:00  
Scope: Data Dictionary / DotTalk++ / x64base redocumentation lane

## Purpose

DD-030 resolves the blocker exposed by DD-029: root-level `mdo_*` maintenance package scripts were correctly classified as HIGH because they are executable scripts outside the stable source baseline.

DD-030 does **not** delete, move, rewrite, execute, or promote those scripts. It classifies them and produces a boundary ledger so the project can decide whether each package is:

- temporary generated package residue
- accepted maintenance evidence
- source-controlled maintenance tooling
- archive candidate
- excluded from stable source fingerprint after evidence acceptance
- human-triage-required

## Inputs

Primary input:

```text
DD-029 artifact disposition run directory
  or
DD-029 artifact disposition rows CSV
```

Expected DD-029 files:

```text
dd029_artifact_disposition_rows.csv
dd029_disposition_summary.csv
dd029_artifact_disposition_manifest.json
DD029_ARTIFACT_DISPOSITION_REPORT.md
```

## Outputs

```text
dd030_script_boundary_manifest.json
dd030_script_boundary_rows.csv
dd030_package_summary.csv
dd030_exclusion_policy_patch_proposal.json
dd030_next_actions.csv
DD030_SCRIPT_BOUNDARY_REPORT.md
```

## Boundary

DD-030 is report-only.

It does not:

- edit source
- run PowerShell scripts
- launch DotTalk++
- build C++
- mutate HELP, META, CMDHELPCHK
- write DBF, CDX, LMDB, or catalog data
- accept a new baseline
- change exclusion policies directly

## Classification rule

The default policy treats root-level `mdo_*` package folders as maintenance package evidence, not product source. Executable scripts inside those packages remain blocking until reviewed, but DD-030 can recommend a policy patch to exclude accepted package folders from stable source fingerprinting while preserving them as maintenance evidence.

## Recommended downstream sequence

```text
DD-029 disposition blocked on maintenance scripts
  -> DD-030 classify script/package boundaries
  -> DD-031 apply reviewed exclusion/disposition policy to scanner, still report-only unless authorized
  -> DD-028 rerun current baseline check
  -> DD-027 accept DDBASE-stable-v1 only after clean/pass sequence
```
