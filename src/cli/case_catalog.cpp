#include "edu/case_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "textio.hpp"

namespace fs = std::filesystem;

namespace dottalk::cases {

namespace {

static bool starts_with(const std::string& s, const std::string& prefix) {
    return s.size() >= prefix.size() && s.compare(0, prefix.size(), prefix) == 0;
}

static bool ieq(const std::string& a, const std::string& b) {
    return up_copy(a) == up_copy(b);
}

static std::string strip_quotes(const std::string& s) {
    const std::string t = trim_copy(s);
    if (t.size() >= 2) {
        const char a = t.front();
        const char z = t.back();
        if ((a == '"' && z == '"') || (a == '\'' && z == '\'')) {
            return t.substr(1, t.size() - 2);
        }
    }
    return t;
}

static std::vector<std::string> split_lines(const std::string& text) {
    std::vector<std::string> out;
    std::istringstream iss(text);
    for (std::string line; std::getline(iss, line); ) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        out.push_back(line);
    }
    return out;
}

static std::string join_lines(const std::vector<std::string>& lines, std::size_t begin, std::size_t end) {
    std::ostringstream oss;
    for (std::size_t i = begin; i < end; ++i) {
        oss << lines[i];
        if (i + 1 < end) oss << "\n";
    }
    return oss.str();
}

static std::string normalize_key(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char ch : s) {
        unsigned char c = static_cast<unsigned char>(ch);
        if (std::isalnum(c)) out.push_back(static_cast<char>(std::toupper(c)));
        else if (std::isspace(c) || ch == '_' || ch == '-') out.push_back('_');
    }

    // collapse repeated underscores
    std::string collapsed;
    collapsed.reserve(out.size());
    bool last_us = false;
    for (char ch : out) {
        if (ch == '_') {
            if (!last_us) collapsed.push_back(ch);
            last_us = true;
        } else {
            collapsed.push_back(ch);
            last_us = false;
        }
    }

    while (!collapsed.empty() && collapsed.front() == '_') collapsed.erase(collapsed.begin());
    while (!collapsed.empty() && collapsed.back() == '_') collapsed.pop_back();
    return collapsed;
}

static std::vector<std::string> parse_yaml_list_inline(const std::string& value) {
    // expects: [a, b, c]
    std::vector<std::string> out;
    std::string t = trim_copy(value);
    if (t.size() < 2 || t.front() != '[' || t.back() != ']') return out;
    t = t.substr(1, t.size() - 2);

    std::string cur;
    bool in_quotes = false;
    char quote_char = '\0';

    for (char ch : t) {
        if ((ch == '"' || ch == '\'') && (!in_quotes || ch == quote_char)) {
            if (in_quotes && ch == quote_char) {
                in_quotes = false;
                quote_char = '\0';
            } else if (!in_quotes) {
                in_quotes = true;
                quote_char = ch;
            }
            cur.push_back(ch);
            continue;
        }

        if (ch == ',' && !in_quotes) {
            const std::string item = strip_quotes(trim_copy(cur));
            if (!item.empty()) out.push_back(item);
            cur.clear();
            continue;
        }

        cur.push_back(ch);
    }

    const std::string item = strip_quotes(trim_copy(cur));
    if (!item.empty()) out.push_back(item);

    return out;
}

static bool read_file_text(const fs::path& p, std::string& out, std::string* err) {
    std::ifstream ifs(p, std::ios::binary);
    if (!ifs) {
        if (err) *err = "unable to open file: " + p.string();
        return false;
    }

    std::ostringstream oss;
    oss << ifs.rdbuf();
    out = oss.str();

    // strip UTF-8 BOM if present
    if (out.size() >= 3 &&
        static_cast<unsigned char>(out[0]) == 0xEF &&
        static_cast<unsigned char>(out[1]) == 0xBB &&
        static_cast<unsigned char>(out[2]) == 0xBF) {
        out.erase(0, 3);
    }

    return true;
}

static bool parse_front_matter_and_body(const std::string& text,
                                        std::unordered_map<std::string, std::string>& meta,
                                        std::string& body) {
    auto lines = split_lines(text);
    if (lines.empty() || trim_copy(lines[0]) != "---") {
        body = text;
        return true;
    }

    std::size_t i = 1;
    for (; i < lines.size(); ++i) {
        const std::string t = trim_copy(lines[i]);
        if (t == "---") {
            ++i;
            break;
        }

        const auto pos = lines[i].find(':');
        if (pos == std::string::npos) continue;

        const std::string key = trim_copy(lines[i].substr(0, pos));
        const std::string val = trim_copy(lines[i].substr(pos + 1));
        if (!key.empty()) meta[normalize_key(key)] = val;
    }

    body = join_lines(lines, i, lines.size());
    return true;
}

