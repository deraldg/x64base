# DDICT functionality and repository crosswalk

Follow-up: the owner clarified xbase.com was a typo for x64base.com and
authorized the recommended curation order. See the
[catalog authority assessment](DDICT_CATALOG_AUTHORITY_2026-10-09.md) and
[bounded consolidation plan](DDICT_CONSOLIDATION_PLAN_2026-10-09.md) for the
subsequent measurements and implemented navigation. The original review below
retains its initial evidence boundary.

Date: 2026-10-09 (America/Los_Angeles)
Status: review-needed; read-only source and artifact assessment
Baseline: development, HEAD 0eb1ee5df (2026-10-08)
Authorization: maintainer requested access, AI Portal onboarding, a high-level DDICT crosswalk, and examination of src/cli/cmd_ddict.cpp.

DDICT is a live command implementation inside DotTalk++, backed by shared C++ readers and a much larger historical redocumentation pipeline. The immediate preparation need is to reconcile catalog authority and discovery paths before reorganizing files or extending behavior.

Access to D:/code/ccode and D:/dev was requested through the approval tool and the directory read succeeded. Repository investigation stayed under D:/code/ccode; D:/dev content was not searched. The user-supplied attachment was read separately. The AI Portal seed, laws, front door, authority and lifecycle seeds, current target, search map, project registry, AI-Friendly directory, and latest closeout by filesystem modification time were consulted. CURRENT_TARGET.md still records the July 31 ruling that there is no single controlling lane; its timestamp precedes HEAD and is not evidence of current lane progress.

## Functionality crosswalk

| Surface | Current location | Role and evidence |
| --- | --- | --- |
| CLI | src/cli/cmd_ddict.cpp:800 | Routes bare DDICT to STATUS; supports HELP/?/USAGE, STATUS, TABLES, FIELDS, TAGS, REL, EVIDENCE, OBJECTS. No mutation command is dispatched. |
| Registration and build | src/cli/shell_commands.cpp:636; src/CMakeLists.txt:126,310,581 | DDICT is registered inside the shell. The executable is dottalkpp, not ddict.exe. Build object files are products of compiling these sources. |
| Shared implementation | src/datadict/; include/datadict/ | Catalog location, raw DBF reading, object resolution, string helpers, and alias bridging. Four public helper headers are under include; resolver and bridge headers are beside their implementation under src. |
| GUI consumer | src/gui/wx/main_frame.cpp:1474; src/gui/core/CMakeLists.txt:40 | The Workbench reads DDOBJECT, DDATTR, DDEDGE, DDEVID, and DDSOURCE through the same helper layer. Source changes here can affect both CLI and GUI. |
| Active data locations | dottalkpp/data/datadict/; dottalkpp/data/indexes/datadict/; dottalkpp/data/lmdb/datadict/ | Catalog DBFs and index artifacts are separate storage surfaces. dottalkpp/data/workspaces/ddbase.dtschema also exists. Presence is not index validity or runtime proof. |
| Runtime help | src/help/helpdata_messages.cpp:6945 | Maintained usage text includes OBJECTS with TYPE and PROFILE filters. Historical help validation also exists outside docs/datadict. |
| Design and history | docs/datadict/specs/README.md:3; docs/datadict/contracts/ | The specs README explicitly calls the DD-series a closed historical generation. Its NEXT_ACTIONS files are not current work orders. Contracts preserve the staged evolution of the implementation. |
| Pipeline tooling | tools/datadict/ | Extractors, orchestration, reconciliation, validation, review, disposition, baseline comparison, and catalog work. The catalog subdirectory has 145 direct files at inspection, including historical patch/apply tools; those need classification before reuse. |
| Reports and baseline | docs/datadict/reports/; docs/datadict/baselines/current_baseline.json | Reports record runs and generated candidates. The current baseline pointer names DDBASE-stable-v2; it is a pointer, not a fresh successful comparison. |
| Runtime script templates | dottalkpp/scripts/datadict/README.md | Explicitly distinguishes proof/capture/staging templates from executed proof. dottalkpp/data/scripts/ddict_help.dts is another runtime-facing location. |
| Later maintenance evidence | docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md | June help-family validation postdates the May DD098 closeout. It must be considered before treating the old candidate-only help state as current. |
| Focused regression | src/tests/test_ddict_catalog_dir.cpp; src/tests/CMakeLists.txt:705 | Source tests canonical directory selection from several working directories, staging layout, and missing-catalog fallback. Not executed in this review. |
| LabTalk discovery | labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md; labtalk/registries/projects.yaml | Targeted DDICT/datadict/data-dictionary searches found no direct routing entry in these two files. This is a bounded discoverability finding, not a claim that all LabTalk references are absent. |

