// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/rel_enum_engine.cpp
#include "rel_enum_engine.hpp"

#include "set_relations.hpp"
#include "xbase.hpp"
#include "workareas.hpp"
#include "xbase_field_getters.hpp"
#include "textio.hpp"
#include "workarea_util.hpp"
#include "cli/command_registry.hpp"

#include <cctype>
#include <cstddef>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <streambuf>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

extern "C" xbase::XBaseEngine* shell_engine();

namespace
{
    static std::string trim(std::string s) { return textio::trim(std::move(s)); }
    static std::string up(std::string s)   { return textio::up(std::move(s)); }

    // AIF-074 P0.2: slot_of_area, ScopedAreaSelect, ScopedEngineArea moved to
    // the shared home in workarea_util.{hpp,cpp}; behavior unchanged.
    using cli::ScopedAreaSelect;
    using cli::ScopedEngineArea;

    class ScopedStdoutCapture {
    public:
        ScopedStdoutCapture() : old_(std::cout.rdbuf(buf_.rdbuf())) {}
        ~ScopedStdoutCapture() { std::cout.rdbuf(old_); }

        std::string str() const { return buf_.str(); }

        ScopedStdoutCapture(const ScopedStdoutCapture&) = delete;
        ScopedStdoutCapture& operator=(const ScopedStdoutCapture&) = delete;

    private:
        std::ostringstream buf_;
        std::streambuf* old_{nullptr};
    };

    // AIF-074 P0.2: find_open_area_by_name_ci and split_tuple_expr_csv moved
    // to the shared home in workarea_util.{hpp,cpp}; behavior unchanged.
    using cli::find_open_area_by_name_ci;
    using cli::split_tuple_expr_csv;

    static bool parse_field_ref(const std::string& term,
                                std::string& area_name_out,
                                std::string& field_name_out)
    {
        std::string t = trim(term);
        if (t.empty()) return false;

        for (char c : t) {
            if (c == '(' || c == ')' || c == '"' || c == '\'' || c == '+' || c == '-' ||
                c == '*' || c == '/' || c == '%' || c == '<' || c == '>' || c == '=' ||
                c == '&' || c == '|' || c == '!') {
                return false;
            }
        }

        const std::size_t dot = t.find('.');
        if (dot == std::string::npos) {
            area_name_out.clear();
            field_name_out = trim(t);
            return !field_name_out.empty();
        }

        area_name_out = trim(t.substr(0, dot));
        field_name_out = trim(t.substr(dot + 1));
        return !area_name_out.empty() && !field_name_out.empty();
    }

    static bool build_distinct_key_from_exprs(const std::vector<std::string>& tuple_exprs,
                                              xbase::DbArea* home_area,
                                              std::string& key_out)
    {
        key_out.clear();
        if (tuple_exprs.empty()) return false;

        bool all_ok = true;
        std::string key;

        for (const auto& term : tuple_exprs) {
            std::string area_name, field_name;
            if (!parse_field_ref(term, area_name, field_name)) {
                all_ok = false;
                break;
            }

            xbase::DbArea* db = nullptr;
            if (!area_name.empty()) db = find_open_area_by_name_ci(area_name);
            if (!db) db = home_area;
            if (!db) { all_ok = false; break; }

            std::string val;
            try {
                ScopedAreaSelect focus(db);
                db->readCurrent();
                val = xfg::getFieldAsString(*db, field_name);
            } catch (...) {
                all_ok = false;
                break;
            }

            if (!key.empty()) key.push_back('\x1f');
            key += trim(val);
        }

        if (!all_ok) return false;
        key_out = std::move(key);
        return true;
    }

    static std::string join_tuple_exprs_csv(const std::vector<std::string>& exprs)
    {
        std::string out;
        for (std::size_t i = 0; i < exprs.size(); ++i) {
            if (i) out += ", ";
            out += exprs[i];
        }
        return out;
    }

    static std::vector<std::string> split_pipe_row(const std::string& line)
    {
        std::vector<std::string> out;
        std::string cur;
        for (char c : line) {
            if (c == '|') {
                out.push_back(trim(cur));
                cur.clear();
            } else {
                cur.push_back(c);
            }
        }
        out.push_back(trim(cur));
        return out;
    }

    static void append_captured_rows(const std::string& captured,
                                     rel_enum_engine::Result& out)
    {
        std::istringstream iss(captured);
        std::string line;
        while (std::getline(iss, line)) {
            line = trim(line);
            if (line.empty()) continue;
            if (up(line) == "OK") continue;

            rel_enum_engine::Row row{};
            row.cells = split_pipe_row(line);
            out.rows.push_back(std::move(row));
        }
    }

