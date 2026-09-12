// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_count.cpp
//
// COUNT -- selector-backed, predicate-backed.
// Forms supported:
//   COUNT
//   COUNT FOR <expr>
//   COUNT WHERE <expr>
//   COUNT <expr>          (implicit expression)
//   COUNT DELETED
//   COUNT NOT DELETED
//   COUNT !DELETED
//   COUNT ALL
//   COUNT LIST [<any form above>]        (folded from SQL, 2026-09-04)
//   COUNT VERBOSE [<any form above>]     (folded from SQL, 2026-09-04)
//
// Notes:
//   • Uses cli::scan::collect_selected_recnos(...) for the common scan/selection path.
//   • Keeps the active-tag simple equality fast path local to COUNT.
//   • Preserves cursor cohesion: COUNT must not leave the work area at EOF/last rec.
//   • Suppresses relations auto-refresh during full scans to prevent refresh thrash.
//   • Persistent SET FILTER is part of the logical rowset.
//     Therefore plain COUNT must NOT use raw recCount() when a persistent filter is active.
//   • SET DELETED is part of the logical rowset for exactly the same reason
//     (AIF-123, 2026-08-24). The rule above was written for SET FILTER and was
//     correct; it simply predates the delete rung being wired, and a rule that
//     names one filter does not generalise itself. recCount() is the PHYSICAL
//     count and includes delete-flagged rows, so the shortcut is valid only
//     when nothing at all is narrowing the rowset.

// @dottalk.usage v1
// owner: DOT|COUNT
// command: COUNT
// category: query
// status: supported
// noargs: report
// effect: report
// mutates: cursor transient-relation-refresh-state
// usage-access: COUNT USAGE
// summary:
//   Count records in the current logical rowset using selector-backed and
//   predicate-backed scan paths, preserving cursor cohesion.
//
// usage:
//   COUNT
//   COUNT USAGE
//   COUNT ALL
//   COUNT FOR <expr>
//   COUNT WHERE <expr>
//   COUNT <expr>
//   COUNT DELETED
//   COUNT NOT DELETED
//   COUNT !DELETED
//   COUNT LIST [FOR <expr>]
//   COUNT VERBOSE [FOR <expr>]
//
// notes:
//   COUNT with no arguments counts the current logical rowset.
//   With no open table, COUNT preserves existing behavior and prints 0.
//   Persistent SET FILTER is part of the logical rowset.
//   COUNT FOR and COUNT WHERE normalize the predicate form before scanning.
//   COUNT DELETED and COUNT NOT DELETED select by deletion state.
//   COUNT LIST prints each matching row before the count.
//   COUNT VERBOSE prints every in-scope row with its verdict, then a
//     scanned/matched line, then the count.
//   LIST and VERBOSE are recognized only as the FIRST token after COUNT, so a
//     field of either name needs the explicit form: COUNT FOR LIST = "x".
//   Both suppress the counting fast paths, because those return a number
//     without materializing the rows it came from.
//   COUNT preserves the active cursor where possible after scans.
//   COUNT suppresses relation auto-refresh during full scans to avoid refresh thrash.
//   COUNT is read-only for table data, though it may temporarily move and restore the cursor.
//
// risk:
//   reads_table_records: yes
//   mutates_table_data: no
//   cursor_movement: temporary during scans
//   cursor_restore: best effort
//   relation_refresh_suppression: temporary during scans
//
// related:
//   LOCATE
//   LIST
//   FILTER
//   SET FILTER
//   GOTO
//

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include "cli/settings.hpp"
#include "xbase.hpp"
#include "xbase_field_getters.hpp"      // COUNT LIST/VERBOSE row rendering (folded from SQL)
#include "cli/where_eval_shared.hpp"    // extract_field_names, dt_trim, dt_upcase
#include "cli/scan_selector.hpp"
#include "cli/order_state.hpp"
#include "cli/order_iterator.hpp"
#include "cli/expr/api.hpp"          // compile_where: refuse an unparseable FOR
#include "cli/expr/normalize_where.hpp"
#include "cli/expr/text_compare.hpp"
#include "cli/output_router.hpp"
#include "cli/command_output.hpp"
#include "filters/filter_registry.hpp"
#include "help/helpdata_messages.hpp"
#include "predicate_eval.hpp"

