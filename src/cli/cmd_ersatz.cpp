// src/cli/cmd_ersatz.cpp
#include "cli/cmd_ersatz.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <system_error>
#include <unordered_map>
#include <vector>

#include "browser/browser.hpp"
#include "browser/browser_session.hpp"
#include "colors.hpp"
#include "common/path_state.hpp"
#include "db_tuple_stream.hpp"
#include "cli/order_state.hpp"
#include "textio.hpp"
#include "xbase.hpp"

// Real WORKSPACE command entry point
void cmd_WORKSPACE(xbase::DbArea& current, std::istringstream& in);

// Exported by cmd_workspace.cpp
std::string workspace_last_loaded_file();

namespace fs = std::filesystem;

namespace
{
    static std::string trim(const std::string& s)
    {
        return textio::trim(s);
    }

    static std::string upper_copy(const std::string& s)
    {
        return textio::up(s);
    }

    static std::string current_area_name(xbase::DbArea& area)
    {
        try {
            const std::string ln = area.logicalName();
            if (!ln.empty())
                return ln;
        } catch (...) {}

        try {
            const std::string nm = area.name();
            if (!nm.empty())
                return nm;
        } catch (...) {}

        return "";
    }

    struct ErsatzOrderInfo
    {
        bool active = false;
        bool ascending = true;
        std::string backend;
        std::string container;
        std::string tag;
    };

    static ErsatzOrderInfo current_order_info(xbase::DbArea& area)
    {
        ErsatzOrderInfo info{};

        try {
            if (!orderstate::hasOrder(area))
                return info;

            info.active = true;
            info.ascending = orderstate::isAscending(area);
            info.container = orderstate::orderName(area);
            info.tag = orderstate::activeTag(area);

            if (orderstate::isCdx(area))
                info.backend = "CDX/LMDB";
            else if (orderstate::isCnx(area))
                info.backend = "CNX";
            else
                info.backend = "INX";
        }
        catch (...) {
            info = ErsatzOrderInfo{};
        }

        return info;
    }

    static std::string order_info_line(xbase::DbArea& area)
    {
        const ErsatzOrderInfo info = current_order_info(area);
        if (!info.active)
            return "physical";

        std::ostringstream oss;
        oss << info.backend;
        if (!info.container.empty())
            oss << " file=" << info.container;
        if (!info.tag.empty())
            oss << " tag=" << info.tag;
        oss << (info.ascending ? " ASC" : " DESC");
        return oss.str();
    }

    static void print_order_overlay(xbase::DbArea& area)
    {
        std::cout << "; ERSATZ ACTIVE ORDER: " << order_info_line(area) << "\n";
    }

    static long ersatz_recno_safe(xbase::DbArea& area);

    static bool ersatz_read_current_safe(xbase::DbArea& area)
    {
        try {
            (void)area.readCurrent();
            return true;
        } catch (...) {
            return false;
        }
    }

    static bool ersatz_top(xbase::DbArea& area)
    {
        try {
            if (orderstate::hasOrder(area)) {
                // Logical TOP: move to the first root record in the active
                // order vector (CDX/LMDB, CNX, or INX), not physical recno 1.
                dottalk::DbTupleStream nav("*");
                nav.top();
                nav.skip(1);
                return ersatz_read_current_safe(area);
            }

            area.top();
            return ersatz_read_current_safe(area);
        } catch (...) {
            return false;
        }
    }

    static bool ersatz_bottom(xbase::DbArea& area)
    {
        try {
            if (orderstate::hasOrder(area)) {
                // Logical BOTTOM: move to the last root record in the active
                // order vector. DbTupleStream already knows how to materialize
                // CNX/CDX/INX record vectors and honor ASC/DESC.
                dottalk::DbTupleStream nav("*");
                nav.bottom();
                return ersatz_read_current_safe(area);
            }

            area.bottom();
            return ersatz_read_current_safe(area);
        } catch (...) {
            return false;
        }
    }

    static bool ersatz_skip(xbase::DbArea& area, long n)
    {
        try {
            if (n == 0)
                return ersatz_read_current_safe(area);

            if (orderstate::hasOrder(area)) {
                // Logical SKIP/NEXT/PREV: anchor the stream at the current
                // physical recno, map that record into the active ordered
                // vector, then move by n logical positions. This preserves
                // full relational expansion while making the root cursor obey
                // SET ORDER / ASCEND / DESCEND.
                const long saved = ersatz_recno_safe(area);
                dottalk::DbTupleStream nav("*");
                if (saved > 0)
                    (void)nav.goto_recno(saved);
                nav.skip(n);
                return ersatz_read_current_safe(area);
            }

            area.skip(n);
            return ersatz_read_current_safe(area);
        } catch (...) {
            return false;
        }
    }

    static long ersatz_recno_safe(xbase::DbArea& area)
    {
        try {
            return static_cast<long>(area.recno());
        } catch (...) {
            return 0;
        }
    }

    static void render_snapshot_console_order_aware(xbase::DbArea& area,
                                                    const browser::BrowserSnapshot& snap)
    {
        // browser::render_browser_snapshot_console() still owns the canonical
        // browser layout, but its BrowserSnapshot order field is currently
        // populated independently of the live command order state. Capture the
        // renderer output and replace only the stale public ORDER line so
        // ERSATZ reports the same active order as LIST/SMARTLIST/WORKSPACE.
        std::ostringstream captured;
        std::streambuf* const old_buf = std::cout.rdbuf(captured.rdbuf());

        try
        {
            browser::render_browser_snapshot_console(snap);
        }
        catch (...)
        {
            std::cout.rdbuf(old_buf);
            throw;
        }

        std::cout.rdbuf(old_buf);

        std::istringstream lines(captured.str());
        std::string line;
        const std::string replacement = "ORDER: " + order_info_line(area);

        while (std::getline(lines, line))
        {
            if (line == "ORDER: physical")
                std::cout << replacement << "\n";
            else
                std::cout << line << "\n";
        }
    }

