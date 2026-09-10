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
//   REGRESSION delegates script execution to DOTSCRIPT. Selected specs also
//   attach executable transcript validators that turn marked evidence into a
//   final PASS/FAIL and canonical error status.
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

#include <algorithm>
#include <array>
#include <optional>
#include <cstddef>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>

#include "identity/identity_admin.hpp"
#include <streambuf>
#include <string>
#include <system_error>   // std::error_code for the PKDURABLE pre-clear
#include <utility>
#include <vector>

#include "common/path_state.hpp"
#include "cli/path_resolver.hpp"
#include "shell_api.hpp"
#include "textio.hpp"
#include "xbase_error_context.hpp"
#include "xbase/trigger_hooks.hpp"   // AIF-087 M2c: the veto arm registers a BEFORE callback
#include "cli/output_router.hpp"     // AIF-087 M2c: catalog messages bypass std::cout

using xbase::DbArea;

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

enum class RegressionValidator {
    None,
    SqlselSelectOracleV1,
    SqlselJoinOracleV1,
    SqlselJoinEdgesV1,
    SqlselLeftJoinOracleV1,
    SqlselJoinFamilyV1,
    SqlselSetOperationsV1,
    SqlselAggregatesV1,
    SqlselSubqueriesV1,
    SqlselAdvancedJoinV1,
    SqlselDmlTransactionV1,
    SqlselWorkspaceScopeV1,
    SqlmodeSmokeV1,
    SqlselBufferVisibilityV1,
    EvaldiffV1,
    CountListVerboseV1,
    DefFamilyV1,
    PkPolicyV1,
    PkDurabilityV1,
    VarcharAreaResetV1
};

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

    // Optional executable transcript contract. Most historical specs remain
    // DotScript-only; selected oracle specs name the validator that turns
    // their marked output into a verdict instead of relying on visual review.
    RegressionValidator validator = RegressionValidator::None;

    // TRUE means THIS SPEC'S EVIDENCE IS ON THE ROUTED CHANNEL, so its validator
    // is handed a SET ALTERNATE capture instead of the std::cout tee. See the
    // AlternateCapture comment above run_regression_script for why the two are
    // different instruments and why the alternate file is the superset.
    //
    // SILENCE SAYS FALSE AND THAT IS THE SAFE ANSWER HERE, unlike mints_catalog
    // above: a spec that does not need the routed channel is not harmed by the
    // tee, and the failure mode of a WRONGLY FALSE flag is loud -- an empty
    // block or a missing fragment -- not silent. The failure mode of a wrongly
    // TRUE one is also loud: the FORMULA markers would still be there, so the
    // block still resolves. Neither direction can go quietly green.
    //
    // Set it on any spec that asserts on a MESSAGE rather than on DATA ROWS --
    // an error, a refusal, a warning, a diagnostic, or the output of a command
    // that prints through cli::cmdout / OutputRouter::out() rather than through
    // `?` and FORMULA.
    bool capture_routed_channel = false;

    // ORDER IS LOAD-BEARING AND THIS MEMBER IS LAST ON PURPOSE. mints_catalog
    // could be added in the middle because it carries a default AND every entry
    // that stopped short of it was unaffected -- but entries DO initialise
    // `validator` and `capture_routed_channel` positionally, so a new member
    // placed above either of those silently shifts an enum into a bool for
    // every one of them. Caught at compile time here; it would not have been
    // caught by reading.
    // AIF-156, OWNER RULING 2026-09-07 ("3 -- my authority for the test").
    // TRUE means this spec runs as kShellIdentity instead of the boot identity,
    // so it can reach a `!` shell-out. IT IS THE SIXTH MEMBER AND IT CARRIES A
    // DEFAULT for the same reason mints_catalog does: aggregate initialisation
    // value-initialises a member no initialiser reaches, but WITHOUT the
    // '= false' every other entry becomes a -Wmissing-field-initializers hit.
    //
    // WHY A PER-SPEC OPT-IN AND NOT A SUITE-WIDE ONE. `!` is std::system() --
    // arbitrary shell. Eighty specs run in this suite and any of them could
    // later grow a `!` line; a blanket assumption would hand shell access to
    // all eighty on every run. This flag is set on exactly one spec, and the
    // identity is assumed for the DURATION OF THAT SPEC and restored after.
    //
    // IT DOES NOT BYPASS THE SECOND GATE. cmd_bang.cpp asks identity FIRST and
    // cli::security::authorize_external_process SECOND, and the second reads
    // the off-by-default host-command policy that only the operator sets. So a
    // flagged spec still cannot run a shell unless the owner has separately
    // enabled host commands for that session. Both gates survive; this flag
    // moves only the first, and only for one spec.
    bool requires_host_shell = false;
};

