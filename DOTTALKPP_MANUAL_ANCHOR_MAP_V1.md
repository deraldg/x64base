# DotTalk++ Manual Anchor Map v1

Status: working convergence map  
Audience: human developer, AI development agent, documentation maintainer  
Source root: `D:\code\ccode`  
Created: 2026-06-28

This document gives the manual generation work real anchors into the help, SelfDoc, META, harvest, manualgen, runtime proof, and data dictionary systems. It is the bridge between bottom-up evidence and top-down reader manuals.

**The CSV is the SOURCE. The anchor tables below are GENERATED from it** by
`tools/fullstack_docs/derive_anchor_map.py`; edit the CSV and re-run, never the tables.
Everything else on this page is prose and is preserved as written.

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
| `proven_candidate` | Part of the anchor is runtime-proven and part is not; do not promote the whole row. |

## Core Anchors

<!-- BEGIN GENERATED anchors:core -- derive_anchor_map.py; edit the CSV, not this table -->
| Anchor ID | Layer | Evidence path | Manual target | State | Next closure action |
|---|---|---|---|---|---|
| `ANCHOR-X64-TRINITY` | Source contract | `include/xbase.hpp`; `include/xbase_vfp.hpp`; `include/xbase_64.hpp` | Trinity Headers; xBase Lineage; x64 Workflow | observed | Harvest constants, structs, and compatibility rules into data dictionary rows. |
| `ANCHOR-X64-VECTOR-NAMES` | Source contract | `include/xbase_64.hpp` | Vectored Table Names and Field Names | candidate | Add runtime proof for 128-byte names, self-describing `X64M` readback, and any longer-name compile-time policy if constants change. |
| `ANCHOR-X64-MEMOS` | Source contract | `include/memo/dtx_format.hpp`; x64 memo code paths | Theoretical Limits; x64 Memo Limits | candidate | Add proof scripts for memo object IDs, DTX attachment, readback, and failure boundaries. |
| `ANCHOR-X64-INDEXING` | Runtime/indexing | `docs/manuals/developer/proofs/reader_manual_order_cdx_v2.transcript.txt`; `docs/manuals/developer/proofs/reader_manual_order_cnx_v1.transcript.txt`; x64 index source | Indexes, CNX, CDX, and SET ORDER | proven_candidate | Keep CDX/SET ORDER proof promoted; separately harvest x64 theoretical index limits. |
| `ANCHOR-HELP-COMMANDS` | HELP runtime | `dottalkpp/data/help/COMMANDS.dbf` | Commands and Functions Reference | observed | Generate command reference pages from COMMANDS plus META identity and proof state. |
| `ANCHOR-HELP-CMDARGS` | HELP runtime | `dottalkpp/data/help/CMD_ARGS.dbf` | Command syntax and arguments | observed | Join command rows to argument rows; flag arguments without proof examples. |
| `ANCHOR-HELP-TOPICS` | HELP runtime | `dottalkpp/data/help/HELP_TOPIC.dbf` | Help topics and reader navigation | observed | Map topic rows to manual sections and remove orphan topics or mark as internal. |
| `ANCHOR-HELP-ARTIFACTS` | HELP runtime | `dottalkpp/data/help/HELP_ARTIFACTS.dbf`; `dottalkpp/data/help/HELP_ARTIFACTS.dtx` | Embedded help artifacts | observed | Classify artifacts as reader, developer, legacy, or case-study material. |
| `ANCHOR-META-COLLECT` | META semantic layer | `include/dt/meta/metafact.hpp`; `include/dt/meta/metacollect.hpp`; `x64base/src/tools/metacollect_main.cpp`; `metacollect_facts.csv`; `metacollect_compare.csv` | Manual evidence and command identity | observed | Re-run collection and compare facts before promotion. |
| `ANCHOR-CMDHELPCHK` | Validation | `dottalkpp/tools/help/cmdhelpchk_v2_scan.py`; `dottalkpp/scripts/maintenance/lanes/cmdhelpchk` | HELP/META alignment | observed | Use report-only checks as a gate before regenerating command/function sections. |
| `ANCHOR-COMMAND-USAGE-HARVEST` | Source usage contracts | `DOTTALKPP_COMMAND_REFERENCE_GUIDE_V1.md`; `docs/manuals/command_reference/COMMAND_REFERENCE_USAGE_CONTRACT_HARVEST_V1.md`; `docs/manuals/command_reference/command_reference_guide_v1.csv`; `docs/manuals/command_reference/command_reference_usage_contract_harvest_v1.csv`; source @dottalk.usage v1 blocks | Commands and Functions Reference | observed | Join source usage contracts with HELP/META rows and runtime proof state before reader promotion. |
| `ANCHOR-MANUAL-DIAGRAMS` | Visual/manual assets | `docs/manuals/assets/diagrams/MANUAL_DIAGRAM_ASSET_REGISTRY_V1.md`; `docs/manuals/assets/diagrams/manual_diagram_asset_registry_v1.csv`; `docs/manuals/assets/diagrams/*.svg` | Visual Manual Assets; Evidence Anchors and Manual Generation; section-level diagrams | observed | Embed diagrams into relevant manual sections only after checking that each visual claim matches its section anchor and maturity state. |
| `ANCHOR-SELFDOC-POLICY` | SelfDoc policy | `selfdoc/SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0.md`; `selfdoc/SELFDOC_COLLECTION_IMPERFECTION_POLICY_v0.md`; `selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md`; `selfdoc/SELFDOC_INVENTORY_PROBE_PLAN_v0.md`; `selfdoc/pipeline_manifest.yaml`; `selfdoc/tool_manifest.yaml` | Developer Appendix; provenance rules | observed | Add policy excerpts to developer manual only; keep reader copy concise. |
| `ANCHOR-MANUALGEN-LIFECYCLE` | Manualgen | `docs/manuals/developer/manualgen/MDO-*.md`; `docs/manuals/developer/manualgen/PIP-*.md`; `docs/manuals/developer/manualgen/accepted_catalogs` | Developer manual lifecycle | observed | Normalize latest lifecycle state into a compact "how manuals are made" section. |
| `ANCHOR-MANUALGEN-CATALOG` | Manualgen catalog | `docs/manuals/developer/manualgen/accepted_catalogs` | Published manual references | drift | Repair or waive duplicate `EXTRA_MAN_DBF` visibility before calling catalog status clean. |
| `ANCHOR-DATADICT-SCHEMAS` | Data dictionary | `docs/datadict/reports`; `include/datadict`; `include/cli/cmd_ddict.hpp` | Data Dictionaries | observed | Map schema proof reports to dictionary entities, fields, relations, and evidence rows. |
| `ANCHOR-RUNTIME-PROOFS` | Runtime proof | `docs/manuals/developer/proofs` | Promoted command paths | proven | Keep transcript filenames in manual sections and promote only successful, repeatable paths. |
| `ANCHOR-LABTALK-CASES` | Case/manual overlay | `docs/cases`; LabTalk catalog docs | LabTalk Case Catalog | observed | Keep cases as optional educational overlays, not runtime dependencies. |
| `ANCHOR-X64BASE-README` | Project positioning | `x64base/README.md`; `x64base/README_NEW.md`; attached README harvest text | What DotTalk++ Is; History; Educational Purpose; Design Philosophy; Working Model; Current Status Snapshot | observed | Keep overview prose curated and reader-facing; verify volatile status claims before release. |
| `ANCHOR-CURSOR-WORKAREAS` | Runtime state | `src/cli/workareas.hpp`; `src/cli/cmd_recno.cpp`; `src/browser/browser_builders.cpp`; `cursor/status messages` | Work Areas and Cursor Control | observed | Add proof scripts for `RECNO`, `GOTO`, `SKIP`, current-area selection, and cursor restoration. |
| `ANCHOR-LOCKING` | Concurrency | `src/cli/cmd_lock.cpp`; `src/cli/cmd_unlock.cpp`; `include/xbase_locks.hpp`; lock help messages | Record and Table Locking | observed | Add runtime proof for record lock, table lock, status, ownership, failed mutation under lock, and unlock. |
| `ANCHOR-TABLE-BUFFER` | Buffering | `src/cli/table_buffer.cpp`; `include/cli/table_state.hpp`; `include/cli/table_write.hpp`; table-buffer help messages | Table Buffering | observed | Add proof scripts for buffer on/off, dirty/clean/stale/fresh, buffered `REPLACE`, `COMMIT`, and `ROLLBACK`. |
| `ANCHOR-COMMIT-ROLLBACK` | Transaction-like lifecycle | `src/cli/cmd_commit.cpp`; `src/cli/cmd_rollback.cpp`; `src/cli/table_state.cpp` | Commit and Rollback | observed | Promote current RAM-buffer semantics; mark persistent journal hooks as future/stub until proven. |
<!-- END GENERATED anchors:core -->