    static bool has_any_sep(const std::string& s)
    {
        return s.find('/') != std::string::npos || s.find('\\') != std::string::npos;
    }

    static std::vector<std::string> split_path_tokens(const std::string& raw)
    {
        std::vector<std::string> out;

        std::string normalized = raw;
        for (;;)
        {
            const std::size_t pos = normalized.find("->");
            if (pos == std::string::npos)
                break;
            normalized.replace(pos, 2, ",");
        }

        std::stringstream ss(normalized);
        std::string token;
        while (std::getline(ss, token, ','))
        {
            token = trim(token);
            if (!token.empty())
                out.push_back(token);
        }

        return out;
    }

    static fs::path app_root()
    {
        return dottalk::paths::state().data_root.parent_path();
    }

    static fs::path data_workspaces_root()
    {
        return dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES);
    }

    static fs::path data_scripts_root()
    {
        return dottalk::paths::get_slot(dottalk::paths::Slot::SCRIPTS);
    }

    static fs::path user_root_base()
    {
        return app_root() / "user";
    }

    static std::string current_profile_name()
    {
        // Replace later with real authenticated user selection.
        return "default";
    }

    static fs::path profile_root(const std::string& profile_name)
    {
        const std::string name = trim(profile_name).empty() ? "default" : trim(profile_name);
        return user_root_base() / name;
    }

    static fs::path current_user_root()
    {
        return profile_root(current_profile_name());
    }

    static fs::path public_root()
    {
        return profile_root("public");
    }

    static fs::path default_root()
    {
        return profile_root("default");
    }

    static fs::path current_user_workspaces_root()
    {
        return current_user_root() / "workspaces";
    }

    static fs::path public_workspaces_root()
    {
        return public_root() / "workspaces";
    }

    static fs::path default_workspaces_root()
    {
        return default_root() / "workspaces";
    }

    static fs::path current_user_scripts_root()
    {
        return current_user_root() / "scripts";
    }

    static fs::path public_scripts_root()
    {
        return public_root() / "scripts";
    }

    static fs::path default_scripts_root()
    {
        return default_root() / "scripts";
    }

    static std::vector<fs::path> workspace_search_roots()
    {
        return {
            current_user_workspaces_root(),
            public_workspaces_root(),
            default_workspaces_root(),
            data_workspaces_root()
        };
    }

    static std::vector<fs::path> script_search_roots()
    {
        return {
            current_user_scripts_root(),
            public_scripts_root(),
            default_scripts_root(),
            data_scripts_root()
        };
    }

    static bool file_exists(const fs::path& p)
    {
        std::error_code ec;
        return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
    }

    static fs::path absolute_if_exists(const fs::path& p)
    {
        std::error_code ec;
        if (file_exists(p))
            return fs::absolute(p, ec);
        return {};
    }

    static fs::path resolve_in_roots(const std::string& target_in,
                                     const std::vector<fs::path>& roots,
                                     const std::string& default_ext)
    {
        std::string target = trim(target_in);
        fs::path p(target);

        if (!default_ext.empty() && !p.has_extension())
            p.replace_extension(default_ext);

        if (p.is_absolute())
        {
            fs::path abs = absolute_if_exists(p);
            if (!abs.empty())
                return abs;
            return {};
        }

        {
            fs::path abs = absolute_if_exists(p);
            if (!abs.empty())
                return abs;
        }

        if (has_any_sep(target))
        {
            fs::path data_relative = dottalk::paths::state().data_root / p;
            fs::path abs = absolute_if_exists(data_relative);
            if (!abs.empty())
                return abs;

            abs = absolute_if_exists(p);
            if (!abs.empty())
                return abs;
        }

        for (const auto& root : roots)
        {
            fs::path candidate = root / p;
            fs::path abs = absolute_if_exists(candidate);
            if (!abs.empty())
                return abs;
        }

        return {};
    }

    static fs::path fallback_in_current_user_root(const std::string& target_in,
                                                  const fs::path& root,
                                                  const std::string& default_ext)
    {
        std::string target = trim(target_in);
        if (target.empty())
            target = "default";

        fs::path p(target);
        if (!default_ext.empty() && !p.has_extension())
            p.replace_extension(default_ext);

        return root / p;
    }

    static fs::path resolve_ersatz_file_path(const std::string& target_in)
    {
        const std::string target = trim(target_in).empty() ? "default" : trim(target_in);
        fs::path found = resolve_in_roots(target, workspace_search_roots(), ".erz");
        if (!found.empty())
            return found;

        return fallback_in_current_user_root(target, current_user_workspaces_root(), ".erz");
    }

    static fs::path resolve_workspace_target(const std::string& target_in)
    {
        const std::string target = trim(target_in).empty() ? "default" : trim(target_in);
        fs::path found = resolve_in_roots(target, workspace_search_roots(), ".dtschema");
        if (!found.empty())
            return found;

        return fallback_in_current_user_root(target, current_user_workspaces_root(), ".dtschema");
    }

    static fs::path resolve_script_target(const std::string& target_in)
    {
        const std::string target = trim(target_in).empty() ? "default" : trim(target_in);
        fs::path found = resolve_in_roots(target, script_search_roots(), ".dot");
        if (!found.empty())
            return found;

        return fallback_in_current_user_root(target, current_user_scripts_root(), ".dot");
    }

    static bool looks_like_workspace_or_script_file(const fs::path& p)
    {
        const std::string ext = upper_copy(p.extension().string());
        return ext == ".DTSCHEMA" || ext == ".INI" || ext == ".DOT";
    }

    static bool handoff_to_workspace(xbase::DbArea& area,
                                     const std::string& target,
                                     std::string& status)
    {
        const fs::path resolved = resolve_workspace_target(target);
        const std::string before = workspace_last_loaded_file();

        try
        {
            std::istringstream ss("LOAD " + resolved.string());
            cmd_WORKSPACE(area, ss);
        }
        catch (const std::exception& ex)
        {
            status = std::string("workspace load failed: ") + ex.what();
            return false;
        }
        catch (...)
        {
            status = "workspace load failed";
            return false;
        }

        const std::string after = workspace_last_loaded_file();
        if (after.empty() || after == before)
        {
            status = "workspace load failed: " + resolved.string();
            return false;
        }

        browser::reset_session();
        status = "workspace loaded: " + after;
        return true;
    }

    static bool load_ersatz_file(xbase::DbArea& area,
                                 const std::string& target,
                                 std::string& status)
    {
        const std::string trimmed_target = trim(target);

        // ERSATZ LOAD owns .erz browser-session files only.  Keep the older
        // script resolver wired into this guard so a user-supplied .dot path
        // is resolved through the proper script roots before we reject it.
        // That preserves the script lookup behavior instead of letting .dot
        // names fall through the workspace/.erz path.
        {
            fs::path requested(trimmed_target);
            const std::string ext = upper_copy(requested.extension().string());
            if (ext == ".DOT")
            {
                const fs::path script_path = resolve_script_target(trimmed_target);
                status = "expected .erz file, not script file " + script_path.string() +
                         " (run scripts through DO/DOTSCRIPT)";
                return false;
            }
        }

        const fs::path erz_path = resolve_ersatz_file_path(trimmed_target);

        if (looks_like_workspace_or_script_file(erz_path))
        {
            const std::string ext = upper_copy(erz_path.extension().string());
            if (ext == ".DTSCHEMA")
            {
                status = "expected .erz file, not " + erz_path.string() +
                         " (use ERSATZ WLOAD for .dtschema)";
            }
            else if (ext == ".DOT")
            {
                const fs::path script_path = resolve_script_target(erz_path.string());
                status = "expected .erz file, not script file " + script_path.string() +
                         " (run scripts through DO/DOTSCRIPT)";
            }
            else
            {
                status = "expected .erz file, not " + erz_path.string();
            }
            return false;
        }

        std::ifstream in(erz_path);
        if (!in)
        {
            status = "cannot open file: " + erz_path.string();
            return false;
        }

        std::string workspace;
        std::string root;
        int limit = browser::limit();
        std::vector<std::string> path_list;

        bool saw_workspace = false;
        bool saw_root = false;
        bool saw_limit = false;
        bool saw_path = false;

        std::string line;
        while (std::getline(in, line))
        {
            line = trim(line);
            if (line.empty() || line[0] == ';' || line[0] == '#')
                continue;

            const auto eq = line.find('=');
            if (eq == std::string::npos)
                continue;

            const std::string key = upper_copy(trim(line.substr(0, eq)));
            const std::string val = trim(line.substr(eq + 1));

            if (key == "WORKSPACE") { workspace = val; saw_workspace = true; }
            else if (key == "ROOT") { root = val; saw_root = true; }
            else if (key == "LIMIT") { limit = std::stoi(val); saw_limit = true; }
            else if (key == "PATH") { path_list = split_path_tokens(val); saw_path = true; }
        }

        browser::reset_session();

        if (saw_workspace)
        {
            std::string ws_status;
            if (!handoff_to_workspace(area, workspace, ws_status))
            {
                status = ws_status;
                return false;
            }
        }

        if (saw_root)
        {
            if (upper_copy(root) == "USER")
                browser::ensure_session_root(current_area_name(area));
            else
                browser::set_root_alias(root);
        }
        else
        {
            browser::ensure_session_root(current_area_name(area));
        }

        if (saw_limit)
            browser::set_limit(limit);

        if (saw_path)
        {
            browser::clear_path();
            for (const auto& p : path_list)
                browser::push_path_alias(p);
        }

        std::ostringstream oss;
        oss << "loaded " << erz_path.string();
        if (saw_workspace) oss << " WORKSPACE=" << workspace;
        if (saw_root) oss << " ROOT=" << (upper_copy(root) == "USER" ? browser::root_alias() : root);
        if (saw_limit) oss << " LIMIT=" << browser::limit();
        if (saw_path) oss << " PATH=" << browser::path_string();
        status = oss.str();
        return true;
    }

    static bool save_ersatz_file(const std::string& target, std::string& status)
    {
        fs::path out_path = resolve_ersatz_file_path(target);

        std::error_code ec;
        if (out_path.has_parent_path() && !out_path.parent_path().empty())
            fs::create_directories(out_path.parent_path(), ec);

        std::ofstream out(out_path);
        if (!out)
        {
            status = "cannot write file: " + out_path.string();
            return false;
        }

        const std::string ws = workspace_last_loaded_file();
        if (!ws.empty())
            out << "WORKSPACE=" << ws << "\n";

        const std::string root = browser::root_alias();
        if (!root.empty())
            out << "ROOT=" << root << "\n";
        else
            out << "ROOT=USER\n";

        out << "LIMIT=" << browser::limit() << "\n";

        const std::string path = browser::path_string();
        if (!path.empty() && path != "(none)")
            out << "PATH=" << path << "\n";

        out.flush();
        status = "saved " + out_path.string();
        return true;
    }

    static void print_help()
    {
        std::cout
            << "ERSATZ syntax\n"
            << "  ERSATZ                 show full browser snapshot using saved path/root\n"
            << "  ERSATZ SHOW            same as ERSATZ\n"
            << "  ERSATZ TREE            show only relation tree\n"
            << "  ERSATZ GRID            show only tuple grid + summary\n"
            << "  ERSATZ STATUS          show current ERSATZ session state\n"
            << "  ERSATZ ORDER           show active root-table order used by ERSATZ\n"
            << "  ERSATZ TOP             move root to first record in active order and show\n"
            << "  ERSATZ BOTTOM          move root to last record in active order and show\n"
            << "  ERSATZ NEXT [n]        move root forward n record(s) in active order and show\n"
            << "  ERSATZ PREV [n]        move root backward n record(s) in active order and show\n"
            << "  ERSATZ SKIP <n>        move root by signed n in active order and show\n"
            << "  ERSATZ ROOT [alias]    set/show browser root alias\n"
            << "  ERSATZ OPEN <alias>    push one child alias onto the path\n"
            << "  ERSATZ BACK            pop one alias from the path\n"
            << "  ERSATZ PATH            show current path\n"
            << "  ERSATZ CLEARPATH       clear current path\n"
            << "  ERSATZ LIMIT <n>       set row limit\n"
            << "  ERSATZ LOAD [name]     load current/public/default/data workspaces\\name.erz\n"
            << "  ERSATZ SAVE [name]     save current-user workspaces\\name.erz\n"
            << "  ERSATZ WLOAD [name]    load current/public/default/data workspaces\\name.dtschema\n"
            << "  ERSATZ DELTA MARK [name] [LIMIT n]  capture current tuple stream baseline\n"
            << "  ERSATZ DELTA SHOW [name] [LIMIT n]  compare current tuple stream to baseline\n"
            << "  ERSATZ DELTA CLEAR [name|ALL]       clear saved tuple baseline(s)\n"
            << "  ERSATZ DELTA STATUS                 list saved tuple baselines\n"
            << "  ERSATZ REFRESH         rebuild using current root record position\n"
            << "  ERSATZ RESET           clear saved ERSATZ state\n"
            << "  ERSATZ HELP\n";
    }

    static void print_session_status(xbase::DbArea& area)
    {
        browser::ensure_session_root(current_area_name(area));

        std::cout << "ERSATZ STATUS\n";
        std::cout << "  PROFILE       : " << current_profile_name() << "\n";
        std::cout << "  ROOT          : "
                  << (browser::root_alias().empty() ? "(none)" : browser::root_alias())
                  << "\n";
        std::cout << "  LIMIT         : " << browser::limit() << "\n";
        std::cout << "  PATH          : " << browser::path_string() << "\n";
        std::cout << "  ACTIVE ORDER  : " << order_info_line(area) << "\n";
        std::cout << "  USER WORK     : " << current_user_workspaces_root().string() << "\n";
        std::cout << "  PUBLIC WORK   : " << public_workspaces_root().string() << "\n";
        std::cout << "  DEFAULT WORK  : " << default_workspaces_root().string() << "\n";
        std::cout << "  DATA WORK     : " << data_workspaces_root().string() << "\n";
        std::cout << "  USER SCRIPT   : " << current_user_scripts_root().string() << "\n";
        std::cout << "  PUBLIC SCRIPT : " << public_scripts_root().string() << "\n";
        std::cout << "  DEFAULT SCRIPT: " << default_scripts_root().string() << "\n";
        std::cout << "  DATA SCRIPT   : " << data_scripts_root().string() << "\n";
    }

    static bool build_snapshot_from_session(xbase::DbArea& area,
                                            browser::BrowserSnapshot& snap)
    {
        browser::ensure_session_root(current_area_name(area));

        browser::BrowserRequest req{};
        req.root_alias = browser::root_alias();
        req.path_aliases = browser::path();
        req.limit = browser::limit();
        req.refresh_only = true;

        return browser::build_browser_snapshot(area, req, snap);
    }

    static void render_tree_only(const browser::BrowserSnapshot& snap)
    {
        using namespace dli::colors;

        std::cout << "ERSATZ TREE\n";
        std::cout << "ROOT: "
                  << (snap.root.alias.empty() ? "(none)" : snap.root.alias)
                  << "\n";
        std::cout << "PATH: ";
        if (snap.path_aliases.empty())
        {
            std::cout << "(none)\n\n";
        }
        else
        {
            for (std::size_t i = 0; i < snap.path_aliases.size(); ++i)
            {
                if (i) std::cout << " -> ";
                std::cout << snap.path_aliases[i];
            }
            std::cout << "\n\n";
        }

        std::cout << "RELATION TREE\n";
        if (snap.relation_tree.root_alias.empty())
        {
            std::cout << "  (none)\n";
            return;
        }

        std::function<void(const browser::RelationNode&, int)> walk;
        walk = [&](const browser::RelationNode& node, int depth)
        {
            std::string indent(static_cast<std::size_t>(depth * 3), ' ');

            if (treeColorEnabled())
                emitTheme(treeThemeForLevel(depth));

            std::cout << indent << "-> " << node.child_alias;

            if (treeColorEnabled())
                emitCurrentTheme();

            if (!node.on_expr.empty())
            {
                std::cout << "   ON ";

                if (treeColorEnabled())
                    emitTheme(treeThemeForLevel(depth));

                std::cout << node.on_expr;

                if (treeColorEnabled())
                    emitCurrentTheme();
            }
            std::cout << "\n";

            for (const auto& c : node.children)
                walk(c, depth + 1);
        };

        if (treeColorEnabled())
            emitTheme(treeThemeForLevel(0));

        std::cout << "  " << snap.relation_tree.root_alias << "\n";

        if (treeColorEnabled())
            emitCurrentTheme();

        if (snap.relation_tree.links.empty())
        {
            std::cout << "  (none)\n";
            return;
        }

        for (const auto& link : snap.relation_tree.links)
            walk(link, 1);
    }

    static void render_grid_only(const browser::BrowserSnapshot& snap)
    {
        browser::BrowserSnapshot mini = snap;
        mini.root = browser::RecordSnapshot{};
        mini.relation_tree = browser::RelationTreeSnapshot{};
        mini.order = browser::OrderSnapshot{};
        mini.command_name = "ERSATZ GRID";
        browser::render_browser_snapshot_console(mini);
    }

    static bool current_tree_contains_child(const std::vector<browser::RelationNode>& nodes,
                                            const std::string& alias_upper)
    {
        for (const auto& n : nodes)
        {
            if (upper_copy(n.child_alias) == alias_upper)
                return true;
        }
        return false;
    }

    static bool validate_next_alias_against_current_tree(xbase::DbArea& area,
                                                         const std::string& alias)
    {
        browser::BrowserSnapshot snap{};
        if (!build_snapshot_from_session(area, snap))
            return false;

        const std::string want = upper_copy(alias);

        if (browser::path().empty())
            return current_tree_contains_child(snap.relation_tree.links, want);

        const std::vector<browser::RelationNode>* level = &snap.relation_tree.links;

        for (const auto& p : browser::path())
        {
            const browser::RelationNode* found = nullptr;
            for (const auto& n : *level)
            {
                if (upper_copy(n.child_alias) == upper_copy(p))
                {
                    found = &n;
                    break;
                }
            }

            if (!found)
                return false;

            level = &found->children;
        }

        return current_tree_contains_child(*level, want);
    }


    // -----------------------------------------------------------------
    // ERSATZ tupledelta support
    //
    // cmd_tupledelta.cpp currently keeps its engine private and its stream
    // loader is still a stub. ERSATZ therefore carries a small local delta
    // adapter over the live DbTupleStream. When tupledelta is promoted to a
    // shared library, this block can be replaced by calls into that library.
    // -----------------------------------------------------------------

    struct ErsatzDeltaRow
    {
        std::string key;
        dottalk::TupleRow row;
    };

    using ErsatzDeltaMap = std::map<std::string, ErsatzDeltaRow>;

    enum class ErsatzDeltaKind
    {
        Insert,
        Delete,
        Update
    };

    struct ErsatzDelta
    {
        ErsatzDeltaKind kind = ErsatzDeltaKind::Update;
        std::string key;
        dottalk::TupleRow before;
        dottalk::TupleRow after;
    };

    struct ErsatzDeltaBaseline
    {
        std::string name;
        std::string table;
        std::string spec;
        int area_slot = -1;
        int saved_recno = 0;
        std::size_t rows = 0;
        ErsatzDeltaMap map;
    };

    static std::unordered_map<std::string, ErsatzDeltaBaseline>& delta_store()
    {
        static std::unordered_map<std::string, ErsatzDeltaBaseline> s_store;
        return s_store;
    }

    static std::string default_delta_name(xbase::DbArea& area)
    {
        std::string n = current_area_name(area);
        if (trim(n).empty())
            n = "DEFAULT";
        return upper_copy(n);
    }

    static int safe_area_recno(xbase::DbArea& area)
    {
        try { return static_cast<int>(area.recno()); } catch (...) { return 0; }
    }

    static int tuple_row_recno(const dottalk::TupleRow& row)
    {
        for (const auto& f : row.fragments)
        {
            if (f.recno > 0)
                return f.recno;
        }
        return 0;
    }

    static std::string tuple_identity_key(const dottalk::TupleRow& row)
    {
        // Preferred identity for now: first tuple value. In current DotTalk++
        // tables this is normally SID/TID/etc. Once PRIMARY UNIQUE metadata is
        // surfaced to tuple_builder, this should switch to that field.
        if (!row.values.empty() && !trim(row.values.front()).empty())
            return trim(row.values.front());

        const int rn = tuple_row_recno(row);
        if (rn > 0)
            return "RECNO:" + std::to_string(rn);

        return "ROW:";
    }

    static bool same_tuple_payload(const dottalk::TupleRow& a,
                                   const dottalk::TupleRow& b)
    {
        return a.values == b.values;
    }

    static std::string tuple_summary(const dottalk::TupleRow& row)
    {
        std::ostringstream oss;
        const int rn = tuple_row_recno(row);
        if (rn > 0)
            oss << "RECNO=" << rn;
        else
            oss << "RECNO=?";

        const std::size_t n = row.values.size();
        for (std::size_t i = 0; i < n; ++i)
        {
            std::string name;
            if (i < row.columns.size())
                name = row.columns[i].name;
            if (name.empty())
                name = "F" + std::to_string(i + 1);
            oss << " | " << name << "=" << row.values[i];
        }
        return oss.str();
    }

    static void print_field_level_delta(const dottalk::TupleRow& before,
                                        const dottalk::TupleRow& after)
    {
        const std::size_t n = std::max(before.values.size(), after.values.size());
        for (std::size_t i = 0; i < n; ++i)
        {
            const std::string b = (i < before.values.size()) ? before.values[i] : std::string{};
            const std::string a = (i < after.values.size())  ? after.values[i]  : std::string{};
            if (b == a)
                continue;

            std::string name;
            if (i < after.columns.size())
                name = after.columns[i].name;
            else if (i < before.columns.size())
                name = before.columns[i].name;
            if (name.empty())
                name = "F" + std::to_string(i + 1);

            std::cout << "    " << name << ": [" << b << "] -> [" << a << "]\n";
        }
    }

    static std::vector<ErsatzDelta> compute_tuple_delta(const ErsatzDeltaMap& baseline,
                                                        const ErsatzDeltaMap& current)
    {
        std::vector<ErsatzDelta> out;

        for (const auto& kv : baseline)
        {
            const auto it = current.find(kv.first);
            if (it == current.end())
            {
                ErsatzDelta d;
                d.kind = ErsatzDeltaKind::Delete;
                d.key = kv.first;
                d.before = kv.second.row;
                out.push_back(std::move(d));
                continue;
            }

            if (!same_tuple_payload(kv.second.row, it->second.row))
            {
                ErsatzDelta d;
                d.kind = ErsatzDeltaKind::Update;
                d.key = kv.first;
                d.before = kv.second.row;
                d.after = it->second.row;
                out.push_back(std::move(d));
            }
        }

        for (const auto& kv : current)
        {
            if (baseline.find(kv.first) != baseline.end())
                continue;

            ErsatzDelta d;
            d.kind = ErsatzDeltaKind::Insert;
            d.key = kv.first;
            d.after = kv.second.row;
            out.push_back(std::move(d));
        }

        return out;
    }

    static ErsatzDeltaMap capture_current_tuple_map(xbase::DbArea& area,
                                                    const std::string& spec,
                                                    std::size_t limit)
    {
        ErsatzDeltaMap out;

        const int old_recno = safe_area_recno(area);

        dottalk::DbTupleStream stream(spec.empty() ? "*" : spec, "ERSATZ DELTA");
        stream.top();

        const std::size_t page_size = 64;
        std::size_t consumed = 0;

        while (limit == 0 || consumed < limit)
        {
            const std::size_t want = (limit == 0)
                ? page_size
                : std::min(page_size, limit - consumed);

            if (want == 0)
                break;

            std::vector<dottalk::TupleRow> page = stream.next_page(want);
            if (page.empty())
                break;

            for (auto& row : page)
            {
                const std::string key = tuple_identity_key(row);
                ErsatzDeltaRow dr;
                dr.key = key;
                dr.row = std::move(row);
                out[key] = std::move(dr);
                ++consumed;

                if (limit != 0 && consumed >= limit)
                    break;
            }
        }

        if (old_recno > 0)
        {
            try {
                area.gotoRec(static_cast<std::size_t>(old_recno));
                (void)area.readCurrent();
            } catch (...) {}
        }

        return out;
    }

    static bool parse_limit_token(std::istringstream& iss, std::size_t& limit)
    {
        std::string tok;
        if (!(iss >> tok))
            return false;

        tok = upper_copy(tok);
        if (tok != "LIMIT")
            return false;

        int n = 0;
        if (!(iss >> n))
        {
            std::cout << "ERSATZ DELTA: LIMIT requires a number.\n";
            limit = 0;
            return true;
        }

        limit = (n <= 0) ? 0u : static_cast<std::size_t>(n);
        return true;
    }

    static void print_delta_help()
    {
        std::cout
            << "ERSATZ DELTA syntax\n"
            << "  ERSATZ DELTA MARK [name] [LIMIT n]   capture current tuple stream baseline\n"
            << "  ERSATZ DELTA SHOW [name] [LIMIT n]   compare current tuple stream to baseline\n"
            << "  ERSATZ DELTA [name] [LIMIT n]        same as SHOW\n"
            << "  ERSATZ DELTA CLEAR [name|ALL]        clear saved baseline(s)\n"
            << "  ERSATZ DELTA STATUS                  list saved baselines\n"
            << "\n"
            << "Notes:\n"
            << "  Baselines are in-memory and session-local.\n"
            << "  Identity currently uses the first tuple value, falling back to RECNO.\n"
            << "  The tuple stream respects active order because it uses DbTupleStream.\n";
    }

    static void handle_delta_command(xbase::DbArea& area,
                                     std::istringstream& iss)
    {
        std::string action;
        if (!(iss >> action))
            action = "SHOW";
        action = upper_copy(trim(action));

        if (action == "HELP" || action == "?")
        {
            print_delta_help();
            return;
        }

        if (action == "STATUS")
        {
            std::cout << "ERSATZ DELTA STATUS\n";
            if (delta_store().empty())
            {
                std::cout << "  (no baselines)\n";
                return;
            }

            for (const auto& kv : delta_store())
            {
                const auto& b = kv.second;
                std::cout << "  " << b.name
                          << " table=" << b.table
                          << " area=" << b.area_slot
                          << " rows=" << b.rows
                          << " spec=" << b.spec
                          << "\n";
            }
            return;
        }

        if (action == "CLEAR")
        {
            std::string name;
            if (!(iss >> name))
                name = default_delta_name(area);
            name = upper_copy(trim(name));

            if (name == "ALL")
            {
                delta_store().clear();
                std::cout << "ERSATZ DELTA: all baselines cleared.\n";
                return;
            }

            const auto n = delta_store().erase(name);
            std::cout << "ERSATZ DELTA: "
                      << (n ? "cleared " : "no such baseline ")
                      << name << ".\n";
            return;
        }

        bool mark = false;
        bool show = false;
        std::string name;

        if (action == "MARK" || action == "BASELINE" || action == "SNAP" || action == "SNAPSHOT")
        {
            mark = true;
            if (!(iss >> name))
                name = default_delta_name(area);
        }
        else if (action == "SHOW" || action == "DIFF" || action == "COMPARE")
        {
            show = true;
            if (!(iss >> name))
                name = default_delta_name(area);
        }
        else
        {
            // ERSATZ DELTA <name> is shorthand for SHOW <name>.
            show = true;
            name = action;
        }

        name = upper_copy(trim(name));
        if (name.empty())
            name = default_delta_name(area);

        std::size_t limit = 0;
        (void)parse_limit_token(iss, limit);

        const std::string spec = "*";
        const std::string table = current_area_name(area);
        const int area_slot = -1; // current work area; avoid depending on workareas.hpp here.

        if (mark)
        {
            ErsatzDeltaBaseline b;
            b.name = name;
            b.table = table;
            b.spec = spec;
            b.area_slot = area_slot;
            b.saved_recno = safe_area_recno(area);
            b.map = capture_current_tuple_map(area, spec, limit);
            b.rows = b.map.size();

            delta_store()[name] = std::move(b);

            std::cout << "ERSATZ DELTA: baseline " << name
                      << " captured rows=" << delta_store()[name].rows
                      << " table=" << table;
            if (limit != 0)
                std::cout << " limit=" << limit;
            std::cout << ".\n";
            return;
        }

        if (show)
        {
            const auto it = delta_store().find(name);
            if (it == delta_store().end())
            {
                std::cout << "ERSATZ DELTA: no baseline named " << name
                          << ". Use ERSATZ DELTA MARK " << name << " first.\n";
                return;
            }

            ErsatzDeltaMap current = capture_current_tuple_map(area, it->second.spec, limit);
            const std::vector<ErsatzDelta> deltas = compute_tuple_delta(it->second.map, current);

            std::cout << "ERSATZ DELTA: " << name
                      << " table=" << table
                      << " baseline_rows=" << it->second.rows
                      << " current_rows=" << current.size()
                      << " changes=" << deltas.size()
                      << "\n";

            if (deltas.empty())
            {
                std::cout << "No tuple changes.\n";
                return;
            }

            for (const auto& d : deltas)
            {
                switch (d.kind)
                {
                    case ErsatzDeltaKind::Insert:
                        std::cout << "+ INSERT " << d.key << "  " << tuple_summary(d.after) << "\n";
                        break;

                    case ErsatzDeltaKind::Delete:
                        std::cout << "- DELETE " << d.key << "  " << tuple_summary(d.before) << "\n";
                        break;

                    case ErsatzDeltaKind::Update:
                        std::cout << "~ UPDATE " << d.key << "\n";
                        print_field_level_delta(d.before, d.after);
                        break;
                }
            }
            return;
        }
    }

    static void render_current_ersatz_snapshot(xbase::DbArea& area,
                                               const std::string& mode)
    {
        browser::BrowserSnapshot snap{};
        if (!build_snapshot_from_session(area, snap))
        {
            if (!snap.warnings.empty())
            {
                for (const auto& w : snap.warnings)
                {
                    std::cout << "ERSATZ: " << w;
                    if (w.empty() || w.back() != '\n')
                        std::cout << "\n";
                }
            }
            else
            {
                std::cout << "ERSATZ: build failed";
                if (!snap.status.empty())
                    std::cout << " [" << snap.status << "]";
                std::cout << ".\n";
            }
            return;
        }

        if (mode == "TREE")
        {
            print_order_overlay(area);
            render_tree_only(snap);
            return;
        }

        if (mode == "GRID")
        {
            print_order_overlay(area);
            render_grid_only(snap);
            return;
        }

        print_order_overlay(area);
        render_snapshot_console_order_aware(area, snap);
    }

    static bool parse_optional_positive_count(std::istringstream& iss,
                                              long& count,
                                              const char* verb)
    {
        count = 1;

        std::string tok;
        if (!(iss >> tok))
            return true;

        try
        {
            std::size_t used = 0;
            const long n = std::stol(tok, &used, 10);
            if (used != tok.size() || n < 1)
            {
                std::cout << "ERSATZ: " << verb << " requires a positive count.\n";
                return false;
            }
            count = n;
            return true;
        }
        catch (...)
        {
            std::cout << "ERSATZ: " << verb << " requires a positive count.\n";
            return false;
        }
    }

    static bool parse_required_signed_count(std::istringstream& iss,
                                            long& count,
                                            const char* verb)
    {
        std::string tok;
        if (!(iss >> tok))
        {
            std::cout << "ERSATZ: " << verb << " requires a signed count.\n";
            return false;
        }

        try
        {
            std::size_t used = 0;
            const long n = std::stol(tok, &used, 10);
            if (used != tok.size())
            {
                std::cout << "ERSATZ: " << verb << " requires a signed count.\n";
                return false;
            }
            count = n;
            return true;
        }
        catch (...)
        {
            std::cout << "ERSATZ: " << verb << " requires a signed count.\n";
            return false;
        }
    }
}