// SIZE IS HAND-MAINTAINED. Adding a row without bumping this count is a hard
// compile error ("too many initializers"), which is the safe failure -- but it
// is a recurring papercut: it happened when CNXLIVE was added on 2026-07-31.
// Bump it when you add a regression.
constexpr std::array<RegressionSpec, 81> kRegressionSpecs{{
    {
        "COUNT_LIST_VERBOSE",
        "count_list_verbose_regression.dts",
        "COUNT LIST and COUNT VERBOSE (owner ruling 2026-09-04): the two behaviours "
        "the retired `SQL` scanner had and COUNT did not, refitted onto "
        "cli::scan::collect_selected_recnos. THE POINT IS NOT THE OUTPUT, IT IS THE "
        "ROWSET. `SQL` carried a private DelMode and a raw skip-walk that never "
        "consulted SET FILTER, so `SQL COUNT FOR <x>` and `COUNT FOR <x>` could "
        "return different numbers over the same table and neither said so. Five-row "
        "self-bootstrapping SANDBOX fixture, erased at both ends. CLV_T3 IS THE "
        "DISCRIMINATOR and the rest support it: with SET FILTER TO MAJOR = \"CSCI\" "
        "the logical rowset is three rows and two match, so `scanned 3, matched 2` is "
        "a reading only a filter-honouring implementation produces -- the retired "
        "scanner would have reported the unfiltered five. The unfiltered arm above it "
        "reads the same either way and is there to localize a failure to the filter "
        "rather than the fixture. CLV_T0 is a NON-REGRESSION arm: the fold must not "
        "change what a bare COUNT prints, so the block is required to be EXACTLY one "
        "line, which no fragment check could see. CLV_T4 asserts the reserved verb "
        "answers with direction instead of `unknown command` AND does not scan -- "
        "enforced by counting scanned/matched summaries in the whole transcript, "
        "because a reserved verb that still counted would otherwise pass every "
        "fragment above. NOT PROMOTED: explicit-run until it has soaked.",
        false,
        false,
        RegressionValidator::CountListVerboseV1,
        true                       // evidence is COUNT's own output: routed channel
    },
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
    // basis is pinocchio\wal_phaseA_proof.dts (throwaway table, ERASEd at end) -- and
    // THAT file is TRACKED as of 2026-09-07, because a provenance claim a reader cannot
    // open is not a provenance claim.
    //
    // BOTH COPIES OF commit_rollback_test.dts WERE RETIRED 2026-09-07 under OI-019:
    // dottalkpp/data/scripts/ and .../suites/, moved to scripts/_to_delete/. Neither was
    // ever tracked, so nothing left the repository. Read the sentence above as an
    // EPITAPH and NOT as a pointer -- it records what this entry replaced, and a reader
    // should not expect to find the file. Verified before retiring: both opened with
    // `select students` against a table they did not create, and both had the terminal
    // verb commented out, so run standalone they measured nothing at all.
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
        "Runtime DEF-family testbed: DEFCMD/DEFFN/EXAMPLE define-invoke-arg-compose-list-remove, session-only, no rebuild (RUNTIME_DEF_FAMILY lane). Self-bootstrapping; opens/mutates no table or file (only the session command/function registries, which it cleans up). Permanent worked example of the AI-friendly dev-tools. IT HAD NO VALIDATOR UNTIL 2026-09-05, AND THAT IS WHY IT WAS NOT PROMOTED THAT DAY EITHER. It carried DEF-FAMILY-REGRESSION-BEGIN/-END -- the exact affordance require_exact_transcript_block consumes -- and NOTHING IN THIS FILE CONSUMED THEM, so REGRESSION RUN DEF_FAMILY printed a transcript and returned NO VERDICT: measured 2026-09-05, both L3 arms read 6/6 and this spec reported neither PASS nor FAIL nor a count. A spec that cannot go red is a permanently green line, so promoting it would have made REGRESSION ALL say something it had not checked. DefFamilyV1 is that missing instrument: a 22-line EXACT block, asserted in ORDER, on the ROUTED CHANNEL -- capture_routed_channel is true because the arm `Unknown command: PINGCMD` is cli::cmdout::print_line and a std::cout rdbuf swap cannot see it (the CLV lesson of 2026-09-04, one day old here). WHAT A GREEN DEF_FAMILY DOES NOT MEAN: that a DEFFN body can use its arguments. It cannot -- the MVP body returns stored text and ignores argv -- so the one argument arm is DEFCMD_args, about a COMMAND. PROMOTED TO THE DEFAULT SUITE 2026-09-05, IMMEDIATELY AFTER THE VALIDATOR'S FIRST GREEN AND NOT BEFORE IT. That ordering is the whole point of this entry: promoting on the strength of the runs taken while NOTHING WAS GRADING is exactly the mistake the paragraph above records, and the owner's promote instruction arrived while the spec was still in that state. THE SOAK ARGUMENT IS DELIBERATELY NOT MADE. NULLASSERT took three greens before its flag moved; this one has ONE run of its instrument, and the reason to promote anyway is the RELSCOPE2 precedent -- a MEASURED COVERAGE HOLE rather than a soak. What the default suite could not reach: not DEFCMD, not UNDEFCMD, not DEFFN, not UNDEFFN, not fn_custom, not the runtime command registry's remove path, not a custom function resolving inside `?`, and not one of the five evaluator insertion points. A whole shipped facility, four source files, behind a suite that would have stayed green through any of it breaking. THE COST IS NEAR ZERO: no catalog rows (none of the three minting verbs, and mints_catalog is false), no LMDB, no index containers, NO TABLE AND NO FILE AT ALL -- it touches only the session command and function registries and cleans both up with UNDEFCMD and UNDEFFN. It sets ECHO OFF and STOP_ON_ERROR OFF, which are session settings it does NOT restore; harmless where it sits and worth knowing if it ever moves. It takes the ROUTED CHANNEL for the length of its run, so it cannot run under an operator's own SET ALTERNATE -- AlternateCapture declines rather than clobbering, and says so. VERIFIED IN-SUITE 2026-09-05 ON THE PROMOTING BUILD (e4c3f78ea plus this flag flip; the build stamp is NOT quoted here because the run transcript began below the banner and a stamp nobody read is not a measurement). THE LISTING WAS NOT THE PROOF THIS TIME -- THE RUN WAS: the transcript begins mid-listing, so the [default] tag was not read, and what establishes the promotion took is that `REGRESSION: running DEF_FAMILY` appears in the suite sequence at all. That is a STRONGER reading than the tag, not a weaker one, and it is recorded this way rather than claiming a check that was not performed. RUN TENTH OF TWENTY-EIGHT, AND THAT POSITION IS THE POINT: every other spec promoted in this lane runs LAST, where it can only inherit. This one INHERITS FROM LEXING AND HANDS OFF TO SQLSEL_BUFFER_VIS, so it is the first here whose order-independence is tested in BOTH directions by the suite itself. The suite went 27 specs to 28. IT RETURNED THE ROUTED CHANNEL, which is the one interaction a single-spec run cannot expose: AlternateCapture took the channel mid-suite without meeting an operator's own SET ALTERNATE, and the six SQLSEL specs that follow all printed their own transcript-derived validator verdicts, so the channel was released rather than held. THE UNRESTORED SESSION SETTINGS COST NOTHING, measured rather than assumed: this spec leaves ECHO OFF and STOP_ON_ERROR OFF, and SQLSEL_BUFFER_VIS opens by setting both itself. IT MINTED NOTHING: seven specs took scratch brackets, wscat_run_305 through 311, and DEF_FAMILY was not among them; the L3 arm read six of six at both ends and the production catalog at 279 rows before and after. WHAT THIS DOES NOT SETTLE, and here it is a REAL gap rather than a formality: THE 22-LINE BLOCK HAS NEVER GONE RED. DefFamilyV1 is one day old and has seen exactly two runs, both green. Its FAIL paths -- the line-count mismatch and the line-N diff -- exist only in code, and its two declared brittlenesses (the en-US rendering of MessageId::UnknownCommand, and any added echo line in cmd_defcmd or cmd_deffn) are both UNMEASURED. A validator that has only ever passed is the exact condition this entry was written to correct one paragraph above, so it is named here rather than left for a later reader to notice.",
        true,    // PROMOTED 2026-09-05 -- one green run of DefFamilyV1; the argument is the coverage hole, not a soak
        false,
        RegressionValidator::DefFamilyV1,
        true                       // "Unknown command:" is cmdout, not cout
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
        "SQLMODE_SMOKE",
        "sqlmode_smoke_regression.dts",
        "SQLsel G2 (AIF-074): the sqlsel library target owns statement execution and session mode state; SQL mode routes SELECT to SQLSEL, blocks REL/SET RELATION and relation auto-refresh, intercepts native expression fallback, and marks the prompt. NATIVE/OTHER retain work-area SELECT, canonical SQLSEL is mode-invariant, and mode is process-local. Two SELECT/SQLSEL row sets are compared with SQLite; four behavioral mode/cursor markers and three exact refusals are required. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlmodeSmokeV1
    },
    {
        "SQLSEL_BUFFER_VIS",
        "sqlsel_buffer_visibility_regression.dts",
        "SQLSEL/TUPLE TABLE BUFFER visibility split (AIF-074): TUPLE previews the dirty current-row buffer while SQLSEL reads committed table truth. Five marked SQLSEL result sets are compared with an in-run SQLite oracle across dirty preview, rollback, and commit; the dirty TUPLE row and three cursor guards are exact transcript requirements. Self-bootstrapping throwaway SQLBUFVIS table in SANDBOX; self-erasing. Promoted 2026-09-03 because no other default spec asserts the committed-truth boundary while a native TableBuffer is dirty.",
        true,
        false,
        RegressionValidator::SqlselBufferVisibilityV1
    },
    {
        "SQLSEL_SELECT_V1",
        "sqlsel_select_v1_regression.dts",
        "SQLSEL statement surface, gate G3 (AIF-074 P3): SELECT <cols|*> FROM <table> with typed expression projection, WHERE, ORDER BY [ASC|DESC], LIMIT and COUNT(*), each row set compared against an in-process SQLite oracle over identical data in the same run. Asserts cursor neutrality by data, corrective errors for an unopened table / bad LIMIT / unknown ORDER BY field / ORDER BY on COUNT(*), and that ORDER BY sorts the full match set BEFORE LIMIT applies. Legacy predicate form preserved. Self-bootstrapping throwaway SQLSTU table in SANDBOX; self-erasing. Promoted 2026-09-03 because the prior default suite invoked SQLSEL HELP but executed no SQLSEL statement, leaving the complete statement path unasserted.",
        true,
        false,
        RegressionValidator::SqlselSelectOracleV1
    },
    {
        "SQLSEL_INNER_JOIN",
        "sqlsel_inner_join_regression.dts",
        "SQLsel G4a/G4b (AIF-074 P4.1/P4.2): two-table INNER JOIN with aliases, qualified fields, numeric equi-key matching, row multiplication, joined TupleRow WHERE, ORDER BY/LIMIT, COUNT(*), two-cursor restoration, corrective errors, and reported CDX-seek or nested-loop access. Four marked SQLsel row sets are automatically compared with an in-run SQLite oracle over identical data; two run through the indexed inner side and two through scan fallback. A mismatch, a missing path, a hybrid path, or surviving CDX metadata records an error and prints FAIL. Self-bootstrapping throwaway SQLJSTU/SQLJENR tables and index sidecars in SANDBOX; cleanup asserted 1/1. Promoted 2026-09-03 because no other default spec executes SQL-syntax JOIN or asserts its access-path report.",
        true,
        false,
        RegressionValidator::SqlselJoinOracleV1
    },
    {
        "SQLSEL_JOIN_EDGES",
        "sqlsel_join_edges_regression.dts",
        "Adversarial SQLsel INNER JOIN proof (AIF-074 P4.2): numeric duplicates, deleted outer/inner rows, unmatched keys, CDX character-key case collisions that require typed row revalidation, active-tag mismatch scan fallback, cursor restoration, caller-owned FLOCK preservation, canonical two-table read fences with reversed statement order, and two corrective refusals. Four marked SQLsel row sets are compared with an in-run SQLite oracle. The validator pins the access-path composition at exactly two CDX seeks, two nested-loop scans, zero hybrid, pins the probe/candidate counts that make the duplicate and case-collision arms discriminating, and asserts CDX metadata cleanup 2/2. Self-bootstrapping four-table SANDBOX fixture. Promoted 2026-09-03 because the basic INNER JOIN oracle does not cover collision revalidation, wrong-tag fallback, reversed lock order, or caller-owned FLOCK preservation.",
        true,
        false,
        RegressionValidator::SqlselJoinEdgesV1
    },
    {
        "SQLSEL_LEFT_JOIN",
        "sqlsel_left_join_regression.dts",
        "SQLsel G4c (AIF-074 P4.3): LEFT JOIN preserves duplicate matches, emits one produced-absent row for each unmatched non-deleted outer row, distinguishes genuine DBF blanks from absence through the one TupleRow marker plus an exact left-extended count, and returns identical rows through CDX-seek and scan paths. Seven marked SQLsel row sets are compared with SQLite after explicit NULL-to-marker mapping. The validator also pins 3 seek/4 scan paths, seven read fences, cursor restoration, caller-owned FLOCK preservation, ON -> extension -> WHERE ordering, SQL UNKNOWN behavior, and CDX metadata cleanup 1/1. Self-bootstrapping SANDBOX fixtures. Promoted 2026-09-03 because this is the default suite's only assertion of produced absence, blank/absence distinction, LEFT extension counts, and outer-WHERE three-valued logic.",
        true,
        false,
        RegressionValidator::SqlselLeftJoinOracleV1
    },
    {
        "SQLSEL_JOIN_FAMILY",
        "sqlsel_join_family_regression.dts",
        "SQLsel G4d (AIF-074 P4.4): RIGHT, FULL, and CROSS JOIN over two open tables. Fourteen marked SQLsel row sets are compared as SQL multisets with SQLite after explicit NULL-to-<UNMATCHED> mapping. The validator pins duplicate multiplication, unmatched rows from either side, genuine blank and stored-marker values, deleted-row exclusion, RIGHT/FULL CDX-seek versus scan parity, SQL three-valued outer WHERE, CROSS Cartesian count, exact extension reports, fourteen canonical read fences, both cursors, caller-owned FLOCK preservation, three corrective malformed-ON refusals, and CDX metadata cleanup 1/1. Self-bootstrapping SANDBOX fixtures. Promoted 2026-09-03 because no other default spec executes or oracle-checks RIGHT, FULL, or CROSS JOIN.",
        true,
        false,
        RegressionValidator::SqlselJoinFamilyV1
    },
    {
        "SQLSEL_SET_OPS",
        "sqlsel_set_operations_regression.dts",
        "SQLsel P4.5 (AIF-074): SELECT DISTINCT plus typed UNION, UNION ALL, INTERSECT, and EXCEPT over TupleRow results. Seven marked SQLsel row multisets are compared with an in-run SQLite oracle. The validator pins duplicate preservation/removal, SQL INTERSECT precedence, date-family set compatibility, deleted-row exclusion, exact operation cardinality reports, three cursor restorations, and six corrective refusals including column-count, numeric/text and date/text type mismatches, unsupported INTERSECT ALL, dangling UNION, and set-level ORDER BY/LIMIT. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlselSetOperationsV1
    },
    {
        "SQLSEL_AGGREGATES",
        "sqlsel_group_aggregate_regression.dts",
        "SQLsel P4.6 (AIF-074): typed GROUP BY and HAVING plus COUNT(*), COUNT(column), SUM, AVG, MIN, and MAX over single-table and joined TupleRow sources. Seven marked SQLsel row sets are compared with an in-run SQLite oracle whose blank numeric inputs are mapped to NULL. The validator pins R28 skip-and-report counts, SQL clause order, date MIN/MAX typing, join-source aggregation, two cursor restorations, one join fence/path, and five corrective aggregate/grouping refusals. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlselAggregatesV1
    },
    {
        "SQLSEL_SUBQUERIES",
        "sqlsel_subquery_regression.dts",
        "SQLsel P4.7 (AIF-074): typed uncorrelated and correlated scalar, IN, NOT IN, EXISTS, and NOT EXISTS subqueries over single-table outer scopes, including double-NOT-EXISTS relational division. Seven marked SQLsel row sets are compared with an in-run SQLite oracle. The validator pins one-evaluation caching for uncorrelated subqueries, per-outer-row correlated evaluation counts, three cursor restorations, typed IN mismatch and scalar cardinality refusals, and the explicit joined-outer boundary. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlselSubqueriesV1
    },
    {
        "SQLSEL_ADVANCED_JOIN",
        "sqlsel_advanced_join_regression.dts",
        "SQLsel generalized JOIN proof (AIF-074): self-join aliases over one physical table, composite boolean ON, three-table INNER/LEFT chains, shared-AST expression projection, independent multi-column ORDER BY directions, chain COUNT(*), empty-right typed schema preservation, and canonical read fencing across distinct physical tables. Eight marked SQLsel row sets are compared with an in-run SQLite oracle; three nonempty source cursors and exact access-path/report composition are pinned. The empty source has no readable row on which this language can assert cursor position. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlselAdvancedJoinV1
    },
    {
        "SQLSEL_DML",
        "sqlsel_dml_transaction_regression.dts",
        "SQLsel P5 (AIF-074): typed INSERT, UPDATE, and DELETE over the house table buffer, TBJ1 WAL, owner-aware table fence, and workspace-wide cursor guard. Six committed row sets are compared with SQLite. The validator pins autocommit, explicit rollback/commit, read-your-writes across buffered INSERT/arithmetic UPDATE, committed-view SELECT during a transaction, WAL cleanup, caller-owned FLOCK preservation, and fail-closed type/NULL/width/unknown-column/unsafe-delete controls. Transactions intentionally refuse a second target table because x64base has no cross-table atomic commit protocol. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, second-compiler proof, independent review, and soak.",
        false,
        false,
        RegressionValidator::SqlselDmlTransactionV1
    },
    {
        "SQLSEL_WORKSPACE",
        "sqlsel_workspace_scope_regression.dts",
        "SQLsel workspace-scope proof (AIF-074): two simultaneously open workspaces carry the same two table names with different typed values. Four SQLsel SELECT/JOIN/DML row sets are compared with SQLite. Every block discriminates against engine-global lowest-slot resolution; cursor markers prove both workspaces remain parked, and UPDATE must modify only the current workspace's table. Self-erasing SANDBOX fixtures. Explicit-run pending mutation proof, second-compiler proof, independent review, and soak.",
        false,
        true,
        RegressionValidator::SqlselWorkspaceScopeV1
    },
    {
        "EVALDIFF",
        "evaldiff_regression.dts",
        "SQLSEL evaluator differential harness (AIF-074 P4.0a/P4.0b): self-bootstraps a mixed-type X64 fixture in SANDBOX, compares classic DbArea and TupleRow-bound predicate outcomes over the same physical records, restores the cursor, and self-erases. Its validator checks the exact ordered 22-case truth/error vector, not parity alone. The 2026-09-03 repair makes valid function/logical/deleted cases verdict-parity and missing-field/type/malformed controls parity-on-failure. Promoted 2026-09-03 because no other default spec compares both evaluator paths or pins the repaired function/fail-closed truth vectors.",
        true,
        false,
        RegressionValidator::EvaldiffV1
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
        "WORKSPACE IDENTITY LADDER: a workspace is born durable, and can die durable (AIF-078 D10.1/D10.2/D10.3, 2026-08-23). WSL_T4 IS THE DISCRIMINATOR and it is one line: destroy WSLADR1, create WSLADR1 again, and the second WS_ID must be GREATER than the first. That can only pass if retirement actually reached the catalog -- if WORKSPACE DESTROY silently no-ops, supersedes the wrong row, or writes a flag that does not stick, the name still has a live chain, the second NEW ADOPTS it, and the two ids are EQUAL. It separates a real retirement from a cheerful message, which is the defect shape this house keeps finding. ASSERTIONS READ THE CATALOG TABLE, not the console: WORKSPACES.dbf is an ordinary x64 table -- the map drawn in the same ink as the territory -- so the spec opens it and compares FIELDS, per the FIELDMGR_APPEND doctrine that a spec asserting SHAPE passes green on a blanked table. WSL_T1/T2/T3 read the birth row itself: FMT 'BIRTH 1' (self-describing rather than inferred), SIZE_B 0 (no payload), PREV_ID 0 (it IS the chain root, which is what D10.2 makes identity). WSL_T5 reads the RETIRED row and finds it still present and flagged SUPERSEDED -- retirement is supersession, not deletion, so a destroyed workspace leaves a record rather than a hole, and SUPERSEDED keeps ONE meaning ('no longer the current state of this name') whether a newer save replaced it or nothing did. WSL_T6/T7 are the refusal arms and neither claims anything is absent: USE_AGAIN established over three cuts that no marker in this language can assert emptiness and that an ERRORED marker PRINTS NOTHING rather than going red, so both ask the answerable question instead -- did the KNOWN OCCUPANT SURVIVE. T6: DEFAULT refuses destruction (invariant I1 needs it to outlive every other workspace) and its sentinel still reads. T7: a workspace still holding an area refuses, and the area is still readable -- destroy does not cascade, so it can never be the thing that silently orphaned an open area. NOT COVERED, stated rather than implied: ADOPTION ACROSS A PROCESS BOUNDARY. WORKSPACE NEW refuses a duplicate name within a session, so one process cannot ask a second NEW to adopt. It was proven by hand instead (2026-08-23, build 05:27:07: two datarun processes, 'WS_ID 110' then 'WS_ID 110' + ADOPTED), and a two-process fixture is the chartered follow-up; this spec does not claim it. GUARDS: if any WSL_G* reds, treat every WSL_T* as UNPROVEN -- the catalog predicates depend on locating the right row, and the refusal arms depend on a sentinel actually having been written. WSL_G4/G5 EXIST BECAUSE THE FIRST RUN NEEDED THEM: the fixture wrote APPEND BLANK, which this shell does not take -- BLANK falls through as an unrecognized argument, APPEND prints its usage, nothing is appended, and REPLACE reports 'no current record'. CORRECTED 2026-09-05: THIS SHELL NOW TAKES IT, and the sentence before this one is left standing because it was true of every build up to that date. cli::preprocess_for_dispatch rewrites APPEND BLANK to APPEND_BLANK, runtime-proven the same day (COUNT 0 -> APPEND BLANK -> COUNT 1, on a build 4 minutes newer than the source). WHAT DOES NOT CHANGE IS WHY G4/G5 EXIST. The lesson was never 'this shell lacks a verb' -- it was that the spec guarded its catalog reads and not its sentinel WRITES, so a fixture failure wore a verb failure's clothes and would have been a FALSE GREEN had the unwritten field compared equal. That holds for every unguarded input regardless of which verbs work. THE HAZARD ALSO RECURRED AFTER BEING WRITTEN HERE, on 2026-09-05, to an author who had read this entry: cmd_append_blank.cpp's own usage block said APPEND BLANK was 'the friendly command spelling when routed by the dispatcher' and nothing routed it -- a conditional whose condition was false, filed next to the code, out-arguing a correct warning filed here. A warning filed somewhere true does not outrank a falsehood filed somewhere obvious, and that is the transferable half of this paragraph. Both sentinel tables were created EMPTY, and WSL_T6 and WSL_T7 went RED while the verb under test had behaved perfectly, printing both refusals exactly as designed. A FIXTURE failure wearing a VERB failure's clothes -- and had the unwritten field happened to compare equal it would have been a FALSE GREEN instead. The spec had guarded its catalog reads and not its sentinel writes, the same omission WSMULTI's WSM_G4 was added to close: guard every input an arm reads, not only the interesting ones. This verb is also where xbase::workspace::destroy() finally gets a call site: defined, correct, and CALLED BY NOTHING since stage 3, the fifth AIF-079 instance this lane catalogued and the first it closed. Self-bootstrapping WSLDEF/WSLOCC in SANDBOX, erased at the end; leaves retired catalog rows behind BY DESIGN -- that is the history D10.3 keeps and what WSL_T5 reads. Explicit-run until soaked, then promote to default. PROMOTED to the default suite 2026-08-24, ON A STEWARD RULING ABOUT ITS COST AND AFTER THAT COST WAS ACTUALLY MEASURED. This spec was held back longer than any other in this lane because it carries the most catalog residue of any spec -- minting and retiring WS_IDs IS its subject matter -- and the residue question was open. It was framed as a disk question and that framing was wrong. MEASURED 2026-08-24 by parsing WORKSPACES.dbf at record boundaries: 150 rows, ZERO deleted-flagged, 132 SUPERSEDED, 18 live. SNAPSHOT is a memo field and WORKSPACES.dtx is 2.74 MB against a 104 KB table, so the worry was that each residue row drags a snapshot with it -- IT DOES NOT. 110 of 150 rows carry a memo pointer and ZERO of the 39 workspace-spec rows do. Residue is 703 bytes a row: one REGRESSION ALL costs 4,921 bytes of DBF and 0 bytes of memo, so a thousand runs is 4.7 MB. The steward accepted that cost. WHAT THE MEASUREMENT FOUND INSTEAD, and it is why this spec is safe to promote while others would not be: eighteen rows are SUPERSEDED=0, i.e. LIVE HEADS, and thirteen of those are test and probe fixtures that were never retired (goneprobe, goneprobe2, partialprobe, ls_probe, ls_idxprobe, cycle_from_ram, v3_regress, sess_regress, wm_regress, minidb_regress, minidb_sidecar, ram_hydrate_src, LADDERTEST). A spec that mints a name which already has a live row does not get a fresh workspace -- IT ADOPTS, inheriting whatever the previous run left there, which is history-dependence wearing a green suit. THIS SPEC RETIRES EVERYTHING IT MINTS and WSL_T4 is the arm that proves it: destroy WSLADR1, create it again, second WS_ID must be GREATER. That arm cannot pass if a live row survived. So the property promotion actually requires is the property this spec already asserts about itself. NOTE THE ONE ROW IT LEAVES LIVE: LADDERTEST (rec 110) is a live head in the catalog today and this spec does not create it -- it predates the lane and is listed above as one of the thirteen. It is not this spec's residue and is not this spec's to clean up; it is named here so a reader counting LADDER-ish rows does not attribute it to this file. A WORKSPACE PURGE verb was ruled in on the same day and is designed separately (claude/AIF078_DESIGN_WORKSPACE_PURGE.md); when it exists the thirteen live heads are what it should be pointed at first, NOT this spec's superseded rows, which are the history D10.3 exists to keep. VERIFIED IN-SUITE 2026-08-24, and it CORRECTS THE ARITHMETIC ABOVE. Promoted, then run inside REGRESSION ALL on the same build. All seven WSL_T* arms and all five WSL_G* guards read .T.; WSL_T4 saw WS_ID 156 retired and 157 minted, greater as required. Order-independence is demonstrated rather than assumed: this spec's own opening teardown printed 'WORKSPACE DESTROY: no such workspace: WSLADR1' -- the previous run's names had been properly retired, so it started from a clean slate INSIDE a suite that had already run fourteen specs ahead of it. THE PER-RUN COST IS NOT 7 ROWS, IT IS 10. The 4,921-byte figure above was measured BEFORE this promotion and is the pre-promotion number; this spec mints three of its own (WSLADR1 twice, because WSL_T4 destroys and re-creates it, plus WSLADR2). Measured on the promoting run: the catalog went 150 -> 160 rows, WS_IDs 151-160, of which 156/157/158 are this spec's. So one REGRESSION ALL now costs 10 rows = 7,030 bytes of DBF and still 0 bytes of memo, and a thousand runs is 6.7 MB. Recorded as a correction rather than by editing the 4,921 away, because both numbers are true of the moment they describe and a summary that silently retunes its own measurements is the defect this house keeps finding one layer up. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. MEASURED ON THE 2026-08-29 PROMOTING RUN: this spec's rows went to data/tmp/wscat_run_81, 3 of them -- exactly the three this entry already claims (WSLADR1 twice, WSLADR2 once) -- and the L3 isolation arm read the PRODUCTION catalog at 264 rows BOTH BEFORE AND AFTER the suite. THE MINT COUNT DID NOT CHANGE AND WAS NEVER WRONG -- what changed is WHERE IT LANDS, and that is the whole correction. The four bracketed default-suite specs still mint exactly TEN rows between them (WORKSPACE_SCOPE 2, WSMULTI 3, WSLADDER 3, RELSCOPE2 2), the same ten the L2 comment in this file measured as 252 -> 262 on 2026-08-28 -- so the per-spec numbers corroborate rather than contradict. What is void is every projection built on top of them: a row count per run cannot be multiplied into megabytes of a durable catalog that is not being written. The cost is a throwaway directory under the gitignored TMP slot. MWXSHAKE joined the suite the same day at 16 rows, so the suite now mints 26 per run and the production total still did not move. BOTH BYTE FIGURES ABOVE ARE THEREFORE VOID AS DURABLE-CATALOG COSTS: 4,921 bytes, 7,030 bytes, 4.7 MB and 6.7 MB all described growth in WORKSPACES.dbf, and WORKSPACES.dbf no longer grows on a regression run. The ROW counts they were computed from stand. Kept rather than deleted for the reason the sentence before this one gives: they are true of the moment they describe, and this is the third time this entry has been corrected by measuring instead of inheriting.",
        true,
        true  // AIF-078 L2: mints catalog rows -- bracket it
    },
    {
        "WSPURGE",
        "workspace_purge_regression.dts",
        "WORKSPACE DELETE (spelled PURGE until 2026-08-24; the alias is still accepted and PG_T5 keeps it exercised): catalog rows are FLAGGED, never packed (AIF-078, steward ruling 2026-08-24 \"A -- flag, never pack\"; design claude/AIF078_DESIGN_WORKSPACE_PURGE.md). THE VERB WAS RENAMED BECAUSE THE OWNER READ ITS OUTPUT: \"how could you ever locate a purged row, it is gone forever, delete is a flag and that means the row still exists just ignored.\" Correct -- the verb sets the delete flag and SUPERSEDED and the row stays on disk PERMANENTLY, which is the whole design since max(WS_ID)+1 needs those rows COUNTED. The name promised removal and the code guaranteed the opposite; in xBase the pair is exact, DELETE flags and PACK removes. The name misled the OWNER reading output written by its own author, which is the proof that a name reaches further than any definition beneath it. The spec file and this spec id keep the WSPURGE spelling deliberately -- a spec id is an allocated identifier with run history behind it. PG_T5 IS A FIELD-VALUE MARKER, NOT A COMMAND RUN: its first draft was the WORKSPACE PURGE line plus a comment naming itself PG_T5, asserting nothing, so a dead alias would have printed an error and left the spec all green -- the FIELDMGR_APPEND defect committed inside the arm written to prevent it, caught before it ran. PG_T1 IS THE DISCRIMINATOR and it exists because WS_ID allocation is max(WS_ID)+1 DERIVED by scanning surviving rows -- nothing persists a high-water mark. Physically remove the newest rows and the next WORKSPACE NEW re-mints an id a purged workspace already used; D10.2 makes the chain-root WS_ID the DURABLE IDENTITY, so that is two workspaces sharing one identity across time, R5 on the time axis, undetectable after the fact. The fixture arranges the trap on purpose: WSPRG1 is minted, retired, minted and retired again so its two rows are the two HIGHEST in the catalog, both are purged, and then a NEW name must mint ABOVE the highest purged id. Pack, and PG_T1 reads .F. PG_T2/PG_T3 ARE A PAIR because ruling A has two halves and a row is WORSE OFF if only one lands: the delete flag hides the row, SUPERSEDED=1 stops scan_catalog ELECTING it live -- and that scan does not filter deleted rows, it elects on WS_NAME plus SUPERSEDED alone, so a flag-only purge would leave a row invisible to the user and still adoptable by the next NEW, the AIF-118 shape exactly. PG_T2 reads the purged row with SET DELETED OFF and asserts SUPERSEDED=1. PG_T3 WAS WRITTEN TO SHOW THE ROW GOES AWAY UNDER SET DELETED ON AND INVERTED ON ITS FIRST RUN, 2026-08-24 -- which is the most valuable thing this spec has produced. LOCATE printed 'Located.' and moved the cursor onto the purged row with the shell reporting 'Deleted visibility: HIDE (ON)' one line earlier: a DELETE-FLAGGED RECORD IS STILL REACHED BY LOCATE. The flag itself landed -- purge_durable_workspace re-reads isDeleted() from the record before counting a row done and refuses to continue if it is false, and the verb reported both rows purged -- so this is LOCATE not consulting the setting, not a write that failed. WHAT IT CORRECTS: the delete flag is NOT what protects the catalog. SUPERSEDED is. The flag's value is that scan_catalog still COUNTS the row, which is exactly what preserves the high-water mark PG_T1 asserts. Hiding was assumed rather than measured, in the design and in this spec's own header, and the assumption was wrong. PG_T3 is now a TRIPWIRE recording the measured behaviour, with PG_T3B reading the protection that actually holds off the same row in the same breath; if PG_T3 ever reads .F. again, LOCATE has GAINED delete-filtering and the arm should be repointed deliberately rather than allowed to retune itself (the IDXSTALE precedent). THE TRIPWIRE FIRED THE SAME DAY AND HAS BEEN REPOINTED DELIBERATELY. AIF-123 found the cause: filter::visible() -- the ONE gate LIST, COUNT, SMARTLIST, LOCATE, FIND, SCAN, EXPORT and logical_nav all ask, twelve callers -- applied SET FILTER and FOR and NEVER consulted SET DELETED. Not a LOCATE defect at all; LOCATE was behaving like every other caller of a gate with a missing rung. The rung had been absent since 06ba79e93 (2025-08-16), which rewrote LIST, replaced its Settings::deletedOn() read with a per-command flag, and PRESERVED THE DEFAULT WHILE SEVERING THE CONTROL -- so nothing changed on the path anyone ran and nothing could go red, for fourteen months. With the rung restored LOCATE reports 'Not Located.' and PG_T3 is INVERTED to assert that. PG_T3B is REPURPOSED rather than deleted: it used to read SUPERSEDED off the row LOCATE landed on, and with no landing it was reading a stale cursor and would have gone red for a reason unrelated to its own name; it now carries the OTHER HALF, that SET DELETED OFF still reaches the row. Both-halves is the point -- 'hidden under ON' asserts nothing without 'visible under OFF' beside it, because a build that hides unconditionally passes the first and fails the second. See SDVIS, which is built entirely on that principle. PG_T4 IS THE REFUSAL ARM AND IT GUARDS A RULE THAT CHANGED BETWEEN DESIGN AND CODE: the design said PURGE would refuse any name with a LIVE catalog row and send the caller to DESTROY first, until DESTROY's dispatch was actually read -- it resolves its target through resolve_workspace_token(), the RUNTIME registry, and answers 'no such workspace' for anything not currently declared. A catalog-only live head (the thirteen the 2026-08-24 census found: goneprobe, ls_probe, wm_regress and ten others) would have been reachable by NEITHER verb. The clause would have fenced off the exact rows the verb was ruled in to deal with -- the same mistake as calling workarea_util 'a shared home' before checking the second consumer could link it. What is refused instead is a workspace DECLARED IN THIS SESSION, whose identity must not be yanked out from under it. PG_G2 DELIBERATELY DOES NOT USE RECCOUNT(): USE_AGAIN measured that RECNO()/FOUND() render EMPTY in a '?' marker, RECCOUNT() serves compile_predicate rather than the marker path, and a marker that errors prints nothing rather than going red -- so that guard would have vanished from the suite while the count still read full. Every marker is a FIELD-VALUE comparison against WORKSPACES.dbf per the FIELDMGR_APPEND doctrine. Leaves its own rows behind flagged and superseded BY DESIGN: the file never shrinks, which is what ruling A chose, and the honest cost is 4 rows per run. SUPERSEDED 2026-08-29 BY THE L2 CATALOG BRACKET, and the clause above is LEFT STANDING because it was true when it was written. These rows no longer land in WORKSPACES.dbf at all. A spec flagged mints_catalog runs inside CatalogBracket, which re-points the WORKSPACES slot at a per-run scratch root and restores it from a destructor; it sits in run_regression_script, the ONE place any spec is run, so an EXPLICIT single-spec run is bracketed exactly as REGRESSION ALL is. This spec is flagged mints_catalog and is EXPLICIT-RUN, so it is bracketed on the same code path -- but it was NOT run on 2026-08-29 and its 4 is therefore NOT RE-MEASURED, stated rather than assumed. What is established is the DESTINATION, which follows from the flag plus the bracket's placement and needs no run of this spec to be true: whatever it mints goes to a per-run scratch root, and 'the file never shrinks' now describes a throwaway file. Re-measure the 4 when this spec is next run. NOT COVERED, stated rather than implied: that a purged row is genuinely delete-FLAGGED as opposed to merely hidden -- DELETED() is a predicate-path function, not a marker-path one, so PG_T3 proves reachability rather than the flag byte; a unit fixture over DbArea::isDeleted() is the honest home for that claim. RE-PURGE IS IDEMPOTENT AND IS NOW REPORTED AS SUCH, which this spec's own SECOND run exposed: the fixture uses stable names, so run two found run one's rows still carrying WSPRG1 and re-purged them, and the verb announced 'Purged 4 row(s), WS_ID 161,162,165,166' when only 165 and 166 had moved. The outcome was correct -- setting SUPERSEDED on a superseded row and re-flagging a flagged one changes nothing -- but the COUNT was not, and left alone every run would report a larger number for the same work: 2, then 4, then 6, with nothing saying why. WORKSPACE WRITEBACK's rule pointed at a different loop -- a count is a fact about a loop until something declares what it SHOULD be. The verb now reads each row's state before touching it and reports transitioned and already-purged rows separately. NOT ASSERTED BY AN ARM, stated rather than implied: no marker reads those counts, because markers are field-value comparisons and counts are console text; the idempotence is visible in the transcript and verified by reading it, the IDXDIFF precedent. Explicit-run until soaked.",
        false,
        true  // AIF-078 L2: mints catalog rows -- bracket it (NEW x6; WSPRG4 is
              // minted twice by the 2026-09-06 adopt-then-DESTROY arm, and the
              // second is an ADOPTION that writes no row)
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
    },
    {
        "NULLASSERT",
        "vfp_null_assertions.dts",
        "NULL IS ASSERTABLE (AIF-091, 2026-09-05). The lane could CREATE a nullable VFP table, write a null, read it, display it and filter on it -- every leg graded against bytes Visual FoxPro wrote -- and REGRESSION ALL could reach NONE of it, because no .dts asserted a null. THIS SPEC'S FIRST RUN WAS 17/21 AND THE FOUR REDS WERE ONE DEFECT: a value write stored the value AND re-committed the null bit (DbArea::set() never touched _fd_null; storeFieldsToBuffer() recomputes the bitmap FROM _fd_null), so REPLACE VNAME WITH \"restored\" left a cell that read `restored` to `?` and `.NULL.` to LIST, and survived a close and reopen. Fixed in 22c748381; the four arms are the regression. NL_T1 IS THE DISCRIMINATOR AND THE FIXTURE IS ORDERED FOR IT: rec 2's VNAME is BLANK AND NOT NULL and sits AHEAD of the nulled rec 3, and LOCATE takes the first match from the top, so a build that answers ISNULL from emptiness lands on rec 2 and reads `blankvn`. NL_T5/T6 state the problem out loud -- the nulled cell and the blank cell BOTH read empty by value, which is why ISNULL has to exist and why its argument is never evaluated. NL_T11 is the strongest single arm: with rec 3 cleared, LOCATE FOR ISNULL(VNAME) must find REC 5, which proves three things at once -- rec 3's bit actually cleared rather than being overwritten in the value area, rec 5's bit was set by the DOTTED `.NULL.` spelling, and the two rows' bits are independent. WHY NO ARM USES `? \"NAME:\" + ISNULL(f)`, WHICH WAS THE PLAN: `?` is a SHORTCUT FOR FORMULA (shortcut_resolver.hpp), FORMULA calls eval_rhs, and eval_rhs tries its OWN scalar parser first -- which is where `+` string concatenation lives and whose four builtin tables do not contain ISNULL. Only the fallback (eval_any -> compile_where_program) knows it, and in THAT AST `+` is Arith and Arith::evalString returns a NUMBER. PREDICTED FROM THE CODE, THEN MEASURED by the spec's own NL_P2 probe, which printed a bare `0` AND SWALLOWED THE LABEL -- so a spec written that way would have emitted one anonymous zero per arm and the marker-count discipline could not have seen it. This is a property of the whole FunctionCategory::Cursor category, not of one function; the catalogue already files the same note one entry above ISNULL's, about RECNO. So every marker here is a FIELD-VALUE comparison and the nulls are asserted through LOCATE FOR ISNULL(<field>), the FOR-predicate path the feature was built for. COVERAGE: bit index (T2 -- ID and VNAME do not own adjacent bits, because a Varchar owns a varlength bit too; two commits in this lane exist because that order was got wrong); field and row isolation (T3, T4, T7); the write reached DISK (T8, T9, T12 -- close and reopen, the only question a suite can ask that a staged row cannot answer for itself); the bit CLEARS (T10, T11); refusal on a non-nullable field (T13, T14); refusal under TABLE BUFFER (T15, T16, run LAST because they touch a session setting, and buffering is restored OFF). Neither refusal arm claims a MESSAGE appeared -- console text is unreadable by a marker -- so both ask the answerable questions instead: did the value survive, and did the refusal leave the rest of the bitmap alone. NOT CLAIMED, stated rather than implied: that no OTHER row is null (no marker in this language can assert an absence, and an errored marker PRINTS NOTHING rather than going red); that LIST prints `.NULL.` (true, proven by hand in 11b40895a, and console text); anything about null ORDERING (opened NOINDEX throughout, and what a CDX/CNX/LMDB backend makes of a null key is unclaimed by this lane); ISNULL over a JOINED or TupleRow source; what VFP's own APPEND BLANK writes into a bitmap. 21 GRADED MARKERS -- 5 NL_G* guards, 16 NL_T* arms -- plus 3 UNGRADED NL_P* probes that are not part of the 21. COUNT THEM: a transcript with 20 is a spec that lost a claim, not a spec that passed. If any NL_G* reds, treat every NL_T* as UNPROVEN; the arms read fields of rows the guards establish. Disposable table, rebuilt every run, mints no catalog rows. Explicit-run until soaked: TWO GREEN 21/21 RUNS, 2026-09-05, the second on a build nobody had changed anything on -- the first proved the fix, the second proves the spec. PROMOTED TO THE DEFAULT SUITE 2026-09-05. THREE GREEN 21/21 RUNS BEFORE THE FLAG MOVED: two by DOTSCRIPT (the second on a build nobody had changed anything on -- the first proved the fix, the second proves the spec) and one by REGRESSION RUN NULLASSERT, which is a DIFFERENT measurement and was treated as one: it exercises the bracketed path and the L3 isolation arm, machinery a bare DOTSCRIPT never touches (L3 6/6 before, 21/21, L3 6/6 after, production catalog 279 rows on both reads). THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, NOT THE SOAK ALONE -- the RELSCOPE2 precedent. REGRESSION ALL COULD NOT REACH ONE INCH OF THIS LANE: not CREATE VFP with NULL, not REPLACE ... WITH NULL, not the .NULL. spelling, not ISNULL in a predicate, not the clear path, not either refusal. Six commits of engine work behind a suite that would have stayed green through all of it. THE COST IS THE CHEAPEST IN THE SUITE: no catalog rows (none of the three minting verbs), no LMDB, no index containers, one disposable VFP table rebuilt and overwritten every run in DBF/SANDBOX -- the SDVIS pattern. IT RUNS LAST BY DECLARATION ORDER AND THAT IS THE SAFE POSITION: it re-points the DBF slot to SANDBOX and does NOT restore it (SDVIS does the same), and nothing in the suite runs after it except the L3 AFTER arm, which sets its own slots. It restores TABLE BUFFER to OFF, which is the only session setting it touches. It inherits INDEXES and LMDB rather than re-pointing them -- the same standing fixture omission recorded against MWXSHAKE section 5C and OPENJOIN, harmless here because this spec builds no containers, and it will stop being harmless the moment an arm needs an index. NOT YET VERIFIED IN-SUITE at the time of writing, which is the property a single-spec run cannot prove: order-independence when it inherits WSENV's open areas and path slots. VERIFIED IN-SUITE 2026-09-05 ON THE PROMOTING BUILD (c1678d167 plus this uncommitted registry edit; build/src/Release/dottalkpp.exe stamped Sep 5 2026 17:39), and every clause above is LEFT STANDING because it was true when it was written. THE LISTING WAS READ BEFORE THE RUN, which is the check the sentence below demands and the one NAV_NATURAL's entry records a wasted REGRESSION ALL for: REGRESSION LIST showed NULLASSERT [default], so the rebuild took and the entry was live rather than merely edited. Run as the TWENTY-SEVENTH AND LAST spec of REGRESSION ALL: 21 of 21, full count, five NL_G* guards and sixteen NL_T* arms, with the two ungraded probes behaving exactly as this entry predicts -- NL_P1 printing .T., and NL_P2 printing a bare anonymous `0` with its label swallowed, so the `+` finding above is now reproduced INSIDE THE SUITE and not only in a single-spec run. IT MINTED NOTHING, measured rather than assumed: seven specs took scratch brackets this run, wscat_run_298 through 304, and NULLASSERT WAS NOT AMONG THEM; the L3 isolation arm read six of six at both ends and the production catalog at 279 rows before and after. ORDER-INDEPENDENCE IS DEMONSTRATED RATHER THAN ASSUMED, which is the one thing this run adds over the three that preceded it: it inherited WSENV's session with the DBF slot left on the bare data/DBF root rather than the DBF/SANDBOX its earlier greens started from, re-pointed ONLY DBF in its own opening line, and built its fixture from a slate WSENV's teardown had cleared -- so it depended on nothing it inherited, and the single-slot re-pointing noted against MWXSHAKE section 5C is confirmed harmless HERE while remaining the same standing omission everywhere. WHAT THIS RUN STILL DOES NOT SETTLE -- AND THIS PARAGRAPH IS A CORRECTION, because the sentence first committed here (a46fa95c9) said something THE SPEC'S OWN HEADER REFUTES ON LINE 171. IT IS NOT TRUE that NULLASSERT has never run against a pre-fix binary. Its FIRST RUN -- 2026-09-05, build Sep 05 2026 08:29:36 (11b40895 dirty) -- was 17 OF 21, with exactly NL_T11, NL_T12, NL_T14 and NL_T16 red and all five guards green, which is the prediction element for element; and the header records that the four arms were DELIBERATELY NOT RETUNED afterwards, so the markers that went red are the markers that ship. The four reds are a MEASUREMENT. This spec is known to be capable of failing, and it failed for the reason the fix addresses. THE REAL REMAINING GAP IS NARROWER, AND IT IS THE ONE THAT MATTERS FOR A PROMOTED SPEC: that 17/21 was taken by DOTSCRIPT. THE BRACKETED REGRESSION PATH -- the grader REGRESSION ALL actually runs through, with its L3 isolation arm and its pass/fail rollup -- HAS ONLY EVER SEEN THIS SPEC GREEN. Nothing here shows the SUITE REPORTS the failure rather than merely containing a spec that can fail; that would take one REGRESSION RUN NULLASSERT against a binary with 22c748381 backed out. That debt is smaller than the one first written here and it is still open. THE ERROR IS WORTH KEEPING RATHER THAN ERASING: it is the sixth AIF-079 instance in this lane and the same shape as the others -- a claim asserted about a file without reading the file, when the file being described contained the disproof. THE FLAG FLIP NEEDS A REBUILD -- the registry is compiled in, and NAV_NATURAL's entry records a whole REGRESSION ALL wasted on exactly that mistake, a full green over a spec that never executed, caught only because the curated listing showed it without its [default] tag. Read REGRESSION LIST for the tag before believing the run. CORRECTED 2026-09-08, AND THE CORRECTED CLAUSE IS THE ONE THIS ENTRY ARGUED HARDEST FOR: \"IT RUNS LAST BY DECLARATION ORDER AND THAT IS THE SAFE POSITION\" IS FALSE. RUNNING LAST IS ONLY SAFE IF NOTHING RUNS AFTER, and an operator running an explicit spec afterward -- REGRESSION ALL then REGRESSION PKPOLICY, which is an ordinary thing to type -- is exactly that. Measured 2026-09-08: that sequence turned four PKPOLICY markers red while PKPOLICY alone read 15 of 15, reproduced down to REGRESSION NULLASSERT then REGRESSION PKPOLICY (481 lines), then to a bare DOTSCRIPT of this spec's own file (365), then to LINES 1-278 OF IT (318) -- a cut of 23 executable lines in which NOT ONE NULL IS WRITTEN. AND THE RISK THIS ENTRY NAMED WAS THE WRONG ONE. The unrestored DBF slot was INNOCENT: it points at DBF/SANDBOX, which is where PKPOLICY builds its own fixtures anyway, and PKPOLICY re-points all three slots itself. What actually leaked was DbArea::_null_layout -- assigned in ONE place (partitionTrailingSystemField) and reset in NONE, because clearFields() and DbArea::close() are two hand-maintained teardown lists over the same members and BOTH skipped it. So this spec's CREATE VFP NULLSPEC left a VARCHAR bit layout in area 1; the next table opened there had isVarlengthField_() answer from it and storeFieldsToBuffer() write a LENGTH BYTE into the last byte of a plain C() field, on disk, with nothing refused and nothing printed. Fixed in 5e54df79e. THE LESSON FOR THIS ENTRY IS NOT THAT THE SLOT ANALYSIS WAS SLOPPY -- it was careful, and it enumerated what this spec re-points and does not restore. It is that a spec can leak state NOBODY HAS THOUGHT TO ENUMERATE, so \"it runs last\" is a statement about ORDER and never a proof of ISOLATION. VARCHARRESET (8885ab999) is the arm that now asserts the thing this paragraph could only assume: that closing a varchar table leaves its area clean.",
        true    // PROMOTED 2026-09-05 -- three green 21/21 runs before the flag moved (two DOTSCRIPT, one REGRESSION RUN), then VERIFIED IN-SUITE the same day, 27th and last in REGRESSION ALL; see the summary for the coverage argument and for what the run still does not settle
    }
    ,
    {
        "PKPOLICY",
        "pk_policy_regression.dts",
        "PRIMARY KEY POLICY: WHAT HOLDS TODAY, AND WHAT THE POLICY WORK MUST MAKE HOLD (AIF-156, 2026-09-06). x64base DECLARES a primary key (SET UNIQUE FIELD <f> PRIMARY), GENERATES it on APPEND into a BLANK key field inside try_lock_table/unlock_table so max+1 is taken by one writer at a time, and RESERVES a deleted row's key until PACK because a deleted row can be RECALLed -- all three deliberate, all three worth keeping, and NONE of them enforcement. IT ENFORCED THE KEY NOWHERE, MEASURED 2026-09-06 on build Sep 05 2026 21:18:51: a native REPLACE wrote a duplicate over a PRIMARY key and it SURVIVED A CLOSE AND REOPEN, and SQLSEL INSERT committed a second duplicate through the table buffer and WAL. ALL THREE OF THE ARMS THAT EXISTED THAT DAY WENT GREEN, RE-MEASURED 2026-09-07 on build Sep 07 2026 09:20:18: SQLSEL INSERT and SQLSEL UPDATE are refused at validate_field_constraint_for_store, which both reach through evaluate_store_expression, and native REPLACE now writes through xbase::cli::replaceFieldStored() -- the field-write funnel declared in include/xbase_cli.hpp on 2026-07-30 and never defined until AIF-156 built it. AND THREE OF THREE WAS NOT AN ENFORCED KEY: this spec has never asked about CALCWRITE, REPLACE_MULTI, BROWSE or RECORDVIEW editing, COPY, SORT or IMPORTSQL, and a crude count found roughly 86 candidate direct-write call sites across 21 files -- CORRECTED 2026-09-07 TO 28 SITES IN 19 FILES, 27 after CALCWRITE was routed. The 86 was a crude grep that counted comments, counted these very registry summaries (which discuss replaceFieldStored at length inside string literals), and counted name-keyed wrapper calls like w.set(\"ID\", ...) that are not field writes. tools/staging/check_field_write_callers.py is the measurement -- CORRECTED 2026-09-07 TO 28 SITES IN 19 FILES, 27 after CALCWRITE was routed. The 86 was a crude grep that counted comments, counted these very registry summaries (which discuss replaceFieldStored at length inside string literals), and counted name-keyed wrapper calls like w.set(\"ID\", ...) that are not field writes. tools/staging/check_field_write_callers.py is the measurement. What closes that gap is a STATIC gate over the callers, because no runtime marker can enumerate a call site. VALIDATE UNIQUE then found what it was built to find. FIFTEEN GRADED MARKERS, DERIVED NOT DECLARED: seven guards PKP_G1..G7 and eight arms PKP_T1..T8, contiguous -- count them, because an errored marker in this language PRINTS NOTHING rather than going red and a transcript with fourteen is a spec that lost a claim. PKP_G5 EXISTS BECAUSE THE FIRST RUN OF THIS SPEC WAS BLIND ON PART B: Part A closes PKPOL to build the dirty fixture, a bare SELECT 1 then selected an area with NO FILE OPEN, and T4/T5/T6 printed .F. because NOTHING RAN -- the value this spec expects today, so it PASSED. The right answer for the wrong reason, and a ratchet that could never have fired when enforcement arrived. G5 reopens the table and is a HARD GATE on the acceptance count. A CLOSE FOLLOWED BY A SELECT IS NOT AN OPEN, which is the USE_AGAIN/WSENV/MWXSHAKE-5C shape arriving for the fifth recorded time, in a spec whose own header warns about it. THE HALVES ARE GRADED DIFFERENTLY AND THAT IS THE DESIGN. PART A (G1..G4, T1..T3) is green today and locks in what already works; PKP_T1 deletes record 3 and requires the next APPEND to issue 4, PKP_T2 recalls record 3 and requires it to still read 3, which is the pair that would red if the generator ever stopped scanning deleted rows -- the exact trap an index-backed fast path falls into, and the reason compute_next_numeric() is still an O(n) scan on purpose. PART B (T4..T8) is the ACCEPTANCE CRITERION for write-time refusal and is GREEN AS OF 2026-09-07, asserted as FIVE SEPARATE ARMS rather than one because native REPLACE, SQLSEL INSERT, SQLSEL UPDATE and the two legacy verbs each reach a field write by their own path and a fix wired into one is not evidence about the other -- which is exactly what happened: the first increment turned T5 and T6 green and left T4 untouched, and had this been one arm instead of three that transcript would have read as a win. THE SAME LESSON THEN ARRIVED ONE LEVEL UP: three arms is itself too few for the native side, which has at least five doors across three files, and the answer was to CONSOLIDATE THE ROUTE rather than mint arms -- one funnel, plus a static gate proving nobody goes around it. THE VALIDATOR IS A RATCHET THAT FAILS IN BOTH DIRECTIONS: kPkAcceptanceExpected records how many Part B arms were green when this spec was last reviewed, so enforcement ARRIVING fails the spec until a human bumps the constant deliberately, and enforcement REGRESSING fails it too. Without that, a permanently-red half is DEF_FAMILY's mistake repeated -- markers with no grader, green by construction. NOT CLAIMED, stated rather than implied: PERSISTENCE ACROSS A RESTART (the declaration lives in a process-local map that unique_registry.cpp calls 'not persistent schema metadata'; a .dts runs in ONE process so no marker here can ask the question, and a two-run harness is step 1 of the lane); CONCURRENCY (one writer cannot exercise the table lock); REFERENTIAL INTEGRITY (out of scope, nothing here declares a foreign key). EVERY ANSWER IS A FIELD READ, never console text: if the cell still holds its original value the write was refused, if it holds the new one it was not. EXPLICIT-RUN AND IT MUST STAY THAT WAY WHILE PART B IS RED -- a partially-red spec must not enter REGRESSION ALL. Promote on the NULLASSERT precedent only after Part B is green and soaked: two green runs on a build nobody changed anything on, then the flag moves, then a REBUILD, then read REGRESSION LIST for the [default] tag BEFORE believing the run. SECOND INCREMENT 2026-09-07, RATCHET 3 -> 5: PKP_T7 and PKP_T8 measure the LEGACY bare INSERT and UPDATE verbs -- cmd_sql_insert.cpp and cmd_sql_update.cpp, registered at shell_commands.cpp:458-459. THEY ARE A SECOND DOOR AND T5/T6 NEVER TOUCHED IT: those two measure SQLSEL INSERT and SQLSEL UPDATE, which are different files reached by a different registration, so 'three of three' had described an enforced key for a day while a bare INSERT could still write a duplicate primary key. PKP_G6 AND PKP_G7 SHIPPED WITH THEM AND ARE THE MORE INTERESTING HALF: T7 and T8 both read 'refused' from a write NOT HAPPENING, and a verb that did nothing at all -- unregistered, unparsed, or a WHERE matching no row -- reads identically. G6 proves the INSERT verb appends, G7 proves the UPDATE verb's WHERE reaches record 3, and both write a NON-KEY field so neither is a second measurement of the policy. That is PKP_G5's lesson for the sixth recorded time in this tree and the first time it was designed in rather than discovered after. T7 ALSO ASKS WHETHER THE REFUSAL LEFT A BLANK ROW: the legacy INSERT appends first and writes second, so a gate before the field write rather than before appendBlank() would refuse the duplicate and still grow the table, which is why the arm reads LNAME = 'EPS' and not LNAME <> 'DUP7'. REPLACE_MULTI WAS GATED THE SAME DAY AND IS STILL UNASSERTED HERE, named rather than counted, because multirep_buffering_regression.dts was retired to _to_delete/ on 2026-09-04 and nothing replaced it -- a fix with no arm, recorded as one. AND THIS SPEC'S OWN ERASE FOUND A SEPARATE DEFECT ON 2026-09-07: it reported 'FAILED: PKPOL.dbf.tbj (used by another process)', which was the process's own leaked handle. enlist_sql_transaction opens the write-ahead journal before any change exists, cmd_ROLLBACK calls journal_note_rollback only inside `if (!tb.empty())`, and a transaction the primary-key gate refuses never buffers a change -- so an EMPTY transaction leaked the FILE* for the life of the process and orphaned a header-only .tbj. Fixed by closing the journal in release_sql_transaction, the pair of the enlist that opened it. IT WAS ONLY VISIBLE BECAUSE ERASE HAD JUST LEARNED TO SWEEP .tbj: the orphan had been landing silently for as long as the journal has existed, and an older one with a WSL-era path was sitting in the same directory. Disposable PKPOL/PKPDIRTY tables in DBF/SANDBOX, erased at both ends; mints no catalog rows.",
        false,
        false,
        RegressionValidator::PkPolicyV1,
        true // VALIDATE UNIQUE and the shell both print through routed channels
    }
    ,
    {
        "PKDURABLE",
        "pk_durability_regression.dts",
        "A PRIMARY KEY DECLARATION SURVIVES A RESTART, AND THIS IS THE ONLY SPEC IN THE TREE THAT CAN SAY SO (AIF-156, 2026-09-07). A .dts RUNS IN ONE PROCESS -- not a gap in PKPOLICY but a LIMIT OF THE INSTRUMENT, and PKPOLICY's own header says so under NOT CLAIMED: no marker in it can distinguish a designation READ BACK from the x64 header from one merely remembered in a map that had not died yet. Until 2026-09-07 the answer was the second. unique_registry.cpp held the designation in a static std::unordered_map under its own boundary comment 'not persistent schema metadata', so a fresh session without a redeclare let REPLACE overwrite a primary key IN SILENCE on a build where all three PKPOLICY arms read green. THE SPEC IS A THIN WRAPPER AND ASSERTS ALMOST NOTHING ITSELF. The measurement runs in TWO CHILD PROCESSES: run 1 creates PKDUR, declares SET UNIQUE FIELD EMPNO PRIMARY, mints keys 1 and 2, and EXITS LEAVING THE TABLE ON DISK -- deliberately, because every other fixture in this tree cleans up after itself and this one must outlive its process or there is nothing to reopen; run 2 opens it, ISSUES NO DECLARATION AT ALL, and tries to duplicate the key. GRADING HAPPENS IN C++ BECAUSE IT MUST: `!` is std::system(), so a child's stdout never passes through the stream AlternateCapture swaps, and a transcript-reading validator would see NONE of the child markers. The children write theirs through SET ALTERNATE and validate_pk_durability() READS THOSE CAPTURES OFF DISK. A VALIDATOR CAN OPEN A FILE AND A MARKER CANNOT -- that asymmetry is the only reason a cross-process claim is assertable here at all. WHAT THE SPEC ITSELF CONTRIBUTES is the one thing the captures cannot supply: PKDUR_G0 prints before the shell-out and PKDUR_G1 after it, so a transcript with G0 and no G1 says the launch DIED -- PowerShell, an execution policy, an unbuilt runtime -- which is a different finding from a durability failure and must not be reported as one. FIFTEEN CHILD MARKERS, TEN OF THEM GUARDS, AND TWO ARMS THAT ARE SUPPOSED TO PRINT .F. -- the validator grades against an EXPECTED VALUE rather than against green, because a spec whose correct reading includes a red cannot be graded any other way. PKD_W3 is the load-bearing one: it proves the refusal fires IN THE DECLARING PROCESS, so a red in run 2 cannot be confused with enforcement being broken on this build entirely, and the validator reports UNPROVEN rather than FAIL when a guard reds. PKD_T2 closes and reopens after the refusal, because a write that got through and merely failed to flush would read green on T1 and red there. MISSING IS COUNTED SEPARATELY FROM RED, the house COUNT THE MARKERS rule applied to a file instead of a transcript: an errored marker prints nothing rather than going red, so seven of eight green is a lost claim wearing a clean face. THE CHILD LAUNCHER INVOKES THE EXE DIRECTLY and does not go through datarun.ps1, because that calls Update-DotTalkRuntimeExe which may COPY the runtime -- and the parent process holding the launcher open IS that runtime; copying over a running binary fails on Windows. It copies nothing and sets no environment. FIRST MEASURED 2026-09-07 by the standalone driver tools/staging/pk_durability_two_run.ps1 on build Sep 07 2026 12:55:02: 8 markers, 8 green, 0 red, 0 missing, with 'REPLACE: SID: is the PRIMARY key and cannot be written.' printed by a process that never declared the key. NOT CLAIMED, stated rather than implied: THE LONG-NAME HAZARD -- primary_field() returns a NAME and is_primary_field_() compares it against field_name_upper(), and SID is three characters, so this fixture CANNOT expose a mismatch between a long logical name and its 10-byte descriptor token, the exact class AIF-157 consolidated onto xfg::resolve_field_index_std; CONCURRENCY (two processes in sequence, not at once); and everything the write funnel does not cover -- CALCWRITE, REPLACE_MULTI, BROWSE and RECORDVIEW editing, COPY, SORT, IMPORTSQL. Durability of the DESIGNATION says nothing about completeness of the REFUSAL. THE VALIDATOR HAS BEEN OBSERVED REPORTING PASS ON A RUN THAT NEVER HAPPENED, AND THE FIX WAS WHERE THE GUARD SITS, NOT WHAT IT CHECKS. MEASURED 2026-09-07 on build Sep 07 2026 14:24:17: a session started WITHOUT DOTTALK_ALLOW_HOST_COMMANDS=1 printed BANG: refused for member.ai.regression, the children never ran, and the validator graded the .alt captures left on disk by the PREVIOUS successful run and reported PASS -- 8 of 8 markers green across TWO PROCESSES. G0 and G1 were honestly green and COULD NOT have caught it: the bang command RETURNS NORMALLY AFTER A REFUSAL, so reached-the-shell-out and shell-out-returned are both true on a run where nothing launched. They separate a launcher that DIED from one that RAN, never one that was never permitted to start. The stale-capture hazard was KNOWN -- it was written into the commit message that introduced it -- and the deletion was placed in the CHILD LAUNCHER, downstream of the very gate that refuses to start the launcher. THE FIRST REPLACEMENT WAS ALSO WRONG AND ALSO MEASURED, the same day: a transcript check for the launcher's own completion line, which a child process CANNOT deliver, because its stdout goes to the console handle and never passes through the stream the routed capture swaps. It turned a passing measurement red while the children's lines sat on the operator's screen, and pk_durability_child.ps1's own header comment had already said so in as many words. WHAT HOLDS NOW: the PARENT clears both captures in run_regression_script BEFORE anything the host-command policy can refuse, confirms they are gone by asking the filesystem rather than reading remove()'s verdict, and prints a pre-clear sentinel that validate_pk_durability() requires. A refused shell-out therefore leaves NO capture at all and is reported as an unrun measurement. THE TRANSFERABLE RULE, worth more than this spec: A GUARD AGAINST EVIDENCE SURVIVING A RUN HAS TO SIT WHERE THE RUN CANNOT SKIP IT, AND IT HAS TO ANNOUNCE ITSELF ON A CHANNEL THE GRADER ACTUALLY READS. EXPLICIT-RUN, and it should stay that way until the nesting is understood: this is the first spec that LAUNCHES PROCESSES, and what a `!` shell-out does inside REGRESSION ALL -- to the routed channel, to path slots, to a suite that already holds files open -- is UNMEASURED. Mints no catalog rows. The two child scripts carry absolute paths and that is a known debt recorded in their commit. AIF-158, 2026-09-08 -- THE FIXTURE WAS RENAMED AND THE RENAME WAS THE INSTRUMENT. PKDUR is now (EMPNO N(6,0), SID N(6,0), LNAME C(12)) with EMPNO declared PRIMARY and SID declared NOWHERE. SID stays as a LIVE CONTROL riding in the same row as the arm, written by the same APPEND: plan_sid_if_needed() mints any field with that spelling and asks no registry and no header, so PKD_G5 green beside PKD_T3 tells generation-by-name apart from generation-by-stamp. AN EARLIER CUT OF THIS MEASUREMENT HAD NO SUCH CONTROL, READ GREEN, AND PROVED ONLY THAT THE FIXTURE'S KEY FIELD WAS NAMED SID. The rename immediately exposed a defect no spec in the tree could see: finalize_appended_record() ran two generators in sequence and compute_next_numeric() restores its cursor with A.readCurrent(), which RELOADS THE RECORD BUFFER FROM DISK -- so the second generator's scan destroyed the first one's value and the declared primary key reached disk BLANK, in the declaring process, unfillable afterwards because the funnel refuses every write to a primary key. Every fixture in this tree that generates a key names it SID, so exactly one generator ever fired and there was nothing to destroy. Fixed by planning all key values first and applying them in one pass. IT THEN MEASURED THE ASYMMETRY IT WAS EXTENDED FOR, and the answer was a defect: unique_reg::primary_field() read the FILE while unique_reg::list_unique_fields() read the process map only, so a fresh process ENFORCED a key it would not MINT. PKD_T3 read .F. Fixed by merging the header-stamped primary into list_unique_fields, file first and cache second, the shape primary_field() has used since AIF-156; PKD_T3 now reads .T. PKD_T3B AND PKD_T4 ARE EXPECTED RED AND THAT IS NOT A CONCESSION. T3B is the complementary half of T3 -- both read EMPNO, one asks '= 3' and the other '= 0' -- and it exists so the arm cannot be made unfalsifiable by writing down only the outcome its author expected; measured the same day, a BLANK numeric field is not zero, so T3B reads .F. either way. T4 tries to overwrite a minted key by hand and the refusal IS the policy, so a GREEN T4 would mean enforcement had been lost.",
        false,
        false,
        RegressionValidator::PkDurabilityV1,
        true, // the spec's own markers print through the routed channel
        true  // AIF-156: needs a `!` shell-out; see ActingIdentityBracket
    }
    ,
    {
        "TAGFIELD",
        "index_field_name_resolution.dts",
        "A CDX TAG IS A FIELD NAME, AND THE INDEX LAYER NOW ASKS THE SAME RESOLVER EVERYONE ELSE ASKS (AIF-157 step 3, 2026-09-06). xfg::resolve_field_index_std is the house answer to 'which field is this name' -- it trims, lets logical names win, and for x64 tables accepts the generated 10-byte DBF descriptor token as an alias when it maps uniquely. Eleven files called it and NOTHING UNDER src/xindex/ DID: activeTagFieldIndex1() was upper-only with no trim and no alias, cdx_native_backend and cnx_backend each carried a field_index_for_tag_() (byte-for-byte copies of each other), dbarea_adapt carried a seventh-hand field_index_ci(), and BUILDLMDB had its own loop. All are routed onto the standard resolver and nothing in the corpus exercised what that changed. TWO CLAIMS, TWO MECHANISMS. (1) A tag name LONGER THAN TEN BYTES: the CDX tag directory stores names in char name[32] NUL-padded, trim_copy strips only isspace, and NUL is not isspace -- so field_name_core_ had to absorb the NUL handling that was the ONE capability the retired backend matchers had and the standard resolver lacked. Without it the consolidation was a quiet downgrade. (2) The X64 DESCRIPTOR TOKEN as an alias: COURSE_TITLE_LONG is 17 bytes and its token is COURSE_TIT, which the old upper-only compare could never have matched. THE DISCRIMINATOR IS THE ROW, NOT THE VALUE -- every marker reads TAILKEY, six bytes with nothing about its own resolution in question, and the three orders disagree at both ends, so a tag resolved to the WRONG FIELD reads T2 where T3 is demanded and an engine that walked physically reads T1. UNCOVERED AND NAMED: the mangled ~n token for two fields colliding at ten bytes, and logical-wins-over-a-colliding-token. Both want a second cut; '~' in a tag argument is an unmeasured question about the tokenizer and putting an untested parse inside the arm that proves the resolver would muddy both results. Sets all THREE path slots explicitly -- written the day MWXSHAKE was found red for re-setting two of three after a WORKSPACE SWITCH (R131). SECTION 2 ADDS THE CNX BRANCH (2026-09-06): SET ORDER TAG has TWO validation gates and they are different code -- cmd_setorder.cpp:804 asks cdx_has_tag() (which checks the CONTAINER's tag directory) and :811 asks cnx_has_tag() (which walks area.fields(), making it the SEVENTH field-name matcher in this lane and the one the first sweep missed, because that sweep went through src/xindex/ plus BUILDLMDB and stopped). It compared up_copy(trim(f.name)) with no NUL handling and no alias, so on an x64 table with an ATTACHED CNX -- legal, and by AIF-099 an attached container wins tag resolution -- it REFUSED a descriptor-token tag the resolver accepts, refusal first. Its `#n` ordinal form is NOT routed and must not be: the resolver returns -1 for `#3`, so folding it away would be the quiet downgrade field_name_core_ existed to prevent. SECTION 3 IS THE SECOND CUT (2026-09-06) AND IT IS WHERE THE POLICY ACTUALLY HAS TO CHOOSE: sections 1 and 2 never made the resolver decide anything, because every name there matched one field by one rule, so 'logical names win' had nothing to win against. plan_x64_unique_fallback walks fields IN ORDER and gives the plain token to whoever asks first, so the contest only exists when the field whose LOGICAL NAME is the contested spelling comes AFTER the field that took it as a TOKEN: STUDENT_LAST_NAME -> STUDENT_LA, STUDENT_LABEL -> STUDENT_~1, STUDENT_LA -> STUDENT_~2. Now `STUDENT_LA` is both field 3's authoritative name and field 1's descriptor token, and rule 1 says field 3 wins (T11). T10 is the MANGLED token, deferred in the first cut until '~' was measured: cmd_SETORDER reads arguments with `args >> t` (whitespace-delimited), '#' is the ordinal sigil and '~' is special to nothing. T9 is not a formality -- without it T11's negative ('not field 1') is unfalsifiable, since nothing else shows field 1 is reachable. FOUR ROWS because three cannot separate four worlds: physical T1, field 1 T2, field 2 T3, field 3 T4. STILL NOT COVERABLE FROM A FIXTURE: the resolver's ambiguity branch, which cannot fire -- the planner guarantees distinct tokens and for a generated token field_name_core_ and descriptor_key agree exactly, so at most one field can match. It is defence-in-depth, not dead weight; what is wrong is the resolver's comment implying the RESOLVER decides uniqueness when the PLANNER does. READ RULE: fourteen markers must print and all fourteen read .T.; grep -c '^? \"TAGF_'.",
        false
    }
    ,
    {
        "VARCHARRESET",
        "varchar_area_reset_regression.dts",
        "A CLOSED VARCHAR TABLE MUST NOT POISON ITS AREA (2026-09-08). DbArea::_null_layout is assigned in ONE place -- partitionTrailingSystemField() -- and was reset in NONE, because clearFields() and DbArea::close() are TWO HAND-MAINTAINED TEARDOWN LISTS over the same members and both skipped it. So a VFP table with a VARCHAR field left its bit layout in the work area when it closed; the next table opened there had isVarlengthField_() answer from the stale layout, and storeFieldsToBuffer() took the VARCHAR BRANCH for a plain C() field -- writing the value correctly and then a LENGTH BYTE into that field's last byte. have_bitmap was false on the new table, so NOTHING WAS REFUSED AND NOTHING WAS PRINTED, and the bad byte reached DISK. THE VALUE WAS NEVER LOST: \"GAMMA\" was written correctly and CHR(5) was glued to its end, where ALLTRIM cannot remove it because it is not a space -- which is why the symptom read as a lost write and was not one. THIS SPEC EXISTS BECAUSE THE FIX SHIPPED WITHOUT AN ARM. The defect was found by a SECOND-ORDER symptom -- REGRESSION ALL then an explicit REGRESSION PKPOLICY went red on four markers while PKPOLICY alone read 15 of 15 -- and EIGHT hypotheses were refuted by measurement before the AREA was suspected at all: the magic name SID, the declaration, a second APPEND, is_unique_field(), the std::cout rdbuf swap, TABLE BUFFER, the nullable table, and the regression harness itself. Nothing in the corpus asserted that closing a varchar table leaves an area clean, so nothing could see it. FOUR CASES IN FOUR AREAS, EACH DROPPING ONE PROPERTY of the caught shape, so a future red says WHICH property returned rather than merely that something did: A intervening X64 three-field (shape change alone), B intervening VFP with no varchar and no null (VFP-ness alone), C intervening VFP with V(10) AND NO NULL (the varchar alone), D the caught shape with V(10) NULL. MEASURED PRE-FIX: A green, B green, C RED, D RED -- B and C differ by ONE CHARACTER, C(10) against V(10), which is what identified the varchar and exonerated nullability, VFP-ness and shape change. AREAS ARE CONTAMINATED INDEPENDENTLY (area 2 stayed clean while area 1 was broken in the same process) and that is what lets four cases share one run without poisoning each other. NINE GUARDS AND SIX ARMS, FIFTEEN GRADED MARKERS -- count them, an errored marker PRINTS NOTHING rather than going red. Every case carries intervening_live and arm_key_minted because a red arm and a case that NEVER EXECUTED read identically; a failed guard returns UNPROVEN, not FAIL. VAR_TD_survived_reopen closes and reopens because the corruption was DURABLE and a buffer read cannot see that. NOT CLAIMED: that _extras and _null_flags are cleared on close -- as of 2026-09-08 DbArea::close() still leaves BOTH standing and no marker here can see them; that any field index other than #2 is safe; that a different varchar WIDTH behaves the same; anything across a RESTART. EXPLICIT-RUN UNTIL SOAKED on the NULLASSERT precedent -- two green runs on a build nobody changed anything on, THEN the flag moves, THEN a REBUILD, THEN read REGRESSION LIST for the [default] tag BEFORE believing the run. Disposable tables in DBF/SANDBOX, erased at both ends; mints no catalog rows. PROMOTED TO THE DEFAULT SUITE 2026-09-08, AND THE SENTENCE ABOVE ABOUT BEING EXPLICIT-RUN IS LEFT STANDING BECAUSE IT WAS THE CONDITION AT THE TIME. THREE GREEN 15/15 RUNS BEFORE THE FLAG MOVED, and the last two are the ones that count: build Sep 08 2026 15:13:56 (first green), then 15:23:52 TWICE WITH NOTHING CHANGED IN BETWEEN. The middle run alone would NOT have satisfied the soak -- a NULLASSERT summary string was edited between runs one and two, and \"a string literal cannot affect execution\" is exactly the harmlessness argument this lane spent a day being wrong about, so a third run was taken rather than the argument made. THE REASON FOR PROMOTION IS A MEASURED COVERAGE HOLE, NOT THE SOAK -- the RELSCOPE2 and NULLASSERT precedent. REGRESSION ALL could not reach ONE INCH of this: a closed varchar table poisoning its area wrote BAD BYTES TO DISK with nothing refused and nothing printed, and the suite stayed green through all of it. The defect surfaced only when an operator typed REGRESSION ALL and then REGRESSION PKPOLICY. THE VALIDATOR HAS BEEN PROVEN TO FAIL BEFORE PROMOTION, which is the half DEF_FAMILY's entry says is usually left unmeasured: no rebuild is needed because the .dts is DATA read at runtime, so the registered spec was swapped for deliberately broken copies and restored in a finally block (verified byte-identical after). Breaking an ARM read FAIL naming VAR_TC_varchar_alone with its full diagnosis and 15 markers still printed, exactly one red; breaking a GUARD read UNPROVEN naming VAR_GC_intervening_live and correctly did NOT report it as a failing arm. THE COST IS NEAR ZERO: no catalog rows (none of the three minting verbs, mints_catalog is false), no LMDB, no index containers, nine disposable tables in DBF/SANDBOX erased at both ends. IT RUNS LAST BY DECLARATION ORDER AND THAT IS NOT CLAIMED AS SAFE -- see the correction filed against NULLASSERT in this same file (8fba98c5c), which is that \"it runs last\" is a statement about ORDER and never a proof of ISOLATION. What IS true here is that it runs AFTER NULLASSERT, the spec whose leaked state started this, so the in-suite run is a live check of the fix under the exact sequence that produced the original red.",
        true,   // PROMOTED 2026-09-08 -- three green 15/15 runs, the last two on a
                // build nobody changed anything on; see the summary for the
                // coverage argument and for the validator's proven FAIL path
        false,
        RegressionValidator::VarcharAreaResetV1,
        true // markers are `?` output; the routed capture is a SUPERSET, per PKPOLICY
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
        << "  - REGRESSION launches DOTSCRIPT; selected specs also validate marked\n"
        << "    transcript evidence and set final PASS/FAIL error status.\n"
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

// ---------------------------------------------------------------------------
// ACTING-IDENTITY BRACKET -- AIF-156, owner ruling 2026-09-07.
//
// THE MEASUREMENT THIS EXISTS FOR CANNOT BE MADE ANY OTHER WAY. A .dts runs in
// ONE process, so no marker in the corpus can assert anything across a restart;
// the only route is a `!` shell-out, and `!` is refused because the shell BOOTS
// as member.public (identity_admin.cpp: g_acting = kAnon) and never
// authenticates. That refusal is CORRECT and is not being removed -- BANG is
// arbitrary shell execution and gating it is the right default.
//
// WHAT THIS DOES INSTEAD is assume a NAMED identity for the duration of ONE
// flagged spec and put the previous one back. The grant lives in the identity
// tables where an auditor can read it, not in this code: nothing here creates a
// member, and nothing here grants a permission. If member.ai.regression does
// not exist or has no live host.shell grant, the shell-out is refused exactly
// as it is today and the spec's own guards report an unrun measurement rather
// than a passing one.
//
// SCOPE IS THE POINT. Restoration is by destructor so an exception or an early
// return cannot leave the suite elevated, and the previous key is captured by
// VALUE because acting_member_key() returns a reference to the very global this
// overwrites.
class ActingIdentityBracket {
public:
    explicit ActingIdentityBracket(const std::string& spec_name)
        : prev_(dottalk::identity::acting_member_key())   // by value, deliberately
    {
        dottalk::identity::set_acting_member(kShellIdentity);
        std::cout << "REGRESSION: " << spec_name << " runs as " << kShellIdentity
                  << " (was " << prev_ << ") -- it needs a host shell.\n"
                  << "  The host-command policy still applies on top of this; the "
                     "identity is restored when the spec returns.\n";
    }

    ~ActingIdentityBracket()
    {
        dottalk::identity::set_acting_member(prev_);
        std::cout << "REGRESSION: acting identity restored to " << prev_ << "\n";
    }

    ActingIdentityBracket(const ActingIdentityBracket&) = delete;
    ActingIdentityBracket& operator=(const ActingIdentityBracket&) = delete;

    static constexpr const char* kShellIdentity = "member.ai.regression";

private:
    std::string prev_;
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

// PATH-SLOT BRACKET -- the leak CatalogBracket's reasoning never covered.
//
// MEASURED 2026-09-06, one fresh session, three commands:
//     REGRESSION CNXLIVE    -> 7/7 green
//     REGRESSION MWXSHAKE   -> MWX_G6, MWX_T25, MWX_T26 RED, and the engine
//                              printed the cause: "SET ORDER: openCdx: LMDB env
//                              missing: ...\data\lmdb\STUDENTS.cdx.d"
//     REGRESSION CNXLIVE    -> 7/7 green again
//
// MWXSHAKE did not fail on its own behaviour. CNXLIVE ran first, its `DO x32`
// moved the INDEXES slot to INDEXES\x32 and left LMDB where it found it, and
// MWXSHAKE inherited both. The same MWXSHAKE line that printed
// "INDEXES = ...\INDEXES\SANDBOX, LMDB = ...\LMDB\SANDBOX" inside REGRESSION
// ALL printed "INDEXES = ...\INDEXES\x32, LMDB = ...\data\lmdb" here. Same
// spec, same line, different session history.
//
// THE CHANNEL IS R131. A workspace carries its own environment, DEFAULT
// included, and DEFAULT captures whatever the session slots hold. So a spec
// that moves a slot writes it into DEFAULT, and the NEXT spec gets it back the
// moment it does WORKSPACE SWITCH DEFAULT. The leak runs in both directions and
// through every spec, which is why it reads as "the suite poisons whatever runs
// after it" rather than as one bad actor.
//
// WHAT MAKES IT BITE is a spec setting SOME of the three slots. `DO x32` moves
// DBF and INDEXES and not LMDB; several specs do the same. A spec that sets two
// of three inherits the third from whoever ran before it, and inherits it
// silently -- openCdx then fails on a path nothing in the spec ever named.
//
// UNCONDITIONAL, unlike CatalogBracket's mints_catalog flag. A spec that mints
// catalog rows can be identified by reading it; a spec that moves a path slot
// cannot, because DO, SET PATH and WORKSPACE SWITCH all move slots and any of
// them can arrive through a nested script. Restoring a slot that never moved is
// a no-op; skipping a restore that was needed is the defect -- the same
// argument WorkspacesSlotGuard's destructor already makes.
//
// THE THREE R131 SLOTS ONLY. Not SCRIPTS -- resolve_regression_script_path
// reads it and the note at the call site says this must not disturb it. Not
// WORKSPACES -- CatalogBracket owns that one and nesting two owners over one
// slot is how a restore gets skipped.
//
// IT ANNOUNCES ONLY WHEN A SLOT ACTUALLY MOVED. A line per spec would drown the
// transcript and teach people to skim it; a line only when something leaked is
// the signal, and it names the spec so the leak has an owner.
class PathSlotBracket {
public:
    explicit PathSlotBracket(std::string spec_name)
        : spec_(std::move(spec_name)),
          dbf_(dottalk::paths::get_slot(dottalk::paths::Slot::DBF)),
          indexes_(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES)),
          lmdb_(dottalk::paths::get_slot(dottalk::paths::Slot::LMDB))
    {
    }

    ~PathSlotBracket()
    {
        restore_one(dottalk::paths::Slot::DBF,     dbf_,     "DBF");
        restore_one(dottalk::paths::Slot::INDEXES, indexes_, "INDEXES");
        restore_one(dottalk::paths::Slot::LMDB,    lmdb_,    "LMDB");
    }

    PathSlotBracket(const PathSlotBracket&) = delete;
    PathSlotBracket& operator=(const PathSlotBracket&) = delete;

private:
    void restore_one(dottalk::paths::Slot slot,
                     const std::filesystem::path& saved,
                     const char* label) const
    {
        const std::filesystem::path now = dottalk::paths::get_slot(slot);
        if (now == saved) return;
        dottalk::paths::set_slot(slot, saved);
        std::cout << "REGRESSION: path slot " << label
                  << " was left at " << now.string()
                  << " by " << spec_
                  << "; restored to " << saved.string() << "\n";
    }

    std::string spec_;
    std::filesystem::path dbf_;
    std::filesystem::path indexes_;
    std::filesystem::path lmdb_;
};

class TeeStreamBuf final : public std::streambuf {
public:
    TeeStreamBuf(std::streambuf* visible, std::streambuf* captured)
        : visible_(visible), captured_(captured)
    {
    }

protected:
    int_type overflow(int_type ch) override
    {
        if (traits_type::eq_int_type(ch, traits_type::eof())) {
            return traits_type::not_eof(ch);
        }
        const char c = traits_type::to_char_type(ch);
        if (traits_type::eq_int_type(visible_->sputc(c), traits_type::eof()) ||
            traits_type::eq_int_type(captured_->sputc(c), traits_type::eof())) {
            return traits_type::eof();
        }
        return ch;
    }

    std::streamsize xsputn(const char* text, std::streamsize count) override
    {
        const std::streamsize visible_count = visible_->sputn(text, count);
        const std::streamsize captured_count = captured_->sputn(text, count);
        return (visible_count == count && captured_count == count) ? count : 0;
    }

    int sync() override
    {
        return (visible_->pubsync() == 0 && captured_->pubsync() == 0) ? 0 : -1;
    }

private:
    std::streambuf* visible_;
    std::streambuf* captured_;
};

std::string clean_transcript_line(std::string line)
{
    if (!line.empty() && line.back() == '\r') line.pop_back();
    line = trim_copy(std::move(line));
    while (line.size() >= 2 && line[0] == '.' && line[1] == ' ') {
        line = trim_copy(line.substr(2));
    }
    return line;
}

bool transcript_block(const std::string& transcript,
                      const std::string& begin_marker,
                      const std::string& end_marker,
                      std::vector<std::string>& lines,
                      std::string& error)
{
    const std::size_t begin = transcript.find(begin_marker);
    if (begin == std::string::npos) {
        error = "missing marker " + begin_marker;
        return false;
    }

    const std::size_t body = transcript.find('\n', begin);
    if (body == std::string::npos) {
        error = "marker has no body " + begin_marker;
        return false;
    }

    const std::size_t end = transcript.find(end_marker, body + 1);
    if (end == std::string::npos) {
        error = "missing marker " + end_marker;
        return false;
    }

    std::istringstream in(transcript.substr(body + 1, end - body - 1));
    std::string line;
    while (std::getline(in, line)) {
        line = clean_transcript_line(std::move(line));
        if (!line.empty() && line != ".") lines.push_back(std::move(line));
    }
    return true;
}

std::string canonical_table_row(const std::string& line)
{
    std::istringstream in(line);
    std::string cell;
    std::string row;
    bool first = true;
    while (std::getline(in, cell, '|')) {
        if (!first) row.push_back('\x1f');
        row += trim_copy(std::move(cell));
        first = false;
    }
    return row;
}

std::string display_table_row(std::string row)
{
    std::string out;
    for (char c : row) {
        if (c == '\x1f') {
            out += " | ";
        } else {
            out.push_back(c);
        }
    }
    return out;
}

bool is_sqlite_separator(const std::string& line)
{
    bool saw_dash = false;
    for (char c : line) {
        if (c == '-') {
            saw_dash = true;
        } else if (c != '+' && c != '|' && c != ' ' && c != '\t') {
            return false;
        }
    }
    return saw_dash;
}

bool sqlsel_rows_from_block(const std::vector<std::string>& lines,
                           std::vector<std::string>& rows,
                           std::string& error)
{
    for (std::size_t i = 0; i < lines.size(); ++i) {
        const std::size_t suffix = lines[i].find(" row(s) selected.");
        if (suffix == std::string::npos) continue;

        std::size_t count = 0;
        std::istringstream count_in(lines[i].substr(0, suffix));
        if (!(count_in >> count)) {
            error = "cannot read SQLSEL row count";
            return false;
        }
        if (count == 0) {
            error = "SQLSEL block is silently empty";
            return false;
        }
        if (i < count + 1) {
            error = "SQLSEL block has fewer rows than its reported count";
            return false;
        }

        const std::size_t first_row = i - count;
        for (std::size_t r = first_row; r < i; ++r) {
            rows.push_back(canonical_table_row(lines[r]));
        }
        return true;
    }

    error = "SQLSEL block has no row-count footer";
    return false;
}

bool sqlite_rows_from_block(const std::vector<std::string>& lines,
                           std::vector<std::string>& rows,
                           std::string& error)
{
    for (std::size_t i = 0; i < lines.size(); ++i) {
        if (!is_sqlite_separator(lines[i])) continue;
        for (std::size_t r = i + 1; r < lines.size(); ++r) {
            rows.push_back(canonical_table_row(lines[r]));
        }
        if (rows.empty()) {
            error = "SQLite oracle block is silently empty";
            return false;
        }
        return true;
    }

    error = "SQLite oracle block has no table separator";
    return false;
}

struct SqlselOraclePair {
    const char* actual;
    const char* oracle;
    bool unordered = false;
};

template <std::size_t N>
bool validate_sqlsel_oracle_rows(const std::string& transcript,
                                 const char* label,
                                 const std::array<SqlselOraclePair, N>& pairs)
{
    std::size_t passed = 0;
    for (const SqlselOraclePair& pair : pairs) {
        std::vector<std::string> actual_lines;
        std::vector<std::string> oracle_lines;
        std::vector<std::string> actual_rows;
        std::vector<std::string> oracle_rows;
        std::string error;

        if (!transcript_block(transcript, std::string(pair.actual) + "-BEGIN",
                              std::string(pair.actual) + "-END", actual_lines, error) ||
            !sqlsel_rows_from_block(actual_lines, actual_rows, error) ||
            !transcript_block(transcript, std::string(pair.oracle) + "-BEGIN",
                              std::string(pair.oracle) + "-END", oracle_lines, error) ||
            !sqlite_rows_from_block(oracle_lines, oracle_rows, error)) {
            std::cout << label << ": FAIL -- " << pair.actual
                      << " vs " << pair.oracle << ": " << error << "\n";
            return false;
        }

        if (pair.unordered) {
            std::sort(actual_rows.begin(), actual_rows.end());
            std::sort(oracle_rows.begin(), oracle_rows.end());
        }
        if (actual_rows != oracle_rows) {
            std::cout << label << ": FAIL -- " << pair.actual
                      << " vs " << pair.oracle
                      << (pair.unordered ? " row multiset mismatch\n" : " row mismatch\n")
                      << "  SQLSEL rows: " << actual_rows.size() << "\n";
            for (const std::string& row : actual_rows) {
                std::cout << "    " << display_table_row(row) << "\n";
            }
            std::cout << "  SQLite rows: " << oracle_rows.size() << "\n";
            for (const std::string& row : oracle_rows) {
                std::cout << "    " << display_table_row(row) << "\n";
            }
            return false;
        }
        ++passed;
    }
    return passed == pairs.size();
}

std::size_t transcript_count(const std::string& transcript,
                             const std::string& fragment)
{
    std::size_t count = 0;
    for (std::size_t pos = 0;
         (pos = transcript.find(fragment, pos)) != std::string::npos;
         pos += fragment.size()) {
        ++count;
    }
    return count;
}

template <std::size_t N>
bool require_cdx_metadata_erased(const char* label,
                                 const std::array<const char*, N>& table_stems)
{
    for (const char* stem : table_stems) {
        std::filesystem::path meta =
            dottalk::paths::resolve_index(std::string(stem) + ".cdx");
        meta += ".meta";

        std::error_code ec;
        const bool exists = std::filesystem::exists(meta, ec);
        if (ec) {
            std::cout << label << ": FAIL -- could not inspect cleanup path '"
                      << meta.string() << "': " << ec.message() << "\n";
            return false;
        }
        if (exists) {
            std::cout << label << ": FAIL -- cleanup left CDX metadata '"
                      << meta.string() << "'\n";
            return false;
        }
    }
    return true;
}

template <std::size_t N>
bool require_transcript_fragments(const std::string& transcript,
                                  const char* label,
                                  const std::array<const char*, N>& required)
{
    for (const char* fragment : required) {
        if (transcript.find(fragment) == std::string::npos) {
            std::cout << label << ": FAIL -- missing required evidence: "
                      << fragment << "\n";
            return false;
        }
    }
    return true;
}

template <std::size_t N>
bool require_exact_transcript_block(const std::string& transcript,
                                    const char* label,
                                    const char* marker,
                                    const std::array<const char*, N>& expected)
{
    std::vector<std::string> actual;
    std::string error;
    if (!transcript_block(transcript, std::string(marker) + "-BEGIN",
                          std::string(marker) + "-END", actual, error)) {
        std::cout << label << ": FAIL -- " << error << "\n";
        return false;
    }
    if (actual.size() != expected.size()) {
        std::cout << label << ": FAIL -- " << marker << " expected "
                  << expected.size() << " line(s), got " << actual.size() << "\n";
        return false;
    }
    for (std::size_t i = 0; i < expected.size(); ++i) {
        if (actual[i] != expected[i]) {
            std::cout << label << ": FAIL -- " << marker << " line " << (i + 1)
                      << " mismatch\n"
                      << "  expected: " << expected[i] << "\n"
                      << "  actual  : " << actual[i] << "\n";
            return false;
        }
    }
    return true;
}

bool validate_sqlsel_buffer_visibility(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 5> pairs{{
        {"SQLSEL-BV-S1", "SQLSEL-BV-O1"},
        {"SQLSEL-BV-S2", "SQLSEL-BV-O2"},
        {"SQLSEL-BV-S3", "SQLSEL-BV-O3"},
        {"SQLSEL-BV-S4", "SQLSEL-BV-O4"},
        {"SQLSEL-BV-S5", "SQLSEL-BV-O5"}
    }};
    static constexpr std::array<const char*, 1> dirty_preview{{
        "1 | MATH"
    }};
    static constexpr std::array<const char*, 3> required{{
        "BV_C1_dirty_query_cursor_restored:.T.",
        "BV_C2_rollback_query_cursor_restored:.T.",
        "BV_C3_commit_query_cursor_restored:.T."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL BUFFER ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL BUFFER ORACLE",
                                        "SQLSEL-BV-DIRTY-TUPLE", dirty_preview) ||
        !require_exact_transcript_block(transcript, "SQLSEL BUFFER ORACLE",
                                        "SQLSEL-BV-DIRTY-TUPLE-AFTER", dirty_preview) ||
        !require_transcript_fragments(transcript, "SQLSEL BUFFER ORACLE", required)) {
        return false;
    }

    std::cout << "SQLSEL BUFFER ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " committed row sets equal SQLite; dirty preview 2/2; "
              << "cursors 3/3; rollback and commit distinguished.\n";
    return true;
}

// COUNT LIST / COUNT VERBOSE -- the behaviours folded out of the retired `SQL`
// scanner (owner ruling 2026-09-04).
//
// CLV_T3 IS THE ONLY ARM THAT CAN REFUTE THE DEFECT THIS CHANGE WAS MADE FOR,
// and the others exist to keep it honest. The retired scanner walked the table
// with a private loop that never consulted SET FILTER, so it reported the
// UNFILTERED population. With `SET FILTER TO MAJOR = "CSCI"` the fixture's
// logical rowset is three rows, two of them matching -- so `scanned 3,
// matched 2` is the reading only a filter-honouring implementation produces.
// The unfiltered arm above it (`scanned 5, matched 3`) would read identically
// against the defect and proves nothing on its own; it is here so that a
// failure can be localized to the filter rather than to the fixture.
//
// CLV_T0 IS A NON-REGRESSION ARM, not a feature arm. The fold must not have
// changed what a bare COUNT prints, so this asserts the block is EXACTLY one
// line carrying the number. An extra row line leaking into the default path
// would be invisible to every fragment check in this file.
// THIS VALIDATOR READS THE ALTERNATE CAPTURE, NOT THE std::cout TEE, and the
// difference is the whole reason the first run of this spec went red. Every
// line COUNT prints -- the number, the row lines, the scanned/matched summary --
// goes through cmd_count.cpp's local print_line, whose sink is
// OutputRouter::out(). The tee cannot see that channel, so on 2026-09-04 CLV-T0
// read "expected 1 line(s), got 0" while the operator watched the line print.
// The spec carries capture_routed_channel = true and run_regression_script
// hands this function the SET ALTERNATE file instead.
bool validate_count_list_verbose(const std::string& transcript)
{
    static constexpr std::array<const char*, 1> t0{{"5"}};
    if (!require_exact_transcript_block(transcript, "COUNT LIST/VERBOSE", "CLV-T0", t0)) {
        return false;
    }

    static constexpr std::array<const char*, 6> required{{
        // T1: LIST names the predicate's field and prints no verdict.
        "[rec 1] GPA=",
        "[rec 5] GPA=",
        // T2: unfiltered scope.
        "scanned 5, matched 3",
        // T3: THE DISCRIMINATOR -- the filtered scope.
        "scanned 3, matched 2",
        // T4: the reserved verb answers, and points at the command that replaced it.
        "SQL: reserved verb -- it no longer scans records.",
        "COUNT VERBOSE FOR <expr>"
    }};
    if (!require_transcript_fragments(transcript, "COUNT LIST/VERBOSE", required)) {
        return false;
    }

    // The reserved verb must not have COUNTED. Two verbose runs are expected in
    // the whole transcript (T2 and T3); a third would mean `SQL COUNT FOR ...`
    // still scanned something, which is the retirement failing silently.
    const std::size_t summaries = transcript_count(transcript, "scanned ");
    if (summaries != 2) {
        std::cout << "COUNT LIST/VERBOSE: FAIL -- expected exactly 2 scanned/matched "
                     "summaries, got " << summaries
                  << ". A third means the reserved SQL verb still scans.\n";
        return false;
    }

    std::cout << "COUNT LIST/VERBOSE: PASS -- default output unchanged, LIST and\n"
                 "  VERBOSE report from the same selection, and SET FILTER narrows\n"
                 "  the rowset the retired scanner ignored.\n";
    return true;
}

// DEF_FAMILY -- the runtime DEF-family testbed (RUNTIME_DEF_FAMILY lane).
//
// WHY THIS EXISTS AT ALL, and it is the finding rather than the feature: until
// 2026-09-05 THIS SPEC HAD NO VALIDATOR. It carried DEF-FAMILY-REGRESSION-BEGIN
// and -END -- the exact affordance require_exact_transcript_block consumes, the
// same one BV_C1, S5A and J6A use -- and NOTHING IN THIS FILE CONSUMED THEM. Its
// own header said "Expected (grep the transcript between BEGIN/END)": the grader
// was a human eye. MEASURED, not inferred: on 2026-09-05 REGRESSION RUN DEF_FAMILY
// printed its transcript, both L3 arms reported 6/6, and DEF_FAMILY reported NO
// VERDICT OF ANY KIND -- neither PASS nor FAIL nor a marker count. A spec in that
// state CANNOT GO RED, so promoting it to the default suite would have added a
// permanently green line that means nothing. An unrunnable gate reads exactly like
// an ungated lane, and this one had the SHAPE of a graded spec, which is worse
// than having no shape at all.
//
// WHY AN EXACT BLOCK AND NOT FRAGMENTS. Nothing here is a data row. Every claim is
// "this label is IMMEDIATELY FOLLOWED BY this answer", and fragments prove presence,
// not adjacency: `hello` appearing somewhere in the transcript is not evidence that
// GREETFN() returned it. The block asserts content, order and COUNT at once, and the
// count is what catches an arm that quietly stopped printing.
//
// WHY NOT .T. MARKERS, which is the house default and is wrong here: DEFCMD's whole
// subject is the output of an EXECUTED COMMAND, and a marker cannot see console text
// -- the standing limit recorded against NULLASSERT one entry-family over. The
// transcript block can see it. For DEFCMD it is the only instrument that can.
//
// TWO KNOWN BRITTLENESSES, STATED HERE RATHER THAN DISCOVERED IN A RED RUN:
//   - LOCALE. "Unknown command: PINGCMD" is MessageId::UnknownCommand rendered
//     en-US; helpdata_messages.cpp carries it/es/fr/de renderings of that same id.
//     Run the suite under another locale and this arm reds for a reason that is not
//     a defect. No other arm in this block is localized.
//   - UI TEXT. Any added echo line in cmd_defcmd/cmd_deffn breaks the block. That is
//     the POINT for an undeliberate change, and one edit to this array for a
//     deliberate one.
//
// ROUTED CHANNEL -- the spec carries capture_routed_channel = true, and it must.
// "Unknown command: PINGCMD" is CommandRegistry::run -> cli::cmdout::print_line
// (command_registry.cpp:203), a channel a std::cout rdbuf swap CANNOT SEE. That is
// the CLV lesson of 2026-09-04, one day old when this was written, and skipping it
// here would have cost the same red run for the same instrument reason. The other
// twenty-one lines are raw std::cout out of cmd_defcmd/cmd_deffn and reach the same
// file because shell.cpp:574 wraps every shell command in push_cout_redirect(), so
// both channels share one stream and interleave correctly.
//
// NOT CLAIMED, stated rather than implied: that a DEFFN body can USE its arguments.
// It cannot -- the MVP body returns its stored text and ignores argv -- so the one
// argument arm here (DEFCMD_args) is about a COMMAND, not a function. When the
// formula body lands this block grows an arm; until then the gap is the spec's and
// not the validator's, and a reader should not mistake a green DEF_FAMILY for
// evidence that custom functions take parameters.
bool validate_def_family(const std::string& transcript)
{
    static constexpr std::array<const char*, 22> expected{{
        "EXAMPLE_TEST_expect_OK:",
        "OK",
        "DEFCMD: defined PINGCMD",
        "DEFCMD_invoke_expect_DEFCMD_BODY_OK:",
        "DEFCMD_BODY_OK",
        "DEFCMD_args_expect_DEFCMD_BODY_OK_a_b:",
        "DEFCMD_BODY_OK a b",
        "Scratch commands (1):",
        "PINGCMD = DEFCMD_BODY_OK",
        "UNDEFCMD: removed PINGCMD",
        "DEFCMD_removed_expect_Unknown_PINGCMD:",
        "Unknown command: PINGCMD",
        "DEFFN: defined GREETFN",
        "DEFFN_resolve_expect_hello:",
        "hello",
        "DEFFN_compose_expect_HELLO:",
        "HELLO",
        "Custom functions (1):",
        "GREETFN",
        "UNDEFFN: removed GREETFN",
        "DEFFN_removed_expect_error:",
        "FORMULA error: function evaluation failed -- in: GREETFN()"
    }};

    if (!require_exact_transcript_block(transcript, "DEF FAMILY",
                                        "DEF-FAMILY-REGRESSION", expected)) {
        return false;
    }

    std::cout << "DEF FAMILY: PASS -- 22 line(s), exact and in order. DEFCMD and DEFFN\n"
                 "  each DEFINE, INVOKE, LIST and REMOVE at runtime with no rebuild;\n"
                 "  DEFFN resolves inside `?` and composes with a builtin (UPPER);\n"
                 "  both are GONE after removal -- the command unknown, the function\n"
                 "  refusing to evaluate.\n";
    return true;
}

bool validate_sqlsel_select_oracle(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 12> pairs{{
        {"SQLSEL-S1", "SQLSEL-O1"},
        {"SQLSEL-S2", "SQLSEL-O2"},
        {"SQLSEL-S3", "SQLSEL-O3"},
        {"SQLSEL-S4", "SQLSEL-O4"},
        {"SQLSEL-S6Q", "SQLSEL-O6"},
        {"SQLSEL-S8A", "SQLSEL-O8A"},
        {"SQLSEL-S8D", "SQLSEL-O8D"},
        {"SQLSEL-S9", "SQLSEL-O9"},
        {"SQLSEL-S10A", "SQLSEL-O10A"},
        {"SQLSEL-S10F", "SQLSEL-O10F"},
        {"SQLSEL-S13Q", "SQLSEL-O13"},
        {"SQLSEL-S14", "SQLSEL-O14"}
    }};
    static constexpr std::array<const char*, 10> required{{
        "S5A_cursor_parked_before:.T.",
        "S5B_cursor_unmoved_after:.T.",
        "S12_cursor_unmoved_after_slice2:.T.",
        "SQLSEL: table 'NOSUCHTABLE' is not open.",
        "SQLSEL: LIMIT expects a non-negative integer (got 'abc').",
        "SQLSEL: ORDER BY field 'NOSUCHFIELD' is not in SQLSTU.",
        "SQLSEL: ORDER BY direction must be ASC or DESC (got 'SIDEWAYS').",
        "SQLSEL: ORDER BY does not apply to COUNT(*).",
        "SQLSEL: predicate evaluation failed: unknown field 'NOSUCH'",
        "SQLSEL: predicate evaluation failed: incompatible field/literal types in comparison"
    }};
    static const std::string limit_report = "SQLSEL: LIMIT reached;";
    static const std::string sort_report = " -- materialized sort over ";

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL SELECT ORACLE", pairs) ||
        !require_transcript_fragments(transcript, "SQLSEL SELECT ORACLE", required)) {
        return false;
    }
    const std::size_t limit_count = transcript_count(transcript, limit_report);
    if (limit_count != 2) {
        std::cout << "SQLSEL SELECT ORACLE: FAIL -- expected 2 LIMIT reports, got "
                  << limit_count << "\n";
        return false;
    }
    const std::size_t sort_count = transcript_count(transcript, sort_report);
    if (sort_count != 4) {
        std::cout << "SQLSEL SELECT ORACLE: FAIL -- expected 4 sort-path reports, got "
                  << sort_count << "\n";
        return false;
    }

    std::cout << "SQLSEL SELECT ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row sets equal SQLite; cursors 3/3; "
              << "typed expression projection proven; refusals 7/7; "
              << "LIMIT reports 2/2; sort paths 4/4.\n";
    return true;
}

bool validate_sqlsel_join_oracle(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 4> pairs{{
        {"SQLSEL-J1-J2", "SQLSEL-O1"},
        {"SQLSEL-J3", "SQLSEL-O3"},
        {"SQLSEL-J4", "SQLSEL-O4"},
        {"SQLSEL-J5", "SQLSEL-O5"}
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL JOIN ORACLE", pairs)) {
        return false;
    }

    static constexpr std::array<const char*, 5> required{{
        "J6A_left_cursor_restored:.T.",
        "J6B_right_cursor_restored:.T.",
        "SQLSEL: column 'SID' is ambiguous; qualify it with a table alias.",
        "SQLSEL: JOIN ON columns must be qualified (got 'SID').",
        "SQLSEL: table 'NOSUCH' is not open."
    }};
    if (!require_transcript_fragments(transcript, "SQLSEL JOIN ORACLE", required)) {
        return false;
    }

    static const std::string access_prefix =
        "SQLSEL: INNER JOIN access path -- ";
    static const std::string seek_path =
        "SQLSEL: INNER JOIN access path -- CDX seek";
    static const std::string scan_path =
        "SQLSEL: INNER JOIN access path -- nested-loop scan";
    static const std::string hybrid_path =
        "SQLSEL: INNER JOIN access path -- hybrid";
    const std::size_t access_path_count = transcript_count(transcript, access_prefix);
    const std::size_t seek_path_count = transcript_count(transcript, seek_path);
    const std::size_t scan_path_count = transcript_count(transcript, scan_path);
    const std::size_t hybrid_path_count = transcript_count(transcript, hybrid_path);
    if (access_path_count != pairs.size() || seek_path_count != 2 ||
        scan_path_count != 2 || hybrid_path_count != 0) {
        std::cout << "SQLSEL JOIN ORACLE: FAIL -- expected 4 access paths"
                  << " (2 CDX seek, 2 nested-loop scan, 0 hybrid); got "
                  << access_path_count << " (" << seek_path_count << " CDX seek, "
                  << scan_path_count << " nested-loop scan, " << hybrid_path_count
                  << " hybrid)\n";
        return false;
    }

    static constexpr std::array<const char*, 1> cleanup_tables{{"SQLJENR"}};
    if (!require_cdx_metadata_erased("SQLSEL JOIN ORACLE", cleanup_tables)) {
        return false;
    }

    std::cout << "SQLSEL JOIN ORACLE: PASS -- " << pairs.size() << '/' << pairs.size()
              << " row sets equal SQLite; cursors 2/2; refusals 3/3; access paths "
              << access_path_count << '/' << pairs.size()
              << " (CDX seek 2, scan 2); cleanup 1/1.\n";
    return true;
}

bool validate_sqlsel_join_edges(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 4> pairs{{
        {"SQLSEL-JE-NUM-SEEK", "SQLSEL-JE-ON1"},
        {"SQLSEL-JE-NUM-SCAN", "SQLSEL-JE-ON2"},
        {"SQLSEL-JE-CHAR-SEEK", "SQLSEL-JE-OC1"},
        {"SQLSEL-JE-CHAR-SCAN", "SQLSEL-JE-OC2"}
    }};
    static constexpr std::array<const char*, 9> required{{
        "JE_C1_numeric_left_cursor_restored:.T.",
        "JE_C2_numeric_right_cursor_restored:.T.",
        "JE_C3_char_left_cursor_restored:.T.",
        "JE_C4_char_right_cursor_restored:.T.",
        "JE_T1_caller_table_lock_preserved:.T.",
        "SQLSEL: INNER JOIN access path -- CDX seek (inner=SQLJNR, tag=ID, probes=3, candidates=3).",
        "SQLSEL: INNER JOIN access path -- nested-loop scan (outer=5 row(s), inner=4 row(s)).",
        "SQLSEL: INNER JOIN access path -- CDX seek (inner=SQLJCR, tag=CKEY, probes=3, candidates=8).",
        "SQLSEL: INNER JOIN access path -- nested-loop scan (outer=4 row(s), inner=6 row(s))."
    }};
    static constexpr std::array<const char*, 2> refusals{{
        "SQLSEL: joined table aliases must be distinct.",
        "SQLSEL: JOIN ON must compare one column from each table."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL JOIN EDGES ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL JOIN EDGES ORACLE",
                                        "SQLSEL-JE-REFUSALS", refusals) ||
        !require_transcript_fragments(transcript, "SQLSEL JOIN EDGES ORACLE", required)) {
        return false;
    }

    static const std::string transaction_prefix =
        "SQLSEL: INNER JOIN read transaction -- table fence (";
    static const std::string numeric_fence =
        "SQLSEL: INNER JOIN read transaction -- table fence (SQLJNL -> SQLJNR).";
    static const std::string character_fence =
        "SQLSEL: INNER JOIN read transaction -- table fence (SQLJCL -> SQLJCR).";
    if (transcript_count(transcript, transaction_prefix) != 4 ||
        transcript_count(transcript, numeric_fence) != 2 ||
        transcript_count(transcript, character_fence) != 2) {
        std::cout << "SQLSEL JOIN EDGES ORACLE: FAIL -- expected 4 canonical read "
                     "transactions (2 numeric, 2 character)\n";
        return false;
    }

    static const std::string access_prefix =
        "SQLSEL: INNER JOIN access path -- ";
    static const std::string seek_path =
        "SQLSEL: INNER JOIN access path -- CDX seek";
    static const std::string scan_path =
        "SQLSEL: INNER JOIN access path -- nested-loop scan";
    static const std::string hybrid_path =
        "SQLSEL: INNER JOIN access path -- hybrid";
    const std::size_t access_path_count = transcript_count(transcript, access_prefix);
    const std::size_t seek_path_count = transcript_count(transcript, seek_path);
    const std::size_t scan_path_count = transcript_count(transcript, scan_path);
    const std::size_t hybrid_path_count = transcript_count(transcript, hybrid_path);
    if (access_path_count != 4 || seek_path_count != 2 || scan_path_count != 2 ||
        hybrid_path_count != 0) {
        std::cout << "SQLSEL JOIN EDGES ORACLE: FAIL -- expected 4 access paths"
                  << " (2 CDX seek, 2 nested-loop scan, 0 hybrid); got "
                  << access_path_count << " (" << seek_path_count << " CDX seek, "
                  << scan_path_count << " nested-loop scan, " << hybrid_path_count
                  << " hybrid)\n";
        return false;
    }

    static constexpr std::array<const char*, 2> cleanup_tables{{"SQLJNR", "SQLJCR"}};
    if (!require_cdx_metadata_erased("SQLSEL JOIN EDGES ORACLE", cleanup_tables)) {
        return false;
    }

    std::cout << "SQLSEL JOIN EDGES ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row sets equal SQLite; cursors 4/4; refusals 2/2; "
              << "read transactions 4/4; caller lock preserved; "
              << "access paths 4/4 (CDX seek 2, scan 2, hybrid 0); "
              << "probe/candidate counts exact; cleanup 2/2.\n";
    return true;
}

bool validate_sqlsel_left_join(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 7> pairs{{
        {"SQLSEL-LJ-SEEK-ROWS", "SQLSEL-LJ-O1"},
        {"SQLSEL-LJ-SEEK-COUNT", "SQLSEL-LJ-O2"},
        {"SQLSEL-LJ-SCAN-ROWS", "SQLSEL-LJ-O3"},
        {"SQLSEL-LJ-SCAN-COUNT", "SQLSEL-LJ-O4"},
        {"SQLSEL-LJ-SEEK-WHERE", "SQLSEL-LJ-O5"},
        {"SQLSEL-LJ-SCAN-WHERE", "SQLSEL-LJ-O6"},
        {"SQLSEL-LJ-UNKNOWN-OR-TRUE", "SQLSEL-LJ-O7"}
    }};
    static constexpr std::array<const char*, 9> required{{
        "LJ_C1_left_cursor_restored:.T.",
        "LJ_C2_right_cursor_restored:.T.",
        "LJ_T1_caller_table_lock_preserved:.T.",
        "SQLSEL: LEFT JOIN access path -- CDX seek (inner=SQLLJR, tag=ID, probes=5, candidates=4).",
        "SQLSEL: LEFT JOIN access path -- nested-loop scan (outer=6 row(s), inner=6 row(s)).",
        "SQLSEL: LEFT JOIN left-extended 2 row(s) with <UNMATCHED> right-side cells.",
        "L2 | ",
        "L3 | <UNMATCHED>",
        "L5 | <UNMATCHED>"
    }};
    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL LEFT JOIN ORACLE", pairs) ||
        !require_transcript_fragments(transcript, "SQLSEL LEFT JOIN ORACLE", required)) {
        return false;
    }

    const std::size_t seek_count = transcript_count(
        transcript, "SQLSEL: LEFT JOIN access path -- CDX seek");
    const std::size_t scan_count = transcript_count(
        transcript, "SQLSEL: LEFT JOIN access path -- nested-loop scan");
    const std::size_t hybrid_count = transcript_count(
        transcript, "SQLSEL: LEFT JOIN access path -- hybrid");
    const std::size_t fence_count = transcript_count(
        transcript, "SQLSEL: LEFT JOIN read transaction -- table fence (SQLLJL -> SQLLJR).");
    const std::size_t extended_count = transcript_count(
        transcript, "SQLSEL: LEFT JOIN left-extended 2 row(s) with <UNMATCHED> right-side cells.");
    if (seek_count != 3 || scan_count != 4 || hybrid_count != 0 ||
        fence_count != pairs.size() || extended_count != pairs.size()) {
        std::cout << "SQLSEL LEFT JOIN ORACLE: FAIL -- expected paths 3 seek/4 scan/0 hybrid, "
                  << "fences 7, extension reports 7; got "
                  << seek_count << '/' << scan_count << '/' << hybrid_count << ", "
                  << fence_count << ", " << extended_count << "\n";
        return false;
    }

    static constexpr std::array<const char*, 1> cleanup_tables{{"SQLLJR"}};
    if (!require_cdx_metadata_erased("SQLSEL LEFT JOIN ORACLE", cleanup_tables)) {
        return false;
    }

    std::cout << "SQLSEL LEFT JOIN ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row sets equal SQLite; blank and produced absence distinct; "
              << "outer WHERE and UNKNOWN proven; left-extended reports 7/7; cursors 2/2; "
              << "caller lock preserved; paths 3 seek/4 scan/0 hybrid; read fences 7/7; "
              << "cleanup 1/1.\n";
    return true;
}

bool validate_sqlsel_join_family(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 14> pairs{{
        {"SQLSEL-JF-RIGHT-SEEK-ROWS", "SQLSEL-JF-O1", true},
        {"SQLSEL-JF-RIGHT-SEEK-COUNT", "SQLSEL-JF-O2", true},
        {"SQLSEL-JF-FULL-SEEK-ROWS", "SQLSEL-JF-O3", true},
        {"SQLSEL-JF-FULL-SEEK-COUNT", "SQLSEL-JF-O4", true},
        {"SQLSEL-JF-RIGHT-SCAN-ROWS", "SQLSEL-JF-O5", true},
        {"SQLSEL-JF-RIGHT-SCAN-COUNT", "SQLSEL-JF-O6", true},
        {"SQLSEL-JF-FULL-SCAN-ROWS", "SQLSEL-JF-O7", true},
        {"SQLSEL-JF-FULL-SCAN-COUNT", "SQLSEL-JF-O8", true},
        {"SQLSEL-JF-CROSS-ROWS", "SQLSEL-JF-O9", true},
        {"SQLSEL-JF-CROSS-COUNT", "SQLSEL-JF-O10", true},
        {"SQLSEL-JF-RIGHT-SEEK-WHERE", "SQLSEL-JF-O11", true},
        {"SQLSEL-JF-FULL-SEEK-WHERE", "SQLSEL-JF-O12", true},
        {"SQLSEL-JF-RIGHT-SCAN-WHERE", "SQLSEL-JF-O13", true},
        {"SQLSEL-JF-FULL-SCAN-WHERE", "SQLSEL-JF-O14", true}
    }};
    static constexpr std::array<const char*, 12> required{{
        "JF_C1_left_cursor_restored:.T.",
        "JF_C2_right_cursor_restored:.T.",
        "JF_T1_caller_table_lock_preserved:.T.",
        "SQLSEL: RIGHT JOIN access path -- CDX seek (inner=SQLJFR, tag=ID, probes=5, candidates=5).",
        "SQLSEL: RIGHT JOIN access path -- nested-loop scan (outer=6 row(s), inner=7 row(s)).",
        "SQLSEL: FULL JOIN access path -- CDX seek (inner=SQLJFR, tag=ID, probes=5, candidates=5).",
        "SQLSEL: FULL JOIN access path -- nested-loop scan (outer=6 row(s), inner=7 row(s)).",
        "SQLSEL: CROSS JOIN access path -- nested-loop scan (outer=6 row(s), inner=7 row(s)).",
        "2 |  | 2 | R2",
        "<UNMATCHED> | <UNMATCHED> | 7 | ",
        "3 | <UNMATCHED> | <UNMATCHED> | <UNMATCHED>",
        "6 | L6_ONLY | <UNMATCHED> | <UNMATCHED>"
    }};
    static constexpr std::array<const char*, 3> refusals{{
        "SQLSEL: CROSS JOIN does not accept an ON clause.",
        "SQLSEL: RIGHT JOIN requires ON <left-column> = <right-column>.",
        "SQLSEL: FULL JOIN requires ON <left-column> = <right-column>."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL JOIN FAMILY ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL JOIN FAMILY ORACLE",
                                        "SQLSEL-JF-REFUSALS", refusals) ||
        !require_transcript_fragments(transcript, "SQLSEL JOIN FAMILY ORACLE", required)) {
        return false;
    }

    const std::size_t right_seek = transcript_count(
        transcript, "SQLSEL: RIGHT JOIN access path -- CDX seek");
    const std::size_t right_scan = transcript_count(
        transcript, "SQLSEL: RIGHT JOIN access path -- nested-loop scan");
    const std::size_t full_seek = transcript_count(
        transcript, "SQLSEL: FULL JOIN access path -- CDX seek");
    const std::size_t full_scan = transcript_count(
        transcript, "SQLSEL: FULL JOIN access path -- nested-loop scan");
    const std::size_t cross_scan = transcript_count(
        transcript, "SQLSEL: CROSS JOIN access path -- nested-loop scan");
    const std::size_t hybrid = transcript_count(
        transcript, "JOIN access path -- hybrid");
    const std::size_t fence_count = transcript_count(
        transcript, "JOIN read transaction -- table fence (SQLJFL -> SQLJFR).");
    const std::size_t right_extended = transcript_count(
        transcript, "SQLSEL: RIGHT JOIN right-extended 3 row(s) with <UNMATCHED> left-side cells.");
    const std::size_t full_left_extended = transcript_count(
        transcript, "SQLSEL: FULL JOIN left-extended 2 row(s) with <UNMATCHED> right-side cells.");
    const std::size_t full_right_extended = transcript_count(
        transcript, "SQLSEL: FULL JOIN right-extended 3 row(s) with <UNMATCHED> left-side cells.");
    if (right_seek != 3 || right_scan != 3 || full_seek != 3 || full_scan != 3 ||
        cross_scan != 2 || hybrid != 0 || fence_count != pairs.size() ||
        right_extended != 6 || full_left_extended != 6 || full_right_extended != 6) {
        std::cout << "SQLSEL JOIN FAMILY ORACLE: FAIL -- expected RIGHT 3 seek/3 scan, "
                     "FULL 3 seek/3 scan, CROSS 2 scan, 0 hybrid, 14 fences, "
                     "and extension reports RIGHT 6/FULL-left 6/FULL-right 6; got "
                  << right_seek << '/' << right_scan << ", "
                  << full_seek << '/' << full_scan << ", " << cross_scan << ", "
                  << hybrid << ", " << fence_count << ", " << right_extended << '/'
                  << full_left_extended << '/' << full_right_extended << "\n";
        return false;
    }

    static constexpr std::array<const char*, 1> cleanup_tables{{"SQLJFR"}};
    if (!require_cdx_metadata_erased("SQLSEL JOIN FAMILY ORACLE", cleanup_tables)) {
        return false;
    }

    std::cout << "SQLSEL JOIN FAMILY ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row multisets equal SQLite; RIGHT/FULL absence and "
              << "outer WHERE/UNKNOWN and CROSS product proven; cursors 2/2; caller lock "
              << "preserved; refusals 3/3; paths RIGHT 3 seek/3 scan, FULL 3 seek/3 scan, "
              << "CROSS 2 scan; hybrid 0; fences 14/14; extension reports 18/18; "
              << "cleanup 1/1.\n";
    return true;
}

bool validate_sqlsel_set_operations(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 7> pairs{{
        {"SQLSEL-SO-DISTINCT", "SQLSEL-SO-O1", true},
        {"SQLSEL-SO-UNION", "SQLSEL-SO-O2", true},
        {"SQLSEL-SO-UNION-ALL", "SQLSEL-SO-O3", true},
        {"SQLSEL-SO-INTERSECT", "SQLSEL-SO-O4", true},
        {"SQLSEL-SO-EXCEPT", "SQLSEL-SO-O5", true},
        {"SQLSEL-SO-PRECEDENCE", "SQLSEL-SO-O6", true},
        {"SQLSEL-SO-DATE", "SQLSEL-SO-O7", true}
    }};
    static constexpr std::array<const char*, 3> cursors{{
        "SO_C1_left_cursor_restored:.T.",
        "SO_C2_right_cursor_restored:.T.",
        "SO_C3_third_cursor_restored:.T."
    }};
    static constexpr std::array<const char*, 6> refusals{{
        "SQLSEL: set operands have 1 and 2 columns; counts must match.",
        "SQLSEL: set operand column 1 has incompatible types 'N' and 'C'.",
        "SQLSEL: set operand column 1 has incompatible types 'D' and 'C'.",
        "SQLSEL: INTERSECT ALL is not part of the SQLsel P4.5 set-operation contract.",
        "SQLSEL: every set operator requires a SELECT operand on both sides.",
        "SQLSEL: P4.5 set expressions do not accept ORDER BY or LIMIT; materialize or filter each source before combining it."
    }};
    static constexpr std::array<const char*, 8> operation_reports{{
        "SQLSEL: DISTINCT reduced 5 row(s) to 4 row(s).",
        "SQLSEL: UNION set operation -- left=5, right=5, output=6.",
        "SQLSEL: UNION ALL set operation -- left=5, right=5, output=10.",
        "SQLSEL: INTERSECT set operation -- left=5, right=5, output=2.",
        "SQLSEL: EXCEPT set operation -- left=5, right=5, output=2.",
        "SQLSEL: INTERSECT set operation -- left=5, right=1, output=1.",
        "SQLSEL: UNION set operation -- left=5, right=1, output=5.",
        "SQLSEL: UNION set operation -- left=4, right=3, output=3."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL SET OPERATIONS ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL SET OPERATIONS ORACLE",
                                        "SQLSEL-SO-REFUSALS", refusals) ||
        !require_transcript_fragments(transcript, "SQLSEL SET OPERATIONS ORACLE", cursors) ||
        !require_transcript_fragments(transcript, "SQLSEL SET OPERATIONS ORACLE",
                                      operation_reports)) {
        return false;
    }

    std::cout << "SQLSEL SET OPERATIONS ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row multisets equal SQLite; DISTINCT and four set "
                 "operators proven; typed date compatibility and two typed refusals proven; "
                 "INTERSECT precedence proven; cursors 3/3; refusals 6/6.\n";
    return true;
}

bool validate_sqlsel_aggregates(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 7> pairs{{
        {"SQLSEL-GA-GLOBAL", "SQLSEL-GA-O1"},
        {"SQLSEL-GA-GROUPED", "SQLSEL-GA-O2"},
        {"SQLSEL-GA-HAVING-COUNT", "SQLSEL-GA-O3"},
        {"SQLSEL-GA-HAVING-AVG", "SQLSEL-GA-O4"},
        {"SQLSEL-GA-WHERE", "SQLSEL-GA-O5"},
        {"SQLSEL-GA-DATE", "SQLSEL-GA-O6"},
        {"SQLSEL-GA-JOIN", "SQLSEL-GA-O7"}
    }};
    static constexpr std::array<const char*, 2> cursors{{
        "GA_C1_fact_cursor_restored:.T.",
        "GA_C2_dimension_cursor_restored:.T."
    }};
    static constexpr std::array<const char*, 5> refusals{{
        "SQLSEL: SUM(DEPT) requires a numeric column (got type 'C').",
        "SQLSEL: selected column 'SCORE' must appear in GROUP BY.",
        "SQLSEL: column 'NOSUCH' was not found in the aggregate source.",
        "SQLSEL: aggregate argument 'SALARY+1' must be a column name.",
        "SQLSEL: AVG(*) is not supported; only COUNT(*) accepts '*'."
    }};
    static constexpr std::array<const char*, 10> required{{
        "SQLSEL: COUNT(SALARY) aggregate -- 3 of 6 row(s) carried a value; 3 blank.",
        "SQLSEL: SUM(SALARY) aggregate -- 3 of 6 row(s) carried a value; 3 blank.",
        "SQLSEL: AVG(SALARY) aggregate -- 3 of 6 row(s) carried a value; 3 blank.",
        "SQLSEL: MIN(SALARY) aggregate -- 3 of 6 row(s) carried a value; 3 blank.",
        "SQLSEL: MAX(SALARY) aggregate -- 3 of 6 row(s) carried a value; 3 blank.",
        "SQLSEL: COUNT(SALARY) aggregate -- 2 of 5 row(s) carried a value; 3 blank.",
        "SQLSEL: aggregation produced 2 group row(s) from 6 source row(s).",
        "SQLSEL: aggregation produced 1 group row(s) from 6 source row(s).",
        "SQLSEL: INNER JOIN read transaction -- table fence (SQLAGG -> SQLDEPT).",
        "SQLSEL: INNER JOIN access path -- nested-loop scan (outer=7 row(s), inner=4 row(s))."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL AGGREGATE ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL AGGREGATE ORACLE",
                                        "SQLSEL-GA-REFUSALS", refusals) ||
        !require_transcript_fragments(transcript, "SQLSEL AGGREGATE ORACLE", cursors) ||
        !require_transcript_fragments(transcript, "SQLSEL AGGREGATE ORACLE", required)) {
        return false;
    }
    const std::size_t aggregate_reports = transcript_count(
        transcript, "SQLSEL: aggregation produced ");
    const std::size_t join_fences = transcript_count(
        transcript, "SQLSEL: INNER JOIN read transaction -- table fence (SQLAGG -> SQLDEPT).");
    if (aggregate_reports != pairs.size() || join_fences != 1) {
        std::cout << "SQLSEL AGGREGATE ORACLE: FAIL -- expected 7 aggregation reports and "
                     "one joined-source read fence; got "
                  << aggregate_reports << " and " << join_fences << ".\n";
        return false;
    }

    std::cout << "SQLSEL AGGREGATE ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " ordered row sets equal SQLite; GROUP BY/HAVING, aliases, and six "
                 "aggregates proven; R28 blank split reported; typed date and joined TupleRow "
                 "sources proven; cursors 2/2; refusals 5/5.\n";
    return true;
}

bool validate_sqlsel_subqueries(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 7> pairs{{
        {"SQLSEL-SQ-IN", "SQLSEL-SQ-O1"},
        {"SQLSEL-SQ-NOT-IN", "SQLSEL-SQ-O2"},
        {"SQLSEL-SQ-SCALAR", "SQLSEL-SQ-O3"},
        {"SQLSEL-SQ-EXISTS", "SQLSEL-SQ-O4"},
        {"SQLSEL-SQ-NOT-EXISTS", "SQLSEL-SQ-O5"},
        {"SQLSEL-SQ-DIVISION", "SQLSEL-SQ-O6"},
        {"SQLSEL-SQ-SCALAR-AGG", "SQLSEL-SQ-O7"}
    }};
    static constexpr std::array<const char*, 3> cursors{{
        "SQ_C1_student_cursor_restored:.T.",
        "SQ_C2_enrollment_cursor_restored:.T.",
        "SQ_C3_requirement_cursor_restored:.T."
    }};
    static constexpr std::array<const char*, 3> refusals{{
        "SQLSEL: subquery predicate failed: IN subquery compares incompatible typed columns",
        "SQLSEL: subquery predicate failed: scalar subquery must return exactly one row and one column (got 5 row(s), 1 column(s))",
        "SQLSEL: P4.7 subquery predicates currently require a single-table outer query; joined outer scopes arrive with generalized JOIN."
    }};

    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL SUBQUERY ORACLE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLSEL SUBQUERY ORACLE",
                                        "SQLSEL-SQ-REFUSALS", refusals) ||
        !require_transcript_fragments(transcript, "SQLSEL SUBQUERY ORACLE", cursors)) {
        return false;
    }
    const std::size_t cached_once = transcript_count(
        transcript, "SQLSEL: subquery evaluation count -- correlated=0, uncorrelated=1.");
    const std::size_t correlated_four = transcript_count(
        transcript, "SQLSEL: subquery evaluation count -- correlated=4, uncorrelated=0.");
    const std::size_t division_twelve = transcript_count(
        transcript, "SQLSEL: subquery evaluation count -- correlated=12, uncorrelated=0.");
    if (cached_once != 4 || correlated_four != 2 || division_twelve != 1) {
        std::cout << "SQLSEL SUBQUERY ORACLE: FAIL -- expected evaluation reports "
                     "uncorrelated-once=4, correlated-four=2, division-twelve=1; got "
                  << cached_once << '/' << correlated_four << '/' << division_twelve << ".\n";
        return false;
    }

    std::cout << "SQLSEL SUBQUERY ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " ordered row sets equal SQLite; scalar/IN/EXISTS and "
                 "relational division proven; uncorrelated cache and correlated cost counts "
                 "pinned; cursors 3/3; refusals 3/3.\n";
    return true;
}

