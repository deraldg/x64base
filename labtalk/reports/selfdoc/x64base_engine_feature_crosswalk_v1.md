# x64base Engine Feature Crosswalk v1

Generated: 2026-07-04T03:32:01Z

Status language:

- `runtime-evidenced`: implemented/supported HELP command plus source evidence.
- `source-evidenced`: source evidence exists, but no matching supported HELP command was found by this scanner.
- `help-catalog-evidenced`: HELP catalog evidence exists, but source mapping needs review.
- `planned-or-in-progress`: found as a planning lane or broad diagnostic lane; do not market as complete.
- `review-needed`: no strong evidence found by this pass.

Manualgen note: this report is generated outside the protected manual publication. Promote only after review.

## Summary

- Features scanned: 28
- Source files inspected through feature globs: 4520
- HELP commands loaded: 290
- Manualgen validation status: FAIL
- Manualgen validation caveat: Python 3.12 required; prior manualgen validation used Python 3.11.

## Feature Hierarchy

### Concurrency

#### Record locking and unlock lifecycle

- Status: `runtime-evidenced`
- Commands: LOCK (implemented=T, supported=T); UNLOCK (implemented=T, supported=T)
- Evidence: include/lock_cleanup.hpp [lock]; include/xbase_locks.hpp [lock, unlock, record lock]; src/cli/cmd_lock.cpp [lock, unlock, record lock, xbase_locks]; src/cli/cmd_unlock.cpp [lock, unlock, record lock, xbase_locks]; src/xbase/lock_cleanup.cpp [lock, lock_cleanup]; src/xbase/xbase_locks.cpp [lock, unlock, xbase_locks]

### Documentation

#### SelfDoc, HELP metadata, contracts, MAINT, Blackbox, and manualgen pipeline

- Status: `runtime-evidenced`
- Commands: CMDHELP (implemented=T, supported=T); CMDHELPCHK (implemented=T, supported=T); COMMANDSHELP (implemented=T, supported=T); DOTHELP (implemented=T, supported=T); DRAWIO (implemented=T, supported=T); FOXHELP (implemented=T, supported=T); HELP (implemented=T, supported=T); PREDHELP (implemented=T, supported=T); SQLHELP (implemented=T, supported=T)
- Evidence: docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md [contract, metacollect, @dottalk.contract]; docs/contracts/CONTRACT_LANE_MANIFEST_V1.md [SelfDoc, manualgen, CMDHELPCHK, HELP]; docs/contracts/CONTRACT_LANE_WORKFLOW_V1.md [SelfDoc, manualgen, CMDHELPCHK, HELP]; docs/contracts/CONTRACT_LIFECYCLE_V1.md [SelfDoc, manualgen, HELP, contract]; docs/contracts/CONTRACT_MANAGER_MODE_V1.md [SelfDoc, manualgen, CMDHELPCHK, HELP]; docs/contracts/CONTRACT_REGISTRY_V1.md [SelfDoc, manualgen, CMDHELPCHK, HELP]; docs/contracts/CONTRACT_TEMPLATE_V1.md [HELP, contract]; docs/contracts/README.md [SelfDoc, manualgen, CMDHELPCHK, HELP]
- Note: Source contracts, comments evidence, HELP DATA, CMDHELPCHK, MAINT, manualgen, and website promotion are curated as a procedural lane with report-only defaults and explicit mutation gates.

### Editing

#### Buffered editing, dirty state, commit and rollback

- Status: `runtime-evidenced`
- Commands: CALCWRITE (implemented=T, supported=T); COMMIT (implemented=T, supported=T); EDIT (implemented=T, supported=T); REPLACE (implemented=T, supported=T); ROLLBACK (implemented=T, supported=T)
- Evidence: src/cli/cmd_commit.cpp [buffer, dirty, commit, rollback]; src/cli/cmd_rollback.cpp [buffer, dirty, commit, rollback]; src/cli/shell_buffer_utils.cpp [buffer]; src/cli/table_buffer.cpp [buffer, dirty, table_buffer]; src/tv/cmd_browsetui.cpp [commit, PendingEdits]

