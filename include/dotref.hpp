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
        {"DBAREA",    "DBAREA", "Report or inspect the current DbArea/workspace (diagnostics).", true},

        {"DBAREAS",   "DBAREAS", "Report the current work-area tree and relation-oriented area diagnostics.", true},

        {"STATUS",    "STATUS", "Display area status.", true},

        {"STRUCT",    "STRUCT", "Display table structure.", true},

        {"FIELDS",    "FIELDS", "Show structure (field list).", true},

        {"SET ORDER", "SET ORDER TO <tag>",
                 "Set controlling index tag (compatibility form; see SETORDER).", true},

        {"SETORDER",  "SETORDER <tag>|PHYSICAL",
                 "Set controlling order/tag for the current area (or PHYSICAL for natural order).", true},

        {"SET INDEX", "SET INDEX TO <base>", "Attach/activate a single-tag INX index (base name).", true},

        {"SETINDEX",  "SETINDEX <tag|path>", "Activate an index for the area (DotTalk++ convenience wiring).", true},

        {"SET CDX",   "SET CDX TO <file>", "Attach or inspect a CDX container for the current area.", true},

        {"SETCDX",    "SETCDX TO <file>", "Attach or inspect a CDX container using the compact DotTalk++ command form.", true},

        {"SET CNX",   "SET CNX TO <file>", "Attach or activate a CNX container for the current area.", true},

        {"SET LMDB",  "SET LMDB TO <path>", "Attach or point the current area at an LMDB-backed index environment where supported.", true},

        {"SETLMDB",   "SETLMDB TO <path>", "Attach or point the current area at an LMDB-backed index environment using the compact DotTalk++ form.", true},

        {"SET NEAR",  "SET NEAR ON|OFF|STATUS", "Control near-match seek behavior for active-order navigation.", true},

        {"SET FILTER","SET FILTER TO <expr>", "Set a filter expression using the spaced compatibility form.", true},

        {"SET CASE",  "SET CASE ON|OFF", "Control case-sensitivity using the spaced compatibility form.", true},

        {"SET PATH",  "SET PATH <slot> <path>", "Set a runtime root/path slot using the spaced command form.", true},

        {"SET RELATION", "SET RELATION TO <child> ON <field>[,<field>...]", "Define or route FoxPro-style relation wiring into the DotTalk++ relation backend.", true},

        {"REINDEX",   "REINDEX [ALL]",
                 "Rebuild index files for the current table (or all open tables).", true},

        {"BUILDLMDB", "BUILDLMDB [HELP|?] [MAPSIZE <n[K|M|G]>|SIZE <n[K|M|G]>|TINY|SMALL|MEDIUM|LARGE|XL|HUGE] [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]",
                 "Build or rebuild the LMDB backing store for the current CDX container; may mutate LMDB/index files but not table records.", true},

        {"CDX",       "CDX [INFO|TAGS|CREATE|ADDTAG|DROPTAG] [<path.cdx>]", "Inspect or manage CDX container metadata and tag directories.", true},

        {"INDEX",     "INDEX [ON <field> TAG <name> | STATUS | LIST]", "General index-management command surface for the current table.", true},

        {"LMDB",      "LMDB [USAGE|INFO|OPEN|USE|SEEK|DUMP|SCAN|CLOSE] ...", "Inspect or manage per-area LMDB-backed index/storage wiring where supported.", true},

        {"CNX",       "CNX <name>",
                 "Index container command (CNX multi-tag support).", true},

        {"SETCNX",    "SETCNX TO <file>",
                 "Attach/activate a CNX container for the current area.", true},

        {"INDEXSEEK", "INDEXSEEK <value>", "Seek using the active index/order (DotTalk++ seek wiring).", true},

        {"WHERE",     "WHERE <expr>", "Apply an SQL-like filter to the current context.", true},

        {"SETFILTER", "SETFILTER <expr>", "Set a filter expression (DotTalk++ variant).", true},

        {"CLEAR",     "CLEAR [FILTER|ORDER|REL|ALL]", "Clear current state (filters/orders/relations) depending on context.", true},

        {"SETCASE",   "SETCASE ON|OFF", "Control case-sensitivity / collation mode for comparisons.", true},

        {"PREDHELP",  "PREDHELP [<topic>]", "Help for predicates/expressions and filtering.", true},

        {"PREDICATES","PREDICATES", "List supported predicates/operators for filtering.", true},

        {"SMARTLIST", "SMARTLIST [ALL|DELETED|<n>] [DEBUG] [FOR <expr>]",
        R"(LIST-style output with SQL-grade filtering (order-aware).

        Examples:
            SMARTLIST 20 FOR gpa >= 3.5
            SMARTLIST ALL FOR lname LIKE "SMI%"

        Notes:
            Evaluates filters using the expression/predicate pipeline.)", true},

        {"TABLE", "TABLE <subcommand> ...",
        R"(Table buffering / stale tracking.

        Subcommands:
            TABLE ON
                Enable table buffering for the current area. REPLACE writes into a per-field buffer and
                marks fields STALE instead of immediately writing to disk.

            TABLE OFF
                Disable buffering. REPLACE writes directly to disk (no buffering).

            TABLE STALE
                Show which fields are currently stale (buffered) for the current area.

            TABLE FRESH [ALL|<n>|<n>,<m>]
                Apply buffered updates to disk and clear stale flags on success.
                (Scope forms depend on build; ALL / area lists were previously supported.)

        Notes:
            - In current shakedown observations, LIST output reflects the physical record, not buffered overlays.
            - Some builds may not recognize TABLE REFRESH; prefer TABLE FRESH.)", true},

        {"COMMIT", "COMMIT",
        R"(Commit buffered TABLE updates to disk.

        Notes (current shakedown observations):
            - Clears TABLE stale state on success.
            - May currently trigger full INX rebuild work as part of the commit path (performance issue).)", true},
{"EXPORT", "EXPORT <csv>", "Export to CSV.", true},

        {"EXPORTFUNCTIONS", "EXPORTFUNCTIONS [MD [<path>]]", "Export the expression/function catalog through the canonical command surface.", true},

        {"IMPORT", "IMPORT <csv>", "Import from CSV.", true},

        {"COPY", "COPY <source> TO <target>", "Copy table or data content into another target using DotTalk++ copy semantics.", true},

        {"SETPATH", "SETPATH | SETPATH RESET | SETPATH <SLOT> <path>",
        R"(Manage runtime root directories.

        Usage:
            SETPATH
                Show current roots.

            SETPATH RESET
                Restore defaults (based on DATA root).

            SETPATH <SLOT> <path>
                Set a root slot to absolute(path). If <path> is relative, it is resolved under DATA.

        Slots:
            DATA, DBF, INDEXES, SCHEMAS, SCRIPTS, TESTS, HELP, LOGS, TMP

        Notes:
            Used so HELP/TESTS/etc. can be moved without requiring full paths.)", true},

        {"WORKSPACE", "WORKSPACE [OPEN <DBF|dir>|CLOSE|SAVE <name>|LOAD <name>]",
        R"(Canonical live work-area/session command.

        Usage:
            WORKSPACE
                List current open work areas.

            WORKSPACE CLOSE
                Close all work areas and clear relation state.

            WORKSPACE OPEN DBF
                Scan the configured DBF path slot and open tables into areas 0..N.

            WORKSPACE OPEN <dir>
                Scan a specific directory and open DBFs into areas 0..N.

            WORKSPACE SAVE <name>
                Save a workspace layout where supported.

            WORKSPACE LOAD <name>
                Restore a saved workspace layout where supported.

        Notes:
            WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
            DDL owns schema/definition work.
            WSREPORT owns verbose diagnostics.)", true},

        {"SCHEMAS", "SCHEMAS [OPEN <DBF|dir>|CLOSE]",
        R"(Deprecated compatibility shim for WORKSPACE.

        Current mapping:
            SCHEMAS             -> WORKSPACE
            SCHEMAS OPEN <arg>  -> WORKSPACE OPEN <arg>
            SCHEMAS CLOSE       -> WORKSPACE CLOSE

        Notes:
            Use WORKSPACE for live work-area/session operations.
            Use DDL for schema/definition operations.
            SCHEMAS remains only so older DotScript files continue to run.)", true},

        {"REL", "REL <subcommand> ...",
        R"(Relations engine commands (native DotTalk++ relation graph).

Subcommands:
    REL LIST
    REL LIST ALL
    REL REFRESH
    REL ENUM [LIMIT <n>] <child1> [<child2> ...] TUPLE <tuple-expr>
    REL SAVE [path] | REL SAVE AS <dataset>
    REL LOAD [path] | REL LOAD AS <dataset>
    REL ADD <parent> <child> ON <field>[,<field>...]
    REL CLEAR <parent>|ALL

Examples:
    REL LIST
    REL ADD STUDENTS ENROLL ON SID
    REL ADD ENROLL CLASSES ON CLS_ID
    REL REFRESH

    REL ENUM LIMIT 10 ENROLL CLASSES TASSIGN TEACHERS TUPLE ;
        STUDENTS.SID,STUDENTS.LNAME,ENROLL.CLS_ID,CLASSES.CID,TEACHERS.LNAME

Conceptual Model:
    REL maintains a directed relation graph between work areas.
    REL ADD defines edges.
    REL REFRESH recalculates relation state.
    REL ENUM traverses the graph and emits tuple rows.

Traversal Behavior:
    REL ENUM performs depth-first traversal of the relation chain.
    Each successful path produces one tuple row.

    Example chain:
        STUDENTS -> ENROLL -> CLASSES -> TASSIGN -> TEACHERS

Matching:
    Current implementation uses same-name field equality:
        parent.FIELD == child.FIELD

Notes:
    REL is the native DotTalk++ relation system.
    FoxPro-style SET RELATION commands map into this backend.

    REL ENUM is the row enumeration engine used by relational
    browsers and tuple views.)", true},

        {"REL ENUM", "REL ENUM [LIMIT <n>] <path...> TUPLE <tuple-expr>",
        R"(Traverse a relation chain and emit tuple rows.

Syntax:
    REL ENUM [LIMIT <n>] <child1> [<child2> ...] TUPLE <tuple-expr>

Example:
    REL ENUM LIMIT 5 ENROLL CLASSES TASSIGN TEACHERS
        TUPLE STUDENTS.SID,STUDENTS.LNAME,TEACHERS.LNAME

Execution Model:
    1. Current selected area is the root.
    2. Each child token represents the next relation edge.
    3. Traversal expands matches depth-first.

Example traversal:
    STUDENTS
        -> ENROLL
            -> CLASSES
                -> TASSIGN
                    -> TEACHERS

Each complete path emits one tuple row.

LIMIT:
    LIMIT applies to emitted rows, not intermediate matches.

Projection:
    The TUPLE clause defines which fields are emitted.

Used By:
    SIMPLEBROWSER
    SMARTBROWSER
    relational tuple views.)", true},

        {"RELATIONS", "RELATIONS [USAGE|ALL]",
        R"(Compatibility-facing relation listing surface backed by the native REL engine.

Examples:
    RELATIONS
    RELATIONS ALL

Notes:
    RELATIONS and REL LIST point at the same relation-state reporting lane.
    Prefer REL for the canonical DotTalk++ relation command family.)", true},

        {"REL_LIST", "REL_LIST [ALL]",
                 "Alias for relation-state listing through the REL/RELATIONS reporting lane.", true},

        {"REL_REFRESH", "REL_REFRESH",
                 "Refresh relation state for the current workspace through the native REL backend.", true},

        {"TUPLE", "TUPLE <spec>",
        R"(Build one tuple row from fields across work areas.

        Examples:
            TUPLE *                    (all fields from current area)
            TUPLE LNAME,FNAME          (selected fields from current area)
            TUPLE #11.*                (all fields from area 11)
            TUPLE #9.*,#11.LNAME       (mix of areas)

        Notes:
            #n prefixes a work area slot; "*" means all fields for that area.
            Output fields are separated by ASCII Unit Separator (0x1F).)", true},

        {"TUPTALK", "TUPTALK", "DotTalk++ tuple/logical-row command.", true},

        {"ARCTICTALK", "ARCTICTALK",
        R"(Launch the ArcticTalk Turbo Vision TUI shell.

        Example:
            ARCTICTALK

        Notes:
            Intended for keyboard-driven browsing and diagnostics.
            Exits back to the DotTalk++ CLI.)", true},

        {"FOXTALK", "FOXTALK",
        R"(Legacy alias for the ArcticTalk Turbo Vision TUI shell.

        Example:
            FOXTALK

        Notes:
            Intended for keyboard-driven browsing and diagnostics.
            Exits back to the DotTalk++ CLI.)", true},

        {"BROWSETUI","BROWSETUI", "Text-mode browser UI (developer tool).", true},

        {"BROWSETV", "BROWSETV", "Turbo Vision browser UI (developer tool).", true},

        {"BROWSE",   "BROWSE", "Open the classic browse surface for the current table/work-area context.", true},

        {"BROWSER",  "BROWSER", "Developer browser command (experimental).", true},

        {"RECORDVIEW","RECORDVIEW", "Vertical record viewer.", true},

        {"SIMPLEBROWSER", "SIMPLEBROWSER [options]",
        R"(SIMPLEBROWSER  (SB)
        NAME
            SIMPLEBROWSER

        ALIASES
            SB

        PURPOSE
            Workspace/DbArea-centric interactive browser for table relationships and logical rows.

        SYNTAX
            SIMPLEBROWSER [FOR <expr>] [ORDER <tag>|PHYSICAL] [LIMIT <n>]

        OPTIONS / SUBCOMMANDS
            FOR <expr>           Apply a filter expression (tuple/expr aware).
            CLEAR FOR            Clear active filter.
            ORDER PHYSICAL|INX|CNX|<tag>   Change controlling order/tag.
            SHOW CHILDREN [LIMIT n]        Browse related child rows from current record.
            SHOW|HIDE SCHEMA|JSON          Toggle schema/JSON debug overlays.
            STATUS VERBOSE|COMPACT         Toggle status verbosity.

        EXAMPLES
            SIMPLEBROWSER
            SB FOR lname = "GRIMWOOD"
            SB ORDER LNAME
            SB SHOW CHILDREN LIMIT 20

        NOTES
            Simple Browser is designed for browsing within the current workspace DbArea.
            It is order-aware and expression/predicate aware.

        SEE ALSO
            SMARTBROWSER, SMARTLIST, REL, TUPLE, WORKSPACE

        STATUS
            stable
        )", true},

        {"SB", "SB", "Alias for SIMPLEBROWSER.", true},

        {"SMARTBROWSER", "SMARTBROWSER [options]",
        R"(SMARTBROWSER  (SM, SMART)
        NAME
            SMARTBROWSER

        ALIASES
            SM, SMART

        PURPOSE
            Advanced browser/workhorse for relational + expression-aware browsing across backends.

        SYNTAX
            SMARTBROWSER [<source>] [FOR <expr>] [ORDER <tag>|PHYSICAL]

        OPTIONS / SUBCOMMANDS
            <source>             Optional source (DbArea/workspace, SQLite3, or schema engine where available).
            FOR <expr>           Apply an expression filter using the predicate pipeline.
            ORDER <tag>|PHYSICAL Set controlling order/tag when browsing DbArea-backed sources.

        EXAMPLES
            SMARTBROWSER
            SM FOR gpa >= 3.5
            SMART ORDER LNAME

        NOTES
            Smart Browser is the flagship browser. It can operate with DbArea/workspaces and,
            when configured, can also operate with SQLite3 and schema-driven sources.

        SEE ALSO
            SIMPLEBROWSER, SMARTLIST, WORKSPACE, SQLITE, REL, TUPLE

        STATUS
            stable
        )", true},

        {"SMART", "SMART", "Alias for SMARTBROWSER.", true},

        {"SM",    "SM",    "Alias for SMARTBROWSER.", true},

        {"COLOR", "COLOR <GREEN|AMBER|DEFAULT>",
        R"(Switch CLI/TUI color theme.

        Examples:
            COLOR GREEN
            COLOR G+
            COLOR AMBER
            COLOR DEFAULT

        Notes:
            Used by ArcticTalk/Foxtalk Turbo Vision palette wiring.)", true},

        {"TVISION",   "TVISION", "Turbo Vision diagnostics / demos.", true},

        {"TURBOPACK", "TURBOPACK", "Turbo Vision / pack-related utility.", true},

        {"FOXPRO",    "FOXPRO", "DotTalk++ UI / browser command.", true},

        {"HELP", "HELP [<topic>] | HELP GIANT [USAGE|TOPICS|KIND|SOURCE|<topic>] | HELP /GIANT [USAGE|TOPICS|KIND|SOURCE|<topic>] [/FOX] [/PRED]",
                 "General help entry point; HELP GIANT uses normal shell paging via SET PAGING ON|OFF.", true},

        {"FOXHELP", "FOXHELP [<term>]",
        R"(List or search command help topics.

        Examples:
            FOXHELP
            FOXHELP WORKSPACE
            FOXHELP REL

        Notes:
            Uses the help catalogs and any HELP DBFs.)", true},

        {"CMDHELP", "CMDHELP [BUILD]",
        R"(Build / report the HELP command catalogs.

        Examples:
            CMDHELP BUILD
            CH               (alias report, if enabled)

        Notes:
            Mines command registry + foxref + optional DBF help sources.)", true},

        {"COMMANDSHELP", "COMMANDSHELP", "Command help (alias of CMDHELP).", true},

        {"CMDHELPCHK",   "CMDHELPCHK", "Validate HELP catalogs vs the command registry.", true},


        {"DDICT", "DDICT [STATUS|HELP|TABLES|OBJECTS|FIELDS <table>|TAGS <table>|REL <object>|EVIDENCE <object>]",
        R"(Inspect the active Data Dictionary catalog from inside DotTalk++.

Usage:
    DDICT
    DDICT HELP
    DDICT STATUS
    DDICT TABLES
    DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
    DDICT FIELDS <table>
    DDICT TAGS <table>
    DDICT REL <object-id-or-name> [IN|OUT|BOTH]
    DDICT EVIDENCE <object-id-or-name>

Notes:
    DDICT is read-only over the active Data Dictionary catalog.)", true},

        {"MANUAL", "MANUAL [USAGE|STATUS|TABLES|COUNTS|RESOLVE <token>|CATALOG STATUS|CATALOG TABLES|CATALOG COUNTS|CATALOG RESOLVE <token>|SECTIONS|MEDIA|REVIEW]",
        R"(Inspect the accepted MAN* manualgen catalog from inside DotTalk++.

Usage:
    MANUAL
    MANUAL USAGE
    MANUAL STATUS
    MANUAL TABLES
    MANUAL COUNTS
    MANUAL RESOLVE <token>
    MANUAL CATALOG STATUS
    MANUAL CATALOG TABLES
    MANUAL CATALOG COUNTS
    MANUAL CATALOG RESOLVE <token>
    MANUAL SECTIONS
    MANUAL MEDIA
    MANUAL REVIEW

Notes:
    MANUAL is read-only.
    MANUAL reports accepted MAN* manualgen catalog evidence.
    MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source files, or publication artifacts.
    Resolver/reader/formatter support modules are not registered commands.)", true},

        {"MANSTAR", "MANSTAR [USAGE|<args...>]", "Inspect or drive the MANSTAR/manual-star helper surface where enabled.", true},

        {"MSGMGR", "MSGMGR [USAGE|STATUS|CHECK|SEED PRIORITYA CHECK|SEED PRIORITYA APPLY]",
        R"(Message Manager command house for runtime messaging and locale-spine inspection.

Notes:
    STATUS and CHECK are report-oriented.
    SEED PRIORITYA APPLY mutates SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT and matching messaging LMDB backends.
    MSGMGR does not mutate HELP DATA, CMDHELPCHK, manualgen, Data Dictionary, SelfDoc, or source-derived catalogs.)", true},


        {"BBOX", "BBOX [USAGE|MODEL|LANES|COMMENTS|HELP|MANUALGEN|DATADICT|MESSAGING|MAINT]",
        R"(Teach and inspect the Blackbox model: data enters a processing system and information comes out.

Usage:
    BBOX
    BBOX USAGE
    BBOX MODEL
    BBOX LANES
    BBOX COMMENTS
    BBOX HELP
    BBOX MANUALGEN
    BBOX DATADICT
    BBOX MESSAGING
    BBOX MAINT

Notes:
    BBOX is read-only.
    BBOX is educational.
    BBOX explains SelfDoc lanes using the data in -> processing -> information out model.
    BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.)", true},
        {"MAINT", "MAINT [USAGE|STATUS|LANES|COOKBOOK|BOUNDARY|BBOX|DOCS|GUI|AI|CONTRACTS]",
        R"(Inspect DotTalk++ maintenance lanes, cookbooks, status, AI Friendly, and protected-system boundaries.

Usage:
    MAINT
    MAINT USAGE
    MAINT STATUS
    MAINT LANES
    MAINT COOKBOOK
    MAINT BOUNDARY
    MAINT BBOX
    MAINT DOCS
    MAINT GUI
    MAINT AI
    MAINT AI DASHBOARD
    MAINT AI ASSIMILATE
    MAINT AI BOOK
    MAINT AI INTAKE
    MAINT AI VISIBILITY
    MAINT CONTRACTS

Notes:
    MAINT is read-only first wave.
    MAINT inspects and explains maintenance/SDLC lanes; it does not execute mutation lanes.
    MAINT AI is a read-only native visibility surface for AI Portal partner onboarding, curation, and routing.
    MAINT AI ASSIMILATE points a new or second-opinion AI to the durable repo-local AI Portal.
    The AI Portal is an Alpha Python/registry surface; MAINT AI does not launch it or grant mutation authority.
    MAINT does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.
    PowerShell is MDO scaffolding only; the permanent maintenance app is native C++.)", true},

        {"CMDARGCHK",    "CMDARGCHK", "Validate command argument parsing and report issues.", true},

        {"WSREPORT",     "WSREPORT", "Workspace report / diagnostics.", true},

        {"SHOW",         "SHOW <topic>", "Show internal engine state / debug views.", true},

        {"DUMP",         "DUMP", "Debug: print a structured dump of an internal value/state.", true},

        {"VERSION",      "VERSION", "Print build/version information.", true},

        {"DOTSCRIPT", "DOTSCRIPT <file.dts>",
        R"(Run a DotTalk script file (test harness / automation).

        Example:
            DOTSCRIPT run_all_sql_tests.dts)", true},

        {"TEST", "TEST <script>|<suite>", "DotTalk++ scripting/test harness command.", true},

        {"GO",   "GO <commandLine>", "Execute a DotTalk++ command line (dispatch to command handlers).", true},

        {"SCAN",    "SCAN [ALL|DELETED] [FOR <pred>] [WHILE <pred>] [NEXT <n>|REST]",
                 "Iterate records using a SCAN block (record loop).", true},

        {"ENDSCAN", "ENDSCAN", "End a SCAN block.", true},

        {"CONTINUE","CONTINUE", "Continue a running loop/scan block (scripting control flow).", true},

        {"LOOP",    "LOOP FOR <n> TIMES", "Begin a LOOP block (scripting).", true},

        {"ENDLOOP", "ENDLOOP", "End a LOOP block (scripting).", true},

        {"WHILE",   "WHILE <expr>", "Begin a WHILE block (scripting).", true},

        {"ENDWHILE","ENDWHILE", "End a WHILE block (scripting control flow).", true},

        {"UNTIL",   "UNTIL <expr>", "Begin an UNTIL block (scripting).", true},

        {"ENDUNTIL","ENDUNTIL", "End an UNTIL block (scripting).", true},
{"SET VAR",  "SET VAR <name> TO <value> | SET VAR <name>",
                 "Set or show a macro variable (used by &name expansion in scripts).", true},

        {"SET VAR!", "SET VAR! <name> TO <value> | SET VAR! <name>",
                 "Force-set a macro variable (variant used in some scripts).", true},

        {"CALC", "CALC <expr>",
        R"(Evaluate an expression and display the result.

        Important parsing note:
            In current DotTalk++ behavior, if the expression contains operators like =, >=, <=,
            it should be wrapped in parentheses to avoid being parsed as CALCWRITE syntax.

        Examples:
            CALC 1 + 2
            CALC (UPPER("a") = "A")     && safe
            CALC UPPER("a") = "A"       && may be parsed as CALCWRITE

        Notes:
            Quoted strings containing '=' are treated as literals and should not trigger CALCWRITE.)", true},

        {"CALCWRITE", "CALCWRITE <expr>",
                 "Evaluate an expression and write the result to a target (see command usage).", true},

        {"EVAL", "EVAL <expr>", "Evaluate an expression and print its value.", true},

        {"CONCAT", "CONCAT(<c1>[, <c2> ...]) | CONCAT <args...>",
                 "Concatenate string arguments. (Available as CALC function; also usable as a command where wired.)", true},

        {"STRCAT", "STRCAT(<c1>[, <c2> ...]) | STRCAT <args...>",
                 "Compatibility alias for CONCAT in the DotTalk++ string-expression surface.", true},

        {"SQLITE", "SQLITE <subcommand> ...",
        R"(SQLite integration.

        Examples:
            SQLITE DB data\sql_regression.sqlite
            SQLITE EXEC CREATE TABLE t(x INT)
            SQLITE EXEC INSERT INTO t(x) VALUES (1)
            SQLITE SELECT * FROM t

        Notes:
            Used for regression testing and DBF↔SQL bridging experiments.)", true},

        {"SQLVER", "SQLVER", "Report SQLite availability and version.", true},

        {"SQL",    "SQL <statement>", "Execute an SQL statement using the configured SQL engine.", true},

        {"SQLSEL", "SQLSEL <expr>", "Execute an SQL SELECT and display results.", true},

        {"INSERT", "INSERT <statement>", "Insert data rows (scripting/SQL helper; see command usage).", true},

        {"UPDATE", "UPDATE <statement>", "Update data rows (scripting/SQL helper; see command usage).", true},

        {"DDL", "DDL [args...]", "Canonical schema/definition command family.", true},

        {"SCHEMA", "SCHEMA [args...]", "Deprecated compatibility alias for DDL. Use DDL for schema/definition work.", true},

        {"VALIDATE", "VALIDATE <path>", "Schema/sidecar validation command.", true},

        {"AREA51", "AREA51", "Developer sandbox / experimental command.", true},

        {"GENERIC", "GENERIC", "Developer utility placeholder command.", true},

        {"NORMALIZE", "NORMALIZE <expr>", "Normalize/clean an input expression or text (developer utility).", true},

        {"RECORD", "RECORD", "Display or return the current record context (utility).", true},

        {"LOCK", "LOCK [RECORD|TABLE|<recno>...]", "Lock the current record (or table) for editing.", true},

        {"UNLOCK", "UNLOCK [ALL]", "Release a previously acquired lock (optionally all locks).", true},

        {"REFRESH", "REFRESH", "Refresh internal state / UI view (where applicable).", true},

        {"MULTIREP", "MULTIREP <field>=<expr> ...", "Perform multiple replace operations in one pass (text transform).", true},

        {"ASCEND", "ASCEND", "Set ascending sort direction for the active order/tag.", true},

        {"DESCEND", "DESCEND", "Set descending sort direction for the active order/tag.", true},

        // Phase 5 DOTREF high-visibility/help-adjacent curation batch.