bool validate_sqlsel_advanced_join(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 8> pairs{{
        {"SQLSEL-AJ-SELF", "SQLSEL-AJ-O1"},
        {"SQLSEL-AJ-COMPOSITE", "SQLSEL-AJ-O2"},
        {"SQLSEL-AJ-CHAIN", "SQLSEL-AJ-O3"},
        {"SQLSEL-AJ-LEFT-CHAIN", "SQLSEL-AJ-O4"},
        {"SQLSEL-AJ-EXPRESSION", "SQLSEL-AJ-O5"},
        {"SQLSEL-AJ-MULTIORDER", "SQLSEL-AJ-O6"},
        {"SQLSEL-AJ-COUNT", "SQLSEL-AJ-O7"},
        {"SQLSEL-AJ-EMPTY-RIGHT", "SQLSEL-AJ-O8"}
    }};
    static constexpr std::array<const char*, 3> cursors{{
        "AJ_C1_employee_cursor_restored:.T.",
        "AJ_C2_bonus_cursor_restored:.T.",
        "AJ_C3_category_cursor_restored:.T."
    }};
    static constexpr std::array<const char*, 5> required{{
        "SQLSEL: multi-join read transaction -- table fence (SQLADV -> SQLBON -> SQLCAT).",
        "SQLSEL: INNER JOIN stage 1 access path -- nested-loop scan",
        "SQLSEL: INNER JOIN stage 2 access path -- nested-loop scan",
        "SQLSEL: LEFT JOIN stage 1 access path -- nested-loop scan",
        "SQLSEL: LEFT JOIN stage 2 access path -- nested-loop scan"
    }};
    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL ADVANCED JOIN ORACLE", pairs) ||
        !require_transcript_fragments(transcript, "SQLSEL ADVANCED JOIN ORACLE", cursors) ||
        !require_transcript_fragments(transcript, "SQLSEL ADVANCED JOIN ORACLE", required)) {
        return false;
    }
    const std::size_t multi_fences = transcript_count(
        transcript, "SQLSEL: multi-join read transaction -- table fence");
    const std::size_t expression_reports = transcript_count(
        transcript, "SQLSEL: expression projection evaluated");
    const std::size_t multi_order_reports = transcript_count(
        transcript, "result column(s) -- materialized sort");
    if (multi_fences != 4 || expression_reports != 2 || multi_order_reports != 2) {
        std::cout << "SQLSEL ADVANCED JOIN ORACLE: FAIL -- expected multi fences 4, "
                     "TupleRow projection reports 2, multi-order reports 2; got "
                  << multi_fences << '/' << expression_reports << '/'
                  << multi_order_reports << ".\n";
        return false;
    }
    std::cout << "SQLSEL ADVANCED JOIN ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " ordered row sets equal SQLite; self/composite/chain JOIN, "
                 "typed expression projection, empty-right typed schema, multi-order, cursors 3/3, and canonical "
                 "multi-table fences proven.\n";
    return true;
}