### Education

#### Education, retro, ASCII, blackbox, and student extension commands

- Status: `runtime-evidenced`
- Commands: ASCII (implemented=T, supported=T); BOOLEAN (implemented=T, supported=T); CASE (implemented=T, supported=T); CHRISTMAS (implemented=T, supported=T); COBOL (implemented=T, supported=T); CODASYL (implemented=T, supported=T); IDX (implemented=T, supported=T); NORMALIZE (implemented=T, supported=T); RETRO (implemented=T, supported=T); SECHO (implemented=T, supported=T); SET CASE (implemented=F, supported=T); SETCASE (implemented=T, supported=T); SHELLO (implemented=T, supported=T); SIX (implemented=T, supported=T); STUDENTECHO (implemented=T, supported=T); STUDENTHELLO (implemented=T, supported=T)
- Evidence: docs/teaching/TEACHING_POINT_LEDGER.md [student extension]; src/cli/cmd_bbox.cpp [education, Blackbox]; src/cli/cmd_retro.cpp [ASCII, retro]; src/edu/edu_ascii_table.cpp [education, ASCII]; src/edu/edu_bibletalk.cpp [education]; src/edu/edu_boolean.cpp [education]; src/edu/edu_boyce_codd.cpp [education]; src/edu/edu_case.cpp [education]
- Note: LabTalk should treat these as runnable education features and proof/curriculum inputs, not only as novelty commands.

### Gui

#### Open GUI API, TUI, wxWidgets, and browser lanes

- Status: `runtime-evidenced`
- Commands: BROWSER (implemented=T, supported=T); BROWSETUI (implemented=T, supported=T); BROWSETV (implemented=T, supported=T); FOXTALK (implemented=T, supported=T); SIMPLEBROWSE (implemented=T, supported=T); SIMPLEBROWSER (implemented=F, supported=T); SMARTBROWSE (implemented=T, supported=T); SMARTBROWSER (implemented=F, supported=T)
- Evidence: docs/gui/ARCTICTALK_BRANDING_AND_LINEAGE_V1.md [GUI, TUI, browse, foxtalk]; docs/gui/GUI_BUILD_AND_RUN_V1.md [GUI, wx, Tk, browse]; docs/gui/GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md [GUI, wx, Tk, TUI]; docs/gui/GUI_RUNTIME_FACADE_PLAN_V1.md [GUI, wx, Tk, browse]; docs/gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md [GUI, wx, Tk, TUI]; docs/gui/GUI_THREADING_EVENT_MODEL_V1.md [GUI, wx, Tk, TUI]; docs/gui/GUI_TUI_STATUS_AND_BRANCH_STRATEGY_V1.md [GUI, wx, Tk, TUI]; docs/gui/OPEN_ARCH_GUI_PLAN_V1.md [GUI, wx, Tk, TUI]

### Index

#### Open index API and index backends

- Status: `runtime-evidenced`
- Commands: BUILDLMDB (implemented=T, supported=T); CDX (implemented=T, supported=T); CNX (implemented=T, supported=T); IDX (implemented=T, supported=T); INDEX (implemented=T, supported=T); INDEXSEEK (implemented=T, supported=T); LIST_LMDB (implemented=T, supported=T); LMDB (implemented=T, supported=T); LMDBDUMP (implemented=T, supported=T); LMDB_UTIL (implemented=T, supported=T); REINDEX (implemented=T, supported=T); SEEK (implemented=T, supported=T); SET INDEX (implemented=F, supported=T); SET ORDER (implemented=F, supported=T); SETCDX (implemented=T, supported=T); SETCNX (implemented=T, supported=T)
- Evidence: include/xindex/attach.hpp [IndexManager]; include/xindex/bpt_backend.hpp [seek]; include/xindex/bptree.hpp [seek, order]; include/xindex/bptree_backend.hpp [seek]; include/xindex/cdx_backend.hpp [IndexManager, LMDB, CDX, seek]; include/xindex/common.hpp [INX, order]; include/xindex/index_backend.hpp [seek]; include/xindex/index_format_detect.hpp [CDX, CNX, INX]
- Note: SET ORDER defaults v32/classic-like tables to .cnx and v64/VFP/x64 tables to .cdx; SET INDEX accepts .inx/.cnx for v32 and .cdx for v64.

