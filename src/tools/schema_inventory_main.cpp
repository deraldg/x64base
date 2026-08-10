// @dottalk.file v1
// subsystem: tools
// layer: helper
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: experimental

// Read-only schema inventory for the website data feed.
// Scans a repository's docs/ and source tree, emitting deterministic JSON.

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return s;
}

static std::string json_escape(const std::string& s) {
    std::string out;
    for (unsigned char c : s) {
        if (c == '\\') out += "\\\\";
        else if (c == '"') out += "\\\"";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c < 0x20) out += ' ';
        else out += char(c);
    }
    return out;
}

static bool ignored(const fs::path& p) {
    const auto n = lower(p.filename().string());
    return n == ".git" || n == ".venv" || n == "node_modules" || n == "build" ||
           n == "cmake-build-debug" || n == "cmake-build-release" || n == "public";
}

static std::string kind_for(const fs::path& p, const std::string& head) {
    const auto ext = lower(p.extension().string());
    const auto name = lower(p.filename().string());
    if (ext == ".dbf") return "dbf";
    if (ext == ".sql" || head.find("create table") != std::string::npos) return "sql";
    if (ext == ".json" && (name.find("schema") != std::string::npos || head.find("$schema") != std::string::npos)) return "json-schema";
    if (ext == ".dtschema") return "schema-document";
    if (name.find("schema") != std::string::npos || name.find("ddl") != std::string::npos) return "schema-document";
    return {};
}

int main(int argc, char** argv) {
    fs::path root = ".";
    fs::path output = "docs/generated/schema_inventory.json";
    if (argc > 1) root = argv[1];
    if (argc > 2) output = argv[2];
    if (!fs::is_directory(root)) { std::cerr << "schema_inventory: root is not a directory\n"; return 2; }

    struct Row { std::string path, kind; std::uintmax_t bytes{}; };
    std::vector<Row> rows;
    std::error_code ec;
    for (fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end; it != end; it.increment(ec)) {
        if (ec) { ec.clear(); continue; }
        if (it->is_directory() && ignored(it->path())) { it.disable_recursion_pending(); continue; }
        if (!it->is_regular_file()) continue;
        const auto rel = it->path().lexically_relative(root).generic_string();
        // The root is the repository boundary; ignored directories above keep
        // generated/build trees out while allowing schema files anywhere in
        // docs/ and the repository source/data tree.
        std::ifstream in(it->path(), std::ios::binary);
        std::string head(8192, '\0');
        in.read(head.data(), static_cast<std::streamsize>(head.size()));
        head.resize(static_cast<size_t>(in.gcount()));
        const auto kind = kind_for(it->path(), lower(head));
        if (!kind.empty()) rows.push_back({rel, kind, it->file_size(ec)});
    }
    std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) { return a.path < b.path; });
    fs::create_directories(output.parent_path(), ec);
    std::ofstream out(output, std::ios::binary);
    if (!out) { std::cerr << "schema_inventory: cannot write output\n"; return 3; }
    out << "{\n  \"schema\": \"x64base.schema_inventory.v1\",\n  \"root\": \"" << json_escape(fs::absolute(root).generic_string()) << "\",\n  \"count\": " << rows.size() << ",\n  \"items\": [\n";
    for (size_t i = 0; i < rows.size(); ++i) {
        out << "    {\"path\":\"" << json_escape(rows[i].path) << "\",\"kind\":\"" << rows[i].kind << "\",\"bytes\":" << rows[i].bytes << "}" << (i + 1 == rows.size() ? "\n" : ",\n");
    }
    out << "  ]\n}\n";
    std::cout << "schema_inventory: wrote " << rows.size() << " items to " << output.string() << "\n";
}
