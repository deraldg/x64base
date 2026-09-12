// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_sql_select.cpp
// @dottalk.usage v1
// owner: DOT|SQLSEL
// command: SQLSEL
// category: sql
// status: supported
// noargs: corrective-error
// effect: query
// mutates: cursor-temporary
// usage-access: SQLSEL USAGE
// summary:
//   Typed set-oriented SELECT and DML over open x64base work areas.
//
// usage:
//   SQLSEL USAGE
//   SQLSEL [SELECT] [DISTINCT] <list> FROM <source> [WHERE <predicate>]
//          [GROUP BY <list>] [HAVING <predicate>]
//          [ORDER BY <item>[,<item>...]] [LIMIT <n>]
//   SQLSEL <select> UNION [ALL] <select> | <select> INTERSECT <select> | <select> EXCEPT <select>
//   SQLSEL INSERT INTO <table> (<fields>) VALUES (<values>)[,(<values>)...]
//   SQLSEL UPDATE <table> [[AS] <alias>] SET <field>=<expr>[,...] WHERE <predicate>
//   SQLSEL DELETE FROM <table> [[AS] <alias>] WHERE <predicate>
//
// examples:
//   SQLSEL SID,LNAME,FNAME FROM STUDENTS
//   SQLSEL * FROM STUDENTS LIMIT 5
//   SQLSEL SID,LNAME FROM STUDENTS WHERE MAJOR = "CSCI"
//   SQLSEL SID,LNAME FROM STUDENTS ORDER BY LNAME DESC LIMIT 10
//   SQLSEL COUNT(*) FROM STUDENTS WHERE GPA >= 3.0
//   SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID
//   SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S LEFT JOIN ENROLL E ON S.SID = E.SID
//   SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S RIGHT JOIN ENROLL E ON S.SID = E.SID
//   SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S FULL JOIN ENROLL E ON S.SID = E.SID
//   SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S CROSS JOIN ENROLL E
//   SQLSEL DEPT,COUNT(*),AVG(SALARY) FROM STAFF GROUP BY DEPT
//   SQLSEL SID FROM STUDENTS UNION SELECT SID FROM ALUMNI
//   SQLSEL SID FROM STUDENTS S WHERE EXISTS (SELECT SID FROM ENROLL E WHERE E.SID=S.SID)
//   SQLSEL INSERT INTO STUDENTS (SID,LNAME) VALUES (9,'SMITH')
//   SQLSEL UPDATE STUDENTS SET LNAME=UPPER(LNAME) WHERE SID=9
//   SQLSEL DELETE FROM STUDENTS WHERE SID=9
//
// notes:
//   SQLSEL USAGE prints usage before open-table checks.
//   SQLSEL is the select verb; a leading SELECT keyword remains optional.
//   A statement names open tables inside the current workspace. SELECT restores
//   the current area and source cursors and ignores SET FILTER/SET RELATION.
//   SELECT reads committed data. DML in one explicit transaction reads its own
//   buffered writes; SELECT during that transaction remains a committed view.
//   All JOIN forms are statement-scoped ad-hoc set matching. They do not
//   consult a declared relation; every run reports its fence and access path.
//   Outer joins render produced-absent cells as <UNMATCHED> and report their
//   extension counts. WHERE uses SQL three-valued logic for that absence.
//   CROSS JOIN takes no ON clause. Multi-join chains support INNER/LEFT/CROSS;
//   RIGHT/FULL remain two-table forms.
//   Projection uses the typed TupleRow expression engine. Aggregates are
//   COUNT/SUM/AVG/MIN/MAX; numeric blanks are skipped and reported.
//   Set operands require equal arity and compatible tuple types.
//   LIMIT reports how many rows remain rather than truncating silently.
//   DML reuses APPEND/REPLACE/DELETE semantics through TableBuffer + TBJ1 WAL.
//   Explicit BEGIN/COMMIT/ROLLBACK requires SET MODE SQL and is atomic for one
//   target table only. NULL and memo-field DML refuse; DBF blanks remain values.
//   The legacy predicate form was RETIRED 2026-09-09 (AIF-074, owner ruling).
//     COUNT carries that job -- COUNT FOR <expr>, COUNT LIST, COUNT VERBOSE --
//     and honours SET FILTER and SET DELETED as the logical rowset.
//
// risk:
//   requires_open_table: no; a statement names tables already open in the workspace
//   scans_records: yes
//   mutates_cursor: temporary
//   mutates_table_data: DML only
//
// related:
//   SQL
//   WHERE
//
#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "record_view.hpp"
#include "textio.hpp"
// #include "predicate_eval.hpp" // reserved

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include "cli/expr/api.hpp"
#include "cli/expr/for_parser.hpp"

