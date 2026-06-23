// src/cli/cmd_relations.cpp
// @dottalk.usage v1
// owner: DOT|RELATIONS
// command: RELATIONS
// category: relation
// status: supported
// noargs: report
// effect: mixed
// mutates: relation-graph
// usage-access: RELATIONS USAGE
// summary:
//   Inspect and manage active relation definitions, relation files, and relation
//   enumeration helpers.
//
// usage:
//   RELATIONS
//   RELATIONS USAGE
//   RELATIONS ALL
//   SET RELATIONS
//   SET RELATIONS USAGE
//   SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]
//   SET RELATIONS CLEAR <parent|ALL>
//
// examples:
//   RELATIONS
//   RELATIONS ALL
//   SET RELATIONS ADD STUDENTS ENROLL ON SID
//   SET RELATIONS CLEAR ALL
//
// notes:
//   RELATIONS USAGE prints usage and does not inspect or mutate relation state.
//   SET RELATIONS USAGE prints usage and does not mutate the relation graph.
//   SET RELATIONS ADD/CLEAR mutate relation definitions.
//   RELATIONS ALL reports a recursive tree rooted at the current parent.
//
// risk:
//   mutates_relation_graph: SET RELATIONS ADD/CLEAR, REL_REFRESH
//   reads_workspace_state: RELATIONS/RELATIONS ALL
//   mutates_table_data: no
//
// related:
//   RBROWSE
//   TUPLE
//   WORKSPACE
//

#include "cmd_relations.hpp"

#include "set_relations.hpp"
#include "rel_enum_engine.hpp"
#include "xbase.hpp"
#include "workareas.hpp"
#include "xbase_field_getters.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"

#include <cctype>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#ifdef _WIN32
#include <direct.h>
#endif

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static std::string trim(std::string s) { return textio::trim(std::move(s)); }
static std::string up(std::string s) { return textio::up(std::move(s)); }

static std::vector<std::string> split_fields_csv(const std::string& csv) {
    std::vector<std::string> out;
    std::string tok;
    for (char c : csv) {
        if (c == ',') {
            tok = trim(tok);
            if (!tok.empty()) out.push_back(tok);
            tok.clear();
        } else {
            tok.push_back(c);
        }
    }
    tok = trim(tok);
    if (!tok.empty()) out.push_back(tok);
    return out;
}

static bool split_on_to_clause(const std::string& tail,
                               std::string& parent_csv,
                               std::string& child_csv) {
    parent_csv.clear();
    child_csv.clear();

    std::istringstream ss(tail);
    std::vector<std::string> before;
    std::vector<std::string> after;
    bool saw_to = false;
    std::string tok;
    while (ss >> tok) {
        if (up(tok) == "TO") {
            if (saw_to) return false;
            saw_to = true;
            continue;
        }
        if (saw_to) after.push_back(tok);
        else before.push_back(tok);
    }

    auto join_tokens = [](const std::vector<std::string>& parts) {
        std::string out;
        for (std::size_t i = 0; i < parts.size(); ++i) {
            if (i) out += " ";
            out += parts[i];
        }
        return trim(std::move(out));
    };

    parent_csv = join_tokens(before);
    child_csv = saw_to ? join_tokens(after) : parent_csv;
    return !parent_csv.empty() && !child_csv.empty();
}

static int slot_of_area(xbase::DbArea* area) {
    if (!area) return -1;
    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        if (workareas::db(i) == area) return static_cast<int>(i);
    }
    return -1;
}

class ScopedAreaSelect {
public:
    explicit ScopedAreaSelect(xbase::DbArea* area) noexcept {
        eng_ = shell_engine();
        if (!eng_ || !area) return;

        const int slot = slot_of_area(area);
        if (slot < 0) return;

        try {
            prev_ = eng_->currentArea();
            if (prev_ != slot) {
                eng_->selectArea(slot);
                active_ = true;
            }
        } catch (...) { active_ = false; }
    }

    ~ScopedAreaSelect() noexcept {
        if (!active_ || !eng_) return;
        try { eng_->selectArea(prev_); } catch (...) {}
    }

    ScopedAreaSelect(const ScopedAreaSelect&) = delete;
    ScopedAreaSelect& operator=(const ScopedAreaSelect&) = delete;

private:
    xbase::XBaseEngine* eng_{nullptr};
    int prev_{-1};
    bool active_{false};
};