// Provided by src/cli/shell.cpp
extern "C" void shell_rel_refresh_push() noexcept;
extern "C" void shell_rel_refresh_pop() noexcept;

static inline void ltrim_inplace(std::string& s){
    size_t i = 0;
    while (i < s.size() && std::isspace((unsigned char)s[i])) ++i;
    if (i) s.erase(0, i);
}

static inline void rtrim_inplace(std::string& s){
    while (!s.empty() && std::isspace((unsigned char)s.back())) s.pop_back();
}

static inline std::string trim(std::string s){
    rtrim_inplace(s);
    ltrim_inplace(s);
    return s;
}

static inline std::string upcopy(std::string s){
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

static inline bool starts_with_i(const std::string& s, const char* kw){
    const size_t n = std::char_traits<char>::length(kw);
    if (s.size() < n) return false;
    for (size_t i = 0; i < n; ++i){
        if ((char)std::toupper((unsigned char)s[i]) !=
            (char)std::toupper((unsigned char)kw[i])) return false;
    }
    return true;
}

static inline void print_line(const std::string& s)
{
    auto& out = cli::OutputRouter::instance().out();
    out << s << '\n';
}

// Conservative inline comment stripper
static inline std::string strip_inline_comments(std::string s){
    const auto pos_dblamp = s.find("&&");
    const auto pos_slash  = s.find(" //");

    size_t cut = std::string::npos;
    if (pos_dblamp != std::string::npos) cut = pos_dblamp;
    if (pos_slash  != std::string::npos) cut = (cut == std::string::npos ? pos_slash : std::min(cut, pos_slash));

    if (cut != std::string::npos) s.erase(cut);
    return trim(s);
}


static bool is_count_usage_request(std::string raw)
{
    const std::string t = upcopy(trim(std::move(raw)));
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_count_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CountUsageText);
}

enum class CountMode {
    ALLRECS,
    ONLY_DELETED,
    ONLY_NOT_DELETED,
    EXPR
};

struct CountSpec {
    CountMode mode{CountMode::ALLRECS};
    std::string expr;

    // FOLDED IN FROM THE RETIRED `SQL` VERB (owner ruling 2026-09-04).
    //
    // `SQL` offered two things COUNT did not: a LISTING of the matching rows
    // and a VERBOSE per-row trace. Everything else it did, COUNT already did
    // better -- and it did it DIFFERENTLY, which was the actual defect. `SQL`
    // carried a private DelMode enum and a raw `do { } while (skip(+1))` walk
    // that never consulted SET FILTER, so `SQL COUNT FOR <x>` and
    // `COUNT FOR <x>` could return different numbers over the same table with
    // neither reporting that they differed.
    //
    // So the two behaviours move here, onto the ONE selection path that honours
    // the logical rowset. Both are opt-in and neither changes the default
    // output: a bare COUNT still prints exactly one line containing a number.
    bool list{false};      // print the matching rows, then the count
    bool verbose{false};   // print EVERY in-scope row with its verdict, then the count
};

struct CountFastPath {
    bool usable{false};
    std::string field;
    std::string literal;
};

static bool strip_matching_quotes(std::string& s){
    s = trim(std::move(s));
    if (s.size() >= 2) {
        const char a = s.front();
        const char b = s.back();
        if ((a == '"' && b == '"') || (a == '\'' && b == '\'')) {
            s = s.substr(1, s.size() - 2);
            return true;
        }
    }
    return false;
}

