
// src/cli/relations_boot.cpp
// Auto-load relations on startup; auto-save on process exit.
// Honors env toggles: SB_REL_AUTOLOAD=0 or SB_REL_AUTOSAVE=0 to disable.

#include "relations_boot.hpp"
#include "set_relations.hpp"
#include "cli/settings.hpp"
#include "workareas.hpp"
#include "textio.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <iostream>

namespace {

static std::string default_rel_path() { return std::string(".relations/relations.json"); }
static std::vector<relations_api::RelationSpec>& pending_rel_specs() {
    static std::vector<relations_api::RelationSpec> specs;
    return specs;
}

static void emit_rel_boot_diag(const std::string& text) {
#if DOTTALK_EXTRA_DIAGNOSTICS
    if (!cli::Settings::passiveDevDiagnosticsEnabled()) {
        return;
    }

    try {
        std::cerr << "[RELDBG] " << text << "\n";
        std::cerr.flush();
    } catch (...) {
    }

    try {
        std::ofstream log("dottalk_rel_trace.log", std::ios::app);
        if (log.is_open()) {
            log << text << "\n";
            log.flush();
        }
    } catch (...) {
    }
#else
    (void)text;
#endif
}

static bool env_enabled(const char* name, bool defval) {
    const char* v = std::getenv(name);
    if (!v) return defval;
    if (*v=='0') return false;
    return true;
}

static bool area_is_open_ci(const std::string& logical_or_name) {
    const std::string target = textio::up(textio::trim(logical_or_name));
    if (target.empty()) return false;

    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        xbase::DbArea* area = workareas::db(i);
        if (!area) continue;

        bool open = false;
        try { open = area->isOpen(); } catch (...) { open = false; }
        if (!open) continue;

        try {
            const std::string ln = area->logicalName();
            if (!ln.empty() && textio::up(ln) == target) return true;
            const std::string nm = area->name();
            if (!nm.empty() && textio::up(nm) == target) return true;
        } catch (...) {}
    }

    return false;
}