static std::string extract_section(const std::string& body, const std::string& wanted_heading) {
    const auto lines = split_lines(body);
    const std::string wanted = "## " + up_copy(wanted_heading);

    std::size_t start = std::string::npos;
    for (std::size_t i = 0; i < lines.size(); ++i) {
        const std::string t = trim_copy(lines[i]);
        if (starts_with(t, "## ")) {
            const std::string heading = "## " + up_copy(trim_copy(t.substr(3)));
            if (heading == wanted) {
                start = i + 1;
                break;
            }
        }
    }

    if (start == std::string::npos) return {};

    std::size_t end = lines.size();
    for (std::size_t i = start; i < lines.size(); ++i) {
        const std::string t = trim_copy(lines[i]);
        if (starts_with(t, "## ")) {
            end = i;
            break;
        }
    }

    std::string section = join_lines(lines, start, end);

    // light cleanup:
    // remove surrounding blank lines
    auto sec_lines = split_lines(section);
    while (!sec_lines.empty() && trim_copy(sec_lines.front()).empty()) sec_lines.erase(sec_lines.begin());
    while (!sec_lines.empty() && trim_copy(sec_lines.back()).empty()) sec_lines.pop_back();

    return join_lines(sec_lines, 0, sec_lines.size());
}

static bool parse_case_file(const fs::path& p, CaseStudy& out, std::string* err) {
    std::string text;
    if (!read_file_text(p, text, err)) return false;

    std::unordered_map<std::string, std::string> meta;
    std::string body;
    parse_front_matter_and_body(text, meta, body);

    out.path = p.string();
    out.id = strip_quotes(trim_copy(meta["ID"]));
    out.title = strip_quotes(trim_copy(meta["TITLE"]));
    out.type = strip_quotes(trim_copy(meta["TYPE"]));
    out.era = strip_quotes(trim_copy(meta["ERA"]));
    out.level = strip_quotes(trim_copy(meta["LEVEL"]));
    out.lab = strip_quotes(trim_copy(meta["LAB"]));
    out.raw_body = body;

    if (meta.count("DOMAINS")) {
        out.domains = parse_yaml_list_inline(meta["DOMAINS"]);
    }

    if (out.id.empty() || out.title.empty()) {
        if (err) *err = "missing required yaml fields id/title in: " + p.string();
        return false;
    }

    out.summary  = extract_section(body, "SUMMARY");
    out.problem  = extract_section(body, "PROBLEM");
    out.workflow = extract_section(body, "WORKFLOW");
    out.model    = extract_section(body, "MODEL");
    out.takeaway = extract_section(body, "TAKEAWAY");

    return true;
}

static fs::path guess_cases_dir() {
    // Conservative first pass:
    // 1. ./docs/cases
    // 2. ../docs/cases
    // 3. ../../docs/cases
    const fs::path p0 = fs::path("docs") / "cases";
    if (fs::exists(p0) && fs::is_directory(p0)) return fs::absolute(p0);

    const fs::path p1 = fs::path("..") / "docs" / "cases";
    if (fs::exists(p1) && fs::is_directory(p1)) return fs::absolute(p1);

    const fs::path p2 = fs::path("..") / ".." / "docs" / "cases";
    if (fs::exists(p2) && fs::is_directory(p2)) return fs::absolute(p2);

    return fs::absolute(p0);
}

} // namespace

std::string up_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

std::string trim_copy(std::string s) {
    return textio::trim(std::move(s));
}

bool Catalog::load(std::string* err) {
    if (loaded_) return true;
    return reload(err);
}

bool Catalog::reload(std::string* err) {
    by_id_.clear();
    loaded_ = false;

    const fs::path dir = guess_cases_dir();
    if (!fs::exists(dir) || !fs::is_directory(dir)) {
        if (err) *err = "cases directory not found: " + dir.string();
        return false;
    }

    for (const auto& ent : fs::directory_iterator(dir)) {
        if (!ent.is_regular_file()) continue;

        const fs::path p = ent.path();
        const std::string name = up_copy(p.filename().string());

        // Preserve the old helper by wiring it into real catalog filtering.
        // This keeps case-study discovery case-insensitive for .md/.MD files.
        if (!ieq(p.extension().string(), ".md")) continue;
        if (!starts_with(name, "CASE_")) continue;
        if (ieq(name, "CASE_FRAMEWORK.MD")) continue;

        CaseStudy cs;
        std::string one_err;
        if (!parse_case_file(p, cs, &one_err)) {
            // Skip malformed case files in first pass.
            continue;
        }

        by_id_[up_copy(cs.id)] = std::move(cs);
    }

    loaded_ = true;
    return true;
}

bool Catalog::empty() const {
    return by_id_.empty();
}

std::size_t Catalog::size() const {
    return by_id_.size();
}

const CaseStudy* Catalog::find(const std::string& id) const {
    const auto it = by_id_.find(up_copy(id));
    if (it == by_id_.end()) return nullptr;
    return &it->second;
}

std::vector<const CaseStudy*> Catalog::list() const {
    std::vector<const CaseStudy*> out;
    out.reserve(by_id_.size());
    for (const auto& kv : by_id_) out.push_back(&kv.second);

    std::sort(out.begin(), out.end(),
              [](const CaseStudy* a, const CaseStudy* b) {
                  return up_copy(a->id) < up_copy(b->id);
              });
    return out;
}

std::string Catalog::cases_dir() const {
    return guess_cases_dir().string();
}

Catalog& catalog() {
    static Catalog g;
    return g;
}

} // namespace dottalk::cases