static int find_field_index_ci(const xbase::DbArea& area, const std::string& name){
    const auto& defs = area.fields();
    const std::string needle = upcopy(trim(name));

    for (size_t i = 0; i < defs.size(); ++i) {
        if (upcopy(defs[i].name) == needle) {
            return static_cast<int>(i) + 1; // 1-based
        }
    }
    return 0;
}

static bool expression_has_function_call(const std::string& expr){
    // Conservative guard: any parenthesized expression is allowed to pass
    // unchanged to the full predicate evaluator. This prevents COUNT from
    // rewriting function predicates such as SOUNDEX(LNAME)=SOUNDEX("WHITE")
    // or LEFT(LNAME,1)="W" before scan_selector evaluates them.
    return expr.find('(') != std::string::npos &&
           expr.find(')') != std::string::npos;
}

static CountFastPath try_parse_simple_eq_fast_path(const CountSpec& spec){
    CountFastPath fp;
    if (spec.mode != CountMode::EXPR) return fp;

    std::string expr = trim(spec.expr);
    if (expr.empty()) return fp;

    // Reject boolean logic for v1 fast path.
    const std::string up = upcopy(" " + expr + " ");
    if (up.find(" AND ") != std::string::npos ||
        up.find(" OR ")  != std::string::npos ||
        up.find(" NOT ") != std::string::npos) {
        return fp;
    }

    const auto pos = expr.find('=');
    if (pos == std::string::npos) return fp;

    // Reject <=, >=, ==, != in v1.
    if ((pos > 0 && (expr[pos - 1] == '<' || expr[pos - 1] == '>' || expr[pos - 1] == '!' || expr[pos - 1] == '=')) ||
        (pos + 1 < expr.size() && expr[pos + 1] == '=')) {
        return fp;
    }

    std::string lhs = trim(expr.substr(0, pos));
    std::string rhs = trim(expr.substr(pos + 1));
    if (lhs.empty() || rhs.empty()) return fp;

    // Fast path is only for simple FIELD = literal comparisons.
    // Function predicates must remain on the full evaluator path.
    if (expression_has_function_call(lhs) || expression_has_function_call(rhs)) {
        return fp;
    }

    strip_matching_quotes(rhs);

    fp.usable  = true;
    fp.field   = upcopy(lhs);
    fp.literal = rhs;
    return fp;
}

static bool active_tag_matches_field(xbase::DbArea& area, const CountFastPath& fp){
    if (!fp.usable) return false;
    if (!orderstate::hasOrder(area)) return false;

    const std::string tag = upcopy(trim(orderstate::activeTag(area)));
    if (tag.empty() || tag == "(NONE)") return false;

    return tag == fp.field;
}

static uint64_t do_count_fast_eq_active_tag(xbase::DbArea& area,
                                            const CountFastPath& fp)
{
    uint64_t matched = 0;
    std::vector<uint64_t> recnos;
    cli::OrderIterSpec spec{};
    std::string err;

    if (!cli::order_collect_recnos_asc(area, recnos, &spec, &err) || recnos.empty()) {
        return 0;
    }

    const int field_idx = find_field_index_ci(area, fp.field);
    if (field_idx <= 0) {
        return 0;
    }

    const bool case_on = predx::get_case_sensitive();

    for (uint64_t rn : recnos) {
        if (!area.gotoRec((int32_t)rn)) continue;
        if (!area.readCurrent()) continue;

        // Keep fast path logically consistent with COUNT selection semantics.
        // AIF-123: this fast path is only taken when the spec carries no
        // deleted clause (see usable_fast_path, which refuses ONLY_DELETED and
        // ONLY_NOT_DELETED), so SessionDefault is the whole of the policy here
        // and is stated rather than defaulted into silently.
        if (!filter::visible(&area, nullptr,
                             filter::DeletedPolicy::SessionDefault)) continue;

        const std::string val = trim(area.get(field_idx));
        const auto match = dottalk::expr::compare_text_values(val, fp.literal);
        if (dottalk::expr::text_match_is_true(match, case_on)) {
            ++matched;
        }
    }
    return matched;
}

