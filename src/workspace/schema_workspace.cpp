// @dottalk.file v1
// subsystem: workspace
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "workspace/schema_workspace.hpp"
#include "workspace/workarea_manager.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <sstream>
#include <string>

#include "cli/order_state.hpp"

// Engine bridge
extern "C" xbase::XBaseEngine* shell_engine();

namespace dottalk::workspace {

namespace {

static inline std::string trim_copy(std::string s)
{
    auto is_space = [](unsigned char ch){ return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c){ return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c){ return !is_space(c); }).base(), s.end());
    return s;
}

static inline bool ci_equal(const std::string& a, const std::string& b)
{
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (std::tolower((unsigned char)a[i]) != std::tolower((unsigned char)b[i])) {
            return false;
        }
    }
    return true;
}

static inline std::string infer_index_type_from_path(const std::string& path)
{
    if (path.empty() || ci_equal(path, "none")) return "NONE";

    auto dot = path.find_last_of('.');
    if (dot == std::string::npos) return "UNKNOWN";

    std::string ext = path.substr(dot);
    std::transform(ext.begin(), ext.end(), ext.begin(),
        [](unsigned char c){ return (char)std::tolower(c); });

    if (ext == ".inx") return "INX";
    if (ext == ".cnx") return "CNX";
    if (ext == ".cdx") return "CDX";
    return "UNKNOWN";
}

template <typename Area>
static inline std::string get_order_name_safe(Area& a)
{
    try { return orderstate::orderName(a); } catch (...) { return {}; }
}

template <typename Area>
static inline std::string get_active_tag_safe(Area& a)
{
    try { return orderstate::activeTag(a); } catch (...) {}
    return {};
}

template <typename Area>
static inline bool set_active_tag_safe(Area& a, const std::string& tag)
{
    if (tag.empty() || ci_equal(tag, "none")) return true;

    try {
        orderstate::setActiveTag(a, tag);
        return true;
    } catch (...) {}

    return false;
}

template <typename T>
using has_setLogicalName_t = decltype(std::declval<T&>().setLogicalName(std::declval<std::string>()));
template <typename T, typename = has_setLogicalName_t<T>>
static inline void setLogicalNameIf(T& a, const std::string& s, int) { a.setLogicalName(s); }
template <typename T>
static inline void setLogicalNameIf(T&, const std::string&, long) {}

template <typename T>
using has_setName_t = decltype(std::declval<T&>().setName(std::declval<std::string>()));
template <typename T, typename = has_setName_t<T>>
static inline void setLegacyNameIf(T& a, const std::string& s, int) { a.setName(s); }
template <typename T>
static inline void setLegacyNameIf(T&, const std::string&, long) {}

static inline std::string encode_field(const std::string& s)
{
    std::string out;
    out.reserve(s.size() + 8);

    for (char c : s) {
        switch (c) {
            case '\\': out += "\\\\"; break;
            case '|':  out += "\\p";  break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            default:   out.push_back(c); break;
        }
    }
    return out;
}

static inline std::string decode_field(const std::string& s)
{
    std::string out;
    out.reserve(s.size());

    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '\\' || i + 1 >= s.size()) {
            out.push_back(s[i]);
            continue;
        }

        const char n = s[++i];
        switch (n) {
            case '\\': out.push_back('\\'); break;
            case 'p':  out.push_back('|');  break;
            case 'n':  out.push_back('\n'); break;
            case 'r':  out.push_back('\r'); break;
            default:
                out.push_back('\\');
                out.push_back(n);
                break;
        }
    }

    return out;
}

static inline std::vector<std::string> split_pipe_escaped(const std::string& s)
{
    std::vector<std::string> parts;
    std::string cur;
    cur.reserve(s.size());

    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] == '|') {
            parts.push_back(cur);
            cur.clear();
            continue;
        }

        if (s[i] == '\\' && i + 1 < s.size()) {
            cur.push_back(s[i]);
            cur.push_back(s[++i]);
            continue;
        }

        cur.push_back(s[i]);
    }

    parts.push_back(cur);
    return parts;
}

} // namespace

bool SchemaWorkspace::capture_from_runtime(const WorkAreaManager& wam)
{
    areas.clear();
    current_slot = wam.current_slot();

    for (int i = 0; i < wam.count(); ++i)
    {
        auto* a = wam.dbarea(i);
        if (!a) continue;

        const std::string file = a->filename();
        if (file.empty()) continue;

        SchemaAreaState s;
        s.slot       = i;
        s.dbf_path   = file;
        s.logical_name = a->logicalName();
        s.alias        = s.logical_name;
        s.recno      = a->recno();
        s.index_container_path = get_order_name_safe(*a);
        s.active_order_name = s.index_container_path;
        s.active_tag = get_active_tag_safe(*a);

        areas.push_back(s);
    }

    return true;
}

bool SchemaWorkspace::apply_to_runtime(WorkAreaManager& wam)
{
    auto* eng = shell_engine();
    if (!eng) return false;

    for (const auto& a : areas)
    {
        try {
            eng->selectArea(a.slot);

            xbase::DbArea& area = eng->area(a.slot);

            try { orderstate::clearOrder(area); } catch (...) {}
            try { area.close(); } catch (...) {}

            area.open(a.dbf_path);
            area.setFilename(a.dbf_path);

            if (!a.logical_name.empty()) {
                setLogicalNameIf(area, a.logical_name, 0);
                setLegacyNameIf(area, a.logical_name, 0);
            }

            if (!a.index_container_path.empty() && !ci_equal(a.index_container_path, "none")) {
                try { orderstate::setOrder(area, a.index_container_path); } catch (...) {}
            }

            if (!a.active_tag.empty() && !ci_equal(a.active_tag, "none")) {
                (void)set_active_tag_safe(area, a.active_tag);
            }

            if (a.recno > 0) {
                (void)area.gotoRec(a.recno);
            }
        }
        catch (...) {
            return false;
        }
    }

    return wam.select(current_slot);
}