void cmd_ERSATZ(xbase::DbArea& area, std::istringstream& iss)
{
    std::string sub;
    if (!(iss >> sub))
        sub = "SHOW";

    const std::string raw_sub = trim(sub);
    sub = upper_copy(raw_sub);

    if (sub == "HELP")
    {
        print_help();
        return;
    }

    if (sub == "RESET")
    {
        browser::reset_session();
        std::cout << "ERSATZ: session reset.\n";
        return;
    }

    if (sub == "STATUS")
    {
        print_session_status(area);
        return;
    }

    if (sub == "ORDER")
    {
        std::cout << "ERSATZ ORDER: " << order_info_line(area) << "\n";
        return;
    }

    if (sub == "TOP")
    {
        if (!area.isOpen())
        {
            std::cout << "ERSATZ TOP: no table open.\n";
            return;
        }

        if (!ersatz_top(area))
        {
            std::cout << "ERSATZ TOP: failed.\n";
            return;
        }

        std::cout << "ERSATZ TOP: recno " << ersatz_recno_safe(area)
                  << " (" << order_info_line(area) << ")\n";
        render_current_ersatz_snapshot(area, "SHOW");
        return;
    }

    if (sub == "BOTTOM")
    {
        if (!area.isOpen())
        {
            std::cout << "ERSATZ BOTTOM: no table open.\n";
            return;
        }

        if (!ersatz_bottom(area))
        {
            std::cout << "ERSATZ BOTTOM: failed.\n";
            return;
        }

        std::cout << "ERSATZ BOTTOM: recno " << ersatz_recno_safe(area)
                  << " (" << order_info_line(area) << ")\n";
        render_current_ersatz_snapshot(area, "SHOW");
        return;
    }

    if (sub == "NEXT" || sub == "PREV")
    {
        if (!area.isOpen())
        {
            std::cout << "ERSATZ " << sub << ": no table open.\n";
            return;
        }

        long count = 1;
        if (!parse_optional_positive_count(iss, count, sub.c_str()))
            return;

        const long delta = (sub == "PREV") ? -count : count;
        if (!ersatz_skip(area, delta))
        {
            std::cout << "ERSATZ " << sub << ": failed.\n";
            return;
        }

        std::cout << "ERSATZ " << sub << ": recno " << ersatz_recno_safe(area)
                  << " (" << order_info_line(area) << ")\n";
        render_current_ersatz_snapshot(area, "SHOW");
        return;
    }

    if (sub == "SKIP")
    {
        if (!area.isOpen())
        {
            std::cout << "ERSATZ SKIP: no table open.\n";
            return;
        }

        long delta = 0;
        if (!parse_required_signed_count(iss, delta, "SKIP"))
            return;

        if (!ersatz_skip(area, delta))
        {
            std::cout << "ERSATZ SKIP: failed.\n";
            return;
        }

        std::cout << "ERSATZ SKIP: recno " << ersatz_recno_safe(area)
                  << " (" << order_info_line(area) << ")\n";
        render_current_ersatz_snapshot(area, "SHOW");
        return;
    }

    if (sub == "ROOT")
    {
        std::string alias;
        if (!(iss >> alias))
        {
            browser::ensure_session_root(current_area_name(area));
            std::cout << "ERSATZ ROOT: " << browser::root_alias() << "\n";
            return;
        }

        if (upper_copy(alias) == "USER")
            browser::ensure_session_root(current_area_name(area));
        else
            browser::set_root_alias(alias);

        browser::clear_path();
        std::cout << "ERSATZ ROOT set to " << browser::root_alias() << ".\n";
        return;
    }

    if (sub == "LIMIT")
    {
        int n = 0;
        if (!(iss >> n))
        {
            std::cout << "ERSATZ: LIMIT requires a number.\n";
            return;
        }

        browser::set_limit(n);
        std::cout << "ERSATZ LIMIT set to " << browser::limit() << ".\n";
        return;
    }

    if (sub == "PATH")
    {
        browser::ensure_session_root(current_area_name(area));
        std::cout << "ERSATZ PATH: " << browser::path_string() << "\n";
        return;
    }

    if (sub == "CLEARPATH")
    {
        browser::clear_path();
        std::cout << "ERSATZ: path cleared.\n";
        return;
    }

    if (sub == "BACK")
    {
        if (!browser::pop_path_alias())
        {
            std::cout << "ERSATZ: path already empty.\n";
            return;
        }

        std::cout << "ERSATZ PATH: " << browser::path_string() << "\n";
        return;
    }

    if (sub == "OPEN")
    {
        std::string alias;
        if (!(iss >> alias))
        {
            std::cout << "ERSATZ: OPEN requires a child alias.\n";
            return;
        }

        browser::ensure_session_root(current_area_name(area));

        if (!validate_next_alias_against_current_tree(area, alias))
        {
            std::cout << "ERSATZ: alias '" << alias
                      << "' is not a valid next child for the current path.\n";
            return;
        }

        browser::push_path_alias(alias);
        std::cout << "ERSATZ PATH: " << browser::path_string() << "\n";
        return;
    }

    if (sub == "LOAD")
    {
        std::string target;
        std::getline(iss, target);

        std::string status;
        if (!load_ersatz_file(area, target, status))
        {
            std::cout << "ERSATZ: LOAD failed (" << status << ")\n";
            return;
        }

        std::cout << "ERSATZ: " << status << "\n";
        return;
    }

    if (sub == "SAVE")
    {
        std::string target;
        std::getline(iss, target);

        std::string status;
        if (!save_ersatz_file(target, status))
        {
            std::cout << "ERSATZ: SAVE failed (" << status << ")\n";
            return;
        }

        std::cout << "ERSATZ: " << status << "\n";
        return;
    }

    if (sub == "WLOAD")
    {
        std::string target;
        std::getline(iss, target);

        std::string status;
        if (!handoff_to_workspace(area, target, status))
        {
            std::cout << "ERSATZ: " << status << "\n";
            return;
        }

        std::cout << "ERSATZ: " << status << "\n";
        return;
    }

    if (sub == "DELTA" || sub == "TUPLEDELTA")
    {
        handle_delta_command(area, iss);
        return;
    }


    const bool known =
        sub == "SHOW" ||
        sub == "REFRESH" ||
        sub == "TREE" ||
        sub == "GRID" ||
        sub == "HELP" ||
        sub == "RESET" ||
        sub == "STATUS" ||
        sub == "ORDER" ||
        sub == "TOP" ||
        sub == "BOTTOM" ||
        sub == "NEXT" ||
        sub == "PREV" ||
        sub == "SKIP" ||
        sub == "ROOT" ||
        sub == "LIMIT" ||
        sub == "PATH" ||
        sub == "CLEARPATH" ||
        sub == "BACK" ||
        sub == "OPEN" ||
        sub == "LOAD" ||
        sub == "SAVE" ||
        sub == "WLOAD" ||
        sub == "DELTA" ||
        sub == "TUPLEDELTA";

    if (!known)
    {
        std::string status;
        if (!load_ersatz_file(area, raw_sub, status))
        {
            std::cout << "ERSATZ: LOAD failed (" << status << ")\n";
            return;
        }

        std::cout << "ERSATZ: " << status << "\n";
        return;
    }

    if (sub == "TREE" || sub == "GRID" || sub == "REFRESH" || sub == "SHOW")
    {
        render_current_ersatz_snapshot(area, sub);
        return;
    }

    std::cout << "ERSATZ: unknown subcommand: " << sub << "\n";
    print_help();
}