## Command behavior and limits

- STATUS counts the eleven legacy catalog DBFs, sidecars, and bytes. Its present state checks file presence, not schema validity, referential integrity, freshness, or long-name catalog agreement (cmd_ddict.cpp:214; ddict_catalog_paths.cpp:187).
- TABLES lists those eleven legacy files (cmd_ddict.cpp:237).
- FIELDS reads CATALOG_FIELD objects and attribute counts from the dictionary; it does not independently inspect an arbitrary table's physical field descriptors (cmd_ddict.cpp:268).
- TAGS combines catalog rows with filesystem artifact discovery; it does not prove an index is usable (cmd_ddict.cpp:347).
- REL resolves an object and shows incoming/outgoing edges, bounded to 40 per direction (cmd_ddict.cpp:463).
- EVIDENCE joins evidence, sources, artifacts, and attributes, with 20-row display bounds (cmd_ddict.cpp:568).
- OBJECTS filters by TYPE and PROFILE and displays up to 80 rows (cmd_ddict.cpp:710).

## Findings to resolve before data dictionary changes

1. **Catalog aliasing does not select the long-name storage family.** FIELDS, TAGS, REL, EVIDENCE, OBJECTS, and the GUI explicitly request legacy DD* files. read_dbf_table constructs that filename directly (src/datadict/ddict_dbf_reader.cpp:134). The six bindings in ddict_catalog_resolver.cpp change tokens; the FIELDS/TAGS bridge expands owner-name matches. The source header's description of authoritative long names is therefore stronger than the file-read behavior.

   Live artifact header measurements confirm the families are not interchangeable copies:

   | Pair | Legacy header records | Long-name header records |
   | --- | ---: | ---: |
   | DDOBJECT / DATA_DICTIONARY_OBJECTS | 100 | 10 |
   | DDATTR / DATA_DICTIONARY_OBJECT_ATTRIBUTES | 423 | 127 |
   | DDEDGE / DATA_DICTIONARY_RELATION_EDGES | 89 | 16 |
   | DDEVID / DATA_DICTIONARY_EVIDENCE_RECORDS | 1 | 7 |

   These are declared DBF header record counts, not validated live-row counts. They demonstrate different artifacts, not which family should win.

2. **TAGS can overstate physical tag evidence.** cmd_ddict.cpp:401 treats DBF existence alone as has_physical_artifact. That branch emits PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS (src/help/helpdata_messages.cpp:7163), including the case where neither CDX nor LMDB was found. This is a source-evidenced reporting defect; the branch was not executed here.

3. **Read failures can look like an empty catalog.** ddict_dbf_reader.cpp:102,134 returns an empty vector for open/short-header/parse failures, and can stop early on truncated records without returning a diagnostic. Callers can then report no objects, fields, or tags. The same reader turns every field into trimmed raw bytes; it does not dereference memo storage. EVIDENCE's ATTRMEMO fallback at cmd_ddict.cpp:695 therefore does not establish readable memo content.

4. **Directory selection tests existence, not catalog completeness.** ddict_catalog_paths.cpp:123 chooses the first existing candidate. The September change fixed the known repository-root versus launcher-root ordering problem, but an empty earlier candidate can still shadow a populated later one. The focused test covers path choice, not content validity.