class ScopedEngineArea {
public:
    ScopedEngineArea() noexcept {
        eng_ = shell_engine();
        if (!eng_) return;
        try {
            prev_ = eng_->currentArea();
            active_ = true;
        } catch (...) { active_ = false; }
    }

    ~ScopedEngineArea() noexcept {
        if (!active_ || !eng_) return;
        try { eng_->selectArea(prev_); } catch (...) {}
    }

    ScopedEngineArea(const ScopedEngineArea&) = delete;
    ScopedEngineArea& operator=(const ScopedEngineArea&) = delete;

private:
    xbase::XBaseEngine* eng_{nullptr};
    int prev_{-1};
    bool active_{false};
};

static xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name) {
    const std::string target = up(trim(logical_or_name));
    if (target.empty()) return nullptr;

    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        xbase::DbArea* a = workareas::db(i);
        if (!a) continue;

        bool open = false;
        try { open = a->isOpen(); } catch (...) { open = false; }
        if (!open) continue;

        try {
            const std::string ln = a->logicalName();
            if (!ln.empty() && up(ln) == target) return a;
            const std::string nm = a->name();
            if (!nm.empty() && up(nm) == target) return a;
        } catch (...) {}
    }
    return nullptr;
}

static std::vector<std::string> split_tuple_expr_csv(const std::string& s) {
    std::vector<std::string> out;
    std::string cur;
    int paren_depth = 0;
    bool in_quote = false;

    for (std::size_t i = 0; i < s.size(); ++i) {
        const char c = s[i];

        if (c == '"' && (i == 0 || s[i - 1] != '\\')) {
            in_quote = !in_quote;
            cur.push_back(c);
            continue;
        }
        if (!in_quote) {
            if (c == '(') { ++paren_depth; cur.push_back(c); continue; }
            if (c == ')' && paren_depth > 0) { --paren_depth; cur.push_back(c); continue; }
            if (c == ',' && paren_depth == 0) {
                std::string t = trim(cur);
                if (!t.empty()) out.push_back(std::move(t));
                cur.clear();
                continue;
            }
        }

        cur.push_back(c);
    }

    std::string t = trim(cur);
    if (!t.empty()) out.push_back(std::move(t));
    return out;
}

static bool parse_field_ref(const std::string& term,
                            std::string& area_name_out,
                            std::string& field_name_out) {
    std::string t = trim(term);
    if (t.empty()) return false;

    for (char c : t) {
        if (c == '(' || c == ')' || c == '"' || c == '\'' || c == '+' || c == '-' ||
            c == '*' || c == '/' || c == '%' || c == '<' || c == '>' || c == '=' ||
            c == '&' || c == '|' || c == '!' ) {
            return false;
        }
    }

    std::size_t dot = t.find('.');
    if (dot == std::string::npos) {
        area_name_out.clear();
        field_name_out = trim(t);
        return !field_name_out.empty();
    }

    area_name_out = trim(t.substr(0, dot));
    field_name_out = trim(t.substr(dot + 1));
    return !area_name_out.empty() && !field_name_out.empty();
}

