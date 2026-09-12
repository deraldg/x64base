// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: the reserved `SQL` verb name
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// src/cli/cmd_sql.cpp
// SQL -- RESERVED NAME. Retired as a scanner by owner ruling, 2026-09-04.
//
// WHAT THIS COMMAND USED TO BE, and why that ended. `SQL` was a predicate
// scanner over the current work area: `SQL [COUNT] [ALL|DELETED] [FOR <expr>]
// [VERBOSE]`. It was never a statement executor -- the name was historical --
// and it already carried a guard redirecting `SQL SELECT ...` to SQLSEL.
//
// THE NAME WAS NOT THE PROBLEM. The problem was that COUNT already did all of
// it, and the two DISAGREED. `cmd_count.cpp` treats persistent SET FILTER and
// SET DELETED as part of the LOGICAL ROWSET (AIF-123, 2026-08-24) and selects
// through `cli::scan::collect_selected_recnos`, the shared path cmd_delete and
// cmd_recall also use. This file did none of that: it declared a PRIVATE
// DelMode enum with its own deleted-flag policy and walked the table with a raw
// `do { ... } while (A.skip(+1) && A.readCurrent())`. The string FILTER did not
// appear in it. So `SQL COUNT FOR <x>` and `COUNT FOR <x>` could return
// DIFFERENT NUMBERS over the same table, and neither said so -- a second,
// weaker declaration of which rows are in scope, which is the defect shape this
// house records elsewhere for field-name normalizers.
//
// WHAT MOVED, AND WHERE. The two behaviours COUNT lacked are now COUNT's, built
// on the shared selector rather than on a private walk:
//     SQL LNAME = "SMITH"                 ->  COUNT LIST FOR LNAME = "SMITH"
//     SQL VERBOSE COUNT FOR GPA >= 3.0    ->  COUNT VERBOSE FOR GPA >= 3.0
//
// STILL OPEN, AND STATED HERE SO IT IS NOT FOUND BY SURPRISE: this retirement
// closes ONE of TWO copies. `cmd_sql_select.cpp` carries the same compat scan
// form for `SQLSEL COUNT FOR <expr>`, with its own DelMode at :144 and its own
// raw walk at :572-613, and it consults the shared selector zero times. That
// twin is untouched here because SQLSEL is a `supported` surface and removing
// part of it is a separate owner ruling.
//
// THE NAME IS RESERVED, NOT DELETED. It stays registered so that `SQL ...`
// answers with direction instead of "unknown command", and so the name remains
// available for a real SQL surface later. That is the owner's stated intent.

// @dottalk.usage v1
// owner: DOT|SQL
// command: SQL
// category: sql
// status: reserved
// noargs: report
// effect: report
// mutates: nothing
// usage-access: SQL USAGE
// summary:
//   Reserved verb. Reports where the scanning and statement surfaces now live.
//
// usage:
//   SQL
//   SQL USAGE
//
// examples:
//   SQL
//   SQL USAGE
//
// notes:
//   SQL no longer scans records and never requires an open table.
//   Retired as a scanner 2026-09-04; its LIST and VERBOSE behaviour moved to
//     COUNT, onto the shared selection path that honours SET FILTER and
//     SET DELETED. The retired form could disagree with COUNT and did not say so.
//   Family boundary, stated because the three names invite confusion:
//     SQL     -- reserved (this command)
//     SQLSEL  -- SQLsel, the SELECT statement surface
//     SQLITE  -- the SQLite bridge, for an actual SQLite database
//   Any argument is accepted and answered with the same guidance, so a script
//     carrying an old `SQL COUNT FOR ...` line gets a correction, not silence.
//
// risk:
//   requires_open_table: no
//   scans_records: no
//   mutates_cursor: no
//   mutates_table_data: no
//
// related:
//   COUNT
//   SQLSEL
//   SQLITE

#include "shell_commands.hpp"

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"

namespace {

// ONE MESSAGE FOR EVERY INVOCATION, deliberately. A reserved verb that answered
// `SQL` and `SQL COUNT FOR GPA >= 3.0` differently would be re-growing a
// grammar, and the whole point of the retirement is that this name no longer
// has one. The old forms are named in the mapping so a stale script or a stale
// habit gets corrected rather than merely refused.
void print_sql_reserved()
{
    std::cout
        << "SQL: reserved verb -- it no longer scans records.\n"
        << "\n"
        << "  Predicate scans and counts are COUNT's, on the one selection path\n"
        << "  that honours SET FILTER and SET DELETED:\n"
        << "    COUNT                          count the current logical rowset\n"
        << "    COUNT FOR <expr>               count matches\n"
        << "    COUNT LIST FOR <expr>          list the matching rows, then the count\n"
        << "    COUNT VERBOSE FOR <expr>       every in-scope row with its verdict\n"
        << "    COUNT DELETED | NOT DELETED    select by deletion state\n"
        << "\n"
        << "  Statements are SQLSEL:  SQLSEL <cols> FROM <table> [WHERE] [ORDER BY] [LIMIT]\n"
        << "  An actual SQLite database is SQLITE:  SQLITE USAGE\n"
        << "\n"
        << "  Retired 2026-09-04: the old SQL scanner kept its own idea of which\n"
        << "  rows were in scope and could disagree with COUNT without saying so.\n";
}

} // namespace

// The signature is unchanged and the verb stays in the registry, so `SQL`
// remains discoverable and answerable rather than becoming an unknown command.
// The area is untouched: this command opens nothing, moves no cursor, and reads
// no record.
void cmd_SQL(xbase::DbArea& /*A*/, std::istringstream& /*iss*/) {
    print_sql_reserved();
}