### Integration

#### External app, shell, image, web, URL, SFTP, and archive boundaries

- Status: `runtime-evidenced`
- Commands: BANG (implemented=T, supported=T); EDIT (implemented=T, supported=T); IMAGE (implemented=T, supported=T); PSHELL (implemented=T, supported=T); SFTP (implemented=T, supported=T); TEXT (implemented=T, supported=T); WEB (implemented=T, supported=T); ZIP (implemented=T, supported=T)
- Evidence: src/cli/cmd_bang.cpp [launches_external, SFTP, PSHELL]; src/cli/cmd_image_display.cpp [ShellExecute, launches_external]; src/cli/cmd_sftp.cpp [launches_external, SFTP, PSHELL]; src/cli/cmd_web.cpp [ShellExecute, WinHTTP, launches_external, default URL handler]; src/cli/cmd_zip.cpp [ZIP]; src/edu/edu_edit.cpp [launches_external]
- Note: These commands must document external process, network, viewer/browser launch, and filesystem-write risk separately from database mutation.

#### SQL bridge, CSV import/export, DBF copy, and tuple export

- Status: `runtime-evidenced`
- Commands: AUTODBF (implemented=T, supported=T); COPY (implemented=T, supported=T); EXPORT (implemented=T, supported=T); EXPORTSQL (implemented=T, supported=T); IMPORT (implemented=T, supported=T); IMPORTSQL (implemented=T, supported=T); SQL (implemented=T, supported=T); SQLERASE (implemented=T, supported=T); SQLHELP (implemented=T, supported=T); SQLITE (implemented=T, supported=T); SQLSEL (implemented=T, supported=T); SQLVER (implemented=T, supported=T); TUPEXPORT (implemented=T, supported=T)
- Evidence: src/cli/cmd_autodbf.cpp [SQL, import, CSV]; src/cli/cmd_export.cpp [export, CSV, copy]; src/cli/cmd_export_functions.cpp [export]; src/cli/cmd_import.cpp [import, export, CSV]; src/cli/cmd_importsql.cpp [SQL, import, export, CSV]; src/cli/cmd_sql.cpp [SQL]; src/cli/cmd_sql_erase.cpp [SQL]; src/cli/cmd_sql_help.cpp [SQL, sqlite, import]
- Note: IMPORT reads CSV into an open DBF by matching headers to field names; EXPORT writes the current or named open area to CSV by default.

#### Remote and system integration surfaces

- Status: `runtime-evidenced`
- Commands: PSHELL (implemented=T, supported=T); SFTP (implemented=T, supported=T); WEB (implemented=T, supported=T); ZIP (implemented=T, supported=T)
- Evidence: src/cli/cmd_sftp.cpp [SFTP, SSH, web, system]; src/cli/cmd_web.cpp [SFTP, web, system]; src/cli/cmd_zip.cpp [zip, system]; src/cli/zip_backend_posix.cpp [zip, system]; src/cli/zip_backend_win.cpp [zip, PowerShell, system]

### Language

#### SET family: session, output, paths, indexes, filters, relations, locale, and buffering

