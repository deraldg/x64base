// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_regression.cpp
// @dottalk.usage v1
// owner: DOT|REGRESSION
// command: REGRESSION
// category: test
// status: supported
// noargs: usage
// effect: execute
// mutates: delegates regression scripts session data filesystem
// usage-access: REGRESSION USAGE
// summary:
//   Launch curated DotTalk++ regression and smoke DotScript files through the
//   normal DOTSCRIPT runner so regression entrypoints stay discoverable and
//   consistent.
//
// usage:
//   REGRESSION USAGE
//   REGRESSION LIST
//   REGRESSION FIND <words...>
//   REGRESSION SHOW <name>
//   REGRESSION RUN <name>
//   REGRESSION <name>
//   REGRESSION ALL
//
// examples:
//   REGRESSION LIST
//   REGRESSION SHOW NONDESTRUCTIVE
//   REGRESSION RUN INDEX_X32
//   REGRESSION RUN X64_METRICS
//   REGRESSION RUN HARVEST
//   REGRESSION CURSOR
//   REGRESSION ALL
//
// notes:
//   REGRESSION is a curated launcher, not a separate test executor.
//   Actual script execution is delegated to DOTSCRIPT.
//   Regression scripts are expected to bootstrap their own environment.
//   LIST shows only curated stable entrypoints, not every historical script on disk.
//   ALL runs the curated default suite in declared order.
//   Dev-only warning/repro canaries should remain outside this surface unless
//   they are intentionally promoted.
//
// risk:
//   reads_files: yes
//   executes_commands: yes
//   mutates_data: depends on selected script contents
//   mutates_session: yes
//   writes_files: depends on selected script contents
//   no_transaction_or_rollback: yes
//
// related:
//   DOTSCRIPT
//   TEST
//   WORKSPACE
//   ERSATZ
//   CMDHELP
//

#include "shell_commands.hpp"

#include <array>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "common/path_state.hpp"
#include "shell_api.hpp"
#include "textio.hpp"

using xbase::DbArea;