bool validate_sqlsel_dml_transaction(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 6> pairs{{
        {"SQLSEL-DML-S1", "SQLSEL-DML-O1"},
        {"SQLSEL-DML-S2", "SQLSEL-DML-O2"},
        {"SQLSEL-DML-S3", "SQLSEL-DML-O3"},
        {"SQLSEL-DML-S4", "SQLSEL-DML-O4"},
        {"SQLSEL-DML-S5", "SQLSEL-DML-O5"},
        {"SQLSEL-DML-S6", "SQLSEL-DML-O6"}
    }};
    static constexpr std::array<const char*, 12> required{{
        "DML_C1_autocommit_cursor_restored:.T.",
        "DML_C2_final_cursor_restored:.T.",
        "DML_W1_autocommit_wal_closed:.T.",
        "DML_W2_rollback_wal_closed:.T.",
        "DML_W3_commit_wal_closed:.T.",
        "DML_L1_caller_table_lock_preserved:.T.",
        "SQLSEL: UPDATE refused -- one SQL transaction may modify one table; cross-table atomic commit is not available.",
        "SQLSEL: UPDATE refused -- ACTIVE: invalid logical for field.",
        "SQLSEL: INSERT refused -- NULL is not a stored x64base value; use an explicit typed blank.",
        "SQLSEL: UPDATE refused -- value for 'NAME' exceeds its declared width 12.",
        "SQLSEL: UPDATE column 'NOSUCH' was not found.",
        "SQLSEL: DELETE without WHERE is refused."
    }};
    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL DML ORACLE", pairs) ||
        !require_transcript_fragments(transcript, "SQLSEL DML ORACLE", required)) {
        return false;
    }
    const std::size_t begun = transcript_count(
        transcript, "SQLSEL: transaction begun; the first DML statement will take its table fence.");
    const std::size_t committed = transcript_count(transcript, "SQLSEL: transaction committed.");
    const std::size_t rolled_back = transcript_count(transcript, "SQLSEL: transaction rolled back.");
    const std::size_t autocommitted = transcript_count(
        transcript, "committed through table buffer + WAL.");
    if (begun != 3 || committed != 1 || rolled_back != 2 || autocommitted != 4) {
        std::cout << "SQLSEL DML ORACLE: FAIL -- expected transaction reports "
                     "begin=3, commit=1, rollback=2, autocommit=4; got "
                  << begun << '/' << committed << '/' << rolled_back << '/'
                  << autocommitted << ".\n";
        return false;
    }
    std::cout << "SQLSEL DML ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " committed row sets equal SQLite; typed DML, "
                 "read-your-writes, rollback/commit, WAL cleanup, cursor/lock preservation, "
                 "and fail-closed boundaries proven.\n";
    return true;
}

