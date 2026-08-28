// @dottalk.file v1
// subsystem: common
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// common/path_resolver.cpp
#include "common/path_resolver.hpp"

#include "cli/cmd_setpath.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <filesystem>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;

namespace dottalk::paths {

namespace {

static bool has_any_sep(const std::string& s)
{
    return s.find('/') != std::string::npos || s.find('\\') != std::string::npos;
}

static bool file_exists(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
}

static fs::path abs_if_exists(const fs::path& p)
{
    std::error_code ec;
    if (file_exists(p))
        return fs::absolute(p, ec);
    return {};
}

static fs::path relative_under_root(const fs::path& path, const fs::path& root)
{
    if (path.empty() || root.empty()) {
        return {};
    }

    std::error_code ec_path;
    std::error_code ec_root;
    const fs::path abs_path = fs::weakly_canonical(path, ec_path);
    const fs::path abs_root = fs::weakly_canonical(root, ec_root);
    if (ec_path || ec_root) {
        return {};
    }

    std::error_code ec_rel;
    const fs::path rel = fs::relative(abs_path, abs_root, ec_rel);
    if (ec_rel || rel.empty()) {
        return {};
    }

    for (const auto& part : rel) {
        if (part == "..") {
            return {};
        }
    }
    return rel;
}

// Returns an EXISTING path or EMPTY. No fallback, no invention.
//
// AIF-145 R-a: split out of resolve_in_search_roots so a caller can ask "is it
// here?" and act on no. The old function could not be reused for a multi-
// extension search because it never returns empty -- it always falls back to
// roots.front(), so a caller had no way to learn that this extension missed and
// the next should be tried.
static fs::path find_in_search_roots(const std::string& token,
                                     const std::vector<fs::path>& roots,
                                     const std::string& default_ext = "")
{
    fs::path p(token);

    if (!default_ext.empty() && !p.has_extension())
        p.replace_extension(default_ext);

    if (p.is_absolute())
        return abs_if_exists(p);

    {
        fs::path found = abs_if_exists(p);
        if (!found.empty())
            return found;
    }

    if (has_any_sep(token))
        return abs_if_exists(state().data_root / p);

    for (const auto& root : roots) {
        fs::path found = abs_if_exists(root / p);
        if (!found.empty())
            return found;
    }

    return {};
}

// Unchanged in behaviour: find, else invent the conventional location. Every
// fallback below is exactly what this function returned before the split, in
// the same order and for the same inputs.
static fs::path resolve_in_search_roots(const std::string& token,
                                        const std::vector<fs::path>& roots,
                                        const std::string& default_ext = "")
{
    fs::path found = find_in_search_roots(token, roots, default_ext);
    if (!found.empty())
        return found;

    fs::path p(token);
    if (!default_ext.empty() && !p.has_extension())
        p.replace_extension(default_ext);

    if (p.is_absolute())
        return fs::absolute(p);

    if (has_any_sep(token))
        return fs::absolute(state().data_root / p);

    if (!roots.empty())
        return fs::absolute(roots.front() / p);

    return fs::absolute(p);
}

} // namespace

fs::path resolve_in_slot(const fs::path& slot_root, const std::string& token)
{
    fs::path p(token);

    if (p.is_absolute()) {
        return p;
    }

    // If token already contains separators, treat it as relative to DATA root,
    // so "dbf/students.dbf" works regardless of current working directory.
    if (has_any_sep(token)) {
        return fs::absolute(state().data_root / p);
    }

    return fs::absolute(slot_root / p);
}

fs::path ensure_ext(fs::path p, const std::string& ext_with_dot)
{
    if (!p.has_extension()) {
        p.replace_extension(ext_with_dot);
    }
    return p;
}

fs::path resolve_dbf(const std::string& token)
{
    const fs::path root = get_slot(Slot::DBF);
    const fs::path p = resolve_in_slot(root, token);
    return ensure_ext(p, ".dbf");
}

fs::path resolve_index(const std::string& token)
{
    const fs::path root = get_slot(Slot::INDEXES);
    const fs::path p = resolve_in_slot(root, token);
    // Public index container/file root:
    //   .inx, .cnx, .cdx
    // Do not force an extension here.
    return p;
}

fs::path resolve_lmdb_root()
{
    return get_slot(Slot::LMDB);
}

fs::path resolve_lmdb_env_for_cdx(const fs::path& public_cdx_path)
{
    const fs::path root = get_slot(Slot::LMDB);
    const fs::path indexes_root = get_slot(Slot::INDEXES);

    if (const fs::path rel = relative_under_root(public_cdx_path, indexes_root); !rel.empty()) {
        return fs::absolute(root / fs::path(rel.string() + ".d"));
    }

    // Derive backend env from public CDX container filename only.
    // Example:
    //   data\indexes\students.cdx
    // -> data\lmdb\students.cdx.d
    fs::path name = public_cdx_path.filename();
    if (name.empty()) {
        name = fs::path("table.cdx");
    }

    return fs::absolute(root / fs::path(name.string() + ".d"));
}

// AIF-145 R-a. Before this, ladder 2 could not do ERSATZ's job and therefore
// could not replace it. Two capabilities were missing, both transcribed from
// cmd_ersatz.cpp:588-612, which was the only implementation that had them:
//
// (1) AN EMPTY NAME MEANS "default". ERSATZ has always done this.
//
// (2) THE EXTENSION IS THE OUTER LOOP, and the order is load-bearing. A posture
//     may be `.dtschema` or `.dtschemas`. `.dtschema` is tried across EVERY
//     root before `.dtschemas` is tried anywhere, so a `.dtschemas` sitting on
//     a user rung does NOT beat a `.dtschema` in data. Inverting those loops
//     would silently change which file a name resolves to, which is the whole
//     defect this consolidation exists to end -- so the loop order is stated
//     here rather than left to be inferred from the nesting.
//
// A token that already carries an extension is taken as given, exactly as
// before, and no extension is appended.
//
// This function still has NO CALLERS. Building the capability and switching the
// callers are separate commits on purpose: the first cannot change behaviour,
// and the second changes it observably.
fs::path resolve_workspace(const std::string& token)
{
    std::string target = token;
    {
        const auto b = target.find_first_not_of(" \t\r\n");
        const auto e = target.find_last_not_of(" \t\r\n");
        target = (b == std::string::npos) ? std::string() : target.substr(b, e - b + 1);
    }
    if (target.empty())
        target = "default";

    if (fs::path(target).has_extension())
        return resolve_in_search_roots(target, workspace_search_roots());

    for (const char* ext : {".dtschema", ".dtschemas"}) {
        fs::path found = find_in_search_roots(target, workspace_search_roots(), ext);
        if (!found.empty())
            return found;
    }

    // Nothing exists under either extension. Name the conventional location,
    // which is the first search root under the primary extension -- the same
    // shape of answer resolve_in_search_roots gives, and the same one ERSATZ's
    // fallback_in_current_user_root gave.
    return resolve_in_search_roots(target, workspace_search_roots(), ".dtschema");
}

fs::path resolve_test(const std::string& token)
{
    const fs::path root = get_slot(Slot::TESTS);
    const fs::path p = resolve_in_slot(root, token);
    return ensure_ext(p, ".dts");
}

fs::path resolve_schema(const std::string& token)
{
    const fs::path root = get_slot(Slot::SCHEMAS);
    return resolve_in_slot(root, token);
}

fs::path resolve_script(const std::string& token)
{
    return resolve_in_search_roots(token, script_search_roots());
}

fs::path resolve_project(const std::string& token)
{
    const fs::path root = get_slot(Slot::PROJECTS);
    return resolve_in_slot(root, token);
}

} // namespace dottalk::paths