namespace {

struct RegressionSpec {
    const char* name;
    const char* script;
    const char* summary;
    bool in_default_suite;
};

// SIZE IS HAND-MAINTAINED. Adding a row without bumping this count is a hard
// compile error ("too many initializers"), which is the safe failure -- but it
// is a recurring papercut: it happened when CNXLIVE was added on 2026-07-31.
// Bump it when you add a regression.
constexpr std::array<RegressionSpec, 48> kRegressionSpecs{{
    {
        "NONDESTRUCTIVE",
        "dottalkpp_non_destructive_smoke.dts",
        "Broad non-destructive shell smoke over stable command surface",
        true
    },
    {
        "INDEX_X32",
        "index_x32_inx_cnx_smoke.dts",
        "x32 INX/CNX order and attachment smoke",
        true
    },
    {
        "INDEX_X64",
        "index_v64_cdx_lmdb_smoke.dts",
        "v64 CDX/LMDB order and attachment smoke",
        true
    },
    {
        "INDEX_X64_CNX",
        "index_x64_cnx_smoke.dts",
        "CNX-on-x64 policy proof (owner ruling 2026-08-09): explicit .cnx attaches on a v64 table with an advisory instead of the old hard refusal; SET ORDER honors the .cnx both as an explicit container and via the bare-tag fallback when no .cdx exists; bare REINDEX routes to the CNX engine when the active order is CNX; and the CDX/LMDB default is proven UNCHANGED when no .cnx is requested. Self-bootstrapping disposable copy in SANDBOX (students_cnx64_smoke), self-erasing. This is the lane's final test promoted to a regression per the promote-final-tests rule. Explicit-run until soaked, then promote to the default suite.",
        false
    },
    {
        "CASCADE_ENV",
        "cascade_env_regression.dts",
        "Cascade system-bundle environment proof (AIF-105, promoted final test per the promote-final-tests rule, runtime-proven 2026-08-10): bundle slots stand up, USE auto-attaches the built CDX orders, SET ORDER TAG + ordered traversal follow the tag, SEEK reaches PDU-100 through the SKU unique tag, and ERP CASCADE opens the SQLite carrier at the bundle path (ERP CHECK scorecard as transcript evidence). C_T1/T2 deliberately encode the MEASURED lexicographic ordering of the N-type ITEM_ID key (1,10,11..) -- a recorded behavioral-parity difference vs SQLite's numeric order for the lane's parity oracle; if numeric key encoding lands, repoint them (IDXSTALE precedent). Section 2 (proven 2026-08-10): WORKSPACE LOAD cascade_all restores 43 areas + 58 relations (logical-name plane -- REL resolves x64 LONG names, CDX resolves descriptors), then SET RELATION traversal is asserted BY FIELD VALUE: parent TOP/BOTTOM + REL REFRESH drives the child to SO 1 / SO 6 (child recno measured 1 -> 11). House semantic recorded: slaving is REFRESH-driven, not implicit per movement. Requires workspaces/cascade_all.dtschema. Read-only; no fixture mutation. Explicit-run until soaked, then promote to default.",
        false
    },
    {
        "MEMO_RAM_HELLO",
        "memo_ram_hello.dts",
        "x64 memo field lifecycle in RAM (promoted final test, runtime-proven 2026-08-11): CREATE X64 with NOTES M in the RAM VFS, write a memo string, close/reopen, read it back as TEXT, and update after reopen -- H_T1/H_T2/H_T3 all field-value markers. H_T2/H_T3 are exactly the two KNOWN-RED cases MEMO_X64_REOPEN_CANARY_20260513 recorded (memo reading back as its reference token after reopen; REPLACE reporting 'memo backend not attached') -- both measured GREEN on the RAM path 2026-08-11, so that canary's expectations are stale and it is due a disk-path rerun and repoint (IDXSTALE precedent). Born as an owner tiny-favor ('append a memo field to students, copy to RAM, say hello') that re-measured a three-month-old defect by accident. Students-shaped structure built fresh because no ALTER-add-field verb exists yet (named gap: sql_ref ALTER-TABLE-ADD). CORRECTED 2026-08-11 (measured by the hydration leak check): the original 'zero disk writes' claim was FALSE -- the DBF lives in ramfs but the DTX memo sidecar does its own file I/O, bypasses the VFS, and lands as a REAL file (data/ram/STUDMEMO.dtx, 4624 B, survived unmount). This solved the named VDISK census gap: 'RAM files = 1 despite (+ memo)' was the census telling the truth. Lifecycle markers stand; the memo RESIDENCY claim does not. Ramfs coverage for the memo store layer is the chartered prerequisite for true RAM memos. Explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_MEMO",
        "workspace_memo_regression.dts",
        "Workspace-in-memo proof (AIF-070 M2/M3, promoted final test per the promote-final-tests rule, runtime-proven 2026-08-11): a whole database posture (43 areas + 58 relations) is saved INTO a memo field of the self-creating WORKSPACES catalog (WORKSPACE SAVE <name> MEMO -- x64 table, FLOCK per append, attributed via current_member, append-history with SUPERSEDED per owner ruling D4, SET PATH roots recorded because .dtschema payloads are root-relative) and restored FROM INSIDE THE TABLE (WORKSPACE LOAD <name> MEMO), then proven live: refresh-driven SET RELATION traversal drives the child to SO 1 / SO 6 / record 11, and SQLSEL agrees cursor-neutrally (WM_T1..WM_T4). The save's oracle byte-compares the payload against the token read back FROM THE FIELD -- a len=10 truncation of the canonical 16-hex x64 memo token slipped past a memory-ref oracle once (2026-08-11) and cannot again. One format, two carriers; the .dtschema text is byte-identical in file or memo. Writes catalog rows by design (append-history, reruns supersede). Requires workspaces/cascade_all.dtschema + the cascade_erp bundle. Explicit-run until soaked, then promote to default.",
        false
    },
    {
        "WORKSPACE_V3",
        "workspace_v3_selflocate.dts",
        "DTSHEMA 3 step 1 (owner-chartered 2026-08-11, promoted final test, runtime-proven same day, build 14:47:06): version 3 is v2 plus declarative lines -- FLAVOR (measured from the open areas at save time, never declared: versionByte 0x64/V128=X64, 0x30-32=VFP, V32=X32, disagreement=MIXED) and DBFROOT/IDXROOT/LMDBROOT (owner suggestion: the posture stores its own dbf/index/lmdb locations; LMDBROOT is recorded-not-applied, disk-only application chartered). v3 is opt-in per save (trailing V3 keyword, combinable with MEMO in either order); v2 remains the default so every proven producer and consumer is untouched -- the owner's no-blowing-up-2 rule, enforced by pairing this with WORKSPACE_MEMO green on the same build. The proof deliberately BREAKS the environment (SETPATH to the default roots) before the v3 load; restoration of all 13 MCC areas plus a readable STUDENTS row (V3_T1) proves the payload's roots -- not the environment -- resolved the tables, because the loader re-points its resolution roots at the payload's DBFROOT/IDXROOT lines for that load only (global SETPATH never mutated). Self-locating postures end the env-first fragility that made every workspace script SETPATH before LOAD. Writes catalog rows by design (append-history; reruns supersede). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_RAM",
        "workspace_ram_hydrate.dts",
        "Memo -> RAM hydration (owner lane step 2, promoted final test, runtime-proven 2026-08-11 build 14:59:07): WORKSPACE LOAD <name> MEMO RAM copies the posture's tables + native CDX files from their DISK homes into the mounted RAM VFS and loads with roots re-pointed at RAM (the DTSHEMA 3 self-location mechanism reused as the hydration vehicle). The copy goes through xbase::ramfs streams, NEVER std::filesystem -- the VFS is in-process and an OS copy would land on real disk while claiming RAM (a false hydration). LMDB is not hydrated: owner rule 'lmdb only for disks', grounded in ramfs.hpp's own contract (LMDB must mmap a real OS file). First measure: 24 file(s), 92139 B in 94.2 ms for the 13-table MCC posture, VDISK census agreeing byte-for-byte (92139 B / 24 files) -- an independent cross-check of the hydration counter. HYD_T1 asserts a STUDENTS row reads from the RAM-resident copy. Index attach in RAM, measured 2026-08-11 (ENROLL, hydrated .cdx): the LMDB-backed route fails ('SET ORDER: failed.' -- no LMDB in RAM, by design) and the native-CDX fallback then attaches (SET ORDER: CDX TAG 'SID'); attach is proven, ordered-traversal-by-value assertion is a chartered follow-up. Environment note: the source-authoring leg MUST run under DO x64 -- without the LMDB slot, LOAD attaches zero CDX orders and the posture records index=none (measured: the 13-vs-24 hydrated-file variance). VDISK UNMOUNT at the end IS the dismiss exit of the chartered two-exit close (save-state or dismiss); the save-state exit is the lane's next step. Memo-sidecar hydration chartered with the Part B MCC regeneration (no MCC table carries a memo field yet). Self-contained: authors its own v3 source posture (ram_hydrate_src) from mcc_x64. Writes catalog rows + mutates only the RAM VFS (self-erasing on unmount). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_SESSION",
        "workspace_session_state.dts",
        "v3 session-state capture (owner requirement 2026-08-11 'we need the cursor states and refresh relations'; promoted final test, runtime-proven same day, build 15:22:32, FIRST TRY): a v3 save emits CURSOR <area> <physical-recno> per open area plus CURRENT <area>; the v3 loader applies them after AREA/REL restoration, the saved selection outranks normalization, and the final refresh slaves children to the RESTORED parents -- so a workspace save is now a complete session snapshot: shape, index attachments, keys, cursors, selection, and refresh state. PHYSICAL recno is the recorded anchor per the GPS prior art (owner pointer: see cmd_gps.cpp -- logical row is derived from physical under the active order, so physical is what restores exactly); GPS is the post-restore verifier. Old loaders skip the lines (tolerate-unknown, the KEY precedent) -- v2 coexistence preserved. Proof: Sales_Orders driven to BOTTOM (SO 6) with child slaved, session saved (9792 B = posture + 43 CURSOR lines + CURRENT), full teardown, reload -- '(+ 43 cursor(s))', GPS Area 21 Physical Recno 6 / Logical Row 6, SS_T1 parent at SO 6 not row 1, SS_T2 child re-slaved to Recno 11 through the load's own refresh. Writes catalog rows (append-history; reruns supersede). Requires workspaces/cascade_all.dtschema + the cascade_erp bundle. Explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_MINIDB",
        "workspace_minidb.dts",
        "Memo-resident mini-database (AIF-070's chartered destination LANDED, owner 'do it' 2026-08-11; promoted final test, runtime-proven same day build 18:35:35 FIRST TRY): WORKSPACE SAVE <name> MEMO MINIDB writes a MINIDB 1 container -- the self-locating v3 posture PLUS every open table's bytes and every attached native index's bytes, length-prefixed and binary-safe (the memo store's payload-agnosticism, zoo-proven on embedded NULs, is what makes DBF/CDX bytes legal cargo). WORKSPACE LOAD <name> MEMO RAM detects the container and hydrates FROM THE PAYLOAD: memo -> RAM VFS, ZERO disk reads; the carried posture then stands areas up re-pointed at RAM. Reads are residence-aware (RAM-resident sources come from ramfs), so a RAM session can save its whole working set into a memo -- the owner's save-the-state vision. Plain MEMO load refuses a MINIDB payload with the hydration instruction rather than half-loading. First measure: mcc_db = 94200 B container (92139 B tables+indexes, 1443 B posture), oracle byte-compare OK on the WHOLE container; hydration onto a clean RAM disk 65.5 ms -- FASTER than disk-sourced hydration (71-94 ms) because it is memory to memory; STUDENTS row read and ENROLL CDX attached from memo-carried bytes (DB_T1/DB_T2). The catalog row records FMT='MINIDB 1'. What this makes true: a whole small database -- data, indexes, posture, session state -- lives inside one memo field of another database, versioned by the supersede chain, attributed, oracle-verified. Memo-sidecar carriage LANDED 2026-08-12 (AIF-108 [SIDECAR] unblock): the container now also carries each open area's attached memo sidecar -- the backend names its own file (IMemoBackend::path(), flushed before capture), no extension guessing -- and hydration lands sidecars on the REAL filesystem under the mount dir, because the DTX layer bypasses the ramfs (bypass-ledger member 1) and would never see a VFS-resident sidecar; the disk landing is the measured status quo made deliberate. Act-2 proof (DB_T3/DB_T4) is residue-hardened: the live sidecar is POISONED after the container is saved, so a green can only come from container bytes (hydration truncate-overwrites residue); DB_T4 proves post-hydration writability. Still chartered: the writeback cycle (RAM -> disk commit), LMDB carriage (out of ramfs scope by contract), ramfs memo-store coverage (which would collapse the sidecar disk landing into the VFS). Writes catalog rows; mutates the RAM VFS plus one real-disk sidecar residue (MDMEMO.dtx under data/ram, truncated by the next run). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false
    },
    {
        "USE_AGAIN",
        "use_again_regression.dts",
        "USE ... AGAIN: a second work area on an already-open DBF (workspace design I5 v1 arm, "
        "owner 'add use again' then 'fix the use command' 2026-08-12). Every marker is a "
        "field-value comparison, and the count is deliberately not stated here -- it changed "
        "three times on the day of writing, and a literal that drifts is worse than no literal: "
        "UA_G0 fixture by value; UA_T1a/UA_T1 duplicate USE WITHOUT AGAIN stays a no-op, proven "
        "at BOTH ends -- the target area keeps its sentinel table AND area 1 is undisturbed, "
        "which took a correction, because asserting only the second is green even if the guard "
        "is deleted outright (a second instance opening in area 2 does not touch area 1); "
        "UA_T2 the AGAIN instance reads row 1 by value from a second area; "
        "UA_T3 is the COHERENCE MEASUREMENT -- a write through area 1 re-read through area 2 -- "
        "which measures v1 rather than assuming it (a red here is a finding about two fstreams "
        "on one file, not a broken spec); UA_T5 memo-carrying tables REFUSE AGAIN -- two sidecar "
        "appenders would interleave offsets, the AIF-110 shape landing where it would be "
        "permanent -- and the FIRST instance survived the refusal, by value. "
        "UA_T4 TOOK THREE CUTS AND THE HISTORY IS THE LESSON: .NOT. (ID = 7) and then "
        "RECCOUNT() = 0 were both asserted in the EMPTY target area, and neither COULD work, "
        "because the marker evaluator binds a null area unless the area is OPEN "
        "(rhs_eval.cpp:969) -- being closed was the very thing under assertion. So cut 1 passed "
        "because its symbol was unresolvable rather than because the refusal fired, reproducing "
        "one layer down the defect that splitting T4 from T5 was meant to remove. Generalised and "
        "worth carrying: NO MARKER IN THIS LANGUAGE CAN ASSERT THAT AN AREA IS EMPTY, and an "
        "errored marker PRINTS NOTHING rather than going red, so a green count still reads full "
        "while a claim has silently left the suite. Cut 3 asks an answerable question instead -- "
        "did a KNOWN OCCUPANT SURVIVE -- and forced the source fix it needed: the memo guard ran "
        "AFTER reset_area_runtime_best_effort() and a.open(), so it destroyed the target area's "
        "occupant and then printed 'Nothing was opened'. Hoisted into the duplicate-open guard, "
        "where AGAIN's own precondition makes the probe free (the file is already open elsewhere, "
        "so its field list is in memory and no filesystem is touched). "
        "UA_T6/T7/T8 are the ALIAS arm, and it is not a convenience clause: without it USE AGAIN "
        "produced a second cursor that was open and UNREACHABLE BY NAME, since both instances "
        "took the file stem and find_open_area_by_name_ci (workarea_util.cpp:29, 18 call sites) "
        "returns the FIRST match with no diagnostic -- so SET RELATION silently bound the "
        "lower-numbered area, and naming is how a join is declared. T6 proves the alias RESOLVES "
        "(asserted by value THROUGH SELECT <alias>, not by reading the name back, which would "
        "only prove a string was stored); T7 a duplicate explicit alias is refused with the "
        "target area's DIFFERENT table intact -- distinct on purpose, because the first draft "
        "used the same table and would have gone green even if SELECT had failed; T8 the refusal "
        "did not evict the name's real holder. Aliases are refused rather than renamed when "
        "explicit, auto-derived and ANNOUNCED (<table>2) when implicit, and all-digit aliases are "
        "refused because SELECT would read them as area numbers. Owner-found stubs confirmed "
        "while doing it: DbArea::_db_name has three writers and ZERO readers, and the "
        "_setLegacyName SFINAE wrapper has always selected its empty fallback because DbArea has "
        "no setName() -- a silent no-op under a comment reading 'legacy alias', which is why "
        "AREA prints Logical name and Legacy name() identically. The table-name-vs-alias split "
        "those fields were shaped for needs a DbArea accessor and is priced separately. Related: "
        "RECCOUNT was surfaced beside DELETED in glue_xbase.cpp and is real, but it serves "
        "compile_predicate -- scan and FOR clauses over an OPEN area -- not the '?' marker path. "
        "v1 boundaries stated in "
        "the arm itself: AGAIN forces PHYSICAL ORDER (a second in-process attach would "
        "double-open one LMDB environment, undefined by LMDB's contract, cdx_backend.cpp:224) "
        "and writes are arbitrated by record locks per the owner's multi-user model -- "
        "intra-process lock isolation arrives with the (pid,workspace) owner (design I5). "
        "Index-attach-on-AGAIN and memo-share-on-AGAIN are later separately-gated arms. "
        "Self-bootstrapping throwaway UAREGR/UAMEMO in SANDBOX, self-erasing; explicit-run "
        "until soaked.",
        false
    },
    {
        "WORKSPACE_WRITEBACK",
        "workspace_writeback.dts",
        "The return leg of disk -> memo -> RAM -> disk (AIF-070's last arm; verb owner-ruled 2026-08-12 over PERSIST and FLUSH, pairing with the settled DISMISS). WORKSPACE WRITEBACK writes every table the POSTURE declares plus each area's memo sidecar out of wherever they currently live -- residence-aware, so a RAM working set writes out fine -- and onto a real disk root, defaulting to the catalog row's DBF_ROOT because that is what 'write it back' means. Hydration is the proven inverse, so the round trip IS the test: WB_T1/WB_T2/WB_T3 read Taylor Quinn, 200 records, and a null-virgin memo out of files that made the full circuit; WB_T4 proves it was not a one-table accident. WHAT THIS SPEC REALLY GUARDS is the enumeration authority: the manifest comes from the posture's AREA lines -- the record of what the workspace IS -- not from the session's attached order, because the first cut asked the session and silently wrote 15 of 27 files while reporting cheerful success, and that same order-dependent enumeration is why a canonical posture once omitted students.cdx. A count is a fact about a loop until something declares what it SHOULD be. Owner correction that shaped the fix: enumerating by naming convention would have been assumption wearing a respectable coat, and pinning the container into the posture would have killed indexing orthogonality -- a workspace stores its index CHOICE per table (index=/indextype=), which is what lets one workspace mix CNX, CDX and INX, with the x64-prefers-CDX autoload only a fallback. So index FILES are not written by default (derived, rebuildable at the destination, WITH INDEXES for a byte-mirror) while the choice travels in the posture. WB_T5/WB_T6 are the refusal arms and matter as much as the green ones: a shortfall ABORTS rather than writing a partial workspace that looks finished, and an abort leaves the filesystem untouched INCLUDING empty directories -- measured, because the first cut created target dirs before the manifest check while printing 'Nothing was written'. Safety stack proven by construction: gather-all-before-writing (a read failure aborts having written nothing), zero-byte-source abort (that is the AIF-110 corruption shape, and writeback is where it would become permanent), CONFIRM required to replace existing files with the replacement list printed first, .__wbak copies of everything replaced, and an oracle re-read plus byte-compare on every landed file. Writes to dbf/wbregress and erases it; requires the mcc_minidb_memo catalog row. Explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_LOADSHORT",
        "workspace_load_shortfall.dts",
        "WORKSPACE LOAD refuses a partial restore, and refuses it BEFORE anything is closed (owner-directed 2026-08-12). "
        "THE ASYMMETRY CLOSED: both ends of this lane read the same manifest -- the posture's AREA lines -- and reached "
        "opposite verdicts on the same shortfall. WRITEBACK: 'ABORTED -- the posture declares 13 table(s); 12 are not open "
        "... Nothing was written.' LOAD: 'restored 0 area(s)'. The second was MEASURED, not supposed: a v3 posture whose "
        "declared DBFROOT had been deleted closed every area, failed all 13 opens, and ended on a sentence containing the "
        "word 'restored' -- honest line by line, a lie in summary, and a script reading the last line saw success. "
        "THE FIX IS THE ORDERING, not the wording: the old loader called schema_close_all() BEFORE discovering it could not "
        "refill those areas, so even a corrected message would have reported damage already done. Now RESOLVE-ALL-BEFORE-"
        "CLOSING, the mirror of writeback's proven gather-all-before-writing, sharing ONE resolver and ONE field parser with "
        "the loader so a preflight cannot drift from the load it guards. Probes are RESIDENCE-AWARE (ramfs::is_virtual then "
        "ramfs::exists, never std::filesystem) or a hydrated RAM workspace would be reported missing. L_T1 is the arm that "
        "matters and it does not assert that the load failed -- it asserts the ORIGINAL session SURVIVED it, by reading a "
        "field out of an area left deliberately open. INDEXES ARE NOT CHECKED, by design: derived, rebuildable, the choice "
        "travels in the posture, and refusing over a missing .cdx would refuse a recoverable workspace; L_T5 asserts that "
        "non-check so a future tightening fails here instead of surprising someone mid-restore. PARTIAL keeps the old "
        "permissive behaviour as an explicit choice (house idiom: ERASE ... CONFIRM, WRITEBACK ... CONFIRM). Mutation-killed "
        "before promotion: un-remove the member -> only L_T2 reds; force PARTIAL on the refusal arm -> only L_T1 reds; "
        "delete a table in the index arm -> only L_T5 reds. Areas are selected BY NAME, never ordinal -- the x64 root carries "
        "FMGRTST.__fldbak and the scratch root does not, which produced two false reds in the first draft. "
        "Writes dbf/lsfall and erases it; leaves catalog rows ls_probe / ls_idxprobe. Requires mcc_minidb_memo. Explicit-run until soaked.",
        false
    },
    {
        "FIELDMGR_APPEND",
        "fieldmgr_append.dts",
        "In-place schema mutation, values-not-shape (the regression AIF-110 proved nobody ever wrote; authored 2026-08-12 the morning after the defect landed). FIELDMGR APPEND rewrites a table through a temp create / record copy / backup swap / reopen. On 2026-08-12 that rewrite was found to BLANK-CORRUPT every x64 table it touched -- record count, schema, field descriptors, and deleted flags all read CORRECT while every field value became 0x20 -- because the loop never called writeCurrent(): set() only fills an in-memory vector that the next appendBlank() discards. THE DOCTRINE THIS SPEC CARRIES: a test that asserts SHAPE passes green on a blanked table, so every marker here asserts a FIELD VALUE. Seven arms: FA_T1 values survive the rewrite; FA_T2 the appended memo reads empty rather than garbage; FA_T3/FA_T4 a long field name (> 10 chars) resolves after the rewrite and round-trips a value written THROUGH it -- the x64 two-tier naming scheme, X64M carrying the authoritative long name while the descriptor carries the field_name_policy 10-byte token (long names were REFUSED before this lane, not merely untested); FA_T5 the DELETED-ROW arm, which is the arm that would have caught the original defect on day one -- deleteCurrent() ends in its own writeCurrent(), so deleted rows survived correct while live rows blanked, and the MCC fixtures have no deleted records, which is exactly why the corruption read 200/200 and looked total; FA_T6 the BINARY-CODEC arm (I/B/Y/T round-trip), which doubles as a live probe of a flagged latent -- those codecs have 16 encode() failure sites and storeFieldsToBuffer SWALLOWS the result, leaving the space-padded region, the same silent-blank shape one layer down, so a red here converts a suspicion into a numbered defect; FA_T7 a third row intact across TWO successive rewrites. Not covered, stated rather than implied: the deleted FLAG itself (only the deleted row's data is asserted), legacy-flavor appends, MODIFY/DELETE field ops (not implemented), concurrent append. Creates and erases its own disposable x64 table; cannot run in the RAM VFS because the rewrite swaps files with std::filesystem::rename, which the ramfs does not serve. Explicit-run until soaked.",
        false
    },
    {
        "X64_METRICS",
        "canaries\\x64_matrix_metrics_boundary_canary.dts",
        "x64 structural boundary proof above legacy 16-bit record/header limits",
        true
    },
    {
        "LANGUAGE",
        "canaries\\language_shakedown_canary.dts",
        "Messaging-normalization locale proof: es/fr/de/it USAGE render across the localized command surface",
        true
    },
    {
        "HARVEST",
        "main\\harvest_top_shakedown.dts",
        "Top-layer harvest proof across regression launcher, security roles, holiday demos, and curated runtime shakedowns",
        false
    },
    {
        "CURSOR",
        "CURSOR_FAMILY_REGRESSION_001.DTS",
        "Navigation/cursor family regression on classic ordered traversal",
        false
    },
    {
        "RELJOIN",
        "main\\rel_join_enum_regression.dts",
        "Relation join/enum projection regression",
        false
    },
    {
        "LIMITS",
        "limits\\limits_all_shakedown.dts",
        "Engine limit guardrails: MAX_AREA=512, x64 name ceilings 256, record-size advisory, CLOSE ALL over every open area",
        false
    },
    {
        "DOTSCRIPT_EXPR",
        "dotscript\\dotscript_expr_regression.dts",
        "DotScript memvars (VAR/$name) + arrays ({}/$a[n], nested/chained) via the house expression path, with an IF literal baseline (AIF-041 M1)",
        true
    },
    {
        "DOTSCRIPT_PARITY",
        "dotscript\\predicate_memvar_parity_regression.dts",
        "Predicate parity target: $name/$a[n] in IF/WHILE/WHERE -- now GREEN via the shared house-evaluator bridge (AIF-041, landed 2026-07-21). Fixture-free, self-asserting; safe for the default suite",
        true
    },
    {
        "LEXING",
        "lexing\\comment_handling_regression.dts",
        "Canonical comment vocabulary on the script path after the AIF-037 lexer consolidation (full-line * REM # //, inline && #, single & macro survives); read-only, fixture-free",
        true
    },
    {
        "CALC",
        "calc\\calc_output_regression.dts",
        "CALC output-routing regression: every ValueKind path (Bool/Number/String/Date/empty/Error) via cli::cmdout::print_line (AIF-031); read-only, but leaves ECHO ON so it stays out of the default suite (explicit run)",
        false
    },
    {
        "ERRORSTOP",
        "errorstop\\stop_on_error_regression.dts",
        "stop_on_error threshold: OFF continues past a recorded error, ERROR aborts at the failing line; self-contained, but Phase-2 aborts leaving STOP_ON_ERROR ON so it stays out of the default suite (explicit run) (AIF-036)",
        false
    },
    {
        "WAL_COMMIT_ROLLBACK",
        "pinocchio\\wal_commit_rollback_regression.dts",
        "WAL durability: COMMIT applies a buffered+logged REPLACE, ROLLBACK discards one; self-bootstrapping (creates+erases a throwaway WALREGR table, never touches the students fixture), self-asserting W0/W1/W2 markers. Mutates the filesystem so it stays out of the default suite (explicit run) (AIF-017/023)",
        false
    },
    // NOTE: this WAL_COMMIT_ROLLBACK entry replaces the legacy commit_rollback_test.dts,
    // which assumed an already-open `students` table, did not self-bootstrap (regression
    // doctrine violation), and silently no-op'd when run standalone. The self-contained
    // basis is pinocchio\wal_phaseA_proof.dts (throwaway table, ERASEd at end).
    {
        "INDEX_TXN",
        "migrated\\index_txn_lmdb_maintenance.dts",
        "SET INDEXTXN transactional in-COMMIT index maintenance: buffered REPLACE/DELETE + COMMIT maintains the live CDX/LMDB index with NO BUILDLMDB. Self-asserting and fixture-free (builds + erases its own throwaway x64 IDXTXN table; never touches students). Scored on ORDERED position = index-truth (T1 commit-maintains, T2 dup-survivor): OFF => .F. (RED), ON => .T. (GREEN). Mode is env-driven (DOTTALK_INDEX_TXN) or runtime SET INDEXTXN; the script does not force the flag. Out of the default suite (mutates the filesystem; explicit run) (AIF-027/023; feeds AIF-041 M1)",
        false
    },
    {
        "SCAN_PARITY",
        "dotscript\\scan_memvar_parity_regression.dts",
        "Scan-path parity: $name resolves in a FOR/scan predicate (eval_bool: LOCATE/COUNT/SCAN/LIST FOR + SET FILTER) via the shared bridge. GREEN since the AIF-041 scan convergence landed (2026-07-21). Self-bootstrapping throwaway SCANREGR in SANDBOX; stays out of the default suite because it mutates the filesystem (explicit run) (AIF-041)",
        false
    },
    {
        "DEF_FAMILY",
        "dotscript\\def_family_regression.dts",
        "Runtime DEF-family testbed: DEFCMD/DEFFN/EXAMPLE define-invoke-arg-compose-list-remove, session-only, no rebuild (RUNTIME_DEF_FAMILY lane). Self-bootstrapping; opens/mutates no table or file (only the session command/function registries, which it cleans up). Permanent worked example of the AI-friendly dev-tools. Explicit-run until proven green in-suite, then promote to default.",
        false
    },
    {
        "MEM",
        "mem_proof.dts",
        "AIF-043 in-memory indexed table end-to-end proof: DO mem mounts the in-process RAM VFS (xbase::ramfs), then an x64 table AND its native CDX-V64 index are built, indexed, and traversed entirely in RAM (RUN8, no LMDB, zero files on disk). Self-contained (leads with DO mem, clean-slate remount) and self-asserting: ordered read-back must yield ADAMS/MILLER/ZEBRA (MEM_T1/T2/T3 = .T.); teardown unmounts and restores the x64 disk env. Mutates the RAM VFS only (no disk table), but kept out of the default suite (explicit run) until soaked. (AIF-043)",
        false
    },
    {
        "BUILD_VECTORS",
        "dotscript\\build_vectors_regression.dts",
        "Build-vector runtime report (AIF-044 M4): BUILDVECTORS prints the compiled capacity authority; GATE #1 proof (areas=512, fields=256, rows=int64max). Read-only, no fixture/mutation. Explicit-run until proven, then promote.",
        false
    },
    {
        "IDENTITY_PERSIST",
        "dotscript\\identity_persistence_regression.dts",
        "Identity/RBAC DBF persistence round-trip (AIF-045 2b-ii, APH-5): USER SAVE writes the nine SYS* identity tables, USER VERIFY reloads and confirms counts, user id/key/profile, and every member x permission authorize() verdict are preserved. Writes DBF under data/metadata/identity only; no fixture mutation. Explicit-run until proven, then promote.",
        false
    },
    {
        "PHASE0_DECODE_COST",
        "pinocchio\\ticketb_phase0_decode_cost.dts",
        "Scan-evaluator baseline benchmark (scan-evaluator optimization lane M0): self-times SUM GPA / COUNT FOR (1 term) / COUNT FOR (3 terms) over the 1,000,000-row pinocchio STUDENTS fixture via SET TIMER (now script-aware) cross-checked by fractional SECONDS(). Read-only, no mutation. Baseline floor (Alienware m16 R2 / Core Ultra 9 185H): SUM ~19.5s, DEC1 ~38.5s, DEC3 ~70.5s. NOT a pass/fail regression and long-running (~2+ min); requires the 1M-row pinocchio fixture. EXEMPT from REGRESSION ALL by design -- explicit run only, as the M1-M4 speedup floor. (scan-evaluator lane, origin AIF-043 Ticket B Phase-0 KILL)",
        false
    },
    {
        "IDENTITY_ACCEPT",
        "dotscript\\identity_accept_regression.dts",
        "AI-agent local-security accept cycle (AIF-045 2c): admits a throwaway AI member, proves the resolver DENIES git.commit, owner USER GRANT flips it to ALLOW, USER UNGRANT flips it back to DENY, then USER DELETE removes it. Repeatable + self-cleaning (deletes any leftover up front and at the end). Mutates only data/metadata/identity (adds+removes a throwaway member); seeded rows intact. Explicit-run until proven, then promote.",
        false
    },
    {
        "HELP_DIDYOUMEAN",
        "dotscript\\help_didyoumean_regression.dts",
        "HELP unknown-topic feedback + did-you-mean (AIF-047 M1-M3): HELP GAINT -> 'No help found for: GAINT' + 'Did you mean: GIANT, ...' (soundex phonetic), HELP SELCT -> SELECT, HELP GIANT <unknown> shares the not-found terminal, and SOUNDEX(\"GIANT\") still returns G530 after sharing its implementation with the suggester. Read-only, no mutation. Explicit-run until proven, then promote.",
        false
    },
    {
        "BBS_LANE",
        "bbs\\bbs_lane_regression.dts",
        "AI-BBS command-surface smoke (AIF-052/054/055): BBS BOARDS tops up + lists the seeded rooms (governance/afb.chat/notice/lounge/guestbook), BBS READ board.governance renders the SYSGRANT projection, and a POST/READ round-trip on board.afb.chat self-asserts. Read-mostly (first BBS BOARDS tops up the board store, idempotent after; no fixture touched). The guest-scoping SECURITY regression lives in the socket smoke D:\\code\\bbs_smoke.ps1 (server-side permission denial needs the listener). Out of the default suite (explicit run).",
        false
    },
    {
        "DDL_SCHEMA",
        "ddl\\ddl_schema_flavor_regression.dts",
        "DDL schema flavor smoke (AIF-063): creates classic MSDOS/DBASE and X64 throwaway tables from JSON schema fixtures, writes seed blanks through the DBF backend, reopens them from TMP, and self-asserts classic fields plus X64 long logical names. Emits sidecars and documents index declarations as metadata-only in this milestone. Mutates TMP only, so it stays out of the default suite (explicit run).",
        false
    },
    {
        "SQLSEL_BUFFER_VIS",
        "sqlsel_buffer_visibility_regression.dts",
        "SQLSEL/TUPLE TABLE BUFFER visibility split (AIF-074 follow-up): TUPLE remains buffer-preview, while SQLSEL SELECT projects the same committed table truth its WHERE predicate scans. Self-bootstrapping throwaway SQLBUFVIS table in SANDBOX; explicit-run because it mutates the filesystem.",
        false
    },
    {
        "SQLSEL_SELECT_V1",
        "sqlsel_select_v1_regression.dts",
        "SQLSEL statement surface, gate G3 (AIF-074 P3): SELECT <cols|*> FROM <table> with WHERE, ORDER BY [ASC|DESC], LIMIT and COUNT(*), each row set compared against an in-process SQLite oracle over identical data in the same run. Asserts cursor neutrality by data (the cursor is parked on a known record before and after), corrective errors for an unopened table / expression select-item / bad LIMIT / unknown ORDER BY field / ORDER BY on COUNT(*), and that ORDER BY sorts the full match set BEFORE LIMIT applies. Legacy predicate form preserved. Self-bootstrapping throwaway SQLSTU table in SANDBOX; explicit-run because it mutates the filesystem.",
        false
    },
    {
        "EVALDIFF",
        "evaldiff_regression.dts",
        "SQLSEL evaluator differential harness (AIF-074 P4.0a): self-bootstraps a mixed-type X64 fixture in SANDBOX, compares classic DbArea and TupleRow-bound predicate outcomes over the same physical records, reports verdict/failure parity and known differences, restores the cursor, and self-erases. Observer only; explicit-run while findings are being classified.",
        false
    },
    {
        "EXPORT_SDF",
        "export\\export_sdf_regression.dts",
        "EXPORT SDF smoke: creates a throwaway table in SANDBOX and exports fixed-width, space-padded records with TUPTALK PUSH ROW-compatible alignment. Explicit-run because it writes an output text file.",
        false
    },
    {
        "IDXDIFF",
        "index_replace_diff_bench.dts",
        "Index replace-diff benchmark (item A, session 2026-07-30): apply_replace_snapshot now emits only the tags whose (tag,key) actually moved instead of deleting and re-inserting every tag, turning a single-field REPLACE on an N-tag table from 2N committed LMDB write transactions into 2. Builds a throwaway 4-tag x64 table, replaces one indexed field then one non-indexed field, and carries two correctness markers (moved key reachable, skipped tag intact). MEASUREMENT is external: run with DOTTALK_INDEX_TRACE=1 and read the '[INDEX TRACE] apply_replace ... emitted_del/emitted_ins/skipped' lines; a .dts cannot count engine trace output. Expect 1/1 skipped=3 for the indexed edit and 0/0 skipped=4 for the unindexed one. Explicit-run: benchmark, not a pass/fail gate.",
        false
    },
    {
        "VUREPAIR",
        "validate_unique_repair_index_proof.dts",
        "VALIDATE UNIQUE ... REPAIR maintains the active index (item C1, session 2026-07-30): builds a throwaway x64 table with a duplicated key, indexes the uniqueness-candidate field via CDX, repairs the duplicate, then asserts the repaired record is reachable at its NEW key with NO REINDEX between (VUR_T2) and that the surviving legitimate duplicate is still correct (VUR_T3). Runtime-proven 2026-07-30 on the wsl-lean build. REPAIR previously used set()+writeCurrent(), which carry no index hook, and left the tag pointing at the old value with nothing marked stale. Proven on x64/CDX. It was ALSO restricted to x64/CDX because CnxBackend upsert/erase were stubs, so x32/CNX would have failed for an unrelated reason -- that restriction LAPSED 2026-07-31 when XIDX-TXN-02 M1 gave CNX realtime maintenance (see CNXLIVE). Whether VUREPAIR now passes on x32/CNX is UNMEASURED; the blocker is gone, the run has not been done. Self-bootstrapping and self-erasing; explicit-run until proven green.",
        false
    },
    {
        "IDXSTALE",
        "index_maintenance_failure_proof.dts",
        "Index-staleness REPORTING on a backend that cannot maintain incrementally (item E, session 2026-07-31): apply_replace_snapshot compares wasStale() across the apply and reports a false->true transition, so such a backend is no longer silent; wasStale() had seven overrides and ZERO call sites (AIF-079 instance 1). SUBJECT REPOINTED 2026-07-31: this ran against CNX/v32 until XIDX-TXN-02 M1 gave CNX realtime maintenance, at which point CNX stopped qualifying and E_T2 correctly inverted to .F. The test was not wrong -- its subject moved -- so it now targets native CDX-V64, whose upsert/erase are STILL no-op stubs that set stale_ and return normally (cdx_native_backend.cpp:507-519). That is the RAM/vdisk x64 path, so this now covers the in-memory lane; the realtime CNX behaviour that replaced it is proven separately by CNXLIVE. Scored on ORDER, not key lookup -- a native SEEK compares LIVE field values through a stale recno ordering, so a key probe proves nothing either way (measured on CNX: after moving MILLER->AAAAA, SEEK MILLER misses and SEEK AAAAA still hits). E_G0/E_G1 guard the fixture, E_T2 shows the stale order still starting at ANDERSON, E_T4 shows REINDEX fixing it. If E_T2 ever reads .F. the backend has GAINED realtime maintenance and this proof needs repointing again. Every marker is a FIELD comparison: RECNO() and FOUND() render EMPTY in a '?' marker and STR() does not rescue them. Builds a throwaway x64 table entirely in the RAM VFS and unmounts on teardown, so it writes nothing to disk; explicit-run until re-proven against the new subject.",
        false
    },
    {
        "CNXLIVE",
        "cnx_realtime_index_proof.dts",
        "Realtime CNX index maintenance (XIDX-TXN-02 M1, session 2026-07-31): a REPLACE that moves an indexed value re-places that record in the CNX ordering IMMEDIATELY, with no REBUILD between the edit and the ordered read, and the staleness warning is correctly ABSENT (trace 'staleBefore=no leftStale=no'). The positive counterpart to IDXSTALE, which asserts the opposite contract for a backend that cannot maintain; the two are kept separate so the inversion that happened when M1 landed reads as a deliberate split rather than a silently retuned regression. A CNX RUN1 payload stores 4 bytes per recno and NO keys (cnx_document.cpp:81 -> InxEntry{\"\", rn}), so upsert cannot binary-search stored keys: it searches the PERMUTATION, comparing the edited record's live field value against the live value at each probe (~log2 n record reads). The table is the ordering authority, the same authority REBUILD uses, and both share derive_sort_entry_/sort_entry_less_ so they cannot drift -- L_T6 asserts exactly that by re-checking the order after a REBUILD that must be a no-op. L_G0/L_G1 guard the fixture, L_T2 is the marker that inverted (top is AAAAA with no rebuild), L_T3/L_T4 catch an insert that appends instead of placing, L_T5 confirms lookup and order agree. Markers are FIELD comparisons for the same reason as IDXSTALE. Self-bootstrapping v32 table, self-erasing; explicit-run until soaked.",
        false
    },
    {
        "WORKSPACE_SCOPE",
        "workspace_scope_regression.dts",
        "WORKSPACE CLOSE is SCOPED to a workspace (AIF-078 stage 3, owner-directed 2026-08-22: 'close_all needs to be SCOPED to a specific workspace instead of 0-max_areas. workspaces have to know the group of areas that belong to them'). Until stage 3 the close ran for (area0 = 0; area0 < MAX_AREA; ++area0) and was correct only because exactly one workspace had ever existed; stage 2 built the membership group (14 tables opened -> 14 members -> 0 after close, measured 2026-08-22) and this is the first spec that can tell the two implementations apart. WS_T1 IS THAT DISCRIMINATOR: closing a nested workspace must leave DEFAULT's sentinel readable, which the old sweep could not do -- delete the scoping and exactly one line reds. The cost argument rides along and is not secondary: MAX_AREA is 512 for testing and the owner has stated the real ceiling is not 512 ('can you imagine how long it would take to give you a dotscript results of a 10 trillion max_area pass'), so an O(MAX_AREA) close does not survive that sentence while an O(members) close does not care. SET RECURSION ON|OFF is proven by WS_T2 and nowhere else -- owner ruling 'even with OFF we still allow multiple workspaces, just parallel', so the flag gates whether an operation DESCENDS, not whether nesting may exist; same script, same shape, one flag flipped, and the nested workspace's table is still readable afterward. WS_T4 proves CLOSE ALL reached the FILESYSTEM and not just the bookkeeping, by reopening and reading. WHAT IT DELIBERATELY DOES NOT ASSERT, stated rather than implied: that a recursively-closed workspace is EMPTY. USE_AGAIN established over three cuts that NO MARKER IN THIS LANGUAGE CAN ASSERT AN AREA IS EMPTY -- the marker evaluator binds a null area unless the area is OPEN (rhs_eval.cpp:969), which is the very thing under assertion, and an errored marker PRINTS NOTHING rather than going red, so a green count still reads full while a claim has silently left the suite. The recursive close is therefore proven by CONTRAST (WS_T2 under OFF against its absence under ON) plus the member counts in the two WORKSPACE REGISTRY blocks, read from the transcript -- external measurement, the IDXDIFF precedent. Every marker is a FIELD-VALUE comparison per the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. Two guards ride the close path in the engine and both ANNOUNCE rather than returning silently, which is the direct lesson of the relation depth cap (set_relations.cpp, hardcoded 24, twice, silent): a cycle in the workspace tree prints, and the depth cap prints what it did not close. Self-bootstrapping WSDEF/WSPAR/WSCHI in SANDBOX, self-erasing; leaves two runtime-only workspaces declared (they hold no areas and do not survive a restart) and restores SET RECURSION ON. Explicit-run until soaked, then promote to default.",
        false
    },
    {
        "USE_ARGS",
        "use_argument_validation.dts",
        "USE refuses arguments it does not understand, and IN <n> places (AIF-121, 2026-08-22). USE parsed its tail with THREE independent NON-CONSUMING scans -- contains_noindex, contains_again, parse_alias_clause -- each saving the stream position, sweeping for its own keyword, and rewinding. Nothing ever enumerated the tail, so NO TOKEN WAS EVER UNACCOUNTED FOR: unknown arguments were not ignored by oversight, nothing was in a position to notice them. MEASURED at baada444: `USE dbf\\x64\\students` then `USE dbf\\x32\\students IN 1` printed two 'Opened' lines, WORKSPACE REGISTRY reported members 1, and AREA showed slot 0 holding the x32 table -- the second open replaced the first and said NOTHING. `IN <n>` is FoxPro-standard and documented in this tree twice (command_argchk.cpp:47-48, printed in EVERY REGRESSION ALL run, and fox_standard_catalog.cpp:78); it was swallowed, so the house's own CMDREL recipe died on 'No table is currently open.' Implementing the clause makes both doc sites TRUE rather than correcting them down to a limitation. U_T1 IS THE DISCRIMINATOR and asserts two things in one read: after `USE utgt IN 3` it reads MARK WITHOUT selecting, so a green proves the current area is still 0 (IN does not move you -- the FoxPro contract) AND still holds its occupant; under the old parser IN 3 was dropped and utgt opened over it, reding both at once. U_T4 IS THE CONTIGUITY ARM and it MOVED when the allocator was scoped on owner ruling: DEFAULT holds areas 0 and 3, a global lowest-free sweep answers 1, and the workspace-scoped allocator answers 4 -- the slot after this workspace's highest member -- because a workspace's areas stay contiguous and a global sweep can drop an area inside a NEIGHBOUR'S run once two workspaces exist. If U_T4 ever reads 1 again, IN FREE has gone back to workspace-blind. U_T5 is the gate arm and asks the answerable question (did the KNOWN OCCUPANT SURVIVE) rather than asserting a refusal, per USE_AGAIN's finding that no marker in this language can assert an area is empty and an errored marker prints nothing rather than going red. U_T7 covers the digits-only parse: std::stoll would read '3junk' as 3, the same longest-valid-prefix trap that let AIF-116 read pid=16,984 as 16. Owner rulings carried: IN FREE not IN NEXT (NEXT implies forward adjacency the allocator does not keep); AGAIN and IN compose with NO interaction rule because AGAIN carries no placement opinion (cmd_use.cpp:743, it lands in the current area -- so IN is the half AGAIN shipped without, and AGAIN is destructive today unless the caller SELECTs a free area first, which USE_AGAIN's spec does every time, which is why the property was exercised around rather than tested); IN 0 is area 0 literally, no magic zero. NOT ASSERTED, stated rather than implied: refusal WORDING (markers are field-value comparisons only, FIELDMGR_APPEND doctrine) and AGAIN+IN together (needs a memo-free duplicate-open fixture; separate arm). The message catalog's USAGE text does not yet list IN -- the help DBFs belong to the concurrent full-stack document push -- so the refusal path prints the correct syntax inline meanwhile. Self-bootstrapping UDEF/UTGT/UFRE/UBAD in SANDBOX, self-erasing. Explicit-run until soaked, then promote to default.",
        false
    }
}};

std::string trim_copy(std::string s)
{
    const auto is_ws = [](unsigned char c) { return std::isspace(c) != 0; };
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

std::string upper_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

// Mirrors upper_copy; used by REGRESSION FIND for case-insensitive matching.
std::string lower_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

const RegressionSpec* find_regression_spec(const std::string& token)
{
    const std::string key = upper_copy(trim_copy(token));
    for (const auto& spec : kRegressionSpecs) {
        if (key == spec.name) return &spec;
    }
    return nullptr;
}

// Normalize a spec's script path separators for the host filesystem.
//
// kRegressionSpecs stores subdirectory paths with Windows backslashes
// ("canaries\\x64_matrix_metrics_boundary_canary.dts"). On Windows that is a
// path separator; on Linux it is an ordinary filename character, so the whole
// string is treated as one impossible filename and the script is never found.
//
// Measured 2026-07-30 on WSL: 22 of 32 specs carry backslash paths, including
// 5 of the 8 DEFAULT-suite entries. REGRESSION ALL therefore ran 3 of 8 default
// suites and reported the rest as "script not found" WITHOUT failing the run --
// a green-looking Linux regression pass missing five eighths of its default
// coverage. The engine is cross-platform; the harness quietly was not.
//
// Fixing it here rather than editing 22 string literals keeps the specs readable
// in their authored form and makes any future backslash entry work too. '/' is
// accepted on Windows as well, so this is safe in both directions.
static std::string normalize_script_separators(const std::string& raw)
{
    std::string out = raw;
    for (char& c : out) {
        if (c == '\\') c = '/';
    }
    return out;
}

std::filesystem::path resolve_regression_script_path(const RegressionSpec& spec)
{
    namespace fs = std::filesystem;

    const std::string script = normalize_script_separators(spec.script);
    const fs::path raw(script);
    if (raw.is_absolute()) return raw.lexically_normal();

    try {
        const fs::path scripts_root = dottalk::paths::get_slot(dottalk::paths::Slot::SCRIPTS);
        if (!scripts_root.empty()) {
            const fs::path rooted = (scripts_root / raw).lexically_normal();
            if (fs::exists(rooted) && fs::is_regular_file(rooted)) {
                return fs::weakly_canonical(rooted);
            }
            return rooted;
        }
    } catch (...) {
    }

    return shell_resolve_script_path(script);
}

void print_regression_usage()
{
    std::cout
        << "Usage:\n"
        << "  REGRESSION USAGE\n"
        << "  REGRESSION LIST\n"
        << "  REGRESSION FIND <words...>       (search names/scripts/summaries)\n"
        << "  REGRESSION SHOW <name>\n"
        << "  REGRESSION RUN <name>\n"
        << "  REGRESSION <name>\n"
        << "  REGRESSION ALL\n"
        << "Notes:\n"
        << "  - REGRESSION is a curated launcher over DOTSCRIPT.\n"
        << "  - Scripts are expected to bootstrap their own environment.\n"
        << "  - LIST shows curated stable entrypoints rather than every historical script.\n"
        << "  - FIND is the question-to-spec bridge: LIST and SHOW both assume you\n"
        << "    already know the NAME. All terms must match. THE SPEC IS THE HOW-TO --\n"
        << "    read the script for worked usage, or RUN it to watch it work.\n"
        << "  - ALL runs the curated default suite in declared order.\n"
        << "  - HARVEST is the top-layer shakedown for newly promoted surfaces.\n"
        << "  - LANGUAGE proves es/fr/de/it USAGE rendering across the localized command surface.\n";
}

void print_regression_list()
{
    std::cout << "Curated regressions:\n";
    for (const auto& spec : kRegressionSpecs) {
        std::cout << "  " << spec.name;
        if (spec.in_default_suite) std::cout << "  [default]";
        std::cout << "\n"
                  << "    " << spec.summary << "\n"
                  << "    " << spec.script << "\n";
    }
}

void print_regression_show(const RegressionSpec& spec)
{
    const std::filesystem::path resolved = resolve_regression_script_path(spec);

    std::cout << "REGRESSION: " << spec.name << "\n"
              << "  Summary : " << spec.summary << "\n"
              << "  Script  : " << spec.script << "\n"
              << "  Resolved: " << resolved.string() << "\n"
              << "  Default : " << (spec.in_default_suite ? "yes" : "no") << "\n";
}

// REGRESSION FIND <words> -- the question-to-spec bridge (owner ruling
// 2026-08-12: "the regression tests are also how-tos").
//
// The specs ARE the documentation. They are the only documentation in this
// tree that cannot drift silently, because a stale one goes RED -- whereas on
// the day this was written, three separate prose surfaces describing WORKSPACE
// were found stale at once (the @dottalk.usage block, the runtime USAGE text,
// and a hand-written operations doc). So FIND deliberately adds NO new prose:
// it searches the summaries that already exist beside the specs and are
// already printed by LIST. The FAQ content IS the spec corpus.
//
// What it fixes: LIST and SHOW both assume you already know the NAME. Nobody
// arrives knowing to type WORKSPACE_MINIDB when the question is "how do I put
// a database inside a memo". FIND closes exactly that gap and nothing else.
//
// Every term must match (AND, not OR) -- with 44 rich summaries a single
// common word matches almost everything, which is not an answer.
void print_regression_find(const std::string& terms_raw)
{
    std::vector<std::string> terms;
    {
        std::istringstream ts(lower_copy(trim_copy(terms_raw)));
        std::string t;
        while (ts >> t) terms.push_back(t);
    }
    if (terms.empty()) {
        std::cout << "REGRESSION FIND: give one or more words to search for.\n"
                     "  Searches regression NAMES, script filenames and summaries.\n"
                     "  Example: REGRESSION FIND memo ram\n";
        return;
    }

    std::size_t hits = 0;
    for (const auto& spec : kRegressionSpecs) {
        const std::string hay =
            lower_copy(std::string(spec.name) + " " + spec.script + " " + spec.summary);

        bool all = true;
        for (const auto& t : terms) {
            if (hay.find(t) == std::string::npos) { all = false; break; }
        }
        if (!all) continue;

        ++hits;
        std::cout << "  " << spec.name << "\n"
                  << "    script : " << spec.script << "\n"
                  << "    run    : REGRESSION RUN " << spec.name << "\n"
                  << "    detail : REGRESSION SHOW " << spec.name << "\n";
    }

    if (hits == 0) {
        std::cout << "REGRESSION FIND: no regression matches all of those terms.\n"
                     "  Try fewer or broader words, or REGRESSION LIST to browse.\n";
        return;
    }
    std::cout << "REGRESSION FIND: " << hits << " match(es). The SCRIPT is the how-to --\n"
                 "  read it for worked usage, or REGRESSION RUN it to watch it work.\n";
}

void run_regression_script(DbArea& area, const RegressionSpec& spec)
{
    const std::filesystem::path resolved = resolve_regression_script_path(spec);

    std::cout << "REGRESSION: running " << spec.name << "\n"
              << "  Script: " << spec.script << "\n"
              << "  Resolved: " << resolved.string() << "\n";

    std::ostringstream dotscript_line;
    dotscript_line << '"' << resolved.string() << '"';
    std::istringstream dotscript_args(dotscript_line.str());
    cmd_DOTSCRIPT(area, dotscript_args);
}

void run_regression_default_suite(DbArea& area)
{
    for (const auto& spec : kRegressionSpecs) {
        if (!spec.in_default_suite) continue;
        run_regression_script(area, spec);
    }
}

} // namespace

void cmd_REGRESSION(DbArea& area, std::istringstream& in)
{
    std::string arg1;
    if (!(in >> arg1)) {
        print_regression_usage();
        return;
    }

    const std::string op = upper_copy(arg1);

    if (op == "USAGE" || op == "HELP" || op == "?") {
        print_regression_usage();
        return;
    }

    if (op == "LIST") {
        print_regression_list();
        return;
    }

    if (op == "ALL") {
        run_regression_default_suite(area);
        return;
    }

    if (op == "FIND" || op == "SEARCH") {
        std::string rest;
        std::getline(in, rest);
        print_regression_find(rest);
        return;
    }

    if (op == "SHOW" || op == "RUN") {
        std::string name;
        if (!(in >> name)) {
            std::cout << "REGRESSION: missing regression name.\n";
            print_regression_usage();
            return;
        }
        const RegressionSpec* spec = find_regression_spec(name);
        if (!spec) {
            std::cout << "REGRESSION: unknown regression '" << name << "'.\n";
            print_regression_list();
            return;
        }
        if (op == "SHOW") {
            print_regression_show(*spec);
        } else {
            run_regression_script(area, *spec);
        }
        return;
    }

    if (const RegressionSpec* spec = find_regression_spec(op)) {
        run_regression_script(area, *spec);
        return;
    }

    std::cout << "REGRESSION: unknown option or regression '" << arg1 << "'.\n";
    print_regression_list();
}