// Phase 1 DOT identity promotion for classic database commands.
        // FOX compatibility entries remain in foxref.hpp.
        // Generated by patch_dotref_phase1_classic_db.py.
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
        {"ERASE", "ERASE <target>", "Erase a file or supported target through the DotTalk++ shell surface.", true},
        {"FIND", "FIND <text> [IN <field>]", "Find text or values using the active order when possible, with scan fallback when needed.", true},
        {"GOTO", "GOTO <recno>|TOP|BOTTOM", "Move the current work area to a specific record or boundary position.", true},
        {"LIST", "LIST [ALL] [FIELDS <list>] [FOR <expr>]", "List records from the current table using DotTalk++ command semantics.", true},
        {"LIST_LMDB", "LIST_LMDB [USAGE|ALL|<limit>|DELETED|NODELETED|ASC|DESC|<tag>]",
                 "List records through the active LMDB order/tag, with LL as the shorthand alias.", true},
        {"LOCATE", "LOCATE FOR <expr> | LOCATE <field> <op> <value>", "Position on the first record matching a predicate or simple field comparison.", true},
        {"PACK", "PACK", "Permanently remove deleted records from the current table.", true},
        {"RECALL", "RECALL", "Unmark the current deleted record when supported by the current table state.", true},
        {"UNDELETE", "UNDELETE", "Compatibility alias for RECALL to unmark the current deleted record.", true},
        {"RECNO", "RECNO", "Report the current record number for the active work area.", true},
        {"REPLACE", "REPLACE <field> WITH <value>", "Replace one field in the current record using table-buffer and memo-aware semantics.", true},
        {"REPLACE_MULTI", "REPLACE_MULTI <field> WITH <value>[, <field> WITH <value>]...", "Perform multiple field replacements in one pass with direct-write/index maintenance semantics.", true},
        {"SEEK", "SEEK <value> [IN <field>] | SEEK <field> = <value>", "Seek through the active order or by scanning a requested field.", true},
        {"SELECT", "SELECT <area-or-alias>", "Select the active DotTalk++ work area by number or logical name.", true},
        {"SET", "SET [<option> [<value>]]", "Show or change DotTalk++ runtime settings.", true},
        {"SKIP", "SKIP [<n>]", "Move relative to the current record in the active work area.", true},
        {"TOP", "TOP", "Move to the first record in the current table/order.", true},
        {"USE", "USE <table> [ALIAS <name>] [NOINDEX]", "Open a DBF table in the active DotTalk++ work area.", true},
        {"ZAP", "ZAP", "Delete all records from the current table.", true},

        // Phase 5 DOTREF high-visibility/help-adjacent curation batch.
        {"ABOUT", "ABOUT",
                 "Print DotTalk++ project identity, lineage, build/runtime information, and current session summary.", true},

        {"BETA", "BETA [LIST|<id>|DONE <id>|DEFER <id>|OPEN <id>|CLEAR <id>|SAVE|LOAD]",
                 "Track and manage beta stabilization notes and local beta-status overrides.", true},

        {"DOTHELP", "DOTHELP [<term>]",
                 "Show project-native DotTalk++ reference entries from the DOTREF catalog.", true},

        {"GPS", "GPS",
                 "Report current session/navigation position and work-area orientation diagnostics.", true},

        {"SHUTDOWN", "SHUTDOWN",
                 "Run DotTalk++ shutdown processing, including shutdown.ini when present.", true},

        {"EXPFUNCS", "EXPFUNCS [MD [<path>]]",
                 "Export the expression/function catalog to Markdown documentation.", true},

        {"AGGS", "AGGS [SUM|AVG|MIN|MAX] <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Aggregate command-family owner for SUM, AVG, MIN, and MAX; use AGGS USAGE for family/subcommand help.", true},

        {"SUM", "SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Direct aggregate verb that sums an expression or numeric field over the current table scope.", true},

        {"AVG", "AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Direct aggregate verb that averages an expression or numeric field over the current table scope.", true},

        {"AVERAGE", "AVERAGE <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Compatibility alias for AVG over the current table scope.", true},

        {"MIN", "MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Direct aggregate verb that reports the minimum value over the current table scope.", true},

        {"MAX", "MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]",
                 "Direct aggregate verb that reports the maximum value over the current table scope.", true},

        // Phase 5 DOTREF curation batch 2: real command surfaces.
        {"MCC", "MCC",
                 "Load the MCC v32 demo workspace by running DotScript x32 and WORKSPACE LOAD mcc.dtschemas.", true},

        {"MEMO", "MEMO [STATUS|VERIFY|GC] [ALL] [CONFIRM]",
                 "Inspect, verify, or garbage-collect memo payload metadata; GC requires CONFIRM for destructive cleanup.", true},

        {"PRN", "PRN [STATUS|ON|OFF|TO <file>|CLOSE]",
                 "Manage printer/output routing for command output and report-style text.", true},

        {"RBROWSE", "RBROWSE",
                 "Launch the relation-aware browser view for the current workspace context.", true},

        {"REGRESSION", "REGRESSION [USAGE|LIST|SHOW <name>|RUN <name>|<name>|ALL]",
                 "Launch curated DotTalk++ regression and shakedown DotScript entrypoints that bootstrap their own environments.", true},

        {"SECURITY", "SECURITY [USAGE|SHOW|SELFTEST|RUNTIME|LOGIN <role> [AS <worker>]|WHOAMI|ASSIGNMENTS|LOGOUT]",
                 "Inspect DotTalk++ security policy/runtime rules and manage the current shell-session role identity and assignment view.", true},

        {"SMARTBROWSE", "SMARTBROWSE [<source>] [FOR <expr>] [ORDER <tag>|PHYSICAL]",
                 "Launch the smart browser surface for relational, expression-aware, and order-aware browsing.", true},

        // Phase 5 DOTREF curation batch 3: small command-surface cleanup.

        // Phase 5 DOTREF curation batch 3: small command-surface cleanup.
        {"BELL", "BELL [ON|OFF]",
                 "Ring the shell bell when enabled, or turn the DotTalk++ bell setting on or off.", true},

        {"IDX", "IDX [USAGE|LIST|DROP <tag>|DROP ALL|ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]]",
                 "Memory-only educational index lab for teaching sort and index concepts without writing persistent index files.", true},

        {"IMAGE", "IMAGE [USAGE|INFO <file>|<file>]",
                 "Inspect image file metadata or open a supported image file in the operating-system viewer.", true},

        {"RETRO", "RETRO [USAGE|LIST|SHOW <system>|<system>|HELP]",
                 "Display ASCII-safe retro computer and system splash screens.", true},

        {"SCX", "SCX [USAGE|CREATE <file>|ADDTAG <file> <name> FIELD <n> [DESC]|BUILD <file>|TAGS <file>|INFO <file>]",
                 "Student/local SCX index-file lab command for creating, tagging, building, listing, and inspecting SCX index files.", true},

        // Phase 5 DOTREF curation batch 4: navigation aliases.
        {"FIRST", "FIRST",
                 "Move to the first record in the current logical order; navigation alias aligned with TOP.", true},

        {"LAST", "LAST",
                 "Move to the last record in the current logical order; navigation alias aligned with BOTTOM.", true},

        {"NEXT", "NEXT [<n>]",
                 "Move forward by one or more records from the current record; navigation alias aligned with SKIP.", true},

        {"PRIOR", "PRIOR [<n>]",
                 "Move backward by one or more records from the current record; navigation alias aligned with SKIP -<n>.", true},

        // Phase 5 DOTREF curation batch 5: small command surfaces.
        {"ASCII", "ASCII [USAGE|TABLE|<value>]",
                 "Display ASCII/character-code reference information for teaching and diagnostics.", true},

        {"AUTODBF", "AUTODBF [USAGE|<source> [TO <dbf>]]",
                 "Create or infer a DBF table from an input source using DotTalk++ automatic DBF-generation rules.", true},

        {"BIBLETALK", "BIBLETALK [USAGE|QUOTE|SEARCH <text>|BOOKS]",
                 "Use the BibleTalk educational seed database for quote, lookup, and teaching/demo workflows.", true},

        {"BOOLEAN", "BOOLEAN [USAGE|<expr>]",
                 "Demonstrate or evaluate boolean/logical expression behavior in the DotTalk++ expression layer.", true},

        {"CASE", "CASE [USAGE|ON|OFF|STATUS]",
                 "Inspect or control case-sensitivity behavior for comparisons and expression/predicate evaluation.", true},

        // Phase 5 DOTREF curation batch 6: educational/demo and expression-adjacent surfaces.
        {"CHRISTMAS", "CHRISTMAS",
                 "Display the DotTalk++ Christmas/holiday console splash screen.", true},

        {"HANUKKAH", "HANUKKAH",
                 "Display the DotTalk++ Hanukkah/holiday console splash screen.", true},

        {"COBOL", "COBOL [USAGE|HELP]",
                 "Display COBOL-oriented educational/demo material for historical data-processing context.", true},

        {"CODASYL", "CODASYL [USAGE|HELP]",
                 "Display CODASYL/network-database educational/demo material for historical database context.", true},

        {"ERP", "ERP [USAGE|HELP]",
                 "Display ERP-oriented educational/demo material connecting database concepts to business systems.", true},

        {"EVALUATE", "EVALUATE <expr>",
                 "Evaluate an expression through the DotTalk++ expression layer and display the result.", true},

        {"TEXT", "TEXT [USAGE|<args...>]",
                 "Text-oriented helper command surface for demonstration, teaching, or local text workflows.", true},

        // Phase 5 DOTREF curation batch 7: creation, import/export, browser, and field-management surfaces.
        {"CREATE", "CREATE [USAGE|<args...>]",
                 "Create a new table, structure, or local project artifact through the implemented DotTalk++ creation surface.", true},

        {"DRAWIO", "DRAWIO [USAGE|<args...>]",
                 "Generate or manage Draw.io-oriented diagram artifacts for documentation and teaching workflows.", true},

        {"ERSATZ", "ERSATZ [USAGE|<args...>]",
                 "Launch or drive the Ersatz relational browser/demo surface for workspace and relation-graph inspection.", true},

        {"EXPORTSQL", "EXPORTSQL [USAGE|<args...>]",
                 "Export DotTalk++ table or workspace data through the SQL export helper surface.", true},

        {"IMPORTSQL", "IMPORTSQL [USAGE|<args...>]",
                 "Import or bridge SQL data into DotTalk++ through the SQL import helper surface.", true},

        {"FIELDMGR", "FIELDMGR [USAGE|<args...>]",
                 "Inspect or manage field-level metadata and field-oriented helper workflows.", true},

        // Phase 5 DOTREF curation batch 8: control-flow and error-status command surfaces.

        // Phase 5 DOTREF curation batch 8: control-flow and error-status command surfaces.
        {"IF", "IF <logical_expr>",
                 "Begin a conditional DotScript block; execute the following block when the logical expression is true.", true},

        {"ELSE", "ELSE",
                 "Begin the alternate branch of an IF block when the IF condition is false.", true},

        {"ENDIF", "ENDIF",
                 "End an IF/ELSE conditional block.", true},

        {"ERROR CLEAR", "ERROR CLEAR",
                 "Clear the current DotTalk++ error/status state.", true},

        {"ERROR STATUS", "ERROR STATUS",
                 "Display the current DotTalk++ error/status state.", true},

        {"ERROR TEST", "ERROR TEST [<args...>]",
                 "Exercise the DotTalk++ error/status reporting path for diagnostics and tests.", true},

        {"ERROR_CLEAR", "ERROR_CLEAR",
                 "Compatibility/direct-handler spelling for ERROR CLEAR.", true},

        {"ERROR_STATUS", "ERROR_STATUS",
                 "Compatibility/direct-handler spelling for ERROR STATUS.", true},

        {"ERROR_TEST", "ERROR_TEST [<args...>]",
                 "Compatibility/direct-handler spelling for ERROR TEST.", true},

        // Phase 5 DOTREF curation batch 9: rebuild, rollback, rules, echo, and SET policy surfaces.
        {"REBUILD", "REBUILD [USAGE|ALL|<target>]",
                 "Rebuild table/index/help-related derived state where supported by the current target context.", true},

        {"ROLLBACK", "ROLLBACK [USAGE|HELP|?]",
                 "Discard staged TABLE/buffered changes without committing them; operational behavior depends on the current buffering state.", true},

        {"RULE", "RULE [USAGE|<args...>]",
                 "Inspect or manage validation-rule metadata and rule-oriented helper workflows.", true},

        {"SECHO", "SECHO [USAGE|<text...>]",
                 "Scripted/student echo helper for emitting text from teaching, demo, or test scripts.", true},

        {"SET UNIQUE", "SET UNIQUE [ON|OFF] | SET UNIQUE FIELD <field> ON|OFF",
                 "View or control uniqueness policy for the current SET command context or a specific field.", true},

        {"SETNEAR", "SETNEAR [ON|OFF|STATUS]",
                 "Compatibility/internal surface for seek-near behavior policy behind SET-family navigation semantics.", true},

        // Phase 5 DOTREF curation batch 10: project, shell, transfer, config, browser, and SIX surfaces.
        {"PROJECTS", "PROJECTS [USAGE|LIST|OPEN <name>|STATUS]",
                 "Inspect or manage DotTalk++ project/workflow entries and project-oriented local state.", true},

        {"PSHELL", "PSHELL [USAGE|<command...>]",
                 "Invoke or document the PowerShell/platform-shell helper surface where enabled by the runtime policy.", true},

        {"BANG", "BANG [USAGE|<command...>]",
                 "Run the host-shell escape surface when enabled by runtime policy; ! is the shell shortcut alias.", true},

        {"SFTP", "SFTP [USAGE|<args...>]",
                 "File-transfer helper surface for SFTP-oriented workflows where enabled by local policy.", true},

        {"SHOWINI", "SHOWINI [USAGE|SYSTEM|USER|ALL]",
                 "Display DotTalk++ initialization/configuration files and resolved startup settings.", true},

        {"INIT", "INIT [USAGE]",
                 "Initialize default paths, perform best-effort stale-lock cleanup, and process startup ini scripts.", true},

        {"SIMPLEBROWSE", "SIMPLEBROWSE [FOR <expr>] [ORDER <tag>|PHYSICAL] [LIMIT <n>]",
                 "Launch the implemented simple browser surface for current work-area, relation, and logical-row inspection.", true},

        {"SIX", "SIX [USAGE|<args...>]",
                 "Experimental or compatibility index-related surface for SIX-style indexing concepts and diagnostics.", true},

        // Phase 5 DOTREF curation batch 11: sort, SQL helper, table metadata, tuple export, and variable surfaces.
        {"SORT", "SORT [USAGE|<args...>]",
                 "Sort or demonstrate ordering behavior through the implemented DotTalk++ sort command surface.", true},

        {"SQLERASE", "SQLERASE [USAGE|<args...>]",
                 "SQL helper surface for erase/drop/delete-style SQL maintenance workflows where enabled.", true},

        {"SQLHELP", "SQLHELP [USAGE|<topic>]",
                 "Show SQL-oriented help and guidance for DotTalk++ SQL bridge workflows.", true},

        {"TABLEMETA", "TABLEMETA [USAGE|<args...>]",
                 "Inspect table metadata, structural facts, and table-oriented metadata helper output.", true},

        {"TUPEXPORT", "TUPEXPORT [USAGE|<args...>]",
                 "Export tuple/projection output through the tuple export helper surface.", true},

        {"VAR", "VAR [USAGE|LIST|SET <name> <value>|CLEAR <name>]",
                 "Inspect or manage DotTalk++ session variables and macro-style script values.", true},

        // Phase 5 DOTREF curation batch 12: example, standard-reference, hierarchy, and student/demo surfaces.
        {"EXAMPLE", "EXAMPLE [USAGE|<name>|LIST]",
                 "Show or run small DotTalk++ example/demo material for teaching and verification workflows.", true},

        {"FOXSTANDARD", "FOXSTANDARD [USAGE|HELP|<topic>]",
                 "Display FoxPro/xBase standard-reference or compatibility teaching material.", true},

        {"HIER", "HIER [USAGE|<args...>]",
                 "Inspect or demonstrate hierarchy-oriented data, relation, or teaching views.", true},

        {"SHELLO", "SHELLO [USAGE|<text...>]",
                 "Small shell/student hello demonstration command for teaching command wiring and output.", true},

        {"STUDENTECHO", "STUDENTECHO [USAGE|<text...>]",
                 "Student/demo echo command used to teach command registration, argument handling, and output.", true},

        {"STUDENTHELLO", "STUDENTHELLO [USAGE]",
                 "Student/demo hello command used to teach the simplest command registration and output path.", true},

        // Phase 5 DOTREF curation batch 13: student/demo, work-area, web, and archive surfaces.
        {"STU_REPEAT", "STU_REPEAT [USAGE|<text...>]",
                 "Student/demo repeat command used to teach argument handling, loops, and command output.", true},

        {"STU_UPPER", "STU_UPPER [USAGE|<text...>]",
                 "Student/demo uppercase command used to teach string handling and command output.", true},

        {"QUIT", "QUIT", "Request DotTalk++ shell shutdown without mutating table data or documentation catalogs.", true},

        {"EXIT", "EXIT", "Alias for QUIT.", true},

        {"WA", "WA [USAGE|<args...>]",
                 "Work-area shorthand/helper surface for inspecting or selecting active work-area context.", true},

        {"WEB", "WEB [USAGE|<args...>]",
                 "Web-oriented helper command surface for local documentation, preview, or integration workflows where enabled.", true},

        {"ZIP", "ZIP [USAGE|<args...>]",
                 "Archive helper command surface for ZIP-oriented local packaging or inspection workflows.", true},

        // Phase 5 DOTREF curation batch 14: developer/diagnostic LMDB, cache, and tuple-helper surfaces.
        {"LMDBDUMP", "LMDBDUMP [USAGE|<args...>]",
                 "Developer/diagnostic surface for dumping or inspecting LMDB-backed index/storage state.", true},

        {"LMDB_UTIL", "LMDB_UTIL [USAGE|<args...>]",
                 "Developer/diagnostic LMDB utility surface for low-level backend inspection and maintenance workflows.", true},

        {"WHERECACHE", "WHERECACHE [USAGE|<args...>]",
                 "Developer/diagnostic surface for inspecting, clearing, or validating WHERE/predicate cache behavior.", true},

        {"TUPLEDELTA", "TUPLEDELTA [USAGE|<args...>]",
                 "Tuple diagnostic helper surface for comparing projected tuple output or tuple-state deltas.", true},

        {"TUPVALIDATE", "TUPVALIDATE [USAGE|<args...>]",
                 "Tuple validation helper surface for checking tuple projection, relation-walk, or logical-row consistency.", true},

        // Phase 5 DOTREF curation batch 15: buffer/control-flow diagnostic surfaces.
        {"LOOP_BUFFER", "LOOP_BUFFER [USAGE|<args...>]",
                 "Developer/diagnostic helper surface for inspecting or testing buffered LOOP control-flow behavior.", true},

        {"SCAN_BUFFER", "SCAN_BUFFER [USAGE|<args...>]",
                 "Developer/diagnostic helper surface for inspecting or testing buffered SCAN/table-iteration behavior.", true},

        {"TABLE_BUFFER", "TABLE_BUFFER [USAGE|<args...>]",
                 "Developer/diagnostic helper surface for inspecting or testing TABLE buffering and stale-field behavior.", true},

        {"UNTIL_BUFFER", "UNTIL_BUFFER [USAGE|<args...>]",
                 "Developer/diagnostic helper surface for inspecting or testing buffered UNTIL control-flow behavior.", true},

        {"WHILE_BUFFER", "WHILE_BUFFER [USAGE|<args...>]",
                 "Developer/diagnostic helper surface for inspecting or testing buffered WHILE control-flow behavior.", true},
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
