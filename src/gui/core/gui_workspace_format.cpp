// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "gui/core/gui_workspace_format.hpp"

#include "dottalk/minidb.hpp"
#include "dottalk/dtschema.hpp"

#include <cctype>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <vector>

namespace dottalk::gui {

namespace {

std::string visible_area_id(AreaId id) {
    return id == 0 ? std::string("none") : std::to_string(id - 1);
}

} // namespace

std::string format_workspace_graph_text(const ListAreasResult& areas,
                                        const std::string& title,
                                        const std::string& no_open_areas_text) {
    std::ostringstream graph;
    graph << title << "\n\n";
    graph << "Areas: " << areas.areas.size() << "\n";
    graph << "Active area: " << visible_area_id(areas.active_area_id) << "\n\n";

    if (areas.areas.empty()) {
        graph << no_open_areas_text << "\n";
    } else {
        graph << "Areas\n";
        for (const auto& area : areas.areas) {
            graph << (area.active ? "* " : "  ")
                  << visible_area_id(area.area_id) << "  "
                  << area.display_name << "\n"
                  << "    table: " << area.path.string() << "\n"
                  << "    records: " << area.record_count << "\n"
                  << "    fields: " << area.field_count << "\n";
        }
    }

    graph << "\n";
    graph << "Relations: workspace graph service pending\n";
    graph << "Indexes: workspace graph service pending\n";
    graph << "Browsers/lists: workspace graph service pending\n";
    graph << "ERSATZ presets: workspace graph service pending\n";
    graph << "DTSchema load/save: routed through DotTalk++ runtime schema commands; graph service pending\n";
    return graph.str();
}

std::string format_workspace_graph_text(const WorkspaceModel& model,
                                        const std::string& title,
                                        const std::string& no_open_areas_text) {
    // AIF-120. Grouped BY WORKSPACE, because that is the scope every page above
    // is keyed on and because the grouping keeps this view proportional to the
    // working set rather than to the address space -- MAX_AREA is a build vector
    // with no upper bound, so nothing here may enumerate slots.
    //
    // One line per table, not four. The previous shape restated the Tables grid
    // sitting directly above it at four lines each; the thing this view can show
    // that no grid does is STRUCTURE -- who owns what, and how the tables relate.
    std::ostringstream graph;
    graph << title << "\n\n";

    std::vector<std::string> order;
    for (const auto& area : model.tables) {
        if (std::find(order.begin(), order.end(), area.workspace) == order.end()) {
            order.push_back(area.workspace);
        }
    }
    if (order.empty()) {
        order.push_back(model.current_workspace);
    }

    graph << "Workspaces: " << order.size()
          << "    Current: " << model.current_workspace << "\n";
    graph << "Areas: " << model.tables.size()
          << "    Active area: " << visible_area_id(model.active_area_id) << "\n\n";

    if (model.tables.empty()) {
        graph << no_open_areas_text << "\n";
    }

    for (const auto& workspace : order) {
        std::size_t count = 0;
        for (const auto& area : model.tables) {
            if (area.workspace == workspace) ++count;
        }
        graph << workspace << " -- " << count << " area(s)\n";

        for (const auto& area : model.tables) {
            if (area.workspace != workspace) continue;
            graph << (area.active ? "  * " : "    ")
                  << std::setw(4) << std::left << visible_area_id(area.area_id)
                  << std::setw(22) << std::left << area.display_name
                  << std::setw(8) << std::right << area.record_count << " rec"
                  << std::setw(5) << std::right << area.field_count << " fld   "
                  << area.path.string() << "\n";
        }

        graph << "\n  Indexes\n";
        std::size_t shown = 0;
        for (const auto& index : model.indexes) {
            if (index.workspace != workspace) continue;
            ++shown;
            graph << "    " << visible_area_id(index.area_id) << "  "
                  << index.area_name << "  " << index.kind;
            if (index.active) {
                graph << "  " << index.container.string();
                if (!index.tag.empty()) {
                    graph << " TAG " << index.tag;
                }
                graph << (index.ascending ? " ASC" : " DESC");
            }
            graph << "  [" << index.backend << "]\n";
        }
        if (shown == 0) graph << "    none\n";

        graph << "\n  Relations\n";
        // AIF-120. A posture can mirror its RELATION lines while every one of
        // its AREA lines fails to resolve -- measured live: m1_check.dtschema
        // opened 0 of 43 tables and still produced 58 relations. Rendering
        // those identically to live ones puts a healthy-looking graph directly
        // under "0 area(s)" and leaves the reader to notice the contradiction.
        // Endpoint-by-endpoint resolution needs an alias on AreaInfo (today
        // display_name is alias + ".DBF", and guessing the alias back out of it
        // would be a fourth fuzzy name comparison in this tree). The zero-area
        // case needs no guessing and is the one that actually occurs.
        if (count == 0) {
            graph << "    [UNBACKED] No table is open in this workspace, so every\n"
                     "               endpoint below is a name with nothing behind it.\n";
        }
        shown = 0;
        for (const auto& relation : model.relations) {
            if (relation.workspace != workspace) continue;
            ++shown;
            graph << "    " << relation.parent << " -> " << relation.child;
            if (!relation.parent_key.empty()) {
                graph << " ON " << relation.parent_key;
                // AIF-120 G3. A relation may bind DIFFERENTLY NAMED endpoints --
                // `ON EMPLOYEE_ID TO APPROVED_BY`, and one table related to
                // itself by `ON EMPLOYEE_ID TO REPORTS_TO`. Measured across the
                // live workspace catalog: 190 of 1,102 RELATION lines (17.2%)
                // carry an explicit TO. Rendering only the parent key is wrong
                // one time in six, and wrong in a way that reads as correct.
                if (!relation.child_key.empty() &&
                    relation.child_key != relation.parent_key) {
                    graph << " TO " << relation.child_key;
                }
            }
            if (relation.match_count > 0) {
                graph << "  (" << relation.match_count << " matches)";
            }
            graph << "\n";
        }
        if (shown == 0) graph << "    none\n";
        graph << "\n";
    }

    // Named rather than left vague. The three lines this replaces read
    // "workspace graph service pending" and had said so for a long time, which
    // tells a reader nothing about WHAT is missing or why.
    graph << "Not shown: the posture's own identity -- WSID, FLAVOR, and the\n";
    graph << "DBFROOT/IDXROOT/LMDBROOT residence roots. The GUI model does not\n";
    graph << "carry them yet, so a RAM-hydrated workspace is indistinguishable\n";
    graph << "here from a disk-resident one. That is the next slice, and until it\n";
    graph << "lands this view cannot tell you where a table actually lives.\n";
    return graph.str();
}

std::string format_minidb_container_text(const std::string& payload,
                                         const std::string& title) {
    std::ostringstream out;
    out << title << "\n\n";

    if (!dottalk::minidb::is_container(payload)) {
        out << "  This memo does not carry a MINIDB 1 container.\n"
            << "  " << payload.size() << " byte(s); first line does not read 'MINIDB 1'.\n";
        return out.str();
    }

    const auto sc = dottalk::minidb::scan(payload);
    if (!sc.ok) {
        out << "  Container refused: " << sc.error << ".\n"
            << "  Nothing was hydrated. " << payload.size() << " byte(s) in the field.\n";
        return out.str();
    }

    // Split members the way the container itself does: an "indexes/" prefix is
    // the only structure the format carries.
    std::vector<const dottalk::minidb::Member*> tables, indexes;
    std::size_t widest = 0;
    for (const auto& m : sc.files) {
        (m.relpath.rfind("indexes/", 0) == 0 ? indexes : tables).push_back(&m);
        widest = std::max(widest, m.relpath.size());
    }

    out << "  container : MINIDB 1, " << payload.size() << " byte(s) in the memo\n"
        << "  posture   : " << sc.posture.size() << " byte(s)\n"
        << "  members   : " << sc.files.size() << " file(s), "
        << sc.total_file_bytes << " byte(s) hydrated\n";
    if (!sc.ignored_sections.empty()) {
        out << "  unknown   : " << sc.ignored_sections.size()
            << " section(s) this reader does not understand\n";
        for (const auto& sect : sc.ignored_sections) out << "      " << sect << "\n";
    }

    // AIF-120. Is this container complete enough to rebuild from?
    //
    // The CDX container is the PUBLISHED index; LMDB is derived from it by
    // BUILDLMDB and is deliberately never carried here (mcc_build_x64.dts:
    // "LMDB is a derived backend, not a stored format", measured at 53 GB on
    // disk against a 104 KB container). So a container is rebuildable exactly
    // when every table and index its posture DECLARES is actually present as a
    // member -- write that back to disk and BUILDLMDB has everything it needs.
    //
    // A missing member is worth knowing BEFORE the writeback, not after
    // BUILDLMDB comes up short. The "none" sentinel is honoured here for the
    // same reason it is everywhere else: a declared index of "none" is an
    // absence, not a filename.
    {
        auto basename_lower = [](std::string v) {
            const auto slash = v.find_last_of("/\\");
            if (slash != std::string::npos) v = v.substr(slash + 1);
            for (char& ch : v) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            return v;
        };

        std::vector<std::string> have_tables, have_indexes;
        for (const auto& m : sc.files) {
            (m.relpath.rfind("indexes/", 0) == 0 ? have_indexes : have_tables)
                .push_back(basename_lower(m.relpath));
        }
        auto present = [&](const std::vector<std::string>& v, const std::string& want) {
            return std::find(v.begin(), v.end(), basename_lower(want)) != v.end();
        };

        std::vector<std::string> missing;
        std::size_t declared_tables = 0, declared_indexes = 0;
        std::istringstream areas(sc.posture);
        std::string aline;
        while (std::getline(areas, aline)) {
            if (!aline.empty() && aline.back() == '\r') aline.pop_back();
            if (aline.rfind("AREA ", 0) != 0 && aline.rfind("area ", 0) != 0) continue;
            std::string dbf, idx, alias;
            std::istringstream parts(aline);
            std::string part;
            while (std::getline(parts, part, '|')) {
                const auto eq = part.find('=');
                if (eq == std::string::npos) continue;
                std::string key = part.substr(0, eq);
                std::string val = part.substr(eq + 1);
                while (!key.empty() && std::isspace(static_cast<unsigned char>(key.front()))) key.erase(key.begin());
                while (!key.empty() && std::isspace(static_cast<unsigned char>(key.back()))) key.pop_back();
                while (!val.empty() && std::isspace(static_cast<unsigned char>(val.front()))) val.erase(val.begin());
                while (!val.empty() && std::isspace(static_cast<unsigned char>(val.back()))) val.pop_back();
                for (char& ch : key) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
                if (key == "dbf") dbf = val;
                else if (key == "index") idx = val;
                else if (key == "alias") alias = val;
            }
            if (!dottalk::dtschema::is_absent(dbf)) {
                ++declared_tables;
                if (!present(have_tables, dbf)) missing.push_back(alias + ": table " + dbf);
            }
            if (!dottalk::dtschema::is_absent(idx)) {
                ++declared_indexes;
                if (!present(have_indexes, idx)) missing.push_back(alias + ": index " + idx);
            }
        }

        out << "  rebuild   : ";
        if (missing.empty()) {
            out << "COMPLETE -- " << declared_tables << " table(s) and "
                << declared_indexes << " index container(s) declared, all present.\n"
                << "              Written back to disk, BUILDLMDB can re-derive the\n"
                << "              LMDB envs from these CDX containers.\n";
        } else {
            out << "INCOMPLETE -- " << missing.size() << " declared member(s) absent:\n";
            for (const auto& m : missing) out << "              " << m << "\n";
            out << "              A writeback would land short of what the posture claims.\n";
        }
    }

    out << "\n";

    auto dump = [&](const char* label,
                    const std::vector<const dottalk::minidb::Member*>& v) {
        if (v.empty()) return;
        out << "  " << label << "\n";
        for (const auto* m : v) {
            out << "    " << std::left << std::setw(static_cast<int>(widest) + 2)
                << m->relpath << std::right << std::setw(12) << m->length << "\n";
        }
        out << "\n";
    };
    dump("Tables", tables);
    dump("Index containers", indexes);

    out << "  Posture carried by the container\n";
    std::istringstream ps(sc.posture);
    std::string line;
    while (std::getline(ps, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;

        // AIF-120. The three ROOT lines are NOT equally operative, and printing
        // them identically invites the reader to assume they are. The CLI says
        // so on every load (cmd_workspace.cpp:1997 and :2004): DBFROOT/IDXROOT
        // apply to that load's resolution only, and LMDBROOT is "recorded, not
        // applied" under the chartered disk-only rule.
        //
        // The reason behind that rule, since "chartered" alone teaches nothing:
        // LMDB is disk-backed and cannot serve a RAM-resident workspace.
        // index_manager.cpp:110 routes a .cdx under a mounted ramfs root to
        // CdxNativeBackend (CDX-V64, LMDB-free), skipping the LMDB env gate
        // entirely, and hydrate_minidb writes every .cdx member into the RAM
        // VFS. So a hydrated workspace never reaches LMDB, and the root it
        // carried would have nothing to point at.
        //
        // These roots also record whoever SAVED the container -- one row in the
        // live catalog carries a Windows D:\ root and another an agent session's
        // mount path -- so they are provenance, not location. Hydration replaces
        // the first two outright.
        std::string low;
        low.reserve(line.size());
        for (char ch : line) low.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));

        const char* note = nullptr;
        if (low.rfind("lmdbroot ", 0) == 0) {
            note = "   <- recorded, not applied: LMDB needs a disk, and a hydrated\n"
                   "                 workspace serves its .cdx from RAM through the\n"
                   "                 LMDB-free native CDX-V64 backend instead";
        } else if (low.rfind("dbfroot ", 0) == 0 || low.rfind("idxroot ", 0) == 0) {
            note = "   <- the saver's root; hydration replaces this with the RAM root";
        }

        out << "    " << line;
        if (note) out << note;
        out << "\n";
    }

    out << "\n  Nothing above was hydrated. These bytes are still in the memo;\n"
           "  the member sizes are what a WORKSPACE LOAD ... MEMO RAM would place\n"
           "  in the RAM disk, and are the same total the catalog records as EST_HYD_B.\n";
    return out.str();
}

} // namespace dottalk::gui
