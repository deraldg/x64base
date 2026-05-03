#include "fox_standard_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <string>
#include <unordered_map>

namespace dottalk::foxstd {
namespace {

std::string trim_copy(std::string s)
{
    const auto first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return {};
    }

    const auto last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) {
            return static_cast<char>(std::toupper(c));
        });
    return s;
}

std::string normalize_key(const std::string& raw)
{
    std::string s = upper_copy(trim_copy(raw));

    // Collapse internal whitespace so "SET   ORDER" and "SET ORDER" match.
    std::string out;
    bool last_space = false;
    for (char ch : s) {
        const unsigned char c = static_cast<unsigned char>(ch);
        if (std::isspace(c)) {
            if (!last_space && !out.empty()) {
                out.push_back(' ');
                last_space = true;
            }
        } else {
            out.push_back(ch);
            last_space = false;
        }
    }

    if (!out.empty() && out.back() == ' ') {
        out.pop_back();
    }

    return out;
}

const std::vector<FoxStandardDoc>& docs()
{
    static const std::vector<FoxStandardDoc> kDocs = {
    FoxStandardDoc{
        "USE",
        "Open a table in a work area.",
        {
            "USE <table_name> [IN <area>] [INDEX <index_file>]"
        },
        {
            "USE STUDENTS",
            "USE TEACHERS IN 2"
        },
        {
            "Key database command from the static FoxPro reference.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE",
        "Create a new table or other FoxPro artifact.",
        {
            "CREATE <table_name>",
            "CREATE TABLE <table_name>",
            "CREATE <artifact>"
        },
        {
            "CREATE STUDENTS",
            "CREATE TABLE STUDENTS"
        },
        {
            "Generic historical CREATE verb. Specific subforms vary by version.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "INDEX",
        "Create an index on an expression or field.",
        {
            "INDEX ON <expression> TAG <tag_name> [OF <index_file>]"
        },
        {
            "INDEX ON LNAME TAG LNAME"
        },
        {
            "DotTalk++ uses CDX terminology on the public surface while LMDB remains a backend detail.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "REINDEX",
        "Rebuild indexes for the current table.",
        {
            "REINDEX"
        },
        {
            "REINDEX"
        },
        {
            "Historical command for rebuilding active/associated indexes.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SELECT",
        "Switch to a work area.",
        {
            "SELECT <area_number>",
            "SELECT <alias>"
        },
        {
            "SELECT 2",
            "SELECT STUDENTS"
        },
        {
            "Classic xBase work-area command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE",
        "Close tables, indexes, databases, or other open resources.",
        {
            "CLOSE [TABLES | INDEXES | DATABASES]",
            "CLOSE ALL"
        },
        {
            "CLOSE TABLES",
            "CLOSE ALL"
        },
        {
            "Historical CLOSE has many subforms.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "APPEND",
        "Append records or append from another source.",
        {
            "APPEND",
            "APPEND BLANK",
            "APPEND FROM <source_table>",
            "APPEND FROM ARRAY",
            "APPEND GENERAL",
            "APPEND MEMO",
            "APPEND PROCEDURES"
        },
        {
            "APPEND BLANK",
            "APPEND FROM OLDSTUDENTS"
        },
        {
            "APPEND BLANK and APPEND FROM are the main data-engine forms.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DELETE",
        "Mark records for deletion.",
        {
            "DELETE [FOR <condition>]"
        },
        {
            "DELETE",
            "DELETE FOR LNAME = \"SMITH\""
        },
        {
            "Deletion is logical until PACK or equivalent physical cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "REPLACE",
        "Replace field values in records.",
        {
            "REPLACE <field> WITH <value> [FOR <condition>]"
        },
        {
            "REPLACE LNAME WITH \"SMITH\""
        },
        {
            "Core xBase mutation command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LOCATE",
        "Search for the first record matching a condition.",
        {
            "LOCATE FOR <condition>"
        },
        {
            "LOCATE FOR LNAME = \"SMITH\""
        },
        {
            "Often paired with CONTINUE.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "FIND",
        "Search an indexed table for a key.",
        {
            "FIND <key_value>"
        },
        {
            "FIND SMITH"
        },
        {
            "Historical indexed lookup command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SEEK",
        "Search an active index/order for a key.",
        {
            "SEEK <key_value>",
            "SEEK <key_value> IN <field>"
        },
        {
            "SEEK \"SMITH\""
        },
        {
            "Closely related to FIND in xBase command surfaces.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SKIP",
        "Move the record pointer forward or backward.",
        {
            "SKIP [<n>]"
        },
        {
            "SKIP",
            "SKIP -1"
        },
        {
            "Moves relative to current record.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "GO",
        "Move the record pointer to an endpoint or record number.",
        {
            "GO TOP",
            "GO BOTTOM",
            "GO <recno>",
            "GO TO <recno>",
            "GO RECORD <recno>"
        },
        {
            "GO TOP",
            "GO 10"
        },
        {
            "GOTO is a common alias.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "GOTO",
        "Alias form of GO.",
        {
            "GOTO TOP",
            "GOTO BOTTOM",
            "GOTO <recno>"
        },
        {
            "GOTO TOP"
        },
        {
            "Historical alias for GO.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SET ORDER",
        "Set the controlling index order/tag.",
        {
            "SET ORDER TO <tag_name>",
            "SET ORDER TO 0"
        },
        {
            "SET ORDER TO LNAME"
        },
        {
            "Core index navigation command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SET RELATION",
        "Link tables based on an expression into another work area.",
        {
            "SET RELATION TO <expression> INTO <table>"
        },
        {
            "SET RELATION TO STUDENT_ID INTO ENROLL"
        },
        {
            "Historical relation command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY",
        "Copy records, files, structures, indexes, memo fields, procedures, or tags.",
        {
            "COPY TO <new_table> [FOR <condition>]",
            "COPY FILE <source> TO <target>",
            "COPY STRUCTURE TO <target>",
            "COPY STRUCTURE EXTENDED TO <target>",
            "COPY TAG <tag> TO <target>"
        },
        {
            "COPY TO NEWSTUDENTS",
            "COPY STRUCTURE TO EMPTY_STUDENTS"
        },
        {
            "Many subforms exist; data copy and structure copy are most relevant to DotTalk++.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ZAP",
        "Permanently remove all records from a table.",
        {
            "ZAP"
        },
        {
            "ZAP"
        },
        {
            "Destructive historical command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SORT",
        "Sort a table into a new table.",
        {
            "SORT TO <new_table> ON <field> [/A|/D]"
        },
        {
            "SORT TO STUDSORT ON LNAME /A"
        },
        {
            "Creates a sorted output table in classic usage.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COUNT",
        "Count records, optionally with a condition.",
        {
            "COUNT [FOR <condition>]",
            "COUNT ALL",
            "COUNT WHILE <condition>"
        },
        {
            "COUNT",
            "COUNT FOR GPA >= 3.0"
        },
        {
            "Scope and optimization behavior vary by implementation.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SET DELETE",
        "Toggle whether deleted records are considered visible.",
        {
            "SET DELETE ON|OFF"
        },
        {
            "SET DELETE ON"
        },
        {
            "Classic xBase SET option.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "SET TALK",
        "Toggle command-result chatter.",
        {
            "SET TALK ON|OFF"
        },
        {
            "SET TALK OFF"
        },
        {
            "Classic command output control.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ACCEPT",
        "Accept character input.",
        {
            "ACCEPT [<prompt>]"
        },
        {
            "ACCEPT \"Name: \" TO m.name"
        },
        {
            "Mostly language/runtime oriented.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ACTIVATE MENU",
        "Activate a menu.",
        {
            "ACTIVATE MENU <menu_name>"
        },
        {
            "ACTIVATE MENU main"
        },
        {
            "UI/menu oriented.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ACTIVATE POPUP",
        "Activate a popup menu.",
        {
            "ACTIVATE POPUP <popup_name>"
        },
        {
            "ACTIVATE POPUP choices"
        },
        {
            "UI/menu oriented.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ACTIVATE SCREEN",
        "Activate the screen.",
        {
            "ACTIVATE SCREEN"
        },
        {
            "ACTIVATE SCREEN"
        },
        {
            "Legacy UI surface.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ACTIVATE WINDOW",
        "Activate a window.",
        {
            "ACTIVATE WINDOW <window_name>"
        },
        {
            "ACTIVATE WINDOW mainwin"
        },
        {
            "Legacy UI surface.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ADD CLASS",
        "Add a class to a class library.",
        {
            "ADD CLASS <class_name> OF <classlib>"
        },
        {
            "ADD CLASS Customer OF app.vcx"
        },
        {
            "Visual FoxPro object/class feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ADD OBJECT",
        "Add an object to a class or container.",
        {
            "ADD OBJECT <object_name> AS <class>"
        },
        {
            "ADD OBJECT cmdOK AS CommandButton"
        },
        {
            "Visual FoxPro object feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ADD TABLE",
        "Add a table to a database.",
        {
            "ADD TABLE <table_name>"
        },
        {
            "ADD TABLE students"
        },
        {
            "Database-container oriented.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ALTER TABLE",
        "Alter table structure.",
        {
            "ALTER TABLE <table_name> <clause>"
        },
        {
            "ALTER TABLE students ADD COLUMN active L"
        },
        {
            "SQL-style table alteration in VFP.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ASSERT",
        "Assert a condition for debugging.",
        {
            "ASSERT <condition>"
        },
        {
            "ASSERT nCount > 0"
        },
        {
            "Debugging command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BEGIN TRANSACTION",
        "Start a transaction.",
        {
            "BEGIN TRANSACTION"
        },
        {
            "BEGIN TRANSACTION"
        },
        {
            "Transaction-oriented command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BUILD APP",
        "Build an APP file.",
        {
            "BUILD APP <app_name> FROM <project>"
        },
        {
            "BUILD APP myapp FROM myproj"
        },
        {
            "IDE/project build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BUILD DLL",
        "Build a DLL.",
        {
            "BUILD DLL <dll_name> FROM <project>"
        },
        {
            "BUILD DLL mylib FROM myproj"
        },
        {
            "IDE/project build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BUILD EXE",
        "Build an EXE.",
        {
            "BUILD EXE <exe_name> FROM <project>"
        },
        {
            "BUILD EXE myapp FROM myproj"
        },
        {
            "IDE/project build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BUILD MTDLL",
        "Build a multithreaded DLL.",
        {
            "BUILD MTDLL <dll_name> FROM <project>"
        },
        {
            "BUILD MTDLL server FROM myproj"
        },
        {
            "IDE/project build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BUILD PROJECT",
        "Build a project.",
        {
            "BUILD PROJECT <project_name>"
        },
        {
            "BUILD PROJECT myproj"
        },
        {
            "IDE/project build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CALL",
        "Call a binary subroutine.",
        {
            "CALL <address_or_routine>"
        },
        {
            "CALL myproc"
        },
        {
            "Low-level legacy feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CANCEL",
        "Cancel program execution.",
        {
            "CANCEL"
        },
        {
            "CANCEL"
        },
        {
            "Program-control command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CD",
        "Change directory.",
        {
            "CD <path>"
        },
        {
            "CD data"
        },
        {
            "Alias-style directory command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CHDIR",
        "Change directory.",
        {
            "CHDIR <path>"
        },
        {
            "CHDIR data"
        },
        {
            "Directory command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CHANGE",
        "Change records interactively.",
        {
            "CHANGE [FIELDS <field-list>] [FOR <condition>]"
        },
        {
            "CHANGE"
        },
        {
            "Interactive data edit command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR",
        "Clear screen, memory, menus, windows, or other runtime state.",
        {
            "CLEAR",
            "CLEAR ALL",
            "CLEAR SCREEN",
            "CLEAR MEMORY",
            "CLEAR WINDOWS"
        },
        {
            "CLEAR SCREEN"
        },
        {
            "Many historical CLEAR subforms exist.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR ALL",
        "Clear variables and close files.",
        {
            "CLEAR ALL"
        },
        {
            "CLEAR ALL"
        },
        {
            "Broad runtime reset.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR CLASS",
        "Clear a class definition.",
        {
            "CLEAR CLASS <class_name>"
        },
        {
            "CLEAR CLASS Customer"
        },
        {
            "VFP class feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR CLASSLIB",
        "Clear a class library.",
        {
            "CLEAR CLASSLIB <classlib>"
        },
        {
            "CLEAR CLASSLIB app.vcx"
        },
        {
            "VFP class-library feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR DLLS",
        "Clear loaded DLLs.",
        {
            "CLEAR DLLS"
        },
        {
            "CLEAR DLLS"
        },
        {
            "Runtime external-library cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR EVENTS",
        "Clear event loop.",
        {
            "CLEAR EVENTS"
        },
        {
            "CLEAR EVENTS"
        },
        {
            "VFP event-loop command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR FIELDS",
        "Clear field list.",
        {
            "CLEAR FIELDS"
        },
        {
            "CLEAR FIELDS"
        },
        {
            "Runtime/display state.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR GETS",
        "Clear pending GETs.",
        {
            "CLEAR GETS"
        },
        {
            "CLEAR GETS"
        },
        {
            "Legacy UI/input command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR MACROS",
        "Clear macros.",
        {
            "CLEAR MACROS"
        },
        {
            "CLEAR MACROS"
        },
        {
            "Runtime macro cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR MEMORY",
        "Clear memory variables.",
        {
            "CLEAR MEMORY"
        },
        {
            "CLEAR MEMORY"
        },
        {
            "Runtime memory-variable cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR MENUS",
        "Clear menus.",
        {
            "CLEAR MENUS"
        },
        {
            "CLEAR MENUS"
        },
        {
            "UI/menu cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR POPUPS",
        "Clear popups.",
        {
            "CLEAR POPUPS"
        },
        {
            "CLEAR POPUPS"
        },
        {
            "UI/menu cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR PROGRAM",
        "Clear program cache.",
        {
            "CLEAR PROGRAM"
        },
        {
            "CLEAR PROGRAM"
        },
        {
            "Runtime program-cache cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR PROMPT",
        "Clear prompt.",
        {
            "CLEAR PROMPT"
        },
        {
            "CLEAR PROMPT"
        },
        {
            "UI prompt cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR READ",
        "Clear READ level.",
        {
            "CLEAR READ"
        },
        {
            "CLEAR READ"
        },
        {
            "Legacy UI/input command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR RESOURCES",
        "Clear resource cache.",
        {
            "CLEAR RESOURCES"
        },
        {
            "CLEAR RESOURCES"
        },
        {
            "Runtime resource cleanup.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR SCREEN",
        "Clear the screen.",
        {
            "CLEAR SCREEN"
        },
        {
            "CLEAR SCREEN"
        },
        {
            "Display command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR TYPEAHEAD",
        "Clear keyboard buffer.",
        {
            "CLEAR TYPEAHEAD"
        },
        {
            "CLEAR TYPEAHEAD"
        },
        {
            "Input-buffer command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLEAR WINDOWS",
        "Clear windows.",
        {
            "CLEAR WINDOWS"
        },
        {
            "CLEAR WINDOWS"
        },
        {
            "Legacy UI command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE ALL",
        "Close all open resources.",
        {
            "CLOSE ALL"
        },
        {
            "CLOSE ALL"
        },
        {
            "Broad close command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE ALTERNATE",
        "Close alternate output file.",
        {
            "CLOSE ALTERNATE"
        },
        {
            "CLOSE ALTERNATE"
        },
        {
            "Output redirection related.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE DATABASES",
        "Close databases.",
        {
            "CLOSE DATABASES"
        },
        {
            "CLOSE DATABASES"
        },
        {
            "Database-container command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE DEBUGGER",
        "Close debugger.",
        {
            "CLOSE DEBUGGER"
        },
        {
            "CLOSE DEBUGGER"
        },
        {
            "Debugger command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE FORMAT",
        "Close format file.",
        {
            "CLOSE FORMAT"
        },
        {
            "CLOSE FORMAT"
        },
        {
            "Legacy format resource.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE INDEXES",
        "Close indexes.",
        {
            "CLOSE INDEXES"
        },
        {
            "CLOSE INDEXES"
        },
        {
            "Index resource command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE MEMO",
        "Close memo file.",
        {
            "CLOSE MEMO"
        },
        {
            "CLOSE MEMO"
        },
        {
            "Memo resource command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE PRINTER",
        "Close printer.",
        {
            "CLOSE PRINTER"
        },
        {
            "CLOSE PRINTER"
        },
        {
            "Printer/output command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE PROCEDURE",
        "Close procedure file.",
        {
            "CLOSE PROCEDURE"
        },
        {
            "CLOSE PROCEDURE"
        },
        {
            "Procedure resource command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CLOSE TABLES",
        "Close tables.",
        {
            "CLOSE TABLES"
        },
        {
            "CLOSE TABLES"
        },
        {
            "Table resource command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE",
        "Compile code or an artifact.",
        {
            "COMPILE <file>",
            "COMPILE FORM <form>",
            "COMPILE REPORT <report>"
        },
        {
            "COMPILE myprog.prg"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE CLASSLIB",
        "Compile class library.",
        {
            "COMPILE CLASSLIB <classlib>"
        },
        {
            "COMPILE CLASSLIB app.vcx"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE DATABASE",
        "Compile database.",
        {
            "COMPILE DATABASE <database>"
        },
        {
            "COMPILE DATABASE appdbc"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE FORM",
        "Compile form.",
        {
            "COMPILE FORM <form>"
        },
        {
            "COMPILE FORM customer"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE LABEL",
        "Compile label.",
        {
            "COMPILE LABEL <label>"
        },
        {
            "COMPILE LABEL mailing"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COMPILE REPORT",
        "Compile report.",
        {
            "COMPILE REPORT <report>"
        },
        {
            "COMPILE REPORT invoice"
        },
        {
            "Development/build command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CONTINUE",
        "Continue a LOCATE search.",
        {
            "CONTINUE"
        },
        {
            "CONTINUE"
        },
        {
            "Paired with LOCATE.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY FILE",
        "Copy a file.",
        {
            "COPY FILE <source> TO <target>"
        },
        {
            "COPY FILE a.txt TO b.txt"
        },
        {
            "Filesystem utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY INDEXES",
        "Copy indexes.",
        {
            "COPY INDEXES TO <target>"
        },
        {
            "COPY INDEXES TO backup"
        },
        {
            "Index utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY MEMO",
        "Copy memo field content.",
        {
            "COPY MEMO <field> TO <file>"
        },
        {
            "COPY MEMO notes TO notes.txt"
        },
        {
            "Memo utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY PROCEDURES",
        "Copy procedures.",
        {
            "COPY PROCEDURES TO <target>"
        },
        {
            "COPY PROCEDURES TO procs.prg"
        },
        {
            "Procedure utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY STRUCTURE",
        "Copy table structure.",
        {
            "COPY STRUCTURE TO <new_table>"
        },
        {
            "COPY STRUCTURE TO empty_students"
        },
        {
            "Schema utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY STRUCTURE EXTENDED",
        "Copy extended structure.",
        {
            "COPY STRUCTURE EXTENDED TO <new_table>"
        },
        {
            "COPY STRUCTURE EXTENDED TO structdef"
        },
        {
            "Schema documentation/metadata command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "COPY TAG",
        "Copy an index tag.",
        {
            "COPY TAG <tag_name> TO <target>"
        },
        {
            "COPY TAG LNAME TO lnamecopy"
        },
        {
            "Index utility command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE CLASS",
        "Create a class.",
        {
            "CREATE CLASS <class_name>"
        },
        {
            "CREATE CLASS Customer"
        },
        {
            "VFP class feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE CLASSLIB",
        "Create a class library.",
        {
            "CREATE CLASSLIB <classlib>"
        },
        {
            "CREATE CLASSLIB app.vcx"
        },
        {
            "VFP class-library feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE COLOR SET",
        "Create a color set.",
        {
            "CREATE COLOR SET <name>"
        },
        {
            "CREATE COLOR SET amber"
        },
        {
            "Legacy color/UI feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE CONNECTION",
        "Create a database connection.",
        {
            "CREATE CONNECTION <name>"
        },
        {
            "CREATE CONNECTION sqlconn"
        },
        {
            "Database connection feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE CURSOR",
        "Create a cursor.",
        {
            "CREATE CURSOR <cursor_name> (<fields>)"
        },
        {
            "CREATE CURSOR temp (id I, name C(20))"
        },
        {
            "Temporary table/cursor command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE DATABASE",
        "Create a database container.",
        {
            "CREATE DATABASE <database_name>"
        },
        {
            "CREATE DATABASE school"
        },
        {
            "VFP database-container command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE FORM",
        "Create a form.",
        {
            "CREATE FORM <form_name>"
        },
        {
            "CREATE FORM customer"
        },
        {
            "IDE/UI command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE FROM",
        "Create table from structure.",
        {
            "CREATE <table> FROM <structure_table>"
        },
        {
            "CREATE students FROM structdef"
        },
        {
            "Schema-driven table creation.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE LABEL",
        "Create a label.",
        {
            "CREATE LABEL <label_name>"
        },
        {
            "CREATE LABEL mailing"
        },
        {
            "Report/label command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE MENU",
        "Create a menu.",
        {
            "CREATE MENU <menu_name>"
        },
        {
            "CREATE MENU main"
        },
        {
            "IDE/UI command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE PROJECT",
        "Create a project.",
        {
            "CREATE PROJECT <project_name>"
        },
        {
            "CREATE PROJECT app"
        },
        {
            "IDE/project command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE QUERY",
        "Create a query.",
        {
            "CREATE QUERY <query_name>"
        },
        {
            "CREATE QUERY active_students"
        },
        {
            "IDE/query command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE REPORT",
        "Create a report.",
        {
            "CREATE REPORT <report_name>"
        },
        {
            "CREATE REPORT invoice"
        },
        {
            "Report command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE SCREEN",
        "Create a screen.",
        {
            "CREATE SCREEN <screen_name>"
        },
        {
            "CREATE SCREEN main"
        },
        {
            "Legacy screen-builder command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE SQL VIEW",
        "Create a SQL view.",
        {
            "CREATE SQL VIEW <view_name> AS <select>"
        },
        {
            "CREATE SQL VIEW v_students AS SELECT * FROM students"
        },
        {
            "Database view command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE TABLE",
        "Create a table.",
        {
            "CREATE TABLE <table_name> (<fields>)"
        },
        {
            "CREATE TABLE students (id I, lname C(20))"
        },
        {
            "Structured table creation form.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE TRIGGER",
        "Create a trigger.",
        {
            "CREATE TRIGGER <trigger_name>"
        },
        {
            "CREATE TRIGGER trg_students"
        },
        {
            "Database trigger command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "CREATE VIEW",
        "Create a view.",
        {
            "CREATE VIEW <view_name>"
        },
        {
            "CREATE VIEW v_students"
        },
        {
            "View command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DEBUG",
        "Start debugger.",
        {
            "DEBUG"
        },
        {
            "DEBUG"
        },
        {
            "Debugger command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DEBUGOUT",
        "Output text to debugger.",
        {
            "DEBUGOUT <expression>"
        },
        {
            "DEBUGOUT \"checkpoint\""
        },
        {
            "Debugger output command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DECLARE",
        "Declare an array or external DLL function.",
        {
            "DECLARE <name>",
            "DECLARE INTEGER <function> IN <dll>"
        },
        {
            "DECLARE INTEGER MessageBox IN user32"
        },
        {
            "Runtime/external declaration command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DEACTIVATE MENU",
        "Deactivate a menu.",
        {
            "DEACTIVATE MENU <menu_name>"
        },
        {
            "DEACTIVATE MENU main"
        },
        {
            "UI/menu command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DEACTIVATE POPUP",
        "Deactivate a popup.",
        {
            "DEACTIVATE POPUP <popup_name>"
        },
        {
            "DEACTIVATE POPUP choices"
        },
        {
            "UI/menu command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DEACTIVATE WINDOW",
        "Deactivate a window.",
        {
            "DEACTIVATE WINDOW <window_name>"
        },
        {
            "DEACTIVATE WINDOW mainwin"
        },
        {
            "UI/window command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DIMENSION",
        "Dimension an array.",
        {
            "DIMENSION <array_name>(<dims>)"
        },
        {
            "DIMENSION aNames(10)"
        },
        {
            "Language/runtime command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY",
        "Display records or system information.",
        {
            "DISPLAY",
            "DISPLAY STRUCTURE",
            "DISPLAY STATUS",
            "DISPLAY MEMORY"
        },
        {
            "DISPLAY",
            "DISPLAY STRUCTURE"
        },
        {
            "Related to LIST but traditionally pauses/forms output differently.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY CONNECTIONS",
        "Display connections.",
        {
            "DISPLAY CONNECTIONS"
        },
        {
            "DISPLAY CONNECTIONS"
        },
        {
            "Database connection status.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY DATABASE",
        "Display database information.",
        {
            "DISPLAY DATABASE"
        },
        {
            "DISPLAY DATABASE"
        },
        {
            "Database metadata display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY DLLS",
        "Display loaded DLLs.",
        {
            "DISPLAY DLLS"
        },
        {
            "DISPLAY DLLS"
        },
        {
            "Runtime status.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY FILES",
        "Display files.",
        {
            "DISPLAY FILES"
        },
        {
            "DISPLAY FILES"
        },
        {
            "Filesystem/status display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY HISTORY",
        "Display command history.",
        {
            "DISPLAY HISTORY"
        },
        {
            "DISPLAY HISTORY"
        },
        {
            "Command history display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY MEMORY",
        "Display memory variables.",
        {
            "DISPLAY MEMORY"
        },
        {
            "DISPLAY MEMORY"
        },
        {
            "Runtime memory display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY OBJECTS",
        "Display objects.",
        {
            "DISPLAY OBJECTS"
        },
        {
            "DISPLAY OBJECTS"
        },
        {
            "VFP object display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY PROCEDURES",
        "Display procedures.",
        {
            "DISPLAY PROCEDURES"
        },
        {
            "DISPLAY PROCEDURES"
        },
        {
            "Procedure display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY STATUS",
        "Display status.",
        {
            "DISPLAY STATUS"
        },
        {
            "DISPLAY STATUS"
        },
        {
            "Runtime status display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY STRUCTURE",
        "Display table structure.",
        {
            "DISPLAY STRUCTURE"
        },
        {
            "DISPLAY STRUCTURE"
        },
        {
            "Table schema display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY TABLES",
        "Display tables.",
        {
            "DISPLAY TABLES"
        },
        {
            "DISPLAY TABLES"
        },
        {
            "Database/table status display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DISPLAY VIEWS",
        "Display views.",
        {
            "DISPLAY VIEWS"
        },
        {
            "DISPLAY VIEWS"
        },
        {
            "Database view display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DO",
        "Execute a procedure or program.",
        {
            "DO <program_or_procedure>"
        },
        {
            "DO myprog"
        },
        {
            "Program execution command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DO CASE",
        "Begin a case statement block.",
        {
            "DO CASE"
        },
        {
            "DO CASE"
        },
        {
            "Language block command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DO FORM",
        "Execute a form.",
        {
            "DO FORM <form_name>"
        },
        {
            "DO FORM customer"
        },
        {
            "VFP UI command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DO WHILE",
        "Begin a while loop.",
        {
            "DO WHILE <condition>"
        },
        {
            "DO WHILE !EOF()"
        },
        {
            "Language block command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DROP TABLE",
        "Drop a table.",
        {
            "DROP TABLE <table_name>"
        },
        {
            "DROP TABLE old_students"
        },
        {
            "SQL/database command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "DROP VIEW",
        "Drop a view.",
        {
            "DROP VIEW <view_name>"
        },
        {
            "DROP VIEW v_students"
        },
        {
            "SQL/database command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "EJECT",
        "Eject a printer page.",
        {
            "EJECT"
        },
        {
            "EJECT"
        },
        {
            "Printer/output command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "EJECT PAGE",
        "Eject a page.",
        {
            "EJECT PAGE"
        },
        {
            "EJECT PAGE"
        },
        {
            "Printer/output command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "END TRANSACTION",
        "End a transaction.",
        {
            "END TRANSACTION"
        },
        {
            "END TRANSACTION"
        },
        {
            "Transaction command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDCASE",
        "End a case block.",
        {
            "ENDCASE"
        },
        {
            "ENDCASE"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDDO",
        "End a DO WHILE block.",
        {
            "ENDDO"
        },
        {
            "ENDDO"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDFOR",
        "End a FOR block.",
        {
            "ENDFOR"
        },
        {
            "ENDFOR"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDFUNC",
        "End a FUNCTION block.",
        {
            "ENDFUNC"
        },
        {
            "ENDFUNC"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDIF",
        "End an IF block.",
        {
            "ENDIF"
        },
        {
            "ENDIF"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDPRINTJOB",
        "End a print job.",
        {
            "ENDPRINTJOB"
        },
        {
            "ENDPRINTJOB"
        },
        {
            "Printer/output command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDPROC",
        "End a PROCEDURE block.",
        {
            "ENDPROC"
        },
        {
            "ENDPROC"
        },
        {
            "Language block terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ENDTEXT",
        "End a textmerge block.",
        {
            "ENDTEXT"
        },
        {
            "ENDTEXT"
        },
        {
            "Textmerge terminator.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ERASE",
        "Erase a file.",
        {
            "ERASE <file>"
        },
        {
            "ERASE old.txt"
        },
        {
            "Filesystem command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "EXECSCRIPT",
        "Execute script text.",
        {
            "EXECSCRIPT(<script>)"
        },
        {
            "EXECSCRIPT(\"? DATE()\")"
        },
        {
            "VFP script execution feature.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "EXIT",
        "Exit a loop or application context.",
        {
            "EXIT"
        },
        {
            "EXIT"
        },
        {
            "Language/control command. DotTalk++ also uses EXIT as a quit synonym.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "EXPORT",
        "Export data.",
        {
            "EXPORT TO <file> [TYPE <type>]"
        },
        {
            "EXPORT TO students.csv"
        },
        {
            "Data export command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "FLUSH",
        "Flush buffers.",
        {
            "FLUSH"
        },
        {
            "FLUSH"
        },
        {
            "Persistence/buffer command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "FOR",
        "Begin a FOR loop.",
        {
            "FOR <var> = <start> TO <end>",
            "FOR ... ENDFOR"
        },
        {
            "FOR i = 1 TO 10"
        },
        {
            "Language block command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "FREE TABLE",
        "Free a table from a database container.",
        {
            "FREE TABLE <table_name>"
        },
        {
            "FREE TABLE students"
        },
        {
            "Database-container command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "FUNCTION",
        "Define a function.",
        {
            "FUNCTION <name>"
        },
        {
            "FUNCTION MyFunc"
        },
        {
            "Language declaration.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "GATHER",
        "Gather values from an array or object into the current record.",
        {
            "GATHER FROM <array_or_object>"
        },
        {
            "GATHER FROM aData"
        },
        {
            "Data transfer command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "HELP",
        "Display help.",
        {
            "HELP",
            "HELP <topic>"
        },
        {
            "HELP",
            "HELP USE"
        },
        {
            "Live DotTalk++ HELP should come from live catalogs; this is historical reference only.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "HIDE MENU",
        "Hide a menu.",
        {
            "HIDE MENU <menu_name>"
        },
        {
            "HIDE MENU main"
        },
        {
            "UI/menu command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "HIDE POPUP",
        "Hide a popup.",
        {
            "HIDE POPUP <popup_name>"
        },
        {
            "HIDE POPUP choices"
        },
        {
            "UI/menu command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "HIDE WINDOW",
        "Hide a window.",
        {
            "HIDE WINDOW <window_name>"
        },
        {
            "HIDE WINDOW mainwin"
        },
        {
            "UI/window command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "IF",
        "Begin an IF block.",
        {
            "IF <condition>",
            "IF ... ENDIF"
        },
        {
            "IF nCount > 0"
        },
        {
            "Language block command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "IMPORT",
        "Import data.",
        {
            "IMPORT FROM <file> [TYPE <type>]"
        },
        {
            "IMPORT FROM students.csv"
        },
        {
            "Data import command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "INSERT",
        "Insert a record or row.",
        {
            "INSERT INTO <table> ..."
        },
        {
            "INSERT INTO students ..."
        },
        {
            "SQL/data command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "JOIN",
        "Join tables.",
        {
            "JOIN WITH <table> TO <new_table> FOR <condition>"
        },
        {
            "JOIN WITH enroll TO stud_enroll FOR students.id = enroll.sid"
        },
        {
            "Historical data operation.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LABEL",
        "Print labels.",
        {
            "LABEL FORM <label>"
        },
        {
            "LABEL FORM mailing"
        },
        {
            "Label/report command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST",
        "List records or system information.",
        {
            "LIST",
            "LIST ALL",
            "LIST FOR <condition>",
            "LIST STRUCTURE"
        },
        {
            "LIST",
            "LIST FOR GPA >= 3.0"
        },
        {
            "Classic table-display command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST CONNECTIONS",
        "List connections.",
        {
            "LIST CONNECTIONS"
        },
        {
            "LIST CONNECTIONS"
        },
        {
            "Database connection status.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST DATABASE",
        "List database info.",
        {
            "LIST DATABASE"
        },
        {
            "LIST DATABASE"
        },
        {
            "Database metadata display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST DLLS",
        "List loaded DLLs.",
        {
            "LIST DLLS"
        },
        {
            "LIST DLLS"
        },
        {
            "Runtime status.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST FILES",
        "List files.",
        {
            "LIST FILES"
        },
        {
            "LIST FILES"
        },
        {
            "File list command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST HISTORY",
        "List command history.",
        {
            "LIST HISTORY"
        },
        {
            "LIST HISTORY"
        },
        {
            "Command history display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST MEMORY",
        "List memory variables.",
        {
            "LIST MEMORY"
        },
        {
            "LIST MEMORY"
        },
        {
            "Runtime memory display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST OBJECTS",
        "List objects.",
        {
            "LIST OBJECTS"
        },
        {
            "LIST OBJECTS"
        },
        {
            "Object display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST PROCEDURES",
        "List procedures.",
        {
            "LIST PROCEDURES"
        },
        {
            "LIST PROCEDURES"
        },
        {
            "Procedure display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST STATUS",
        "List status.",
        {
            "LIST STATUS"
        },
        {
            "LIST STATUS"
        },
        {
            "Runtime status display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST STRUCTURE",
        "List table structure.",
        {
            "LIST STRUCTURE"
        },
        {
            "LIST STRUCTURE"
        },
        {
            "Table schema display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST TABLES",
        "List tables.",
        {
            "LIST TABLES"
        },
        {
            "LIST TABLES"
        },
        {
            "Database/table status display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "LIST VIEWS",
        "List views.",
        {
            "LIST VIEWS"
        },
        {
            "LIST VIEWS"
        },
        {
            "Database view display.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "MODIFY LABEL",
        "Modify a label.",
        {
            "MODIFY LABEL <label_name>"
        },
        {
            "MODIFY LABEL mailing"
        },
        {
            "IDE/report command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "MODIFY REPORT",
        "Modify a report.",
        {
            "MODIFY REPORT <report_name>"
        },
        {
            "MODIFY REPORT invoice"
        },
        {
            "IDE/report command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "QUIT",
        "Quit FoxPro.",
        {
            "QUIT"
        },
        {
            "QUIT"
        },
        {
            "Exit command.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "BYE",
        "Quit command alias used by some command shells.",
        {
            "BYE"
        },
        {
            "BYE"
        },
        {
            "Included as a practical shell alias, not a primary FoxPro standard entry.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    },
    FoxStandardDoc{
        "ORDER",
        "Set or refer to index order in simplified shell syntax.",
        {
            "ORDER <order>",
            "SET ORDER TO <tag>"
        },
        {
            "ORDER 1"
        },
        {
            "The reference C sketch used ORDER as a simplified command; FoxPro usually uses SET ORDER.",
            "Static historical reference entry. Not the live DotTalk++ command contract."
        },
        {},
        {
            "FoxPro 2.x",
            "Visual FoxPro"
        }
    }
    };

    return kDocs;
}

const std::unordered_map<std::string, const FoxStandardDoc*>& index()
{
    static const std::unordered_map<std::string, const FoxStandardDoc*> kIndex = [] {
        std::unordered_map<std::string, const FoxStandardDoc*> map;

        for (const auto& doc : docs()) {
            map.emplace(normalize_key(doc.command), &doc);
        }

        // Common aliases and grouped-command conveniences.
        map.emplace("GO TOP", get("GO"));
        map.emplace("GO BOTTOM", get("GO"));
        map.emplace("GOTO TOP", get("GOTO"));
        map.emplace("GOTO BOTTOM", get("GOTO"));
        map.emplace("APPEND BLANK", get("APPEND"));
        map.emplace("APPEND FROM", get("APPEND"));
        map.emplace("SET ORDER TO", get("SET ORDER"));
        map.emplace("SET RELATION TO", get("SET RELATION"));
        map.emplace("COPY TO", get("COPY"));
        map.emplace("CREATE DBF", get("CREATE"));
        map.emplace("HELP", get("HELP"));
        map.emplace("EXIT", get("EXIT"));
        map.emplace("BYE", get("BYE"));

        return map;
    }();

    return kIndex;
}

} // namespace

const FoxStandardDoc* get(const std::string& command)
{
    const std::string key = normalize_key(command);
    if (key.empty()) {
        return nullptr;
    }

    const auto it = index().find(key);
    if (it != index().end()) {
        return it->second;
    }

    return nullptr;
}

std::vector<std::string> list_topics()
{
    std::vector<std::string> topics;
    topics.reserve(docs().size());

    for (const auto& doc : docs()) {
        topics.push_back(doc.command);
    }

    std::sort(topics.begin(), topics.end());
    return topics;
}

} // namespace dottalk::foxstd