// FORMAT-NAME COLLISION RECONCILED 2026-08-11 (owner ruling: reconcile now).
// This writer emitted "DTSHEMA 3" -- a pipe-delimited runtime snapshot -- while
// cmd_workspace.cpp's serializer emits the keyed .dtschema posture format under
// the SAME version name. AIF-078 recorded the drift as D5/Q5 ("two writers, two
// versions, one format name") on 2026-07-30; on 2026-08-11 an opt-in DTSHEMA 3
// landed in the CLI serializer, turning a latent drift into an active collision
// with incompatible layouts. The failure mode was SILENT, not loud: the CLI
// loader matches "AREA " (with a space), so a pipe-form "AREA|0|..." line falls
// through to tolerate-unknown and restores ZERO areas without an error.
//
// RULING: the CLI serializer (workspace_save_to_string / workspace_load_from_stream)
// is authoritative for the .dtschema format and owns the DTSHEMA version
// namespace -- one format, one writer, the same rule that keeps file and memo
// carriers from drifting. THIS snapshot is a different artifact (runtime work
// area state, pipe-delimited) and must not claim a DTSHEMA name, so it declares
// its own: DTWSSNAP 1. Version numbers are freed for the .dtschema line, incl.
// the DTSHEMA 4 the multi-workspace change package reserves.
//
// MEASURED the same day: save_file/load_file have ZERO callers in the tree --
// this pair is an unwired parallel serializer (the AIF-079 D1 shape), which is
// why the collision never fired and why renaming is safe. NOT deleted here: the
// multi-workspace package plans to extend SchemaAreaState (ws tag) and this
// class, so retiring it is a maintainer/lane call, not a drive-by.
//
// PRIOR ART, RECORDED HONESTLY: this snapshot already carried per-area recno
// and CURRENT slot -- the same session-state concept the CLI serializer added
// on 2026-08-11 as v3 CURSOR/CURRENT lines. The design was arrived at twice
// because it was registered in neither lane's queue row: AIF-078's own lesson,
// recurring. The CLI implementation is the wired and regression-proven one
// (REGRESSION RUN WORKSPACE_SESSION); this one is its unwired ancestor.
bool SchemaWorkspace::save_file(const std::string& path) const
{
    std::ofstream f(path);
    if (!f) return false;

    f << "DTWSSNAP 1\n";
    f << "CURRENT|" << current_slot << "\n";

    for (const auto& a : areas)
    {
        f << "AREA|"
          << a.slot << "|"
          << encode_field(a.dbf_path) << "|"
          << encode_field(a.logical_name) << "|"
          << a.recno << "|"
          << encode_field(a.index_container_path) << "|"
          << encode_field(infer_index_type_from_path(a.index_container_path)) << "|"
          << encode_field(a.active_tag)
          << "\n";
    }

    return true;
}

bool SchemaWorkspace::load_file(const std::string& path)
{
    std::ifstream f(path);
    if (!f) return false;

    areas.clear();
    current_slot = 0;

    std::string line;
    bool saw_header = false;

    while (std::getline(f, line))
    {
        line = trim_copy(line);
        if (line.empty()) continue;

        if (!saw_header) {
            saw_header = true;

            // Own name first; legacy "DTSHEMA 3" still accepted so any file
            // this writer produced before the 2026-08-11 reconciliation loads
            // unchanged (read-side tolerance, write-side single name).
            if (ci_equal(line, "DTWSSNAP 1") || ci_equal(line, "DTSHEMA 3")) {
                continue;
            }

            if (line.rfind("CURRENT ", 0) == 0) {
                current_slot = std::stoi(trim_copy(line.substr(8)));
                continue;
            }

            if (line.rfind("CURRENT|", 0) == 0) {
                current_slot = std::stoi(trim_copy(line.substr(8)));
                continue;
            }

            return false;
        }

        if (line.rfind("CURRENT|", 0) == 0)
        {
            current_slot = std::stoi(trim_copy(line.substr(8)));
            continue;
        }

        if (line.rfind("CURRENT ", 0) == 0)
        {
            current_slot = std::stoi(trim_copy(line.substr(8)));
            continue;
        }

        if (line.rfind("AREA|", 0) == 0)
        {
            const std::string body = line.substr(5);
            const auto parts = split_pipe_escaped(body);

            if (parts.size() >= 7) {
                SchemaAreaState s;
                s.slot       = std::stoi(parts[0]);
                s.dbf_path   = decode_field(parts[1]);
                s.logical_name = decode_field(parts[2]);
                s.alias        = s.logical_name;
                s.recno      = std::stoi(parts[3]);
                s.index_container_path = decode_field(parts[4]);
                s.active_order_name = decode_field(parts[5]);
                s.active_tag = decode_field(parts[6]);
                areas.push_back(s);
                continue;
            }

            return false;
        }

        if (line.rfind("AREA ", 0) == 0)
        {
            const std::string body = line.substr(5);
            const auto parts = split_pipe_escaped(body);

            if (parts.size() >= 4) {
                SchemaAreaState s;
                s.slot       = std::stoi(parts[0]);
                s.dbf_path   = decode_field(parts[1]);
                s.logical_name = decode_field(parts[2]);
                s.alias        = s.logical_name;
                s.recno      = std::stoi(parts[3]);
                s.index_container_path.clear();
                s.active_order_name = "NONE";
                s.active_tag.clear();
                areas.push_back(s);
                continue;
            }

            return false;
        }
    }

    return saw_header;
}

} // namespace dottalk::workspace