static bool build_distinct_key_from_fields(const std::string& tuple_expr,
                                          xbase::DbArea* home_area,
                                          std::string& key_out) {
    key_out.clear();
    const auto terms = split_tuple_expr_csv(tuple_expr);
    if (terms.empty()) return false;

    bool all_ok = true;
    std::string key;

    for (const auto& term : terms) {
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

static std::string escape_json(std::string s) {
    std::string out;
    out.reserve(s.size() + 16);
    for (char c : s) {
        switch (c) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out.push_back(c); break;
        }
    }
    return out;
}

static std::string default_relations_path() { return ".relations/relations.json"; }
static std::string dataset_relations_path(const std::string& dataset) { return ".relations/" + dataset + ".json"; }

static bool ensure_dir_for(const std::string& path) {
    std::string dir = path;
    for (std::size_t i = dir.size(); i-- > 0;) {
        if (dir[i] == '/' || dir[i] == '\\') { dir.resize(i); break; }
    }
    if (dir.empty()) return true;

#ifdef _WIN32
    std::wstring wdir(dir.begin(), dir.end());
    _wmkdir(wdir.c_str());
#else
    ::system((std::string("mkdir -p \"") + dir + "\"").c_str());
#endif
    return true;
}

static std::string read_entire_file(const std::string& path) {
    std::ifstream ifs(path, std::ios::binary);
    if (!ifs) return {};
    std::ostringstream buf;
    buf << ifs.rdbuf();
    return buf.str();
}

static bool write_entire_file(const std::string& path, const std::string& data) {
    if (!ensure_dir_for(path)) return false;
    std::ofstream ofs(path, std::ios::binary | std::ios::trunc);
    if (!ofs) return false;
    ofs.write(data.data(), static_cast<std::streamsize>(data.size()));
    return true;
}

static std::vector<relations_api::RelationSpec> parse_relations_file(const std::string& content) {
    std::vector<relations_api::RelationSpec> specs;
    std::size_t pos = 0;

    auto skip_ws = [&]{
        while (pos < content.size() && std::isspace(static_cast<unsigned char>(content[pos]))) ++pos;
    };

    auto consume = [&](char ch) -> bool {
        skip_ws();
        if (pos < content.size() && content[pos] == ch) { ++pos; return true; }
        return false;
    };

    auto parse_string = [&]() -> std::string {
        skip_ws();
        if (pos >= content.size() || content[pos] != '"') return {};
        ++pos;
        std::string out;
        while (pos < content.size()) {
            char c = content[pos++];
            if (c == '"') break;
            if (c == '\\' && pos < content.size()) {
                const char n = content[pos++];
                switch (n) {
                    case 'n': out.push_back('\n'); break;
                    case 't': out.push_back('\t'); break;
                    case 'r': out.push_back('\r'); break;
                    case '\\': out.push_back('\\'); break;
                    case '"': out.push_back('"'); break;
                    default: out.push_back(n); break;
                }
                continue;
            }
            out.push_back(c);
        }
        return out;
    };

    auto parse_string_array = [&]() -> std::vector<std::string> {
        std::vector<std::string> out;
        if (!consume('[')) return out;
        for (;;) {
            skip_ws();
            if (consume(']')) break;
            const std::string s = parse_string();
            if (!s.empty()) out.push_back(s);
            skip_ws();
            if (consume(']')) break;
            consume(',');
        }
        return out;
    };

    skip_ws();
    if (!consume('[')) return specs;

    for (;;) {
        skip_ws();
        if (consume(']')) break;
        if (!consume('{')) break;

        relations_api::RelationSpec rs;

        for (;;) {
            skip_ws();
            if (consume('}')) break;

            const std::string key = parse_string();
            if (key.empty()) break;
            if (!consume(':')) break;

            if (key == "parent") rs.parent = parse_string();
            else if (key == "child") rs.child = parse_string();
            else if (key == "fields") rs.fields = parse_string_array();
            else if (key == "parent_fields") rs.parent_fields = parse_string_array();
            else if (key == "child_fields") rs.child_fields = parse_string_array();
            else {
                skip_ws();
                if (pos < content.size() && content[pos] == '"') (void)parse_string();
                else if (pos < content.size() && content[pos] == '[') (void)parse_string_array();
            }

            skip_ws();
            if (consume('}')) break;
            consume(',');
        }

        const bool has_legacy_fields = !rs.fields.empty();
        const bool has_asymmetric_fields = !rs.parent_fields.empty() && !rs.child_fields.empty();
        if (!rs.parent.empty() && !rs.child.empty() && (has_legacy_fields || has_asymmetric_fields)) {
            specs.push_back(std::move(rs));
        }

        skip_ws();
        if (consume(']')) break;
        consume(',');
    }

    return specs;
}

static void show_set_relations_usage() {
    std::cout
        << "Usage:\n"
        << "  SET RELATIONS\n"
        << "  SET RELATIONS USAGE\n"
        << "  SET RELATIONS ADD <parent> <child> ON f1[,f2...]\n"
        << "  SET RELATIONS ADD <parent> <child> ON parent_f1[,parent_f2...] TO child_f1[,child_f2...]\n"
        << "  SET RELATIONS CLEAR <parent>\n"
        << "  SET RELATIONS CLEAR ALL\n"
        << "Examples:\n"
        << "  SET RELATIONS ADD STUDENTS ENROLL ON SID\n"
        << "  SET RELATIONS CLEAR STUDENTS\n"
        << "  SET RELATIONS CLEAR ALL\n";
}


static void show_relations_usage() {
    std::cout
        << "Usage:\n"
        << "  RELATIONS\n"
        << "  RELATIONS USAGE\n"
        << "  RELATIONS ALL\n"
        << "  SET RELATIONS\n"
        << "  SET RELATIONS USAGE\n"
        << "  SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]\n"
        << "  SET RELATIONS CLEAR <parent|ALL>\n"
        << "Examples:\n"
        << "  RELATIONS\n"
        << "  RELATIONS ALL\n"
        << "  SET RELATIONS ADD STUDENTS ENROLL ON SID\n"
        << "  SET RELATIONS CLEAR ALL\n"
        << "Notes:\n"
        << "  - RELATIONS USAGE does not inspect or mutate relation state.\n"
        << "  - SET RELATIONS USAGE does not mutate relation definitions.\n";
}

static void show_relations_file_usage() {
    std::cout <<
        "REL SAVE/LOAD syntax\n"
        "  REL SAVE [<file>|DEFAULT|DATASET <name>]\n"
        "  REL LOAD [<file>|DEFAULT|DATASET <name>]\n";
}

static std::string join_row_for_display(const rel_enum_engine::Row& row)
{
    std::string out;
    for (std::size_t i = 0; i < row.cells.size(); ++i) {
        if (i) out += " | ";
        out += row.cells[i];
    }
    return out;
}

} // namespace

