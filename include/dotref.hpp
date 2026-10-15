// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

//dotref.hpp

#pragma once

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>
#include <vector>

namespace dotref {

struct Item {
    const char* name;    // canonical upper-case command name
    const char* syntax;  // short syntax line
    const char* summary; // one-liner (or longer help text)
    bool supported;      // whether DotTalk++ currently supports it
};

// Policy:
// - dotref.hpp is the project-native DotTalk++ reference surface.
// - dotref should describe the public DotTalk++ identity and preferred
//   command/documentation wording, independent of FoxPro compatibility phrasing.
// - foxref may overlap for historical support, but dotref remains the native
//   namespace/reference lane for DotTalk++ help and higher documentation layers.

inline const std::vector<Item>& catalog() {
    static const std::vector<Item> k = {
        // ===== GENERATED DOTREF ROWS -- AIF-171 M3E =====
        // generator: tools/fullstack_docs/emit_dotref_m3d_candidate_v1.py
        // run: DOCFLUSH-20261013-002
        // approved gate sha256: DEEC42244DC5FC2A193F8E53F5348750DBAB86234458F5DC4A06C26FC2C9035B
        // generated rows below; edit REFVOICE/source authority, not this region

        {"DBAREA", "DBAREA", "Report or inspect the current DbArea/workspace (diagnostics).", true},
        {"DBAREAS", "DBAREAS", "Report the current work-area tree and relation-oriented area diagnostics.", true},
        {"STATUS", "STATUS", "Display area status.", true},
        {"STOP_ON_ERROR", "STOP_ON_ERROR [OFF|WARNING|ERROR]", "Set or report the severity threshold at which a running DotScript aborts (stop_on_error[severity]); SET ERRORSTOP TO is the compatibility form, DOTTALK_ERRORSTOP the startup default.", true},
        {"BUILDVECTORS", "BUILDVECTORS | BUILD VECTORS | BUILD INFO", "Report the compile-time engine capacity limits and configuration fingerprint; read-only.", true},
        {"BUILD", "BUILD [VECTORS|INFO]", "Router for the spaced spellings of BUILDVECTORS; reports the compile-time engine capacity limits and configuration fingerprint; read-only.", true},
        {"BUILD VECTORS", "BUILD VECTORS", "Spaced spelling of BUILDVECTORS: report the compile-time engine capacity limits and configuration fingerprint; read-only.", true},
        {"BUILD INFO", "BUILD INFO", "Spaced spelling of BUILDVECTORS: report the compile-time engine capacity limits and configuration fingerprint; read-only.", true},
        {"DEFCMD", "DEFCMD [USAGE|LIST|<NAME> [=] <body-text>]", "Define or list an experimental session-only scratch command; cannot shadow protected built-ins and never writes table data or disk state.", false},
        {"UNDEFCMD", "UNDEFCMD <NAME>", "Remove a session-only scratch command created by DEFCMD; never removes built-ins or unrelated extensions.", false},
        {"DEFFN", "DEFFN [USAGE|LIST|<NAME> [=] <body-text>]", "Define or list an experimental session-only expression function; cannot shadow compiled built-ins and never writes table data or disk state.", false},
        {"UNDEFFN", "UNDEFFN <NAME>", "Remove a session-only custom expression function created by DEFFN; never removes compiled built-ins.", false},
        {"USER", "USER [USAGE|LIST|ROLES|PERMS|WHOAMI|CAN|STORE|ADD|REQUEST|REQUESTS|GRANTS|APPROVE|DENY|REVOKE|GRANT|UNGRANT|DELETE|LOGIN|LOGOUT|PASSWD|TOKEN|AS|ENFORCE|SAVE|LOAD|VERIFY] ...", "Inspect and administer the identity, authentication, and RBAC model; report modes are read-only, while owner-gated administration and persistence modes may update identity metadata and authorization state.", true},
        {"STRUCT", "STRUCT", "Display table structure.", true},
        {"FIELDS", "FIELDS", "Show structure (field list).", true},
        {"SET ORDER", "SET ORDER TO <tag>", "Set controlling index tag (compatibility form; see SETORDER). ramfs/VDISK-aware: attaches a RAM-resident CDX-V64 under a mounted VDISK (AIF-043).", true},
        {"SETORDER", "SETORDER <tag>|PHYSICAL", "Set controlling order/tag for the current area (or PHYSICAL for natural order). ramfs/VDISK-aware: attaches a RAM-resident CDX-V64 under a mounted VDISK (the LMDB env gate is skipped for virtual containers); ordered traversal reads back in native-index order from RAM (AIF-043).", true},
        {"SET INDEX", "SET INDEX TO <base>", "Attach/activate a single-tag INX index (base name).", true},
        {"SETINDEX", "SETINDEX <tag|path>", "Activate an index for the area (DotTalk++ convenience wiring).", true},
        {"SET CDX", "SET CDX TO <file>", "Attach or inspect a CDX container for the current area.", true},
        {"SETCDX", "SETCDX TO <file>", "Attach or inspect a CDX container using the compact DotTalk++ command form.", true},
        {"SET CNX", "SET CNX TO <file>", "Attach or activate a CNX container for the current area.", true},
        {"SET LMDB", "SET LMDB TO <path>", "Attach or point the current area at an LMDB-backed index environment where supported.", true},
        {"SETLMDB", "SETLMDB TO <path>", "Attach or point the current area at an LMDB-backed index environment using the compact DotTalk++ form.", true},
        {"SET NEAR", "SET NEAR ON|OFF|STATUS", "Control near-match seek behavior for active-order navigation.", true},
        {"SET FILTER", "SET FILTER TO <expr>", "Set a filter expression using the spaced compatibility form.", true},
        {"SET CASE", "SET CASE ON|OFF", "Control case-sensitivity using the spaced compatibility form.", true},
        {"SET PATH", "SET PATH <slot> <path>", "Set a runtime root/path slot using the spaced command form. Slots include DBF, INDEXES, LMDB, and RAM (the relocatable in-process RAM-disk root used by VDISK / DO mem for in-memory tables, default data/ram) (AIF-043).", true},
        {"SET RELATION", "SET RELATION TO <child> ON <field>[,<field>...]", "Define or route FoxPro-style relation wiring into the DotTalk++ relation backend.", true},
        {"REINDEX", "REINDEX [ALL]", "Rebuild index files for the current table (or all open tables). ramfs/VDISK-aware: under a mounted VDISK, REINDEX CDX rebuilds the native CDX-V64 (RUN8) container in RAM with no LMDB and no file on disk (AIF-043).", true},
        {"BUILDLMDB", "BUILDLMDB [HELP|?] [MAPSIZE <n[K|M|G]>|SIZE <n[K|M|G]>|TINY|SMALL|MEDIUM|LARGE|XL|HUGE] [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]", "Build or rebuild the LMDB backing store for the current CDX container; may mutate LMDB/index files but not table records.", true},
        {"CDX", "CDX [INFO|TAGS|CREATE|ADDTAG|DROPTAG] [<path.cdx>]", "Inspect or manage CDX container metadata and tag directories. ramfs/VDISK-aware: under a mounted VDISK the container resolves from RAM (a native CDX-V64), so CREATE/ADDTAG/DROPTAG operate on the in-RAM container with no file on disk (AIF-043).", true},
        {"INDEX", "INDEX [ON <field> TAG <name> | STATUS | LIST]", "General index-management command surface for the current table.", true},
        {"LMDB", "LMDB [USAGE|INFO|OPEN|USE|SEEK|DUMP|SCAN|CLOSE] ...", "Inspect or manage per-area LMDB-backed index/storage wiring where supported.", true},
        {"VDISK", "VDISK MOUNT|UNMOUNT|STATUS|CONFIG", "Activate the in-process RAM virtual disk for in-memory tables (AIF-043). MOUNT points the DBF/INDEXES/LMDB path slots under the relocatable RAM slot (default data\\ram) and mounts it as an xbase::ramfs virtual root, so CREATE X64, USE, and native CDX-V64 live entirely in RAM with no files on disk. UNMOUNT drops all RAM files and unmounts (ephemeral teardown). STATUS reports the RAM root, mount state, byte usage, and resident file list. CONFIG shows the optional bin/vdisk.ini admin config (enabled/root/mode/size/warn_pct/on_full), the Layer-1 sizing recommendation, and the Layer-2 soft budget. Relocate the RAM root with SET PATH RAM <path> (or the vdisk.ini root key) before MOUNT. Typically activated via DO mem.", true},
        {"CNX", "CNX <name>", "Index container command (CNX multi-tag support).", true},
        {"SETCNX", "SETCNX TO <file>", "Attach/activate a CNX container for the current area.", true},
        {"INDEXSEEK", "INDEXSEEK <value>", "Seek using the active index/order (DotTalk++ seek wiring).", true},
        {"WHERE", "WHERE <expr>", "Apply an SQL-like filter to the current context.", true},
        {"SETFILTER", "SETFILTER <expr>", "Set a filter expression (DotTalk++ variant).", true},
        {"CLEAR", "CLEAR [FILTER|ORDER|REL|ALL]", "Clear current state (filters/orders/relations) depending on context.", true},
        {"SETCASE", "SETCASE ON|OFF", "Control case-sensitivity / collation mode for comparisons.", true},
        {"PREDHELP", "PREDHELP [<topic>]", "Help for predicates/expressions and filtering.", true},
        {"PREDICATES", "PREDICATES", "List supported predicates/operators for filtering.", true},
        {"SMARTLIST", "SMARTLIST [ALL|DELETED|<n>] [DEBUG] [FOR <expr>]", "(LIST-style output with SQL-grade filtering (order-aware).\n\n        Examples:\n            SMARTLIST 20 FOR gpa >= 3.5\n            SMARTLIST ALL FOR lname LIKE ", true},
        {"TABLE", "TABLE <subcommand> ...", "(Table buffering / stale tracking.\n\n        Subcommands:\n            TABLE ON\n                Enable table buffering for the current area. REPLACE writes into a per-field buffer and\n                marks fields STALE instead of immediately writing to disk.\n\n            TABLE OFF\n                Disable buffering. REPLACE writes directly to disk (no buffering).\n\n            TABLE STALE\n                Show which fields are currently stale (buffered) for the current area.\n\n            TABLE FRESH [ALL|<n>|<n>,<m>]\n                Apply buffered updates to disk and clear stale flags on success.\n                (Scope forms depend on build; ALL / area lists were previously supported.)\n\n        Notes:\n            - In current shakedown observations, LIST output reflects the physical record, not buffered overlays.\n            - Some builds may not recognize TABLE REFRESH; prefer TABLE FRESH.)", true},
        {"COMMIT", "COMMIT", "(Commit buffered TABLE updates to disk.\n\n        Notes (current shakedown observations):\n            - Clears TABLE stale state on success.\n            - May currently trigger full INX rebuild work as part of the commit path (performance issue).)", true},
        {"EXPORT", "EXPORT [TO] <file> [CSV|PIPE|SDF]", "Export to CSV, pipe-delimited text, or fixed-width SDF.", true},
        {"EXPORTFUNCTIONS", "EXPORTFUNCTIONS [MD [<path>]]", "Export the expression/function catalog through the canonical command surface.", true},
        {"IMPORT", "IMPORT <csv>", "Import from CSV.", true},
        {"COPY", "COPY USAGE | COPY TO <DBFNAME> ... | COPY FILE <SRC> TO <DST> [OVERWRITE] | COPY TABLE [<STEM>] [FROM <WS>] [TO <WS>] [WITH INDEXES] [OVERWRITE]", "(Copy the current DBF, convert the current table to a target DBF flavor, copy a filesystem file, or copy a table and its companions between open workspaces.\n\nUsage:\n    COPY USAGE\n    COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n    COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [KEY DROP] [OVERWRITE]\n    COPY TO <DBFNAME> AS X64 VECTOR [KEY DROP] [OVERWRITE]\n    COPY FILE <SRC> TO <DST> [OVERWRITE]\n    COPY TABLE TO <WS> [WITH INDEXES] [OVERWRITE]\n    COPY TABLE FROM <WS> [WITH INDEXES] [OVERWRITE]\n    COPY TABLE <STEM> TO <WS> [WITH INDEXES] [OVERWRITE]\n    COPY TABLE <STEM> FROM <WS> [WITH INDEXES] [OVERWRITE]\n    COPY TABLE <STEM> FROM <WS> TO <WS> [WITH INDEXES] [OVERWRITE]\n\nNotes:\n    COPY TABLE resolves DBF and index roots through the named open workspaces.\n    An omitted stem uses the current area; an omitted FROM or TO uses the current workspace.\n    FROM and TO may not resolve to the same workspace or destination path.\n    No destination may be open in a work area, and WITH INDEXES refuses when no index container exists.)", true},
        {"SETPATH", "SETPATH | SETPATH RESET | SETPATH <SLOT> <path>", "(Manage runtime root directories.\n\n        Usage:\n            SETPATH\n                Show current roots.\n\n            SETPATH RESET\n                Restore defaults (based on DATA root).\n\n            SETPATH <SLOT> <path>\n                Set a root slot to absolute(path). If <path> is relative, it is resolved under DATA.\n\n        Slots:\n            DATA, DBF, INDEXES, SCHEMAS, SCRIPTS, TESTS, HELP, LOGS, TMP\n\n        Notes:\n            Used so HELP/TESTS/etc. can be moved without requiring full paths.)", true},
        {"WORKSPACE", "WORKSPACE [OPEN <DBF|dir>|CLOSE|SAVE <name> [MEMO [V3|MINIDB]]|LOAD <name> [MEMO [RAM]] [PARTIAL]|WRITEBACK <name> [TO <root>] [WITH INDEXES] [CONFIRM]]", "(Canonical live work-area/session command.\n\n        Usage:\n            WORKSPACE\n                List current open work areas.\n\n            WORKSPACE CLOSE\n                Close all work areas and clear relation state.\n\n            WORKSPACE OPEN DBF\n                Scan the configured DBF path slot and open tables into areas 0..N.\n\n            WORKSPACE OPEN <dir>\n                Scan a specific directory and open DBFs into areas 0..N.\n\n            WORKSPACE SAVE <file>\n                Save the posture to a file.\n\n            WORKSPACE SAVE <name> MEMO [V2|V3]\n                Save the POSTURE into the WORKSPACES memo catalog. Tables stay\n                where they are; the posture records where that is.\n\n            WORKSPACE SAVE <name> MEMO MINIDB\n                Save a CONTAINER whose payload IS the database: the posture PLUS\n                every open area's table bytes, and its index bytes when an order\n                is attached. MINIDB implies V3, because the embedded posture must\n                be self-locating to survive being re-pointed at RAM. Reads are\n                residence-aware, so a RAM-resident working set can be saved whole.\n\n            WORKSPACE LOAD <file>\n                Restore a posture from a file.\n\n            WORKSPACE LOAD <name> MEMO\n                Restore a POSTURE from the catalog. REFUSES a MINIDB payload and\n                names the hydration form instead: a container's tables have no\n                disk home, and standing up empty areas over missing files is the\n                silent failure this subsystem exists to prevent.\n\n            WORKSPACE LOAD <name> MEMO RAM\n                Hydrate a MINIDB container into the mounted VDISK with zero disk\n                reads. Requires VDISK MOUNT (or DO mem).\n\n            WORKSPACE LOAD ... PARTIAL\n                Restore only what exists. WITHOUT this, a shortfall ABORTS before\n                anything is closed, so a load that cannot complete leaves the\n                current workspace standing.\n\n            WORKSPACE WRITEBACK <name> [TO <root>] [WITH INDEXES] [CONFIRM]\n                The return leg: write the workspace out of wherever it currently\n                lives (RAM included) onto a real disk root. TO defaults to the\n                catalog row's DBF_ROOT. CONFIRM is required to replace existing\n                files and every replaced file is kept as <name>.__wbak.\n\n            WORKSPACE CATALOG\n                Read-only report over the memo catalog: name, FMT, size, areas,\n                timestamp, author, and which rows are superseded. FMT is the\n                PAYLOAD -- DTSHEMA 2/3 carry a posture and leave the tables\n                where they are; MINIDB 1 carries the table bytes themselves.\n                Every catalogued row is the MEMO carrier by construction; the\n                FILE carrier is the .dtschema files in the same directory,\n                which this table does not track and the footer counts.\n\n        Notes:\n            WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.\n            DDL owns schema/definition work.\n            WSREPORT owns verbose diagnostics.\n\n            ENUMERATION AUTHORITY: both LOAD and WRITEBACK enumerate from the\n            POSTURE -- the record of what the workspace IS -- never from the\n            session's current attach order, and both REFUSE a shortfall rather\n            than complete a partial one. WRITEBACK refuses before writing;\n            LOAD refuses before closing.\n\n            WITH INDEXES copies index container BYTES only. LMDB environments are\n            not carried (they must mmap a real OS file), so the destination needs\n            BUILDLMDB before SET ORDER TO TAG will work. The per-table index\n            CHOICE travels in the posture, which is what lets one workspace mix\n            CNX, CDX and INX.\n\n            .__wbak is ONE generation deep and kept indefinitely: a second\n            confirmed writeback discards the first backup without saying so.\n\n            Relative paths resolve like every other path token -- absolute stays\n            absolute, separators are DATA-root-relative, a bare name sits in its\n            slot.)", true},
        {"SCHEMAS", "SCHEMAS [OPEN <DBF|dir>|CLOSE]", "(Deprecated compatibility shim for WORKSPACE.\n\n        Current mapping:\n            SCHEMAS             -> WORKSPACE\n            SCHEMAS OPEN <arg>  -> WORKSPACE OPEN <arg>\n            SCHEMAS CLOSE       -> WORKSPACE CLOSE\n\n        Notes:\n            Use WORKSPACE for live work-area/session operations.\n            Use DDL for schema/definition operations.\n            SCHEMAS remains only so older DotScript files continue to run.)", false},
        {"REL", "REL <subcommand> ...", "(Relations engine commands (native DotTalk++ relation graph).\n\nSubcommands:\n    REL LIST\n    REL LIST ALL\n    REL REFRESH\n    REL ENUM [LIMIT <n>] <child1> [<child2> ...] TUPLE <tuple-expr>\n    REL SAVE [path] | REL SAVE AS <dataset>\n    REL LOAD [path] | REL LOAD AS <dataset>\n    REL ADD <parent> <child> ON <field>[,<field>...]\n    REL CLEAR <parent>|ALL\n\nExamples:\n    REL LIST\n    REL ADD STUDENTS ENROLL ON SID\n    REL ADD ENROLL CLASSES ON CLS_ID\n    REL REFRESH\n\n    REL ENUM LIMIT 10 ENROLL CLASSES TASSIGN TEACHERS TUPLE ;\n        STUDENTS.SID,STUDENTS.LNAME,ENROLL.CLS_ID,CLASSES.CID,TEACHERS.LNAME\n\nConceptual Model:\n    REL maintains a directed relation graph between work areas.\n    REL ADD defines edges.\n    REL REFRESH recalculates relation state.\n    REL ENUM traverses the graph and emits tuple rows.\n\nTraversal Behavior:\n    REL ENUM performs depth-first traversal of the relation chain.\n    Each successful path produces one tuple row.\n\n    Example chain:\n        STUDENTS -> ENROLL -> CLASSES -> TASSIGN -> TEACHERS\n\nMatching:\n    Current implementation uses same-name field equality:\n        parent.FIELD == child.FIELD\n\nNotes:\n    REL is the native DotTalk++ relation system.\n    FoxPro-style SET RELATION commands map into this backend.\n\n    REL ENUM is the row enumeration engine used by relational\n    browsers and tuple views.)", true},
        {"REL ENUM", "REL ENUM [LIMIT <n>] <path...> TUPLE <tuple-expr>", "(Traverse a relation chain and emit tuple rows.\n\nSyntax:\n    REL ENUM [LIMIT <n>] <child1> [<child2> ...] TUPLE <tuple-expr>\n\nExample:\n    REL ENUM LIMIT 5 ENROLL CLASSES TASSIGN TEACHERS\n        TUPLE STUDENTS.SID,STUDENTS.LNAME,TEACHERS.LNAME\n\nExecution Model:\n    1. Current selected area is the root.\n    2. Each child token represents the next relation edge.\n    3. Traversal expands matches depth-first.\n\nExample traversal:\n    STUDENTS\n        -> ENROLL\n            -> CLASSES\n                -> TASSIGN\n                    -> TEACHERS\n\nEach complete path emits one tuple row.\n\nLIMIT:\n    LIMIT applies to emitted rows, not intermediate matches.\n\nProjection:\n    The TUPLE clause defines which fields are emitted.\n\nUsed By:\n    SIMPLEBROWSER\n    SMARTBROWSER\n    relational tuple views.)", true},
        {"RELATIONS", "RELATIONS [USAGE|ALL]", "(Compatibility-facing relation listing surface backed by the native REL engine.\n\nExamples:\n    RELATIONS\n    RELATIONS ALL\n\nNotes:\n    RELATIONS and REL LIST point at the same relation-state reporting lane.\n    Prefer REL for the canonical DotTalk++ relation command family.)", true},
        {"REL_LIST", "REL_LIST [ALL]", "Alias for relation-state listing through the REL/RELATIONS reporting lane.", true},
        {"REL_REFRESH", "REL_REFRESH", "Refresh relation state for the current workspace through the native REL backend.", true},
        {"TUPLE", "TUPLE <spec>", "(Build one tuple row from fields across work areas.\n\n        Examples:\n            TUPLE *                    (all fields from current area)\n            TUPLE LNAME,FNAME          (selected fields from current area)\n            TUPLE #11.*                (all fields from area 11)\n            TUPLE #9.*,#11.LNAME       (mix of areas)\n\n        Notes:\n            #n prefixes a work area slot; ", true},
        {"TUPTALK", "TUPTALK", "DotTalk++ tuple/logical-row command.", true},
        {"ARCTICTALK", "ARCTICTALK", "(Launch the ArcticTalk Turbo Vision TUI shell.\n\n        Example:\n            ARCTICTALK\n\n        Notes:\n            Intended for keyboard-driven browsing and diagnostics.\n            Exits back to the DotTalk++ CLI.)", true},
        {"FOXTALK", "FOXTALK", "(Legacy alias for the ArcticTalk Turbo Vision TUI shell.\n\n        Example:\n            FOXTALK\n\n        Notes:\n            Intended for keyboard-driven browsing and diagnostics.\n            Exits back to the DotTalk++ CLI.)", true},
        {"BROWSETUI", "BROWSETUI", "Text-mode browser UI (developer tool).", true},
        {"BROWSETV", "BROWSETV", "Turbo Vision browser UI (developer tool).", true},
        {"BROWSE", "BROWSE", "Open the classic browse surface for the current table/work-area context.", true},
        {"BROWSER", "BROWSER", "Developer browser command (experimental).", true},
        {"RECORDVIEW", "RECORDVIEW", "Vertical record viewer.", true},
        {"SIMPLEBROWSER", "SIMPLEBROWSER [options]", "(SIMPLEBROWSER  (SB)\n        NAME\n            SIMPLEBROWSER\n\n        ALIASES\n            SB\n\n        PURPOSE\n            Workspace/DbArea-centric interactive browser for table relationships and logical rows.\n\n        SYNTAX\n            SIMPLEBROWSER [FOR <expr>] [ORDER <tag>|PHYSICAL] [LIMIT <n>]\n\n        OPTIONS / SUBCOMMANDS\n            FOR <expr>           Apply a filter expression (tuple/expr aware).\n            CLEAR FOR            Clear active filter.\n            ORDER PHYSICAL|INX|CNX|CDX|<tag>   Change controlling order/tag.\n            SHOW CHILDREN [LIMIT n]        Browse related child rows from current record.\n            SHOW|HIDE SCHEMA|JSON          Toggle schema/JSON debug overlays.\n            STATUS VERBOSE|COMPACT         Toggle status verbosity.\n\n        EXAMPLES\n            SIMPLEBROWSER\n            SB FOR lname = ", true},
        {"SB", "SB", "Alias for SIMPLEBROWSER.", true},
        {"SMARTBROWSER", "SMARTBROWSER [options]", "(SMARTBROWSER  (SM, SMART)\n        NAME\n            SMARTBROWSER\n\n        ALIASES\n            SM, SMART\n\n        PURPOSE\n            Advanced browser/workhorse for relational + expression-aware browsing across backends.\n\n        SYNTAX\n            SMARTBROWSER [<source>] [FOR <expr>] [ORDER <tag>|PHYSICAL]\n\n        OPTIONS / SUBCOMMANDS\n            <source>             Optional source (DbArea/workspace, SQLite3, or schema engine where available).\n            FOR <expr>           Apply an expression filter using the predicate pipeline.\n            ORDER <tag>|PHYSICAL Set controlling order/tag when browsing DbArea-backed sources.\n\n        EXAMPLES\n            SMARTBROWSER\n            SM FOR gpa >= 3.5\n            SMART ORDER LNAME\n\n        NOTES\n            Smart Browser is the flagship browser. It can operate with DbArea/workspaces and,\n            when configured, can also operate with SQLite3 and schema-driven sources.\n\n        SEE ALSO\n            SIMPLEBROWSER, SMARTLIST, WORKSPACE, SQLITE, REL, TUPLE\n\n        STATUS\n            stable\n        )", true},
        {"SMART", "SMART", "Alias for SMARTBROWSER.", true},
        {"SM", "SM", "Alias for SMARTBROWSER.", true},
        {"COLOR", "COLOR <GREEN|AMBER|DEFAULT>", "(Switch CLI/TUI color theme.\n\n        Examples:\n            COLOR GREEN\n            COLOR G+\n            COLOR AMBER\n            COLOR DEFAULT\n\n        Notes:\n            Used by ArcticTalk/Foxtalk Turbo Vision palette wiring.)", true},
        {"TVISION", "TVISION", "Turbo Vision diagnostics / demos.", false},
        {"APPGUI", "APPGUI", "Launch the windowed Workbench GUI (dottalk_wb) as a separate process, or report by name why it cannot be launched.", true},
        {"GUI", "APPGUI", "Alias for APPGUI: launch the windowed Workbench GUI, or report why it cannot start.", true},
        {"TURBOPACK", "TURBOPACK", "Turbo Vision / pack-related utility.", true},
        {"FOXPRO", "FOXPRO", "DotTalk++ UI / browser command.", true},
        {"HELP", "HELP [<topic>] | HELP GIANT [USAGE|TOPICS|KIND|SOURCE|<topic>] | HELP /GIANT [USAGE|TOPICS|KIND|SOURCE|<topic>] [/FOX] [/PRED]", "General help entry point; HELP GIANT uses normal shell paging via SET PAGING ON|OFF.", true},
        {"FOXHELP", "FOXHELP [<term>]", "(List or search command help topics.\n\n        Examples:\n            FOXHELP\n            FOXHELP WORKSPACE\n            FOXHELP REL\n\n        Notes:\n            Uses the help catalogs and any HELP DBFs.)", true},
        {"CMDHELP", "CMDHELP [BUILD]", "(Build / report the HELP command catalogs.\n\n        Examples:\n            CMDHELP BUILD\n            CH               (alias report, if enabled)\n\n        Notes:\n            Mines command registry + foxref + optional DBF help sources.)", true},
        {"COMMANDSHELP", "COMMANDSHELP", "Command help (alias of CMDHELP).", true},
        {"CMDHELPCHK", "CMDHELPCHK", "Validate HELP catalogs vs the command registry.", true},
        {"CMDREL", "CMDREL", "Print the recipe for relating HELP COMMANDS to CMD_ARGS (help-build diagnostic).", true},
        {"EXITS", "EXITS [LIST|SHOW <id>|VALIDATE|WHERE]", "Inspect and validate the reviewed extension-exit manifest without executing extension code.", true},
        {"DDICT", "DDICT [STATUS|HELP|TABLES|OBJECTS [TYPE <type>] [PROFILE <profile>] [FAMILY LEGACY|X64]|FIELDS <table>|TAGS <table>|REL <object>|EVIDENCE <object>]", "(Inspect the active Data Dictionary catalog from inside DotTalk++.\n\nUsage:\n    DDICT\n    DDICT HELP\n    DDICT STATUS\n    DDICT TABLES\n    DDICT OBJECTS [TYPE <type>] [PROFILE <profile>] [FAMILY LEGACY|X64]\n    DDICT FIELDS <table>\n    DDICT TAGS <table>\n    DDICT REL <object-id-or-name> [IN|OUT|BOTH]\n    DDICT EVIDENCE <object-id-or-name>\n\nNotes:\n    DDICT is read-only over the active Data Dictionary catalog.\n    FAMILY selects the preserved physical catalog family without collapsing identities.)", true},
        {"MANUAL", "MANUAL [USAGE|STATUS|TABLES|COUNTS|RESOLVE <token>|CATALOG STATUS|CATALOG TABLES|CATALOG COUNTS|CATALOG RESOLVE <token>|SECTIONS|MEDIA|REVIEW]", "(Inspect the accepted MAN* manualgen catalog from inside DotTalk++.\n\nUsage:\n    MANUAL\n    MANUAL USAGE\n    MANUAL STATUS\n    MANUAL TABLES\n    MANUAL COUNTS\n    MANUAL RESOLVE <token>\n    MANUAL CATALOG STATUS\n    MANUAL CATALOG TABLES\n    MANUAL CATALOG COUNTS\n    MANUAL CATALOG RESOLVE <token>\n    MANUAL SECTIONS\n    MANUAL MEDIA\n    MANUAL REVIEW\n\nNotes:\n    MANUAL is read-only.\n    MANUAL reports accepted MAN* manualgen catalog evidence.\n    MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source files, or publication artifacts.\n    Resolver/reader/formatter support modules are not registered commands.)", false},
        {"MANSTAR", "MANSTAR [USAGE|<args...>]", "Inspect or drive the MANSTAR/manual-star helper surface where enabled.", false},
        {"MSGMGR", "MSGMGR [USAGE|STATUS|CHECK|SEED PRIORITYA CHECK|SEED PRIORITYA APPLY]", "(Message Manager command house for runtime messaging and locale-spine inspection.\n\nNotes:\n    STATUS and CHECK are report-oriented.\n    SEED PRIORITYA APPLY mutates SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT and matching messaging LMDB backends.\n    MSGMGR does not mutate HELP DATA, CMDHELPCHK, manualgen, Data Dictionary, SelfDoc, or source-derived catalogs.)", true},
        {"BBOX", "BBOX [USAGE|MODEL|LANES|COMMENTS|HELP|MANUALGEN|DATADICT|MESSAGING|MAINT]", "(Teach and inspect the Blackbox model: data enters a processing system and information comes out.\n\nUsage:\n    BBOX\n    BBOX USAGE\n    BBOX MODEL\n    BBOX LANES\n    BBOX COMMENTS\n    BBOX HELP\n    BBOX MANUALGEN\n    BBOX DATADICT\n    BBOX MESSAGING\n    BBOX MAINT\n\nNotes:\n    BBOX is read-only.\n    BBOX is educational.\n    BBOX explains SelfDoc lanes using the data in -> processing -> information out model.\n    BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.)", false},
        {"MAINT", "MAINT [USAGE|STATUS|LANES|COOKBOOK|BOUNDARY|BBOX|DOCS|GUI|AI|CONTRACTS]", "(Inspect DotTalk++ maintenance lanes, cookbooks, status, AI Friendly, and protected-system boundaries.\n\nUsage:\n    MAINT\n    MAINT USAGE\n    MAINT STATUS\n    MAINT LANES\n    MAINT COOKBOOK\n    MAINT BOUNDARY\n    MAINT BBOX\n    MAINT DOCS\n    MAINT GUI\n    MAINT AI\n    MAINT AI USAGE\n    MAINT AI STATUS\n    MAINT AI DASHBOARD\n    MAINT AI ASSIMILATE\n    MAINT AI BOOK\n    MAINT AI INTAKE\n    MAINT AI GATES\n    MAINT AI VISIBILITY\n    MAINT CONTRACTS\n    MAINT CONTRACTS USAGE\n    MAINT CONTRACTS STATUS\n    MAINT CONTRACTS SCAN\n    MAINT CONTRACTS REGISTRY\n    MAINT CONTRACTS INTAKE\n    MAINT CONTRACTS DRIFT\n    MAINT CONTRACTS GATES\n\nNotes:\n    MAINT is read-only first wave.\n    MAINT inspects and explains maintenance/SDLC lanes; it does not execute mutation lanes.\n    MAINT AI is a read-only native visibility surface for AI Portal partner onboarding, curation, and routing.\n    MAINT AI ASSIMILATE points a new or second-opinion AI to the durable repo-local AI Portal.\n    The AI Portal is an Alpha Python/registry surface; MAINT AI does not launch it or grant mutation authority.\n    MAINT does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.\n    PowerShell is MDO scaffolding only; the permanent maintenance app is native C++.)", false},
        {"CMDARGCHK", "CMDARGCHK", "Validate command argument parsing and report issues.", false},
        {"WSREPORT", "WSREPORT", "Workspace report / diagnostics.", true},
        {"SHOW", "SHOW <topic>", "Show internal engine state / debug views.", true},
        {"DUMP", "DUMP", "Debug: print a structured dump of an internal value/state.", true},
        {"VERSION", "VERSION", "Print build/version information.", true},
        {"DOTSCRIPT", "DOTSCRIPT <file.dts>", "(Run a DotTalk script file (test harness / automation).\n\n        Example:\n            DOTSCRIPT run_all_sql_tests.dts)", true},
        {"TEST", "TEST <script>|<suite>", "DotTalk++ scripting/test harness command.", true},
        {"GO", "GO <commandLine>", "Execute a DotTalk++ command line (dispatch to command handlers).", true},
        {"SCAN", "SCAN [ALL|DELETED] [FOR <pred>] [WHILE <pred>] [NEXT <n>|REST]", "Iterate records using a SCAN block (record loop).", true},
        {"ENDSCAN", "ENDSCAN", "End a SCAN block.", true},
        {"CONTINUE", "CONTINUE", "Continue a running loop/scan block (scripting control flow).", true},
        {"LOOP", "LOOP FOR <n> TIMES", "Begin a LOOP block (scripting).", true},
        {"ENDLOOP", "ENDLOOP", "End a LOOP block (scripting).", true},
        {"WHILE", "WHILE <expr>", "Begin a WHILE block (scripting).", true},
        {"ENDWHILE", "ENDWHILE", "End a WHILE block (scripting control flow).", true},
        {"UNTIL", "UNTIL <expr>", "Begin an UNTIL block (scripting).", true},
        {"ENDUNTIL", "ENDUNTIL", "End an UNTIL block (scripting).", true},
        {"SET VAR", "SET VAR <name> TO <value> | SET VAR <name>", "Set or show a macro variable (used by &name expansion in scripts).", true},
        {"SET VAR!", "SET VAR! <name> TO <value> | SET VAR! <name>", "Force-set a macro variable (variant used in some scripts).", true},
        {"CALC", "CALC <expr>", "(Evaluate an expression and display the result.\n\n        Important parsing note:\n            In current DotTalk++ behavior, if the expression contains operators like =, >=, <=,\n            it should be wrapped in parentheses to avoid being parsed as CALCWRITE syntax.\n\n        Examples:\n            CALC 1 + 2\n            CALC (UPPER(", true},
        {"CALCWRITE", "CALCWRITE <expr>", "Evaluate an expression and write the result to a target (see command usage).", true},
        {"EVAL", "EVAL <expr>", "Evaluate an expression and print its value.", true},
        {"CONCAT", "CONCAT(<c1>[, <c2> ...]) | CONCAT <args...>", "Concatenate string arguments. (Available as CALC function; also usable as a command where wired.)", true},
        {"STRCAT", "STRCAT(<c1>[, <c2> ...]) | STRCAT <args...>", "Compatibility alias for CONCAT in the DotTalk++ string-expression surface.", true},
        {"SQLITE", "SQLITE <subcommand> ...", "(SQLite integration.\n\n        Examples:\n            SQLITE DB datasql_regression.sqlite\n            SQLITE EXEC CREATE TABLE t(x INT)\n            SQLITE EXEC INSERT INTO t(x) VALUES (1)\n            SQLITE SELECT * FROM t\n\n        Notes:\n            Used for regression testing and DBF<->SQL bridging experiments.)", true},
        {"SQLVER", "SQLVER", "Report SQLite availability and version.", true},
        {"SQL", "SQL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]", "Scan the CURRENT work area with a predicate and report matches or a count. It does NOT execute SQL statements -- for a SELECT statement use SQLSEL, and for the SQLite bridge use SQLITE. Reads records and may temporarily move the cursor; does not mutate table data.", false},
        {"SQLSEL", "SQLSEL SELECT <cols>|*|COUNT(*) FROM <table> [WHERE <pred>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]", "SQLsel: run a SELECT statement over an OPEN work area. Statement-scoped -- it names its own table, ignores session filter and cursor state, restores every cursor, and reads committed table truth. Bare column names only in v1 (no expression projection, joins, or GROUP BY). The legacy predicate-scan form SQLSEL [COUNT] [FOR <expr>] is still accepted. See SQLSEL USAGE.", true},
        {"INSERT", "INSERT <statement>", "Insert data rows (scripting/SQL helper; see command usage).", true},
        {"UPDATE", "UPDATE <statement>", "Update data rows (scripting/SQL helper; see command usage).", true},
        {"DDL", "DDL [args...]", "Canonical schema/definition command family.", true},
        {"SCHEMA", "SCHEMA [args...]", "Deprecated compatibility alias for DDL. Use DDL for schema/definition work.", true},
        {"VALIDATE", "VALIDATE <path>", "Schema/sidecar validation command.", true},
        {"AREA51", "AREA51", "Developer sandbox / experimental command.", true},
        {"BBS", "BBS [USAGE|BOARDS|READ <board.key> [THREAD <id>] [LAST <n>]|POST <board.key> SUBJECT <s> BODY <t>|REPLY <post.id> BODY <t>|CLOSE <thread.id>]", "AI-BBS persistence substrate: durable boards, threads and posts as x64base DBF under data/metadata/bbs/, with RBAC and attributed authorship; board.governance projects the SYSGRANT request/approve loop (AIF-075).", true},
        {"NET", "NET [USAGE|EGRESS STATUS|EGRESS OPEN [MINUTES <n>] [reason]|EGRESS CLOSE]", "NET EGRESS: read and toggle the WSL/AFB outbound egress isolation as a permissioned, audited capability (host.network.egress; Windows/mirrored-mode). Verified revocable egress isolation, not an air-gap.", true},
        {"CANARY", "CANARY [USAGE]", "Dev canary for the metadata catalog reader adapter: reads the already-open SYSCMD area and reports adapter row/distribution counts (handler cmd_CATALOGCANARY).", true},
        {"EVALDIFF", "EVALDIFF FOR <predicate>", "Compare classic DbArea and TupleRow predicate-evaluator outcomes over the same physical records without changing either evaluator.", false},
        {"GENERIC", "GENERIC", "Developer utility placeholder command.", true},
        {"NORMALIZE", "NORMALIZE <expr>", "Normalize/clean an input expression or text (developer utility).", true},
        {"RECORD", "RECORD", "Display or return the current record context (utility).", true},
        {"LOCK", "LOCK [RECORD|TABLE|<recno>...]", "Lock the current record (or table) for editing.", true},
        {"UNLOCK", "UNLOCK [ALL]", "Release a previously acquired lock (optionally all locks).", true},
        {"REFRESH", "REFRESH", "Refresh internal state / UI view (where applicable).", true},
        {"MULTIREP", "MULTIREP <field>=<expr> ...", "Perform multiple replace operations in one pass (text transform).", true},
        {"ASCEND", "ASCEND", "Set ascending sort direction for the active order/tag.", true},
        {"DESCEND", "DESCEND", "Set descending sort direction for the active order/tag.", true},
        {"AREA", "AREA", "Report the current DotTalk++ work-area state.", true},
        {"APPEND", "APPEND", "Append a new record using current table defaults and active buffering rules.", true},
        {"APPEND_BLANK", "APPEND BLANK", "Append a blank record to the current table.", true},
        {"BOTTOM", "BOTTOM", "Move to the last record in the current table/order.", true},
        {"CLOSE", "CLOSE [ALL|<area>|<alias>]", "Close the current table, a selected area, or all open work areas.", true},
        {"COUNT", "COUNT [FOR <expr>]", "Count records in the current table, optionally using a FOR expression.", true},
        {"DELETE", "DELETE", "Mark the current record deleted using current table semantics.", true},
        {"DISPLAY", "DISPLAY [ALL] [FIELDS <list>] [FOR <expr>]", "Display records from the current table without changing the default DOT help namespace.", true},
        {"DIR", "DIR [<mask>|<path>]", "List directory or file entries through the DotTalk++ shell surface.", true},
        {"ECHO", "ECHO <text...>", "Echo text to the current DotTalk++ output route.", true},
        {"ERASE", "ERASE [<table>|TABLE <table>|DIR <path>] [CONFIRM]", "(Physically delete a table and its sidecars, or a whole directory.\n\n        Usage:\n            ERASE <table> [CONFIRM]\n            ERASE TABLE <table> [CONFIRM]\n                Delete the DBF plus its same-stem sidecars.\n\n            ERASE DIR <path> [CONFIRM]\n                Delete a directory and everything under it. No .dbf\n                normalization and no sidecar sweep -- a landed writeback target\n                has no table token, and forcing one would mangle the path.\n\n        Notes:\n            Without CONFIRM, ERASE reports what it WOULD delete and does nothing.\n\n            BLAST RADIUS, worth reading before pointing it anywhere: the table\n            form sweeps THREE INDEPENDENT SLOTS -- DBF sidecars in place, index\n            containers through the active INDEXES slot, and the LMDB environment\n            through the active LMDB slot. If those slots point at different\n            datasets, ERASE reaches into all of them, and the deletions it makes\n            in a slot you forgot to repoint are reported in the same\n            undifferentiated file count as the ones you intended. Measured\n            2026-08-12, by destroying a shared fixture's LMDB environment from a\n            scratch root that had repointed only two slots of three.\n\n            A scratch root must own ALL THREE SLOTS before anything destructive\n            runs in it.)", true},
        {"EDIT", "EDIT [USAGE] <file>", "Launch the configured external editor for a file path; OS-sensitive (spawns the editor as a child process, editor.mode Off disables it). See the @dottalk.external contract in src/edu/edu_edit.cpp.", true},
        {"FIND", "FIND <text> [IN <field>]", "Find text or values using the active order when possible, with scan fallback when needed.", true},
        {"GOTO", "GOTO <recno>|TOP|BOTTOM", "Move the current work area to a specific record or boundary position.", true},
        {"LIST", "LIST [ALL] [FIELDS <list>] [FOR <expr>]", "List records from the current table using DotTalk++ command semantics.", true},
        {"LIST_LMDB", "LIST_LMDB [USAGE|ALL|<limit>|DELETED|NODELETED|ASC|DESC|<tag>]", "List records through the active LMDB order/tag, with LL as the shorthand alias.", true},
        {"LOCATE", "LOCATE FOR <expr> | LOCATE <field> <op> <value>", "Position on the first record matching a predicate or simple field comparison.", true},
        {"PACK", "PACK", "Permanently remove deleted records from the current table.", true},
        {"RECALL", "RECALL", "Unmark the current deleted record when supported by the current table state.", true},
        {"UNDELETE", "UNDELETE", "Compatibility alias for RECALL to unmark the current deleted record.", true},
        {"RECNO", "RECNO", "Report the current record number for the active work area.", true},
        {"REPLACE", "REPLACE <field> WITH <value>", "Replace one field in the current record using table-buffer and memo-aware semantics.", true},
        {"SEEK", "SEEK <value> [IN <field>] | SEEK <field> = <value>", "Seek through the active order or by scanning a requested field.", true},
        {"SELECT", "SELECT <area-or-alias>", "Select the active DotTalk++ work area by number or logical name.", true},
        {"SET", "SET [<option> [<value>]]", "Show or change DotTalk++ runtime settings.", true},
        {"SKIP", "SKIP [<n>]", "Move relative to the current record in the active work area.", true},
        {"TOP", "TOP", "Move to the first record in the current table/order.", true},
        {"USE", "USE <table> [ALIAS <name>] [NOINDEX]", "Open a DBF table in the active DotTalk++ work area.", true},
        {"ZAP", "ZAP", "Delete all records from the current table.", true},
        {"ABOUT", "ABOUT", "Print DotTalk++ project identity, lineage, build/runtime information, and current session summary.", true},
        {"BETA", "BETA [LIST|<id>|DONE <id>|DEFER <id>|OPEN <id>|CLEAR <id>|SAVE|LOAD]", "Track and manage beta stabilization notes and local beta-status overrides.", true},
        {"DOTHELP", "DOTHELP [<term>]", "Show project-native DotTalk++ reference entries from the DOTREF catalog.", true},
        {"GPS", "GPS", "Report current session/navigation position and work-area orientation diagnostics.", true},
        {"SHUTDOWN", "SHUTDOWN", "Run DotTalk++ shutdown processing, including shutdown.ini when present.", true},
        {"EXPFUNCS", "EXPFUNCS [MD [<path>]]", "Export the expression/function catalog to Markdown documentation.", true},
        {"AGGS", "AGGS [SUM|AVG|MIN|MAX] <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Aggregate command-family owner for SUM, AVG, MIN, and MAX; use AGGS USAGE for family/subcommand help.", true},
        {"SUM", "SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Direct aggregate verb that sums an expression or numeric field over the current table scope.", true},
        {"AVG", "AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Direct aggregate verb that averages an expression or numeric field over the current table scope.", true},
        {"AVERAGE", "AVERAGE <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Compatibility alias for AVG over the current table scope.", true},
        {"MIN", "MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Direct aggregate verb that reports the minimum value over the current table scope.", true},
        {"MAX", "MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]", "Direct aggregate verb that reports the maximum value over the current table scope.", true},
        {"MCC", "MCC", "Load the MCC v32 demo workspace by running DotScript x32 and WORKSPACE LOAD mcc.dtschemas.", true},
        {"MEMO", "MEMO [STATUS|VERIFY|GC] [ALL] [CONFIRM]", "Inspect, verify, or garbage-collect memo payload metadata; GC requires CONFIRM for destructive cleanup.", true},
        {"PRN", "PRN [STATUS|ON|OFF|TO <file>|CLOSE]", "Manage printer/output routing for command output and report-style text.", true},
        {"RBROWSE", "RBROWSE", "Launch the relation-aware browser view for the current workspace context.", true},
        {"REGRESSION", "REGRESSION [USAGE|LIST|FIND <words...>|SHOW <name>|RUN <name>|<name>|ALL]", "(Launch curated DotTalk++ regression and shakedown DotScript entrypoints that bootstrap their own environments.\n\n        Usage:\n            REGRESSION LIST                 Browse the curated entrypoints.\n            REGRESSION FIND <words...>      Search names, script filenames and\n                                            summaries. Every term must match.\n            REGRESSION SHOW <name>          Summary plus the resolved script path.\n            REGRESSION RUN <name>           Run it.\n            REGRESSION ALL                  Run the curated default suite.\n\n        Notes:\n            THE SPEC IS THE HOW-TO. A regression script is the only documentation\n            in this tree that cannot drift silently, because a stale one goes red.\n            Read the script for worked usage, or RUN it to watch it work.\n\n            FIND exists because LIST and SHOW both assume you already know the\n            NAME. Nobody arrives knowing to type WORKSPACE_MINIDB when the\n            question in their head is ", true},
        {"SECURITY", "SECURITY [USAGE|SHOW|SELFTEST|RUNTIME|LOGIN <role> [AS <worker>]|WHOAMI|ASSIGNMENTS|LOGOUT]", "Inspect DotTalk++ security policy/runtime rules and manage the current shell-session role identity and assignment view.", true},
        {"BELL", "BELL [ON|OFF]", "Ring the shell bell when enabled, or turn the DotTalk++ bell setting on or off.", true},
        {"IDX", "IDX [USAGE|LIST|DROP <tag>|DROP ALL|ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]]", "Memory-only educational index lab for teaching sort and index concepts without writing persistent index files.", true},
        {"IMAGE", "IMAGE [USAGE|INFO <file>|<file>]", "Inspect image file metadata or open a supported image file in the operating-system viewer.", true},
        {"RETRO", "RETRO [USAGE|LIST|SHOW <system>|<system>|HELP]", "Display ASCII-safe retro computer and system splash screens.", true},
        {"SCX", "SCX [USAGE|CREATE <file>|ADDTAG <file> <name> FIELD <n> [DESC]|BUILD <file>|TAGS <file>|INFO <file>]", "Student/local SCX index-file lab command for creating, tagging, building, listing, and inspecting SCX index files.", true},
        {"FIRST", "FIRST", "Move to the first record in the current logical order; navigation alias aligned with TOP.", true},
        {"LAST", "LAST", "Move to the last record in the current logical order; navigation alias aligned with BOTTOM.", true},
        {"NEXT", "NEXT [<n>]", "Move forward by one or more records from the current record; navigation alias aligned with SKIP.", true},
        {"PRIOR", "PRIOR [<n>]", "Move backward by one or more records from the current record; navigation alias aligned with SKIP -<n>.", true},
        {"ASCII", "ASCII [USAGE|TABLE|<value>]", "Display ASCII/character-code reference information for teaching and diagnostics.", true},
        {"AUTODBF", "AUTODBF [USAGE|<source> [TO <dbf>]]", "Create or infer a DBF table from an input source using DotTalk++ automatic DBF-generation rules.", false},
        {"BIBLETALK", "BIBLETALK [USAGE|QUOTE|SEARCH <text>|BOOKS]", "Use the BibleTalk educational seed database for quote, lookup, and teaching/demo workflows.", true},
        {"BOOLEAN", "BOOLEAN [USAGE|<expr>]", "Demonstrate or evaluate boolean/logical expression behavior in the DotTalk++ expression layer.", true},
        {"FORMULA", "FORMULA [USAGE|<expr>]", "Evaluate a scalar expression through the xexpr engine and print the formatted value (education eval command; its FoxPro ? / ?? print form is carried in foxref).", true},
        {"CASE", "CASE [USAGE|ON|OFF|STATUS]", "Inspect or control case-sensitivity behavior for comparisons and expression/predicate evaluation.", true},
        {"CHRISTMAS", "CHRISTMAS", "Display the DotTalk++ Christmas/holiday console splash screen.", true},
        {"HANUKKAH", "HANUKKAH", "Display the DotTalk++ Hanukkah/holiday console splash screen.", true},
        {"COBOL", "COBOL [USAGE|HELP]", "Display COBOL-oriented educational/demo material for historical data-processing context.", true},
        {"CODASYL", "CODASYL [USAGE|HELP]", "Display CODASYL/network-database educational/demo material for historical database context.", true},
        {"ERP", "ERP [USAGE|HELP]", "Display ERP-oriented educational/demo material connecting database concepts to business systems.", true},
        {"EVALUATE", "EVALUATE <expr>", "Evaluate an expression through the DotTalk++ expression layer and display the result.", true},
        {"TEXT", "TEXT [USAGE|<args...>]", "Text-oriented helper command surface for demonstration, teaching, or local text workflows.", true},
        {"CREATE", "CREATE [USAGE|<args...>]", "Create a new table, structure, or local project artifact through the implemented DotTalk++ creation surface.", true},
        {"DRAWIO", "DRAWIO [USAGE|<args...>]", "Generate or manage Draw.io-oriented diagram artifacts for documentation and teaching workflows.", true},
        {"ERSATZ", "ERSATZ [USAGE|<args...>]", "Launch or drive the Ersatz relational browser/demo surface for workspace and relation-graph inspection.", true},
        {"EXPORTSQL", "EXPORTSQL [USAGE|<args...>]", "Export DotTalk++ table or workspace data through the SQL export helper surface.", false},
        {"IMPORTSQL", "IMPORTSQL [USAGE|<args...>]", "Import or bridge SQL data into DotTalk++ through the SQL import helper surface.", false},
        {"FIELDMGR", "FIELDMGR [USAGE|<args...>]", "Inspect or manage field-level metadata and field-oriented helper workflows.", true},
        {"IF", "IF <logical_expr>", "Begin a conditional DotScript block; execute the following block when the logical expression is true.", true},
        {"ELSE", "ELSE", "Begin the alternate branch of an IF block when the IF condition is false.", true},
        {"ENDIF", "ENDIF", "End an IF/ELSE conditional block.", true},
        {"ERROR CLEAR", "ERROR CLEAR", "Clear the current DotTalk++ error/status state.", true},
        {"ERROR STATUS", "ERROR STATUS", "Display the current DotTalk++ error/status state.", true},
        {"ERROR TEST", "ERROR TEST [<args...>]", "Exercise the DotTalk++ error/status reporting path for diagnostics and tests.", true},
        {"ERROR_CLEAR", "ERROR_CLEAR", "Compatibility/direct-handler spelling for ERROR CLEAR.", true},
        {"ERROR_STATUS", "ERROR_STATUS", "Compatibility/direct-handler spelling for ERROR STATUS.", true},
        {"ERROR_TEST", "ERROR_TEST [<args...>]", "Compatibility/direct-handler spelling for ERROR TEST.", true},
        {"REBUILD", "REBUILD [USAGE|ALL|<target>]", "Rebuild table/index/help-related derived state where supported by the current target context.", true},
        {"ROLLBACK", "ROLLBACK [USAGE|HELP|?]", "Discard staged TABLE/buffered changes without committing them; operational behavior depends on the current buffering state.", true},
        {"RULE", "RULE [USAGE|<args...>]", "Inspect or manage validation-rule metadata and rule-oriented helper workflows.", true},
        {"SECHO", "SECHO [USAGE|<text...>]", "Scripted/student echo helper for emitting text from teaching, demo, or test scripts.", true},
        {"SET UNIQUE", "SET UNIQUE [ON|OFF] | SET UNIQUE FIELD <field> ON|OFF", "View or control uniqueness policy for the current SET command context or a specific field.", true},
        {"SETNEAR", "SETNEAR [ON|OFF|STATUS]", "Compatibility/internal surface for seek-near behavior policy behind SET-family navigation semantics.", true},
        {"PROJECTS", "PROJECTS [USAGE|LIST|OPEN <name>|STATUS]", "Inspect or manage DotTalk++ project/workflow entries and project-oriented local state.", true},
        {"PSHELL", "PSHELL [USAGE|<command...>]", "Invoke or document the PowerShell/platform-shell helper surface where enabled by the runtime policy.", true},
        {"BANG", "BANG [USAGE|<command...>]", "Run the host-shell escape surface when enabled by runtime policy; ! is the shell shortcut alias.", true},
        {"SFTP", "SFTP [USAGE|<args...>]", "File-transfer helper surface for SFTP-oriented workflows where enabled by local policy.", true},
        {"SMTP", "SMTP [USAGE|STATUS|PROBE|SEND FROM <file> [TO <addr>] SUBJECT <text>]", "Mail helper surface: probe the configured server or send a message body, where enabled by local policy. Credentials come from the environment and are never read or printed by the command.", false},
        {"SHOWINI", "SHOWINI [USAGE|SYSTEM|USER|ALL]", "Display DotTalk++ initialization/configuration files and resolved startup settings.", true},
        {"INIT", "INIT [USAGE]", "Initialize default paths, perform best-effort stale-lock cleanup, and process startup ini scripts.", true},
        {"SIX", "SIX [USAGE|<args...>]", "Experimental or compatibility index-related surface for SIX-style indexing concepts and diagnostics.", true},
        {"SORT", "SORT [USAGE|<args...>]", "Sort or demonstrate ordering behavior through the implemented DotTalk++ sort command surface.", true},
        {"SQLERASE", "SQLERASE [USAGE|<args...>]", "SQL helper surface for erase/drop/delete-style SQL maintenance workflows where enabled.", true},
        {"SQLHELP", "SQLHELP [USAGE|<topic>]", "Show SQL-oriented help and guidance for DotTalk++ SQL bridge workflows.", true},
        {"TABLEMETA", "TABLEMETA [USAGE|<args...>]", "Inspect table metadata, structural facts, and table-oriented metadata helper output.", true},
        {"TUPEXPORT", "TUPEXPORT [USAGE|<args...>]", "Export tuple/projection output through the tuple export helper surface.", true},
        {"VAR", "VAR USAGE | VAR <name> = <expr>", "Evaluate an expression and store it as a scoped DotScript memory variable, referenced later as $name (e.g. VAR n = 40 + 2 then ? $n). Distinct from SET VAR (&macro) variables.", true},
        {"EXAMPLE", "EXAMPLE [USAGE|<name>|LIST]", "Show or run small DotTalk++ example/demo material for teaching and verification workflows.", true},
        {"FOXSTANDARD", "FOXSTANDARD [USAGE|HELP|<topic>]", "Display FoxPro/xBase standard-reference or compatibility teaching material.", true},
        {"HIER", "HIER [USAGE|<args...>]", "Inspect or demonstrate hierarchy-oriented data, relation, or teaching views.", true},
        {"SHELLO", "SHELLO [USAGE|<text...>]", "Small shell/student hello demonstration command for teaching command wiring and output.", true},
        {"STUDENTECHO", "STUDENTECHO [USAGE|<text...>]", "Student/demo echo command used to teach command registration, argument handling, and output.", false},
        {"STUDENTHELLO", "STUDENTHELLO [USAGE]", "Student/demo hello command used to teach the simplest command registration and output path.", false},
        {"STU_REPEAT", "STU_REPEAT [USAGE|<text...>]", "Student/demo repeat command used to teach argument handling, loops, and command output.", true},
        {"STU_UPPER", "STU_UPPER [USAGE|<text...>]", "Student/demo uppercase command used to teach string handling and command output.", true},
        {"QUIT", "QUIT", "Request DotTalk++ shell shutdown without mutating table data or documentation catalogs.", true},
        {"EXIT", "EXIT", "Alias for QUIT.", true},
        {"WA", "WA [USAGE|<args...>]", "Work-area shorthand/helper surface for inspecting or selecting active work-area context.", true},
        {"WEB", "WEB [USAGE|<args...>]", "Web-oriented helper command surface for local documentation, preview, or integration workflows where enabled.", true},
        {"ZIP", "ZIP [USAGE|<args...>]", "Archive helper command surface for ZIP-oriented local packaging or inspection workflows.", true},
        {"LMDBDUMP", "LMDBDUMP [USAGE|<args...>]", "Developer/diagnostic surface for dumping or inspecting LMDB-backed index/storage state.", true},
        {"LMDB_UTIL", "LMDB_UTIL [USAGE|<args...>]", "Developer/diagnostic LMDB utility surface for low-level backend inspection and maintenance workflows.", false},
        {"WHERECACHE", "WHERECACHE [USAGE|<args...>]", "Developer/diagnostic surface for inspecting, clearing, or validating WHERE/predicate cache behavior.", true},
        {"TUPLEDELTA", "TUPLEDELTA [USAGE|<args...>]", "Tuple diagnostic helper surface for comparing projected tuple output or tuple-state deltas.", false},
        {"TUPVALIDATE", "TUPVALIDATE [USAGE|<args...>]", "Tuple validation helper surface for checking tuple projection, relation-walk, or logical-row consistency.", true},
        {"LOOP_BUFFER", "LOOP_BUFFER [USAGE|<args...>]", "Developer/diagnostic helper surface for inspecting or testing buffered LOOP control-flow behavior.", true},
        {"SCAN_BUFFER", "SCAN_BUFFER [USAGE|<args...>]", "Developer/diagnostic helper surface for inspecting or testing buffered SCAN/table-iteration behavior.", true},
        {"TABLE_BUFFER", "TABLE_BUFFER [USAGE|<args...>]", "Developer/diagnostic helper surface for inspecting or testing TABLE buffering and stale-field behavior.", true},
        {"UNTIL_BUFFER", "UNTIL_BUFFER [USAGE|<args...>]", "Developer/diagnostic helper surface for inspecting or testing buffered UNTIL control-flow behavior.", true},
        {"WHILE_BUFFER", "WHILE_BUFFER [USAGE|<args...>]", "Developer/diagnostic helper surface for inspecting or testing buffered WHILE control-flow behavior.", true},
        {"GROUPCOMMIT", "GROUPCOMMIT [AUTO|MANUAL]", "Commit every buffered area as ONE atomic decision, so a crash leaves either ALL members applied or NONE. COMMIT ALL's atomic twin.", true},
        {"WORKDESK", "WORKDESK [USAGE]", "Report the desk -- every open workspace in this session with its areas, identity, lineage and roots.", false},
};
    return k;
}

inline std::string upcopy(std::string_view s) {
    std::string out(s.begin(), s.end());
    std::transform(out.begin(), out.end(), out.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return out;
}

inline const Item* find(std::string_view name) {
    const std::string key = upcopy(name);
    for (const auto& item : catalog()) {
        if (upcopy(item.name) == key) {
            return &item;
        }
    }
    return nullptr;
}

inline std::vector<const Item*> search(std::string_view token) {
    std::vector<const Item*> matches;
    const std::string key = upcopy(token);

    for (const auto& item : catalog()) {
        const std::string n = upcopy(item.name);
        const std::string s = item.syntax  ? upcopy(item.syntax)  : std::string{};
        const std::string d = item.summary ? upcopy(item.summary) : std::string{};

        if (n.find(key) != std::string::npos ||
            s.find(key) != std::string::npos ||
            d.find(key) != std::string::npos) {
            matches.push_back(&item);
        }
    }
    return matches;
}

} // namespace dotref