- Status: `runtime-evidenced`
- Commands: BROWSETUI (implemented=T, supported=T); BROWSETV (implemented=T, supported=T); SET (implemented=T, supported=T); SET CASE (implemented=F, supported=T); SET FILTER (implemented=F, supported=T); SET INDEX (implemented=F, supported=T); SET ORDER (implemented=F, supported=T); SET PATH (implemented=F, supported=T); SET RELATION (implemented=T, supported=T); SET UNIQUE (implemented=T, supported=T); SET VAR (implemented=F, supported=T); SET VAR! (implemented=F, supported=T); SETCASE (implemented=T, supported=T); SETCDX (implemented=T, supported=T); SETCNX (implemented=T, supported=T); SETFILTER (implemented=T, supported=T)
- Evidence: include/cli/settings.hpp [SET CONSOLE, SET PRINT, SET DEVICE, SET FILTER]; src/cli/cmd_set.cpp [SET TABLE BUFFER, SET CONSOLE, SET PRINT, SET DEVICE]; src/cli/cmd_set_relation.cpp [SET RELATION]; src/cli/cmd_setcdx.cpp [SET PATH, SET ORDER, SET INDEX]; src/cli/cmd_setcnx.cpp [SET PATH, SET ORDER, SET INDEX]; src/cli/cmd_setfilter.cpp [SET FILTER]; src/cli/cmd_setindex.cpp [SET ORDER, SET INDEX]; src/cli/cmd_setlmdb.cpp [SET ORDER, SET INDEX]
- Note: The SET dispatcher mutates session settings and delegates specialized state to path, index/order, filter, relation, locale, and output-routing handlers.

#### DotScript command files, variables, control flow, and one-level nesting

- Status: `runtime-evidenced`
- Commands: DOTSCRIPT (implemented=T, supported=T); ELSE (implemented=T, supported=T); ENDIF (implemented=T, supported=T); ENDLOOP (implemented=T, supported=T); ENDSCAN (implemented=T, supported=T); ENDUNTIL (implemented=T, supported=T); ENDWHILE (implemented=T, supported=T); IF (implemented=T, supported=T); LOOP (implemented=T, supported=T); LOOPS (implemented=F, supported=T); LOOP_BUFFER (implemented=T, supported=T); SCAN (implemented=T, supported=T); SCAN_BUFFER (implemented=T, supported=T); SET VAR (implemented=F, supported=T); SET VAR! (implemented=F, supported=T); UNTIL (implemented=T, supported=T)
- Evidence: src/cli/cmd_dotscript.cpp [DotScript, one-level subscript, nesting limit]; src/cli/cmd_if.cpp [SCAN]; src/cli/cmd_loop.cpp [LOOP, ENDLOOP]; src/cli/cmd_scan.cpp [LOOP, SCAN, ENDSCAN]; src/cli/cmd_until.cpp [LOOP, ENDLOOP, SCAN]; src/cli/cmd_var.cpp [DotScript]; src/cli/cmd_while.cpp [LOOP, ENDLOOP, SCAN]; src/cli/dotscript_var_name.cpp [DotScript, SCAN, ENDSCAN]
- Note: Current DOTSCRIPT nesting is limited to a main script plus one subscript.

### Localization

#### Location, locale, and language support

