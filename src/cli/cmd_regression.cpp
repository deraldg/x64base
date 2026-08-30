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

    // AIF-078 L2. TRUE means this spec MINTS ROWS INTO THE WORKSPACE CATALOG,
    // so it runs with the WORKSPACES slot redirected at a per-run scratch root
    // and leaves production untouched.
    //
    // It is the FIFTH member, and it CARRIES A DEFAULT, on purpose. Both
    // matter and the second was learned the hard way: aggregate initialisation
    // does value-initialise a member no initialiser reaches, so the other 55
    // entries did not have to be edited -- but WITHOUT the '= false' that is
    // 55 hits of -Wmissing-field-initializers under -Wextra, measured. A
    // member with a default initialiser is exempt, the struct stays an
    // aggregate, and the array stays constexpr.
    //
    // The point of not spelling it 59 times is not typing: it is that an entry
    // which says nothing says FALSE, which is the safe answer, and 55 hand-
    // written falses would have been 55 chances to write the wrong one.
    //
    // CORRECTED 2026-08-28, MEASURED. "Silence says FALSE, which is the safe
    // answer" was true of the DEFAULT SUITE and false of this flag. FALSE here
    // means "run this spec against the PRODUCTION catalog, unbracketed", so
    // silence is the UNSAFE answer for any spec that mints -- and ten did.
    // The flag was set on the four default-suite minters, because that is what
    // plan condition 2 needed, and the other ten were never read: the flag is
    // a property of the SPEC (this comment says so above), applied only to the
    // suite. An explicit REGRESSION RUN goes through run_regression_script too
    // and would have been bracketed had the flag been right.
    //
    // AUDIT: all 59 scripts scanned for the THREE minting verbs. The third is
    // the one a reader misses -- a first pass counting only NEW and SAVE
    // reported eight, and RELWSNAME came back zero while its own summary says
    // it leaves two rows per run:
    //
    //     WORKSPACE NEW <name>                 births a row
    //     WORKSPACE SAVE <name> [MEMO ...]     appends to the name's chain
    //     WORKSPACE OPEN <dbf> AS <name>       births a row (R128 + D10.1)
    //
    // Fourteen specs minted when this was written; all fourteen carried the
    // flag. XWSREL made it FIFTEEN on 2026-08-30 -- it declares two workspaces
    // and every WORKSPACE NEW writes a birth row. No spec outside the workspace
    // family mints, so the family filter was not hiding any.
    // NOT AUDITED, stated rather than implied: a script that mints through a
    // script it CALLS. The scan reads each registered file directly.
    bool mints_catalog = false;
};

