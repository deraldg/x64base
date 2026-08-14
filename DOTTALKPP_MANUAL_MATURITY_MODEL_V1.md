# DotTalk++ Manual Maturity Model v1

Status: documentation quality gate  
Audience: human developer, AI development agent, documentation maintainer  
Source root: `D:\code\ccode`  
Created: 2026-06-28

This document defines how DotTalk++ manual material matures from harvested evidence into professional reader-facing documentation.

## Maturity Levels

| Level | Name | Meaning | Reader use |
|---|---|---|---|
| M0 | Captured | The concept was named by a user, source file, HELP row, META row, or harvest artifact. | Do not teach yet. Track it. |
| M1 | Anchored | The concept has an anchor ID and evidence paths. | Can appear in planning, appendix, or caveat prose. |
| M2 | Source-Supported | Source code, headers, or message catalogs show the command or structure exists. | Can be described with source-support caveats. |
| M3 | Runtime-Proven | A transcript proves the behavior in the current runtime. | Can be taught as a workflow. |
| M4 | Reader-Ready | The section has purpose, syntax, example, readback, caveats, anchors, and proof references. | Can appear in the user guide. |
| M5 | Reference-Complete | HELP, META, command syntax, arguments, aliases, proof status, and related commands are cataloged. | Can appear in command/function reference. |
| M6 | Release-Reviewed | Human or designated review accepted the prose, examples, and caveats. | Can be considered publication-grade. |

## Required Fields Per Manual Section

Every serious section should eventually carry:

```text
Section title
Prose role
Anchor IDs
Maturity level
Reader purpose
Source evidence
Runtime proof
Command/function surface
Preconditions
Example
Expected readback
Caveats
Next closure action
```

Short sections can imply some of this, but the information must exist somewhere in the manual family.

## Promotion Rules

M0 and M1 material may be harvested but should not be presented as normal user instructions.

M2 material may be described as source-supported. Use phrases such as:

```text
The command surface exists in source and HELP, but this section still needs a current runtime transcript.
```

M3 material may be taught as a workflow if the transcript is current and repeatable.

M4 material is reader-ready when it includes:

- what the reader is trying to accomplish
- command syntax
- a minimal example
- expected readback
- known caveats
- anchor IDs
- proof path or proof task

M5 material belongs in the command/function reference.

M6 material is the publication target.

## Maturity Matrix For Current Advanced Sections

| Section | Current level | Why | Next step |
|---|---|---|---|
| Work Areas and Cursor Control | M2 | Source and command surface found for work areas and `RECNO`. | Add transcript for `RECNO`, `GOTO`, `SKIP`, current area, and cursor restoration. |
| Record and Table Locking | M2 | `LOCK` and `UNLOCK` source and HELP messages exist. | Add transcript for record lock, table lock, status, ownership, blocked mutation, and unlock. |
| Table Buffering | M2 | `TABLE BUFFER` command and table state machinery exist. | Add transcript for buffer on/off, dirty/clean/stale/fresh, buffered replace, dump, commit, rollback. |
| Commit and Rollback | M2 | `COMMIT` and `ROLLBACK` source contracts exist. | Add transcript for successful commit, rollback, partial commit, memo flush if applicable, and index policy. |
| Indexes, CNX, CDX, and SET ORDER | M3 | Existing reader proof transcripts cover promoted CDX/CNX order paths. | Promote command reference entries and add stress/edge proofs. |
| Creating DBFs | M3 | x64 and schema DDL proof transcripts exist. | Add 128-byte vector-name proof, self-describing `X64M` readback, optional longer-name compile-time proof, and data dictionary linkouts. |
| Vectored Table and Field Names | M2 | `include/xbase_64.hpp` defines `X64M`, name-vector metadata, 128-byte compile-time defaults, and 10-byte fallback tokens. | Prove a file can explain its logical table and field names from in-file `X64M`; prove any changed compile-time name limit before documenting it as a supported build profile. |
| Project Overview and Educational Purpose | M2 | `x64base/README.md`, `x64base/README_NEW.md`, and harvested README prose define project positioning, history, and teaching goals. | Treat as reader-ready orientation after volatile status claims are checked against current runtime/proof state. |
| Manual Diagram Assets | M1 | A diagram registry and simple SVG assets now exist under `docs/manuals/assets/diagrams`. | Embed visuals section-by-section after checking each diagram against its anchor, proof state, and rendered output target. |

## Professional Documentation Standard

A mature DotTalk++ manual should read like documentation for a real database system:

- It teaches operational consequences, not just commands.
- It distinguishes table data, buffer state, lock state, cursor state, index state, and memo state.
- It names failure modes directly.
- It shows how to verify work with readback.
- It never confuses source ambition with runtime proof.
- It keeps developer machinery available without forcing it into the user path.

## Next Maturity Pass

The next maturity pass should create proof scripts and transcripts for:

```text
reader_manual_cursor_control_v1
reader_manual_lock_unlock_v1
reader_manual_table_buffer_commit_v1
reader_manual_table_buffer_rollback_v1
reader_manual_commit_partial_lock_conflict_v1
```

After those transcripts exist, the advanced sections can move from M2 to M3 and the corresponding command reference entries can move toward M4/M5.