- Status: `runtime-evidenced`
- Commands: BROWSETUI (implemented=T, supported=T); BROWSETV (implemented=T, supported=T); SET (implemented=T, supported=T); SET CASE (implemented=F, supported=T); SET FILTER (implemented=F, supported=T); SET INDEX (implemented=F, supported=T); SET ORDER (implemented=F, supported=T); SET PATH (implemented=F, supported=T); SET RELATION (implemented=T, supported=T); SET UNIQUE (implemented=T, supported=T); SET VAR (implemented=F, supported=T); SET VAR! (implemented=F, supported=T); SETCASE (implemented=T, supported=T); SETCDX (implemented=T, supported=T); SETCNX (implemented=T, supported=T); SETFILTER (implemented=T, supported=T)
- Evidence: docs/locale/candidates/PHASE23H-HELP-LOCALE-CONSUMER-INTEGRATION-PLAN/PHASE23H_HELP_LOCALE_CONSUMER_INTEGRATION_PLAN.md [locale, language]; docs/locale/candidates/PHASE23I-HELP-LOCALE-COMPANION-SCHEMA-STAGING/PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING.md [locale]; docs/locale/candidates/PHASE23J-HELP-LOCALE-SAMPLE-ROW-MATERIALIZATION-PLAN/PHASE23J_HELP_LOCALE_SAMPLE_ROW_MATERIALIZATION_PLAN.md [locale, language]; docs/locale/candidates/PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF/PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_STAGING.md [locale]; docs/locale/candidates/PHASE23M-HELP-LOCALE-ACTIVE-PROMOTION-PLAN/reports/PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN.md [locale]; docs/locale/candidates/PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING/reports/PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_EXECUTION_STAGING.md [locale]; docs/locale/candidates/PHASE23P-CMDHELP-ACTIVE-LOCALE-CONSUMER-PROTOTYPE/reports/PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE.md [locale, active locale]; docs/locale/candidates/PHASE23Q-CMDHELP-LOCALE-INTEGRATION-PLAN/reports/PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN.md [locale, language]

### Memo

#### Object-oriented memo storage and display

- Status: `runtime-evidenced`
- Commands: BROWSETUI (implemented=T, supported=T); DISPLAY (implemented=T, supported=T); MEMO (implemented=T, supported=T)
- Evidence: include/memo/dtx_format.hpp [memo]; include/memo/memo64.hpp [memo, MemoRef]; include/memo/memo_auto.hpp [memo]; include/memo/memo_backend.hpp [memo, MemoRef]; include/memo/memo_context.hpp [memo]; include/memo/memo_display.hpp [memo, MemoRef]; include/memo/memo_manager.hpp [memo, MemoManager, MemoObject, MemoRef]; include/memo/memo_object.hpp [memo, MemoObject, MemoRef]

### Metadata

#### Data Dictionary catalog inspection and DDICT bridge

- Status: `source-evidenced`
- Evidence: docs/datadict/backups/DD096ZB-backup-and-inactive-candidate-staging-v0/dottalkpp/data/datadict/datadict_canonical_rebuild_v0/DD056_INDEX_USE_PROOF_TEMPLATE.md [DDOBJECT, DDEDGE]; docs/datadict/backups/DD096ZB-backup-and-inactive-candidate-staging-v0/dottalkpp/data/datadict/datadict_canonical_rebuild_v0/DD056R_CANONICAL_CDX_BUILDLMDB_PROOF_TEMPLATE.md [DDOBJECT, DDEDGE]; docs/datadict/packages/DD-005_dd005_physical_dictionary_source_map_v0/DD005_PHYSICAL_DICTIONARY_SOURCE_MAP_v0.md [DDICT]; docs/datadict/packages/DD-006_dd006_physical_dictionary_manifest_schema_v0/DD006_AUTOLOG_v0.md [read-only]; docs/datadict/packages/DD-006_dd006_physical_dictionary_manifest_schema_v0/DD006_NEXT_ACTIONS_v0.md [read-only]; docs/datadict/packages/DD-006_dd006_physical_dictionary_manifest_schema_v0/DD006_PHYSICAL_DICTIONARY_MANIFEST_SCHEMA_v0.md [DDICT]; docs/datadict/packages/DD-007_dd007_physical_dictionary_extractor_skeleton_v0/DD007_AUTOLOG_v0.md [read-only]; docs/datadict/packages/DD-007_dd007_physical_dictionary_extractor_skeleton_v0/DD007_NEXT_ACTIONS_v0.md [read-only]
- Note: DDICT is currently documented as read-only inspection: no DBF append/replace/delete, no CDX/LMDB rebuild, and no HELP/CMDHELPCHK/manual/catalog mutation.

### Navigation

#### Cursor control and record navigation