bool validate_sqlsel_workspace_scope(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 4> pairs{{
        {"SQLSEL-WS-S1", "SQLSEL-WS-O1"},
        {"SQLSEL-WS-S2", "SQLSEL-WS-O2"},
        {"SQLSEL-WS-S3", "SQLSEL-WS-O3"},
        {"SQLSEL-WS-S4", "SQLSEL-WS-O4"}
    }};
    static constexpr std::array<const char*, 5> required{{
        "SQLWS_C1_A_parent_cursor_restored:.T.",
        "SQLWS_C2_A_child_cursor_restored:.T.",
        "SQLWS_C3_B_child_cursor_restored:.T.",
        "SQLWS_C4_B_parent_cursor_restored:.T.",
        "SQLSEL: UPDATE affected 1 row(s); committed through table buffer + WAL."
    }};
    if (!validate_sqlsel_oracle_rows(transcript, "SQLSEL WORKSPACE ORACLE", pairs) ||
        !require_transcript_fragments(transcript, "SQLSEL WORKSPACE ORACLE", required)) {
        return false;
    }
    const std::size_t fences = transcript_count(
        transcript, "SQLSEL: INNER JOIN read transaction -- table fence");
    if (fences != 2) {
        std::cout << "SQLSEL WORKSPACE ORACLE: FAIL -- expected 2 JOIN table fences, got "
                  << fences << ".\n";
        return false;
    }
    std::cout << "SQLSEL WORKSPACE ORACLE: PASS -- " << pairs.size() << '/'
              << pairs.size() << " row sets equal SQLite; duplicate table names resolve "
                 "inside the current workspace; JOIN/DML and cursors 4/4 proven.\n";
    return true;
}

bool validate_sqlmode_smoke(const std::string& transcript)
{
    static constexpr std::array<SqlselOraclePair, 2> pairs{{
        {"SQLMODE-SELECT-ALIAS", "SQLMODE-O1"},
        {"SQLMODE-CANONICAL", "SQLMODE-O2"}
    }};
    static constexpr std::array<const char*, 4> cursors{{
        "SQLMODE_C0_native_default_select:.T.",
        "SQLMODE_C1_sql_query_cursor_restored:.T.",
        "SQLMODE_C2_other_keeps_native_select:.T.",
        "SQLMODE_C3_native_select_restored:.T."
    }};
    static constexpr std::array<const char*, 2> refusals{{
        "SQL MODE: REL and SET RELATION are unavailable; use SQLSEL JOIN or SET MODE NATIVE.",
        "SQL MODE: REL and SET RELATION are unavailable; use SQLSEL JOIN or SET MODE NATIVE."
    }};
    static constexpr std::array<const char*, 1> expression_refusal{{
        "SQL MODE: expected a SQL command; native expression fallback is disabled. Use SQLSEL or SET MODE NATIVE."
    }};
    if (!validate_sqlsel_oracle_rows(transcript, "SQLMODE SMOKE", pairs) ||
        !require_exact_transcript_block(transcript, "SQLMODE SMOKE",
                                        "SQLMODE-REFUSALS", refusals) ||
        !require_exact_transcript_block(transcript, "SQLMODE SMOKE",
                                        "SQLMODE-EXPR-REFUSAL", expression_refusal) ||
        !require_transcript_fragments(transcript, "SQLMODE SMOKE", cursors)) {
        return false;
    }
    std::cout << "SQLMODE SMOKE: PASS -- SELECT alias and canonical SQLSEL 2/2 equal "
                 "SQLite; mode transitions, relation/expression blocks 3/3, and cursors 4/4 proven.\n";
    return true;
}

std::string evaldiff_predicate_from_line(const std::string& line)
{
    static const std::string marker = " predicate=\"";
    const std::size_t begin = line.find(marker);
    if (begin == std::string::npos || line.empty() || line.back() != '"') {
        return {};
    }

    const std::size_t first = begin + marker.size();
    const std::string encoded = line.substr(first, line.size() - first - 1);
    std::string predicate;
    predicate.reserve(encoded.size());
    for (std::size_t i = 0; i < encoded.size(); ++i) {
        if (encoded[i] == '\\' && i + 1 < encoded.size() &&
            (encoded[i + 1] == '\\' || encoded[i + 1] == '"')) {
            predicate.push_back(encoded[++i]);
        } else {
            predicate.push_back(encoded[i]);
        }
    }
    return predicate;
}

bool validate_evaldiff(const std::string& transcript)
{
    struct Expected {
        const char* predicate;
        const char* counts;
        bool failure;
    };
    static constexpr std::array<Expected, 22> expected{{
        {"CVAL = \"ALPHA\"", "1/3/0", false},
        {"CVAL = \"ALPHA       \"", "1/3/0", false},
        {"NVAL = 12.5", "1/3/0", false},
        {"LVAL = .T.", "2/2/0", false},
        {"EMPTY(CVAL)", "1/3/0", false},
        {"EMPTY(NVAL)", "2/2/0", false},
        {"NVAL >= 0 AND NVAL < 13", "2/2/0", false},
        {"NOT (NVAL < 0) AND (LVAL = .T. OR EMPTY(CVAL))", "2/2/0", false},
        {"DVAL = \"20240115\"", "1/3/0", false},
        {"DTOS(DVAL) = \"20240115\"", "1/3/0", false},
        {"DVAL = CTOD(\"01/15/2024\")", "1/3/0", false},
        {"ALLTRIM(CVAL) = \"ALPHA\"", "1/3/0", false},
        {"UPPER(CVAL) = \"ALPHA\"", "1/3/0", false},
        {"SUBSTR(CVAL, 1, 2) = \"AL\"", "1/3/0", false},
        {"ALLTRIM(CVAL) = \"ZZZZZ\"", "0/4/0", false},
        {"UPPER(\"ALPHA\") = \"ALPHA\"", "4/0/0", false},
        {"DELETED()", "1/3/0", false},
        {"NOSUCH = \"X\"", "0/0/4", true},
        {"NVAL = \"NOTNUM\"", "0/0/4", true},
        {"(CVAL = \"ALPHA\"", "0/0/4", true},
        {"NVAL = 12.5 GARBAGE", "0/0/4", true},
        {"NVAL = 12.5 AND", "0/0/4", true}
    }};

    std::vector<std::string> block;
    std::string error;
    if (!transcript_block(transcript, "EVALDIFF-P4.0A-BEGIN",
                          "EVALDIFF-P4.0A-END", block, error)) {
        std::cout << "EVALDIFF ORACLE: FAIL -- " << error << "\n";
        return false;
    }

    std::vector<std::string> results;
    for (const std::string& line : block) {
        if (line.rfind("EVALDIFF VERDICT-PARITY ", 0) == 0 ||
            line.rfind("EVALDIFF PARITY-ON-FAILURE ", 0) == 0 ||
            line.rfind("EVALDIFF DIFFERENCES ", 0) == 0) {
            results.push_back(line);
        }
    }
    if (results.size() != expected.size()) {
        std::cout << "EVALDIFF ORACLE: FAIL -- expected " << expected.size()
                  << " result lines, got " << results.size() << "\n";
        return false;
    }

    std::size_t verdicts = 0;
    std::size_t failures = 0;
    for (std::size_t i = 0; i < expected.size(); ++i) {
        const Expected& want = expected[i];
        const std::string& line = results[i];
        const std::string status = want.failure
            ? "EVALDIFF PARITY-ON-FAILURE "
            : "EVALDIFF VERDICT-PARITY ";
        const std::string agreement = want.failure
            ? "verdict_agreements=0 failure_parities=4"
            : "verdict_agreements=4 failure_parities=0";
        const std::string classic = std::string("classic[T/F/E]=") + want.counts;
        const std::string tuple = std::string("tuple[T/F/E]=") + want.counts;
        const std::string actual_predicate = evaldiff_predicate_from_line(line);

        if (line.rfind(status, 0) != 0 ||
            line.find("rows=4") == std::string::npos ||
            line.find(agreement) == std::string::npos ||
            line.find("divergences=0") == std::string::npos ||
            line.find(classic) == std::string::npos ||
            line.find(tuple) == std::string::npos ||
            actual_predicate != want.predicate) {
            std::cout << "EVALDIFF ORACLE: FAIL -- case " << (i + 1)
                      << " did not match the expected result\n"
                      << "  expected predicate: " << want.predicate << "\n"
                      << "  expected counts   : " << want.counts << "\n"
                      << "  actual             : " << line << "\n";
            return false;
        }
        if (want.failure) {
            ++failures;
        } else {
            ++verdicts;
        }
    }

    static constexpr std::array<const char*, 3> required{{
        "EVALDIFF_cursor_before:.T.",
        "EVALDIFF_cursor_after:.T.",
        "EVALDIFF FOR <predicate>"
    }};
    if (!require_transcript_fragments(transcript, "EVALDIFF ORACLE", required)) {
        return false;
    }

    std::cout << "EVALDIFF ORACLE: PASS -- " << expected.size() << '/'
              << expected.size() << " exact cases; verdict parity " << verdicts
              << "; failure parity " << failures << "; cursors 2/2.\n";
    return true;
}

