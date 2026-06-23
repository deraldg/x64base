#include "command_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <string>

namespace dottalk::doc {

namespace {

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static const CommandDoc HELP_DOC = {
    "HELP",
    "Show command, function, predicate, SQL, and system help topics",

    {
        "HELP",
        "HELP <command>",
        "HELP FUNCTION <name>",
        "HELP FUNCTIONS",
        "HELP PREDICATES",
        "HELP SQL",
        "HELP BETA",
        "HELP /FOX <topic>",
        "HELP /DOT <topic>",
        "HELP /ED <topic>"
    },

    {
        "HELP",
        "HELP COUNT",
        "HELP FUNCTION ALLTRIM",
        "HELP PREDICATES",
        "HELP /FOX SET ORDER"
    },

    {
        "Default lookup checks reflected metadata, then command_catalog docs, then legacy references",
        "HELP GIANT prints the full command catalog/report path"
    },

    {}
};

static const CommandDoc GO_DOC = {
    "GO",
    "Move to a record or navigation endpoint",

    {
        "GO",
        "GO TOP",
        "GO BOTTOM",
        "GO FIRST",
        "GO LAST",
        "GO [TO] <recno>",
        "GO RECORD <recno>",
        "GO +<n>",
        "GO -<n>"
    },

    {
        "GO",
        "GO TOP",
        "GO TO 10",
        "GO RECORD 25",
        "GO +5",
        "GO -1"
    },

    {
        "GO with no arguments refreshes or reports the current record context",
        "TOP and FIRST are synonyms",
        "BOTTOM and LAST are synonyms",
        "Relative movement uses the current work-area cursor"
    },

    {
        "IN <alias> is not supported yet"
    }
};

static const CommandDoc TOP_DOC = {
    "TOP",
    "Move the current work-area cursor to the first logical record",

    { "TOP" },
    { "TOP" },

    {
        "Uses the active order when an order is active",
        "Equivalent user intent to GO TOP / GO FIRST"
    },

    {}
};

static const CommandDoc BOTTOM_DOC = {
    "BOTTOM",
    "Move the current work-area cursor to the last logical record",

    { "BOTTOM" },
    { "BOTTOM" },

    {
        "Uses the active order when an order is active",
        "Equivalent user intent to GO BOTTOM / GO LAST"
    },

    {}
};

static const CommandDoc SKIP_DOC = {
    "SKIP",
    "Move the current work-area cursor forward or backward",

    {
        "SKIP",
        "SKIP <n>",
        "SKIP +<n>",
        "SKIP -<n>"
    },

    {
        "SKIP",
        "SKIP 5",
        "SKIP -1"
    },

    {
        "Default movement is one record forward",
        "Uses active logical order when one is active"
    },

    {}
};

static const CommandDoc RECNO_DOC = {
    "RECNO",
    "Show or return the current record number",

    {
        "RECNO",
        "RECNO()"
    },

    {
        "RECNO",
        "? RECNO()"
    },

    {
        "Command form prints the current record number",
        "Function form is available in expressions where wired"
    },

    {}
};

static const CommandDoc AREA_DOC = {
    "AREA",
    "Report the current work-area slot and table context",

    { "AREA" },
    { "AREA" },

    {
        "This is a non-mutating inspection command",
        "Use SELECT to change the current work area"
    },

    {}
};

static const CommandDoc DBAREAS_DOC = {
    "DBAREAS",
    "Report all open DbArea/workspace slots",

    { "DBAREAS" },
    { "DBAREAS" },

    {
        "Useful after WORKSPACE LOAD or setup scripts",
        "Does not open, close, or mutate tables"
    },

    {}
};

static const CommandDoc COUNT_DOC = {
    "COUNT",
    "Count records in the current work area",

    {
        "COUNT",
        "COUNT ALL",
        "COUNT DELETED",
        "COUNT NOT DELETED",
        "COUNT FOR <expr>",
        "COUNT WHERE <expr>",
        "COUNT <expr>"
    },

    {
        "COUNT",
        "COUNT ALL",
        "COUNT DELETED",
        "COUNT FOR LNAME = \"SMITH\"",
        "COUNT WHERE AGE > 30"
    },

    {
        "Uses current SET FILTER if active",
        "Preserves the current record position",
        "Predicate forms are routed through the expression/predicate pipeline where available"
    },

    {}
};

static const CommandDoc DISPLAY_DOC = {
    "DISPLAY",
    "Display field values for the current or specified record",

    {
        "DISPLAY",
        "DISPLAY <recno>",
        "DISPLAY FIELDS <fieldlist>"
    },

    {
        "DISPLAY",
        "DISPLAY 10",
        "DISPLAY FIELDS LNAME,FNAME"
    },

    {
        "Displays all fields for the current record by default",
        "Optional record number repositions before display",
        "Memo fields should display through resolved memo display services"
    },

    {}
};

static const CommandDoc STATUS_DOC = {
    "STATUS",
    "Display current table/work-area status",

    { "STATUS" },
    { "STATUS" },

    {
        "Reports state without changing the current work area",
        "Useful as a smoke-test checkpoint after USE, SET ORDER, or WORKSPACE LOAD"
    },

    {}
};

static const CommandDoc STRUCT_DOC = {
    "STRUCT",
    "Display the structure of the current table",

    { "STRUCT" },
    { "STRUCT" },

    {
        "Shows field-level structure for the current area",
        "Non-mutating inspection command"
    },

    {}
};

static const CommandDoc FIELDS_DOC = {
    "FIELDS",
    "List fields for the current table",

    { "FIELDS" },
    { "FIELDS" },

    {
        "Compact structure view for command-line inspection",
        "Use STRUCT for a fuller table-structure display"
    },

    {}
};

static const CommandDoc VERSION_DOC = {
    "VERSION",
    "Print build and version information",

    { "VERSION" },
    { "VERSION" },

    {
        "Useful at the top of regression logs and shakedown transcripts"
    },

    {}
};

static const CommandDoc REFRESH_DOC = {
    "REFRESH",
    "Refresh internal state or the active view where supported",

    { "REFRESH" },
    { "REFRESH" },

    {
        "Intended as a low-risk state/view refresh command",
        "Specific UI/browser refresh behavior depends on the active subsystem"
    },

    {}
};

static const CommandDoc COLOR_DOC = {
    "COLOR",
    "Switch CLI/TUI color theme",

    {
        "COLOR",
        "COLOR GREEN",
        "COLOR AMBER",
        "COLOR DEFAULT",
        "COLOR G+"
    },

    {
        "COLOR GREEN",
        "COLOR AMBER",
        "COLOR DEFAULT"
    },

    {
        "Affects presentation only",
        "Used by CLI/Turbo Vision palette wiring"
    },

    {}
};

// First advanced-command usage pass. These docs intentionally describe public
// usage and architectural boundaries without changing parser/runtime behavior.

static const CommandDoc LIST_DOC = {
    "LIST",
    "List records from the current work area",

    {
        "LIST",
        "LIST ALL",
        "LIST DELETED",
        "LIST FIELDS <fieldlist>",
        "LIST FOR <expr>",
        "LIST WHILE <expr>",
        "LIST NEXT <n>",
        "LIST REST"
    },

    {
        "LIST",
        "LIST FIELDS LNAME,FNAME",
        "LIST FOR GPA >= 3.5",
        "LIST NEXT 10"
    },

    {
        "Developer inspection command; SMARTLIST is the preferred order-aware listing path",
        "Should preserve the current cursor unless a handler explicitly documents movement",
        "Filtering is expression/predicate-aware where wired"
    },

    {}
};

static const CommandDoc SMARTLIST_DOC = {
    "SMARTLIST",
    "Order-aware list output with predicate support",

    {
        "SMARTLIST",
        "SMARTLIST <n>",
        "SMARTLIST ALL",
        "SMARTLIST DELETED",
        "SMARTLIST FOR <expr>",
        "SMARTLIST DEBUG"
    },

    {
        "SMARTLIST",
        "SMARTLIST 20",
        "SMARTLIST ALL FOR GPA >= 3.5",
        "SMARTLIST FOR LNAME LIKE \"SMI%\""
    },

    {
        "Preferred listing command for user-facing ordered output",
        "Respects active order and active filter where available",
        "Uses expression/predicate services rather than ad-hoc string matching"
    },

    {}
};

static const CommandDoc SEEK_DOC = {
    "SEEK",
    "Seek an exact value using the active index/order",

    {
        "SEEK <expr>",
        "SEEK <expr> IN <alias>"
    },

    {
        "SEEK \"SMITH\"",
        "SEEK 1001",
        "SEEK DTOS(DATE())"
    },

    {
        "Requires an active table and normally an active order/index",
        "Successful SEEK intentionally moves the current record pointer",
        "Command wording should stay at the CDX/tag/order level; LMDB is a backend detail"
    },

    {
        "Do not document direct LMDB path parsing as public SEEK behavior"
    }
};

static const CommandDoc SET_DOC = {
    "SET",
    "Route modern SET options such as index, order, filter, relation, and output settings",

    {
        "SET <option> [args]",
        "SET INDEX TO <table>.cdx",
        "SET ORDER TO TAG <tag> [IN <alias>]",
        "SET ORDER TO <tag>",
        "SET ORDER TO 0",
        "SET FILTER TO <expr>",
        "SET FILTER TO",
        "SET RELATION TO <expr> INTO <child>",
        "SET PATH",
        "SET PATH RESET",
        "SET PATH <slot> <path>",
        "SET TALK ON|OFF",
        "SET ECHO ON|OFF",
        "SET DELETED ON|OFF"
    },

    {
        "SET INDEX TO students.cdx",
        "SET ORDER TO TAG lname",
        "SET ORDER TO 0",
        "SET FILTER TO GPA >= 3.5",
        "SET FILTER TO",
        "SET PATH INDEXES indexes"
    },

    {
        "SET is the public router; older SETINDEX/SETORDER/SETFILTER forms are compatibility targets",
        "SET INDEX names the logical CDX container, not the physical LMDB backend",
        "Relative SET PATH values are resolved by the path subsystem"
    },

    {}
};

static const CommandDoc SET_INDEX_DOC = {
    "SET INDEX",
    "Attach the current area's index container",

    {
        "SET INDEX TO <table>.cdx",
        "SET INDEX TO"
    },

    {
        "SET INDEX TO students.cdx",
        "SET INDEX TO"
    },

    {
        "Preferred public syntax for attaching or clearing index container state",
        "The command surface should describe CDX/container behavior, not LMDB internals"
    },

    {}
};

static const CommandDoc SET_ORDER_DOC = {
    "SET ORDER",
    "Activate a tag/order or return to physical order",

    {
        "SET ORDER TO TAG <tag> [IN <alias>]",
        "SET ORDER TO <tag>",
        "SET ORDER TO 0",
        "SET ORDER TO PHYSICAL"
    },

    {
        "SET ORDER TO TAG lname",
        "SET ORDER TO dob",
        "SET ORDER TO 0"
    },

    {
        "Controls logical traversal for commands such as TOP, BOTTOM, SKIP, SEEK, and SMARTLIST",
        "SET ORDER TO 0 / PHYSICAL returns traversal to natural table order"
    },

    {}
};

static const CommandDoc SET_FILTER_DOC = {
    "SET FILTER",
    "Set or clear the current work-area filter expression",

    {
        "SET FILTER TO <expr>",
        "SET FILTER TO"
    },

    {
        "SET FILTER TO GPA >= 3.5",
        "SET FILTER TO LNAME LIKE \"SMI%\"",
        "SET FILTER TO"
    },

    {
        "A blank SET FILTER TO clears the active filter",
        "LIST, COUNT, and SMARTLIST should respect the active filter where wired"
    },

    {}
};

static const CommandDoc REL_DOC = {
    "REL",
    "Manage and inspect the DotTalk++ relation graph",

    {
        "REL LIST",
        "REL LIST ALL",
        "REL REFRESH",
        "REL ADD <parent> <child> ON <field>",
        "REL ADD <parent> <child> ON <parentField> TO <childField>",
        "REL CLEAR <parent>",
        "REL CLEAR ALL",
        "REL ENUM [LIMIT <n>] <path...> TUPLE <projection>",
        "REL SAVE [path]",
        "REL LOAD [path]"
    },

    {
        "REL LIST",
        "REL ADD STUDENTS ENROLL ON SID",
        "REL ADD SYS_CMD SYS_SUBCMD ON CAN_NAME TO PARENT",
        "REL REFRESH",
        "REL ENUM LIMIT 10 ENROLL CLASSES TUPLE STUDENTS.SID,CLASSES.CID"
    },

    {
        "REL is the native relation backend",
        "FoxPro-style SET RELATION syntax routes into this model where implemented",
        "REL ENUM traverses relation paths and emits tuple projections"
    },

    {}
};

static const CommandDoc WORKSPACE_DOC = {
    "WORKSPACE",
    "Manage live work-area/session state",

    {
        "WORKSPACE",
        "WORKSPACE OPEN DBF",
        "WORKSPACE OPEN <dir>",
        "WORKSPACE CLOSE",
        "WORKSPACE SAVE <name>",
        "WORKSPACE LOAD <name>"
    },

    {
        "WORKSPACE",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF",
        "WORKSPACE SAVE mcc",
        "WORKSPACE LOAD mcc.dtschemas"
    },

    {
        "WORKSPACE owns live areas, aliases, orders, and relation/session layout",
        "DDL owns schema/definition work",
        "SCHEMAS remains a compatibility shim for older scripts"
    },

    {}
};

static const CommandDoc COMMIT_DOC = {
    "COMMIT",
    "Apply staged table-buffered changes",

    {
        "COMMIT",
        "COMMIT ALL"
    },

    {
        "COMMIT",
        "COMMIT ALL"
    },

    {
        "Applies buffered table changes and clears stale state on success",
        "Index maintenance should flow through the index subsystem rather than direct backend parsing"
    },

    {
        "COMMIT is a mutation boundary; keep help wording conservative until runtime behavior is verified"
    }
};

} // anonymous namespace

const CommandDoc* get(const std::string& command)
{
    const std::string c = upper_copy(command);

    if (c == "HELP") return &HELP_DOC;

    if (c == "GO" || c == "GOTO") return &GO_DOC;
    if (c == "TOP" || c == "FIRST") return &TOP_DOC;
    if (c == "BOTTOM" || c == "LAST") return &BOTTOM_DOC;
    if (c == "SKIP" || c == "NEXT" || c == "PRIOR") return &SKIP_DOC;
    if (c == "RECNO" || c == "RECNO()") return &RECNO_DOC;

    if (c == "AREA") return &AREA_DOC;
    if (c == "DBAREAS") return &DBAREAS_DOC;
    if (c == "COUNT") return &COUNT_DOC;
    if (c == "DISPLAY") return &DISPLAY_DOC;
    if (c == "STATUS") return &STATUS_DOC;
    if (c == "STRUCT") return &STRUCT_DOC;
    if (c == "FIELDS") return &FIELDS_DOC;
    if (c == "VERSION") return &VERSION_DOC;
    if (c == "REFRESH") return &REFRESH_DOC;
    if (c == "COLOR") return &COLOR_DOC;

    if (c == "LIST") return &LIST_DOC;
    if (c == "SMARTLIST" || c == "SL") return &SMARTLIST_DOC;
    if (c == "SEEK" || c == "FIND" || c == "INDEXSEEK") return &SEEK_DOC;

    if (c == "SET") return &SET_DOC;
    if (c == "SET INDEX" || c == "SETINDEX") return &SET_INDEX_DOC;
    if (c == "SET ORDER" || c == "SETORDER") return &SET_ORDER_DOC;
    if (c == "SET FILTER" || c == "SETFILTER") return &SET_FILTER_DOC;

    if (c == "REL" || c == "RELATION" || c == "RELATIONS") return &REL_DOC;
    if (c == "WORKSPACE" || c == "SCHEMAS") return &WORKSPACE_DOC;
    if (c == "COMMIT") return &COMMIT_DOC;

    return nullptr;
}

} // namespace dottalk::doc