## Spine Anchors (added 2026-09-15)

These bind material the manual ALREADY CARRIES. They were unanchored because the core table
was written 2026-06-28 and the doctrine spine kept growing after it -- dev-21, dev-22 and dev-23
were all written later. An unanchored chapter is not a missing chapter; it is a chapter whose
claims have no recorded evidence path, which is what the anchor rule exists to prevent.

<!-- BEGIN GENERATED anchors:spine -- derive_anchor_map.py; edit the CSV, not this table -->
| Anchor ID | Layer | Evidence path | Manual target | State | Next closure action |
|---|---|---|---|---|---|
| `ANCHOR-SQLSEL-SURFACE` | Source usage contracts | `docs/manuals/user/sqlsel.md`; `docs/manuals/assimilation/sqlsel-state-of-the-surface.md`; `src/cli/sqlsel_statement.hpp`; `src/cli/sqlsel_statement.cpp`; `src/cli/cmd_sql_help.cpp` | SQLsel: typed SQL over x64base work areas; SQL conformance boundary | observed | Bind the user chapter to the SQLite oracle transcripts; state which SELECT clauses are refused rather than unimplemented. |
| `ANCHOR-WORKSPACES-MINIDB` | Runtime state | `docs/manuals/user/workspaces-and-minidbs.md`; `src/cli/cmd_workspace.cpp`; `src/workspace/schema_workspace.cpp`; `include/xbase/workspace_membership.hpp` | Workspaces and MiniDBs; Workspace catalog and durable identity | observed | Reconcile the chapter against the full WORKSPACE verb list; the June command guide lists six of twenty-one. |
| `ANCHOR-BUILD-SYSTEM` | Build/toolchain | `docs/manuals/developer/dev/dev-21-build-system.md`; `CMakePresets.json`; `CMakeLists.txt`; `build.ps1`; `BUILDING.md`; `vcpkg.json` | Build System; Getting Started: Installation | observed | Bind the chapter's measured landmines to preset names; re-verify platform status each release. |
| `ANCHOR-UIDEF-LANGUAGE` | UI contract | `docs/manuals/developer/dev/dev-22-uidef-gui-language.md`; `gui/uidef/`; `src/cli/app_gui.cpp` | The UIDEF GUI Language; Application UI DSL lane | observed | Resolve section 17 of the chapter, where the chapter and the v1 contract disagree out loud. |
| `ANCHOR-DOTSCRIPT` | Script surface | `docs/manuals/developer/dev/dev-06-dotscript.md`; `DOTSCRIPT_README_TESTING.md`; `samples/` | DotScript; DotScript Language Guide | deferred | dev-06 is 543 bytes against a published language-guide page; harvest the script grammar before promotion. |
| `ANCHOR-EXPRESSION-FUNCTIONS` | Expression engine | `docs/manuals/developer/dev/dev-11-expression-engine.md`; `src/cli/expr/`; `SYSFUNC_IMPORT_v1.csv`; `docs/manuals/developer/manualgen/harvested/META_SYSFUNC.csv` | Expression Engine; Function Catalog | observed | Join SYSFUNC rows to proof state; AIF-117 is open against the bare-predicate path and must be cited as a caveat. |
| `ANCHOR-RELATIONS-ERSATZ` | Relational traversal | `docs/manuals/developer/dev/dev-12-relations-workspaces-and-tuple-traversal.md`; `src/cli/set_relations.cpp`; `src/xbase/relation_wire.cpp`; `src/browser/browser_relation_adapter.cpp` | Relations, Workspaces, and Tuple Traversal; RelTalk | observed | Promote the Cascade double-milestone transcripts where SET RELATION and SQLsel agreed on one 34-table graph. |
| `ANCHOR-TUPLE-PROJECTION` | Projection surface | `src/cli/cmd_tuple.hpp`; `src/cli/tuple_types.hpp`; `src/cli/db_tuple_stream.cpp` | TupTalk; Tuple projections, export, and validation | observed | Add proof scripts for projection, export, and relation-aware row output before reader promotion. |
| `ANCHOR-BROWSERS-WORKBENCH` | Front end | `docs/manuals/developer/dev/dev-13-browsers-and-tui.md`; `src/browser/`; `src/tv/`; `src/gui/wx/` | Browsers and TUI; Arctic TUI; Parallel GUI/TUI | observed | Keep the open-architecture rule visible: the runtime owns truth, the front ends consume it. |
| `ANCHOR-REGRESSION-SUITE` | Validation | `docs/manuals/developer/dev/dev-16-smoke-tests-and-canaries.md`; `src/cli/cmd_regression.cpp`; `site:scripts/engine-capabilities-v1.json` | Smoke Tests and Canaries; Regression and Proof Testing | observed | kRegressionSpecs is the capability authority the website sweep already consumes; bind the manual to the same list. |
| `ANCHOR-PYTHON-BINDINGS` | Binding surface | `bindings/pydottalk/`; `pycrud/`; `build_pydottalk.ps1` | Python Integration; pydottalk, pydottalk_api, pycrud | observed | Separate proven binding calls from development possibilities; the published page already makes that split. |
| `ANCHOR-EXTERNAL-REFERENCES` | Reference catalog | `docs/manuals/developer/dev/dev-23-external-references.md`; `include/dotref.hpp`; `include/foxref.hpp` | External References; Reference-header policy | drift | The file is dev-23 and its own H1 still reads DEV-19; repair the heading before this anchor leaves drift. |
| `ANCHOR-DATA-MUTATORS` | Mutation surface | `src/cli/cmd_replace.cpp`; `src/cli/cmd_replace_multi.cpp`; `src/cli/cmd_calc.cpp`; `src/cli/cmd_calcwrite.cpp` | Data Mutators; REPLACE, CALC, CALCWRITE, MULTIREP | observed | Carry AIF-117's F1 finding as a caveat: a REPLACE whose right-hand side fails stores blank and reports success. |
<!-- END GENERATED anchors:spine -->

