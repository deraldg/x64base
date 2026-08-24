# DEV-01 Project Identity

```yaml
page_id: DEV-01
title: Project Identity
status: DRAFT_PATCHED
last_verified: 2026-05-24
```

## Identity

DotTalk++ / x64base is a working educational xBase / FoxPro-inspired database runtime, command shell, teaching system, metadata experiment, and architecture lab built in modern C++.

It is also now a SelfDoc system: a runtime/documentation/metadata environment that mines HELP and metadata evidence, validates reflected command/function structure, and uses that evidence to assemble manuals.

## Short form

```text
DotTalk++ is a visible database runtime with an evidence-backed documentation and metadata spine.
```

## What it is

- an educational database runtime
- an xBase/FoxPro-inspired command environment
- a modern C++ architecture lab
- a visible database teaching system
- a metadata and HELP evidence system
- a SelfDoc/manual-generation platform

## What it is not

- a finished commercial DBMS
- a blind FoxPro clone
- a nostalgia-only museum project
- a single-purpose DBF utility
- a documentation project separate from runtime

## SelfDoc identity

Observed HELP evidence:
- HELP.COMMANDS: 402 records
- HELP.HELP_TOPIC: 471 records
- HELP.HELP_ARTIFACTS: 5412 records

Observed META evidence:
- META.SYSCMD: 40 records
- META.SYSSUBCMD: 12 records
- META.SYSENTVAR: 12 records
- META.SYSFUNC: 0 records in the observed seed
- META.SYSHELP: 8 records

These counts are identity evidence: HELP is broad and richly mined; META is semantic and seeded but currently narrower.