void cmd_SET_RELATIONS(xbase::DbArea& /*A*/, std::istringstream& iss) {
    std::string rest;
    std::getline(iss, rest);
    rest = trim(rest);

    if (rest.empty()) {
        show_set_relations_usage();
        return;
    }

    std::istringstream ss(rest);
    std::string op;
    ss >> op;
    op = up(op);

    if (op == "USAGE" || op == "HELP" || op == "?") {
        show_set_relations_usage();
        return;
    }

    if (op == "ADD") {
        std::string parent, child;
        ss >> parent >> child;

        std::string on_kw;
        ss >> on_kw;
        if (up(on_kw) != "ON") {
            std::cout << "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2\n";
            return;
        }

        std::string fields_tail;
        std::getline(ss, fields_tail);
        fields_tail = trim(fields_tail);

        std::string parent_csv;
        std::string child_csv;
        if (parent.empty() || child.empty() || fields_tail.empty() ||
            !split_on_to_clause(fields_tail, parent_csv, child_csv)) {
            std::cout << "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2 [TO child_f1,child_f2]\n";
            return;
        }

        auto parent_fields = split_fields_csv(parent_csv);
        auto child_fields = split_fields_csv(child_csv);
        if (parent_fields.empty() || child_fields.empty()) {
            std::cout << "SET RELATIONS: no fields provided\n";
            return;
        }
        if (parent_fields.size() != child_fields.size()) {
            std::cout << "SET RELATIONS: parent/child field counts differ\n";
            return;
        }

        if (!relations_api::add_relation(parent, child, parent_fields, child_fields)) return;

        relations_api::refresh_if_enabled();
        std::cout << "OK\n";
        return;
    }

    if (op == "CLEAR") {
        std::string which;
        ss >> which;
        if (which.empty()) {
            std::cout << "Usage: SET RELATIONS CLEAR <parent>|ALL\n";
            return;
        }
        if (up(which) == "ALL") {
            relations_api::clear_all_relations();
            std::cout << "OK\n";
            return;
        }
        relations_api::clear_relations(which);
        std::cout << "OK\n";
        return;
    }

    std::cout << "SET RELATIONS: unknown op. Try: ADD / CLEAR\n";
}

void cmd_RELATIONS_LIST(xbase::DbArea& /*A*/, std::istringstream& iss) {
    std::streampos pos = iss.tellg();
    std::string maybe;
    if (iss >> maybe) {
        const std::string flag = up(trim(maybe));
        if (flag == "USAGE" || flag == "HELP" || flag == "?") {
            show_relations_usage();
            return;
        }
        if (flag == "ALL") {
            const std::string parent = relations_api::current_parent_name();
            if (parent.empty()) {
                std::cout << "REL LIST: no current parent\n";
                return;
            }

            auto rows = relations_api::list_tree_for_current_parent(/*recursive=*/true, /*max_depth=*/24);

            std::cout << "Relations (tree) rooted at: " << up(trim(parent)) << "\n";
            if (rows.empty()) {
                std::cout << "  (none)\n";
                return;
            }

            if (rows.size() == 1) {
                std::cout << rows[0].line << "\n";
                std::cout << "  (none)\n";
                return;
            }

            for (const auto& r : rows) {
                std::cout << r.line << "\n";
            }
            return;
        }
    }

    iss.clear();
    iss.seekg(pos);

    const std::string parent = relations_api::current_parent_name();
    if (parent.empty()) {
        std::cout << "REL LIST: no current parent\n";
        return;
    }

    std::cout << "Relations for parent: " << parent << "\n";
    const auto kids = relations_api::child_areas_for_current_parent();
    if (kids.empty()) {
        std::cout << "  (none)\n";
        return;
    }

    for (const auto& c : kids) {
        const int cnt = relations_api::match_count_for_child(c);
        std::cout << "  -> " << c << "  (matches: " << cnt << ")\n";
    }
}