- Status: `runtime-evidenced`
- Commands: BOTTOM (implemented=T, supported=T); DISPLAY (implemented=T, supported=T); DUMP (implemented=T, supported=T); FIRST (implemented=T, supported=T); GO (implemented=T, supported=T); GOTO (implemented=T, supported=T); LAST (implemented=T, supported=T); LMDBDUMP (implemented=T, supported=T); NEXT (implemented=T, supported=T); PRIOR (implemented=T, supported=T); RECNO (implemented=T, supported=T); SKIP (implemented=T, supported=T); TOP (implemented=T, supported=T)
- Evidence: src/cli/cmd_goto.cpp [recno, skip, top, bottom]; src/cli/cmd_recno.cpp [recno, gotoRec, skip, cursor]; src/cli/cmd_skip.cpp [recno, gotoRec, skip, top]; src/cli/cursor_status.cpp [recno, cursor]; src/xbase/cursor_hook.cpp [cursor]

### Observability

#### Messaging, error/status, and output routing

- Status: `runtime-evidenced`
- Commands: ECHO (implemented=T, supported=T); ERROR CLEAR (implemented=T, supported=T); ERROR STATUS (implemented=T, supported=T); ERROR TEST (implemented=T, supported=T); SECHO (implemented=T, supported=T); STUDENTECHO (implemented=T, supported=T)
- Evidence: docs/messaging/ACTIVE_MESSAGE_CATALOG_SEED_GAP_2026-06-25.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10cj_native_writer_decision_selection_package_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10cj_option_b_branch_reconciliation_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10ck_b_option_b_wrapper_contract_proof_plan_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CK_B_OPTION_B_WRAPPER_CONTRACT_PROOF_PLAN.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10cl_b_option_b_wrapper_contract_proof_staging_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CL_B_OPTION_B_WRAPPER_CONTRACT_PROOF_STAGING.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10cm_b_option_b_wrapper_contract_proof_review_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CM_B_OPTION_B_WRAPPER_CONTRACT_PROOF_REVIEW.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10cn_b_option_b_reuse_proof_decision_package_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE.md [message_catalog]; docs/messaging/apply/phase22ae_6_5_10co_b_targeted_native_writer_invocation_proof_plan_v1/MESSAGE_LOCALE_PHASE22AE_6_5_10CO_B_TARGETED_NATIVE_WRITER_INVOCATION_PROOF_PLAN.md [message_catalog]

#### Command timing and diagnostics

- Status: `runtime-evidenced`
- Commands: BETA (implemented=T, supported=T); CMDHELPCHK (implemented=T, supported=T); ERROR STATUS (implemented=T, supported=T); ERROR_STATUS (implemented=T, supported=T); STATUS (implemented=T, supported=T)
- Evidence: include/cli/edu_idx.hpp [timing, elapsed]; include/cli/settings.hpp [timer]; include/dotref.hpp [profile]; include/dt/data/fixed_profiles.hpp [profile]; include/dt/data/format_profile.hpp [profile]; include/dt/data/row_codec_fixed.hpp [profile]; include/glorius_bridge.hpp [chrono]; include/import/import_profile.hpp [profile]

### Query

#### Filtering, searching, predicates, and WHERE cache

- Status: `runtime-evidenced`
- Commands: FIND (implemented=T, supported=T); INDEXSEEK (implemented=T, supported=T); LOCATE (implemented=T, supported=T); SEEK (implemented=T, supported=T); SET FILTER (implemented=F, supported=T); SMARTLIST (implemented=T, supported=T); WHERE (implemented=T, supported=T); WHERECACHE (implemented=T, supported=T)
- Evidence: src/cli/cmd_locate.cpp [filter, where, predicate, locate]; src/cli/cmd_seek.cpp [find, seek]; src/cli/cmd_setfilter.cpp [filter, locate, find]; src/cli/cmd_where.cpp [filter, where, predicate, find]; src/cli/cmd_wherecache.cpp [filter, where, wherecache]; src/cli/filters/filter_registry.cpp [filter, where, find]

