# DotTalk++ Manual Anchor Map v1

Status: working convergence map  
Audience: human developer, AI development agent, documentation maintainer  
Source root: `D:\code\ccode`  
Created: 2026-06-28

This document gives the manual generation work real anchors into the help, SelfDoc, META, harvest, manualgen, runtime proof, and data dictionary systems. It is the bridge between bottom-up evidence and top-down reader manuals.

The machine-readable companion is:

- `docs/manuals/anchors/manual_generation_anchor_map_v1.csv`

The prose companion is:

- `DOTTALKPP_MANUAL_PROSE_GUIDE_V1.md`

## Purpose

DotTalk++ now has enough harvested material that prose alone is not a safe organizing unit. The manual needs stable anchors that can be traced back to the system that produced the claim.

The anchor rule is:

```text
Do not promote a manual claim as reader-facing unless it has an anchor.
The anchor must identify the source layer, evidence path, manual target, confidence state, and next closure action.
```

This does not mean every reader paragraph needs a footnote. It means every command family, data structure, schema rule, HELP surface, index/memo claim, and developer workflow must be tied to an anchor record somewhere in the map.

## Convergence Model

The documentation system should converge in this order:

```text
Source contracts
  -> HELP DBFs and metadata
  -> META/selfdoc inventories
  -> cmdhelpchk and maintenance validation
  -> runtime proof transcripts
  -> manualgen reviewed/published artifacts
  -> reader manual, developer manual, data dictionary
```

Each layer has a different job:

| Layer | Job |
|---|---|
| Source contracts | Define what the runtime is allowed to do. |
| HELP DBFs | Expose command and topic language to the user surface. |
| META | Attach semantic identity to commands, functions, arguments, messages, and help links. |
| SelfDoc | Preserve provenance, tool identity, collection limits, and artifact lifecycle. |
| cmdhelpchk | Detect missing, mismatched, or drifting help metadata. |
| Runtime proofs | Show what the executable actually accepts, creates, reads, indexes, and orders. |
| manualgen | Convert reviewed evidence into stable manual sections and catalogs. |
| Data dictionary | Store table, field, index, relation, evidence, and schema meaning. |
| Reader manuals | Explain only the material that is useful and sufficiently grounded for users. |

## Anchor States

Use these confidence states consistently:

| State | Meaning |
|---|---|
| `observed` | The file, table, command, or policy exists and has been located. |
| `proven` | A runtime transcript or readback validates the behavior. |
| `candidate` | The source or harvest suggests the claim, but reader wording needs proof or review. |
| `drift` | The evidence exists but a catalog, count, path, duplicate, or state mismatch is known. |
| `deferred` | The concept is important, but systematic harvesting has not closed it yet. |

## Core Anchors