// LIST / VERBOSE ARE ACCEPTED ONLY AS THE LEADING TOKEN, and that is a
// deliberate narrowing of what `SQL` allowed (it took VERBOSE at either end).
// A trailing keyword cannot be stripped safely: `COUNT FOR NAME = "VERBOSE"`
// ends in the word VERBOSE and means nothing of the kind. Leading position is
// unambiguous because it occupies the same slot as the existing ALL / DELETED
// keywords. The cost is that a FIELD named LIST or VERBOSE must be written with
// the explicit form -- `COUNT FOR LIST = "x"` -- which the usage block states.
static bool take_leading_keyword(std::string& tail, const char* kw){
    const std::string up = upcopy(tail);
    const size_t n = std::string(kw).size();
    if (!starts_with_i(up, kw)) return false;
    // Must be the whole tail or followed by a separator, so LISTING is not LIST.
    if (tail.size() > n && !std::isspace(static_cast<unsigned char>(tail[n]))) return false;
    tail = trim(tail.substr(n));
    return true;
}

static CountSpec parse_count_tail(std::string tail_raw){
    CountSpec cs;
    std::string tail = strip_inline_comments(trim(std::move(tail_raw)));

    // Either order, and both may appear; VERBOSE implies the listing work and
    // simply says more about it.
    for (int pass = 0; pass < 2; ++pass) {
        if (take_leading_keyword(tail, "VERBOSE")) cs.verbose = true;
        if (take_leading_keyword(tail, "LIST"))    cs.list    = true;
    }

    const std::string up = upcopy(tail);

    if (up.empty() || up == "ALL"){
        cs.mode = CountMode::ALLRECS;
        return cs;
    }
    if (up == "DELETED"){
        cs.mode = CountMode::ONLY_DELETED;
        return cs;
    }
    if (up == "NOT DELETED" || up == "!DELETED" || up == "! DELETED"){
        cs.mode = CountMode::ONLY_NOT_DELETED;
        return cs;
    }
    if (starts_with_i(up, "FOR ")){
        cs.mode = CountMode::EXPR;
        cs.expr = trim(tail.substr(4));
        return cs;
    }
    if (starts_with_i(up, "WHERE ")){
        cs.mode = CountMode::EXPR;
        cs.expr = trim(tail.substr(6));
        return cs;
    }

    cs.mode = CountMode::EXPR; // implicit expression
    cs.expr = tail;
    return cs;
}

static inline bool count_requires_scan(const CountSpec& spec, bool has_persistent_filter)
{
    if (has_persistent_filter) return true;
    if (spec.mode == CountMode::ONLY_DELETED) return true;
    if (spec.mode == CountMode::ONLY_NOT_DELETED) return true;
    if (spec.mode == CountMode::EXPR && !spec.expr.empty()) return true;
    return false;
}

static cli::scan::SelectionSpec to_selection_spec(const CountSpec& spec)
{
    cli::scan::SelectionSpec ss{};
    ss.scan_mode = cli::scan::ScanMode::All;
    ss.next_n = 0;
    ss.ordered_snapshot = true;

    switch (spec.mode) {
        case CountMode::ONLY_DELETED:
            ss.deleted_mode = cli::scan::DeletedMode::OnlyDeleted;
            break;
        case CountMode::ONLY_NOT_DELETED:
            ss.deleted_mode = cli::scan::DeletedMode::OnlyAlive;
            break;
        case CountMode::ALLRECS:
        case CountMode::EXPR:
        default:
            ss.deleted_mode = cli::scan::DeletedMode::UseDefault;
            break;
    }

    if (spec.mode == CountMode::EXPR && !spec.expr.empty()) {
        ss.use_expr = true;
        ss.expr = spec.expr;
    }

    return ss;
}