### Relations

#### Relations and relation-aware browsing

- Status: `runtime-evidenced`
- Commands: CMDREL (implemented=T, supported=T); ERSATZ (implemented=T, supported=T); RBROWSE (implemented=T, supported=T); REL (implemented=T, supported=T); REL ENUM (implemented=F, supported=T); RELATION (implemented=F, supported=T); RELATIONS (implemented=T, supported=T); REL_ENUM (implemented=F, supported=T); REL_LIST (implemented=T, supported=T); REL_REFRESH (implemented=T, supported=T); SET RELATION (implemented=T, supported=T)
- Evidence: src/cli/cmd_rel.cpp [relation, Rel, rel_enum]; src/cli/cmd_relations.cpp [relation, Rel, RBROWSE, rel_enum]; src/cli/rel_enum_engine.cpp [relation, Rel, rel_enum]; src/cli/rel_iter.cpp [relation, Rel]; src/cli/rel_refresh_suppress.cpp [relation, Rel]; src/cli/relations_boot.cpp [relation, Rel]; src/cli/relations_status.cpp [relation, Rel, RBROWSE]

### Rules

#### Triggers, rules, and validation hooks

- Status: `runtime-evidenced`
- Commands: RULE (implemented=T, supported=T); TUPVALIDATE (implemented=T, supported=T); VALIDATE (implemented=T, supported=T)
- Evidence: src/cli/cmd_rule.cpp [rule, constraint, validate]; src/cli/cmd_trigger.cpp [trigger]; src/cli/cmd_validate.cpp [rule, validate, validator]; src/cli/cmd_validate_unique.cpp [rule, validate]; src/cli/field_constraints.cpp [rule, constraint, validate]

### Schema

#### DDL schema fetch, validation, DBF creation, seeds, and sidecars

- Status: `runtime-evidenced`
- Commands: AUTODBF (implemented=T, supported=T); CREATE (implemented=T, supported=T); DDL (implemented=T, supported=T); FIELDMGR (implemented=T, supported=T)
- Evidence: src/cli/cmd_autodbf.cpp [schema]; src/cli/cmd_create.cpp [schema]; src/cli/cmd_ddl.cpp [DDL FETCH, DDL VALIDATE, DDL CREATE DBF, EMIT SIDECARS]
- Note: DDL FETCH can perform network/file writes; DDL CREATE DBF writes filesystem DBF output and optional sidecars. SEED CSV is recognized by the contract but not fully implemented in this drop-in.

### Security

#### Security and policy surfaces

- Status: `runtime-evidenced`
- Commands: SECURITY (implemented=T, supported=T)
- Evidence: include/xbase_security.hpp [security]; include/xbase_security_policy.hpp [security, policy]; include/xbase_security_runtime.hpp [security, policy, permission]; include/xbase_security_signatures.hpp [security, policy, signature]; include/xbase_security_tests.hpp [security]; src/cli/cmd_security.cpp [security, policy]; src/cli/xbase_security_runtime.hpp [security, policy, permission]; src/cli/xbase_security_tests.cpp [security, policy]

### Storage Formats

#### DBF flavor trinity: MS-DOS/classic, VFP, and x64 DBF_64

- Status: `runtime-evidenced`
- Commands: AUTODBF (implemented=T, supported=T); CREATE (implemented=T, supported=T); EDUCATIONAL_USE (implemented=F, supported=T); FIELDS (implemented=T, supported=T); SET INDEX (implemented=F, supported=T); SET ORDER (implemented=F, supported=T); STRUCT (implemented=T, supported=T); USE (implemented=T, supported=T); VUSE (implemented=T, supported=T)
- Evidence: include/xbase.hpp [ClassicNoMemo, ClassicWithMemo, Fox26Memo, VfpBase]; include/xbase_64.hpp [DBF_VERSION_64]; include/xbase_vfp.hpp [ClassicNoMemo, ClassicWithMemo, Fox26Memo, VfpBase]; src/cli/cmd_setindex.cpp [AreaKind]; src/cli/cmd_setorder.cpp [AreaKind]
- Note: xbase.hpp is the neutral runtime contract; xbase_vfp.hpp bridges classic/MS-DOS, FoxPro, and VFP descriptors; xbase_64.hpp owns x64 extensions, vector metadata, and fallback naming.