| Anchor ID | Layer | Evidence path | Manual target | State | Next closure action |
|---|---|---|---|---|---|
| `ANCHOR-X64-TRINITY` | Source contract | `include/xbase.hpp`; `include/xbase_vfp.hpp`; `include/xbase_64.hpp` | Trinity Headers; xBase Lineage; x64 Workflow | observed | Harvest constants, structs, and compatibility rules into data dictionary rows. |
| `ANCHOR-X64-VECTOR-NAMES` | Source contract | `include/xbase_64.hpp` | Vectored Table Names and Field Names | candidate | Add runtime proof for 128-byte names, self-describing `X64M` readback, and any longer-name compile-time policy if constants change. |
| `ANCHOR-X64-MEMOS` | Source contract | `include/memo/dtx_format.hpp`; x64 memo code paths | Theoretical Limits; x64 Memo Limits | candidate | Add proof scripts for memo object IDs, DTX attachment, readback, and failure boundaries. |
| `ANCHOR-X64-INDEXING` | Runtime/indexing | CDX/LMDB proof scripts; x64 index source | Indexes, CNX, CDX, and SET ORDER | proven/candidate | Keep CDX/SET ORDER proof promoted; separately harvest x64 theoretical index limits. |
| `ANCHOR-HELP-COMMANDS` | HELP runtime | `dottalkpp/data/help/COMMANDS.dbf` | Commands and Functions Reference | observed | Generate command reference pages from COMMANDS plus META identity and proof state. |
| `ANCHOR-HELP-CMDARGS` | HELP runtime | `dottalkpp/data/help/CMD_ARGS.dbf` | Command syntax and arguments | observed | Join command rows to argument rows; flag arguments without proof examples. |
| `ANCHOR-HELP-TOPICS` | HELP runtime | `dottalkpp/data/help/HELP_TOPIC.dbf` | Help topics and reader navigation | observed | Map topic rows to manual sections and remove orphan topics or mark as internal. |
| `ANCHOR-HELP-ARTIFACTS` | HELP runtime | `dottalkpp/data/help/HELP_ARTIFACTS.dbf`; `dottalkpp/data/help/HELP_ARTIFACTS.dtx` | Embedded help artifacts | observed | Classify artifacts as reader, developer, legacy, or case-study material. |
| `ANCHOR-META-COLLECT` | META semantic layer | `include/dt/meta/metafact.hpp`; `include/dt/meta/metacollect.hpp`; `x64base/src/tools/metacollect_main.cpp`; `metacollect_facts.csv` | Manual evidence and command identity | observed | Re-run collection and compare with `metacollect_compare.csv` before promotion. |
| `ANCHOR-CMDHELPCHK` | Validation | `dottalkpp/tools/help/cmdhelpchk_v2_scan.py`; cmdhelpchk maintenance lane | HELP/META alignment | observed | Use report-only checks as a gate before regenerating command/function sections. |
| `ANCHOR-COMMAND-USAGE-HARVEST` | Source usage contracts | `DOTTALKPP_COMMAND_REFERENCE_GUIDE_V1.md`; `docs/manuals/command_reference/COMMAND_REFERENCE_USAGE_CONTRACT_HARVEST_V1.md`; `docs/manuals/command_reference/command_reference_guide_v1.csv`; `docs/manuals/command_reference/command_reference_usage_contract_harvest_v1.csv`; source `@dottalk.usage v1` blocks | Commands and Functions Reference | observed | Join source usage contracts with HELP/META rows and runtime proof state before reader promotion. |
| `ANCHOR-MANUAL-DIAGRAMS` | Visual/manual assets | `docs/manuals/assets/diagrams/MANUAL_DIAGRAM_ASSET_REGISTRY_V1.md`; `docs/manuals/assets/diagrams/manual_diagram_asset_registry_v1.csv`; `docs/manuals/assets/diagrams/*.svg` | Visual Manual Assets; Evidence Anchors and Manual Generation; section-level diagrams | observed | Embed diagrams into relevant manual sections only after checking that each visual claim matches its section anchor and maturity state. |
| `ANCHOR-SELFDOC-POLICY` | SelfDoc policy | `selfdoc/SELFDOC_*_POLICY_v0.md`; `selfdoc/pipeline_manifest.yaml`; `selfdoc/tool_manifest.yaml` | Developer Appendix; provenance rules | observed | Add policy excerpts to developer manual only; keep reader copy concise. |
| `ANCHOR-MANUALGEN-LIFECYCLE` | Manualgen | `docs/manuals/developer/manualgen/MDO-*.md`; `PIP-*.md`; accepted catalogs | Developer manual lifecycle | observed | Normalize latest lifecycle state into a compact "how manuals are made" section. |
| `ANCHOR-MANUALGEN-CATALOG` | Manualgen catalog | `docs/manuals/developer/manualgen/accepted_catalogs/` | Published manual references | drift | Repair or waive duplicate `EXTRA_MAN_DBF` visibility before calling catalog status clean. |
| `ANCHOR-DATADICT-SCHEMAS` | Data dictionary | `docs/datadict/reports/`; `include/datadict/`; `include/cli/cmd_ddict.hpp` | Data Dictionaries | observed | Map schema proof reports to dictionary entities, fields, relations, and evidence rows. |
| `ANCHOR-RUNTIME-PROOFS` | Runtime proof | `docs/manuals/developer/proofs/` | Promoted command paths | proven | Keep transcript filenames in manual sections and promote only successful, repeatable paths. |
| `ANCHOR-LABTALK-CASES` | Case/manual overlay | `docs/cases/`; LabTalk catalog docs | LabTalk Case Catalog | observed | Keep cases as optional educational overlays, not runtime dependencies. |
| `ANCHOR-X64BASE-README` | Project positioning | `x64base/README.md`; `x64base/README_NEW.md`; attached README harvest text | What DotTalk++ Is; History; Educational Purpose; Design Philosophy; Working Model; Current Status Snapshot | observed | Keep overview prose curated and reader-facing; verify volatile status claims before release. |
| `ANCHOR-CURSOR-WORKAREAS` | Runtime state | `src/cli/workareas.hpp`; `src/cli/cmd_recno.cpp`; `src/browser/browser_builders.cpp`; cursor/status messages | Work Areas and Cursor Control | observed | Add proof scripts for `RECNO`, `GOTO`, `SKIP`, current-area selection, and cursor restoration. |
| `ANCHOR-LOCKING` | Concurrency | `src/cli/cmd_lock.cpp`; `src/cli/cmd_unlock.cpp`; `include/xbase_locks.hpp`; lock help messages | Record and Table Locking | observed | Add runtime proof for record lock, table lock, status, ownership, failed mutation under lock, and unlock. |
| `ANCHOR-TABLE-BUFFER` | Buffering | `src/cli/table_buffer.cpp`; `src/cli/table_state.hpp`; `src/cli/table_write.hpp`; table-buffer help messages | Table Buffering | observed | Add proof scripts for buffer on/off, dirty/clean/stale/fresh, buffered `REPLACE`, `COMMIT`, and `ROLLBACK`. |
| `ANCHOR-COMMIT-ROLLBACK` | Transaction-like lifecycle | `src/cli/cmd_commit.cpp`; `src/cli/cmd_rollback.cpp`; `src/cli/table_state.cpp` | Commit and Rollback | observed | Promote current RAM-buffer semantics; mark persistent journal hooks as future/stub until proven. |