// AIF-156 -- PRIMARY KEY POLICY.
//
// Fifteen graded markers, derived not declared: seven guards PKP_G1..G7 and
// eight arms PKP_T1..T8, contiguous. COUNT THEM. An errored marker in this
// language PRINTS NOTHING rather than going red, so a transcript with fourteen
// is a spec that lost a claim, not a spec that passed.
//
// THE SPEC IS WRITTEN IN TWO HALVES AND THEY ARE GRADED DIFFERENTLY.
//
// PART A -- PKP_G1..G4 and PKP_T1..T3 -- is what x64base ALREADY DOES and it
// must be green: declaration, generation into a blank key under the writer's
// table lock, the reservation of a deleted row's key until PACK, the recall
// that proves the reservation mattered, and VALIDATE UNIQUE finding a duplicate
// in data that arrived dirty. If Part A reds, the policy work broke something
// that already worked.
//
// PART B -- PKP_T4..T8 -- is the ACCEPTANCE CRITERION for write-time refusal on
// the native REPLACE path, on SQLSEL INSERT and SQLSEL UPDATE, and on the
// LEGACY bare INSERT and UPDATE verbs. Asserted as five arms rather than one
// because each reaches the table buffer by its own path and a fix wired into
// one is not evidence about the other.
// MEASURED 2026-09-06 ON BUILD Sep 05 2026 21:18:51: all three RED. A native
// REPLACE wrote a duplicate over a PRIMARY key and it survived a close and
// reopen; SQLSEL INSERT committed a second duplicate through the buffer and WAL.
//
// THIS VALIDATOR IS A RATCHET AND IT FAILS IN BOTH DIRECTIONS, which is the
// whole reason a permanently-red half is admissible at all. kPkAcceptanceExpected
// records how many Part B arms were green on the build this spec was last
// reviewed against. If the count RISES, enforcement arrived and somebody must
// bump the constant DELIBERATELY -- an acknowledgement, not an accident. If it
// FALLS, enforcement regressed and the suite says so. A spec that can only fail
// one way is half a spec; a red half that can never fail is DEF_FAMILY's mistake
// repeated -- markers with no grader, permanently green by construction.
//
// RE-MEASURED 2026-09-07 ON BUILD Sep 07 2026 08:41:32 (AIF-156, first
// enforcement increment): TWO of the three arms turned green and the ratchet
// fired exactly as designed -- the suite reported FAIL on a count of 2 against
// an expected 0, and that bump was the deliberate human acknowledgement it was
// asking for. PKP_T5 and PKP_T6 went green because SQLSEL INSERT and SQLSEL
// UPDATE both reach the table buffer through evaluate_store_expression, which
// calls validate_field_constraint_for_store.
//
// RE-MEASURED AGAIN 2026-09-07 ON BUILD Sep 07 2026 09:20:18: PKP_T4 green,
// 3 of 3, ratchet fired a second time in one day. Native REPLACE now writes
// through xbase::cli::replaceFieldStored(), the field-write funnel that was
// DECLARED IN include/xbase_cli.hpp ON 2026-07-30 AND NEVER DEFINED -- flagged
// that day as "a link error waiting for its first caller", found again by the
// header reachability gate on 2026-09-06 as an unreachable header, and built
// out here. REPLACE ... WITH NULL got a sibling entry point in the same funnel,
// because a null is intercepted before the value pipeline and a gate on the
// value path alone never saw it.
//
// FIVE OF FIVE IS NOT A PRIMARY KEY THAT IS ENFORCED, AND THIS IS THE MOST
// IMPORTANT SENTENCE NEXT TO THIS CONSTANT. Part B names five arms because five
// paths were measured in September 2026. It does not name CALCWRITE, BROWSE
// editing, RECORDVIEW editing, COPY, SORT or IMPORTSQL. REPLACE_MULTI was gated
// on 2026-09-07 and IS STILL UNASSERTED HERE: multirep_buffering_regression.dts
// was retired to _to_delete/ on 2026-09-04 and nothing replaced it, so that one
// is a fix with no arm and is named as such rather than counted -- all of which reach a field write by their own
// route, none of which this spec has ever asked about, and a crude count of
// which found roughly 86 candidate direct-write call sites across 21 files -- CORRECTED 2026-09-07 TO 28 SITES IN 19 FILES, 27 after CALCWRITE was routed. The 86 was a crude grep that counted comments, counted these very registry summaries (which discuss replaceFieldStored at length inside string literals), and counted name-keyed wrapper calls like w.set(\"ID\", ...) that are not field writes. tools/staging/check_field_write_callers.py is the measurement.
// This constant measures the arms that exist. The gap between "the arms are
// green" and "the key is enforced" is closed by a STATIC gate over the callers,
// not by another marker, because no runtime marker can enumerate call sites.
//
// RAISED 3 -> 5 ON 2026-09-07 (AIF-156, second increment), AND THE ARMS CAME
// WITH THE FIX RATHER THAN AFTER IT. PKP_T7 and PKP_T8 measure the LEGACY bare
// INSERT and UPDATE verbs -- cmd_sql_insert.cpp and cmd_sql_update.cpp,
// registered at shell_commands.cpp:458-459, a SECOND door onto the same tables
// that PKP_T5 and PKP_T6 never touched because those two measure SQLSEL, which
// is different files reached by a different registration. Three of three had
// read as an enforced key for a day and was not one.
//
// PKP_G6 AND PKP_G7 ARE PART OF THAT CHANGE AND ARE THE MORE INTERESTING HALF.
// T7 and T8 both read "refused" from a write NOT HAPPENING, and a verb that did
// nothing at all -- unregistered, unparsed, or a WHERE that matched no row --
// produces exactly the same reading. G6 proves the INSERT verb appends; G7
// proves the UPDATE verb's WHERE reaches record 3. Both write a NON-KEY field,
// so neither is a second measurement of the policy. This is PKP_G5's lesson
// arriving for the sixth recorded time in this tree, and the first time it was
// designed in rather than discovered afterwards.
//
// T7 ALSO ASKS WHETHER THE REFUSAL LEFT A BLANK ROW BEHIND, not merely whether
// the duplicate landed. The legacy INSERT appends first and writes second, so a
// gate placed before the field write rather than before appendBlank() would
// refuse the duplicate and still grow the table by one. That is why the arm
// reads LNAME = "EPS" (the row G6 left) instead of LNAME <> "DUP7": the weaker
// spelling calls a blank-row refusal a pass.
constexpr int kPkAcceptanceExpected = 5;

// ---------------------------------------------------------------------------
// PKDURABLE -- THE ONLY VALIDATOR IN THIS FILE THAT READS A FILE.
//
// Every other one grades a transcript, because every other spec's evidence is
// produced by the process doing the grading. This one cannot: the measurement
// happens in TWO CHILD PROCESSES launched by `!`, which is std::system(), so
// their stdout never passes through the stream the routed capture swaps. The
// children write their markers through SET ALTERNATE and this reads those
// captures off disk.
//
// A VALIDATOR CAN OPEN A FILE AND A MARKER CANNOT, and that asymmetry is the
// only reason a cross-process claim is assertable here at all.
//
// MISSING IS NOT RED AND BOTH ARE REPORTED SEPARATELY. An errored marker in
// this language PRINTS NOTHING rather than going red, so seven of eight green
// is a lost claim wearing a clean face -- the house COUNT THE MARKERS rule,
// applied to a file instead of a transcript.
//
// A GUARD FAILURE IS "UNPROVEN", NOT "FAIL". PKD_W3 proves the refusal fires
// in the DECLARING process; if it reds, enforcement is broken on this build
// entirely and run 2 says nothing about durability. Those are different
// findings with different fixes and must not be collapsed.
bool validate_pk_durability(const std::string& transcript)
{
    // The spec's own two markers. They claim only that the shell-out was
    // reached and returned; without them, absent captures cannot be told apart
    // from children that ran and wrote nothing.
    if (transcript.find("PKDUR_G0_reached_the_shellout:.T.") == std::string::npos) {
        std::cout << "PK DURABILITY: FAIL -- the spec did not reach the shell-out line.\n";
        return false;
    }
    if (transcript.find("PKDUR_G1_shellout_returned:.T.") == std::string::npos) {
        std::cout << "PK DURABILITY: FAIL -- the shell-out did not return. PowerShell, the "
                     "execution policy or the built runtime is the suspect, NOT the primary "
                     "key -- no durability claim is made either way.\n";
        return false;
    }

    // THE PRE-CLEAR MUST HAVE RUN *THIS TIME*, AND THIS CHECK EXISTS BECAUSE
    // ITS ABSENCE PRODUCED A FALSE GREEN AND ITS FIRST REPLACEMENT PRODUCED A
    // PERMANENT RED. See the note on clear_pk_durability_child_captures() for
    // both measurements.
    //
    // What makes this line usable where the launcher's own completion line was
    // not: it is printed by the PARENT process -- the one whose stdout the
    // routed capture swaps -- so it reaches this transcript. A child's stdout
    // never can.
    //
    // Its presence means both captures were confirmed ABSENT immediately before
    // the shell-out, so any capture read below was written by THIS run. Its
    // absence means either a stale capture could not be deleted, or this
    // validator was reached without the runner's pre-clear step; in both cases
    // the files on disk are unattributable and must not be graded.
    if (transcript.find("PKDURABLE pre-clear -- both child captures removed") ==
        std::string::npos) {
        std::cout << "PK DURABILITY: FAIL -- the pre-clear sentinel is absent, so the "
                     "captures on disk cannot be attributed to THIS run. Grading them "
                     "would risk reporting a measurement that did not happen.\n"
                     "  Either a stale capture could not be deleted -- a message above "
                     "names the file -- or this validator was reached without the "
                     "runner's pre-clear step.\n";
        return false;
    }

    // THE TMP SLOT, NOT A RELATIVE PATH. The first cut wrote "data/tmp/..."
    // and the children's captures were never found: the shell's working
    // directory IS the runtime data root, so that resolved to data/data/tmp.
    // The bug printed the SAME message a genuinely unrun measurement prints,
    // which is why it took a run to see -- and it is the reason the routed
    // capture a few lines up asks the slot rather than assuming a cwd. One
    // authority for where TMP is; this now shares it.
    const std::filesystem::path tmp_dir =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP);
    const std::filesystem::path run1_path = tmp_dir / "pkdur_run1.alt";
    const std::filesystem::path run2_path = tmp_dir / "pkdur_run2.alt";

    // AN EXPECTED VALUE, NOT "GREEN", AND THE DIFFERENCE IS LOAD-BEARING.
    // Two arms are SUPPOSED to print .F., so a validator that equates green
    // with correct would have to be lied to about them -- or, worse, would go
    // green on the day they flip.
    //   PKD_T3B is the complementary half of PKD_T3: both read EMPNO, one asks
    //   "= 3" and the other "= 0", and at most one can be right. It exists so
    //   the arm cannot be made unfalsifiable by writing down only the outcome
    //   its author expected. MEASURED 2026-09-08: a BLANK numeric field is not
    //   zero, so T3B reads .F. whether or not the key was minted.
    //   PKD_T4 tries to overwrite a minted primary key by hand. The refusal IS
    //   the policy -- a key is minted at creation and never edited -- so .F. is
    //   correct here and a green T4 would mean enforcement had been lost.
    //
    // PKD_G5 IS A CONTROL AND IT IS GRADED AS A GUARD. Nothing declares SID,
    // and generate/plan_sid_if_needed mints any field with that spelling. It
    // rides in the SAME ROW as PKD_T3, written by the SAME APPEND, so if it
    // contradicts, generation did not run at all in that process and T3 says
    // nothing. An earlier cut of this measurement had no such control, read
    // green, and proved only that the fixture's key field was named SID.
    struct Expect { int run; const char* name; bool guard; bool expect_true; };
    static constexpr std::array<Expect, 15> kExpect{{
        {1, "PKD_W1_first_key_is_1",                           true,  true},
        {1, "PKD_W5_undeclared_SID_minted_by_name",            true,  true},
        {1, "PKD_W2_second_key_is_2",                          true,  true},
        {1, "PKD_W3_refused_in_declaring_process",             true,  true},
        {1, "PKD_W4_row1_is_ALPHA",                            true,  true},
        {2, "PKD_G1_fixture_reopened",                         true,  true},
        {2, "PKD_G2_key_survived_as_1",                        true,  true},
        {2, "PKD_T1_primary_survived_restart",                 false, true},
        {2, "PKD_T2_still_1_after_reopen",                     false, true},
        {2, "PKD_G3_undeclared_append_parked_on_a_blank_row",  true,  true},
        {2, "PKD_G5_undeclared_SID_minted_by_name",            true,  true},
        {2, "PKD_T3_stamped_key_minted_without_a_declaration", false, true},
        {2, "PKD_T3B_stamped_key_left_at_zero",                false, false},
        {2, "PKD_T4_the_key_could_be_filled_by_hand",          false, false},
        {2, "PKD_G4_the_new_row_accepts_a_non_key_write",      true,  true}
    }};

    // A LOCAL READER, not slurp_capture_file. That helper is defined some three
    // hundred lines BELOW this function and C++ will not look forward for it --
    // the same declared-after-use error this session already made once, in
    // cmd_workspace.cpp. Kept local rather than hoisting the shared one,
    // because moving a function to satisfy a caller reorders a file for a
    // reason a later reader cannot see.
    const auto slurp = [](const std::filesystem::path& path) -> std::string {
        std::ifstream in(path, std::ios::binary);
        if (!in) return {};
        std::ostringstream ss;
        ss << in.rdbuf();
        return ss.str();
    };

    const std::string run1 = slurp(run1_path);
    const std::string run2 = slurp(run2_path);
    if (run1.empty() || run2.empty()) {
        std::cout << "  looked for: " << run1_path.string() << "\n"
                  << "  looked for: " << run2_path.string() << "\n";
        std::cout << "PK DURABILITY: FAIL -- a child capture is missing. The pre-clear "
                     "ran, so this is not a stale-evidence problem: the shell-out returned "
                     "but wrote no evidence. Treat it as an unrun measurement, not as a "
                     "passing one.\n"
                     "  MOST LIKELY: the host-command policy refused the shell-out. Look "
                     "for a BANG refusal above. `!` RETURNS NORMALLY AFTER A REFUSAL, so "
                     "PKDUR_G0 and PKDUR_G1 are both honestly green on a run where nothing "
                     "was launched -- absent captures are the only signal.\n"
                     "  DOTTALK_ALLOW_HOST_COMMANDS=1 must be set in the ENVIRONMENT before "
                     "the process starts. The identity grant alone is not enough, and the "
                     "env var does not travel with the repo.\n";
        return false;
    }

    int agreed = 0;
    int contradicted = 0;
    int missing = 0;
    bool guard_failed = false;

    for (const Expect& e : kExpect) {
        const std::string& text = (e.run == 1) ? run1 : run2;
        const std::string t = std::string(e.name) + ":.T.";
        const std::string f = std::string(e.name) + ":.F.";

        bool actual = false;
        if (text.find(t) != std::string::npos) {
            actual = true;
        } else if (text.find(f) != std::string::npos) {
            actual = false;
        } else {
            ++missing;
            std::cout << "  MISSING (printed nothing, which is not a pass): "
                      << e.name << "\n";
            continue;
        }

        if (actual == e.expect_true) {
            ++agreed;
        } else {
            ++contradicted;
            if (e.guard) guard_failed = true;
            std::cout << "  CONTRADICTED: " << e.name << " printed ."
                      << (actual ? 'T' : 'F') << ". and this spec expects ."
                      << (e.expect_true ? 'T' : 'F') << ".\n";
        }
    }

    if (missing > 0) {
        std::cout << "PK DURABILITY: FAIL -- " << missing
                  << " marker(s) did not print. An errored marker prints nothing rather "
                     "than going red; that is a lost claim, not a pass.\n";
        return false;
    }

    if (guard_failed) {
        std::cout << "PK DURABILITY: UNPROVEN -- a guard failed, so the arms say nothing "
                     "about durability. A contradicted PKD_W3 means enforcement is broken "
                     "on this build ENTIRELY, which is a different finding from a lost "
                     "declaration; a contradicted PKD_G5 means the undeclared SID "
                     "generator did not fire, so PKD_T3 is measuring the wrong thing.\n";
        return false;
    }

    if (contradicted > 0) {
        std::cout << "PK DURABILITY: FAIL -- an arm printed the opposite of what this spec "
                     "expects. Read the CONTRADICTED line above rather than assuming which "
                     "half broke:\n"
                     "  PKD_T1/T2 contradicted -- the declaration did NOT survive the "
                     "restart. A fresh process reopened the table, did not redeclare, and a "
                     "REPLACE overwrote the primary key (AIF-156).\n"
                     "  PKD_T3 contradicted -- a fresh process ENFORCES a key it will not "
                     "MINT. The appended row takes a blank primary key that the write funnel "
                     "then refuses to let anyone fill. That is generation reading the "
                     "process map while enforcement reads the stamped header.\n"
                     "  PKD_T4 contradicted -- a minted primary key was OVERWRITTEN by hand. "
                     "The refusal is the policy, so a green T4 is lost enforcement.\n";
        return false;
    }

    std::cout << "PK DURABILITY: PASS -- " << agreed
              << " of " << kExpect.size()
              << " markers agree with this spec across TWO PROCESSES (13 green and 2 "
                 "deliberately red). The designation was written by one process and both "
                 "HONOURED and ACTED ON by another -- refused on a write it must refuse, "
                 "and minted on an APPEND that declared nothing -- which is the one thing "
                 "a .dts cannot assert on its own.\n";
    return true;
}

bool validate_pk_policy(const std::string& transcript)
{
    static constexpr std::array<const char*, 10> partA{{
        "PKP_G1_declared_and_generated:.T.",
        "PKP_G2_second_key_is_2:.T.",
        "PKP_G3_third_key_is_3:.T.",
        "PKP_G4_parked_on_GAMMA:.T.",
        "PKP_T1_deleted_key_not_reused:.T.",
        "PKP_T2_recalled_row_keeps_its_key:.T.",
        "PKP_T3_dirty_duplicate_is_present:.T.",
        "PKP_G5_partB_fixture_is_open:.T.",
        // AIF-156 2026-09-07: the two verb guards. They are Part A because they
        // assert what the LEGACY INSERT and UPDATE verbs already do -- append a
        // row, reach a row through a WHERE -- and neither writes a key, so
        // neither is a second measurement of the policy. They exist because
        // T7 and T8 read "refused" from a write NOT HAPPENING, and a verb that
        // did nothing at all produces the same reading. That is PKP_G5's
        // lesson arriving for the sixth recorded time in this tree.
        "PKP_G6_legacy_insert_verb_appends:.T.",
        "PKP_G7_legacy_update_verb_reaches_the_row:.T."
    }};
    static constexpr std::array<const char*, 5> partBNames{{
        "PKP_T4_native_replace_refused:",
        "PKP_T5_sqlsel_insert_refused:",
        "PKP_T6_sqlsel_update_refused:",
        "PKP_T7_legacy_insert_refused:",
        "PKP_T8_legacy_update_refused:"
    }};

    bool ok = true;

    for (const char* marker : partA) {
        if (transcript.find(marker) == std::string::npos) {
            std::cout << "PK POLICY: FAIL -- Part A marker missing or red: "
                      << marker << "\n";
            ok = false;
        }
    }

    // PKP_G5 IS A HARD GATE ON THE ACCEPTANCE COUNT, not just another guard.
    // The first run of this spec had no G5: Part A had closed PKPOL, `SELECT 1`
    // selected an area with no file, and T4/T5/T6 printed .F. because NOTHING
    // RAN. That is the value this spec expects today, so it passed -- the right
    // answer for the wrong reason, and a ratchet that could never fire. If the
    // Part B fixture is not open, the count is not evidence of anything.
    if (transcript.find("PKP_G5_partB_fixture_is_open:.T.") == std::string::npos) {
        std::cout << "PK POLICY: FAIL -- the Part B fixture was not open, so the "
                     "acceptance arms did not run. Their verdicts are UNPROVEN, not "
                     "red. A CLOSE followed by a SELECT is not an open.\n";
        return false;
    }

    int green = 0;
    for (const char* name : partBNames) {
        const std::string t = std::string(name) + ".T.";
        const std::string f = std::string(name) + ".F.";
        const bool sawT = transcript.find(t) != std::string::npos;
        const bool sawF = transcript.find(f) != std::string::npos;
        if (!sawT && !sawF) {
            std::cout << "PK POLICY: FAIL -- acceptance marker did not print at all: "
                      << name << " (an errored arm prints nothing; it did not pass)\n";
            ok = false;
            continue;
        }
        if (sawT) ++green;
    }

    if (green != kPkAcceptanceExpected) {
        std::cout << "PK POLICY: FAIL -- acceptance count changed: "
                  << green << " of 5 Part B arms green, expected "
                  << kPkAcceptanceExpected << ".\n";
        if (green > kPkAcceptanceExpected) {
            std::cout << "  Write-time enforcement APPEARS TO HAVE ARRIVED. That is the "
                         "good direction, and it is still a failure until a human bumps "
                         "kPkAcceptanceExpected to " << green
                      << " and says so in the commit. See AIF-156.\n";
        } else {
            std::cout << "  Write-time enforcement REGRESSED. A duplicate primary key can "
                         "now be written on a path that previously refused it.\n";
        }
        ok = false;
    }

    if (!ok) return false;

    // THREE STATES, NOT TWO. This line was binary until 2026-09-07 and it read
    // "write-time enforcement is NOT built yet" on a run whose own transcript,
    // four lines above, showed two refusals firing with a named reason. The
    // constant, the comment block and the registry summary had all been
    // updated; this string had not, and it is the one line a person actually
    // reads. A partial state needs its own sentence or it gets reported as the
    // state it left.
    const char* posture =
        (green == 5)
            ? "the five write paths THIS SPEC ASKS ABOUT refuse a write to a "
              "declared PRIMARY key -- native REPLACE, SQLSEL INSERT, SQLSEL "
              "UPDATE, and the LEGACY bare INSERT and UPDATE verbs, which are "
              "a different pair of files reached by a different registration "
              "and about which three-of-three said nothing whatever. It still "
              "does not ask about CALCWRITE, BROWSE or RECORDVIEW editing, "
              "COPY, SORT or IMPORTSQL, each of which reaches a field write by "
              "its own route; REPLACE_MULTI is gated as of 2026-09-07 and is "
              "UNASSERTED HERE because the multirep spec was retired on "
              "2026-09-04 and nothing replaced it. Five of five is the arms "
              "that exist, NOT a key that is enforced; the static gate over "
              "the callers is what closes that gap."
        : (green == 0)
            ? "write-time enforcement is NOT built; this spec is the acceptance "
              "criterion for it, not a claim that it works."
            : "write-time enforcement is PARTIAL. The arms above name which "
              "paths refuse and which still write. Do not read this PASS as a "
              "working primary key -- it means the count matches what a human "
              "last acknowledged, no more.";

    std::cout << "PK POLICY: PASS -- Part A green (10 markers), acceptance "
              << green << " of 5 as expected. AIF-156: " << posture << "\n";
    return true;
}

// VARCHARRESET (2026-09-08). A ratchet over a defect that shipped SILENTLY and
// was found by a SECOND-ORDER symptom rather than by any arm: REGRESSION ALL
// followed by an explicit REGRESSION PKPOLICY went red on four markers while
// PKPOLICY alone read 15 of 15. Nothing in the corpus asserted that closing a
// varchar table leaves its area clean, so nothing could see it.
//
// EVERY MARKER MUST BE GREEN, which is unusual in this file. PKPOLICY grades two
// halves differently because its Part B is an acceptance criterion still being
// built; there is no half of THIS that is allowed to be red. The engine either
// clears _null_layout in lockstep with _fields or it does not.
//
// THE GUARDS ARE CHECKED FIRST AND A FAILED GUARD RETURNS UNPROVEN, NOT FAIL.
// An arm reads "the write landed" from a field value, and a case that never
// executed reads IDENTICALLY to a case that executed and lost the write. That is
// PKP_G5's lesson, and it is designed in here rather than discovered later.
//
// EACH ARM CARRIES WHAT ITS RED MEANS, because the four cases differ by one
// property each and a future red should say WHICH property came back.
bool validate_varchar_area_reset(const std::string& transcript)
{
    static constexpr std::array<const char*, 9> guards{{
        "VAR_G0_control_key_minted:.T.",
        "VAR_GA_intervening_live:.T.",
        "VAR_GA_arm_key_minted:.T.",
        "VAR_GB_intervening_live:.T.",
        "VAR_GB_arm_key_minted:.T.",
        "VAR_GC_intervening_live:.T.",
        "VAR_GC_arm_key_minted:.T.",
        "VAR_GD_intervening_live:.T.",
        "VAR_GD_arm_key_minted:.T."
    }};

    struct Arm { const char* marker; const char* means; };
    static constexpr std::array<Arm, 6> arms{{
        {"VAR_T0_control_write_landed:.T.",
         "the CONTROL is red, so this fixture is broken BEFORE any VFP table "
         "exists and no other marker here means anything. Read the spec, not "
         "the engine."},
        {"VAR_TA_shape_change_alone:.T.",
         "a MERE SHAPE CHANGE in a reused area loses a write. That is LARGER "
         "than the 2026-09-08 defect, which needed a varchar, and has nothing "
         "to do with VFP or with nulls."},
        {"VAR_TB_vfp_alone:.T.",
         "opening a VFP table poisons its area with NO varchar and NO null. "
         "Also wider than the original defect."},
        {"VAR_TC_varchar_alone:.T.",
         "THE 2026-09-08 DEFECT IS BACK. A closed VFP varchar table left its "
         "bit layout in the area, isVarlengthField_() answered from it, and "
         "storeFieldsToBuffer() wrote a length byte into the last byte of a "
         "plain C() field. Check that clearFields() AND DbArea::close() still "
         "reset _null_layout -- there are two teardown lists and the original "
         "bug was both of them skipping the same member."},
        {"VAR_TD_caught_shape:.T.",
         "the caught shape is broken again. If VAR_TC is GREEN and this is RED "
         "the difference is the NULL COLUMN DECLARATION and its hidden "
         "_NullFlags column, which is a NARROWER defect than the original."},
        {"VAR_TD_survived_reopen:.T.",
         "the write was correct in memory and WRONG ON DISK. That is the "
         "durable half of the corruption, and the reason this arm closes and "
         "reopens rather than trusting the buffer."}
    }};

    bool guards_ok = true;
    for (const char* g : guards) {
        if (transcript.find(g) == std::string::npos) {
            std::cout << "VARCHAR AREA RESET: guard missing or red: " << g << "\n";
            guards_ok = false;
        }
    }
    if (!guards_ok) {
        std::cout << "VARCHAR AREA RESET: UNPROVEN -- a guard failed, so the arms say "
                     "NOTHING about the defect. A red intervening_live means the "
                     "contaminating table never existed; a red arm_key_minted means the "
                     "arm's APPEND never ran. Either way the arms beside it are measuring "
                     "a case that did not happen, which is not the same as a case that "
                     "lost its write.\n";
        return false;
    }

    bool ok = true;
    for (const Arm& a : arms) {
        if (transcript.find(a.marker) == std::string::npos) {
            std::cout << "VARCHAR AREA RESET: FAIL -- " << a.marker << "\n    " 
                      << a.means << "\n";
            ok = false;
        }
    }
    if (!ok) return false;

    std::cout << "VARCHAR AREA RESET: PASS -- 15 of 15. Closing a VFP table with a "
                 "VARCHAR field leaves its area clean, measured in FOUR areas that differ "
                 "by ONE property each (shape, VFP-ness, the varchar, the null "
                 "declaration), plus a close-and-reopen proving the bytes on disk. THIS "
                 "IS NOT A CLAIM THAT _extras AND _null_flags ARE CLEARED ON CLOSE -- as "
                 "of 2026-09-08 they are NOT, and no marker here can see them.\n";
    return true;
}

bool validate_regression_transcript(const RegressionSpec& spec,
                                    const std::string& transcript)
{
    switch (spec.validator) {
        case RegressionValidator::None:
            return true;
        case RegressionValidator::SqlselSelectOracleV1:
            return validate_sqlsel_select_oracle(transcript);
        case RegressionValidator::SqlselJoinOracleV1:
            return validate_sqlsel_join_oracle(transcript);
        case RegressionValidator::SqlselJoinEdgesV1:
            return validate_sqlsel_join_edges(transcript);
        case RegressionValidator::SqlselLeftJoinOracleV1:
            return validate_sqlsel_left_join(transcript);
        case RegressionValidator::SqlselJoinFamilyV1:
            return validate_sqlsel_join_family(transcript);
        case RegressionValidator::SqlselSetOperationsV1:
            return validate_sqlsel_set_operations(transcript);
        case RegressionValidator::SqlselAggregatesV1:
            return validate_sqlsel_aggregates(transcript);
        case RegressionValidator::SqlselSubqueriesV1:
            return validate_sqlsel_subqueries(transcript);
        case RegressionValidator::SqlselAdvancedJoinV1:
            return validate_sqlsel_advanced_join(transcript);
        case RegressionValidator::SqlselDmlTransactionV1:
            return validate_sqlsel_dml_transaction(transcript);
        case RegressionValidator::SqlselWorkspaceScopeV1:
            return validate_sqlsel_workspace_scope(transcript);
        case RegressionValidator::SqlmodeSmokeV1:
            return validate_sqlmode_smoke(transcript);
        case RegressionValidator::SqlselBufferVisibilityV1:
            return validate_sqlsel_buffer_visibility(transcript);
        case RegressionValidator::EvaldiffV1:
            return validate_evaldiff(transcript);
        case RegressionValidator::CountListVerboseV1:
            return validate_count_list_verbose(transcript);
        case RegressionValidator::PkPolicyV1:
            return validate_pk_policy(transcript);
        case RegressionValidator::PkDurabilityV1:
            return validate_pk_durability(transcript);
        case RegressionValidator::DefFamilyV1:
            return validate_def_family(transcript);
        case RegressionValidator::VarcharAreaResetV1:
            return validate_varchar_area_reset(transcript);
    }
    return false;
}

// Echo a routed-channel capture into std::cout. Not decoration: these lines are
// INVISIBLE to std::cout, to a PowerShell transcript, and to every existing
// validator in this file, because cli::cmdout writes to the console through
// OutputRouter's own stream. Folding them into cout is what lets ONE proof file
// hold both channels -- and it is ONE function because two arms now do it, and
// a second copy would be a second declaration of what a folded proof looks like.
void fold_routed_into_cout(const std::string& routed)
{
    std::cout << "  ---- routed-channel capture (" << routed.size()
              << " bytes; std::cout cannot see these) ----\n";
    std::istringstream rin(routed);
    std::string rline;
    while (std::getline(rin, rline)) {
        while (!rline.empty() && (rline.back() == '\r')) rline.pop_back();
        std::cout << "  | " << rline << "\n";
    }
    std::cout << "  ---- end routed capture ----\n";
}