#### Visual FoxPro DBF field/data type compatibility

- Status: `runtime-evidenced`
- Commands: AUTODBF (implemented=T, supported=T); CREATE (implemented=T, supported=T); FIELDS (implemented=T, supported=T); STRUCT (implemented=T, supported=T)
- Evidence: include/cli/field_codecs.hpp [Double]; include/xbase_vfp.hpp [VFP, Visual FoxPro]; src/cli/cli_currency.cpp [Currency]; tests/xbase_vfp_probe.cpp [VFP]

#### x64 DBF extensions and newer data types

- Status: `runtime-evidenced`
- Commands: AUTODBF (implemented=T, supported=T); CREATE (implemented=T, supported=T); STRUCT (implemented=T, supported=T)
- Evidence: include/xbase_64.hpp [DBF64, x64, LargeHeaderExtension, X64Meta]; include/xbase_64_phase1_contract.txt [DBF64, x64, LargeHeaderExtension, X64Meta]; src/cli/dbf64_header_validate.cpp [DBF64, x64, currency, datetime]

#### Vectored table and field names with fallback mangling

- Status: `runtime-evidenced`
- Commands: CREATE (implemented=T, supported=T); FIELDS (implemented=T, supported=T); STRUCT (implemented=T, supported=T)
- Evidence: include/xbase_64.hpp [vector, field name, fallback, string_pool]; include/xbase_64_phase1_contract.txt [vector, fallback, string_pool]

### Workspace

#### Workspaces wrapping active areas

- Status: `runtime-evidenced`
- Commands: AREA (implemented=T, supported=T); AREA51 (implemented=T, supported=T); DBAREA (implemented=T, supported=T); DBAREAS (implemented=T, supported=T); WORKAREA (implemented=F, supported=T); WORKSPACE (implemented=T, supported=T); WSREPORT (implemented=T, supported=T)
- Evidence: include/workspace/relation_state.hpp [workspace]; include/workspace/schema_area_state.hpp [workspace, SchemaAreaState]; include/workspace/schema_workspace.hpp [workspace, SchemaWorkspace, SchemaAreaState]; include/workspace/workarea_manager.hpp [workspace]; include/workspace/workarea_slot.hpp [workspace]; src/cli/cmd_workspace.cpp [workspace, area state]; src/cli/cmd_wsreport.cpp [workspace]; src/workspace/schema_area_state.cpp [workspace, SchemaAreaState]

### Xbase Engine

#### DBF table runtime and DbArea object model

- Status: `runtime-evidenced`
- Commands: AREA (implemented=T, supported=T); AREA51 (implemented=T, supported=T); DBAREA (implemented=T, supported=T); DBAREAS (implemented=T, supported=T); EDUCATIONAL_USE (implemented=F, supported=T); FIELDS (implemented=T, supported=T); STRUCT (implemented=T, supported=T); USE (implemented=T, supported=T); VUSE (implemented=T, supported=T); WORKAREA (implemented=F, supported=T)
- Evidence: include/xbase.hpp [DbArea, dbarea, readCurrent, recCount]; include/xbase_64.hpp [DbArea, dbarea]; include/xbase_cli.hpp [DbArea, dbarea]; include/xbase_field_getters.hpp [DbArea, dbarea]; include/xbase_locks.hpp [DbArea, dbarea]; include/xbase_vfp.hpp [DbArea, dbarea]; src/cli/cmd_dbarea.cpp [DbArea, dbarea, recCount]; src/xbase/cursor_hook.cpp [DbArea, dbarea]