// SIZE IS HAND-MAINTAINED. Adding a row without bumping this count is a hard
// compile error ("too many initializers"), which is the safe failure -- but it
// is a recurring papercut: it happened when CNXLIVE was added on 2026-07-31.
// Bump it when you add a regression.
constexpr std::array<RegressionSpec, 64> kRegressionSpecs{{
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
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO)
    },
    {
        "WORKSPACE_V3",
        "workspace_v3_selflocate.dts",
        "DTSHEMA 3 step 1 (owner-chartered 2026-08-11, promoted final test, runtime-proven same day, build 14:47:06): version 3 is v2 plus declarative lines -- FLAVOR (measured from the open areas at save time, never declared: versionByte 0x64/V128=X64, 0x30-32=VFP, V32=X32, disagreement=MIXED) and DBFROOT/IDXROOT/LMDBROOT (owner suggestion: the posture stores its own dbf/index/lmdb locations; LMDBROOT is recorded-not-applied, disk-only application chartered). v3 is opt-in per save (trailing V3 keyword, combinable with MEMO in either order); v2 remains the default so every proven producer and consumer is untouched -- the owner's no-blowing-up-2 rule, enforced by pairing this with WORKSPACE_MEMO green on the same build. The proof deliberately BREAKS the environment (SETPATH to the default roots) before the v3 load; restoration of all 13 MCC areas plus a readable STUDENTS row (V3_T1) proves the payload's roots -- not the environment -- resolved the tables, because the loader re-points its resolution roots at the payload's DBFROOT/IDXROOT lines for that load only (global SETPATH never mutated). Self-locating postures end the env-first fragility that made every workspace script SETPATH before LOAD. Writes catalog rows by design (append-history; reruns supersede). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO V3)
    },
    {
        "WORKSPACE_RAM",
        "workspace_ram_hydrate.dts",
        "Memo -> RAM hydration (owner lane step 2, promoted final test, runtime-proven 2026-08-11 build 14:59:07): WORKSPACE LOAD <name> MEMO RAM copies the posture's tables + native CDX files from their DISK homes into the mounted RAM VFS and loads with roots re-pointed at RAM (the DTSHEMA 3 self-location mechanism reused as the hydration vehicle). The copy goes through xbase::ramfs streams, NEVER std::filesystem -- the VFS is in-process and an OS copy would land on real disk while claiming RAM (a false hydration). LMDB is not hydrated: owner rule 'lmdb only for disks', grounded in ramfs.hpp's own contract (LMDB must mmap a real OS file). First measure: 24 file(s), 92139 B in 94.2 ms for the 13-table MCC posture, VDISK census agreeing byte-for-byte (92139 B / 24 files) -- an independent cross-check of the hydration counter. HYD_T1 asserts a STUDENTS row reads from the RAM-resident copy. Index attach in RAM, measured 2026-08-11 (ENROLL, hydrated .cdx): the LMDB-backed route fails ('SET ORDER: failed.' -- no LMDB in RAM, by design) and the native-CDX fallback then attaches (SET ORDER: CDX TAG 'SID'); attach is proven, ordered-traversal-by-value assertion is a chartered follow-up. Environment note: the source-authoring leg MUST run under DO x64 -- without the LMDB slot, LOAD attaches zero CDX orders and the posture records index=none (measured: the 13-vs-24 hydrated-file variance). VDISK UNMOUNT at the end IS the dismiss exit of the chartered two-exit close (save-state or dismiss); the save-state exit is the lane's next step. Memo-sidecar hydration chartered with the Part B MCC regeneration (no MCC table carries a memo field yet). Self-contained: authors its own v3 source posture (ram_hydrate_src) from mcc_x64. Writes catalog rows + mutates only the RAM VFS (self-erasing on unmount). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO V3)
    },
    {
        "WORKSPACE_SESSION",
        "workspace_session_state.dts",
        "v3 session-state capture (owner requirement 2026-08-11 'we need the cursor states and refresh relations'; promoted final test, runtime-proven same day, build 15:22:32, FIRST TRY): a v3 save emits CURSOR <area> <physical-recno> per open area plus CURRENT <area>; the v3 loader applies them after AREA/REL restoration, the saved selection outranks normalization, and the final refresh slaves children to the RESTORED parents -- so a workspace save is now a complete session snapshot: shape, index attachments, keys, cursors, selection, and refresh state. PHYSICAL recno is the recorded anchor per the GPS prior art (owner pointer: see cmd_gps.cpp -- logical row is derived from physical under the active order, so physical is what restores exactly); GPS is the post-restore verifier. Old loaders skip the lines (tolerate-unknown, the KEY precedent) -- v2 coexistence preserved. Proof: Sales_Orders driven to BOTTOM (SO 6) with child slaved, session saved (9792 B = posture + 43 CURSOR lines + CURRENT), full teardown, reload -- '(+ 43 cursor(s))', GPS Area 21 Physical Recno 6 / Logical Row 6, SS_T1 parent at SO 6 not row 1, SS_T2 child re-slaved to Recno 11 through the load's own refresh. Writes catalog rows (append-history; reruns supersede). Requires workspaces/cascade_all.dtschema + the cascade_erp bundle. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO V3)
    },
    {
        "WORKSPACE_MINIDB",
        "workspace_minidb.dts",
        "Memo-resident mini-database (AIF-070's chartered destination LANDED, owner 'do it' 2026-08-11; promoted final test, runtime-proven same day build 18:35:35 FIRST TRY): WORKSPACE SAVE <name> MEMO MINIDB writes a MINIDB 1 container -- the self-locating v3 posture PLUS every open table's bytes and every attached native index's bytes, length-prefixed and binary-safe (the memo store's payload-agnosticism, zoo-proven on embedded NULs, is what makes DBF/CDX bytes legal cargo). WORKSPACE LOAD <name> MEMO RAM detects the container and hydrates FROM THE PAYLOAD: memo -> RAM VFS, ZERO disk reads; the carried posture then stands areas up re-pointed at RAM. Reads are residence-aware (RAM-resident sources come from ramfs), so a RAM session can save its whole working set into a memo -- the owner's save-the-state vision. Plain MEMO load refuses a MINIDB payload with the hydration instruction rather than half-loading. First measure: mcc_db = 94200 B container (92139 B tables+indexes, 1443 B posture), oracle byte-compare OK on the WHOLE container; hydration onto a clean RAM disk 65.5 ms -- FASTER than disk-sourced hydration (71-94 ms) because it is memory to memory; STUDENTS row read and ENROLL CDX attached from memo-carried bytes (DB_T1/DB_T2). The catalog row records FMT='MINIDB 1'. What this makes true: a whole small database -- data, indexes, posture, session state -- lives inside one memo field of another database, versioned by the supersede chain, attributed, oracle-verified. Memo-sidecar carriage LANDED 2026-08-12 (AIF-108 [SIDECAR] unblock): the container now also carries each open area's attached memo sidecar -- the backend names its own file (IMemoBackend::path(), flushed before capture), no extension guessing -- and hydration lands sidecars on the REAL filesystem under the mount dir, because the DTX layer bypasses the ramfs (bypass-ledger member 1) and would never see a VFS-resident sidecar; the disk landing is the measured status quo made deliberate. Act-2 proof (DB_T3/DB_T4) is residue-hardened: the live sidecar is POISONED after the container is saved, so a green can only come from container bytes (hydration truncate-overwrites residue); DB_T4 proves post-hydration writability. Still chartered: the writeback cycle (RAM -> disk commit), LMDB carriage (out of ramfs scope by contract), ramfs memo-store coverage (which would collapse the sidecar disk landing into the VFS). Writes catalog rows; mutates the RAM VFS plus one real-disk sidecar residue (MDMEMO.dtx under data/ram, truncated by the next run). Requires workspaces/mcc_x64.dtschema + the x64 MCC tables. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO MINIDB x2)
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
        "THE FIX IS THE ORDERING, not the wording: the old loader called workspace_close_all() BEFORE discovering it could not "
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
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (SAVE <name> MEMO V3 x2)
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
        true
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
        "WORKSPACE CLOSE is SCOPED to a workspace (AIF-078 stage 3, owner-directed 2026-08-22: 'close_all needs to be SCOPED to a specific workspace instead of 0-max_areas. workspaces have to know the group of areas that belong to them'). Until stage 3 the close ran for (area0 = 0; area0 < MAX_AREA; ++area0) and was correct only because exactly one workspace had ever existed; stage 2 built the membership group (14 tables opened -> 14 members -> 0 after close, measured 2026-08-22) and this is the first spec that can tell the two implementations apart. WS_T1 IS THAT DISCRIMINATOR: closing a nested workspace must leave DEFAULT's sentinel readable, which the old sweep could not do -- delete the scoping and exactly one line reds. The cost argument rides along and is not secondary: MAX_AREA is 512 for testing and the owner has stated the real ceiling is not 512 ('can you imagine how long it would take to give you a dotscript results of a 10 trillion max_area pass'), so an O(MAX_AREA) close does not survive that sentence while an O(members) close does not care. SET RECURSION ON|OFF is proven by WS_T2 and nowhere else -- owner ruling 'even with OFF we still allow multiple workspaces, just parallel', so the flag gates whether an operation DESCENDS, not whether nesting may exist; same script, same shape, one flag flipped, and the nested workspace's table is still readable afterward. WS_T4 proves CLOSE ALL reached the FILESYSTEM and not just the bookkeeping, by reopening and reading. WHAT IT DELIBERATELY DOES NOT ASSERT, stated rather than implied: that a recursively-closed workspace is EMPTY. USE_AGAIN established over three cuts that NO MARKER IN THIS LANGUAGE CAN ASSERT AN AREA IS EMPTY -- the marker evaluator binds a null area unless the area is OPEN (rhs_eval.cpp:969), which is the very thing under assertion, and an errored marker PRINTS NOTHING rather than going red, so a green count still reads full while a claim has silently left the suite. The recursive close is therefore proven by CONTRAST (WS_T2 under OFF against its absence under ON) plus the member counts in the two WORKSPACE REGISTRY blocks, read from the transcript -- external measurement, the IDXDIFF precedent. Every marker is a FIELD-VALUE comparison per the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. Two guards ride the close path in the engine and both ANNOUNCE rather than returning silently, which is the direct lesson of the relation depth cap (set_relations.cpp, hardcoded 24, twice, silent): a cycle in the workspace tree prints, and the depth cap prints what it did not close. Self-bootstrapping WSDEF/WSPAR/WSCHI in SANDBOX, self-erasing; leaves two workspaces declared and restores SET RECURSION ON. CORRECTED 2026-08-23 (AIF-078 D10.1, predicted in D10 sec 6 before the code landed): this line used to read 'two RUNTIME-ONLY workspaces declared (they hold no areas and do not survive a restart)', and the second half is now false -- WORKSPACE NEW writes a BIRTH ROW to the workspace catalog, because a workspace is born durable, so these two DO survive a restart as catalog rows. They still hold no areas. Its teardown now retires them: WORKSPACE DESTROY WSCHILD then WSPARENT -- child first, because DESTROY refuses a workspace that still has nested workspaces rather than cascading. Same principle as restoring SET RECURSION ON at the end, and for the same reason ERRORSTOP is the cautionary precedent: a spec that leaves residue poisons everything downstream of it, and rows accumulate more quietly than a flag does. Explicit-run until soaked, then promote to default. PROMOTED to the default suite 2026-08-23, WITH ITS COST STATED. Since D10.1 every WORKSPACE NEW writes a BIRTH ROW, and D10.3 retirement supersedes rather than deletes, so this spec adds catalog rows to WORKSPACES.dbf on EVERY run and a default-suite spec runs every time. Measured 2026-08-23: the catalog holds 143 rows, none deleted-flagged, 28 of them workspace-spec residue. Its teardown still retires what it declared, which is what keeps the NAMES free for the next run -- the rows are history by design (D10.3) and the growth is the price of keeping it. Named here so a future reader finds a decision rather than a surprise. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. MEASURED ON THE 2026-08-29 PROMOTING RUN: this spec's rows went to data/tmp/wscat_run_79, 2 of them, and the L3 isolation arm read the PRODUCTION catalog at 264 rows BOTH BEFORE AND AFTER the whole suite. THE MINT COUNT DID NOT CHANGE AND WAS NEVER WRONG -- what changed is WHERE IT LANDS, and that is the whole correction. The four bracketed default-suite specs still mint exactly TEN rows between them (WORKSPACE_SCOPE 2, WSMULTI 3, WSLADDER 3, RELSCOPE2 2), the same ten the L2 comment in this file measured as 252 -> 262 on 2026-08-28 -- so the per-spec numbers corroborate rather than contradict. What is void is every projection built on top of them: a row count per run cannot be multiplied into megabytes of a durable catalog that is not being written. The cost is a throwaway directory under the gitignored TMP slot. MWXSHAKE joined the suite the same day at 16 rows, so the suite now mints 26 per run and the production total still did not move. So 'the growth is the price of keeping it' names a price this suite has STOPPED PAYING.",
        true,
        true  // AIF-078 L2: mints catalog rows -- bracket it
    },
    {
        "USE_ARGS",
        "use_argument_validation.dts",
        "USE refuses arguments it does not understand, and IN <n> places (AIF-121, 2026-08-22). USE parsed its tail with THREE independent NON-CONSUMING scans -- contains_noindex, contains_again, parse_alias_clause -- each saving the stream position, sweeping for its own keyword, and rewinding. Nothing ever enumerated the tail, so NO TOKEN WAS EVER UNACCOUNTED FOR: unknown arguments were not ignored by oversight, nothing was in a position to notice them. MEASURED at baada444: `USE dbf\\x64\\students` then `USE dbf\\x32\\students IN 1` printed two 'Opened' lines, WORKSPACE REGISTRY reported members 1, and AREA showed slot 0 holding the x32 table -- the second open replaced the first and said NOTHING. `IN <n>` is FoxPro-standard and documented in this tree twice (command_argchk.cpp:47-48, printed in EVERY REGRESSION ALL run, and fox_standard_catalog.cpp:78); it was swallowed, so the house's own CMDREL recipe died on 'No table is currently open.' Implementing the clause makes both doc sites TRUE rather than correcting them down to a limitation. U_T1 IS THE DISCRIMINATOR and asserts two things in one read: after `USE utgt IN 3` it reads MARK WITHOUT selecting, so a green proves the current area is still 0 (IN does not move you -- the FoxPro contract) AND still holds its occupant; under the old parser IN 3 was dropped and utgt opened over it, reding both at once. U_T4 IS THE CONTIGUITY ARM and it MOVED when the allocator was scoped on owner ruling: DEFAULT holds areas 0 and 3, a global lowest-free sweep answers 1, and the workspace-scoped allocator answers 4 -- the slot after this workspace's highest member -- because a workspace's areas stay contiguous and a global sweep can drop an area inside a NEIGHBOUR'S run once two workspaces exist. If U_T4 ever reads 1 again, IN FREE has gone back to workspace-blind. U_T5 is the gate arm and asks the answerable question (did the KNOWN OCCUPANT SURVIVE) rather than asserting a refusal, per USE_AGAIN's finding that no marker in this language can assert an area is empty and an errored marker prints nothing rather than going red. U_T7 covers the digits-only parse: std::stoll would read '3junk' as 3, the same longest-valid-prefix trap that let AIF-116 read pid=16,984 as 16. Owner rulings carried: IN FREE not IN NEXT (NEXT implies forward adjacency the allocator does not keep); AGAIN and IN compose with NO interaction rule because AGAIN carries no placement opinion (cmd_use.cpp:743, it lands in the current area -- so IN is the half AGAIN shipped without, and AGAIN is destructive today unless the caller SELECTs a free area first, which USE_AGAIN's spec does every time, which is why the property was exercised around rather than tested); IN 0 is area 0 literally, no magic zero. NOT ASSERTED, stated rather than implied: refusal WORDING (markers are field-value comparisons only, FIELDMGR_APPEND doctrine) and AGAIN+IN together (needs a memo-free duplicate-open fixture; separate arm). The message catalog's USAGE text does not yet list IN -- the help DBFs belong to the concurrent full-stack document push -- so the refusal path prints the correct syntax inline meanwhile. Self-bootstrapping UDEF/UTGT/UFRE/UBAD in SANDBOX, self-erasing. VERIFIED IN-SUITE 2026-08-23: promoted, then run inside REGRESSION ALL. This spec inherited 14 open areas from the spec before it, closed them in its own opening WORKSPACE CLOSE, and built its fixture from a clean slate -- order-independence demonstrated rather than assumed, which is what promotion actually requires. Explicit-run until soaked, then promote to default. PROMOTED to the default suite 2026-08-23. The soak was the AIF-078 slot-lane step 1 lift, which MOVED the code this spec covers -- find_free_area_for_workspace left cmd_use.cpp for workarea_util and took its engine and membership table as arguments -- and both arms read green afterward. THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, not the soak alone: REGRESSION ALL CANNOT REACH IN FREE. A grep of the whole .dts corpus finds the phrase in exactly two files, this one and the other of this pair, and both were explicit-run -- so a change to the free-slot allocator could pass the entire default suite and say nothing about the policy. That is what happened on 2026-08-23: ALL ran ten specs green over a commit that rewrote the allocator, and the allocator was not exercised once. U_T4 read engine area 4 after the lift -- DEFAULT holding areas 0 and 3, lowest free 1 -- so the workspace-scoped placement survived the move. If it ever reads 1 again, IN FREE has gone back to workspace-blind.",
        true
    },
    {
        "NAME_AMBIG",
        "rel_name_ambiguity_regression.dts",
        "NAME AMBIGUITY: the collision is already PREVENTED, and the ledger that measures it reads zero for a good reason (AIF-120 I1.3a, 2026-08-22). Two resolvers answered 'which open area is called X' and disagreed -- find_open_area_by_name_ci (workarea_util.cpp, 21 call sites) returned the FIRST match, the lowest engine slot, while build_area_by_up_name (set_relations.cpp, the recursive REL LIST tree builder) assigned unconditionally and so returned the LAST. That divergence is closed: the local map is deleted and both are built on one primitive (find_open_areas_by_name_ci, every match ascending by slot), agreeing BY CONSTRUCTION. THE SPEC'S FIRST CUT COULD NOT BUILD ITS OWN FIXTURE, and that is the finding it now carries. Two `USE ... ALIAS NAMDUP` calls were expected to put one name on two areas; the second was REFUSED. cmd_use.cpp:944-972 resolves the name BEFORE touching the target area -- an explicit alias already held is refused, a name derived from the file stem that is already held is auto-renamed to <stem>2 and ANNOUNCED -- and its own comment names this case: 'the ordinary AGAIN case, and also two same-named files from different directories.' So R112 sec 3's measurement (USE ... ALIAS assigns the logical name with NO uniqueness check) is STALE: true at 8aca9ef1b, false since USE_AGAIN's alias arm landed 2026-08-12, and R112 sec 6a scheduled as future work a within-workspace PREVENT half that a different lane had already shipped. CONSEQUENCE, and the reason this spec exists: two open areas in one workspace CANNOT share a logical name, so the ambiguity ledger is STRUCTURALLY ZERO -- not untested, unreachable -- until two workspaces can be open at once and cross-workspace names may repeat. R112 sec 6a predicted exactly this ('would record zero for the wrong reason, and a zero that means nothing was tested is exactly the false green trap-4 is about') and the instrument built under that ruling walked into it. The ledger line is therefore a TRIPWIRE for AIF-078 stage 4, not a migration counter, and it prints even at zero so that 'no collision occurred' and 'nothing is instrumented' cannot look alike (AIF-118). WHAT THE MARKERS PROVE is the two-directories case, which nothing else covers: USE_AGAIN's alias arms cover the same file opened twice and the explicit-alias refusal, never R112's actual measurement of twelve basenames shared across dbf/x64, dbf/x32 and dbf/vfp. This opens two of them read-only. N_T1 parks the first instance on record 2 while the second sits at record 1, telling two copies of the same data apart BY FIELD VALUE, and proves `SELECT students` still reaches the first holder -- but it would pass under first-wins too, so it is not the discriminator. N_T2 IS: `SELECT students2` must reach the second instance, and with no rename there is no such name, SELECT fails, the current area stays parked on Martin, and the marker READS RED rather than vanishing -- arranged that way because an errored marker prints nothing rather than going red (USE_AGAIN's finding). Read-only: no fixture is created and nothing is erased. Explicit-run until soaked, then promote to default.",
        true
    },
    {
        "WSMULTI",
        "workspace_multi_regression.dts",
        "MULTIPLE WORKSPACES: siblings, nesting, and one FILE open in two of them (AIF-078 stage 3/4 evidence; registered 2026-08-22 under D8 sec 7 -- it existed, was mutation tested, and was UNREACHABLE BY NAME because nothing listed it here). Why it exists given workspace_scope_regression already passes: that file proves a scoped close spares DEFAULT, and DEFAULT is the ancestor of everything, so an implementation that closed 'everything except area 0' would pass it. SIBLINGS are the discriminator between 'scoped to a workspace' and 'scoped away from the root'. WSM_T1 is that arm -- WSALPHA and WSBETA are peers, WSALPHA is closed, BETA's sentinel must still read. WSM_T2 IS THE ARM THAT MATTERS MOST and it is about ONE file, not two: MWSHARE.DBF is opened in WSALPHA and again in WSBETA, so the two workspaces disagree about who owns a single handle; close WSALPHA and BETA must still read MWSHARE. If close releases by FILE rather than by workspace MEMBERSHIP, BETA loses a table it never closed -- a failure invisible in any test where each workspace holds distinct files. Every assertion is a POSITIVE READ of a sentinel that must survive: nothing here claims an area is EMPTY, because no marker in this language can (the evaluator binds a null area unless the area is OPEN, and an ERRORED MARKER PRINTS NOTHING RATHER THAN GOING RED, so a suite can lose a claim silently and still report a full green). Absence is proven only by contrast. WSM_G0..G5 are setup guards and WSM_G4 -- share actually open in ALPHA -- is the one that caught this file's own earlier FALSE GREEN, where WSM_T2 asserted a file survived that the arm had never opened; if a guard reds, treat every WSM_T* as UNPROVEN rather than passing. MUTATION TESTED 2026-08-22: WSM_T1 and WSM_T2 were both mutated to expect 'MUTANT' and the suite re-run, so the arms are demonstrated able to red and independent of one another. Prefix is WSM_ rather than WS_ so a combined run can tell these apart from the scope regression. NOTE for AIF-120 R112: this script does NOT drive the name-ambiguity ledger non-zero -- cmd_use.cpp auto-renames a duplicate stem, so it yields MWSHARE/MWSHARE2 rather than a collision, and R112's measured-zero gate needs its own fixture. Self-bootstrapping sentinels; teardown retires WSGAMMA, WSALPHA and WSBETA (AIF-078 D10.3, 2026-08-23 -- since D10.1 each WORKSPACE NEW writes a birth row, so without this the spec would leave three permanent catalog rows behind per run; the nested WSGAMMA goes first because DESTROY refuses a parent that still has children). Explicit-run until soaked, then promote to default. PROMOTED to the default suite 2026-08-23, WITH ITS COST STATED. Since D10.1 every WORKSPACE NEW writes a BIRTH ROW, and D10.3 retirement supersedes rather than deletes, so this spec adds catalog rows to WORKSPACES.dbf on EVERY run and a default-suite spec runs every time. Measured 2026-08-23: the catalog holds 143 rows, none deleted-flagged, 28 of them workspace-spec residue. Its teardown still retires what it declared, which is what keeps the NAMES free for the next run -- the rows are history by design (D10.3) and the growth is the price of keeping it. Named here so a future reader finds a decision rather than a surprise. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. MEASURED ON THE 2026-08-29 PROMOTING RUN: this spec's rows went to data/tmp/wscat_run_80, 3 of them, and the L3 isolation arm read the PRODUCTION catalog at 264 rows BOTH BEFORE AND AFTER the whole suite. THE MINT COUNT DID NOT CHANGE AND WAS NEVER WRONG -- what changed is WHERE IT LANDS, and that is the whole correction. The four bracketed default-suite specs still mint exactly TEN rows between them (WORKSPACE_SCOPE 2, WSMULTI 3, WSLADDER 3, RELSCOPE2 2), the same ten the L2 comment in this file measured as 252 -> 262 on 2026-08-28 -- so the per-spec numbers corroborate rather than contradict. What is void is every projection built on top of them: a row count per run cannot be multiplied into megabytes of a durable catalog that is not being written. The cost is a throwaway directory under the gitignored TMP slot. MWXSHAKE joined the suite the same day at 16 rows, so the suite now mints 26 per run and the production total still did not move. So 'the growth is the price of keeping it' names a price this suite has STOPPED PAYING.",
        true,
        true  // AIF-078 L2: mints catalog rows -- bracket it
    },
    {
        "RELSCAN",
        "rel_scanlimit_honesty_regression.dts",
        "SCAN-LIMIT HONESTY (AIF-074 P1.3 / RDB-06, plus REL SCANLIMIT reach OQ-1). Registered 2026-08-22 under D8 sec 7: the script was authored 2026-07-29 with four documented assertions and was never listed here, so it could not be run by name -- coverage the house had already paid for and could not reach. 'Scan-limit truncation' here means RESULT-SET rows cut off by the relation engine's scan-step cap; it is unrelated to x64base long-name mangling. T1: REL SCANLIMIT reports and sets, a control previously unreachable from the CLI. T2 is the RED path -- with the limit set to 1, REL LIST's match-count scan must warn 'REL: scan limit (1) reached; results may be incomplete.' T3 WAS CLAIMED BY THE SCRIPT HEADER AND DID NOT RUN -- caught 2026-08-22 on the spec's first run by name, which is what registering it bought, and CLOSED 2026-08-28 by doing exactly what that entry prescribed. The header promised 'warning appears ONCE per REL command even with multiple children' while the fixture declared exactly ONE child (REL ADD RSLPAR RSLCHD), folded T3 into T2's comment, and emitted no RELSCAN-T3 block; the latch (note_scan_truncated) was real and simply UNEXERCISED. A second child (RSLCHD2) and its own marked block now exercise it. T1, T2 and T4 are DELIBERATELY UNTOUCHED and still run against a single child, so every assertion already registered against their blocks reads the same output -- the fix is additive, because perturbing a registered assertion to close a different gap is how a suite stops meaning what it says. Registered with the gap named rather than papered over: this summary previously repeated the header's claim, which is the defect the house keeps finding one layer up. T4: with the default limit restored the same REL LIST is warning-free. Read rule, and it is the whole point: the T2 block MUST CONTAIN the warning and the T4 block MUST NOT -- an honest incomplete result announces itself, and a silent truncation reads exactly like a complete answer. Related, recorded 2026-08-22 as NOT FIXED and FIXED 2026-08-28: relations_api::scan_truncated() was declared with the promise 'consumers may poll scan_truncated() to label results as possibly incomplete' and had ZERO pollers -- set internally, cleared by cmd_rel.cpp, read by nobody. It now has three. REL JOIN and REL ENUM restate truncation AT THE RESULT with the limit and the row count, because the latch prints once at the MOMENT of truncation, which lands above the rows a reader then scrolls to. REL LIST says something DIFFERENT on purpose: it reports match COUNTS, and a truncated count is not a short list, it is a WRONG NUMBER in the shape of a right one, so it is told it is reading LOWER BOUNDS (T5). cmd_RELATIONS_LIST also now owns its own latch cycle, because RELATIONS and REL_LIST are registered directly (shell_commands.cpp) and never pass through cmd_REL's per-command clear -- by those names it would have warned about another command's truncation or, already latched, stayed silent about its own. The OK line still prints after a truncated result: suppressing it changes what a script parsing the command sees, which is a ruling and not a cleanup, so the warning is ADDITIVE and this spec's read rule still holds. T6 and T7 cover the neighbouring honesty defect fixed in the same commit: REL ENUM's refusal used to read 'enum_emit_for_current_parent failed', naming WHERE it failed and never WHY, so a correct refusal read as a crash; it now DERIVES the one cause determinable there -- no explicit path plus a child count other than one cannot yield a unique chain -- names the children, and otherwise says it refused WITHOUT inventing a reason. MUTATING, SANDBOX only: throwaway RSLPAR/RSLCHD/RSLCHD2, and the session scan limit is restored to the 500000 default at the end. Explicit-run.",
        false
    },
    {
        "XWSREL",
        "cross_workspace_relation_refusal.dts",
        "AIF-149 REFUSAL HONESTY: the message must say WHERE the area is. add_relation resolves both endpoints through a resolver SCOPED to the current workspace, so an area open in ANOTHER workspace is not refused -- it is INVISIBLE, and until 22991263e the refusal reported invisibility as absence: 'add failed (parent/child not open)' for an area that IS open. NOTHING DECIDED THAT A RELATION MAY NOT CROSS A WORKSPACE. Owner 2026-08-30: 'I don't think we are saying relations can't exist outside of workspace, even nested, I think we mean we haven't developed it yet, or decided whether to leave that gate open.' The FEATURE is PARKED with the gate open (multi-workspace is in HARDENING and crossing is capability); this spec guards the HARDENING half, which is true whichever way the feature lands. T2 IS WHY T1 MEANS ANYTHING: T1 names a table open in the other workspace and its block must contain 'is open in workspace XWSB'; T2 names a table open NOWHERE and its block must contain 'not open' and MUST NOT contain 'is open in workspace'. Collapse the two messages back into one -- the likely edit -- and T2 gains a sentence it must not have. ASSERTED BY TRANSCRIPT, NOT BY FIELD VALUE, and that is a departure stated rather than hidden: relation_workspace_scope.dts asserts by field value 'never by console text' and is right to, but the thing under test HERE IS A REFUSAL and a refusal writes no field. So the RELSCAN idiom applies -- a marked block that MUST CONTAIN a line, and one that MUST NOT. The two field-value guards carry what the arms cannot: G0 proves the fixture, and G1 proves a SAME-workspace ADD still succeeds and slaves, which is the counterweight for making refusals ungated. If G1 reds, every arm below it is UNPROVEN. WHAT IT CANNOT PROVE, NAMED: the defect under the wording defect was that every add-failure path reported through emit_rel_diag, which opens 'if (!g_verbose) return;', and g_verbose defaults to DOTTALK_EXTRA_DIAGNOSTICS -- ON under DOTTALK_PROFILE=DEV, OFF under PROD (CMakeLists.txt:172-177) -- while the caller is a bare 'if (!add_relation(...)) return;' (cmd_relations.cpp:500), so on a PROD build a failing SET RELATION could print NOTHING AT ALL. THIS SPEC RUNS UNDER DEV AND THEREFORE CANNOT TELL THE GATED AND UNGATED BUILDS APART. It discriminates the WORDING; proving the PROD half needs a PROD-profile build, which no run has produced. T3 WAS DECLARED UNVERIFIED IN ADVANCE AND THE FIRST RUN REWROTE IT, which is what declaring it bought. It aims at refresh_from_parent_name's former bare 'if (!child) continue;', now tripping the relation truncation latch. The first draft evicted the child with CLOSE and the block came back EMPTY; measured afterwards rather than guessed, CLOSE calls clear_relations_involving_table (cmd_close.cpp:134, called at :265) which drops EVERY relation the closed table appears in as parent OR child, so the edge was gone before the refresh ran. THE ARM NOW USES 'USE', AND THE DIFFERENCE IS ITSELF THE FINDING: cmd_use.cpp contains no relation handling whatsoever, so there are TWO ways to take a table out of an area and only ONE of them tells the relation store. CLOSE keeps the store consistent; USE leaves an edge naming a table that is no longer open -- the exact state the latch exists to announce, and the only ordinary command sequence that reaches it. RULED THE SAME HOUR, and the ruling is what makes this arm permanent: USE STAYS A CURSOR OPERATION. Owner 2026-08-30, ruling on this asymmetry the hour it was found: 'i argue use needs [no] overcomplicating with relations -- you set your cursor -- use -- and return if you must.' So the two verbs are NOT inconsistent, they are DIFFERENT ACTS. CLOSE retires a table and tidies the store after it. USE re-points an area, and the operator owns what that leaves behind. AND THAT RULING IS WHAT MAKES THE LATCH RIGHT RATHER THAN A STOPGAP. If USE is MEANT to leave an edge naming a table that is no longer open, then that state is legitimate and permanent, and the only defensible treatment is for the refresh to SAY SO when it walks past it. The bare `if (!child) continue;` was not a missing USE fix -- it was silence over a state the language deliberately allows. A spec arm that might not fire is the WSENV blind-arm defect; saying so in advance and reading the first run for the answer is the form that pays. RUNTIME-PROVEN 2026-08-30 on c773f8b7: T3 prints 'relation XWSAP -> XWSAC was NOT refreshed: XWSAC is not open; results may be incomplete.' It prints TWICE and that is expected -- once before the block because SELECT performs its own autorefresh and trips the latch in its own cycle, once inside because REL REFRESH clears the latch at command dispatch and trips it again. The arm is NOT rearranged to hide the first: a spec that tidies its own transcript teaches the next reader that SELECT does not refresh. MUTATING, SANDBOX only: throwaway XWSAP/XWSAC/XWSBC and workspaces XWSA/XWSB, all retired in teardown along with REL CLEAR ALL. Explicit-run until soaked.",
        false,
        true  // WORKSPACE NEW writes birth rows -- bracket it
    },
    {
        "SCRATCHTAB",
        "scratch_sidecar_not_a_table.dts",
        "SCRATCH IS NOT A TABLE (AIF-133, 2026-08-26). SSC_T1 IS THE DISCRIMINATOR AND IT IS PHRASED POSITIVELY ON PURPOSE: it asks whether the table in AREA 0 is the REAL one, not whether the scratch table is absent. A FIELDMGR restructure leaves <stem>.__fldbak.dbf beside the real table; both directory scans in the tree tested the EXTENSION only, so the backup was opened as a work area -- and because the scan SORTS BY FILENAME and '.__fldbak' sorts before '.dbf', it did not tag along at the end, IT TOOK AREA 0 and shifted every area after it. A posture saved from that state records a backup as the active table, a MINIDB save carries its bytes, and WRITEBACK returns them to disk; measured 2026-08-26, STUDENTS.__fldbak.dbf was a 22,425-byte member of a live container, 17 percent of that payload. THE ABSENCE FORM WAS UNAVAILABLE, not merely inelegant: no marker in this language can assert emptiness (USE_AGAIN, three cuts) and an ERRORED marker PRINTS NOTHING rather than going red, so 'the scratch is gone' could be lost silently inside a full green. Asking which table landed in area 0 is answerable, and it is a FIELD comparison rather than a console read -- the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. The two fixtures carry DIFFERENT marks (REAL and BACK) for exactly that reason: if both said REAL the arm would pass on either build. GUARDS: SSC_G0 proves the real table carries REAL, SSC_G1 proves the backup EXISTS and carries BACK. G1 is the load-bearing one -- without it an arm reading REAL cannot separate 'the scratch was correctly skipped' from 'the scratch was never created', and the second is a fixture failure wearing a fix's clothes, which is the WSL_G4/G5 lesson restated. ISOLATED BY CONSTRUCTION: it opens a DIRECTORY, so a stray table from another spec could take area 0 on its own; it therefore creates and scans its own directory under SANDBOX rather than trusting what the shared sandbox contains. VERIFIED AGAINST BOTH BUILDS BEFORE REGISTRATION, which is the only way to know a discriminator discriminates: on the pre-fix binary Area 0 opened SSTAB.__fldbak.dbf, 2 tables, SSC_T1 read .F.; on the post-fix binary Area 0 opened SSTAB.dbf, 1 table, SSC_T1 read .T. -- and BOTH GUARDS READ .T. IN BOTH RUNS, so only the arm moved. Run twice on the fixed build to prove the teardown: the second run starts clean rather than reading the first run's fixture. NOTED IN PASSING AND NOT FIXED: teardown must name the backup in full as SSTAB.__fldbak.dbf, because 'ERASE SSTAB.__fldbak CONFIRM' answers 'Table not found' while the file is sitting there -- the table-token form appends .dbf only when it does not already see an extension, and '.__fldbak' looks like one. ERASE cannot address a name whose second segment resembles an extension: the same root cause as the scan defect, in a different verb, and a third instance of it. Self-bootstrapping, self-erasing, leaves an empty directory. Explicit-run until soaked.",
        false
    },
    {
        "ADDOPEN",
        "workspace_additive_open.dts",
        "WORKSPACE OPEN IS ADDITIVE (R128, owner 2026-08-26: \"open should be additive or it will kill the other workspaces, if a person wants it open by itself then they can close all of the other workspaces first like a sane person\"). WAO_T1 IS THE DISCRIMINATOR and it asks the answerable question rather than asserting an absence: after opening WAOA and then WAOB, does AREA 0 STILL HOLD WAOA'S TABLE. Under the replacing OPEN it holds WAOB's, so the arm reads .F. and goes RED -- it does not merely print nothing, which is the failure mode USE_AGAIN established this language cannot escape when an arm asks whether something is gone. MEASURED BOTH WAYS on 2026-08-26 against two binaries built from the same tree: baseline read T1 .F., T2 .F., T4 .F.; the R128 build read all four .T. WAO_T2 is the placement half -- WAOB landed BESIDE WAOA at area 1 rather than over it, which is what proves the areas came from find_free_area_for_current_workspace and not from the old loop's assumption that it owned slots 0..N-1. That assumption is why removing workspace_close_all() alone would have been WORSE than the defect: the loop closed whatever sat in each slot it wanted, so an additive caller over an unchanged loop would have stomped the low slots, which is precisely where another workspace's areas live. WAO_T3 AND T4 COVER RE-ENTRY, the case R128 sec 4.3 left open and the owner then ruled: a second OPEN of a directory already open RE-ENTERS its workspace and adds only what is not already there. T4 discriminates (baseline .F.); T3 IS GREEN UNDER BOTH IMPLEMENTATIONS AND IS NOT A DISCRIMINATOR -- stated rather than implied, because a reader counting green arms would otherwise credit it with proving something. It is here because a re-entry that disturbed the surviving area would show up nowhere else in this spec. GUARDS WAO_G0/G1/G2 read each fixture ON ITS OWN before any of them is opened as a workspace, and they EARNED THEIR PLACE on 2026-08-26: an edit that added the third fixture put its SET PATH before the second table's CREATE, so WAOT2 was built in the wrong directory. G1 went red on BOTH binaries and correctly marked T2 and T4 unproven, which is a fixture failure caught wearing its own clothes rather than a verb failure's. Without the guards the same edit would have read as a regression in OPEN; without them an arm reading the wrong MARK cannot tell a broken OPEN from a table that never carried the value. Both guards read .T. on BOTH binaries, so the fixture is sound and the red arms are the verb. WAO_T5 IS THE SCOPED-SAVE ARM, the other half of R128 and the half that was a LIVE defect: workspace_save_to_string() swept every MAX_AREA slot with no workspace discriminator, so with two workspaces populated WORKSPACE SAVE <name> wrote the OTHER one's areas into your posture. It is asserted by WHERE THE NEXT AREA LANDS rather than by counting what is absent -- save WAOX while WAOY is also populated, reload, ADD a third table, and slot 1 must read CCC; under the sweep the posture carries both, the reload fills 0 and 1, the ADD lands at 2 and slot 1 reads BBB. IT BUILDS ITS TWO WORKSPACES WITH NEW AND ADD AND NOT WITH OPEN, AND THAT IS THE WHOLE POINT: a first cut used OPEN and read GREEN ON BOTH BINARIES, because under the replacing OPEN the second open closes the first and there is never a second populated workspace to save from. THE ADDITIVE DEFECT WAS MASKING THE SAVE DEFECT -- which is also why the save defect was rarely reached in the field, and it is a reminder that a discriminator has to be checked against the old build and not merely reasoned about. NEW and ADD are untouched by R128 and additive on both builds, so T5 exercises the serializer and nothing else. WHAT THIS SPEC DOES NOT COVER, stated rather than implied: (a) THE CROSS-ROOT COLLISION REFUSAL: two directories whose leaf is the same name cannot share a workspace, and OPEN refuses naming both paths and pointing at AS <name>. That was FOUND BY RUNNING IT -- the first cut decided re-entry on the NAME alone, which answers the same for 'same directory again' and 'a different directory that collides', the AIF-118 shape inside the guard written to prevent an ambiguity -- and it now turns on a session-local origin map. A spec for it needs two directories sharing a leaf under different roots, and the discriminator is WORKSPACE MEMBERSHIP rather than area content (under the bug the foreign table opens into the WRONG workspace at the SAME slot), which REGISTRY reports only as console text; a field-value arm needs a catalog read. Not faked, not claimed. (b) AS <name> WAS UNCOVERED HERE UNTIL R131. On 2026-08-29 the three OPEN lines in this spec gained an explicit `AS`, because R131 withdrew the leaf naming they had been relying on; the SEMANTICS ARE UNCHANGED -- WAOA and WAOB are still two separate workspaces, which is what T1/T2/T4 were measured against on both binaries on 2026-08-26, and only the spelling moved from implicit to typed. So this spec now exercises the AS form incidentally rather than deliberately, and the deliberate coverage of AS is OPENJOIN. RESIDUE: this spec DESTROYs both workspaces it mints, so neither name keeps a live catalog row and a later run mints fresh rather than adopting; the superseded rows remain, which is the history D10.3 exists to keep. Explicit-run until soaked, then promote.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (NEW x2 + SAVE <name> MEMO)
    },
    {
        "PKEYS",
        "workspace_load_posture_keys.dts",
        "A POSTURE RECORDS A KEY, NOT AN ADDRESS (R130, owner 2026-08-27: \"regarding LOAD, no problem, we don't save slots, we allocated them as they are available, do we need a slot provider??\"). PK_T1 AND PK_T2 ARE THE DISCRIMINATORS and they ask the answerable question rather than asserting an absence: after LOADing a posture into a THIRD workspace, do engine slots 0 and 1 STILL HOLD workspace A's tables, still parked where A parked them. workspace_load_from_stream() replayed each recorded AREA number as an ENGINE ADDRESS -- open_into_area(n, ...) calls get_area_0based(n) and A.close() on that exact slot -- so it could only be safe if slot n was free, and workspace_close_all() at cmd_workspace.cpp:2405 was the PRECONDITION that made address replay work. THE CLOSE WAS NOT THE DEFECT. Closing every workspace at once is correct AT SHUTDOWN (owner: \"everybody has database fun until they shutdown their app and all of the workspaces close at one time\"); the defect was LOAD borrowing shutdown's hammer as a precondition. DELETING THE CLOSE ALONE WOULD HAVE BEEN WORSE THAN THE DEFECT, and three of this spec's five arms exist only to prove that: without a recorded-key -> allocated-slot map, the loader allocates past the occupied range and a bare CURSOR 0 still reaches engine slot 0 -- now another workspace's table -- and MOVES ITS CURSOR. AIF-137's shape as a WRITE, on user data, driven by a saved file, and with no instrument at all where AIF-137 at least had one. PK_T3, PK_T4 AND PK_T5 ARE GREEN ON THE PRE-FIX BINARY FOR THE WRONG REASON AND THE SPEC SAYS SO IN ITS OWN TEXT: with the slot space emptied first, the recorded number and the allocated slot coincide by accident, so they discriminate against a NEW implementation whose map is wrong and against nothing else. A green PK_T3 on the old build is not evidence and must not be reported as one. THE FIVE ARMS ARE READ IN THREE WORLDS, not two: TODAY (close_all empties everything, the loaded tables take slots 0 and 1, workspace A is gone), NO MAP (A survives at 0 and 1, the loaded tables allocate to 2 and 3, but CURSOR/CURRENT still address 0 and 1 so A's cursors are DRIVEN and the loaded tables are left at row 1), and R130 (A untouched, loaded tables at 2 and 3 with their recorded cursors restored through the map). Every arm is .F. in the NO MAP world; T1 and T2 are .F. in TODAY as well. MEASURED ON THE PRE-FIX BINARY 2026-08-27 (build 09:20:07, 9e1376e1 dirty), and the prediction was written down before the run: all eight guards .T., PK_T1 .F., PK_T2 .F., PK_T3/T4/T5 .T. The transcript shows the brute close firing inside the LOAD -- \"WORKSPACE: 2 area(s) closed\" and \"REL: cleared all\" -- with PKWSA's areas as its victims. The post-fix reading is recorded in the session closeout, not here. T1 AND T2 CANNOT GO BLANK, AND THAT IS ENGINEERED: an errored marker in this language PRINTS NOTHING rather than going red (USE_AGAIN, three cuts), so an arm that would read a CLOSED area disappears silently instead of failing. Both fixture families therefore use the SAME FIELD NAME (LBL) with DIFFERENT VALUES, so slots 0 and 1 are readable in all three worlds and the comparison is always a real field read -- the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. ADDRESSING IS SLOTS FOR THE SURVIVORS AND NAMES FOR THE TRAVELLERS, AND THE DIFFERENCE FROM RELWSNAME IS DELIBERATE: that spec forbade name addressing because its fixtures shared names by design, so a name could not say which table it read. HERE THE FOUR NAMES ARE UNIQUE, and PK_T3/T4 ask the only question a slot cannot -- wherever the loaded table LANDED, is its cursor where the posture said. A slot-addressed T3 would have to name a slot, and the slot moving is the entire point. GUARDS: PK_G0a..G0d prove each fixture alone before any workspace exists; PK_G1a/G1b prove workspace B landed in slots 0 and 1 BEFORE the save, which is what makes the posture record keys 0 and 1 -- if B landed elsewhere the posture says something else and every arm is meaningless; PK_G2a/G2b prove workspace A occupies 0 and 1 and is parked on the rows the arms expect. IF ANY GUARD READS .F., TREAT EVERY ARM AS UNPROVEN RATHER THAN AS FAILING. WHAT THE FIX COVERS BEYOND THE ARMS, stated because the arms do not reach it: the loader's KEY handler resolved a posture's KEY <table> <field> line through the UNSCOPED find_open_area_by_name_ci and then WROTE through it (unique_reg::set_unique_field / set_primary_field), so under an additive LOAD a posture could stamp a unique-key declaration onto another workspace's same-named table -- AIF-137's shape, third instance, inside the same function. Scoped in the same change and NOT covered by any arm here. ALSO NOT COVERED: WORKSPACE SAVE emits CURRENT from eng->currentArea() with NO scope check while filtering every AREA and CURSOR line through sc.contains(area0), so a scoped save taken while the engine sits in another workspace writes a FOREIGN slot number into the posture. The loader now ignores and REPORTS an unmappable CURRENT rather than guessing, but this spec never produces one. RESIDUE: three workspaces minted and all three destroyed, so no name keeps a live catalog row; the superseded rows remain, which is the history D10.3 exists to keep. The posture pk_posture.dtschema is left in the workspaces root and overwritten each run -- prior art keyregr_sandbox.dtschema. Fixtures self-bootstrap in DBF/SANDBOX/PKA and DBF/SANDBOX/PKB and are erased at the end, leaving two empty directories. Explicit-run until soaked, then promote.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (NEW + OPEN..AS x2 + SAVE <name>)
    },
    {
        "RELWSNAME",
        "relation_parent_workspace_crossing.dts",
        "THE RELATION STORE IS PARTITIONED BY WORKSPACE AND THE RELATION PARENT WAS NOT (AIF-137, 2026-08-27). AIF-078 I1.2 scoped the STORE and relation_workspace_scope.dts proves that half; it CANNOT reach this one, and its own text says why -- it uses DISTINCT table names per workspace (RSAP/RSAC vs RSBP/RSBC) so a name can never collide, which is exactly the case this file supplies. The store was scoped; THE NAMES INSIDE IT WERE NOT. refresh_from_parent_name() took a string and called find_open_area_by_name_ci(), which sweeps every open area and returns the LOWEST engine slot with no workspace filter, so a refresh issued while standing in one workspace resolved its parent AND its child to ANOTHER workspace's areas. FOUND BY RUNNING AN INSTRUMENT, NOT BY READING: R112's ambiguity ledger was built 2026-08-22 and could not fire, R128 made two populated workspaces ordinary on 2026-08-26, and on 2026-08-27 the first reading of it printed 'resolved to area 0 [REL refresh parent]' with the current handle at 3 -- ON THE SECOND WORKSPACE OPEN, before any table name was typed, with REL LIST reporting an EMPTY STORE. IT NEEDED NO SET RELATION TO OCCUR: current_parent_name() falls through to infer_parent_from_workarea() when no override is set, so the unscoped resolution is on the DEFAULT path and not only the shorthand one. The relation-scope spec RECORDED this in 2026-08-23 as 'the next workspace-blind piece of relation state ... should not be found by surprise'; it was not a surprise, it was measured. TWO ARMS IN OPPOSITE DIRECTIONS, BOTH RED BEFORE AND BOTH GREEN AFTER, MEASURED ON TWO BINARIES 2026-08-27. RPC_T1 is the NEGATIVE half and the main discriminator: workspace A's child is parked on a sentinel row and must STILL BE THERE after a refresh issued inside workspace B -- under the defect the refresh drove A's child off it. RPC_T2 is the POSITIVE half: workspace B's own child must have FOLLOWED B's parent -- under the defect B's child was never touched at all and sat where it was parked. BOTH ARMS ARE NEEDED because 'the wrong one moved' and 'the right one did not' are different failures, and a half-fix that stopped touching A without starting to drive B would show T1 green and T2 red. ADDRESSING IS BY ENGINE SLOT AND NEVER BY NAME, AND THAT IS LOAD-BEARING: SELECT <name> is itself unscoped -- the same defect wearing a different verb -- so a name-addressed arm could not say which table it read, and it would silently re-point the day R129 sec 6.2 lands. GUARDS RPC_G0a/G0b prove each fixture on its own before any workspace exists; RPC_G1a/G1b prove the two directories landed in the slots the arms address (these go RED under a REPLACING open, which is the correct reading -- the arrangement would not exist); RPC_G1c proves the sentinel park; RPC_G2 proves the parent is on the key the child must follow, without which the child's destination is undefined. IF ANY GUARD READS .F., TREAT BOTH ARMS AS UNPROVEN RATHER THAN AS FAILING. FIXTURES ARE BUILT, NOT BORROWED, and that was a correction: an attempt to read the shipped dbf/x64 fixtures with a classic-DBF parser reported eight BLANK records, because those files carry version byte 0x64 -- this project's own 64-bit header -- and the extended block was consumed as two bogus field descriptors. An empty result is not a measurement, and an arm built on 'x64's BUILDING is empty' would have been fiction. THE RUN ENUMERATED THE FIX SURFACE THAT READING HAD MISSED: distinct ledger tags showed REL add parent and REL add child crossing as well, so the fix covers ELEVEN sites and not the two the first reading found -- and a grep AFTER scoping the six the spec drives found FIVE MORE on REPORTING paths (REL matchcount parent/child, REL preview child, REL enum parent/child) which are THE COUNT DISCIPLINE and WHICH THIS SPEC DOES NOT COVER; a future edit could unscope any of the five and this suite would stay green. ALSO NOT COVERED AND NOT FIXED: REL LIST ALL resolves through build_open_area_index_ci(), a whole MAP on the same unscoped primitive, so a tree listing can still walk into another workspace. A SECOND FINDING CAME OUT OF THE FIXTURE PHASE AND CORRECTS THIS FILE'S OWN PRIOR TEXT: the ledger fired with 'ws 1 area 0, ws 1 area 2' -- BOTH IN DEFAULT -- because CREATE opens a second same-named table with NO auto-rename, unlike USE. So the claim recorded here that the ledger is 'STRUCTURALLY ZERO -- not untested, unreachable -- until two workspaces can be open at once' is FALSE and has been since before R128. Those two in-workspace hits still print after the fix, deliberately: the scoped resolver drops the cross-workspace hits, which were never ambiguity but this defect, and keeps the in-workspace residue, which is the number R112 sec 6a's measured zero is actually about. Residue: two superseded catalog rows per run (D10.1 mint, D10.3 retirement). Explicit-run until soaked, then promote.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (OPEN..AS x2)
    },
    {
        "WSLADDER",
        "workspace_identity_ladder.dts",
        "WORKSPACE IDENTITY LADDER: a workspace is born durable, and can die durable (AIF-078 D10.1/D10.2/D10.3, 2026-08-23). WSL_T4 IS THE DISCRIMINATOR and it is one line: destroy WSLADR1, create WSLADR1 again, and the second WS_ID must be GREATER than the first. That can only pass if retirement actually reached the catalog -- if WORKSPACE DESTROY silently no-ops, supersedes the wrong row, or writes a flag that does not stick, the name still has a live chain, the second NEW ADOPTS it, and the two ids are EQUAL. It separates a real retirement from a cheerful message, which is the defect shape this house keeps finding. ASSERTIONS READ THE CATALOG TABLE, not the console: WORKSPACES.dbf is an ordinary x64 table -- the map drawn in the same ink as the territory -- so the spec opens it and compares FIELDS, per the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. WSL_T1/T2/T3 read the birth row itself: FMT 'BIRTH 1' (self-describing rather than inferred), SIZE_B 0 (no payload), PREV_ID 0 (it IS the chain root, which is what D10.2 makes identity). WSL_T5 reads the RETIRED row and finds it still present and flagged SUPERSEDED -- retirement is supersession, not deletion, so a destroyed workspace leaves a record rather than a hole, and SUPERSEDED keeps ONE meaning ('no longer the current state of this name') whether a newer save replaced it or nothing did. WSL_T6/T7 are the refusal arms and neither claims anything is absent: USE_AGAIN established over three cuts that no marker in this language can assert emptiness and that an ERRORED marker PRINTS NOTHING rather than going red, so both ask the answerable question instead -- did the KNOWN OCCUPANT SURVIVE. T6: DEFAULT refuses destruction (invariant I1 needs it to outlive every other workspace) and its sentinel still reads. T7: a workspace still holding an area refuses, and the area is still readable -- destroy does not cascade, so it can never be the thing that silently orphaned an open area. NOT COVERED, stated rather than implied: ADOPTION ACROSS A PROCESS BOUNDARY. WORKSPACE NEW refuses a duplicate name within a session, so one process cannot ask a second NEW to adopt. It was proven by hand instead (2026-08-23, build 05:27:07: two datarun processes, 'WS_ID 110' then 'WS_ID 110' + ADOPTED), and a two-process fixture is the chartered follow-up; this spec does not claim it. GUARDS: if any WSL_G* reds, treat every WSL_T* as UNPROVEN -- the catalog predicates depend on locating the right row, and the refusal arms depend on a sentinel actually having been written. WSL_G4/G5 EXIST BECAUSE THE FIRST RUN NEEDED THEM: the fixture wrote APPEND BLANK, which this shell does not take -- BLANK falls through as an unrecognized argument, APPEND prints its usage, nothing is appended, and REPLACE reports 'no current record'. Both sentinel tables were created EMPTY, and WSL_T6 and WSL_T7 went RED while the verb under test had behaved perfectly, printing both refusals exactly as designed. A FIXTURE failure wearing a VERB failure's clothes -- and had the unwritten field happened to compare equal it would have been a FALSE GREEN instead. The spec had guarded its catalog reads and not its sentinel writes, the same omission WSMULTI's WSM_G4 was added to close: guard every input an arm reads, not only the interesting ones. This verb is also where xbase::workspace::destroy() finally gets a call site: defined, correct, and CALLED BY NOTHING since stage 3, the fifth AIF-079 instance this lane catalogued and the first it closed. Self-bootstrapping WSLDEF/WSLOCC in SANDBOX, erased at the end; leaves retired catalog rows behind BY DESIGN -- that is the history D10.3 keeps and what WSL_T5 reads. Explicit-run until soaked, then promote to default. PROMOTED to the default suite 2026-08-24, ON A STEWARD RULING ABOUT ITS COST AND AFTER THAT COST WAS ACTUALLY MEASURED. This spec was held back longer than any other in this lane because it carries the most catalog residue of any spec -- minting and retiring WS_IDs IS its subject matter -- and the residue question was open. It was framed as a disk question and that framing was wrong. MEASURED 2026-08-24 by parsing WORKSPACES.dbf at record boundaries: 150 rows, ZERO deleted-flagged, 132 SUPERSEDED, 18 live. SNAPSHOT is a memo field and WORKSPACES.dtx is 2.74 MB against a 104 KB table, so the worry was that each residue row drags a snapshot with it -- IT DOES NOT. 110 of 150 rows carry a memo pointer and ZERO of the 39 workspace-spec rows do. Residue is 703 bytes a row: one REGRESSION ALL costs 4,921 bytes of DBF and 0 bytes of memo, so a thousand runs is 4.7 MB. The steward accepted that cost. WHAT THE MEASUREMENT FOUND INSTEAD, and it is why this spec is safe to promote while others would not be: eighteen rows are SUPERSEDED=0, i.e. LIVE HEADS, and thirteen of those are test and probe fixtures that were never retired (goneprobe, goneprobe2, partialprobe, ls_probe, ls_idxprobe, cycle_from_ram, v3_regress, sess_regress, wm_regress, minidb_regress, minidb_sidecar, ram_hydrate_src, LADDERTEST). A spec that mints a name which already has a live row does not get a fresh workspace -- IT ADOPTS, inheriting whatever the previous run left there, which is history-dependence wearing a green suit. THIS SPEC RETIRES EVERYTHING IT MINTS and WSL_T4 is the arm that proves it: destroy WSLADR1, create it again, second WS_ID must be GREATER. That arm cannot pass if a live row survived. So the property promotion actually requires is the property this spec already asserts about itself. NOTE THE ONE ROW IT LEAVES LIVE: LADDERTEST (rec 110) is a live head in the catalog today and this spec does not create it -- it predates the lane and is listed above as one of the thirteen. It is not this spec's residue and is not this spec's to clean up; it is named here so a reader counting LADDER-ish rows does not attribute it to this file. A WORKSPACE PURGE verb was ruled in on the same day and is designed separately (claude/AIF078_DESIGN_WORKSPACE_PURGE.md); when it exists the thirteen live heads are what it should be pointed at first, NOT this spec's superseded rows, which are the history D10.3 exists to keep. VERIFIED IN-SUITE 2026-08-24, and it CORRECTS THE ARITHMETIC ABOVE. Promoted, then run inside REGRESSION ALL on the same build. All seven WSL_T* arms and all five WSL_G* guards read .T.; WSL_T4 saw WS_ID 156 retired and 157 minted, greater as required. Order-independence is demonstrated rather than assumed: this spec's own opening teardown printed 'WORKSPACE DESTROY: no such workspace: WSLADR1' -- the previous run's names had been properly retired, so it started from a clean slate INSIDE a suite that had already run fourteen specs ahead of it. THE PER-RUN COST IS NOT 7 ROWS, IT IS 10. The 4,921-byte figure above was measured BEFORE this promotion and is the pre-promotion number; this spec mints three of its own (WSLADR1 twice, because WSL_T4 destroys and re-creates it, plus WSLADR2). Measured on the promoting run: the catalog went 150 -> 160 rows, WS_IDs 151-160, of which 156/157/158 are this spec's. So one REGRESSION ALL now costs 10 rows = 7,030 bytes of DBF and still 0 bytes of memo, and a thousand runs is 6.7 MB. Recorded as a correction rather than by editing the 4,921 away, because both numbers are true of the moment they describe and a summary that silently retunes its own measurements is the defect this house keeps finding one layer up. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. MEASURED ON THE 2026-08-29 PROMOTING RUN: this spec's rows went to data/tmp/wscat_run_81, 3 of them -- exactly the three this entry already claims (WSLADR1 twice, WSLADR2 once) -- and the L3 isolation arm read the PRODUCTION catalog at 264 rows BOTH BEFORE AND AFTER the suite. THE MINT COUNT DID NOT CHANGE AND WAS NEVER WRONG -- what changed is WHERE IT LANDS, and that is the whole correction. The four bracketed default-suite specs still mint exactly TEN rows between them (WORKSPACE_SCOPE 2, WSMULTI 3, WSLADDER 3, RELSCOPE2 2), the same ten the L2 comment in this file measured as 252 -> 262 on 2026-08-28 -- so the per-spec numbers corroborate rather than contradict. What is void is every projection built on top of them: a row count per run cannot be multiplied into megabytes of a durable catalog that is not being written. The cost is a throwaway directory under the gitignored TMP slot. MWXSHAKE joined the suite the same day at 16 rows, so the suite now mints 26 per run and the production total still did not move. BOTH BYTE FIGURES ABOVE ARE THEREFORE VOID AS DURABLE-CATALOG COSTS: 4,921 bytes, 7,030 bytes, 4.7 MB and 6.7 MB all described growth in WORKSPACES.dbf, and WORKSPACES.dbf no longer grows on a regression run. The ROW counts they were computed from stand. Kept rather than deleted for the reason the sentence before this one gives: they are true of the moment they describe, and this is the third time this entry has been corrected by measuring instead of inheriting.",
        true,
        true  // AIF-078 L2: mints catalog rows -- bracket it
    },
    {
        "WSPURGE",
        "workspace_purge_regression.dts",
        "WORKSPACE DELETE (spelled PURGE until 2026-08-24; the alias is still accepted and PG_T5 keeps it exercised): catalog rows are FLAGGED, never packed (AIF-078, steward ruling 2026-08-24 \"A -- flag, never pack\"; design claude/AIF078_DESIGN_WORKSPACE_PURGE.md). THE VERB WAS RENAMED BECAUSE THE OWNER READ ITS OUTPUT: \"how could you ever locate a purged row, it is gone forever, delete is a flag and that means the row still exists just ignored.\" Correct -- the verb sets the delete flag and SUPERSEDED and the row stays on disk PERMANENTLY, which is the whole design since max(WS_ID)+1 needs those rows COUNTED. The name promised removal and the code guaranteed the opposite; in xBase the pair is exact, DELETE flags and PACK removes. The name misled the OWNER reading output written by its own author, which is the proof that a name reaches further than any definition beneath it. The spec file and this spec id keep the WSPURGE spelling deliberately -- a spec id is an allocated identifier with run history behind it. PG_T5 IS A FIELD-VALUE MARKER, NOT A COMMAND RUN: its first draft was the WORKSPACE PURGE line plus a comment naming itself PG_T5, asserting nothing, so a dead alias would have printed an error and left the spec all green -- the FIELDMGR_APPEND defect committed inside the arm written to prevent it, caught before it ran. PG_T1 IS THE DISCRIMINATOR and it exists because WS_ID allocation is max(WS_ID)+1 DERIVED by scanning surviving rows -- nothing persists a high-water mark. Physically remove the newest rows and the next WORKSPACE NEW re-mints an id a purged workspace already used; D10.2 makes the chain-root WS_ID the DURABLE IDENTITY, so that is two workspaces sharing one identity across time, R5 on the time axis, undetectable after the fact. The fixture arranges the trap on purpose: WSPRG1 is minted, retired, minted and retired again so its two rows are the two HIGHEST in the catalog, both are purged, and then a NEW name must mint ABOVE the highest purged id. Pack, and PG_T1 reads .F. PG_T2/PG_T3 ARE A PAIR because ruling A has two halves and a row is WORSE OFF if only one lands: the delete flag hides the row, SUPERSEDED=1 stops scan_catalog ELECTING it live -- and that scan does not filter deleted rows, it elects on WS_NAME plus SUPERSEDED alone, so a flag-only purge would leave a row invisible to the user and still adoptable by the next NEW, the AIF-118 shape exactly. PG_T2 reads the purged row with SET DELETED OFF and asserts SUPERSEDED=1. PG_T3 WAS WRITTEN TO SHOW THE ROW GOES AWAY UNDER SET DELETED ON AND INVERTED ON ITS FIRST RUN, 2026-08-24 -- which is the most valuable thing this spec has produced. LOCATE printed 'Located.' and moved the cursor onto the purged row with the shell reporting 'Deleted visibility: HIDE (ON)' one line earlier: a DELETE-FLAGGED RECORD IS STILL REACHED BY LOCATE. The flag itself landed -- purge_durable_workspace re-reads isDeleted() from the record before counting a row done and refuses to continue if it is false, and the verb reported both rows purged -- so this is LOCATE not consulting the setting, not a write that failed. WHAT IT CORRECTS: the delete flag is NOT what protects the catalog. SUPERSEDED is. The flag's value is that scan_catalog still COUNTS the row, which is exactly what preserves the high-water mark PG_T1 asserts. Hiding was assumed rather than measured, in the design and in this spec's own header, and the assumption was wrong. PG_T3 is now a TRIPWIRE recording the measured behaviour, with PG_T3B reading the protection that actually holds off the same row in the same breath; if PG_T3 ever reads .F. again, LOCATE has GAINED delete-filtering and the arm should be repointed deliberately rather than allowed to retune itself (the IDXSTALE precedent). THE TRIPWIRE FIRED THE SAME DAY AND HAS BEEN REPOINTED DELIBERATELY. AIF-123 found the cause: filter::visible() -- the ONE gate LIST, COUNT, SMARTLIST, LOCATE, FIND, SCAN, EXPORT and logical_nav all ask, twelve callers -- applied SET FILTER and FOR and NEVER consulted SET DELETED. Not a LOCATE defect at all; LOCATE was behaving like every other caller of a gate with a missing rung. The rung had been absent since 06ba79e93 (2025-08-16), which rewrote LIST, replaced its Settings::deletedOn() read with a per-command flag, and PRESERVED THE DEFAULT WHILE SEVERING THE CONTROL -- so nothing changed on the path anyone ran and nothing could go red, for fourteen months. With the rung restored LOCATE reports 'Not Located.' and PG_T3 is INVERTED to assert that. PG_T3B is REPURPOSED rather than deleted: it used to read SUPERSEDED off the row LOCATE landed on, and with no landing it was reading a stale cursor and would have gone red for a reason unrelated to its own name; it now carries the OTHER HALF, that SET DELETED OFF still reaches the row. Both-halves is the point -- 'hidden under ON' asserts nothing without 'visible under OFF' beside it, because a build that hides unconditionally passes the first and fails the second. See SDVIS, which is built entirely on that principle. PG_T4 IS THE REFUSAL ARM AND IT GUARDS A RULE THAT CHANGED BETWEEN DESIGN AND CODE: the design said PURGE would refuse any name with a LIVE catalog row and send the caller to DESTROY first, until DESTROY's dispatch was actually read -- it resolves its target through resolve_workspace_token(), the RUNTIME registry, and answers 'no such workspace' for anything not currently declared. A catalog-only live head (the thirteen the 2026-08-24 census found: goneprobe, ls_probe, wm_regress and ten others) would have been reachable by NEITHER verb. The clause would have fenced off the exact rows the verb was ruled in to deal with -- the same mistake as calling workarea_util 'a shared home' before checking the second consumer could link it. What is refused instead is a workspace DECLARED IN THIS SESSION, whose identity must not be yanked out from under it. PG_G2 DELIBERATELY DOES NOT USE RECCOUNT(): USE_AGAIN measured that RECNO()/FOUND() render EMPTY in a '?' marker, RECCOUNT() serves compile_predicate rather than the marker path, and a marker that errors prints nothing rather than going red -- so that guard would have vanished from the suite while the count still read full. Every marker is a FIELD-VALUE comparison against WORKSPACES.dbf per the FIELDMGR_APPEND doctrine. Leaves its own rows behind flagged and superseded BY DESIGN: the file never shrinks, which is what ruling A chose, and the honest cost is 4 rows per run. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. This spec is flagged mints_catalog and is EXPLICIT-RUN, so it is bracketed on the same code path -- but it was NOT run on 2026-08-29 and its 4 is therefore NOT RE-MEASURED, stated rather than assumed. What is established is the DESTINATION, which follows from the flag plus the bracket's placement and needs no run of this spec to be true: whatever it mints goes to a per-run scratch root, and 'the file never shrinks' now describes a throwaway file. Re-measure the 4 when this spec is next run. NOT COVERED, stated rather than implied: that a purged row is genuinely delete-FLAGGED as opposed to merely hidden -- DELETED() is a predicate-path function, not a marker-path one, so PG_T3 proves reachability rather than the flag byte; a unit fixture over DbArea::isDeleted() is the honest home for that claim. RE-PURGE IS IDEMPOTENT AND IS NOW REPORTED AS SUCH, which this spec's own SECOND run exposed: the fixture uses stable names, so run two found run one's rows still carrying WSPRG1 and re-purged them, and the verb announced 'Purged 4 row(s), WS_ID 161,162,165,166' when only 165 and 166 had moved. The outcome was correct -- setting SUPERSEDED on a superseded row and re-flagging a flagged one changes nothing -- but the COUNT was not, and left alone every run would report a larger number for the same work: 2, then 4, then 6, with nothing saying why. WORKSPACE WRITEBACK's rule pointed at a different loop -- a count is a fact about a loop until something declares what it SHOULD be. The verb now reads each row's state before touching it and reports transitioned and already-purged rows separately. NOT ASSERTED BY AN ARM, stated rather than implied: no marker reads those counts, because markers are field-value comparisons and counts are console text; the idempotence is visible in the transcript and verified by reading it, the IDXDIFF precedent. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (NEW x4)
    },
    {
        "SDVIS",
        "set_deleted_visibility.dts",
        "SET DELETED VISIBILITY: the setting decides whether delete-flagged but unpurged rows are visible to displays and searches (AIF-123; restoration of a rung lost 2025-08-16). BOTH HALVES ARE ASSERTED AND THE **OFF** HALF IS THE DISCRIMINATOR. A spec that only asserts 'SET DELETED ON hides the row' passes green on a build that hides deleted rows UNCONDITIONALLY -- which is precisely the build 06ba79e93 (2025-08-16) produced and precisely what shipped for the next fourteen months. That commit rewrote LIST and replaced its Settings::deletedOn() read with a per-command flag; 523a85e54 the same day pruned the .sav still carrying the old line, after which NOTHING in the tree called Settings::deletedOn(). THE REWRITE PRESERVED THE DEFAULT AND SEVERED THE CONTROL: LIST still hid deleted rows, so no behaviour changed on the path anyone ran and nothing could go red. The only way to observe the loss is to CHANGE THE SETTING AND NOTICE NOTHING CHANGES, which is absence proven by contrast -- the same doctrine FIELDMGR_APPEND paid for, in a new place. THE FIX IS ONE RUNG IN ONE GATE: filter::visible() (filter_registry.cpp) is what LIST, COUNT, SMARTLIST, LOCATE, FIND, SCAN, EXPORT and logical_nav (first/next/prev/last -- NOT SKIP or GO, which was the error corrected by R121) all ask, twelve callers, and it applied SET FILTER and FOR and never consulted SET DELETED. Two comments asserted the rung was there -- logical_nav.hpp:19 named filter::visible() as the enforcer, scan_selector.cpp called its helper 'filter + deleted policy' -- so a reader checking found two affirmations and no code. A third was counted at the time -- foxpro_go.hpp -- and withdrawn 2026-08-24: that file is unreviewed generated prose, not a spec, and it contradicts itself on the point it was cited for. PRECEDENCE, RULED BY THE STEWARD 2026-08-24: an explicit clause beats the session default, so the gate takes a DeletedPolicy and callers carrying a clause pass CallerHandles. SD_ON_T6 IS THE ARM THAT MATTERS MOST and it exists because the owner asked about cmd_delete.cpp before this was committed: RECALL's entire purpose is delete-flagged rows, so a gate reaching it would hide every row RECALL is for and the verb would report success over an empty selection. It does not, because all four of cmd_recall's selection paths set deleted_mode=OnlyDeleted; the arm locks that in rather than trusting it. GO AND SKIP ARE THE ARMS, NOT LIST AND COUNT: markers are FIELD-VALUE comparisons per FIELDMGR_APPEND and GO/SKIP always land the cursor on a readable record, while LIST and COUNT report through console text no marker can read -- their behaviour is visible in the transcript and is NOT claimed by an arm (the IDXDIFF precedent). GO AND SKIP WERE RULED SEPARATELY ON 2026-08-24 BY R121 -- ADDRESSING IS ABSOLUTE, TRAVERSAL IS FILTERED. GO <n> names a record and lands on it under any setting, because a GO that skipped forward could not reach the record it names and would close the only route onto a flagged row for a single RECALL; SKIP, TOP and BOTTOM name a position in a SET and now walk the visible one. The single defect was navsel::resolve_mode choosing the logical view by asking only whether a SET FILTER was active. Ruled on principle: an earlier version of this entry cited include/foxpro_go.hpp as canon for the opposite, and that file turned out to be unreviewed generated prose that contradicts itself -- the citation was the steward's and is withdrawn. NOT SEPARATED, stated rather than implied: if the SD_ON_* arms red, either the flag never landed on record 2 or the setting is not consulted -- both make the row reachable under ON and this spec cannot tell them apart; the honest home for 'is the flag byte set' is a unit fixture over DbArea::isDeleted(). EXPECTED SIDE EFFECT ON WSPURGE: PG_T3 is a TRIPWIRE recording that LOCATE reached a purged row under SET DELETED ON, and this fix makes it read .F. That is the tripwire doing its job. Repoint it deliberately per its own instruction (the IDXSTALE precedent); do not let it retune itself. Disposable table, rebuilt every run, leaves nothing behind. Explicit-run until soaked.",
        false
    },
    {
        "RELSCOPE2",
        "relation_workspace_scope.dts",
        "THE RELATION STORE IS WORKSPACE-SCOPED (AIF-078 I1.2, 2026-08-23). Until this landed the relation graph was ONE process-global map, and cmd_workspace.cpp said so under a comment headed 'KNOWN OVER-REACH, STATED RATHER THAN HIDDEN': a scoped close had to clear EVERY relation, because leaving an edge pointing into an area it had just emptied is the dangling-parent shape and a dangling relation is worse than an over-eager clear. It PRINTED the cost when it could bite -- 'relations are cleared GLOBALLY ... (AIF-078 stage 3 limitation)' -- and it named its own fix. Both arms here FAIL against that implementation and PASS against the partitioned store; delete the partition and both go red. RS_T1: REL CLEAR ALL issued inside RSWSA leaves RSWSB's relation driving its child. RS_T2: a SCOPED WORKSPACE CLOSE of RSWSA does the same. ASSERTED BY FIELD VALUE, never console text: a relation's observable effect is refresh-driven slaving, so each arm moves RSWSB's parent to a DIFFERENT key, refreshes, and reads the CHILD's label -- if the relation survived the child follows and the label CHANGES; if it was collateral damage the child sits still. The two arms deliberately target different rows (B_BETA then back to B_ALPHA) because a spec that re-asserts the value it already saw proves nothing. NOTHING HERE ASSERTS RSWSA'S RELATIONS ARE GONE: no marker in this language can assert absence (USE_AGAIN, three cuts) and an errored marker PRINTS NOTHING rather than going red, so absence is proven by contrast -- and survival is the half that matters anyway, because the defect was never 'clears too little'. GUARDS: RS_G0 the fixture, RS_G1 THE RELATION WAS LIVE BEFORE THE ACT UNDER TEST -- without it an arm reading an unchanged label cannot tell 'survived' from 'never worked' -- and RS_G2 the other workspace's relation was actually rebuilt before the close. If any guard reds, treat both arms as UNPROVEN. RECORDED NOT FIXED: current_parent_override() in set_relations.cpp is still ONE global rather than per workspace; it is the REL parent shorthand and not the graph, so it does not affect these arms, but it is the next workspace-blind piece of relation state and should not be found by surprise. ALSO IN I1.2 and not covered here: set_current_handle() now REJECTS 0 at the API (D9 sec 4 item 4) -- harmless against a flat map, load-bearing against a partitioned one, since a stray 0 would drop a whole workspace's relations into the reserved 'no such workspace' bucket. Self-bootstrapping RSAP/RSAC/RSBP/RSBC in SANDBOX, erased at the end; both workspaces destroyed in teardown (D10.3). CORRECTED 2026-08-23, MEASURED: the clause that used to end here read so no catalog rows accumulate, and that is FALSE. D10.3 retirement is SUPERSESSION, not deletion -- WORKSPACE DESTROY prints History kept: every row in the chain is still there and still readable, a destroyed workspace leaves a record, not a hole. What teardown guarantees is that the NAME HAS NO LIVE ROW, so a later WORKSPACE NEW mints fresh rather than adopting; the rows themselves remain and this spec adds more on every run. Measured by parsing WORKSPACES.dbf at record boundaries: 143 rows, ZERO deleted-flagged, of which 28 are workspace-spec residue (RSWSA 4, RSWSB 4, WSLADR1 8, WSCHILD 3, WSPARENT 3, WSALPHA 2, WSBETA 2, WSGAMMA 2). The claim was inherited from this summary and repeated without measuring it, which is the defect this house keeps finding one layer up. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. MEASURED ON THE 2026-08-29 PROMOTING RUN: this spec's rows went to data/tmp/wscat_run_82, 2 of them, and the L3 isolation arm read the PRODUCTION catalog at 264 rows BOTH BEFORE AND AFTER the suite. The residue census above (RSWSA 4, RSWSB 4, WSLADR1 8 and the rest) is therefore a HISTORICAL reading of a file these specs have stopped adding to; it is left standing as the record of what unbracketed running cost. THE MINT COUNT DID NOT CHANGE AND WAS NEVER WRONG -- what changed is WHERE IT LANDS, and that is the whole correction. The four bracketed default-suite specs still mint exactly TEN rows between them (WORKSPACE_SCOPE 2, WSMULTI 3, WSLADDER 3, RELSCOPE2 2), the same ten the L2 comment in this file measured as 252 -> 262 on 2026-08-28 -- so the per-spec numbers corroborate rather than contradict. What is void is every projection built on top of them: a row count per run cannot be multiplied into megabytes of a durable catalog that is not being written. The cost is a throwaway directory under the gitignored TMP slot. MWXSHAKE joined the suite the same day at 16 rows, so the suite now mints 26 per run and the production total still did not move. PROMOTED to the default suite 2026-08-23. The soak was the AIF-078 slot-lane step 1 lift, which MOVED the code this spec covers -- find_free_area_for_workspace left cmd_use.cpp for workarea_util and took its engine and membership table as arguments -- and both arms read green afterward. THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, not the soak alone: REGRESSION ALL CANNOT REACH IN FREE. A grep of the whole .dts corpus finds the phrase in exactly two files, this one and the other of this pair, and both were explicit-run -- so a change to the free-slot allocator could pass the entire default suite and say nothing about the policy. That is what happened on 2026-08-23: ALL ran ten specs green over a commit that rewrote the allocator, and the allocator was not exercised once. This is also the only spec that runs IN FREE with TWO WORKSPACES OPEN AT ONCE, which is the arrangement the scoping exists for and which USE_ARGS cannot reach: measured 2026-08-23, RSWSA took engine areas 0 and 1 and RSWSB, starting with no members and so having no run to grow, took the lowest free slot 2 and then grew contiguously to 3.",
        true,
        true  // AIF-078 L2: mints catalog rows -- bracket it
    },
    {
        "MWXSHAKE",
        "workspace_minidb_multi_shakedown.dts",
        "MULTI-WORKSPACE AND MINIDB IN ONE FILE, ON PURPOSE (AIF-078 + AIF-070, written 2026-08-28). THE TWO LANES ARE NOT INDEPENDENT: a MINIDB container carries a POSTURE, a posture is a picture of a WORKSPACE, and the interesting failures live where they meet -- a container hydrated into RAM lands its tables in whatever workspace is current, at slots the posture does not control. A spec exercising either alone cannot reach that seam. THE MARKER COUNT IS DERIVED, NOT DECLARED: count the lines whose marker prefix is MWX_ (guards MWX_G*, arms MWX_T1..N contiguous) and read the run against THAT. A number written here is a SECOND DECLARATION and this one already drifted -- it said 35 / 11 guards / 24 arms while the file held 40 / 14 / 26, because section 5B was added and the count beside it was not. COUNT THEM FIRST: an errored marker prints NOTHING rather than going red, so one short of the derived count is a FAILURE wearing a clean transcript. If any MWX_G* reads .F., every arm below it is UNPROVEN rather than failing. EVERY POST-LOAD ASSERTION ADDRESSES BY NAME, NEVER BY SLOT, and that is the direct lesson of 2026-08-28: R130 makes a posture's AREA numbers KEYS rather than addresses, the load prints so, and four specs carried slot-addressed arms that produced FALSE GREENS the moment their fixtures shrank -- because a marker over a CLOSED area does not error, it prints a verdict whose polarity depends on the OPERATOR ((SID >= 1) reads .T. over nothing, (SO_ID = 6) reads .F.). See claude/FINDING_MARKER_OVER_A_CLOSED_AREA_PICKS_A_SIDE.md. MULTI-WORKSPACE COVERAGE: SWITCH-then-open membership (an area joins whichever workspace is CURRENT when it is OPENED, never open-then-assign); UNDER nesting; OPEN <dir> AS <name>, which overrides the directory leaf and is itself a MINTING form; additive re-entry proven by a PARKED CURSOR SURVIVING rather than by a count a re-open could fake; scoped CLOSE with the other workspace's area still readable as the discriminator; and ONE FILE OPEN IN TWO WORKSPACES, the case a global registry cannot represent -- MWXSHARE exists in both fixture directories under the same name with different labels, so the arm can say which copy it read. The R112 ambiguity ledger fires there by design ('open in 2 areas ... first-wins is a migration step'); that is the ledger working, not an error. THE IDENTITY LADDER: DESTROY refuses DEFAULT (invariant I1), refuses a workspace still HOLDING AREAS, and refuses a parent with a CHILD -- three refusals, none of them cascading, each read by asking whether the KNOWN OCCUPANT SURVIVED rather than by claiming absence. MWX_T9 IS THE DISCRIMINATOR and it is one line of meaning: destroy a name, create it again, second WS_ID must be GREATER. If DESTROY silently no-ops or writes a flag that does not stick, the name keeps a live chain, the second NEW ADOPTS, and the ids are EQUAL. DELETE flags and never packs -- there is deliberately no WORKSPACE PACK because max(WS_ID)+1 is DERIVED from surviving rows, so deleted rows must keep being COUNTED or the next NEW inherits a deleted workspace's identity. PURGE is a retained alias whose name is wrong (in xBase DELETE flags, PACK removes) and MWX_T12 asserts it still reaches the verb rather than assuming it. DELETE refuses a workspace DECLARED IN THIS SESSION. MINIDB COVERAGE: SAVE <name> MEMO MINIDB stores a CONTAINER whose payload IS the database, against SAVE <name> MEMO which stores a POSTURE with the tables left on disk -- MWX_T23/T24 read FMT off the catalog table to prove the two rows differ on exactly that field, which is the cheapest possible proof they are not one artifact wearing two names. MINIDB implies V3 because the embedded posture must be SELF-LOCATING to survive being re-pointed at RAM. Plain LOAD ... MEMO REFUSES a MINIDB payload BY DESIGN (its tables have no disk home, and standing up empty areas over missing files is the silent-success failure this codebase hunts) and MWX_T14 reads that the session survived the refusal. LOAD ... MEMO RAM hydrates with zero disk reads; the byte counts and per-file oracle compares in the transcript are EXTERNAL measurements and are deliberately NOT claimed by an arm (the IDXDIFF precedent) -- the arms claim the ROWS ARE THERE and the MEMO SURVIVED. A hydrated table is WRITABLE (MWX_T17), and WRITEBACK returns it to real disk where MWX_T18/T19 read it back AFTER the RAM disk is unmounted, which is the only reading that proves the return leg rather than the mount. THE SHORTFALL CONTRACT: LOAD resolves and probes declared members BEFORE closing anything, so a load that cannot complete leaves the session STANDING -- MWX_T20 proves it by reading an UNRELATED open table that must not have moved. PARTIAL opts back into permissive behaviour explicitly. A MISSING INDEX does NOT refuse (MWX_T22): indexes are derived and rebuildable and deliberately outside the probe. SELF-BOOTSTRAPPING AND SELF-ERASING in DBF/SANDBOX; the writeback directory is scratch and is removed at both ends so MWX_G4's 'really removed' reading cannot inherit a previous run's leftovers. Teardown DESTROYs every workspace it declares, so the NAME has no live row and a second run MINTS rather than ADOPTS -- the rows themselves remain, because D10.3 retirement is SUPERSESSION and a destroyed workspace leaves a record, not a hole. Residue is therefore MEASURED AT 16 CATALOG ROWS PER RUN, ALL OF THEM IN A SCRATCH CATALOG, which is why this entry is flagged mints_catalog. Measured 2026-08-29: the three green runs of the 48-marker version each left 16 rows (wscat_run_73 and wscat_run_78 byte-identical at 12515 bytes with the identical multiset of MWX* names; wscat_run_83, the in-suite run, printing its own WORKSPACE CATALOG as '16 row(s): 6 live, 10 superseded' with every row MWX-named). THE NUMBER IS A DBF HEADER RECORD COUNT, NOT A FIELD PARSE -- an attempt to read WS_NAME out of that file by field offset produced nonsense on the first try, because the X64M metadata block sits INSIDE the descriptor area and shifts every offset after it. CORRECTED BEFORE IT WAS COMMITTED, and recorded rather than quietly retuned: this clause first said FOURTEEN, from 16 minus a 2-row 'baseline' read off wscat_run_77. THERE IS NO BASELINE TO SUBTRACT. The L2 bracket creates a FRESH scratch catalog per bracketed spec, so wscat_run_77 was a DIFFERENT spec's bracket and its 2 rows were never this one's floor -- a number arrived at by arithmetic over two things that were never the same measurement, which is the defect this house keeps finding one layer up. AND THE COST IS NOT WHERE THE OLDER ENTRIES IN THIS FILE SAY IT IS: because of the bracket, this spec adds ZERO rows to the PRODUCTION catalog. The L3 isolation arm read it at 264 rows both before and after the suite on the promoting run. What a REGRESSION ALL actually pays is a 16-row scratch catalog directory under data/tmp, which is disk in a scratch tree rather than growth in the durable one. SET ORDER SURVIVAL IS COVERED, section 5B, added and run green 2026-08-28 -- the clause here used to say it was NOT covered and that no spec in the corpus proved it, which was true for about four hours. THE TAG TRAVELS IN THE ARTIFACT: a DTSCHEMA AREA line carries tag=, so the order is part of what SAVE writes and LOAD reads, and nothing else in the corpus reads it back -- losing it would be silent. IT BORROWS A SHIPPED CDX (STUDENTS under DBF/X64) because this file's own fixtures index with INDEX ON, which writes .inx, while SET ORDER TAG wants a CDX. THE DISCRIMINATOR WAS CHOSEN BY MEASURING BOTH CANDIDATES: SID order == physical order for all 200 rows, so SET ORDER TAG SID then TOP lands exactly where an engine that IGNORED the order would land -- an arm that cannot tell two implementations apart. LNAME diverges at BOTH ends and is therefore the one used: physical rec 1 Taylor against LNAME-first Anderson (rec 21), physical rec 200 Davis against LNAME-last Wilson (rec 157). MWX_G6 reads the order LIVE BEFORE THE SAVE; MWX_T25/T26 read both ends after a MEMO V3 round trip; drop the tag anywhere between and the walk goes physical. SECTION 5C IS THAT BUILT-CDX ARM, added 2026-08-29. It builds a four-row fixture whose physical and keyed orders disagree at BOTH ends (ZULU MIKE ALPHA TANGO physical; ALPHA MIKE TANGO ZULU by CLBL), reads the physical ends BEFORE any index exists (G7a/G7b -- without them T27 landing on ALPHA could be where an order-ignoring engine would have landed anyway), then CDX CREATE / CDX ADDTAG CLBL / BUILDLMDB YES / SET ORDER TAG CLBL. THE TAG NAME IS THE KEY: ADDTAG takes a name and no key expression (cmd_cdx.cpp:324-420) and cmd_buildlmdb.cpp:468-480 resolves it later by walking area.fields() for a match. A TAG NAMING NO FIELD WAS ACCEPTED IN SILENCE AND NOW IS NOT. ADDTAG validated NOTHING AT ALL -- it took the name, wrote the tag, and left the resolution to a loop that answers `if (fld < 1) return false;`, printing nothing while only the total is reported, the count discipline again. The clause here used to say that wanted an arm of its own; it got one the same day. cmd_cdx.cpp and cmd_cnx.cpp now refuse ADDTAG on a CLOSED AREA and on a name xfg::resolve_field_index_std cannot resolve -- the STANDARD resolver, the one REPLACE already refuses on (cmd_replace.cpp:822), so ADDTAG and REPLACE now answer 'what is a field name' with the SAME code rather than two that agree by luck. DROPTAG is deliberately NOT checked: dropping a tag that names nothing is how you clean up after the old behaviour. MWX_T31 IS THAT ARM and it is two claims, not one: ADDTAG on a name no field carries is REFUSED, and the table is then READ to prove the refusal CHANGED NOTHING -- a verb that refused after damaging the container would read identically in console text. STILL NOT FIXED, stated so it is not found by surprise: BUILDLMDB and REBUILD keep their OWN private normalizers (cmd_buildlmdb.cpp:475 is a raw textio::ieq with no trim and no descriptor alias; cmd_rebuild.cpp:144 normalize_field_name has no leading trim and no alias), so that is FOUR live declarations of what a field name is, and a tag arriving by any route other than ADDTAG can still be skipped in silence. REBUILD is the worse of the two -- it rebuilds the whole container in ONE backend call and then prints the OK line once per tag and reports ok = tags.size(), so a DEAD TAG IS REPORTED OK AND COUNTED. Its own comment says 'Report once per tag, but rebuild only happened once.' Teardown is one line because ERASE <table> CONFIRM sweeps same-stem sidecars across the DBF, INDEXES and LMDB roots (cmd_erase.cpp:176-205), so table, container and LMDB environment go together and CDX CREATE -- which refuses to overwrite -- finds clean ground next run. 5C ALSO PRODUCED A FALSE GREEN ON ITS FIRST RUN AND THE FIX IS THE ARM: the table was opened to build the index and therefore belonged to DEFAULT, `USE` on a table already open in the current area is a NO-OP FOR MEMBERSHIP, so the workspace created around it held ZERO members and the scoped SAVE wrote an EMPTY posture -- warning twice in console text no marker can read -- while the arms read the copy still open in DEFAULT. Closing first makes the section self-checking: with no live copy anywhere, an empty posture leaves SELECT with nothing to select and the markers vanish, so a SHORT COUNT is the failure signal. PROMOTED TO THE DEFAULT SUITE 2026-08-29 on TWO CONSECUTIVE GREEN RUNS of the 48-marker version against the same engine (wscat_run_73 and wscat_run_78; 17 guards MWX_G0a..G7c, 31 arms MWX_T1..T31, 48 total, derived by grep -c '^? \"MWX_' and not read off the checklist). THE COST IS PAID KNOWINGLY: 16 catalog rows on every REGRESSION ALL, measured above, which makes this the most expensive spec in the default suite and is the whole reason the mints_catalog flag exists -- and all 16 land in the per-run SCRATCH catalog, not the production one. THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, NOT THE SOAK ALONE -- the RELSCOPE2 precedent. Before this, the default suite reached ADDTAG through exactly ONE spec (INDEX_X64, twice) and reached the WORKSPACE/MINIDB SEAM through none, so the entire class this file was written for -- a posture crossing into RAM, an index order surviving a round trip, a scoped SAVE writing an EMPTY posture while the arms read a copy still open somewhere else -- could pass REGRESSION ALL without being touched once. THE SOAK ITSELF IS THE ARGUMENT: it produced THREE FALSE GREENS in two days, each of a different shape -- a slot-addressed arm over a CLOSED area whose polarity depended on the operator, MWX_T21 reading a REAL open table the verb under test never touched, and 5C's empty posture. NONE OF THE THREE IS FINDABLE BY GREP, which is the case for paying 16 scratch rows a run rather than leaving it explicit-run. Under ALL, read the COUNT first and the verdicts second. VERIFIED IN-SUITE 2026-08-29 ON THE PROMOTING BUILD, which is what promotion actually requires and not the soak alone. Promoted, rebuilt, then run as the SIXTEENTH and last spec of REGRESSION ALL: 17 guards and 31 arms all read .T., 48 markers, full count. ORDER-INDEPENDENCE IS DEMONSTRATED RATHER THAN ASSUMED -- it inherited a session from RELSCOPE2, closed it in its own opening WORKSPACE CLOSE, and its teardown block printed 'no such workspace' for every name it destroys, so the previous run's identities had been properly retired and it started from a clean slate. THE NEW ADDTAG GUARD FIRED LIVE IN THAT RUN: 'CDX ADDTAG: field not found: MWXNOSUCH ... Nothing was added.', with MWX_T31 then reading the table to prove the refusal changed nothing. The R112 ambiguity ledger also fired once during fixture creation ('MWXSHARE is open in 2 areas (ws 1 area 1, ws 1 area 3); resolved to area 1'), which is the ledger working as this entry describes and not an error. The L3 catalog-isolation arm read the production catalog at 264 rows both BEFORE and AFTER the suite, so the bracket held over the most catalog-hungry spec now in it.",
        true,   // PROMOTED 2026-08-29 -- two green runs of the 48-marker version
        true  // AIF-078 L2: mints catalog rows -- bracket it (NEW, OPEN..AS, SAVE)
    },
    {
        "NAV_NATURAL",
        "nav_order_natural_regression.dts",
        "AN ATTACHED CONTAINER IS NOT AN ACTIVE ORDER (AIF-148, written 2026-08-29). orderstate::hasOrder() returns `st && !st->container.empty()` -- it answers IS A CONTAINER ATTACHED. Six sites on the traversal path read it as IS AN ORDER ACTIVE. WORKSPACE OPEN attaches a .cdx to every table it lands and selects NO TAG, so the predicate said true for a table sitting in natural order, and every verb that trusted it went looking for a tag, found none, and returned failure. MEASURED on MCC STUDENTS (200 rows, CDX attached, no tag): TOP, BOTTOM, GO TOP, GO BOTTOM, GO FIRST and GO LAST all printed failed; SKIP printed 'SKIP: at end.' on record 1 and did not move; GO 5 worked. GO <n> survived because R121 already ruled addressing absolute and traversal filtered. SKIP IS THE SEVERITY AND IS WHY THIS SPEC EXISTS: the other six REFUSED, which is a wrong answer a reader can see in a transcript, and SKIP ANSWERED. WHY SIXTY REGISTERED SPECS SAID NOTHING, measured the same day and the more useful half of this entry: (a) 345 markers across the tracked corpus and NOT ONE mentions RECNO -- not laziness, a LANGUAGE LIMIT this house has already recorded four times (cnx_persist_proof, cnx_realtime_buffer_proof, cnx_realtime_index_proof, index_maintenance_failure_proof all say RECNO() RENDERS EMPTY IN A '?' MARKER and STR() does not rescue it), so NO ARM IN THE TREE CAN SAY 'the cursor is at 1'; (b) every navigation line in the corpus is followed by a marker that reads a FIELD, and USE/SELECT/CREATE have already parked the cursor on record 1, so a failed TOP and a working TOP READ IDENTICALLY -- workspace_load_shortfall.dts:149 is the shape exactly, USE STUDENTS / TOP / ? 'L_T4...' + (SID >= 1), green from record 1 and green from record 400; (c) STOP_ON_ERROR is opt-in, so a printed refusal sits above green markers and the run continues. THE COUNTERMEASURE IS STRUCTURAL, NOT DILIGENCE: every arm here PARKS THE CURSOR SOMEWHERE ELSE FIRST with GO <n> and then reads MARK, because an arm that reads row 1 on a table already standing on row 1 cannot fail. NAV_G1 is the load-bearing guard -- it asserts the PARK moved, on a row that is neither first nor last; if GO does not move, every arm below it is meaningless rather than green. THE FIXTURE SORTS BACKWARDS ON PURPOSE: ID descends as the physical order ascends, so natural order and tag order name DIFFERENT rows (natural TOP is ROW1, tag-ascending TOP is ROW6). NAV_T7/T8 ARE THE COUNTERWEIGHT and are the reason that matters -- a fix that forced natural ALWAYS would pass all six failing arms and be exactly as wrong as refusing, so two arms assert the opposite direction on the same fixture. Six arms cover TOP, BOTTOM, SKIP forward, SKIP backward, GO TOP and GO BOTTOM; GO TOP and GO BOTTOM are armed SEPARATELY from bare TOP/BOTTOM because they route differently and failed as their own line in the transcript. MINTS NOTHING, and that is deliberate: the attached-no-tag state is reached with SET INDEX TO (cmd_setindex.cpp:237-239 sets the container and then setActiveTag(A, \"\")), which is the identical state attach_workspace_index leaves behind (cmd_workspace.cpp:1123-1130) without needing a workspace to produce it -- so no catalog bracket is required. SMARTLIST for every transcript dump, never LIST (owner ruling 2026-08-29: 'list is my tool, use smartlist for tests'). NOT COVERED, stated rather than implied: the report sites that read the container predicate where they make an ordering claim -- console text, and no marker in this language can assert it. THOSE FOUR WERE CLOSED LATER THE SAME DAY and one of them was MIS-CLASSIFIED when this sentence was first written: db_tuple_stream.cpp:267 is not a report, it is a NAVIGATION MODE SELECTOR that entered OrderVector mode on the container predicate and was saved only by an empty-vector fallback downstream -- correctness by luck rather than by the predicate. Still unasserted by any arm: the corrected sites are console text or a GUI-side stream, and this language has no marker that reads either; GO FIRST / GO LAST, which failed alongside GO TOP in the same transcript and are BELIEVED to share the path, and believed is not measured; a FILTERED view, since cmd_skip.cpp pairs the order question with view_is_filtered() deliberately (R121) and this exercises the unfiltered half; and CNX, which container_supports_tag() treats identically and which is therefore expected to behave the same -- untested, unclaimed. Self-bootstrapping NAVTAG in SANDBOX, self-erasing. NOT YET RUN AT THE TIME OF WRITING -- the spec was authored against the fix in the same session and no green is claimed for it; it is explicit-run until it has been run twice, then promote. RUN AND PROMOTED 2026-08-29, build d0406cee (Aug 29 2026 12:19:47), TWO GREEN RUNS of that binary: all twelve markers .T. both times -- NAV_G0/G1/G2/G3 and NAV_T1 through T8 -- and the clause above is LEFT STANDING because it was true when it was written. THE TRANSCRIPT CORROBORATES MORE THAN THE GREENS DO, and that is the part worth keeping: the engine itself printed 'SET INDEX: CDX attached ... Use SET ORDER TO TAG <tag>' and then STATUS read 'Order: NATURAL / Index file: ...navtag.cdx / Active tag: (none)', which is the state under test SAYING ITS OWN NAME rather than being assumed; and the tag-order SMARTLIST came back RECNO 6,5,4,3,2,1, exactly inverted from physical, so the six natural arms and the two tag arms CANNOT BOTH PASS BY ACCIDENT. The mints-nothing claim was PROVEN rather than asserted: the L3 isolation arm read the production catalog at 268 rows before and after on both runs, so the suite total stays at 26 rows per run with this spec in it. The fixture worry recorded before the first run -- CDX CREATE on a CREATE X64 table under the SANDBOX index and LMDB slots, the one thing no other spec does -- was unfounded: the container built, BUILDLMDB reported OK=1, and cleanup erased all three artifacts including the .cdx.d environment. STILL NOT MEASURED, and this is the honest gap in the promotion: THE ARMS HAVE NOT BEEN RUN AGAINST THE PRE-FIX BINARY. WAO_T1 and MWXSHAKE both insist a discriminator is checked against the old build rather than reasoned about, and what exists here is the failing behaviour measured live on MCC STUDENTS in this state plus arms constructed so a cursor that does not move reads the parked MARK -- a strong argument, not a measurement. Anyone stashing the AIF-148 fix should see NAV_T1 through T6 go red while NAV_G0 through G3 stay green; if the guards red too, the fixture broke and the arms prove nothing either way. IN-SUITE VERIFICATION IS THE NEXT STEP AND HAS NOT HAPPENED: both green runs were EXPLICIT single-spec runs, which prove the spec works from a clean session and say nothing about order-independence when it inherits open areas from the spec before it -- the property MWXSHAKE's own promotion had to demonstrate rather than assume. VERIFIED IN-SUITE 2026-08-29 ON THE PROMOTING BUILD (7f5f0789, Aug 29 2026 12:54:43), and the clause above is LEFT STANDING because it was true when it was written. Run as the SEVENTEENTH and last spec of REGRESSION ALL: twelve markers, all .T., full count. ORDER-INDEPENDENCE IS DEMONSTRATED RATHER THAN ASSUMED -- it inherited MWXSHAKE's session with the DBF, INDEXES and LMDB slots left on x64, re-pointed all three to SANDBOX in its own opening lines, and its WORKSPACE CLOSE reported ZERO areas because MWXSHAKE's teardown had already left a clean slate, so the fixture was built from nothing. THE FLAG FLIP NEEDS A REBUILD AND THAT COST A RUN: the promotion commit was made and REGRESSION ALL run without rebuilding, so the suite ran SIXTEEN specs against a binary whose compiled-in registry still carried false. The suite was green and the spec was simply absent -- a full green over a spec that never executed, which is this file's own subject matter arriving as a process error rather than a code one. It was caught by the curated listing NONDESTRUCTIVE prints, where NAV_NATURAL still showed WITHOUT its [default] tag. A LMDB-SLOT WORRY RECORDED BEFORE THE RUN IS WITHDRAWN ON MEASUREMENT: BUILDLMDB wrote to LMDB\\SANDBOX\\NAVTAG.cdx.d, following the slot exactly. MWXSHAKE section 5C lands its env in LMDB\\x64 in the same run because THAT spec sets only the DBF and INDEXES slots, which is a fixture omission there and not an engine defect here. PRE-CHANGE BINARY RUN, 2026-08-30 -- THE DEBT IS PAID AND THE PREDICTION HELD EXACTLY. Built 0655860b, the immediate parent of the fix, in an isolated worktree; confirmed pre-change FROM SOURCE rather than from a hash, isNaturalOrder being absent from the tree entirely. MEASURED: NAV_T1 through T6 all .F., NAV_G0 through G3 all .T., NAV_T7 and T8 .T. Twelve markers, and the six reds are the fix's absence rather than a broken fixture because the guards held. THE TRANSCRIPT SAYS MORE THAN THE MARKERS, as this entry always argued it would: 'TOP: failed.', 'BOTTOM: failed.' and 'GO: failed.' twice are refusals a reader can see, and 'SKIP: at end.' printed ON RECORD 1 OF 6, twice, is the wrong ANSWER that is this spec's whole reason for existing. The tag-ordered SMARTLIST came back 6,5,4,3,2,1, exactly inverted from physical, so the six natural arms and the two tag arms cannot both be passing by accident. AN UNPLANNED SECOND MEASUREMENT FELL OUT OF THE SAME RUN: the STATUS block on that binary reads 'Order       : ASCEND' beside 'Active tag  : (none)', the REPORT half of AIF-148 caught against a pre-change build without anyone setting out to catch it. On the current build the same line reads NATURAL. So this run discriminates two fixes. CATALOG FIGURE CORRECTED: the production catalog is 271 rows, not the 268 recorded above -- see the WSENV entry for the cause, which was a steward error on 2026-08-30 and not a defect.",
        true   // PROMOTED 2026-08-29 -- two green runs, twelve markers each; VERIFIED IN-SUITE (see description)
    },
    {
        "OPENJOIN",
        "workspace_open_joins_current.dts",
        "WORKSPACE OPEN LANDS IN THE CURRENT WORKSPACE (R131, owner ruling 2026-08-29; supersedes the leaf-naming half of R128). A bare `WORKSPACE OPEN <dir>` used to derive a workspace name from the RESOLVED DIRECTORY LEAF, mint or adopt that workspace, switch into it, and open there -- so it walked OUT of the workspace the person was standing in, which is why the sanctioned R131 sequence NEW / SWITCH / SET PATH / OPEN never worked. MEASURED 2026-08-29 IN A LIVE SESSION: the one typed command `workspace open dbf` produced a workspace named `dbf` under the default slots and a workspace named `x64` after `SET PATH DBF ...\\DBF\\x64` -- same command, different name, because the NAME WAS A FUNCTION OF THE PATH SLOTS. R131 rules that a workspace owns its environment; leaf naming ran that dependency backwards. The same run also showed `workspace new mcc_x64` / `switch mcc_x64` / `workspace open dbf` leaving mcc_x64 with ZERO MEMBERS while thirteen areas opened in a workspace nobody named. R128 IS NOT REPEALED: \"we can also open two dir into two workspaces too\" (owner, 2026-08-26) survives verbatim as the AS form, together with its re-entry rule and its cross-root refusal; only the IMPLICIT name is withdrawn. WHY THIS NEEDED A SPEC AT ALL, and the part worth reading: THE DEFECT IS INVISIBLE TO AREA CONTENT. Under BOTH builds the opened table lands at the same slot holding the same value, because the allocator is asked for a free area of whatever workspace is CURRENT -- and under the old build OPEN had just made that a different workspace. So every arm that reads the opened table reads GREEN on both binaries, which is the AIF-148 shape -- a failed verb and a working verb reading identically -- arriving in a different subsystem three hours later. The discriminator has to ask WHICH WORKSPACE OWNS THE AREA, and the only instrument in this language that answers it is a SCOPED SAVE: save the workspace the person made, close, reload, and see how many areas come back. That is WAO_T5's shape, reused deliberately rather than reinvented. OJC_T1 IS THE DISCRIMINATOR and it prints a real .F. rather than a silence: under the fix OJCWS carries TWO areas, the reload fills 0 and 1, the ADD lands at 2 and slot 1 reads BBB; under the old build OJCWS carries ONE, the reload fills 0, the ADD lands at 1 and slot 1 reads CCC. OJC_T2 is the placement half and is WEAKER BY CONSTRUCTION, stated rather than implied: under the old build area 2 is never opened, so it may print NOTHING rather than .F. and arrive as a missing marker instead of a red one -- still a failure, but a different kind, and a reader should not count it as the same evidence as T1. OJC_T3 IS THE COUNTERWEIGHT and is the reason the fix cannot overshoot: a change that made EVERY open join the current workspace would pass T1 and T2 and be exactly as wrong as the defect, so T3 asserts the opposite direction on the same fixtures -- `AS <name>` must still put the opened table in a workspace of its own, so OJCWS2 comes back carrying ONE area and slot 1 reads CCC. T3 is GREEN ON BOTH BUILDS; it discriminates the OVERSHOOT, not the defect. OJC_G3 is likewise green on both and is NOT a discriminator -- it is there so a run where OPEN did nothing at all cannot be mistaken for a run where OPEN landed in the wrong workspace. WHAT THIS SPEC DOES NOT COVER, stated rather than implied: (a) THE ROOTS. R131 also wants the workspace to RECORD the directory it was opened from, and that is Q3 and still unruled -- WORKSPACES.dbf declares DBF_ROOT and IDX_ROOT only and has NO LMDB COLUMN AT ALL, so a durable answer for the third slot has nowhere to go. No arm here asserts a root, because nothing writes one. (b) DEFAULT HAS NO CATALOG IDENTITY. A bare OPEN now mints nothing, so the durable row that bare OPEN used to write is GONE for the thirteen tracked specs that use the bare form; they land in DEFAULT, which reports WS_ID (none yet). That is the trade R131 took knowingly and it is not tested here because no marker in this language can read a WS_ID. (c) the cross-root collision refusal, inherited untested from workspace_additive_open.dts. FIXTURE FRAGILITY, DISCLOSED: DBF/SANDBOX/OJCA, OJCB and OJCC are EMPTY DIRECTORIES and git does not track those, so a fresh clone will not have them -- the same standing gap WAOA/WAOB/WAOC, PKA/PKB and RPCA/RPCB already carry, inherited rather than introduced. NOT YET RUN AT THE TIME OF WRITING -- authored against the change in the same session, no green claimed; explicit-run until run twice, then promote. NOT YET RUN AGAINST THE PRE-CHANGE BINARY EITHER, which is the honest gap: WAO_T1 and MWXSHAKE both insist a discriminator is measured against the old build rather than reasoned about, and what exists here is the failing behaviour measured live plus an instrument borrowed from an arm that WAS measured both ways. Anyone stashing the R131 change should see OJC_T1 go red while OJC_G0/G1/G2/G3 and OJC_T3 stay green; if the guards red too, the fixture broke and the arms prove nothing either way. RUN AND PROMOTED 2026-08-29 ON TWO GREEN RUNS, and the clause above is LEFT STANDING because it was true when it was written. All SEVEN markers .T. both times -- OJC_G0/G1/G2/G3 and OJC_T1/T2/T3 -- with the L3 isolation arm reading six of six before and after and the production catalog at 269 rows on every read, so the spec minted nothing outside its bracket. THE TWO RUNS WERE OF TWO DIFFERENT BINARIES, cdc00895 dirty (Aug 29 2026 13:36:21) and 4fc51717 dirty (Aug 29 2026 14:05:53), which DIVERGES FROM NAV_NATURAL'S PRECEDENT of two runs of one binary and is stated rather than glossed: it is stronger evidence for stability across a rebuild and WEAKER evidence for run-to-run repeatability of one build, and a reader should know which of the two they are being handed. THE TRANSCRIPT CORROBORATES MORE THAN THE MARKERS DO. `WORKSPACE SWITCH: current handle 4 (OJCWS), depth 0, members 2` after the open is the ruling stated by the engine in its own words -- the workspace the person made COUNTING the opened table as its own -- and under the old build that line reads members 1. In the T3 half the counterweight says it as plainly from the other side: `WORKSPACE SAVE: workspace 5 (OJCWS2) ... 1 area(s). NOT saved: 1 open area(s) in other workspaces.` -- direct evidence that the AS-opened table sat somewhere else, which is stronger than the marker that infers it from where the reload puts the next ADD. IN-SUITE VERIFICATION HAS NOT HAPPENED AND IS THE NEXT STEP: both greens were EXPLICIT single-spec runs, which prove the spec works from a clean session and say nothing about order-independence when it inherits open areas and path slots from the spec before it. NAV_NATURAL had to demonstrate that rather than assume it, and so does this. NOTE FOR WHOEVER RUNS IT: this spec re-points only the DBF slot and inherits INDEXES and LMDB, which is safe today because it builds no containers -- but it is the same fixture omission recorded against MWXSHAKE section 5C, and it will stop being safe the moment an arm here needs an index. VERIFIED IN-SUITE 2026-08-29 ON THE PROMOTING BUILD (af6e9ea0 dirty, Aug 29 2026 14:12:25), and the clause above is LEFT STANDING because it was true when it was written. Run as the EIGHTEENTH and last spec of REGRESSION ALL: seven markers, all .T., full count, with the L3 isolation arm reading six of six at both ends and the production catalog at 269 rows before and after. ORDER-INDEPENDENCE IS DEMONSTRATED RATHER THAN ASSUMED -- it inherited NAV_NATURAL's session with the DBF, INDEXES and LMDB slots left on SANDBOX rather than the x64 they carry from a clean start, re-pointed only DBF in its own opening lines, and built its fixtures from a slate NAV_NATURAL's teardown had already cleared. THE SUITE-WIDE EFFECT OF R131 WAS MEASURED IN THE SAME RUN AND IS THE MORE USEFUL HALF: the new bare-OPEN message printed inside INDEX_X32 and RELJOIN -- 'WORKSPACE OPEN: opening into the CURRENT workspace 1 (DEFAULT)' -- which is the thirteen-spec blast radius this entry predicted, observed rather than argued, and both specs read green. So bare OPEN landing in DEFAULT costs those specs nothing they were asserting. PRE-CHANGE BINARY RUN, 2026-08-30 -- THE DEBT IS PAID AND THIS ENTRY'S OWN HEDGE TURNED OUT TOO PESSIMISTIC. Built cdc00895, the immediate parent of the change, in an isolated worktree; confirmed pre-change FROM SOURCE, the 'opening into the CURRENT workspace' message being absent from that tree. MEASURED: OJC_G0 through G3 .T., OJC_T1 .F., OJC_T2 .F., OJC_T3 .T. OJC_T2 WAS PREDICTED ABOVE TO ARRIVE AS A MISSING MARKER RATHER THAN A RED ONE, on the grounds that area 2 is never opened under the old build. It printed a real .F. -- SELECT 2 landed on an area with no file and ALLTRIM(MARK) = \"CCC\" still evaluated false. The hedge was the right thing to write and the outcome was better than it; both halves are worth keeping, because a spec author who never hedges is not being careful and one whose hedges are never tested is not being measured. THE TRANSCRIPT CARRIES THE THREE LINES THIS ENTRY PREDICTED IT WOULD. 'WORKSPACE OPEN: workspace 3  name OJCB  WS_ID 2  <- DBF/SANDBOX/OJCB' is THE LEAF NAMING CAUGHT IN THE ACT, a workspace named for the directory it was opened from, which is R131's thesis running backwards. 'WORKSPACE SWITCH: current handle 2 (OJCWS), depth 0, members 1' is the members-1-versus-members-2 discriminator this entry named in advance. And 'NOT saved: 1 open area(s) in other workspaces.' -- cited above as evidence in the T3/AS half -- fires in the T1 half too on this build, which is the defect stating itself from the other side: the bare OPEN also put the table somewhere else. CATALOG FIGURE CORRECTED: the production catalog is 271 rows, not the 269 recorded above -- see the WSENV entry.",
        true,   // PROMOTED 2026-08-29 -- two green runs, seven markers each, on two different binaries; VERIFIED IN-SUITE (see description)
        true  // mints: NEW x2, OPEN..AS, SAVE x2 -- bracket it
    },
    {
        "WSENV",
        "workspace_owns_its_environment.dts",
        "A WORKSPACE OWNS ITS ENVIRONMENT (R131, owner ruling 2026-08-29; sections 1, 7 and 11). The three path slots DBF, INDEXES and LMDB were GLOBAL and WORKSPACE SWITCH moved MEMBERSHIP without moving them, so with two systems open a table in one resolved its container under the other. MEASURED 2026-08-29 and it is R131's founding defect: MCC's STUDENTS answered `openCdx: LMDB env missing: ...SYSTEMS\\CASCADE_ERP\\LMDB\\STUDENTS.cdx.d` because Cascade had been opened last -- both systems stayed READABLE, and what broke was anything that had to RESOLVE a container or an LMDB env. The slots are now STAMPED on the workspace and SWITCH restores them. THE FIXTURE IS TWO TABLES WITH THE SAME NAME IN TWO ROOTS, DIFFERENT CONTENT, AND THAT IS THE WHOLE TRICK. An arm that opens a table present in only one directory CANNOT GO RED when the slot is wrong: the open fails, the area is empty, and a marker over a closed area PRINTS NOTHING rather than a verdict -- USE_AGAIN established that over three cuts and it is the single most repeated trap in this file. With RSPT.dbf in BOTH roots a wrong slot opens the WRONG TABLE and the marker reads .F. A failure has to be able to speak. RSE_T1 IS THE DISCRIMINATOR: build A and B by the owner's sanctioned sequence (NEW / SWITCH / SET PATH / OPEN), switch back to A, and open WITHOUT setting the path again. Under the fix A's slots are restored and RSPT reads AAA; before it the DBF slot is still B's and the same filename opens out of the wrong root. RSE_T2 IS THE COUNTERWEIGHT and is the reason the fix cannot overshoot -- a change that simply PINNED the slots to the first workspace would pass T1 and be exactly as wrong, so T2 asserts the opposite direction on the same fixtures. RSE_T3/T4 COVER Q1'S EXPLICIT CLAUSE, `SET PATH <slot> <value> IN <ws-or-handle>`, and they are TWO CLAIMS BECAUSE ONE IS NOT ENOUGH: the session must NOT move (T3, read by opening in the workspace you are standing in) and the binding must have LANDED on the named workspace (T4, proven by switching to it and opening with no SET PATH). An implementation that silently did nothing would pass T3 alone. RSE_T5 IS THE MISORDERING HAZARD R131 sec 7 exists to answer -- NEW then SET PATH then SWITCH binds the OLD workspace, and the remedy is to NAME the target rather than rely on standing in it. `IN` IS ALREADY THE HOUSE WORD for targeting something other than current (SET ORDER TAG ... IN <alias>, USE ... IN <n>); both of those take AREAS, and after SET PATH it can only mean a workspace because a path has no per-area meaning. WHAT THIS SPEC DOES NOT COVER, stated rather than implied: (a) THE DURABLE HALF. Whether a workspace's roots are written through to WORKSPACES.dbf is R131 sec 11.8 and is UNRULED, so nothing here reads the catalog and this spec asserts only the LIVE stamp. DBF_ROOT and IDX_ROOT are still written from the SESSION slot at birth and at SAVE, exactly as before. (b) INDEXES AND LMDB. All three slots move as a set -- there is deliberately no per-slot setter on the membership table, because a half-stamped workspace resolves tables under one system and indexes under another, which IS the founding defect -- but every arm here reads through the DBF slot, because a marker is a field-value comparison and this language has no marker that can read where a container resolved. The other two are covered by construction and not by assertion. (c) LMDB IS DERIVED (owner, 2026-08-29: 'lmdb is not used in v32, it is not used in vdisks, when we do need lmdb files we can regenerate them'), so it has NO durable column and never will; it rides the live stamp only. (d) DEFAULT. It is stamped LAZILY, on the way OUT of it, because it is built inside xbase before any command runs -- and the ORDER is load-bearing: stamping it as a TARGET instead would capture whatever the workspace being LEFT had set, so DEFAULT would inherit a foreign environment the first time anyone switched back. No arm asserts that; it is argued in the source at the SWITCH branch. SWITCH ANNOUNCES EVERY SLOT IT MOVES, deliberately: this is the one part of R131 that can change what an EXISTING script does, and a run where a spec breaks because its slots moved under it should say so in its own transcript rather than leave a reader inferring it from a failed open three screens later. FIXTURE FRAGILITY, DISCLOSED: DBF/SANDBOX/R131A and R131B are EMPTY DIRECTORIES and git does not track those, so a fresh clone will not have them -- the same standing gap WAOA/WAOB, OJCA/OJCB, PKA/PKB and RPCA/RPCB already carry, inherited rather than introduced. NOT YET RUN AT THE TIME OF WRITING, and NOT YET RUN AGAINST THE PRE-CHANGE BINARY: authored against the change in the same session, no green claimed. Anyone stashing R131 should see RSE_T1, T2, T4 and T5 go red while RSE_G0 through G3 stay green; if the guards red too, the fixture broke and the arms prove nothing either way. PROMOTED TO THE DEFAULT SUITE 2026-08-29, AND THE FIRST TWO OF ITS THREE GREEN RUNS DID NOT COUNT. RSE_T3 WAS BLIND. It was the only USE in the file not preceded by a SWITCH or a CLOSE, so T2's open was still sitting in area 0 and the USE answered 'already open in current area 0' -- the marker then read BBB off a cursor the IN clause had never touched, and would have printed .T. whether or not the clause wrongly moved the session slot. TWO GREENS OVER AN ARM THAT COULD NOT GO RED. That is the AIF-148 shape (a failed open and a working open reading identically) inside the spec whose own header warns that a failure has to be able to speak; the fixture design was sound and the SEQUENCING defeated it in one place. Remedy is one CLOSE, and the transcript now reads 'Closed.' then 'Opened RSPT' at T3. THE TRANSFERABLE RULE: A USE NOT PRECEDED BY A SWITCH OR A CLOSE IS NOT AN OPEN -- the other eight arms were checked against it rather than assumed, and all eight print 'Opened'. QUALIFYING RUNS ARE THE THREE AFTER THAT FIX: wscat_run_110, 111 and 112, all 9/9, over TWO PROCESS STARTS (110 its own, 111 and 112 sequential in one session -- three runs but two cold starts, said plainly because a repeat inside one process is the weaker of the two readings). L3 read the production catalog at 269 rows before and after every one. THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, NOT THE SOAK ALONE -- the RELSCOPE2 precedent. Q1's explicit clause, SET PATH <slot> <path> IN <ws-or-handle>, appears in EXACTLY ONE FILE in the whole .dts corpus and that file is this one (measured 2026-08-29 by grepping the corpus for the form; one hit). While this spec stayed explicit-run, the entire IN branch of cmd_setpath_command.cpp -- resolve the token, compute touches_session, fill a half-stamped Entry from the session before writing one slot, set_roots -- could be rewritten and pass all eighteen default specs in silence. The RESTORE half is nearly as thin: the R131 announce fired FOUR TIMES inside MWXSHAKE on the 2026-08-29 suite run, so the behaviour is OBSERVED in the default suite and ASSERTED NOWHERE IN IT -- MWXSHAKE addresses tables by name and claims nothing about the slots. THE COST, STATED: 2 catalog rows per run, both into the per-run SCRATCH catalog under the gitignored TMP slot because this entry is flagged mints_catalog, so the suite goes 26 to 28 scratch rows a run and ZERO rows to the production catalog. Cheapest bracketed spec in the suite; MWXSHAKE alone is 16. STILL OWED AND NOT CLAIMED: this spec has never been run against a PRE-CHANGE binary. The paragraph above predicts RSE_T1/T2/T4/T5 red with the guards green, and that prediction is still a prediction. VERIFIED IN-SUITE 2026-08-29 ON THE PROMOTING BUILD (dffbf8af dirty, Aug 29 2026 16:47:40), and every clause above is LEFT STANDING because it was true when it was written. Run as the NINETEENTH and last spec of REGRESSION ALL: nine markers, all .T., full count -- RSE_G0 through G3 and RSE_T1 through T5 -- with the L3 isolation arm reading six of six at both ends and the production catalog at 269 rows before and after, so the spec minted nothing outside its bracket. Its scratch catalog was wscat_run_119; the suite's brackets ran 113 through 119. THE BLIND ARM WAS RE-READ IN-SUITE RATHER THAN ASSUMED FIXED, because that is the whole reason this entry needed a third reading: T3 printed `bound to workspace 29 (RSEWSA); the session's own slots are unchanged.` then `Closed.` then `Opened RSPT (v64) : Record count 1` -- a real close and a real open, in the suite, at the one place where two earlier greens came off a cursor nothing had touched. ORDER-INDEPENDENCE IS DEMONSTRATED RATHER THAN ASSUMED, which is the only thing an in-suite run can prove that a single-spec run cannot: WSENV inherited OPENJOIN's session with the DBF slot left on DBF/SANDBOX/OJCC rather than the x64 it carries from a clean start, re-pointed only DBF in its own opening lines, and its closing WORKSPACE CLOSE reported zero areas -- so it neither depended on what it inherited nor left anything for the next spec, and the single-slot re-pointing noted against MWXSHAKE section 5C is confirmed harmless HERE while remaining the same standing fixture omission everywhere. MWXSHAKE'S R131 ANNOUNCE LINES FIRED AGAIN and MWXSHAKE stayed green. The COUNT DIFFERS from the four recorded earlier in this entry -- three switch points this run -- and it is REPORTED RATHER THAN RECONCILED, because nothing asserts that number and I have not measured why it moved. A count is a fact about a loop until something declares what it should be. WHAT THIS RUN STILL DOES NOT SETTLE, unchanged and restated so the promotion does not read as closure: this spec has never been run against a PRE-CHANGE binary, so RSE_T1/T2/T4/T5 going red with the guards green is STILL A PREDICTION. In-suite green on the promoting build is evidence the spec is stable and order-independent; it is not evidence that it can fail. PRE-CHANGE BINARY RUN, 2026-08-30. THE DEBT THIS ENTRY RECORDED AS STILL OWED IS PAID, AND IT COST THIS ENTRY ONE OF ITS OWN CLAIMS. Built ae8fbc9d -- the immediate parent of the change -- in a detached worktree under tmp/ with its own build dir and its own data tree, so nothing here could reach the production catalog. PRE-CHANGE WAS CONFIRMED FROM SOURCE RATHER THAN FROM A COMMIT HASH: workspace_roots_bind_from_slots/_apply_to_slots are absent from workarea_util.cpp and cmd_setpath_command.cpp has no IN branch at all on that tree. THE PREDICTION ABOVE SAYS T1, T2, T4 AND T5 GO RED. MEASURED: T1 .F., T2 .T., T3 .F., T4 .F., T5 .F., G0 through G3 all .T. T2 CAME BACK GREEN. THE ENTRY CONTRADICTED ITSELF AND THE MEASUREMENT SETTLED IT. Read up: 'RSE_T2 IS THE COUNTERWEIGHT and is the reason the fix cannot overshoot.' Read down: T2 listed among the four expected reds. Both sentences are in this entry and they cannot both be right. The counterweight reading is the correct one, and the reason is structural rather than incidental: on the pre-change build the global DBF slot is simply left wherever it was last set, which is B, and B is exactly what T2 expects. T2 IS GREEN ON BOTH BUILDS BY CONSTRUCTION -- it discriminates the OVERSHOOT, a fix that pinned the slots to the first workspace, and never the defect. Same species as OJC_T3, which its own entry labels correctly. So this spec has THREE discriminators (T1, T4, T5), not four. WORSE, AND THE PART WORTH READING: T1 AND T2 WERE BOTH BLIND ON THAT BUILD. Each answered 'already open in current area 0' and NOTHING OPENED. T1 still printed .F., but by reading the stale cursor G3 left in area 0 -- not by opening out of the wrong root, which is what the T1 paragraph above describes. A RED FOR THE WRONG REASON IS NOT THE EVIDENCE AN ENTRY CLAIMS IT IS. THE TRANSFERABLE RULE WRITTEN ONE DAY EARLIER WAS TOO LOOSE, AND THIS IS THE THIRD RECURRENCE OF THE SAME SHAPE. It said A USE NOT PRECEDED BY A SWITCH OR A CLOSE IS NOT AN OPEN, and on that reading T3 was the only offender because T1/T2/T4/T5 all follow a SWITCH. On the pre-change binary all four were blind anyway. A SWITCH THAT MOVES NO SLOT CHANGES NOTHING ABOUT WHAT THE NAME RESOLVES TO. The rule in its real form: A SWITCH ONLY COUNTS AS AN OPEN WHEN IT CHANGES WHAT THE NAME RESOLVES TO, AND A SPEC CANNOT ASSUME THE BUILD UNDER TEST IS ONE WHERE IT DOES. Note how the first version failed: the other eight arms WERE checked against it, honestly and deliberately, and all eight printed 'Opened' -- ON THE FIXED BINARY, the one build where a SWITCH does move the slot. THE RULE WAS VERIFIED ON THE ONLY BUILD WHERE IT HAPPENS TO HOLD. REMEDY, AND IT IS STRUCTURAL RATHER THAN A RULE TO REMEMBER: every USE in T1 through T5 is now preceded by a CLOSE, which a reader checks by inspection. G2 and G3 are the two deliberate exceptions and are safe on any build because each is preceded by an EXPLICIT SET PATH, which changes resolution regardless of what SWITCH does. RE-MEASURED WITH THE AMENDED SPEC, SAME PRE-CHANGE BINARY: T1 .F. now printing 'Closed.' then 'Opened RSPT (v64) : Record count 1' before the marker -- A REAL OPEN OF THE WRONG TABLE, the mechanism this entry has always described and never until now performed. T2 .T. off a real open rather than a stale cursor. T3/T4/T5 .F., guards green. AND ON THE FIXED BINARY the amended spec still reads 9/9 with the four added CLOSEs visible in the transcript and no arm moved, so the change buys evidence on the old build and costs nothing on the new one. ONE STEWARD MISPREDICTION RECORDED: T3 was predicted GREEN-FOR-THE-WRONG-REASON on the theory that the old parser would reject the IN clause and so leave the session alone. It went RED, because the old SET PATH SWALLOWED 'IN RSEWSA' INTO THE PATH STRING -- 'SETPATH: DBF = ...\\R131A IN RSEWSA' with nothing but 'warning: path does not exist' -- a silent misparse rather than a usage error. A HOUSE DOCTRINE NARROWED BY THE SAME RUNS: 'a marker over a closed area PRINTS NOTHING rather than a verdict' (USE_AGAIN, three cuts) is quoted in this spec's own header as the reason for the two-tables-same-name fixture. Four counter-examples were measured on 2026-08-30 -- OJC_T2 over an empty area 2, and RSE_T3/T4/T5 each after 'USE: nothing was opened, and area 0 is untouched' -- all four printing .F. The fixture design is still right, because a wrong slot opening the WRONG TABLE beats an open that merely fails; the stated reason for it is narrower than the header claims. CATALOG FIGURE CORRECTED: the production catalog is 271 rows, not the 269 recorded above. On 2026-08-30 this spec was run against the main tree through DOTSCRIPT rather than REGRESSION WSENV -- DOTSCRIPT IS NOT BRACKETED, because CatalogBracket is a suite facility -- and minted WS_ID 270 and 271, both immediately destroyed and so SUPERSEDED with no live head left behind. The mints-nothing-outside-its-bracket claim is unaffected and the figure a future L3 arm will read is not. Steward error, recorded rather than quietly corrected.",
        true,   // PROMOTED 2026-08-29 -- three post-fix green runs (110/111/112), two process starts; VERIFIED IN-SUITE (see description)
        true  // mints: NEW x2 -- bracket it
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

// Resolves a script TOKEN, not a spec. Split out 2026-08-28 so the L3
// isolation arm -- which is deliberately NOT a registered spec -- resolves
// through the same SCRIPTS-slot path every spec does. A second resolver for
// the arm would be a second answer to "where do scripts live", which is the
// shape this lane keeps finding.
std::filesystem::path resolve_script_token(const std::string& token)
{
    namespace fs = std::filesystem;

    const std::string script = normalize_script_separators(token);
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

std::filesystem::path resolve_regression_script_path(const RegressionSpec& spec)
{
    return resolve_script_token(spec.script);
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
        << "  - EVERY run -- ALL or a single spec -- is bracketed by the L3 catalog\n"
        << "    isolation arm, which reads the PRODUCTION workspace catalog before\n"
        << "    and after and proves its own detector first. Count its markers: an\n"
        << "    errored marker PRINTS NOTHING rather than going red.\n"
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

// ---------------------------------------------------------------------------
// AIF-078 L2 -- THE CATALOG BRACKET.
//
// A spec flagged mints_catalog runs with the WORKSPACES slot pointed at a
// per-run scratch root, so its WORKSPACE NEW rows land in a throwaway catalog
// and PRODUCTION IS NOT WRITTEN. Measured cost before this landed: exactly ten
// rows per REGRESSION ALL, 252 -> 262 on 2026-08-28, from four specs.
//
// RAII, AND THAT IS THE REQUIREMENT RATHER THAN THE STYLE. The plan asked for
// a restore that survives a throw, because L0 measured what the alternative
// costs: a mistyped path was ACCEPTED -- SETPATH validates non-blockingly --
// and the session ran several commands redirected at a garbage directory.
// Nothing was damaged only because WORKSPACE NEW refused correctly. The engine
// behaved well; that is not a substitute for an unconditional restore. A
// destructor runs on the normal path, on a throw, and on an early return, and
// there is no fourth path for someone to forget.
//
// THE SCRATCH ROOT IS PER RUN, NOT PER SESSION. l0probe and l1verify both use
// a fixed directory and say so; that is fine for a probe run by hand and wrong
// for a suite, because two sessions running REGRESSION ALL at once would share
// one catalog and mint into each other. Each bracket CLAIMS its own directory,
// so concurrent sessions cannot collide and successive specs in one run cannot
// inherit each other's rows.
//
// CORRECTED 2026-08-28: this paragraph used to end "the name carries the
// process id and a monotonic counter". It never did -- that was the first
// cut's ::_getpid() spelling, withdrawn before the commit for the reason the
// next block gives, and the sentence survived the code it described. Two
// statements of one mechanism, one of them false, three paragraphs apart in a
// single comment: AIF-143's shape, in prose rather than in declarations.
//
// ensure_catalog() calls fs::create_directories(catalog_dir()), so the root
// does not have to exist first -- measured 2026-08-28. SETPATH will still warn
// that it does not exist. That warning is EXPECTED here and is the same one a
// typo produces, which is a defect recorded against SETPATH and not fixed by
// this change.
// UNIQUENESS BY CLAIMING THE DIRECTORY, NOT BY NAMING THE PROCESS.
//
// The obvious spelling is <tmp>/wscat_run_<pid>_<n>, and the first cut wrote
// exactly that -- with ::_getpid(), which is Windows-only and would not have
// survived the first portable build. The tree ALREADY has a portable answer,
// dottalk::locks::current_pid() with the right #ifdef, but it sits in an
// ANONYMOUS NAMESPACE in lock_cleanup.cpp and is not exported. Copying its
// #ifdef here would put a second answer to "what is my process" in the tree,
// which is the shape this project keeps finding and paying for.
//
// So this does not ask. fs::create_directory returns TRUE only if THIS CALL
// created the directory, and FALSE if it already existed -- so the first n
// that returns true is a root nobody else holds. Two processes racing the same
// n cannot both win. That is stronger than a pid-derived name, which is unique
// only because pids happen to be, and it needs no platform knowledge at all.
//
// The roots are NOT deleted on the way out. They are the evidence of what a
// bracketed spec minted, they live under the TMP slot which is gitignored
// scratch, and deleting them would throw away the only record of a run that
// went wrong. Sweeping old ones is a follow-up, not this change.
static std::filesystem::path claim_scratch_root()
{
    const std::filesystem::path base =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP);

    std::error_code ec;
    std::filesystem::create_directories(base, ec);

    for (unsigned n = 1; n < 100000; ++n) {
        const std::filesystem::path cand =
            base / ("wscat_run_" + std::to_string(n));
        ec.clear();
        if (std::filesystem::create_directory(cand, ec) && !ec)
            return cand;
    }

    // Cannot happen short of 100k undeleted roots. Named rather than silent,
    // because a bracket that quietly reused somebody's root would produce
    // exactly the cross-contamination it exists to prevent.
    std::cout << "REGRESSION: WARNING -- could not claim a fresh scratch "
                 "catalog root under " << base.string()
              << "; falling back to a shared one.\n";
    return base / "wscat_run_overflow";
}

// ONE PLACE KNOWS HOW TO PUT THE SLOT BACK. Two things now move the WORKSPACES
// slot inside a suite run -- the per-spec bracket below, and the L3 arm, which
// moves it in DotScript. Both need the same unconditional restore, and two
// copies of a restore is how one of them drifts. So the restore lives here and
// is composed into the bracket rather than duplicated beside it.
//
// The saved value is captured in the MEMBER INITIALISER, before anything in
// any owner's constructor body can move the slot, and the destructor takes no
// condition: restoring a slot that never moved is a no-op, while skipping a
// restore that was needed is the defect. The message text is unchanged from
// the L2 commit on purpose -- transcripts and the AIF-078 record cite it.
class WorkspacesSlotGuard {
public:
    WorkspacesSlotGuard()
        : saved_(dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES))
    {
    }

    ~WorkspacesSlotGuard()
    {
        dottalk::paths::set_slot(dottalk::paths::Slot::WORKSPACES, saved_);
        std::cout << "REGRESSION: catalog restored to " << saved_.string() << "\n";
    }

    const std::filesystem::path& saved() const { return saved_; }

    WorkspacesSlotGuard(const WorkspacesSlotGuard&) = delete;
    WorkspacesSlotGuard& operator=(const WorkspacesSlotGuard&) = delete;

private:
    std::filesystem::path saved_;
};

class CatalogBracket {
public:
    explicit CatalogBracket(const std::string& spec_name)
    {
        const std::filesystem::path scratch = claim_scratch_root();
        dottalk::paths::set_slot(dottalk::paths::Slot::WORKSPACES, scratch);

        std::cout << "REGRESSION: catalog BRACKETED for " << spec_name << "\n"
                  << "  production catalog : " << guard_.saved().string()
                  << "  (untouched)\n"
                  << "  scratch catalog    : " << scratch.string() << "\n";
    }

    CatalogBracket(const CatalogBracket&) = delete;
    CatalogBracket& operator=(const CatalogBracket&) = delete;

private:
    // Declared FIRST so it is constructed FIRST: it must read the production
    // root before the constructor body redirects the slot, and it must be
    // destroyed LAST.
    WorkspacesSlotGuard guard_;
};

void run_regression_script(DbArea& area, const RegressionSpec& spec)
{
    const std::filesystem::path resolved = resolve_regression_script_path(spec);

    std::cout << "REGRESSION: running " << spec.name << "\n"
              << "  Script: " << spec.script << "\n"
              << "  Resolved: " << resolved.string() << "\n";

    std::ostringstream dotscript_line;
    dotscript_line << '"' << resolved.string() << '"';
    std::istringstream dotscript_args(dotscript_line.str());

    // The bracket lives in the ONE place a spec is run, so a new caller cannot
    // acquire a spec and forget it. Scoped to the DOTSCRIPT call and nothing
    // else -- resolve_regression_script_path above reads the SCRIPTS slot,
    // which this must not disturb.
    if (spec.mints_catalog) {
        CatalogBracket bracket(spec.name);
        cmd_DOTSCRIPT(area, dotscript_args);
        return;
    }

    cmd_DOTSCRIPT(area, dotscript_args);
}

// ---------------------------------------------------------------------------
// AIF-078 L3 -- THE ISOLATION ARM, WIRED AROUND THE SUITE INSTEAD OF AROUND
// ITSELF.
//
// The arm has existed and been red-capable since 785eb9a5c, and as a .dts it
// could only bracket its OWN execution: run it and it measures the two seconds
// it was running for. The measurement condition 2 actually asks for is around
// the SUITE, and the only place that can be taken is here.
//
// THE ARM IS THE AUTHORITY AND THIS CODE IS NOT. The obvious alternative was
// to read the catalog high-water in C++ before and after the loop and compare
// two numbers. That would be a SECOND declaration of a measurement the arm
// already owns, in a different language, free to drift from it -- and the arm's
// instrument is not naive: it is the high-water WS_ID rather than a row count,
// because RECCOUNT()/RECNO()/FOUND() render EMPTY in a marker, and it proves
// its own detector in scratch before it reports on production. So this runs the
// arm and stays out of the way. It prints no number of its own.
//
// IT IS DELIBERATELY NOT A REGISTERED SPEC. Registered, it would run inside the
// loop like any other spec, bracket only itself, and pass trivially while
// measuring nothing -- the exact false green the plan warned about.
//
// A MISSING ARM IS REPORTED, LOUDLY. If the script is not on disk this says the
// run is UNMEASURED rather than saying nothing. "Nothing went wrong" and
// "nothing was checked" must never print the same way (AIF-118), and an absent
// instrument is the cheapest way to get a suite that reports peace forever.
//
// THE AFTER PASS IS NOT RAII, and that is a choice rather than an oversight.
// If a spec throws, the suite unwinds and no AFTER pass runs -- so an aborted
// suite yields NO isolation verdict instead of a verdict taken mid-unwind.
// Running a DotScript from a destructor during stack unwinding is how a second
// throw becomes std::terminate, and a measurement is not worth that.
static const char* const kIsolationArmScript = "l3_catalog_isolation_arm.dts";

void run_isolation_arm(DbArea& area, const char* phase)
{
    namespace fs = std::filesystem;

    const fs::path resolved = resolve_script_token(kIsolationArmScript);

    std::cout << "\nREGRESSION: L3 CATALOG ISOLATION ARM -- " << phase
              << " the suite\n"
              << "  Script  : " << kIsolationArmScript << "\n"
              << "  Resolved: " << resolved.string() << "\n";

    std::error_code ec;
    if (!fs::exists(resolved, ec) || ec) {
        std::cout << "  NOT RUN -- the arm is not on disk at that path.\n"
                     "  THIS IS NOT A PASS. Catalog isolation is UNMEASURED for\n"
                     "  this run. A missing instrument and a green one must not\n"
                     "  read alike.\n";
        return;
    }

    std::cout << "  READ RULE: six markers must PRINT and all six read .T.\n"
                 "  An errored marker prints NOTHING rather than going red, so\n"
                 "  COUNT them. If L3_D1 is .F. the detector is blind and L3_G1\n"
                 "  means nothing -- never credit G1 without D1.\n";

    // The arm moves the WORKSPACES slot itself, in DotScript, and puts it back
    // by hand. This guard is the backstop: a script that aborts between its
    // redirect and its restore would otherwise hand the REST OF THE SUITE a
    // moved catalog slot, which is the failure L2 exists to prevent, arriving
    // through the instrument built to detect it.
    WorkspacesSlotGuard guard;

    std::ostringstream dotscript_line;
    dotscript_line << '"' << resolved.string() << '"';
    std::istringstream dotscript_args(dotscript_line.str());
    cmd_DOTSCRIPT(area, dotscript_args);
}

// AN EXPLICIT RUN GETS THE SAME INSTRUMENT THE SUITE GETS.
//
// `REGRESSION ALL` has carried the arm since cb92ef310. A single
// `REGRESSION RUN <name>` did not, and that is the command a developer uses to
// SOAK a spec -- so the one path where a spec is being evaluated for promotion
// was the one path with no measurement. A spec that wrote production during a
// soak looked exactly like one that did not.
//
// THE ARM IS DELIBERATELY *NOT* GATED ON spec.mints_catalog, and this is the
// whole point rather than a detail. 19b1928c4 fixed ten specs that mint and
// were flagged false; the flag is set BY HAND from a reading of three verbs,
// and a reader who knows two of them under-flags in the direction of writing
// production. Gate the DETECTOR on the same flag whose correctness it exists
// to verify and it cannot fire on the only case that matters -- a spec that
// mints and is not flagged. That is this project's recurring defect shape, and
// it would have been introduced here by an optimisation that looked obvious.
//
// So the arm runs around EVERY explicit run, including specs believed inert.
// The cost is one directory erase, two scratch mints and two production reads;
// REGRESSION RUN is an interactive act, not a hot loop.
void run_regression_script_measured(DbArea& area, const RegressionSpec& spec)
{
    run_isolation_arm(area, "BEFORE");
    run_regression_script(area, spec);
    run_isolation_arm(area, "AFTER");
}

void run_regression_default_suite(DbArea& area)
{
    // Plan condition 2: "REGRESSION ALL leaves PRODUCTION unchanged." The arm
    // reads production's high-water before and after everything below, and the
    // BEFORE pass is also what proves the detector is alive on this build.
    run_isolation_arm(area, "BEFORE");

    for (const auto& spec : kRegressionSpecs) {
        if (!spec.in_default_suite) continue;
        run_regression_script(area, spec);
    }

    run_isolation_arm(area, "AFTER");
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
            run_regression_script_measured(area, *spec);
        }
        return;
    }

    if (const RegressionSpec* spec = find_regression_spec(op)) {
        run_regression_script_measured(area, *spec);
        return;
    }

    std::cout << "REGRESSION: unknown option or regression '" << arg1 << "'.\n";
    print_regression_list();
}
