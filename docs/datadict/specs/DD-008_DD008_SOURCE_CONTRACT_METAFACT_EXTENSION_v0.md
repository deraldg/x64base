# DD-008 — Source Contract + MetaFact Manifest Extension v0

Status: **REPORT_ONLY**  
Generated: 2026-05-27T14:41:57+00:00  
Input repo package: `ccode_homegrown_20260527-055727.zip`

## Purpose

DD-008 connects three existing evidence streams into the data-dictionary path:

1. `@dottalk.usage v1` source contracts.
2. command registration evidence from the shell/registry scan.
3. the existing `dt::meta::MetaFact` model in `include/dt/meta/metafact.hpp` and `src/meta/metacollect.cpp`.

This is intentionally an extension to the DD-006/DD-007 physical manifest path, not a separate metadata universe.

## Counts

| Item | Count |
|---|---:|
| usage/source-contract fact rows | 200 |
| registry fact rows | 222 |
| MetaFact domains parsed | 10 |
| MetaFact evidence kinds parsed | 8 |
| metacollect-compatible fact seed rows | 1233 |
| source anchor scan rows | 325 |
| HELP/message anchor rows | 55 |
| command reconciliation rows | 235 |
| matched compact usage/registry rows | 170 |
| usage without compact registry match | 21 |
| registry without compact usage match | 44 |

## Design decision

`dt::meta::MetaFact` should be treated as the current bridge into dictionary facts. It is not yet the whole dictionary, but it already names the right fact families: command, function, subcommand, entry variant, argument, help text, message, field dictionary, and runtime proof.

The dictionary should therefore add source-contract and MetaFact extensions rather than inventing a disconnected catalog model.

## Manifest extension objects

DD-008 reserves these extension objects:

```text
source_contracts
registry_entries
metafacts
metafact_domain_bridge
metafact_evidence_bridge
command_reconciliation
help_message_anchors
```

## Trust boundary

A usage block is source contract evidence. A registry row is dispatch/registration evidence. A MetaFact seed row is source-catalog or source-registry evidence. None of these alone is runtime proof.

Runtime proof still requires transcripts, generated reports, or future controlled DotTalk++ runs.

## Boundary preserved

No repo files were changed. No C++ was built. No DotTalk++ runtime was launched. No HELP, META, CMDHELPCHK, DBF, CDX, LMDB, source, catalog, or runtime data mutation occurred.