## Website Coverage Anchors (added 2026-09-15)

These are topics the PUBLISHED WEBSITE already covers and the manual does not mention at all.
Every row names the site page that makes the claim. They enter at `deferred` by definition:
the concept is important and published, and systematic harvesting has not closed it.
A site page is evidence that the topic matters to a reader; it is NOT evidence for the claim itself.

<!-- BEGIN GENERATED anchors:website -- derive_anchor_map.py; edit the CSV, not this table -->
| Anchor ID | Layer | Evidence path | Manual target | State | Next closure action |
|---|---|---|---|---|---|
| `ANCHOR-PRIMARY-KEYS` | Key policy | `src/cli/unique_registry.cpp`; `src/cli/cmd_setunique.cpp`; `src/xbase/x64_field_meta.cpp`; `site:content/docs/engine/primary-keys.mdx` | Primary Keys: policy, proof, and boundary | deferred | The site states generate/reserve/refuse with a named spec for each; the manual has no primary-key section at all. |
| `ANCHOR-ERROR-IDENTITY` | Error contract | `src/cli/xbase_error_codes.cpp`; `src/cli/cmd_error_status.cpp`; `src/cli/help_errors.hpp`; `site:content/docs/engine/error-codes.mdx` | Error Codes; Severity, facility, and code | deferred | HRESULT-style error identity is published and unmentioned in the manual; harvest the code table from source. |
| `ANCHOR-IDENTITY-RBAC` | Security | `src/identity/identity_dbf_store.cpp`; `src/identity/identity_admin.cpp`; `src/identity/identity_bootstrap.cpp`; `site:content/docs/engine/identity-security.mdx` | Identity, Authentication, and RBAC | deferred | USER store, sessions, roles, and owner-gated administration are published; no manual chapter exists. |
| `ANCHOR-MESSAGING-LOCALE` | Messaging | `src/cli/message_catalog.cpp`; `src/help/locale_spine_catalog.cpp`; `src/cli/cmd_msgmgr.cpp`; `site:content/docs/engine/messaging-and-localization.mdx` | Messaging and Localization | deferred | The locale spine was promoted and announced; the manual spine never gained a chapter for it. |
| `ANCHOR-INMEMORY-VDISK` | Storage substrate | `src/cli/cmd_vdisk.cpp`; `src/cli/vdisk_config.cpp`; `include/cli/vdisk_config.hpp`; `site:content/docs/engine/in-memory-databases.mdx`; `site:content/docs/engine/ram-dbf-vdisk.mdx` | In-Memory Databases; RAM DBF and VDISK | deferred | Two published pages, no manual section; bind lifetime and visibility rules to the VDISK source before promotion. |
| `ANCHOR-ENGINE-API` | API boundary | `include/xbase.hpp`; `include/xbase_64.hpp`; `include/xbase_vfp.hpp`; `site:content/docs/engine/api-reference.mdx` | Open Engine API Reference | deferred | The site publishes public API boundaries; decide whether this is its own chapter or an appendix to the trinity anchor. |
| `ANCHOR-BENCHMARKS` | Performance | `src/cli/cmd_regression.cpp`; `src/cli/db_tuple_stream.hpp`; `site:content/docs/engine/pinocchio-benchmarks.mdx` | Pinocchio Engine Benchmarks | deferred | The published page already states its evidence limits and machine-identity rules; do not promote numbers without a rerun. |
| `ANCHOR-ECOSYSTEM-POSITION` | Positioning | `site:content/docs/engine/xbase-ecosystem-context.mdx`; `site:content/docs/engine/ecosystem-feature-comparison.mdx`; `README.md` | xBase Ecosystem Context; Feature comparison | deferred | Comparison claims about other products age fastest of anything published; date them or keep them off the manual. |
| `ANCHOR-ACID-BOUNDARY` | Durability | `include/xbase/durable.hpp`; `src/cli/cmd_commit.cpp`; `src/cli/cmd_rollback.cpp`; `site:content/docs/engine/acid-and-glass-box.mdx` | ACID and the Glass-Box Engine | deferred | Consumer of ANCHOR-COMMIT-ROLLBACK; durable.hpp names the compaction gap itself, which belongs in the caveat. |
| `ANCHOR-DBF-PATH-POLICY` | Path policy | `DOTTALKPP_DBF_PATH_POLICY.md`; `src/cli/cmd_setpath.cpp`; `config/` | Path policy and the sys layout | deferred | Owner-flagged 2026-09-14: the website describes paths but never references the current sys layout. No page owns this yet. |
| `ANCHOR-NAMING-CONVENTIONS` | House convention | `include/conventions.hpp`; `docs/manuals/developer/dev/dev-17-contributor-rules.md`; `site:content/docs/dev/naming-conventions.mdx` | Naming Conventions | deferred | Published as a site page with no manual counterpart; fold into the contributor chapter or give it its own. |
| `ANCHOR-COINED-VOCABULARY` | Glossary | `labtalk/ai_portal/AI_GLOSSARY_V1.md`; `site:content/docs/dev/coined-vocabulary.mdx`; `site:content/docs/dev/coined-vocabulary-index.mdx` | Coined Vocabulary; Global glossary | observed | The developer README already names this the global glossary for all manuals; it has never had an anchor. |
| `ANCHOR-AI-PORTAL` | Agent interface | `AI_PORTAL.md`; `AI_README.md`; `docs/ai-friendly/`; `site:content/portal/schemas.mdx` | AI Portal; Registered schemas and identity crosswalk | deferred | Nineteen registered schemas are published; decide whether the portal belongs in the developer manual or stays external. |
| `ANCHOR-FRONTAL-MEMORY` | Research lane | `site:content/memory/overview.mdx`; `site:content/memory/roadmap.mdx`; `site:content/memory/team-model.mdx` | Frontal Memory | deferred | Three published pages with no source lane and no manual section; confirm this is a thesis surface before anchoring deeper. |
<!-- END GENERATED anchors:website -->

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