## Manual Generation Rules

1. Start with the anchor, not the prose.
2. Classify the target reader: ordinary user, developer, AI maintainer, data dictionary consumer, or case-study reader.
3. Check whether the anchor state is `proven`, `observed`, `candidate`, `drift`, or `deferred`.
4. Promote `proven` behavior into direct instructions.
5. Promote `observed` structure into architecture or glossary language.
6. Keep `candidate` and `deferred` material in planning, appendices, or explicit caveat sections.
7. Never hide `drift`; either repair it, waive it with a reason, or keep it out of reader instructions.

## Prose Generation Rules

Anchors are not prose. They are the evidence keys used to write prose safely.

Each manual section should declare or imply a prose role:

| Prose role | Use for |
|---|---|
| `orientation` | What a subsystem is and why it matters. |
| `tutorial` | How to complete a proven workflow. |
| `reference` | Commands, functions, arguments, files, statuses, fields, and catalog entries. |
| `concept` | Design ideas such as trinity headers, x64 vectors, memo limits, and indexing model. |
| `caveat` | Drift, failure modes, unproven edges, and compatibility boundaries. |
| `handoff` | Developer or AI next steps, gates, and closure actions. |
| `data_dictionary` | Entity, field, relation, index, schema, and evidence descriptions. |

The prose pattern is:

```text
Anchor -> reader purpose -> command or concept -> proof/readback -> caveat or next step
```

Use `DOTTALKPP_MANUAL_PROSE_GUIDE_V1.md` for the detailed prose contract.

## Data Dictionary Rules

Manual anchors and data dictionary rows should share concepts, but they should not collapse into one artifact.

Manual anchors answer:

```text
What can we safely say to a reader?
```

Data dictionary rows answer:

```text
What object, field, relation, index, source, or proof exists in the system?
```

When harvesting data dictionary material:

- Use `ANCHOR-X64-TRINITY` for structural contracts.
- Use `ANCHOR-HELP-*` for command and topic surfaces.
- Use `ANCHOR-META-COLLECT` for semantic IDs and joins.
- Use `ANCHOR-RUNTIME-PROOFS` for validated behavior.
- Use `ANCHOR-MANUALGEN-*` for reviewed publication state.

## Immediate Manual Impact

The reader manual should now treat these sections as anchored:

- Trinity Headers: `ANCHOR-X64-TRINITY`
- What DotTalk++ Is: `ANCHOR-X64BASE-README`
- Theoretical Limits of x64base: `ANCHOR-X64-TRINITY`, `ANCHOR-X64-MEMOS`, `ANCHOR-X64-INDEXING`
- Vectored Table Names and Field Names: `ANCHOR-X64-VECTOR-NAMES`
- Creating DBFs: `ANCHOR-RUNTIME-PROOFS`
- Indexes, CNX, CDX, and SET ORDER: `ANCHOR-X64-INDEXING`, `ANCHOR-RUNTIME-PROOFS`
- Commands and Functions Reference: `ANCHOR-HELP-COMMANDS`, `ANCHOR-HELP-CMDARGS`, `ANCHOR-META-COLLECT`, `ANCHOR-CMDHELPCHK`, `ANCHOR-COMMAND-USAGE-HARVEST`
- Work Areas and Cursor Control: `ANCHOR-CURSOR-WORKAREAS`
- Record and Table Locking: `ANCHOR-LOCKING`
- Table Buffering: `ANCHOR-TABLE-BUFFER`
- Commit and Rollback: `ANCHOR-COMMIT-ROLLBACK`
- Developer Appendix: `ANCHOR-SELFDOC-POLICY`, `ANCHOR-MANUALGEN-LIFECYCLE`, `ANCHOR-MANUALGEN-CATALOG`

## Next Build Step

The next harvest task should generate a command/function reference skeleton from HELP and META using this anchor pattern:

```text
command_id
primary_name
aliases
argument_rows
help_topic
meta_identity
proof_status
manual_section
reader_status
```

That will let the command and function manual grow from the ground up while remaining readable from the top down.