// Render one row as `[rec N] FLD="value" (num=x), ... => true`.
//
// The field list is the one the PREDICATE names, not the whole record, which is
// what made `SQL`'s output readable and is the only part of it worth keeping.
// With no predicate there is nothing to name, so the recno stands alone.
static std::string render_row(xbase::DbArea& area,
                              const std::vector<std::string>& fields,
                              bool with_verdict,
                              bool verdict)
{
    std::ostringstream fv;
    fv << "[rec " << area.recno() << "]";
    for (size_t i = 0; i < fields.size(); ++i) {
        fv << (i ? ", " : " ");
        const std::string& fld = fields[i];
        std::string s;
        try { s = where_eval::dt_upcase(where_eval::dt_trim(xfg::getFieldAsString(area, fld))); }
        catch (...) { s = "(ERR)"; }
        fv << fld << "=\"" << s << "\"";
        try {
            const double n = xfg::getFieldAsNumber(area, fld);
            if (std::isfinite(n)) fv << " (num=" << n << ")";
        } catch (...) {}
    }
    if (with_verdict) fv << " => " << (verdict ? "true" : "false");
    return fv.str();
}

// LIST prints the matched rows. VERBOSE prints every row in the LOGICAL ROWSET
// with its verdict -- and it gets that rowset by asking the SAME selector for
// the same spec with the predicate removed, rather than by walking the table
// itself. That is the whole point of the fold: there is one definition of
// "which rows are in scope" and both outputs are derived from it.
static void emit_selected_rows(xbase::DbArea& area,
                               const CountSpec& spec,
                               const cli::scan::SelectionSpec& sel_spec,
                               const cli::scan::SelectionResult& matched)
{
    std::vector<std::string> fields;
    if (spec.mode == CountMode::EXPR && !spec.expr.empty()) {
        fields = where_eval::extract_field_names(spec.expr);
    }

    const auto show = [&](uint64_t rec, bool with_verdict, bool verdict) {
        if (!area.gotoRec(static_cast<int32_t>(rec))) return;
        if (!area.readCurrent()) return;
        print_line(render_row(area, fields, with_verdict, verdict));
    };

    if (!spec.verbose) {
        for (const uint64_t rec : matched.recnos) show(rec, false, true);
        return;
    }

    // VERBOSE: the same spec with the predicate dropped is the in-scope set.
    cli::scan::SelectionSpec scope_spec = sel_spec;
    scope_spec.use_expr = false;
    scope_spec.expr.clear();
    const cli::scan::SelectionResult scope = cli::scan::collect_selected_recnos(area, scope_spec);

    const std::unordered_set<uint64_t> hit(matched.recnos.begin(), matched.recnos.end());
    for (const uint64_t rec : scope.recnos) show(rec, true, hit.count(rec) != 0);

    print_line("scanned " + std::to_string(scope.recnos.size()) +
               ", matched " + std::to_string(matched.recnos.size()));
}