// ---------- helpers: trim + uppercase ----------
static inline std::string dt_trim(std::string s) {
    auto sp = [](unsigned char c){ return c==' '||c=='\t'||c=='\r'||c=='\n'; };
    while (!s.empty() && sp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && sp((unsigned char)s.back()))  s.pop_back();
    return s;
}
static inline std::string dt_upcase(std::string s) {
    for (auto &ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}
static inline bool ieq(std::string a, std::string b) {
    return dt_upcase(dt_trim(std::move(a))) == dt_upcase(dt_trim(std::move(b)));
}

// Map getters for DotTalk glue (case-insensitive string compares)
#define DOTTALK_GET_FIELD_STR(area, name)  dt_upcase(dt_trim(xfg::getFieldAsString(area, name)))
#define DOTTALK_GET_FIELD_NUM(area, name)  xfg::getFieldAsNumber(area, name)
#include "cli/expr/glue_xbase.hpp"

// SQL normalizer
#include "expr/sql_normalize.hpp"
#include "sqlsel_statement.hpp"   // AIF-074 P3: SELECT ... FROM statement surface

// AIF-074, owner ruling 2026-09-09: the legacy predicate machinery that stood
// here is gone with the form it served -- DelMode, Opts/parse_opts,
// extract_field_names, the STok tokenizer, parse_simple_chain, eval_clause and
// eval_chain, plus the compile_where declaration they alone used. Every one was
// referenced only from the retired path; the census is in the finding.

static void print_sqlsel_usage_contract()
{
    // AIF-074 P3: the statement grammar has exactly ONE runtime description,
    // owned by sqlsel_statement.cpp. Do not restate it here -- a second copy is
    // how help text drifts from code (this file grew three copies once; the
    // regression caught it twice in one day).
    sqlsel::print_statement_usage();
    std::cout
        << "Notes:\n"
        << "  - SQLSEL USAGE does not require an open table.\n"
        << "  - Statement SELECT restores the current area and source cursors.\n"
        << "  - INSERT, UPDATE, and DELETE use typed TableBuffer + WAL writes.\n"
        << "  - The legacy predicate form was retired (AIF-074). COUNT carries that\n"
        << "    job: COUNT FOR <expr>, COUNT LIST, COUNT VERBOSE.\n";
}

static bool sqlsel_usage_contract(std::string tok)
{
    std::transform(tok.begin(), tok.end(), tok.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return tok == "USAGE" || tok == "HELP" || tok == "?";
}
void cmd_SQL_SELECT(xbase::DbArea& A, std::istringstream& iss) {
    // SQLSEL_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = iss.tellg();
        std::string usage_tok;
        if (iss >> usage_tok) {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }

            if (sqlsel_usage_contract(usage_tok)) {
                print_sqlsel_usage_contract();
                return;
            }
        } else {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }
        }
    }

    // AIF-074 P3: statement path, and since 2026-09-09 the ONLY path. A
    // statement names its own table in FROM and does not require (or disturb) a
    // current area. Dispatch by keyword, never by guess -- anything that is not
    // statement-shaped now gets a corrective error rather than a second engine.
    {
        const std::streampos stmt_pos = iss.tellg();
        std::string stmt_tail;
        {
            std::ostringstream rest;
            rest << iss.rdbuf();
            stmt_tail = rest.str();
        }
        iss.clear();
        if (stmt_pos != std::streampos(-1)) iss.seekg(stmt_pos);
        if (sqlsel::try_execute_statement(stmt_tail)) return;
        iss.clear();
        if (stmt_pos != std::streampos(-1)) iss.seekg(stmt_pos);
    }

    // AIF-074, OWNER RULING 2026-09-09: THE LEGACY PREDICATE FORM IS RETIRED.
    //
    // What stood here was a second, weaker, divergent declaration of WHICH ROWS
    // ARE IN SCOPE: a private DelMode that ignored SET DELETED, and a raw walk
    // that used none of cli::scan::collect_selected_recnos -- the shared
    // selector COUNT, DELETE and RECALL all go through, and which treats
    // SET FILTER and SET DELETED as the logical rowset (AIF-123).
    //
    // That is the same ground the bare SQL verb was retired on 2026-09-04
    // ("fold verbose and listing into count and reserve SQL command name for
    // other use"). Here it was worse: the two implementations were not two
    // commands but ONE VERB answering differently depending on whether the text
    // happened to parse as a statement, with nothing telling the caller which
    // branch had run. It was also the half of SQLSEL that broke the cursor
    // neutrality the statement path guarantees -- its own usage block said so --
    // and no spec in the tree exercised it.
    (void)A;
    std::cout
        << "SQLSEL: that is not a statement, and the legacy predicate form has been retired.\n"
        << "  SQLSEL is the statement verb: SQLSEL <list> FROM <table> [WHERE ...].\n"
        << "  For a predicate scan over the current work area use COUNT, which carries\n"
        << "  the listing and verbose forms: COUNT FOR <expr>, COUNT LIST, COUNT VERBOSE.\n"
        << "  COUNT honours SET FILTER and SET DELETED as the logical rowset; this form\n"
        << "  did not, which is why it is gone.\n";
}