// CATALOG MESSAGES DO NOT GO THROUGH std::cout, and the AIF-087 veto arm is
// where that was found. cli::cmdout writes to cli::OutputRouter::out(), which
// returns `impl_->routed_stream`, whose sink pointer is captured ONCE at router
// construction (output_router.cpp:372) and is the real console buffer forever
// after. Swapping std::cout's rdbuf, which is how every other validator here
// captures a transcript, CANNOT SEE IT. That is not a bug in the router; it is
// why SET ALTERNATE exists as the sanctioned capture (AIF-081).
//
// SECOND INSTANCE, 2026-09-04, and the reason this is no longer the veto arm's
// private workaround: COUNT_LIST_VERBOSE asserts on COUNT's own output, which is
// entirely on that channel (cmd_count.cpp:159-161 -- the count, the row lines
// and the scanned/matched summary all go through one local print_line whose sink
// is OutputRouter::out()). It failed with "CLV-T0 expected 1 line(s), got 0"
// while the operator watched the line print. The FORMULA fences were found and
// the body was not, because the fences are on std::cout and the body is not.
// That is the instrument reporting accurately on a channel it cannot see.
//
// THE ALTERNATE FILE IS A SUPERSET, NOT A SECOND PARTIAL CAPTURE, and the reason
// is worth stating because it is not obvious: shell.cpp:574 wraps every shell
// command in push_cout_redirect(), so during a command std::cout ALSO flows
// through the router's MultiBuf, and MultiBuf writes to alt_file regardless of
// destination. Both channels, one stream, correct interleaving. That holds
// BECAUSE the spec runs under the shell guard -- run outside it and the FORMULA
// markers never reach the file, which fails as "missing marker". Loud, and right.
//
// NOT THE GENERAL FIX. The general fix is to capture at the SINK -- a scoped
// swap of the router's console_buf -- which would let every validator in this
// file see the channel. It is one pointer swap and a full-suite soak, because
// every existing transcript would suddenly contain the catalog channel too, and
// every exact-block and transcript_count assertion here would have to be
// re-measured against it. That is a lane with a number, not a patch.
//
// The capture OWNS the path rather than agreeing on a filename with the script:
// one fact, one declaration.
class AlternateCapture {
public:
    AlternateCapture(std::filesystem::path path, std::string label)
        : path_(std::move(path)), label_(std::move(label))
    {
        auto& router = cli::OutputRouter::instance();

        // REFUSE RATHER THAN CLOBBER. If the operator already has SET ALTERNATE
        // running -- capturing this very run -- taking the channel would end
        // their capture, and set_alternate_to TRUNCATES (AIF-081), so it cannot
        // be handed back afterwards without destroying what they collected.
        // There is no safe save/restore here, so the caller declines and says why.
        existing_ = router.alternate_to_path();
        if (!existing_.empty()) {
            std::cout << label_ << ": NOT RUN -- SET ALTERNATE is already active on\n"
                      << "  " << existing_ << "\n"
                         "  This run needs that channel to read output std::cout cannot\n"
                         "  see, and taking it would TRUNCATE your capture. Close it\n"
                         "  (SET ALTERNATE TO) and re-run.\n"
                         "  START-TRANSCRIPT IS NOT AN ALTERNATIVE, measured 2026-09-04:\n"
                         "  it captured its own headers and NOTHING from the engine,\n"
                         "  because the engine writes to the console directly. The\n"
                         "  capture has to be inside the process.\n"
                         "  THIS IS NOT A PASS AND NOT A FAILURE: the claim is UNMEASURED.\n";
            return;
        }

        ok_ = router.set_alternate_to(path_.string());
        if (ok_) router.set_alternate(true);
    }
    ~AlternateCapture()
    {
        if (!ok_) return;              // never took the channel; leave it alone
        auto& router = cli::OutputRouter::instance();
        router.set_alternate(false);
        router.close_alternate_to();   // closes and flushes; read the file after
    }
    bool ok() const noexcept { return ok_; }
    const std::filesystem::path& path() const noexcept { return path_; }

    AlternateCapture(const AlternateCapture&)            = delete;
    AlternateCapture& operator=(const AlternateCapture&) = delete;

private:
    std::filesystem::path path_;
    std::string           label_;
    std::string           existing_;
    bool                  ok_ = false;
};

std::string slurp_capture_file(const std::filesystem::path& path)
{
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

// PKDURABLE'S STALE-EVIDENCE GUARD, AND IT LIVES HERE BECAUSE HERE IS WHERE THE
// RUN CANNOT SKIP IT.
//
// This spec's evidence is two .alt files written by CHILD PROCESSES. Nothing a
// validator can read tells this run's file from last run's, so something must
// delete them first. TWO EARLIER PLACEMENTS WERE WRONG, both measured:
//
//   1. THE CHILD LAUNCHER deleted them -- correct, and useless. The launcher is
//      DOWNSTREAM of the host-command policy that refuses to start it. MEASURED
//      2026-09-07: a session started without DOTTALK_ALLOW_HOST_COMMANDS=1
//      printed "BANG: refused for member.ai.regression", the children never
//      ran, and the validator graded the PREVIOUS run's captures and reported
//      "PASS -- 8 of 8 markers green across TWO PROCESSES".
//
//   2. A TRANSCRIPT CHECK for the launcher's own completion line. Structurally
//      unsatisfiable: `!` is std::system(), so a child's stdout goes to the
//      console handle and never passes through the C++ stream the routed
//      capture swaps. MEASURED 2026-09-07: a run in which the children
//      demonstrably executed -- their lines were on the operator's screen --
//      produced a routed capture holding only the parent's output, and the spec
//      went red on a passing measurement. pk_durability_child.ps1's own header
//      states this; the check was written past it.
//
// So the PARENT deletes and the PARENT prints. A transcript check can only rely
// on a line written by the process being captured. The sentinel is emitted ONLY
// when both files are confirmed GONE afterwards -- a delete that failed must
// never read like a delete that worked.
//
// This is the transferable shape, not a detail of this spec: A GUARD AGAINST
// EVIDENCE SURVIVING A RUN HAS TO SIT WHERE THE RUN CANNOT SKIP IT, AND IT HAS
// TO ANNOUNCE ITSELF ON A CHANNEL THE GRADER ACTUALLY READS.
bool clear_pk_durability_child_captures()
{
    const std::filesystem::path tmp_dir =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP);

    bool cleared = true;
    for (const char* name : {"pkdur_run1.alt", "pkdur_run2.alt"}) {
        const std::filesystem::path target = tmp_dir / name;
        std::error_code ec;
        std::filesystem::remove(target, ec);
        // remove() reports "it was not there" as success, and reports a locked
        // file as failure -- but the only question that matters is whether the
        // file is gone NOW. Ask the filesystem instead of reading the verdict.
        if (std::filesystem::exists(target)) {
            std::cout << "REGRESSION: PKDURABLE pre-clear could NOT remove a stale child "
                         "capture: " << target.string() << "\n";
            cleared = false;
        }
    }

    if (!cleared) {
        std::cout << "REGRESSION: PKDURABLE pre-clear FAILED. The sentinel is deliberately "
                     "NOT printed, so the validator will refuse to grade rather than read "
                     "a file it cannot date.\n";
        return false;
    }

    std::cout << "REGRESSION: PKDURABLE pre-clear -- both child captures removed BEFORE the "
                 "shell-out.\n"
                 "  Any pkdur_run*.alt found after this line was written by THIS run. If "
                 "the host-command policy refuses the shell-out, no capture appears at all "
                 "and the validator reports an unrun measurement -- which is what it should "
                 "have reported the day it graded last run's evidence instead.\n";
    return true;
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

    const auto run_script = [&]() {
        // BEFORE any bracket. Nothing here touches a path slot, and the
        // deletion has to precede everything the host-command policy is able to
        // refuse -- which is the whole point of it not living in the launcher.
        // Keyed on the validator, so the spec cannot be renamed out of its own
        // guard.
        if (spec.validator == RegressionValidator::PkDurabilityV1) {
            clear_pk_durability_child_captures();
        }

        // The bracket lives in the ONE place a spec is run, so a new caller
        // cannot acquire a spec and forget it. Scoped to the DOTSCRIPT call and
        // nothing else -- resolve_regression_script_path above reads the
        // SCRIPTS slot, which this must not disturb.
        //
        // PathSlotBracket is declared FIRST so it is destroyed LAST: DBF,
        // INDEXES and LMDB go back after CatalogBracket has already returned
        // WORKSPACES, so neither restore can observe the other mid-flight. It
        // is unconditional because any spec can move a path slot -- see the
        // note on the class.
        PathSlotBracket paths(spec.name);

        // Declared before the catalog bracket so it is destroyed after it: the
        // identity goes back last, once every path and catalog restore has run
        // under whatever identity performed them.
        std::optional<ActingIdentityBracket> identity;
        if (spec.requires_host_shell) identity.emplace(spec.name);

        if (spec.mints_catalog) {
            CatalogBracket bracket(spec.name);
            cmd_DOTSCRIPT(area, dotscript_args);
            return;
        }
        cmd_DOTSCRIPT(area, dotscript_args);
    };

    if (spec.validator == RegressionValidator::None) {
        run_script();
        return;
    }

    // Oracle validators consume exactly what the operator sees. Tee stdout to
    // the visible stream and a capture buffer at the same time; capture-then-
    // replay would reorder cout lines around commands that use another output
    // channel, changing the evidence while trying to validate it.
    std::ostringstream captured;
    std::streambuf* const original = std::cout.rdbuf();
    TeeStreamBuf tee(original, captured.rdbuf());

    // A ROUTED-CHANNEL SPEC ALSO TAKES SET ALTERNATE, AND MUST NEVER FALL BACK
    // TO THE TEE IF IT CANNOT GET IT. The fallback is precisely the failure this
    // flag exists to end: the tee sees the FORMULA fences and not the body, so
    // it reports an EMPTY BLOCK -- an instrument failure wearing the exact shape
    // of a product failure. An unmeasured claim and a refuted one must not read
    // alike, so this returns without a verdict and says so.
    std::filesystem::path alt_path;
    std::unique_ptr<AlternateCapture> alt;
    if (spec.capture_routed_channel) {
        alt_path = dottalk::paths::get_slot(dottalk::paths::Slot::TMP) /
                   (std::string("regression_") + spec.name + ".alt");
        std::error_code ec;
        std::filesystem::create_directories(alt_path.parent_path(), ec);
        alt = std::make_unique<AlternateCapture>(alt_path, std::string(spec.name));
        if (!alt->ok()) {
            std::cout << "REGRESSION " << spec.name << ": UNMEASURED -- its evidence is on\n"
                         "  the routed channel and the ALTERNATE capture was not taken.\n"
                         "  Nothing was validated. THIS IS NOT A PASS AND NOT A FAILURE.\n";
            xbase::error::set_last_error(xbase::error::e_invalid_argument());
            return;
        }
    }

    std::cout.rdbuf(&tee);
    try {
        run_script();
    } catch (...) {
        std::cout.rdbuf(original);
        throw;
    }
    std::cout.flush();
    std::cout.rdbuf(original);

    std::string transcript = captured.str();
    if (spec.capture_routed_channel) {
        alt.reset();   // closes and flushes; the file is only complete after this
        transcript = slurp_capture_file(alt_path);
        std::cout << "  Routed-channel capture: " << alt_path.string() << "\n";
        if (transcript.empty()) {
            std::cout << "REGRESSION " << spec.name << ": UNMEASURED -- the ALTERNATE\n"
                         "  capture is EMPTY. The channel was taken and nothing arrived,\n"
                         "  which is an instrument failure, not a verdict.\n";
            xbase::error::set_last_error(xbase::error::e_invalid_argument());
            return;
        }
    }
    if (!validate_regression_transcript(spec, transcript)) {
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
    } else {
        // Expected corrective-error arms inside a spec may have recorded an
        // error while proving the refusal. The regression command's final
        // status is the validator verdict, so a validated PASS ends clear.
        xbase::error::clear_last_error();
    }
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

bool run_isolation_arm(DbArea& area, const char* phase)
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
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
        return false;
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

    // The arm's own header says a missing or false marker voids the isolation
    // claim. Make that rule executable. A human read rule allowed the WSL path
    // separator defect to print D0/D1 false while REGRESSION still returned
    // success -- exactly the silent-green family this arm exists to prevent.
    std::ostringstream captured;
    std::streambuf* const original = std::cout.rdbuf();
    TeeStreamBuf tee(original, captured.rdbuf());
    std::cout.rdbuf(&tee);
    try {
        cmd_DOTSCRIPT(area, dotscript_args);
    } catch (...) {
        std::cout.rdbuf(original);
        throw;
    }
    std::cout.flush();
    std::cout.rdbuf(original);

    static constexpr std::array<const char*, 6> required{{
        "L3_L0_arm_started:.T.",
        "L3_L1_production_catalog_readable:.T.",
        "L3_D0_scratch_catalog_minted:.T.",
        "L3_D1_detector_sees_a_mint:.T.",
        "L3_G1_production_high_water_unchanged:.T.",
        "L3_G2_production_bottom_row_is_the_same_row:.T."
    }};
    if (!require_transcript_fragments(captured.str(), "L3 CATALOG ISOLATION", required)) {
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
        return false;
    }
    std::cout << "L3 CATALOG ISOLATION: PASS -- 6/6 markers true.\n";
    return true;
}

// ---------------------------------------------------------------------------
// AIF-087 M2c -- THE BEFORE-TRIGGER VETO ARM, CONTROL PASS.
//
// Driven from C++ and DELIBERATELY NOT A REGISTERED SPEC, for the same reason
// the L3 arm is not: a registered spec runs inside the suite loop and could not
// install a C++ callback around its own execution. Nothing in the language can
// register a trigger yet -- that is M5 -- so the veto pass has no other way in.
//
// WHY A CONTROL PASS EXISTS AT ALL, which is the whole design:
// "nothing was written" is ALSO what you observe when the .dts had a typo, the
// table never opened, or the WHERE matched no row. Every one of those produces
// a perfect green on a naive veto test. The L3 arm already states the rule this
// obeys -- prove the detector before crediting the result, never credit G1
// without D1 -- and this is that rule applied to a refusal.
//
// SHIPPED HERE: the control only. The veto pass is deliberately absent rather
// than stubbed, so no reader can mistake a half-built arm for a proven veto.
// ---------------------------------------------------------------------------

static const char* const kTriggerVetoSetupScript = "trigger_veto_arm_setup.dts";
static const char* const kTriggerVetoWorkScript  = "trigger_veto_arm_work.dts";
static const char* const kTriggerVetoTeardownScript = "trigger_veto_arm_teardown.dts";
static const char* const kTriggerMultirepScript     = "trigger_veto_arm_multirep.dts";
static const char* const kTriggerRecoveryPoisonScript   = "trigger_recovery_poison.dts";
static const char* const kTriggerRecoveryReopenScript   = "trigger_recovery_reopen.dts";
static const char* const kTriggerRecoveryLivenessScript = "trigger_recovery_liveness.dts";

// Run one arm script through DOTSCRIPT, teeing stdout so the operator sees it
// and the arm can read it. Same capture shape as run_isolation_arm: tee rather
// than capture-then-replay, because replay reorders cout around commands that
// use another output channel -- changing the evidence while validating it.
bool trigger_veto_run_script(DbArea& area, const char* token, std::string& captured_out)
{
    namespace fs = std::filesystem;

    const fs::path resolved = resolve_script_token(token);
    std::cout << "  Script  : " << token << "\n"
              << "  Resolved: " << resolved.string() << "\n";

    std::error_code ec;
    if (!fs::exists(resolved, ec) || ec) {
        std::cout << "  NOT RUN -- the arm script is not on disk at that path.\n"
                     "  THIS IS NOT A PASS. A missing instrument and a green one\n"
                     "  must not read alike (AIF-118).\n";
        return false;
    }

    std::ostringstream dotscript_line;
    dotscript_line << '"' << resolved.string() << '"';
    std::istringstream dotscript_args(dotscript_line.str());

    std::ostringstream captured;
    std::streambuf* const original = std::cout.rdbuf();
    TeeStreamBuf tee(original, captured.rdbuf());
    std::cout.rdbuf(&tee);
    try {
        cmd_DOTSCRIPT(area, dotscript_args);
    } catch (...) {
        std::cout.rdbuf(original);
        throw;
    }
    std::cout.flush();
    std::cout.rdbuf(original);

    captured_out = captured.str();
    return true;
}

// The arm's refusing callback. Refuses EVERY write it is offered, which is the
// unambiguous form for a proof: any commit that survives this did not consult
// the Before phase at all.
constexpr xbase::trigger_hooks::RefusalCode kVetoReasonCode = 87087;

struct VetoProbe {
    int           calls             = 0;
    std::uint64_t first_recno       = 0;
    std::size_t   first_field_count = 0;
};

// THE MUTATION, AS A PERMANENT CONTROL RATHER THAN A ONE-OFF EDIT.
// A source mutation run by hand proves the arm could fail ON THE DAY SOMEBODY
// RAN IT. This one is registered the same way and simply ALLOWS the write, so
// `REGRESSION TRIGGERVETO SELFTEST` re-proves on every run that the arm's
// detectors actually fire. A green arm and an arm that cannot go red read
// identically, and this is the difference.
bool trigger_veto_allow(xbase::DbArea& /*area*/,
                        const xbase::trigger_hooks::WriteEvent& ev,
                        xbase::trigger_hooks::RefusalCode* /*reason*/,
                        void* user) noexcept
{
    auto* p = static_cast<VetoProbe*>(user);
    if (p) {
        if (p->calls == 0) {
            p->first_recno       = ev.recno;
            p->first_field_count = ev.field_count;
        }
        p->calls += 1;
    }
    return true;   // consulted, and permits the write
}

bool trigger_veto_refuse(xbase::DbArea& /*area*/,
                         const xbase::trigger_hooks::WriteEvent& ev,
                         xbase::trigger_hooks::RefusalCode* reason,
                         void* user) noexcept
{
    auto* p = static_cast<VetoProbe*>(user);
    if (p) {
        if (p->calls == 0) {
            p->first_recno       = ev.recno;
            p->first_field_count = ev.field_count;
        }
        p->calls += 1;
    }
    if (reason) *reason = kVetoReasonCode;
    return false;
}

// AIF-087 M3 -- the AFTER probe. Notification only; it cannot refuse.
struct AfterProbe {
    int           fires             = 0;
    std::uint64_t last_recno        = 0;
    std::size_t   last_field_count  = 0;
    std::string   last_kind;
};

void trigger_after_observe(xbase::DbArea& /*area*/,
                           const xbase::trigger_hooks::WriteEvent& ev,
                           void* user) noexcept
{
    auto* p = static_cast<AfterProbe*>(user);
    if (!p) return;
    p->fires += 1;
    p->last_recno = ev.recno;
    p->last_field_count = ev.field_count;
    try { p->last_kind = ev.event_kind ? ev.event_kind : ""; } catch (...) {}
}

class AfterRegistration {
public:
    // TAKES THE FUNCTION, NOT JUST THE USER POINTER, because M4 registers a
    // DIFFERENT observer through the same registration discipline. A second
    // registration class would be a second declaration of "register on every
    // area", and the reason for registering on every area (the work script
    // picks its own area; a guessed slot yields a NO-FIRE, which reads exactly
    // like a mechanism that did not fire) would then live in two places.
    AfterRegistration(xbase::trigger_hooks::AfterWriteFn fn, void* user) noexcept
    {
        if (auto* eng = shell_engine()) {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                xbase::trigger_hooks::set_after_callback(eng->area(i), fn, user);
            }
        }
    }
    ~AfterRegistration() noexcept
    {
        if (auto* eng = shell_engine()) {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                xbase::trigger_hooks::clear_after_callback(eng->area(i));
            }
        }
    }
    AfterRegistration(const AfterRegistration&)            = delete;
    AfterRegistration& operator=(const AfterRegistration&) = delete;
};

// REGISTERS ON EVERY AREA, and that is deliberate rather than lazy. The work
// script picks its own work area, and binding the callback to a slot guessed
// here would produce a NO-FIRE if the guess were wrong. A no-fire in this arm
// reads as "the veto did not work" -- safe, since it fails red rather than
// green, but it would be a red for the wrong reason and cost a run to diagnose.
// Registration is a map insert per area and this is not a hot path.
class VetoRegistration {
public:
    VetoRegistration(xbase::trigger_hooks::BeforeWriteFn fn, VetoProbe* probe) noexcept
    {
        if (auto* eng = shell_engine()) {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                xbase::trigger_hooks::set_before_callback(eng->area(i), fn, probe);
            }
        }
    }
    ~VetoRegistration() noexcept
    {
        if (auto* eng = shell_engine()) {
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                xbase::trigger_hooks::clear_before_callback(eng->area(i));
            }
        }
    }
    VetoRegistration(const VetoRegistration&)            = delete;
    VetoRegistration& operator=(const VetoRegistration&) = delete;
};


// Read the write-ahead journal and answer the two questions that separate a
// refusal from a commit. The COMMIT-marker test is THE SAME TEST RECOVERY USES
// (table_state.cpp: first field "C"), on purpose -- a second, differently
// written test of the same condition is how the two drift.
bool trigger_veto_read_journal(const std::filesystem::path& path,
                               bool& has_redo, bool& has_commit)
{
    has_redo = false;
    has_commit = false;

    std::ifstream in(path, std::ios::binary);
    if (!in) return false;

    std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
        if (line.empty()) continue;
        if (line[0] == 'I' || line[0] == 'U' || line[0] == 'D') has_redo = true;
        if (line[0] == 'C' && (line.size() == 1 || line[1] == ' ')) has_commit = true;
    }
    return true;
}

// PASS 1 -- CONTROL. No trigger registered. Proves the work script drives a
// real buffered commit, so that a later refusal is distinguishable from a
// script that never committed anything.
bool run_trigger_veto_control(DbArea& area)
{
    std::cout << "\nREGRESSION: AIF-087 BEFORE-TRIGGER VETO ARM -- PASS 1, CONTROL\n"
                 "  Registers NO trigger.\n"
                 "  READ RULE: the veto pass may not be credited unless this is\n"
                 "  green. A red control makes a refusal UNMEASURABLE, not proven.\n";

    std::string setup_out;
    if (!trigger_veto_run_script(area, kTriggerVetoSetupScript, setup_out)) return false;
    static constexpr std::array<const char*, 2> setup_required{{
        "TRGVETO-SETUP-BEGIN", "TRGVETO-SETUP-END"
    }};
    if (!require_transcript_fragments(setup_out, "TRIGGER VETO SETUP", setup_required)) return false;

    std::string work_out;
    if (!trigger_veto_run_script(area, kTriggerVetoWorkScript, work_out)) return false;

    // W1 AND W2 TOGETHER are the control's proof, and the pair matters more than
    // either half. W1 says the record took the write. W2 says the journal is
    // GONE -- journal_note_commit deletes the log on success -- so the write went
    // through a COMPLETED transaction rather than around one.
    // W3 IS ASSERTED .F. HERE ON PURPOSE. With no transaction active the work
    // script's native COMMIT is a silent no-op and the row still reads VETOED
    // from its own successful commit. Asserting the .F. is what stops an
    // over-broad guard -- one that refused EVERY native COMMIT -- from passing
    // this arm unnoticed. See AIF-159 section 3.
    static constexpr std::array<const char*, 6> control_required{{
        "TRGVETO-WORK-END",
        "TRG_W0_fixture_row1_is_alpha:.T.",
        "TRG_W1_row1_took_the_write:.T.",
        "TRG_W2_journal_survived:.F.",
        "TRG_W3_native_commit_did_not_write:.F.",
        "TRG_W4_native_rollback_left_the_row:.F."
    }};
    if (!require_transcript_fragments(work_out, "TRIGGER VETO CONTROL", control_required)) {
        std::cout << "TRIGGER VETO CONTROL: FAIL -- no commit was observed.\n"
                     "  With the control red, a refusal and a script that never\n"
                     "  ran are THE SAME OBSERVATION.\n"
                     "  LOOK FIRST for \"staged N row(s) in the active transaction\"\n"
                     "  above. That means a SQLsel transaction was ALREADY OPEN when\n"
                     "  the arm started, so the work script never autocommitted and\n"
                     "  this red says nothing about triggers. Close it (SET MODE SQL,\n"
                     "  then COMMIT or ROLLBACK) and re-run.\n";
        return false;
    }
    std::string teardown_out;
    if (!trigger_veto_run_script(area, kTriggerVetoTeardownScript, teardown_out)) return false;
    static constexpr std::array<const char*, 2> teardown_required{{
        "TRGVETO-TEARDOWN-END",
        "TRG_T3_scope_released:.T."
    }};
    if (!require_transcript_fragments(teardown_out, "TRIGGER VETO CONTROL TEARDOWN",
                                      teardown_required)) return false;

    std::cout << "TRIGGER VETO CONTROL: PASS -- record took the write, journal deleted.\n";
    return true;
}

// PASS 2 -- VETO. Same work script, unchanged, with a refusing callback.
bool run_trigger_veto_refusal(DbArea& area, xbase::trigger_hooks::BeforeWriteFn fn)
{
    namespace fs = std::filesystem;

    std::cout << "\nREGRESSION: AIF-087 BEFORE-TRIGGER VETO ARM -- PASS 2, VETO\n"
                 "  Same work script, byte for byte. The ONLY difference is a\n"
                 "  registered BEFORE callback that refuses every write.\n";

    std::string setup_out;
    if (!trigger_veto_run_script(area, kTriggerVetoSetupScript, setup_out)) return false;
    static constexpr std::array<const char*, 2> setup_required{{
        "TRGVETO-SETUP-BEGIN", "TRGVETO-SETUP-END"
    }};
    if (!require_transcript_fragments(setup_out, "TRIGGER VETO SETUP", setup_required)) return false;

    const fs::path alt_path =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP) / "trigger_veto_arm.alt";

    VetoProbe probe;
    std::string work_out;
    std::string routed_out;
    {
        AlternateCapture alt(alt_path, "TRIGGER VETO");
        if (!alt.ok()) {
            std::cout << "TRIGGER VETO: FAIL -- could not open the ALTERNATE capture at "
                      << alt_path.string() << "\n"
                         "  The refusal message is on a channel std::cout cannot see,\n"
                         "  so without this capture it is UNMEASURED, not absent.\n";
            return false;
        }
        VetoRegistration registered(fn, &probe);
        if (!trigger_veto_run_script(area, kTriggerVetoWorkScript, work_out)) return false;
    }
    routed_out = slurp_capture_file(alt_path);

    fold_routed_into_cout(routed_out);

    bool ok = true;

    // 1. The callback was actually consulted. Without this, everything below is
    //    equally consistent with a commit that never reached the Before phase.
    if (probe.calls < 1) {
        std::cout << "TRIGGER VETO: FAIL -- the BEFORE callback was never called.\n"
                     "  Nothing below this line is evidence about a veto.\n";
        ok = false;
    } else {
        std::cout << "  Before callback consulted " << probe.calls
                  << " time(s); first event recno=" << probe.first_recno
                  << " changed-field count=" << probe.first_field_count << "\n";
    }

    // 2. The refusal was reported through the message catalog, carrying the
    //    arm's own reason code so the code round-tripped rather than being lost.
    static constexpr std::array<const char*, 1> cout_required{{
        "TRG_W0_fixture_row1_is_alpha:.T."
    }};
    if (!require_transcript_fragments(work_out, "TRIGGER VETO", cout_required)) ok = false;

    static constexpr std::array<const char*, 2> routed_required{{
        "refused by a BEFORE trigger at record 1",
        "(reason 87087)"
    }};
    if (!require_transcript_fragments(routed_out, "TRIGGER VETO (routed)", routed_required)) {
        std::cout << "  (routed capture was " << routed_out.size() << " bytes at "
                  << alt_path.string() << ")\n";
        ok = false;
    }

    // 3. The journal SURVIVED, which is the refusal's fingerprint: a completed
    //    commit deletes it.
    static constexpr std::array<const char*, 1> journal_marker{{
        "TRG_W2_journal_survived:.T."
    }};
    if (!require_transcript_fragments(work_out, "TRIGGER VETO", journal_marker)) ok = false;

    // 4. And it contains the staged redo WITHOUT a COMMIT marker -- the write
    //    was recorded as intended and never made true.
    const fs::path tbj =
        dottalk::paths::get_slot(dottalk::paths::Slot::DBF) / "TRGVETO.dbf.tbj";
    bool has_redo = false, has_commit = false;
    if (!trigger_veto_read_journal(tbj, has_redo, has_commit)) {
        std::cout << "TRIGGER VETO: FAIL -- could not read the journal at "
                  << tbj.string() << "\n";
        ok = false;
    } else {
        std::cout << "  Journal " << tbj.string() << ": redo=" << (has_redo ? "yes" : "no")
                  << " commit-marker=" << (has_commit ? "YES" : "no") << "\n";
        // has_redo IS NOT ASSERTED, and the reason is the veto working.
        // journal_note_change defers durability to journal_begin_commit's single
        // fsync (table_state.cpp), and the refusal returns BEFORE that call --
        // so the staged redo lines are still in the stdio buffer and the file on
        // disk is empty. Measured 2026-09-04: redo=no on a correct refusal.
        // Requiring redo here would demand that a refused transaction leave
        // durable evidence, which is the opposite of what a refusal is for.
        std::cout << "  (redo on disk is EXPECTED to be absent: the only fsync is\n"
                     "   the one the veto prevents.)\n";
        if (has_commit) {
            std::cout << "TRIGGER VETO: FAIL -- a COMMIT marker was written. The\n"
                         "  veto did not fire before journal_begin_commit.\n";
            ok = false;
        }
    }

    // MEASURED 2026-09-04, NOW ASSERTED. The open question was whether a native
    // read after a refused SQLsel UPDATE shows the committed value or the
    // still-buffered one. Observed: .F. -- the record still holds ALPHA, so the
    // read reports COMMITTED TRUTH and the retained buffer does not overlay it.
    // Asserted from here on, because a change to that behaviour would mean a
    // refused write had become visible to a reader.
    static constexpr std::array<const char*, 1> w1_required{{
        "TRG_W1_row1_took_the_write:.F."
    }};
    if (!require_transcript_fragments(work_out, "TRIGGER VETO", w1_required)) ok = false;

    // 4b. AIF-159 s3 -- THE NATIVE COMMIT DID NOT REACH AROUND THE SQL SCOPE.
    //
    // A refused autocommit leaves the transaction ACTIVE with the session still
    // in NATIVE mode. Before the guard, a bare COMMIT in that window committed
    // the very write the trigger had just refused and left the scope open, so
    // every later autocommit staged instead of committing -- success reported
    // at every step and nothing written. Both halves are required: the refusal
    // must be SAID, and the record must still hold ALPHA.
    //
    // This pair is what makes the guard measured rather than argued. On a
    // pre-guard binary the marker reads .F., so this arm goes red on the code
    // it was written against.
    // AIF-159 s7.6 adds the ROLLBACK twin to this same block. Note what proves
    // which: the COMMIT half is proven by TRG_W3 (the vetoed write did not
    // land), but the ROLLBACK half is proven by TRG_T1 IN THE TEARDOWN -- if
    // the native ROLLBACK had been obeyed, the buffer would be gone and the
    // retry would have nothing to commit. TRG_W4 is the control-side guard
    // against an over-broad refusal, not the discriminator for this half.
    static constexpr std::array<const char*, 4> native_guard_required{{
        "COMMIT: a SQL transaction is active; end it with COMMIT or ROLLBACK in SQL mode",
        "TRG_W3_native_commit_did_not_write:.T.",
        "ROLLBACK: a SQL transaction is active; end it with COMMIT or ROLLBACK in SQL mode",
        "TRG_W4_native_rollback_left_the_row:.T."
    }};
    if (!require_transcript_fragments(work_out, "TRIGGER VETO (native guard)",
                                      native_guard_required)) {
        std::cout << "TRIGGER VETO: FAIL -- a native COMMIT or ROLLBACK was able to\n"
                     "  act inside the still-open SQL transaction. That is the\n"
                     "  AIF-159 defect: COMMIT lands the vetoed write, ROLLBACK\n"
                     "  discards the buffer, and either way the scope stays open.\n"
                     "  If TRG_T1 is also red below, the ROLLBACK was obeyed and\n"
                     "  the buffered change no longer exists to retry.\n";
        ok = false;
    }

    // 5. THE PROPERTY THAT MAKES A REFUSAL SAFE RATHER THAN MERELY OBSTRUCTIVE.
    //    The callback is unregistered by now, so this retries the SAME buffered
    //    change and it must land. A veto that DISCARDED the user's work would
    //    satisfy every assertion above and still be the wrong behaviour.
    //    This also clears the buffer, which is what stops CLOSE ALL raising the
    //    interactive "COMMIT changes? (y/N)" prompt that would hang the arm.
    std::string teardown_out;
    if (!trigger_veto_run_script(area, kTriggerVetoTeardownScript, teardown_out)) return false;
    static constexpr std::array<const char*, 4> retry_required{{
        "TRGVETO-TEARDOWN-END",
        "TRG_T1_retry_committed:.T.",
        "TRG_T2_journal_cleared:.T.",
        "TRG_T3_scope_released:.T."
    }};
    if (!require_transcript_fragments(teardown_out, "TRIGGER VETO RETRY", retry_required)) {
        std::cout << "TRIGGER VETO: FAIL -- the refused change did not survive for\n"
                     "  retry. The veto is destructive, not correctable.\n";
        ok = false;
    }

    if (!ok) return false;
    std::cout << "TRIGGER VETO: PASS -- the write was staged, refused, reported,\n"
                 "  never marked committed, and STILL COMMITTED ON RETRY.\n";
    return true;
}