    static void fill_counts_for_path(const std::vector<std::string>& path_aliases,
                                     std::vector<rel_enum_engine::Count>& out_counts)
    {
        out_counts.clear();

        // Uses the already-available tree listing to populate per-hop match counts.
        // Long-term note:
        //   cycle/visited safety belongs inside relations_api traversal/listing code,
        //   not here in the browser/enum adapters.
        const auto rows = relations_api::list_tree_for_current_parent(/*recursive=*/true, /*max_depth=*/24);

        std::map<std::string, int> counts_by_alias;

        for (const auto& r : rows) {
            const std::string line = r.line;

            const std::size_t arrow = line.find("->");
            if (arrow == std::string::npos) continue;

            std::size_t p = arrow + 2;
            while (p < line.size() && std::isspace(static_cast<unsigned char>(line[p]))) ++p;

            std::size_t q = p;
            while (q < line.size() && !std::isspace(static_cast<unsigned char>(line[q]))) ++q;

            const std::string alias = trim(line.substr(p, q - p));
            if (alias.empty()) continue;

            const std::string needle = "(matches:";
            const std::size_t m = line.find(needle);
            if (m == std::string::npos) continue;

            std::size_t n = m + needle.size();
            while (n < line.size() && std::isspace(static_cast<unsigned char>(line[n]))) ++n;

            std::size_t e = n;
            while (e < line.size() && std::isdigit(static_cast<unsigned char>(line[e]))) ++e;

            int count = 0;
            try {
                count = std::stoi(line.substr(n, e - n));
            } catch (...) {
                count = 0;
            }

            counts_by_alias[up(alias)] = count;
        }

        out_counts.reserve(path_aliases.size());
        for (const auto& a : path_aliases) {
            rel_enum_engine::Count c{};
            c.alias = a;
            const auto it = counts_by_alias.find(up(a));
            c.count = (it == counts_by_alias.end()) ? 0 : it->second;
            out_counts.push_back(std::move(c));
        }
    }
} // namespace

namespace rel_enum_engine
{
    bool run(xbase::DbArea& area, const Request& req, Result& out)
    {
        out = Result{};

        if (req.tuple_exprs.empty()) {
            out.status = "ERROR";
            out.warnings.push_back("REL ENUM engine: missing tuple expressions.");
            return false;
        }

        // Preserve the older CSV tuple-expression parser. Most callers now pass
        // tuple expressions as a vector, but early REL ENUM / browser glue could
        // hand us one comma-separated expression string. Keep that compatibility
        // here instead of deleting split_tuple_expr_csv().
        std::vector<std::string> tuple_exprs = req.tuple_exprs;
        if (tuple_exprs.size() == 1) {
            std::vector<std::string> parsed = split_tuple_expr_csv(tuple_exprs.front());
            if (!parsed.empty()) {
                tuple_exprs = std::move(parsed);
            }
        }

        xbase::DbArea* home = &area;

        const std::string tuple_csv = join_tuple_exprs_csv(tuple_exprs);
        std::unordered_set<std::string> seen;
        std::size_t emitted = 0;

        {
            ScopedAreaSelect focus(&area);

            const bool ok = relations_api::enum_emit_for_current_parent(
                req.path_aliases,
                req.limit,
                [&]() {
                    ScopedEngineArea keep_area;

                    if (!req.distinct) {
                        ScopedStdoutCapture cap;
                        std::istringstream t(tuple_csv);
                        dli::registry().run(area, "TUPLE", t);
                        append_captured_rows(cap.str(), out);
                        return;
                    }

                    std::string key;
                    const bool have_key = build_distinct_key_from_exprs(tuple_exprs, home, key);
                    if (!have_key) {
                        // Same fallback behavior as existing command:
                        // if DISTINCT key cannot be built, emit anyway.
                        ScopedStdoutCapture cap;
                        std::istringstream t(tuple_csv);
                        dli::registry().run(area, "TUPLE", t);
                        append_captured_rows(cap.str(), out);
                        return;
                    }

                    if (seen.insert(key).second) {
                        ScopedStdoutCapture cap;
                        std::istringstream t(tuple_csv);
                        dli::registry().run(area, "TUPLE", t);
                        append_captured_rows(cap.str(), out);
                    }
                },
                &emitted
            );

            if (!ok) {
                out.status = "ERROR";

                // AIF-078 R-f: this used to say only
                // "enum_emit_for_current_parent failed", which names WHERE the
                // failure happened and never WHY. A correct refusal delivered as
                // an internal function name reads as a crash, and the commonest
                // cause -- an ambiguous chain -- is both recoverable and
                // invisible in that wording.
                //
                // The cause is DERIVED, never guessed. enum_emit_for_current_parent
                // returns false for several reasons; the only one determinable
                // from here is the documented inference rule (set_relations.hpp:121):
                // with no explicit path, a chain is inferred by following the ONLY
                // child at each step, so a parent with any number of children other
                // than one cannot yield a unique chain. When that is demonstrably
                // the case we say so and name the children. When it is not, we say
                // the engine refused and DO NOT invent a reason.
                if (req.path_aliases.empty()) {
                    const std::vector<std::string> kids =
                        relations_api::child_areas_for_current_parent();
                    if (kids.size() != 1) {
                        std::string msg =
                            "REL ENUM: no child path was given and one cannot be "
                            "inferred -- the current parent has ";
                        msg += std::to_string(kids.size());
                        msg += " child relation(s)";
                        if (!kids.empty()) {
                            msg += " (";
                            for (std::size_t i = 0; i < kids.size(); ++i) {
                                if (i) msg += ", ";
                                msg += kids[i];
                            }
                            msg += ")";
                        }
                        msg += ", and inference follows the ONLY child at each step. "
                               "Name the chain explicitly, e.g. REL ENUM <child> "
                               "[<child> ...] TUPLE <expr>.";
                        out.warnings.push_back(msg);
                        return false;
                    }
                }

                out.warnings.push_back(
                    "REL ENUM: the relation enumerator refused this traversal. "
                    "No further cause is determinable here -- check that the "
                    "parent area is selected, that each named child is open, and "
                    "that a relation exists for every hop (REL LIST ALL).");
                return false;
            }

            fill_counts_for_path(req.path_aliases, out.counts);
        }

        if (out.status.empty())
            out.status = out.warnings.empty() ? "OK" : "WARN";

        return true;
    }
}