void cmd_RELATIONS_REFRESH(xbase::DbArea& /*A*/, std::istringstream& /*iss*/) {
    relations_api::refresh_for_current_parent();
    std::cout << "OK\n";
}

void cmd_REL_SAVE(xbase::DbArea& /*A*/, std::istringstream& iss) {
    std::string mode;
    iss >> mode;
    mode = up(trim(mode));

    std::string path;
    if (mode.empty() || mode == "DEFAULT") {
        path = default_relations_path();
    } else if (mode == "DATASET") {
        std::string dataset;
        iss >> dataset;
        dataset = trim(dataset);
        if (dataset.empty()) { show_relations_file_usage(); return; }
        path = dataset_relations_path(dataset);
    } else {
        path = trim(mode);
    }

    const auto specs = relations_api::export_relations();

    std::ostringstream out;
    out << "[\n";
    for (std::size_t i = 0; i < specs.size(); ++i) {
        const auto& s = specs[i];
        auto write_array = [&](const char* key, const std::vector<std::string>& values) {
            out << ",\"" << key << "\":[";
            for (std::size_t j = 0; j < values.size(); ++j) {
                if (j) out << ",";
                out << "\"" << escape_json(values[j]) << "\"";
            }
            out << "]";
        };

        out << "  {\"parent\":\"" << escape_json(s.parent)
            << "\",\"child\":\"" << escape_json(s.child) << "\"";
        if (!s.fields.empty()) write_array("fields", s.fields);
        if (!s.parent_fields.empty() || !s.child_fields.empty()) {
            write_array("parent_fields", s.parent_fields);
            write_array("child_fields", s.child_fields);
        }
        out << "}";
        if (i + 1 < specs.size()) out << ",";
        out << "\n";
    }
    out << "]\n";

    if (!write_entire_file(path, out.str())) {
        std::cout << "REL SAVE: cannot write file: " << path << "\n";
        return;
    }

    std::cout << "OK (" << specs.size() << " relation(s) saved to " << path << ")\n";
}

void cmd_REL_LOAD(xbase::DbArea& /*A*/, std::istringstream& iss) {
    std::string mode;
    iss >> mode;
    mode = up(trim(mode));

    std::string path;
    if (mode.empty() || mode == "DEFAULT") {
        path = default_relations_path();
    } else if (mode == "DATASET") {
        std::string dataset;
        iss >> dataset;
        dataset = trim(dataset);
        if (dataset.empty()) { show_relations_file_usage(); return; }
        path = dataset_relations_path(dataset);
    } else {
        path = trim(mode);
    }

    const std::string content = read_entire_file(path);
    if (content.empty()) {
        std::cout << "REL LOAD: cannot read file or file empty: " << path << "\n";
        return;
    }

    const auto specs = parse_relations_file(content);
    if (specs.empty()) {
        std::cout << "REL LOAD: no relations found in file\n";
        return;
    }

    relations_api::import_relations(specs, /*clear_existing=*/true);
    relations_api::refresh_if_enabled();

    std::cout << "OK (" << specs.size() << " relation(s) loaded from " << path << ")\n";
}