// Write the arm's own proof. EVIDENCE IS CAPTURED BY THE INSTRUMENT, not around
// it -- measured 2026-09-04: PowerShell's Start-Transcript captured 817 bytes of
// its own headers and NOTHING from the engine, because the engine writes to the
// console directly. An outside capture cannot see this run. The arm can.
void trigger_veto_write_proof(const std::string& body, bool verdict, const std::string& mode)
{
    namespace fs = std::filesystem;
    // ONE FILE PER MODE. A single path meant the SELFTEST run overwrote the
    // real run's proof and nothing said so -- the same shape AIF-081 fixed in
    // SET ALTERNATE, where one transcript held three runs and a conclusion was
    // drawn from the wrong one. Truncate is right; sharing a name is not.
    const char* stem = "trigger_veto_arm_proof.txt";
    if (mode == "SELFTEST") stem = "trigger_veto_arm_selftest_proof.txt";
    else if (mode == "MULTIREP") stem = "trigger_veto_arm_multirep_proof.txt";
    else if (mode == "AFTER") stem = "trigger_veto_arm_after_proof.txt";
    else if (mode == "RECOVERY") stem = "trigger_veto_arm_recovery_proof.txt";
    const fs::path out = dottalk::paths::get_slot(dottalk::paths::Slot::LOGS) / stem;

    std::error_code ec;
    fs::create_directories(out.parent_path(), ec);

    std::ofstream f(out, std::ios::out | std::ios::trunc | std::ios::binary);
    if (!f) {
        std::cout << "TRIGGER VETO: WARNING -- could not write the proof to "
                  << out.string() << "; this run is UNCAPTURED.\n";
        return;
    }
    const std::time_t now = std::time(nullptr);
    f << "AIF-087 M2c -- BEFORE-trigger veto arm, captured proof\n"
      << "mode     : " << mode << "\n"
      << "unix_time: " << static_cast<long long>(now) << "\n"
      << "verdict  : " << (verdict ? "PASS" : "FAIL") << "\n"
      << "note     : both output channels are folded into this file. The routed\n"
      << "           channel (catalog messages) is marked with a leading '|'.\n"
      << "----------------------------------------------------------------\n"
      << body;
    f.close();
    std::cout << "  Proof written: " << out.string() << "\n";
}

// AIF-151 x AIF-087 -- IS A BUFFERED MULTIREP VISIBLE TO A TRIGGER?
//
// The claim the whole AIF-151/AIF-087 connection rests on, and it was INFERRED
// until this ran. Before AIF-151 MULTIREP wrote through regardless of TABLE ON,
// never reached a commit, and was invisible to BOTH phases.
//
// Registers a callback that is CONSULTED and ALLOWS -- refusing would prove
// visibility too, but would prove nothing about the fields actually landing.
//
// SELF-CONTROLLED, so it needs no separate control pass: TRG_MR1 fails if
// MULTIREP did not buffer, TRG_MR2 fails if the commit did not land, and
// calls==0 fails if the hook never fired. The three cannot all pass by accident.
//
// AND IT DISCRIMINATES THE GRANULARITY. One call carrying two fields is the
// AIF-087 M2a design. A per-field hook would report TWO calls of ONE field; a
// dead hook reports zero. The assertion below can tell all three apart.
bool run_trigger_multirep_visibility(DbArea& area)
{
    std::cout << "\nREGRESSION: AIF-151 -- IS A BUFFERED MULTIREP VISIBLE TO A TRIGGER?\n"
                 "  Callback ALLOWS; the assertion is on WHAT IT WAS SHOWN.\n"
                 "  Expect ONE call carrying TWO changed fields -- and only one,\n"
                 "  across THREE MULTIREPs: a rolled-back one, a committed one, and\n"
                 "  an unbuffered direct write. Only the committed one may fire.\n";

    std::string setup_out;
    if (!trigger_veto_run_script(area, kTriggerVetoSetupScript, setup_out)) return false;
    static constexpr std::array<const char*, 2> setup_required{{
        "TRGVETO-SETUP-BEGIN", "TRGVETO-SETUP-END"
    }};
    if (!require_transcript_fragments(setup_out, "MULTIREP SETUP", setup_required)) return false;

    VetoProbe probe;
    std::string work_out;
    {
        VetoRegistration registered(&trigger_veto_allow, &probe);
        if (!trigger_veto_run_script(area, kTriggerMultirepScript, work_out)) return false;
    }

    bool ok = true;

    static constexpr std::array<const char*, 6> required{{
        "TRGMULTI-WORK-END",
        "TRG_MR0_fixture_row1_is_alpha:.T.",
        "TRG_MR1_staged_not_written:.T.",
        "TRG_MR2_rollback_discarded:.T.",
        "TRG_MR3_both_fields_landed:.T.",
        "TRG_MR4_direct_write_immediate:.T."
    }};
    if (!require_transcript_fragments(work_out, "MULTIREP VISIBILITY", required)) ok = false;

    std::cout << "  Before callback consulted " << probe.calls
              << " time(s); first event recno=" << probe.first_recno
              << " changed-field count=" << probe.first_field_count << "\n";

    if (probe.calls == 0) {
        std::cout << "MULTIREP VISIBILITY: FAIL -- the trigger was never consulted.\n"
                     "  A buffered MULTIREP is still invisible to the BEFORE phase.\n";
        ok = false;
    } else if (probe.calls != 1) {
        std::cout << "MULTIREP VISIBILITY: FAIL -- " << probe.calls
                  << " calls, expected exactly 1.\n"
                     "  Either the fire unit reverted to the field (AIF-087 M2a), or\n"
                     "  a ROLLBACK or an unbuffered direct write fired a trigger --\n"
                     "  neither reaches a commit and neither may.\n";
        ok = false;
    } else if (probe.first_field_count != 2) {
        std::cout << "MULTIREP VISIBILITY: FAIL -- the event carried "
                  << probe.first_field_count << " changed field(s), expected 2.\n"
                     "  The commit-entry fold does not match what MULTIREP staged.\n";
        ok = false;
    }

    if (!ok) return false;
    std::cout << "MULTIREP VISIBILITY: PASS -- one event, two fields, both landed.\n"
                 "  A buffered MULTIREP now arrives at commit entry as ONE decision\n"
                 "  over the whole record, which is what M2a reshaped the fire unit for.\n";
    return true;
}

// AIF-087 M3 -- DOES THE AFTER PHASE FIRE ON THE BUFFERED PATH?
//
// Reuses the MULTIREP work script deliberately, because it runs THREE MULTIREPs
// and only one of them may notify:
//
//   rolled back   -> never commits          -> MUST NOT fire
//   committed     -> apply_one_recno lands  -> fires ONCE, TWO fields
//   TABLE OFF     -> direct write           -> MUST NOT fire, because MULTIREP
//                    MIRRORS replaceFieldStored instead of calling it and never
//                    inherited the fire. That is the unfixed half of
//                    AIF-151's finding, and this arm re-measures it rather than
//                    trusting yesterday's reading.
//
// So "fires == 1 with field_count == 2" is four claims in one number, exactly
// as the BEFORE side is.
bool run_trigger_after_visibility(DbArea& area)
{
    std::cout << "\nREGRESSION: AIF-087 M3 -- DOES THE AFTER PHASE FIRE AFTER APPLY?\n"
                 "  Notification only; the callback cannot refuse.\n"
                 "  Three MULTIREPs, ONE commit. Expect ONE fire of TWO fields:\n"
                 "  a ROLLBACK must not notify, and an unbuffered direct write\n"
                 "  still does not fire at all (AIF-151's unfixed half).\n";

    std::string setup_out;
    if (!trigger_veto_run_script(area, kTriggerVetoSetupScript, setup_out)) return false;
    static constexpr std::array<const char*, 2> setup_required{{
        "TRGVETO-SETUP-BEGIN", "TRGVETO-SETUP-END"
    }};
    if (!require_transcript_fragments(setup_out, "AFTER SETUP", setup_required)) return false;

    AfterProbe probe;
    std::string work_out;
    {
        AfterRegistration registered(&trigger_after_observe, &probe);
        if (!trigger_veto_run_script(area, kTriggerMultirepScript, work_out)) return false;
    }

    bool ok = true;
    static constexpr std::array<const char*, 3> required{{
        "TRGMULTI-WORK-END",
        "TRG_MR3_both_fields_landed:.T.",
        "TRG_MR4_direct_write_immediate:.T."
    }};
    if (!require_transcript_fragments(work_out, "AFTER VISIBILITY", required)) ok = false;

    std::cout << "  After callback fired " << probe.fires
              << " time(s); last recno=" << probe.last_recno
              << " changed-field count=" << probe.last_field_count
              << " kind=" << (probe.last_kind.empty() ? "<none>" : probe.last_kind) << "\n";

    if (probe.fires == 0) {
        std::cout << "AFTER VISIBILITY: FAIL -- the AFTER phase never fired.\n"
                     "  A committed buffered write notified nobody.\n";
        ok = false;
    } else if (probe.fires != 1) {
        std::cout << "AFTER VISIBILITY: FAIL -- " << probe.fires
                  << " fires for ONE commit.\n"
                     "  Either a ROLLBACK notified, or an unbuffered direct write\n"
                     "  did, or the fire unit reverted to the field.\n";
        ok = false;
    } else if (probe.last_field_count != 2) {
        std::cout << "AFTER VISIBILITY: FAIL -- the event carried "
                  << probe.last_field_count << " field(s), expected 2.\n";
        ok = false;
    } else if (probe.last_kind != "record_update") {
        // The label must agree with the count. A two-field write reported as
        // "field_replace" contradicted its own field_count, and a consumer
        // reading kind alone would have misclassified it.
        std::cout << "AFTER VISIBILITY: FAIL -- kind was '" << probe.last_kind
                  << "', expected 'record_update' for a multi-field record write.\n";
        ok = false;
    }

    if (!ok) return false;
    std::cout << "AFTER VISIBILITY: PASS -- one notification, two fields, and only\n"
                 "  for the write that actually became true.\n";
    return true;
}

// ---------------------------------------------------------------------------
// AIF-087 M4 -- RECOVERY REPLAYS THE DATA AND DOES NOT RE-FIRE THE TRIGGER.
//
// Decision E 4.4 says replay cannot reach the AFTER fire BY CONSTRUCTION rather
// than by a suppression flag: recover_table_buffer_journal (table_state.cpp:393)
// replays with area.set + writeCurrent + deleteCurrent and never calls
// apply_one_recno, which is where M3 put the fire. A property that holds by
// construction is exactly the kind that a later tidying refactor removes without
// anyone noticing, so this arm exists to make the removal loud.
//
// THE HARD PART IS THE FIXTURE, AND M3 MAKES IT. A committed journal is not
// something a passing run leaves behind: journal_begin_commit writes the COMMIT
// marker and fsyncs, apply runs, and journal_note_commit DELETES the log
// (table_state.cpp:366-375). The file exists only between those two points --
// which is precisely the window the AFTER phase fires in. So the arm registers
// an AFTER callback whose side effect is to COPY THE LIVE JOURNAL, and gets a
// real, engine-written, marker-carrying .tbj out of an ordinary successful
// commit. The mechanism M3 built is the instrument M4 needs.
//
// WHAT THAT IS AND IS NOT. The bytes are identical to what a crash between the
// marker and apply completion would leave: the log is append-only and NOTHING
// writes to it between journal_begin_commit and journal_note_commit -- measured
// by reading table_state.cpp, whose only writers are journal_note_change during
// staging, the marker itself, and rollback's R line. So the on-disk state this
// arm restores is the crash state. What it does NOT prove is anything about the
// crash itself: fsync semantics under a real kill, torn lines, a partially
// written marker. THAT IS STILL THE CRASH TEST'S JOB AND IT IS STILL OWED.
// This is the guard, and it says so.
//
// THE READING DISCIPLINE, which is the whole design:
//
//   TRG_R0  the poison landed          -- without it, TRG_R1 reading VETOED
//                                         cannot mean replay ran; it could mean
//                                         nothing ever changed the record.
//   TRG_R1  the replay landed          -- D1 for the zero below. Zero fires is
//                                         also what you get when the journal was
//                                         never restored or the table never
//                                         opened. NEVER CREDIT G1 WITHOUT D1.
//   fires == 0 across the reopen       -- G1, the claim.
//   TRG_R2 + fires == 1 afterwards     -- D1 for the PROBE. A dead callback
//                                         reads zero too. Zero then one: the
//                                         first number is a measured absence,
//                                         and without the second it is a
//                                         silence.
//
// The liveness write is an ordinary unbuffered REPLACE, which reaches the AFTER
// phase through DbArea::replaceFieldStored (dbarea.cpp:330 -> fire_field_replace
// -> fire_record_write), so its kind must be "field_replace" and not
// "record_update" -- the degenerate one-field case where the field genuinely IS
// the whole write. Checking it here re-measures the M2a/M3 unit-and-label split
// from the other side.
// ---------------------------------------------------------------------------
struct RecoveryProbe {
    int         fires = 0;
    std::string last_kind;

    // Snatch mode: copy the live journal at the instant the AFTER phase fires,
    // which is the only instant a committed .tbj exists on disk.
    bool                  snatch   = false;
    bool                  snatched = false;
    std::filesystem::path snatch_to;
    std::string           snatched_from;
};

void trigger_recovery_observe(xbase::DbArea& area,
                              const xbase::trigger_hooks::WriteEvent& ev,
                              void* user) noexcept
{
    auto* p = static_cast<RecoveryProbe*>(user);
    if (!p) return;
    p->fires += 1;
    // noexcept: every allocating or throwing step is inside the try. A probe
    // that terminates the process would take the run with it.
    try {
        p->last_kind = ev.event_kind ? ev.event_kind : "";
        if (p->snatch && !p->snatched) {
            const std::filesystem::path live = area.filename() + ".tbj";
            p->snatched_from = live.string();
            std::error_code ec;
            std::filesystem::copy_file(
                live, p->snatch_to,
                std::filesystem::copy_options::overwrite_existing, ec);
            p->snatched = !ec && std::filesystem::exists(p->snatch_to, ec);
        }
    } catch (...) {}
}

bool trigger_recovery_journal_is_committed(const std::filesystem::path& p)
{
    // The SAME test recovery uses (table_state.cpp: a line whose first field is
    // "C"), on purpose. A second, differently-written test could agree with
    // recovery today and drift from it tomorrow, and the drift would be silent.
    std::istringstream in(slurp_capture_file(p));
    std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
        if (!line.empty() && line[0] == 'C' && (line.size() == 1 || line[1] == ' ')) return true;
    }
    return false;
}

bool run_trigger_recovery_nonrefire(DbArea& area)
{
    namespace fs = std::filesystem;

    std::cout << "\nREGRESSION: AIF-087 M4 -- DOES REPLAY RE-FIRE THE AFTER PHASE?\n"
                 "  Decision E 4.4: recovery replays with area.set + writeCurrent and\n"
                 "  never calls apply_one_recno, so the fire is unreachable BY\n"
                 "  CONSTRUCTION. This arm makes that construction loud if removed.\n"
                 "  The fixture is a REAL committed journal, captured by an AFTER\n"
                 "  callback at the one instant such a file exists.\n"
                 "  READ RULE: zero fires means nothing unless TRG_R1 says the replay\n"
                 "  ran AND the liveness step then fires exactly once.\n";

    const fs::path stash =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP) / "trigger_recovery_committed.tbj";
    std::error_code ec;
    fs::create_directories(stash.parent_path(), ec);
    fs::remove(stash, ec);   // a leftover from an aborted run must not be reused

    // --- 1. fixture ---------------------------------------------------------
    std::string setup_out;
    if (!trigger_veto_run_script(area, kTriggerVetoSetupScript, setup_out)) return false;
    static constexpr std::array<const char*, 2> setup_required{{
        "TRGVETO-SETUP-BEGIN", "TRGVETO-SETUP-END"
    }};
    if (!require_transcript_fragments(setup_out, "RECOVERY SETUP", setup_required)) return false;

    // --- 2. one committed write, and steal the journal on the way past ------
    RecoveryProbe snatcher;
    snatcher.snatch = true;
    snatcher.snatch_to = stash;

    std::string work_out;
    {
        AfterRegistration registered(&trigger_recovery_observe, &snatcher);
        if (!trigger_veto_run_script(area, kTriggerVetoWorkScript, work_out)) return false;
    }

    bool ok = true;
    static constexpr std::array<const char*, 3> work_required{{
        "TRG_W0_fixture_row1_is_alpha:.T.",
        "TRG_W1_row1_took_the_write:.T.",
        "TRG_W2_journal_survived:.F."
    }};
    if (!require_transcript_fragments(work_out, "RECOVERY COMMIT", work_required)) ok = false;

    if (snatcher.fires != 1) {
        std::cout << "RECOVERY: FAIL -- the AFTER phase fired " << snatcher.fires
                  << " time(s) for one committed write.\n"
                     "  The fixture is produced BY that fire, so nothing below is evidence.\n";
        ok = false;
    }
    if (!snatcher.snatched) {
        std::cout << "RECOVERY: NOT RUN -- could not capture the live journal at\n"
                     "  " << snatcher.snatched_from << "\n"
                     "  There is no fixture, so replay is UNMEASURED -- not proven,\n"
                     "  and not refuted.\n";
        return false;
    }
    if (!trigger_recovery_journal_is_committed(stash)) {
        std::cout << "RECOVERY: NOT RUN -- the captured journal carries NO COMMIT marker,\n"
                     "  so recovery would DISCARD it and the arm would be measuring a\n"
                     "  discard while reporting on a replay.\n";
        return false;
    }
    std::cout << "  Captured a committed journal: " << stash.string() << " ("
              << fs::file_size(stash, ec) << " bytes, COMMIT marker present)\n";
    if (!ok) return false;

    // --- 3. poison the record so replay has something to undo ---------------
    std::string poison_out;
    if (!trigger_veto_run_script(area, kTriggerRecoveryPoisonScript, poison_out)) return false;
    static constexpr std::array<const char*, 1> poison_required{{
        "TRG_R0_poison_landed:.T."
    }};
    if (!require_transcript_fragments(poison_out, "RECOVERY POISON", poison_required)) return false;

    // --- 4. put the crash state back on disk --------------------------------
    const fs::path live_journal =
        dottalk::paths::get_slot(dottalk::paths::Slot::DBF) / "TRGVETO.dbf.tbj";
    fs::copy_file(stash, live_journal, fs::copy_options::overwrite_existing, ec);
    if (ec || !fs::exists(live_journal, ec)) {
        std::cout << "RECOVERY: NOT RUN -- could not restore the journal to\n"
                     "  " << live_journal.string() << "\n";
        return false;
    }

    // --- 5. open, let recovery run, and watch a live probe read zero --------
    const fs::path alt_path =
        dottalk::paths::get_slot(dottalk::paths::Slot::TMP) / "trigger_recovery_arm.alt";

    RecoveryProbe probe;
    std::string reopen_out;
    std::string live_out;
    std::string routed_out;
    int fires_after_recovery = -1;
    {
        // The recovery announcement is a catalog message (cmd_use.cpp:991) and
        // travels on the routed channel, so std::cout cannot see it. Capturing
        // it gives a THIRD independent witness that replay ran, beside the data
        // and the fire count.
        AlternateCapture alt(alt_path, "RECOVERY");
        if (!alt.ok()) {
            std::cout << "RECOVERY: NOT RUN -- could not open the ALTERNATE capture at "
                      << alt_path.string() << "\n";
            return false;
        }
        AfterRegistration registered(&trigger_recovery_observe, &probe);
        if (!trigger_veto_run_script(area, kTriggerRecoveryReopenScript, reopen_out)) return false;
        fires_after_recovery = probe.fires;
        if (!trigger_veto_run_script(area, kTriggerRecoveryLivenessScript, live_out)) return false;
    }
    routed_out = slurp_capture_file(alt_path);
    fold_routed_into_cout(routed_out);

    // D1 for the claim: the replay actually ran.
    static constexpr std::array<const char*, 1> reopen_required{{
        "TRG_R1_replay_restored_committed_value:.T."
    }};
    if (!require_transcript_fragments(reopen_out, "RECOVERY REPLAY", reopen_required)) ok = false;

    static constexpr std::array<const char*, 1> routed_required{{
        "recovered a committed table-buffer journal"
    }};
    if (!require_transcript_fragments(routed_out, "RECOVERY REPLAY (routed)", routed_required)) {
        std::cout << "  The engine did not announce a recovery. The data reading above\n"
                  << "  and this are independent witnesses; disagreement between them is\n"
                  << "  itself the finding.\n";
        ok = false;
    }

    std::cout << "  After callback fired " << fires_after_recovery
              << " time(s) across the replay; " << (probe.fires - fires_after_recovery)
              << " time(s) for the liveness write (kind="
              << (probe.last_kind.empty() ? "<none>" : probe.last_kind) << ")\n";

    // G1: the claim itself.
    if (fires_after_recovery != 0) {
        std::cout << "RECOVERY: FAIL -- replay fired the AFTER phase "
                  << fires_after_recovery << " time(s).\n"
                     "  A replayed write is not a new write. Either the fire moved into\n"
                     "  a path recovery reaches, or recovery was refactored to share\n"
                     "  apply_one_recno -- which would look like tidiness.\n";
        ok = false;
    }

    // D1 for the probe: it could have fired, and did, immediately afterwards.
    static constexpr std::array<const char*, 1> live_required{{
        "TRG_R2_liveness_write_landed:.T."
    }};
    if (!require_transcript_fragments(live_out, "RECOVERY LIVENESS", live_required)) ok = false;

    const int liveness_fires = probe.fires - fires_after_recovery;
    if (liveness_fires != 1) {
        std::cout << "RECOVERY: FAIL -- the liveness write produced " << liveness_fires
                  << " fire(s), expected 1.\n"
                     "  THE ZERO ABOVE IS THEREFORE NOT EVIDENCE. A probe that cannot\n"
                     "  fire reads zero for a replay exactly as it reads zero for a\n"
                     "  write, and this arm cannot tell you which one you have.\n";
        ok = false;
    } else if (probe.last_kind != "field_replace") {
        std::cout << "RECOVERY: FAIL -- the liveness event carried kind '"
                  << probe.last_kind << "', expected 'field_replace'.\n"
                     "  A one-field direct write IS the degenerate case; if it now\n"
                     "  reports 'record_update' the unit and the label have parted\n"
                     "  company again.\n";
        ok = false;
    }

    // The replayed log must be gone: recovery removes it, and a survivor would
    // replay again on the next open, forever.
    if (fs::exists(live_journal, ec)) {
        std::cout << "RECOVERY: FAIL -- the journal survived the replay at\n"
                     "  " << live_journal.string() << "\n"
                     "  It would be replayed again on every open.\n";
        ok = false;
    }

    fs::remove(stash, ec);
    fs::remove(alt_path, ec);

    if (!ok) return false;
    std::cout << "RECOVERY: PASS -- a real committed journal replayed its data and\n"
                 "  notified nobody, and the probe that read zero fired one line later.\n"
                 "  STILL OWED: the crash test. This restores the state a crash leaves;\n"
                 "  it does not prove what a crash leaves.\n";
    return true;
}

bool run_trigger_veto_arm_inner(DbArea& area, const std::string& mode)
{
    if (mode == "MULTIREP") return run_trigger_multirep_visibility(area);
    if (mode == "AFTER")    return run_trigger_after_visibility(area);
    if (mode == "RECOVERY") return run_trigger_recovery_nonrefire(area);

    const bool selftest = (mode == "SELFTEST");
    const bool control_ok = run_trigger_veto_control(area);
    if (!control_ok) {
        std::cout << "\nTRIGGER VETO ARM: NOT RUN -- control red, veto pass skipped.\n"
                     "  THIS IS NOT A PASS AND NOT A FAILURE OF THE VETO. The veto\n"
                     "  is UNMEASURED for this run.\n";
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
        return false;
    }

    if (selftest) {
        // Register a callback that IS consulted and ALLOWS the write. Every
        // veto-pass assertion must now fail. If the arm still reports PASS, its
        // detectors do not depend on the refusal and the normal green means
        // nothing.
        std::cout << "\nREGRESSION: TRIGGER VETO SELFTEST -- the arm must go RED.\n"
                     "  Same arm, same scripts, callback ALLOWS instead of refusing.\n"
                     "  A PASS below is a FAILURE of the selftest.\n";
        const bool mutated_ok = run_trigger_veto_refusal(area, &trigger_veto_allow);
        if (mutated_ok) {
            std::cout << "\nTRIGGER VETO SELFTEST: FAIL -- THE ARM PASSED WITH THE VETO\n"
                         "  REMOVED. Its assertions do not depend on the refusal, so a\n"
                         "  green run proves nothing about the veto.\n";
            xbase::error::set_last_error(xbase::error::e_invalid_argument());
            return false;
        }
        std::cout << "\nTRIGGER VETO SELFTEST: PASS -- the arm went red when the veto\n"
                     "  was removed. Its detectors fire on the refusal, not on the\n"
                     "  scaffolding around it.\n";
        xbase::error::clear_last_error();
        return true;
    }

    const bool veto_ok = run_trigger_veto_refusal(area, &trigger_veto_refuse);
    if (!veto_ok) {
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
        return false;
    }

    // WHERE THE EVIDENCE ACTUALLY IS. This banner used to promise that TRGVETO
    // and its journal were left on disk to be read by hand. They are not, and
    // COULD NOT BE, and the second half is why the wording had to change rather
    // than the behaviour: teardown ends with ERASE TABLE TRGVETO CONFIRM, and
    // TRG_T2_journal_cleared ASSERTS the journal is gone after the retry commit.
    // An arm that left a readable journal behind would be an arm reporting a
    // FAILURE. So the promise was not merely stale, it contradicted an assertion
    // in the same run -- and a reader who followed it found an empty sandbox
    // with nothing saying what the emptiness meant.
    //
    // The proof file named on the next line is the evidence, and it is the only
    // capture that HAS the routed channel: the engine writes catalog messages
    // past std::cout, so an outside transcript cannot see them (see
    // trigger_veto_write_proof). Point the reader at the instrument's own
    // capture, never at a fixture the run is required to destroy.
    std::cout << "\nTRIGGER VETO ARM: PASS -- control green, veto green.\n"
                 "  Fixture TRGVETO and its journal are GONE, by design: teardown\n"
                 "  erases the table and TRG_T2 asserts the journal was cleared.\n"
                 "  The proof file named on the next line IS the evidence -- it\n"
                 "  folds in the routed channel, which no outside capture sees.\n";
    xbase::error::clear_last_error();
    return true;
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
    const bool before_ok = run_isolation_arm(area, "BEFORE");
    run_regression_script(area, spec);
    const bool after_ok = run_isolation_arm(area, "AFTER");
    if (!before_ok || !after_ok) {
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
    }
}

void run_regression_default_suite(DbArea& area)
{
    // Plan condition 2: "REGRESSION ALL leaves PRODUCTION unchanged." The arm
    // reads production's high-water before and after everything below, and the
    // BEFORE pass is also what proves the detector is alive on this build.
    const bool before_ok = run_isolation_arm(area, "BEFORE");

    for (const auto& spec : kRegressionSpecs) {
        if (!spec.in_default_suite) continue;
        run_regression_script(area, spec);
    }

    const bool after_ok = run_isolation_arm(area, "AFTER");
    if (!before_ok || !after_ok) {
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
    }
}

bool run_trigger_veto_arm(DbArea& area, const std::string& mode)
{
    std::ostringstream captured;
    std::streambuf* const original = std::cout.rdbuf();
    TeeStreamBuf tee(original, captured.rdbuf());
    std::cout.rdbuf(&tee);

    bool verdict = false;
    try {
        verdict = run_trigger_veto_arm_inner(area, mode);
    } catch (...) {
        std::cout.flush();
        std::cout.rdbuf(original);
        trigger_veto_write_proof(captured.str(), false, mode);
        throw;
    }
    std::cout.flush();
    std::cout.rdbuf(original);
    trigger_veto_write_proof(captured.str(), verdict, mode);
    return verdict;
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

    if (op == "TRIGGERVETO") {
        std::string mode;
        in >> mode;
        std::string up = upper_copy(mode);
        if (up.empty()) up = "NORMAL";
        if (up != "NORMAL" && up != "SELFTEST" && up != "MULTIREP" &&
            up != "AFTER" && up != "RECOVERY") {
            std::cout << "REGRESSION TRIGGERVETO: unknown mode '" << mode
                      << "'. Use NORMAL, SELFTEST, MULTIREP, AFTER or RECOVERY.\n";
            return;
        }
        run_trigger_veto_arm(area, up);
        return;
    }

    if (const RegressionSpec* spec = find_regression_spec(op)) {
        run_regression_script_measured(area, *spec);
        return;
    }

    std::cout << "REGRESSION: unknown option or regression '" << arg1 << "'.\n";
    print_regression_list();
}