5. **Entry documentation has drifted.** docs/datadict/README.md:35 still directs future catalogs to data/metadata/datadict. Current source and actual artifacts use data/datadict. The source usage annotation at cmd_ddict.cpp:24 also omits OBJECTS, although both the dispatcher and runtime help include it. DD098's May help status must remain dated historical evidence, with the later June validation linked from a current landing page.

## Duplicate-directory assessment

The root and dottalkpp share directory names: .relations, cases, cmake, docs, results, scripts, tools, and user. Matching names alone do not prove duplicate contents. Root tools/datadict contains engineering tooling; dottalkpp/scripts/datadict contains runtime templates. Those are distinct roles worth making explicit.

An actual duplicate is confirmed: all eleven direct DD*.dbf files under dottalkpp/data/datadict have identically named files under its nested datadict directory, and every pair matched by SHA-256 during this review. The comparison excludes memos, indexes, backups, and long-name tables. Their duplication is a maintenance risk, but does not authorize removal: the resolver still retains the nested location as a fallback candidate.

The user's pasted listing also includes build objects, archival source backups, original packages, draft patches, generated source candidates, and temporary copies. These are different lifecycle roles. Neither a repeated basename nor an older timestamp is sufficient grounds to delete one. Compiled .obj/.o entries are not alternate maintained source implementations.

## Proposed curation order

1. Establish a current DDICT landing page and routing entry: CLI -> shared helpers -> consumers -> catalog families -> refresh pipeline -> latest applicable proof. Reuse existing directories.
2. Record an explicit decision about the legacy and long-name catalog families, including schemas, consumer mappings, migration completeness, and rollback. Do not infer authority from naming alone.
3. Classify a bounded manifest of files as active source, maintained tool, runtime template, generated output, historical proof, original package, backup, or temporary artifact. Include owner, producer, consumers, replacement, and retention decision.
4. Address misleading TAGS output, distinguish failed reads from empty results, and align help annotations. Add focused behavioral proof when those changes are authorized.
5. Only then plan exact duplicate moves/removals, preserving references and regeneration/rollback evidence. Keep history immutable and repair current entry points instead of rewriting old closeouts.

Suggested discovery-map route captured by this report: DDICT / Data Dictionary -> src/cli/cmd_ddict.cpp; src/datadict; include/datadict; docs/datadict/README.md; docs/datadict/specs/README.md; tools/datadict/README.md; docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md.

## Website and verification boundary

The requested https://xbase.com could not be retrieved by the web tool. The repository identifies https://x64base.com as its companion site, and that homepage was accessible and identified the x64base/DotTalk++/LabTalk project. No website files were searched or changed, and no claim is made about current website DDICT coverage.

This is maintenance / C0 / documentation-only review under the owning DotTalk++ maintenance lifecycle. No build or DDICT runtime session was run. Historical green reports are historical evidence, not fresh runtime validation. Measurements were direct directory listings, bounded file searches, source reads, DBF header reads, and eleven SHA-256 comparisons. No recursive repository-wide content scan was used.

Only this report was authored. Existing source, catalogs, HELP data, workspace data, registries, board entries, and other concurrent dirty work were left untouched. These include src-independent changes in tools/dbf/schema_registry.py, labtalk/portal/labtalk_portal.py, labtalk/ai_portal/validate_portal_identifiers.py, labtalk/registries/ai_runs.yaml, the AI-Friendly dashboard and board, HELP DBFs, STUDENTS data/index files, WORKSPACES data/memos, and other maintenance documents. Their individual authors were not established; none is attributed to this review.

No staging, commit, push, promotion, catalog refresh, cleanup, or publication was performed. The report was moved from the ignored docs/datadict/reports output directory to docs/maintenance/reviews so ordinary Git status can discover it. The full status check warned that .pytest_cache was unreadable; no claim of exhaustive cleanliness is made. This report remains a local, uncommitted handoff; the next gate is maintainer review of catalog authority and the bounded curation scope.