void cmd_COUNT(xbase::DbArea& area, std::istringstream& args)
{
    std::string tail;
    std::getline(args, tail);

    if (is_count_usage_request(tail)) {
        print_count_usage();
        return;
    }

    if (!area.isOpen()){
        print_line("0");
        return;
    }

    CountSpec spec = parse_count_tail(tail);

    if (spec.mode == CountMode::EXPR && !spec.expr.empty()) {
        // Do not rewrite expressions containing function calls. The selector
        // routes these to predx::eval_expr(), and the normalizer can damage
        // predicates such as SOUNDEX(LNAME)=SOUNDEX("WHITE") or LEFT(LNAME,1)="W".
        if (!expression_has_function_call(spec.expr)) {
            spec.expr = normalize_unquoted_rhs_literals(area, spec.expr);
        }

        // AIF-074 ED-01b, applied at the CONSUMER, 2026-08-27.
        //
        // COUNT never asked whether its predicate compiled. It handed the raw
        // text to the scan, every record evaluated false, and it printed `0`.
        // A confident zero. "No rows match" and "I could not evaluate your
        // question" had the same output, and zero is a PLAUSIBLE ANSWER -- R6,
        // absent represented among present, in the most-used counting verb in
        // the shell.
        //
        // Measured 2026-08-27 against WORKSPACES.dbf:
        //     COUNT                        216
        //     COUNT FOR SUPERSEDED =  "1"  195
        //     COUNT FOR SUPERSEDED <> "1"    0   <- twenty-one rows match
        // The three numbers do not reconcile, which is the only reason anyone
        // noticed. Nothing errored.
        //
        // Now the predicate is compiled FIRST and a failure REFUSES. COUNT
        // prints an error and no number, because a number is a claim.
        //
        // Functions are exempt: the selector routes those to predx::eval_expr()
        // and compile_where does not model that grammar, so compiling here
        // would refuse predicates that work. Named rather than silently
        // skipped -- it is a real hole in this guard and it is the reason the
        // check sits inside the no-function-call branch above it.
        if (!expression_has_function_call(spec.expr)) {
            auto cr = dottalk::expr::compile_where(spec.expr);
            if (!cr) {
                print_line("COUNT FOR error: " + cr.error + " - refusing.");
                return;
            }
        }
    }

    const bool has_persistent_filter = filter::has_active_filter(&area);
    const bool will_scan = count_requires_scan(spec, has_persistent_filter) || spec.mode == CountMode::ALLRECS;

    // Bookmark current cursor state.
    const uint64_t saved_recno = static_cast<uint64_t>(area.recno());
    const uint64_t total       = static_cast<uint64_t>(area.recCount());

    if (will_scan) {
        shell_rel_refresh_push();
    }

    uint64_t result = 0;

    // AIF-123. `recCount()` is the PHYSICAL record count -- it includes
    // delete-flagged rows. Taking it when SET DELETED is ON would have walked
    // straight around the rung this lane just restored, and it would have done
    // so on the single most common invocation in the shell: a bare COUNT.
    //
    // This is the same shape as the rule six lines of comment above, one level
    // up: a shortcut that is sound only while NOTHING narrows the rowset. That
    // rule was written when SET FILTER was the only narrowing thing, and it was
    // right then. Adding a second narrowing thing does not update it by itself.
    const bool hides_deleted = cli::Settings::instance().deleted_on.load();

    // BOTH FAST PATHS ARE SKIPPED WHEN ROWS ARE ASKED FOR, and that is not an
    // oversight to optimize away later. `recCount()` and the active-tag counter
    // return a NUMBER and never materialize which records it came from, so
    // there is nothing to print. Reporting rows from one path and the count
    // from another is how the two-implementations defect this change removes
    // got into the tree in the first place: when LIST or VERBOSE is asked for,
    // the printed rows and the printed number come from the SAME selection.
    const bool wants_rows = (spec.list || spec.verbose);

    if (!wants_rows && spec.mode == CountMode::ALLRECS && !has_persistent_filter && !hides_deleted) {
        // True fast-path: no persistent SET FILTER and SET DELETED OFF, so the
        // logical rowset really is every physical record.
        result = static_cast<uint64_t>(area.recCount());
    } else {
        // Keep COUNT's local optimization.
        const CountFastPath fp = try_parse_simple_eq_fast_path(spec);
        if (!wants_rows && active_tag_matches_field(area, fp)) {
            result = do_count_fast_eq_active_tag(area, fp);
        } else {
            const cli::scan::SelectionSpec sel_spec = to_selection_spec(spec);
            const cli::scan::SelectionResult sel = cli::scan::collect_selected_recnos(area, sel_spec);
            result = static_cast<uint64_t>(sel.recnos.size());

            if (wants_rows) {
                emit_selected_rows(area, spec, sel_spec, sel);
            }
        }
    }

    if (will_scan) {
        shell_rel_refresh_pop();

        if (saved_recno >= 1 && saved_recno <= total) {
            (void)area.gotoRec((int32_t)saved_recno);
            (void)area.readCurrent();
        }
    }

    print_line(std::to_string(result));
}