void cmd_REL_JOIN(xbase::DbArea& A, std::istringstream& iss) {
    std::string rest;
    std::getline(iss, rest);
    rest = trim(rest);

    if (rest.empty()) {
        std::cout <<
            "REL JOIN syntax\n"
            "  REL JOIN [ONE] [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\n"
            "Flags\n"
            "  ONE       emit exactly one row using the current relation context (historical behavior)\n"
            "  DISTINCT  de-duplicate tuples (field lists only)\n"
            "  ALL       allow duplicates (default; overrides DISTINCT)\n";
        return;
    }

    xbase::DbArea* home = workareas::db(workareas::current_slot());

    std::istringstream ss(rest);
    std::size_t max_rows = 0;
    bool distinct = false;
    bool one = false;
    std::unordered_set<std::string> seen;

    std::vector<std::string> path;
    std::string tok;

    std::string tuple_tail;
    bool saw_tuple = false;

    while (ss >> tok) {
        const std::string U = up(tok);

        if (U == "ONE") { one = true; continue; }
        if (U == "DISTINCT") { distinct = true; continue; }
        if (U == "ALL") { distinct = false; continue; }

        if (U == "LIMIT") {
            std::string n;
            if (!(ss >> n)) { std::cout << "REL JOIN: LIMIT requires a number\n"; return; }
            try { max_rows = static_cast<std::size_t>(std::stoull(n)); }
            catch (...) { std::cout << "REL JOIN: LIMIT requires a number\n"; return; }
            continue;
        }

        if (U == "TUPLE") {
            saw_tuple = true;
            std::string tmp;
            std::getline(ss, tmp);
            tuple_tail = trim(tmp);
            break;
        }

        path.push_back(tok);
    }

    if (!saw_tuple) { std::cout << "REL JOIN: missing TUPLE\n"; return; }
    if (tuple_tail.empty()) { std::cout << "REL JOIN: TUPLE requires an expression\n"; return; }

    std::size_t emitted = 0;
    const auto emit_row = [&]{
        ScopedEngineArea keep_area;

        if (!distinct) {
            std::istringstream t(tuple_tail);
            dli::registry().run(A, "TUPLE", t);
            return;
        }

        std::string key;
        const bool have_key = build_distinct_key_from_fields(tuple_tail, home, key);
        if (!have_key) {
            std::istringstream t(tuple_tail);
            dli::registry().run(A, "TUPLE", t);
            return;
        }

        if (seen.insert(key).second) {
            std::istringstream t(tuple_tail);
            dli::registry().run(A, "TUPLE", t);
        }
    };

    bool ok = false;
    if (one) {
        ok = relations_api::join_emit_one_for_current_parent(path, max_rows, emit_row, &emitted);
    } else {
        ok = relations_api::join_emit_for_current_parent(path, max_rows, emit_row, &emitted);
    }

    if (!ok) return;
    std::cout << "OK\n";
}

void cmd_REL_ENUM(xbase::DbArea& A, std::istringstream& iss) {
    std::string rest;
    std::getline(iss, rest);
    rest = trim(rest);

    if (rest.empty()) {
        std::cout <<
            "REL ENUM syntax\n"
            "  REL ENUM [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\n"
            "Flags\n"
            "  DISTINCT  de-duplicate tuples (field lists only)\n"
            "  ALL       allow duplicates (default; overrides DISTINCT)\n";
        return;
    }

    std::istringstream ss(rest);
    std::size_t max_rows = 0;
    bool distinct = false;

    std::vector<std::string> path;
    std::string tok;

    std::string tuple_tail;
    bool saw_tuple = false;

    while (ss >> tok) {
        const std::string U = up(tok);

        if (U == "DISTINCT") { distinct = true; continue; }
        if (U == "ALL") { distinct = false; continue; }

        if (U == "LIMIT") {
            std::string n;
            if (!(ss >> n)) { std::cout << "REL ENUM: LIMIT requires a number\n"; return; }
            try { max_rows = static_cast<std::size_t>(std::stoull(n)); }
            catch (...) { std::cout << "REL ENUM: LIMIT requires a number\n"; return; }
            continue;
        }

        if (U == "TUPLE") {
            saw_tuple = true;
            std::string tmp;
            std::getline(ss, tmp);
            tuple_tail = trim(tmp);
            break;
        }

        path.push_back(tok);
    }

    if (!saw_tuple) { std::cout << "REL ENUM: missing TUPLE\n"; return; }
    if (tuple_tail.empty()) { std::cout << "REL ENUM: TUPLE requires an expression\n"; return; }

    rel_enum_engine::Request req{};
    req.root_alias = "";
    req.path_aliases = path;
    req.tuple_exprs = split_tuple_expr_csv(tuple_tail);
    req.limit = max_rows;
    req.distinct = distinct;

    rel_enum_engine::Result res{};
    if (!rel_enum_engine::run(A, req, res)) {
        for (const auto& w : res.warnings)
            std::cout << w << "\n";
        return;
    }

    for (const auto& row : res.rows)
        std::cout << join_row_for_display(row) << "\n";

    std::cout << "OK\n";
}