static std::vector<relations_api::RelationSpec> read_default_specs() {
    const std::string path = default_rel_path();
    std::ifstream f(path, std::ios::binary);
    if (!f) {
        emit_rel_boot_diag("autoload: no relation file at " + path);
        return {};
    }

    emit_rel_boot_diag("autoload: reading " + path);
    std::string data((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    std::vector<relations_api::RelationSpec> specs;
    size_t pos = data.find("[", data.find("\"relations\""));
    if (pos == std::string::npos) {
        emit_rel_boot_diag("autoload: no relations array in " + path);
        return {};
    }
    while (true) {
        size_t p_obj = data.find("{", pos);
        size_t p_end = data.find("]", pos);
        if (p_obj == std::string::npos || (p_end != std::string::npos && p_obj > p_end)) break;
        size_t p_obj_end = data.find("}", p_obj);
        if (p_obj_end == std::string::npos) break;
        std::string obj = data.substr(p_obj, p_obj_end - p_obj + 1);
        auto trim = [](std::string s){ auto sp=[](unsigned char c){return c==' '||c=='\t'||c=='\r'||c=='\n';};
            while(!s.empty()&&sp((unsigned char)s.front())) s.erase(s.begin());
            while(!s.empty()&&sp((unsigned char)s.back())) s.pop_back();
            return s; };
        auto grab_string = [&](const std::string& key)->std::string{
            std::string pat = "\"" + key + "\":\"";
            size_t s = obj.find(pat);
            if (s == std::string::npos) return "";
            s += pat.size();
            size_t e = obj.find("\"", s);
            if (e == std::string::npos) return "";
            return obj.substr(s, e - s);
        };
        auto grab_array = [&](const std::string& key)->std::vector<std::string>{
            std::vector<std::string> out;
            std::string pat = "\"" + key + "\":[";
            size_t s = obj.find(pat);
            if (s == std::string::npos) return out;
            s += pat.size();
            size_t e = obj.find("]", s);
            if (e == std::string::npos) return out;
            std::string arr = obj.substr(s, e - s);
            std::istringstream as(arr);
            std::string tok;
            while (std::getline(as, tok, ',')) {
                tok = trim(tok);
                if (!tok.empty() && tok.front()=='\"' && tok.back()=='\"') {
                    tok = tok.substr(1, tok.size()-2);
                }
                if (!tok.empty()) out.push_back(tok);
            }
            return out;
        };
        relations_api::RelationSpec rs;
        rs.parent = grab_string("parent");
        rs.child  = grab_string("child");
        rs.fields = grab_array("fields");
        rs.parent_fields = grab_array("parent_fields");
        rs.child_fields = grab_array("child_fields");
        const bool has_legacy_fields = !rs.fields.empty();
        const bool has_asymmetric_fields = !rs.parent_fields.empty() && !rs.child_fields.empty();
        if (!rs.parent.empty() && !rs.child.empty() && (has_legacy_fields || has_asymmetric_fields)) specs.push_back(std::move(rs));
        pos = p_obj_end + 1;
    }
    emit_rel_boot_diag("autoload: parsed=" + std::to_string(specs.size()));
    return specs;
}

static bool try_import_specs_if_ready(const std::vector<relations_api::RelationSpec>& specs,
                                      const char* source_tag) {
    if (specs.empty()) {
        emit_rel_boot_diag(std::string(source_tag) + ": no pending relations");
        return false;
    }

    const auto existing = relations_api::export_relations();
    if (!existing.empty()) {
        emit_rel_boot_diag(
            std::string(source_tag) + ": relation graph already populated; skip pending import count=" +
            std::to_string(existing.size()));
        return true;
    }

    std::size_t blocked = 0;
    for (const auto& spec : specs) {
        if (!area_is_open_ci(spec.parent)) {
            emit_rel_boot_diag(std::string(source_tag) + ": wait parent not open: " + spec.parent + " -> " + spec.child);
            ++blocked;
            continue;
        }
        if (!area_is_open_ci(spec.child)) {
            emit_rel_boot_diag(std::string(source_tag) + ": wait child not open: " + spec.parent + " -> " + spec.child);
            ++blocked;
            continue;
        }
    }

    emit_rel_boot_diag(
        std::string(source_tag) + ": parsed=" + std::to_string(specs.size()) +
        " blocked=" + std::to_string(blocked));

    if (blocked != 0) return false;

    relations_api::import_relations(specs, /*clear_existing*/true);
    emit_rel_boot_diag(
        std::string(source_tag) + ": import complete count=" + std::to_string(specs.size()));
    return true;
}

static void save_default() {
    const std::string path = default_rel_path();
    auto specs = relations_api::export_relations();

    // Do not create runtime state merely because an otherwise idle shell exits.
    // If a file already exists, still rewrite it so clearing all relations is
    // persisted correctly.
    if (specs.empty() && !std::filesystem::exists(path)) return;

    // ensure dir exists (simple approach)
#ifdef _WIN32
    _wmkdir(L".relations");
#else
    ::system("mkdir -p .relations");
#endif
    std::ofstream f(path, std::ios::binary);
    if (!f) return;
    auto jesc = [](const std::string& s){
        std::string out; out.reserve(s.size()+8);
        for (char c : s) {
            switch (c) {
                case '\\': out += "\\\\"; break;
                case '"':  out += "\\\""; break;
                case '\n': out += "\\n"; break;
                case '\r': out += "\\r"; break;
                case '\t': out += "\\t"; break;
                default: out.push_back(c); break;
            }
        }
        return out;
    };
    f << "{\n  \"relations\": [\n";
    for (size_t i=0;i<specs.size();++i) {
        const auto& s = specs[i];
        auto write_array = [&](const char* key, const std::vector<std::string>& values) {
            f << ",\"" << key << "\":[";
            for (size_t j=0;j<values.size();++j) {
                if (j) f << ",";
                f << "\"" << jesc(values[j]) << "\"";
            }
            f << "]";
        };

        f << "    {\"parent\":\"" << jesc(s.parent) << "\",\"child\":\"" << jesc(s.child) << "\"";
        if (!s.fields.empty()) write_array("fields", s.fields);
        if (!s.parent_fields.empty() || !s.child_fields.empty()) {
            write_array("parent_fields", s.parent_fields);
            write_array("child_fields", s.child_fields);
        }
        f << "}";
        if (i + 1 < specs.size()) f << ",";
        f << "\n";
    }
    f << "  ]\n}\n";
}

} // namespace

namespace relations_boot {
void autoload() {
    const bool enabled = env_enabled("SB_REL_AUTOLOAD", true);
    emit_rel_boot_diag(std::string("autoload: ") + (enabled ? "enabled" : "disabled"));
    if (!enabled) {
        pending_rel_specs().clear();
        return;
    }

    pending_rel_specs() = read_default_specs();
    if (try_import_specs_if_ready(pending_rel_specs(), "autoload")) {
        pending_rel_specs().clear();
    }
}
bool retry_pending_autoload() {
    auto& pending = pending_rel_specs();
    if (pending.empty()) return false;

    if (try_import_specs_if_ready(pending, "autoload-retry")) {
        pending.clear();
        return true;
    }
    return false;
}
void autosave() { save_default(); }
bool autosave_enabled() noexcept { return env_enabled("SB_REL_AUTOSAVE", true); }
} // namespace relations_boot
