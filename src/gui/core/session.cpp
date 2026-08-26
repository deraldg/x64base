// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "dottalk/scratch_sidecar.hpp"
#include "gui/core/session.hpp"
#include "xbase/workspace_membership.hpp"
#include "xbase/workspace_naming.hpp"   // I1.2: relations carry their owning workspace

#include "common/path_resolver.hpp"
#include "common/path_state.hpp"
#include "dottalk/dtschema.hpp"
#include "dottalk/minidb.hpp"
#include "dottalk/minidb_hydrate.hpp"
#include "xbase/ramfs.hpp"
#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"
#include "gui/core/gui_command_catalog.hpp"
#include "gui/core/gui_runtime_adapter.hpp"
#include "gui_shell_runtime.hpp"
#include "gui_cli_bridge.hpp"
#include "relation_parse.hpp"
#include "cli/shell_shortcuts.hpp"
#include "xbase.hpp"
#include "xbase/area_alloc.hpp"   // AIF-078 step 2b: the ONE free-slot policy
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <utility>
#include <vector>

namespace dottalk::gui {

namespace {

StatusMessage make_status(Severity severity, std::string code, std::string text, std::string detail = {}) {
    StatusMessage message;
    message.severity = severity;
    message.text = std::move(text);
    message.code = std::move(code);
    message.detail = std::move(detail);
    return message;
}

StatusMessage info(std::string code, std::string text, std::string detail = {}) {
    return make_status(Severity::info, std::move(code), std::move(text), std::move(detail));
}

StatusMessage warning(std::string code, std::string text, std::string detail = {}) {
    return make_status(Severity::warning, std::move(code), std::move(text), std::move(detail));
}

StatusMessage error(std::string code, std::string text, std::string detail = {}) {
    return make_status(Severity::error, std::move(code), std::move(text), std::move(detail));
}

std::string trim_ascii(std::string value) {
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), [&](char ch) {
        return !is_space(static_cast<unsigned char>(ch));
    }));
    value.erase(std::find_if(value.rbegin(), value.rend(), [&](char ch) {
        return !is_space(static_cast<unsigned char>(ch));
    }).base(), value.end());
    return value;
}

std::string lower_ascii(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return value;
}

std::string upper_ascii(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

bool ends_with_ci(const std::string& text, const std::string& suffix) {
    const std::string lower_text = lower_ascii(text);
    const std::string lower_suffix = lower_ascii(suffix);
    return lower_text.size() >= lower_suffix.size() &&
           lower_text.compare(lower_text.size() - lower_suffix.size(), lower_suffix.size(), lower_suffix) == 0;
}

std::string first_token_lower(const std::string& text) {
    std::istringstream stream(text);
    std::string token;
    stream >> token;
    return lower_ascii(token);
}

std::string remove_first_token(std::string text) {
    text = trim_ascii(std::move(text));
    const auto first_space = text.find_first_of(" \t");
    if (first_space == std::string::npos) {
        return {};
    }
    return trim_ascii(text.substr(first_space + 1));
}

std::string remove_first_tokens(std::string text, std::size_t count) {
    text = trim_ascii(std::move(text));
    for (std::size_t i = 0; i < count; ++i) {
        const auto first_space = text.find_first_of(" \t");
        if (first_space == std::string::npos) {
            return {};
        }
        text = trim_ascii(text.substr(first_space + 1));
    }
    return text;
}

std::vector<std::string> split_words(const std::string& text) {
    std::istringstream stream(text);
    std::vector<std::string> words;
    std::string word;
    while (stream >> word) {
        words.push_back(word);
    }
    return words;
}

bool parse_i64(const std::string& text, long long& out) {
    try {
        std::size_t used = 0;
        const long long value = std::stoll(text, &used, 10);
        if (used != text.size()) {
            return false;
        }
        out = value;
        return true;
    } catch (...) {
        return false;
    }
}

bool parse_i64_prefix(const std::string& text, long long& out) {
    std::string digits;
    std::size_t index = 0;
    while (index < text.size() && std::isspace(static_cast<unsigned char>(text[index])) != 0) {
        ++index;
    }
    if (index < text.size() && (text[index] == '+' || text[index] == '-')) {
        digits.push_back(text[index++]);
    }
    while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index])) != 0) {
        digits.push_back(text[index++]);
    }
    return !digits.empty() && digits != "+" && digits != "-" && parse_i64(digits, out);
}

std::optional<std::filesystem::path> workspace_open_dir_from_cli_output(const std::string& output) {
    constexpr const char* marker = "WORKSPACE OPEN: scanning directory:";
    std::istringstream stream(output);
    std::string line;
    std::optional<std::filesystem::path> found;
    while (std::getline(stream, line)) {
        const auto pos = line.find(marker);
        if (pos == std::string::npos) {
            continue;
        }

        std::string text = trim_ascii(line.substr(pos + std::char_traits<char>::length(marker)));
        const auto option_pos = text.find(" [");
        if (option_pos != std::string::npos) {
            text = trim_ascii(text.substr(0, option_pos));
        }
        if (!text.empty()) {
            found = std::filesystem::path(text);
        }
    }
    return found;
}

struct WorkspaceOpenIndexAttachment {
    // AIF-078. This is parsed out of the CLI's "Area <n>" line, and that n is a
    // POSITION. It used to be stored as an AreaId with a + 1 welded on, which is
    // what made a positional token and an identity the same C++ type.
    MaybeAreaOrdinal area_ordinal;
    std::filesystem::path container;
};

struct WorkspaceSchemaArea {
    long long slot {0};
    std::filesystem::path dbf;
    std::filesystem::path index;
    std::string index_type;
    std::string tag;
    std::string alias;
};

std::string strip_matching_quotes(std::string value) {
    value = trim_ascii(std::move(value));
    if (value.size() >= 2 &&
        ((value.front() == '"' && value.back() == '"') ||
         (value.front() == '\'' && value.back() == '\''))) {
        return value.substr(1, value.size() - 2);
    }
    return value;
}

std::optional<std::filesystem::path> resolve_workspace_schema_token(const std::filesystem::path& token) {
    if (token.empty()) {
        return std::nullopt;
    }

    std::vector<std::filesystem::path> candidates;
    auto add = [&](std::filesystem::path path) {
        if (path.empty()) {
            return;
        }
        candidates.push_back(path);
        if (!path.has_extension()) {
            auto with_ext = path;
            with_ext.replace_extension(".dtschema");
            candidates.push_back(std::move(with_ext));
            with_ext = path;
            with_ext.replace_extension(".dtschemas");
            candidates.push_back(std::move(with_ext));
        }
    };

    if (token.is_absolute()) {
        add(token);
    } else {
        add(dottalk::paths::get_slot(dottalk::paths::Slot::CUR_WORKSPACES) / token);
        add(dottalk::paths::get_slot(dottalk::paths::Slot::DEF_WORKSPACES) / token);
        add(dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES) / token);
        add(dottalk::paths::get_slot(dottalk::paths::Slot::SCHEMAS) / token);
        add(token);
    }

    for (const auto& candidate : candidates) {
        std::error_code ec;
        if (std::filesystem::is_regular_file(candidate, ec) && !ec) {
            return candidate;
        }
    }
    return std::nullopt;
}

std::filesystem::path normalize_workspace_schema_extension(std::filesystem::path path) {
    if (!path.has_extension()) {
        path.replace_extension(".dtschema");
    }
    return path;
}

std::filesystem::path resolve_workspace_schema_save_target(const std::string& token_text) {
    std::filesystem::path path(strip_matching_quotes(token_text));
    path = normalize_workspace_schema_extension(std::move(path));
    if (path.is_absolute()) {
        return path;
    }
    return dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES) / path;
}

bool path_is_under_root(const std::filesystem::path& path, const std::filesystem::path& root) {
    if (path.empty() || root.empty()) {
        return false;
    }
    std::error_code ec;
    const auto relative = std::filesystem::relative(path, root, ec);
    if (ec || relative.empty()) {
        return false;
    }
    const std::string text = relative.generic_string();
    return text != ".." && text.rfind("../", 0) != 0;
}

std::filesystem::path relativize_schema_path(const std::filesystem::path& path,
                                             const std::filesystem::path& preferred_root) {
    if (path_is_under_root(path, preferred_root)) {
        std::error_code ec;
        const auto relative = std::filesystem::relative(path, preferred_root, ec);
        if (!ec && !relative.empty()) {
            return relative;
        }
    }
    return path;
}

std::optional<std::filesystem::path> workspace_load_schema_from_cli_output(const std::string& output,
                                                                           const std::string& command_text) {
    std::istringstream stream(output);
    std::string line;
    std::optional<std::filesystem::path> found;
    while (std::getline(stream, line)) {
        const auto marker = line.find("WORKSPACE=");
        if (marker == std::string::npos) {
            continue;
        }
        std::string text = trim_ascii(line.substr(marker + 10));
        const auto stop = text.find_first_of(" \t\r\n");
        if (stop != std::string::npos) {
            text = text.substr(0, stop);
        }
        if (auto resolved = resolve_workspace_schema_token(std::filesystem::path(strip_matching_quotes(text)))) {
            found = *resolved;
        }
    }

    if (found) {
        return found;
    }

    const auto words = split_words(command_text);
    if (words.size() >= 3 && lower_ascii(words[0]) == "workspace" && lower_ascii(words[1]) == "load") {
        return resolve_workspace_schema_token(std::filesystem::path(strip_matching_quotes(words[2])));
    }
    return std::nullopt;
}

std::optional<std::filesystem::path> resolve_workspace_open_index_container(const std::filesystem::path& dbf_dir,
                                                                            const std::filesystem::path& token) {
    if (token.empty()) {
        return std::nullopt;
    }

    const std::string ext = lower_ascii(token.extension().string());
    std::vector<std::filesystem::path> candidates;
    auto append_candidate = [&](std::filesystem::path path) {
        if (!path.empty()) {
            candidates.push_back(std::move(path));
        }
    };

    if (token.is_absolute()) {
        append_candidate(token);
    } else {
        append_candidate(dbf_dir / token);
        if (ext == ".cdx") {
            append_candidate(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X64) / token);
        } else if (ext == ".cnx" || ext == ".inx") {
            append_candidate(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X32) / token);
        }
        append_candidate(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES) / token);
    }

    for (const auto& candidate : candidates) {
        std::error_code ec;
        if (std::filesystem::is_regular_file(candidate, ec) && !ec) {
            return candidate;
        }
    }
    return std::nullopt;
}

std::vector<WorkspaceOpenIndexAttachment> workspace_open_indexes_from_cli_output(const std::string& output,
                                                                                const std::filesystem::path& dbf_dir) {
    std::vector<WorkspaceOpenIndexAttachment> attachments;
    std::istringstream stream(output);
    std::string line;
    while (std::getline(stream, line)) {
        line = trim_ascii(line);
        constexpr const char* area_prefix = "Area ";
        if (line.rfind(area_prefix, 0) != 0) {
            continue;
        }

        long long area0 = 0;
        if (!parse_i64_prefix(line.substr(std::char_traits<char>::length(area_prefix)), area0) || area0 < 0) {
            continue;
        }

        const auto index_pos = line.find("[index:");
        if (index_pos == std::string::npos || line.find(", attached", index_pos) == std::string::npos) {
            continue;
        }

        std::string rest = trim_ascii(line.substr(index_pos + 7));
        const auto comma = rest.find(',');
        if (comma != std::string::npos) {
            rest = trim_ascii(rest.substr(0, comma));
        }
        if (rest.empty()) {
            continue;
        }

        if (auto container = resolve_workspace_open_index_container(dbf_dir, std::filesystem::path(rest))) {
            WorkspaceOpenIndexAttachment attachment;
            attachment.area_ordinal = static_cast<AreaOrdinal>(area0);
            attachment.container = std::move(*container);
            attachments.push_back(std::move(attachment));
        }
    }
    return attachments;
}

std::vector<WorkspaceSchemaArea> load_dtschema2_areas_from_stream(
        std::istream& file,
        std::vector<WorkspaceRelationInfo>& relations);

std::vector<WorkspaceSchemaArea> load_dtschema2_areas(const std::filesystem::path& schema_path,
                                                      std::vector<WorkspaceRelationInfo>& relations) {
    std::ifstream file(schema_path);
    if (!file) {
        return {};
    }
    return load_dtschema2_areas_from_stream(file, relations);
}

std::optional<std::filesystem::path> resolve_schema_dbf_path(const std::filesystem::path& token,
                                                             const std::string& index_type) {
    if (token.empty()) {
        return std::nullopt;
    }

    std::vector<std::filesystem::path> candidates;
    auto add = [&](std::filesystem::path path) {
        if (!path.empty()) {
            candidates.push_back(std::move(path));
        }
    };

    if (token.is_absolute()) {
        add(token);
    } else {
        const std::string mode = upper_ascii(trim_ascii(index_type));
        if (mode == "CDX") {
            add(dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X64) / token);
        } else if (mode == "CNX" || mode == "INX" || mode == "IDX") {
            add(dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X32) / token);
        }
        add(dottalk::paths::get_slot(dottalk::paths::Slot::DBF) / token);
        add(token);
    }

    for (const auto& candidate : candidates) {
        std::error_code ec;
        if (std::filesystem::is_regular_file(candidate, ec) && !ec) {
            return candidate;
        }
    }
    return std::nullopt;
}

std::optional<std::filesystem::path> resolve_schema_index_path(const std::filesystem::path& token,
                                                               const std::string& index_type) {
    if (token.empty()) {
        return std::nullopt;
    }

    std::vector<std::filesystem::path> candidates;
    auto add = [&](std::filesystem::path path) {
        if (!path.empty()) {
            candidates.push_back(std::move(path));
        }
    };

    if (token.is_absolute()) {
        add(token);
    } else {
        const std::string mode = upper_ascii(trim_ascii(index_type));
        if (mode == "CDX") {
            add(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X64) / token);
        } else if (mode == "CNX" || mode == "INX" || mode == "IDX") {
            add(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X32) / token);
        }
        add(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES) / token);
        add(token);
    }

    for (const auto& candidate : candidates) {
        std::error_code ec;
        if (std::filesystem::is_regular_file(candidate, ec) && !ec) {
            return candidate;
        }
    }
    return std::nullopt;
}

// AIF-078 I1.2 follow-up. WorkspaceRelationInfo::workspace had ZERO WRITERS:
// all three construction sites in this file left it at its kDefaultWorkspace
// default, while gui_workspace_format.cpp filtered on it and main_frame.cpp
// displayed it in a column. A filter on a constant, and a column that could
// only ever read DEFAULT.
//
// That was defensible while the runtime had nothing to report -- model.hpp said
// so: "Relations are engine-global today, so a refresh has no group scope."
// It stopped being true when the relation store was partitioned, so the field
// gets its writer here.
//
// The OWNING workspace of a parsed edge is the session's CURRENT workspace,
// for both sources and for the same reason: REL LIST reports the current
// workspace's map (that is what the partition means), and a posture is loaded
// INTO a workspace named by the command, never one it records itself
// (invariant I3). Neither source carries a workspace of its own, so neither is
// being second-guessed.
std::string owning_workspace_now() {
    const std::string name =
        xbase::workspace::name_of(xbase::workspace::current_handle());
    return name.empty() ? std::string(kDefaultWorkspace) : name;
}

// AIF-120. A posture is a posture whether it came from a file or out of a memo
// field, so the parser reads a stream and the path form is a wrapper. The memo
// path has no file to hand it.
std::vector<WorkspaceSchemaArea> load_dtschema2_areas_from_stream(
        std::istream& file,
        std::vector<WorkspaceRelationInfo>& relations) {
    std::vector<WorkspaceSchemaArea> areas;

    std::string line;
    while (std::getline(file, line)) {
        line = trim_ascii(line);
        if (line.empty()) {
            continue;
        }

        if (line.rfind("AREA ", 0) == 0) {
            const auto first_pipe = line.find('|');
            if (first_pipe == std::string::npos) {
                continue;
            }

            long long slot = 0;
            if (!parse_i64_prefix(line.substr(5, first_pipe - 5), slot) || slot < 0) {
                continue;
            }

            WorkspaceSchemaArea area;
            area.slot = slot;

            std::string rest = line.substr(first_pipe + 1);
            std::istringstream parts(rest);
            std::string part;
            while (std::getline(parts, part, '|')) {
                const auto equal = part.find('=');
                if (equal == std::string::npos) {
                    continue;
                }
                const std::string key = lower_ascii(trim_ascii(part.substr(0, equal)));
                const std::string value = strip_matching_quotes(part.substr(equal + 1));
                if (key == "dbf") {
                    area.dbf = value;
                } else if (key == "index") {
                    area.index = value;
                } else if (key == "indextype") {
                    area.index_type = upper_ascii(value);
                } else if (key == "tag") {
                    area.tag = value;
                } else if (key == "alias") {
                    area.alias = value;
                }
            }

            if (!area.dbf.empty()) {
                areas.push_back(std::move(area));
            }
            continue;
        }

        WorkspaceRelationInfo relation;
        // R125: THE HANDLE, not owning_workspace_now()'s rendered name. The
        // conversion back to a name for display happens inside the parser, in
        // one place, which is what GUI_LAYER_DECISION_OUTLINE step 2 asked for.
        if (parse_relation_posture_line(line, xbase::workspace::current_handle(), relation)) {
            merge_relation(relations, std::move(relation));
        }
    }

    std::sort(areas.begin(), areas.end(), [](const auto& left, const auto& right) {
        return left.slot < right.slot;
    });
    return areas;
}

std::vector<std::filesystem::path> default_index_candidates_for_area(const xbase::DbArea& area,
                                                                     const std::filesystem::path& dbf_path,
                                                                     const std::string& requested_mode) {
    std::string mode = upper_ascii(trim_ascii(requested_mode));
    if (mode.empty() || mode == "AUTO") {
        if (area.kind() == xbase::AreaKind::V64 || area.kind() == xbase::AreaKind::V128) {
            mode = "CDX";
        } else if (area.kind() == xbase::AreaKind::V32) {
            mode = "CNX";
        }
    }

    const std::filesystem::path stem = dbf_path.stem();
    const std::filesystem::path dbf_dir = dbf_path.parent_path();
    std::vector<std::filesystem::path> candidates;
    auto append = [&](std::filesystem::path dir, const std::string& ext) {
        if (dir.empty()) {
            return;
        }
        std::filesystem::path candidate = dir / stem;
        candidate.replace_extension(ext);
        candidates.push_back(std::move(candidate));
    };

    if (mode == "CDX") {
        append(dbf_dir, ".cdx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X64), ".cdx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES), ".cdx");
    } else if (mode == "CNX") {
        append(dbf_dir, ".cnx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X32), ".cnx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES), ".cnx");
    } else if (mode == "INX" || mode == "IDX") {
        append(dbf_dir, ".inx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X32), ".inx");
        append(dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES), ".inx");
    }

    return candidates;
}

std::optional<std::filesystem::path> first_existing_regular_file(const std::vector<std::filesystem::path>& paths) {
    for (const auto& path : paths) {
        std::error_code ec;
        if (std::filesystem::is_regular_file(path, ec) && !ec) {
            return path;
        }
    }
    return std::nullopt;
}

std::optional<long long> last_cli_area_from_output(const std::string& output) {
    std::istringstream stream(output);
    std::string line;
    std::optional<long long> found;
    while (std::getline(stream, line)) {
        line = trim_ascii(line);
        long long value = 0;
        constexpr const char* selected_prefix = "Selected area ";
        constexpr const char* current_prefix = "Current area:";
        if (line.rfind(selected_prefix, 0) == 0 &&
            parse_i64_prefix(line.substr(std::char_traits<char>::length(selected_prefix)), value)) {
            found = value;
        } else if (line.rfind(current_prefix, 0) == 0 &&
                   parse_i64_prefix(line.substr(std::char_traits<char>::length(current_prefix)), value)) {
            found = value;
        }
    }
    return found;
}

std::optional<long long> last_cli_recno_from_output(const std::string& output) {
    std::istringstream stream(output);
    std::string line;
    std::optional<long long> found;
    while (std::getline(stream, line)) {
        line = trim_ascii(line);
        constexpr const char* recno_prefix = "Recno:";
        long long value = 0;
        if (line.rfind(recno_prefix, 0) == 0 &&
            parse_i64_prefix(line.substr(std::char_traits<char>::length(recno_prefix)), value)) {
            found = value;
        }
    }
    return found;
}

bool parse_direction_word(const std::string& word, bool& ascending) {
    const std::string token = upper_ascii(word);
    if (token == "ASC" || token == "ASCEND" || token == "--ASC") {
        ascending = true;
        return true;
    }
    if (token == "DESC" || token == "DESCEND" || token == "--DESC") {
        ascending = false;
        return true;
    }
    return false;
}

bool is_physical_order_token(const std::string& word) {
    const std::string token = upper_ascii(word);
    return token == "0" || token == "PHYSICAL" || token == "NATURAL" || token == "PHYS";
}

bool is_v64_area(const xbase::DbArea& area) {
    return area.kind() == xbase::AreaKind::V64;
}

std::filesystem::path resolve_gui_index_token(const xbase::DbArea& area,
                                              const std::string& token,
                                              const std::string& default_extension) {
    std::filesystem::path path;
    if (token.empty()) {
        const std::string stem = !area.dbfBasename().empty() ? area.dbfBasename() : area.logicalName();
        path = dottalk::paths::resolve_index(stem);
    } else if (ends_with_ci(token, ".cdx.d")) {
        std::string text = token;
        text.erase(text.size() - 2);
        path = dottalk::paths::resolve_index(text);
    } else {
        path = dottalk::paths::resolve_index(token);
    }

    if (!default_extension.empty() && !path.has_extension()) {
        path.replace_extension(default_extension);
    }
    return path;
}

std::filesystem::path default_order_container_for_area(const xbase::DbArea& area) {
    return resolve_gui_index_token(area, "", is_v64_area(area) ? ".cdx" : ".cnx");
}

bool position_gui_area_to_first_ordered(xbase::DbArea& area, std::string& err) {
    err.clear();
    std::vector<std::uint64_t> recnos;
    cli::OrderIterSpec spec;
    if (!cli::order_collect_recnos_asc(area, recnos, &spec, &err) || recnos.empty()) {
        return false;
    }

    const std::uint64_t recno = spec.ascending ? recnos.front() : recnos.back();
    if (recno == 0 || recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        err = "ordered record number is outside GUI range";
        return false;
    }
    return area.gotoRec(static_cast<int32_t>(recno)) && area.readCurrent();
}

bool position_gui_area_to_last_ordered(xbase::DbArea& area, std::string& err) {
    err.clear();
    std::vector<std::uint64_t> recnos;
    cli::OrderIterSpec spec;
    if (!cli::order_collect_recnos_asc(area, recnos, &spec, &err) || recnos.empty()) {
        return false;
    }

    const std::uint64_t recno = spec.ascending ? recnos.back() : recnos.front();
    if (recno == 0 || recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        err = "ordered record number is outside GUI range";
        return false;
    }
    return area.gotoRec(static_cast<int32_t>(recno)) && area.readCurrent();
}

bool skip_gui_area_ordered(xbase::DbArea& area, int delta, std::string& err) {
    err.clear();
    if (delta == 0) {
        return area.readCurrent();
    }

    std::vector<std::uint64_t> recnos;
    cli::OrderIterSpec spec;
    if (!cli::order_collect_recnos_asc(area, recnos, &spec, &err) || recnos.empty()) {
        return false;
    }
    if (!spec.ascending) {
        std::reverse(recnos.begin(), recnos.end());
    }

    const auto current = static_cast<std::uint64_t>(std::max(0, area.recno()));
    const auto it = std::find(recnos.begin(), recnos.end(), current);
    if (it == recnos.end()) {
        err = "current record is not present in the active order";
        return false;
    }

    const long long index = static_cast<long long>(std::distance(recnos.begin(), it));
    const long long next = index + static_cast<long long>(delta);
    if (next < 0 || next >= static_cast<long long>(recnos.size())) {
        err = "ordered skip is outside the active order range";
        return false;
    }

    const std::uint64_t recno = recnos[static_cast<std::size_t>(next)];
    if (recno == 0 || recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        err = "ordered record number is outside GUI range";
        return false;
    }
    return area.gotoRec(static_cast<int32_t>(recno)) && area.readCurrent();
}

bool activate_gui_order(xbase::DbArea& area,
                        const std::filesystem::path& container,
                        const std::string& tag,
                        bool ascending,
                        std::string& err) {
    err.clear();
    const std::string container_text = container.string();
    const std::string tag_upper = upper_ascii(trim_ascii(tag));

    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);
    orderstate::setOrder(area, container_text);
    orderstate::setActiveTag(area, tag_upper);
    orderstate::setAscending(area, ascending);

    bool opened = false;
    if (ends_with_ci(container_text, ".cdx")) {
        opened = xindex::ensure_manager(area).openCdx(container_text, tag_upper, &err);
    } else if (ends_with_ci(container_text, ".cnx")) {
        opened = xindex::ensure_manager(area).openCnx(container_text, tag_upper, &err);
    } else {
        err = "GUI ordered browse supports CDX/CNX activation in this bridge pass.";
    }

    if (!opened) {
        xindex::ensure_manager(area).close();
        orderstate::clearOrder(area);
        return false;
    }

    std::string move_err;
    if (!position_gui_area_to_first_ordered(area, move_err) && err.empty()) {
        err = move_err;
    }
    return true;
}

bool attach_gui_order_container(xbase::DbArea& area, const std::filesystem::path& container, std::string& err) {
    err.clear();
    const std::string container_text = container.string();
    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);
    orderstate::setOrder(area, container_text);
    orderstate::setActiveTag(area, "");
    orderstate::setAscending(area, true);

    bool opened = false;
    if (ends_with_ci(container_text, ".cdx")) {
        opened = xindex::ensure_manager(area).openCdx(container_text, {}, &err);
    } else if (ends_with_ci(container_text, ".cnx")) {
        opened = xindex::ensure_manager(area).openCnx(container_text, {}, &err);
    } else {
        err = "GUI workspace index mirror supports CDX/CNX containers.";
    }

    if (!opened) {
        xindex::ensure_manager(area).close();
        orderstate::clearOrder(area);
        return false;
    }
    return true;
}

bool mirror_setpath_output_to_gui(const std::string& output, std::vector<StatusMessage>& messages) {
    std::istringstream stream(output);
    std::string line;
    std::size_t changed = 0;
    while (std::getline(stream, line)) {
        const auto pos = line.find("SETPATH:");
        if (pos == std::string::npos) {
            continue;
        }

        std::string rest = trim_ascii(line.substr(pos + 8));
        const auto eq = rest.find('=');
        if (eq == std::string::npos) {
            continue;
        }

        const std::string key = trim_ascii(rest.substr(0, eq));
        const std::filesystem::path value(trim_ascii(rest.substr(eq + 1)));
        if (key.empty() || value.empty()) {
            continue;
        }

        if (auto slot = dottalk::paths::slot_from_string(key)) {
            dottalk::paths::set_slot(*slot, value);
            ++changed;
        }
    }

    if (changed > 0) {
        messages.push_back(info("gui.paths.synced",
                                "GUI path slots mirrored SETPATH output from DotTalk++ shell.",
                                std::to_string(changed) + " path slot(s)"));
    }
    return changed > 0;
}

bool mirror_set_index_to_gui(xbase::DbArea& area,
                             const std::vector<std::string>& words,
                             std::vector<StatusMessage>& messages) {
    std::size_t i = 0;
    if (words.size() >= 2 && lower_ascii(words[0]) == "set" && lower_ascii(words[1]) == "index") {
        i = 2;
    } else if (!words.empty() && lower_ascii(words[0]) == "setindex") {
        i = 1;
    } else {
        return false;
    }

    if (i < words.size() && lower_ascii(words[i]) == "to") {
        ++i;
    }
    if (i >= words.size()) {
        return false;
    }

    const std::string container_token = words[i++];
    std::string tag;
    if (i < words.size()) {
        if (lower_ascii(words[i]) == "tag" && i + 1 < words.size()) {
            tag = words[i + 1];
        } else {
            tag = words[i];
        }
    }

    std::filesystem::path container = resolve_gui_index_token(area,
                                                              container_token,
                                                              is_v64_area(area) ? ".cdx" : ".cnx");
    if (tag.empty()) {
        std::string err;
        if (!attach_gui_order_container(area, container, err)) {
            messages.push_back(warning("gui.order.index_attach_failed",
                                       "DotTalk++ shell index attach succeeded, but GUI index attach failed.",
                                       err));
            return false;
        }
        messages.push_back(info("gui.order.index_attached",
                                "GUI attached the same index container used by the DotTalk++ shell.",
                                container.string()));
        return true;
    }

    std::string err;
    if (activate_gui_order(area, container, tag, true, err)) {
        messages.push_back(info("gui.order.activated",
                                "GUI activated the same ordered index used by the DotTalk++ shell.",
                                container.string() + " TAG " + upper_ascii(tag)));
        return true;
    }

    messages.push_back(warning("gui.order.activate_failed",
                               "DotTalk++ shell order succeeded, but GUI order activation failed.",
                               err));
    return false;
}

bool mirror_set_order_to_gui(xbase::DbArea& area,
                             std::vector<std::string> words,
                             std::vector<StatusMessage>& messages) {
    std::size_t i = 0;
    if (words.size() >= 2 && lower_ascii(words[0]) == "set" && lower_ascii(words[1]) == "order") {
        i = 2;
    } else if (!words.empty() && lower_ascii(words[0]) == "setorder") {
        i = 1;
    } else {
        return false;
    }

    bool ascending = orderstate::isAscending(area);
    if (words.size() > i && parse_direction_word(words.back(), ascending)) {
        words.pop_back();
    }

    if (i < words.size() && lower_ascii(words[i]) == "to") {
        ++i;
    }
    if (i >= words.size()) {
        return false;
    }

    if (is_physical_order_token(words[i])) {
        xindex::ensure_manager(area).close();
        orderstate::clearOrder(area);
        messages.push_back(info("gui.order.cleared", "GUI order returned to physical record order."));
        return true;
    }

    std::filesystem::path container;
    std::string tag;
    if (lower_ascii(words[i]) == "tag") {
        if (i + 1 >= words.size()) {
            return false;
        }
        tag = words[i + 1];
    } else if (i + 1 < words.size()) {
        container = resolve_gui_index_token(area, words[i], is_v64_area(area) ? ".cdx" : ".cnx");
        tag = words[i + 1];
    } else {
        tag = words[i];
    }

    if (container.empty()) {
        const std::string attached = orderstate::hasOrder(area) ? orderstate::orderName(area) : std::string{};
        if (!attached.empty() && (ends_with_ci(attached, ".cdx") || ends_with_ci(attached, ".cnx"))) {
            container = attached;
        } else {
            container = default_order_container_for_area(area);
        }
    }

    std::string err;
    if (activate_gui_order(area, container, tag, ascending, err)) {
        messages.push_back(info("gui.order.activated",
                                "GUI activated the same ordered index used by the DotTalk++ shell.",
                                container.string() + " TAG " + upper_ascii(tag) +
                                    (ascending ? " ASC" : " DESC")));
        return true;
    }

    messages.push_back(warning("gui.order.activate_failed",
                               "DotTalk++ shell order succeeded, but GUI order activation failed.",
                               err));
    return false;
}

bool mirror_order_direction_to_gui(xbase::DbArea& area,
                                   bool ascending,
                                   std::vector<StatusMessage>& messages) {
    if (!orderstate::hasOrder(area)) {
        return false;
    }
    orderstate::setAscending(area, ascending);
    std::string err;
    if (!position_gui_area_to_first_ordered(area, err)) {
        messages.push_back(warning("gui.order.position_failed",
                                   "GUI order direction changed, but cursor positioning failed.",
                                   err));
    }
    messages.push_back(info("gui.order.direction",
                            ascending ? "GUI order direction is ascending." : "GUI order direction is descending."));
    return true;
}

std::string order_kind(const xbase::DbArea& area) {
    if (!orderstate::hasOrder(area)) {
        return "PHYSICAL";
    }
    if (orderstate::isCdx(area)) {
        return "CDX";
    }
    if (orderstate::isCnx(area)) {
        return "CNX";
    }
    if (orderstate::isInx(area)) {
        return "INX";
    }
    if (orderstate::isSix(area)) {
        return "SIX";
    }
    if (orderstate::isSnx(area)) {
        return "SNX";
    }
    if (orderstate::isIsx(area)) {
        return "ISX";
    }
    if (orderstate::isCsx(area)) {
        return "CSX";
    }
    return "ORDER";
}

std::string order_backend(const xbase::DbArea& area) {
    if (!orderstate::hasOrder(area)) {
        return "physical";
    }
    if (const auto* index = xindex::manager_if_attached(area); index && index->hasBackend()) {
        if (index->isCdx()) {
            return "CDX/LMDB";
        }
        if (index->isCnx()) {
            return "CNX";
        }
        return "xindex";
    }
    return "orderstate";
}

std::string schema_index_type(const xbase::DbArea& area) {
    if (orderstate::isCdx(area) || area.kind() == xbase::AreaKind::V64 || area.kind() == xbase::AreaKind::V128) {
        return "CDX";
    }
    if (orderstate::isInx(area)) {
        return "INX";
    }
    if (orderstate::isCnx(area)) {
        return "CNX";
    }
    if (area.kind() == xbase::AreaKind::V32) {
        return "CNX";
    }
    return {};
}

bool output_clears_relations(const std::string& output) {
    std::istringstream stream(output);
    std::string line;
    while (std::getline(stream, line)) {
        const std::string text = lower_ascii(trim_ascii(line));
        if (text.rfind("rel: cleared all", 0) == 0 ||
            text.rfind("relations: cleared", 0) == 0 ||
            text.rfind("workspace close:", 0) == 0) {
            return true;
        }
    }
    return false;
}

std::string first_token_from_command_text(const std::string& text) {
    std::istringstream stream(text);
    std::string token;
    stream >> token;
    return lower_ascii(token);
}

std::string resolve_shell_shortcut(std::string command) {
    return trim_ascii(shell_shortcuts::resolve(trim_ascii(std::move(command))));
}

int edit_distance_limited(const std::string& a, const std::string& b, int limit) {
    if (std::abs(static_cast<int>(a.size()) - static_cast<int>(b.size())) > limit) {
        return limit + 1;
    }

    std::vector<int> prev(b.size() + 1);
    std::vector<int> cur(b.size() + 1);
    for (std::size_t j = 0; j <= b.size(); ++j) {
        prev[j] = static_cast<int>(j);
    }

    for (std::size_t i = 1; i <= a.size(); ++i) {
        cur[0] = static_cast<int>(i);
        int row_best = cur[0];
        for (std::size_t j = 1; j <= b.size(); ++j) {
            const int cost = a[i - 1] == b[j - 1] ? 0 : 1;
            cur[j] = std::min({prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost});
            row_best = std::min(row_best, cur[j]);
        }
        if (row_best > limit) {
            return limit + 1;
        }
        std::swap(prev, cur);
    }
    return prev[b.size()];
}

const std::set<std::string>& gui_known_command_verbs() {
    static const std::set<std::string> verbs = [] {
        std::set<std::string> out {
            "help", "aiuto", "about", "openarch", "architecture",
            "area", "areas", "workspace", "graph", "status", "paths", "setpath",
            "select", "dbarea", "recno", "goto", "go", "skip", "top", "bottom",
            "list", "browse", "structure", "cli", "ersatz", "dir", "area51",
            "do", "run", "dotscript", "scan", "endscan", "loop", "endloop",
            "while", "endwhile", "until", "enduntil", "var", "set",
            "smart", "sm", "smartbrowse", "smartbrowser", "smartlist", "sl",
            "use", "close", "gps", "lock", "unlock", "replace", "append",
            "delete", "recall", "seek", "find", "locate", "continue",
            "bang", "formula", "cmdhelp", "foxhelp", "pshell", "browsetui",
            "tvision", "foxtalk", "test", "lmdb_util", "table_buffer",
            "simplebrowse", "tuple", "descend", "evaluate", "boolean"
        };
        for (const auto& action : gui_command_catalog()) {
            const std::string token = first_token_from_command_text(action.command);
            if (!token.empty()) {
                out.insert(token);
            }
        }
        return out;
    }();
    return verbs;
}

bool should_auto_bridge_command(const std::string& verb) {
    if (verb.empty()) {
        return false;
    }
    return gui_known_command_verbs().find(verb) != gui_known_command_verbs().end();
}

std::string command_suggestion(const std::string& verb) {
    if (verb.empty()) {
        return {};
    }

    std::string best;
    int best_distance = 3;
    for (const auto& candidate : gui_known_command_verbs()) {
        const int distance = edit_distance_limited(verb, candidate, 2);
        if (distance < best_distance) {
            best = candidate;
            best_distance = distance;
        }
    }
    return best_distance <= 2 ? best : std::string{};
}

// AIF-078: the conversion visible_area_id -- id minus 1 -- lived here, in
// main_frame.cpp and in
// gui_workspace_format.cpp -- three identical copies of a rung conversion, which
// is three more than D10 R3 allows. The one survivor is
// model.hpp's format_area_ordinal(), and the ordinal it formats is now looked up
// in the area list rather than reconstructed by arithmetic from an identity.

std::string dbf_flavor_label(const xbase::DbArea& area) {
    std::ostringstream out;
    switch (area.versionByte()) {
    case 0x03:
        out << "xBase/dbf v32";
        break;
    case 0x83:
        out << "xBase/dbf v32 memo";
        break;
    case 0xF5:
        out << "FoxPro v32 memo";
        break;
    case 0x30:
        out << "Visual FoxPro/v64";
        break;
    case 0x31:
        out << "Visual FoxPro/v64 autoinc";
        break;
    case 0x32:
        out << "Visual FoxPro/v64 variable";
        break;
    case 0x64:
        out << "x64base/x64";
        break;
    default:
        out << "unknown";
        break;
    }
    out << " (version 0x"
        << std::uppercase << std::hex << std::setw(2) << std::setfill('0')
        << static_cast<int>(area.versionByte()) << ")";
    return out.str();
}

std::string comparable_path(std::filesystem::path path) {
    std::error_code ec;
    path = std::filesystem::weakly_canonical(path, ec);
    if (ec) {
        path = std::filesystem::absolute(path, ec);
    }
    std::string text = path.lexically_normal().string();
#ifdef _WIN32
    text = lower_ascii(std::move(text));
#endif
    return text;
}

bool is_dbf_file(const std::filesystem::directory_entry& entry) {
    if (!entry.is_regular_file()) {
        return false;
    }
    if (lower_ascii(entry.path().extension().string()) != ".dbf") {
        return false;
    }
    // Engine scratch is not a user table. See dottalk/scratch_sidecar.hpp.
    return !dottalk::is_engine_scratch_table(entry.path());
}

bool workspace_dbf_path_less_like_cli(const std::filesystem::path& left,
                                      const std::filesystem::path& right) {
    return lower_ascii(left.filename().string()) < lower_ascii(right.filename().string());
}

void write_cli_result(std::ostringstream& out, const RuntimeCliResult& cli) {
    out << "External DotTalk++ CLI";
    if (!cli.executable.empty()) {
        out << " (" << cli.executable.string() << ")";
    }
    out << "\nexit=" << cli.exit_code << "\n";
    if (!cli.output.empty()) {
        out << cli.output;
    }
    if (!cli.detail.empty()) {
        out << cli.detail << "\n";
    }
}

std::filesystem::path gui_source_root() {
#ifdef DOTTALK_GUI_SOURCE_ROOT
    return std::filesystem::path(DOTTALK_GUI_SOURCE_ROOT);
#else
    return std::filesystem::current_path();
#endif
}

std::filesystem::path first_existing_dir(const std::vector<std::filesystem::path>& candidates) {
    for (const auto& candidate : candidates) {
        std::error_code ec;
        if (!candidate.empty() && std::filesystem::is_directory(candidate, ec)) {
            return std::filesystem::absolute(candidate, ec).lexically_normal();
        }
    }
    return {};
}

std::filesystem::path gui_data_root() {
    std::vector<std::filesystem::path> candidates;
    if (const char* env = std::getenv("DOTTALKPP_DATA")) {
        candidates.emplace_back(env);
    }
    if (const char* env = std::getenv("DOTTALK_DATA")) {
        candidates.emplace_back(env);
    }
    const auto source = gui_source_root();
    candidates.push_back(source / "dottalkpp" / "data");
    candidates.push_back(source / "data");
    candidates.push_back(std::filesystem::current_path());
    return first_existing_dir(candidates);
}

std::filesystem::path gui_bin_root() {
#ifdef DOTTALK_GUI_BINARY_DIR
    const std::filesystem::path binary_root(DOTTALK_GUI_BINARY_DIR);
    std::vector<std::filesystem::path> candidates {
        binary_root / "src" / "Release",
        binary_root / "src" / "Debug",
        binary_root / "src" / "RelWithDebInfo",
        binary_root
    };
    if (const auto found = first_existing_dir(candidates); !found.empty()) {
        return found;
    }
#endif
    return gui_source_root() / "build" / "src" / "Release";
}

std::filesystem::path gui_app_bin_root() {
    if (const char* env = std::getenv("DOTTALKPP_GUI_BIN")) {
        if (const auto found = first_existing_dir({std::filesystem::path(env)}); !found.empty()) {
            return found;
        }
    }
    return {};
}

std::vector<std::filesystem::path> lifecycle_script_candidates(const std::string& name) {
    const auto data = dottalk::paths::get_slot(dottalk::paths::Slot::DATA);
    const auto root = data.empty() ? gui_source_root() : data.parent_path();
    return {
        gui_app_bin_root() / name,
        data / name,
        gui_bin_root() / name,
        root / "bin" / name,
        root / name,
        gui_source_root() / name
    };
}

std::vector<std::filesystem::path> existing_lifecycle_scripts(const std::vector<std::string>& names) {
    std::vector<std::filesystem::path> out;
    for (const auto& name : names) {
        for (const auto& candidate : lifecycle_script_candidates(name)) {
            std::error_code ec;
            if (std::filesystem::is_regular_file(candidate, ec)) {
                out.push_back(std::filesystem::absolute(candidate, ec).lexically_normal());
                break;
            }
        }
    }
    return out;
}

void initialize_gui_paths() {
    const auto data = gui_data_root();
    if (!data.empty()) {
        dottalk::paths::initialize(gui_bin_root(), data);
        dottalk::paths::ensure_directories();
    }
}

void run_lifecycle_scripts(GuiShellRuntime& runtime, const std::vector<std::string>& names) {
    for (const auto& script : existing_lifecycle_scripts(names)) {
        RuntimeCliResult ignored = runtime.run(RuntimeCliRequest{
            .command = "DOTSCRIPT " + script.string(),
        });
        (void)ignored;
    }
}

} // namespace

struct Session::Impl {
    // AIF-078 slot lane, step 2b. THE AREA IS BORROWED, NOT OWNED.
    //
    // It used to hold `xbase::DbArea area;` BY VALUE, and that one fact is what
    // made a session-owned area second class: setEngineSlot() has exactly one
    // caller in the tree -- XBaseEngine's constructor in dbf_file.cpp, over the
    // engine's own array, named rather than numbered because the line number
    // this comment used to carry was already wrong. An area outside that array
    // could never have an engine slot and carried -1 for life. -1 is ALSO the
    // member array's free-slot sentinel, so join(h, -1)
    // matched the first FREE slot and claimed nothing, and leave(h, -1) cleared
    // nothing. Membership could not see these areas at all.
    //
    // Now it holds a reference into the engine's array, at a slot claimed from
    // the same allocator the CLI's USE ... IN FREE uses. join() and leave() are
    // already called from DbArea::open()/close(); they simply start receiving a
    // REAL slot. Nothing else had to change for membership to become true.
    struct Area {
        // R6: an absent value must not be representable among present ones.
        // There is NO default constructor, so an unbound Area cannot exist and
        // area() has no absent case to defend against across its 132 callers.
        Area(xbase::XBaseEngine& eng, int slot) noexcept : eng_(&eng), slot_(slot) {}

        // RAII PRESERVED ACROSS THE OWNERSHIP CHANGE, and this destructor is
        // load-bearing. Before 2b, `areas.clear()` closed files implicitly --
        // destroying an Area destroyed its by-value DbArea and ~DbArea() calls
        // close(). The DbArea is no longer ours to destroy, so without this the
        // three clears and one erase would stop closing anything: files left
        // open, slots left claimed, NO compile error and no failing test. A
        // silent leak. Keeping the release here means those four call sites need
        // no edits at all, and close() does workspace::leave() itself.
        ~Area() {
            try {
                if (eng_ && slot_ >= 0) eng_->area(slot_).close();
            } catch (...) {
                // A destructor may not throw. Losing the close is bad; losing
                // the process is worse.
            }
        }

        Area(const Area&)            = delete;
        Area& operator=(const Area&) = delete;

        AreaId id {0};
        std::filesystem::path path;
        std::string display_name;

        // The ENGINE slot -- the number that means AREA <n> in the CLI, in a
        // posture, and in SELECT n. Step 3 re-points the GUI's positional rung
        // at this instead of at the list index.
        int slot() const noexcept { return slot_; }

        xbase::DbArea&       area()       { return eng_->area(slot_); }
        const xbase::DbArea& area() const { return eng_->area(slot_); }

    private:
        xbase::XBaseEngine* eng_;
        int                 slot_;
    };

    Area* active_area() {
        return find_area(active_area_id);
    }

    const Area* active_area() const {
        return find_area(active_area_id);
    }

    Area* find_area(AreaId id) {
        for (const auto& area : areas) {
            if (area->id == id) {
                return area.get();
            }
        }
        return nullptr;
    }

    const Area* find_area(AreaId id) const {
        for (const auto& area : areas) {
            if (area->id == id) {
                return area.get();
            }
        }
        return nullptr;
    }

    // The identity rung -> the positional rung. A LOOKUP, not arithmetic, and
    // it fails in the return value (D10 R3): an id that is not in the list has
    // no position, and under R6.3 that is an EMPTY OPTIONAL rather than a
    // reserved number -- so a caller cannot forget to check it and then do
    // arithmetic on the answer.
    MaybeAreaOrdinal ordinal_of(AreaId id) const {
        for (const auto& area : areas) {
            if (area->id == id) {
                // AIF-078 step 3 (ruling R120, 2026-08-24). THE ENGINE SLOT,
                // not the list index. Still a lookup and still downward-only;
                // what changed is WHICH positional rung this session reports,
                // so that "area 5" means the same area whether it is typed at
                // the GUI or at the CLI.
                return static_cast<AreaOrdinal>(area->slot());
            }
        }
        return std::nullopt;
    }

    // The positional rung -> the identity rung. Also a lookup. Takes the
    // optional so "no ordinal" and "no area at that position" both land on the
    // same honest nullptr, and neither needs a magic number to say so.
    //
    // AIF-078 step 3. This SEARCHES rather than indexes, and that is the shape
    // change, not a cost. The old bounds test `*ordinal >= areas.size()` was
    // only correct while the position WAS the index; a slot is an address in
    // the engine's array of MAX_AREA, so a session holding two areas can hold
    // slots 0 and 7, and "is 7 past the end of a list of 2" is the wrong
    // question. Asking which area SITS at 7 is the right one, and it answers
    // absent for a slot this session does not hold.
    Area* find_area_by_ordinal(const MaybeAreaOrdinal& ordinal) {
        if (!ordinal) return nullptr;
        for (const auto& area : areas) {
            if (static_cast<AreaOrdinal>(area->slot()) == *ordinal) return area.get();
        }
        return nullptr;
    }

    const Area* find_area_by_ordinal(const MaybeAreaOrdinal& ordinal) const {
        if (!ordinal) return nullptr;
        for (const auto& area : areas) {
            if (static_cast<AreaOrdinal>(area->slot()) == *ordinal) return area.get();
        }
        return nullptr;
    }

    // What to SHOW. Every caller that used to write visible_area_id writes
    // this instead, so the list is consulted exactly once per printed number.
    std::string visible_ordinal(AreaId id) const {
        return format_area_ordinal(ordinal_of(id));
    }

    Area* find_area_by_path(const std::filesystem::path& path) {
        const std::string wanted = comparable_path(path);
        for (const auto& area : areas) {
            if (comparable_path(area->path) == wanted) {
                return area.get();
            }
        }
        return nullptr;
    }

    Area* find_area_by_user_token(const std::string& token) {
        if (token.empty()) {
            return nullptr;
        }

        long long visible = 0;
        if (parse_i64(token, visible) && visible >= 0) {
            // What the user typed is a POSITION. It was previously turned into
            // an identity by adding 1, which agreed with the mint counter only
            // until the first close.
            return find_area_by_ordinal(static_cast<AreaOrdinal>(visible));
        }

        const std::string wanted = lower_ascii(token);
        for (const auto& area : areas) {
            std::vector<std::string> names {
                area->display_name,
                area->path.filename().string(),
                area->path.stem().string(),
                area->area().logicalName()
            };
            for (auto name : names) {
                name = lower_ascii(std::move(name));
                if (name == wanted || name == wanted + ".dbf") {
                    return area.get();
                }
            }
        }
        return nullptr;
    }

    // ---- AIF-078: relation ENDPOINT matching, ONE spelling ---------------
    //
    // A relation edge names its endpoints as TEXT -- whatever the CLI printed
    // or a DTSCHEMA2 posture carried -- and an area answers to four different
    // spellings of itself. Deciding whether a given area IS a given endpoint is
    // a real question with a real answer, and it used to be asked in exactly
    // one place: a lambda inside workspace_model(), reachable only by building
    // a whole model.
    //
    // It was lifted here on 2026-08-24 because close_area and the display side
    // both asked it and a second spelling is the R5 defect. R123 then deleted
    // the display-side caller, so TODAY THERE IS ONE CALLER --
    // drop_relations_naming. That is recorded rather than quietly tidied: the
    // predicate stays factored because the question is a real one with a real
    // answer, not because two places happen to ask it this week. Behaviour is
    // unchanged from the lift: same four names, same lowering, same .dbf
    // strip.
    static std::vector<std::string> relation_names_of(const Area& area) {
        std::vector<std::string> names {
            area.area().logicalName(),
            area.display_name,
            area.path.filename().string(),
            area.path.stem().string()
        };
        for (auto& name : names) {
            name = lower_ascii(trim_ascii(std::move(name)));
            if (ends_with_ci(name, ".dbf")) {
                name.resize(name.size() - 4);
            }
        }
        return names;
    }

    // Does `area` answer to the endpoint name `relation_table`? An EMPTY name
    // never matches -- neither an endpoint with no text nor an area with no
    // logical name -- because "both are blank" is not a match, it is two
    // absences, and treating it as one would drop every relation on the first
    // close of an unnamed area.
    static bool area_answers_to(const Area& area, const std::string& relation_table) {
        const std::string wanted = lower_ascii(trim_ascii(relation_table));
        if (wanted.empty()) {
            return false;
        }
        for (const auto& name : relation_names_of(area)) {
            if (!name.empty() && name == wanted) {
                return true;
            }
        }
        return false;
    }

    // THE DISPLAY-SIDE LOOKUP WAS DELETED BY R123, and it is worth saying why
    // rather than leaving a gap. area_for_relation_endpoint resolved a relation
    // ENDPOINT NAME to an open area, and its only caller was the match counter.
    // With the counter gone it had zero call sites -- the AIF-079 shape this
    // project already pays to name -- so it went with it. Nothing else in the
    // GUI has ever needed to turn a relation endpoint into an area; the counter
    // was the only reason that question was ever asked here.

    // Drop every relation edge naming `area` on either side; return how many
    // went. THE CLOSE SIDE.
    //
    // MUST BE CALLED BEFORE DbArea::close(). relation_names_of reads
    // logicalName() off the LIVE area, and close() clears area identity
    // (dbarea.cpp) -- so an area closed first answers to one fewer name than it
    // did a line earlier, and an edge written against its logical name would
    // survive the close of its own table. There is no compile error for getting
    // that order wrong and the result has the same SHAPE either way, which is
    // why the order is stated here instead of left to be noticed.
    std::size_t drop_relations_naming(const Area& area) {
        const auto before = relations.size();
        relations.erase(
            std::remove_if(relations.begin(), relations.end(),
                [&](const WorkspaceRelationInfo& relation) {
                    return area_answers_to(area, relation.parent) ||
                           area_answers_to(area, relation.child);
                }),
            relations.end());
        return before - relations.size();
    }

    // DECLARED BEFORE `areas` ON PURPOSE. Members are destroyed in REVERSE
    // declaration order, so this engine is torn down AFTER the areas that hold
    // references into its array. Swap these two lines and every ~Area() runs
    // against a destroyed engine -- which would compile, and would not
    // necessarily fail a test.
    xbase::XBaseEngine engine;

    // Claim a slot for a new area, or -1. ONE allocator, shared with the CLI:
    // xbase::find_free_area_for_workspace grows this workspace's own block
    // first and falls back to the lowest free slot anywhere, reporting when it
    // breaks contiguity (owner rulings 2026-08-22, "scoped" and "keep the areas
    // contiguous"). A second free-slot policy for the same array is R5's defect.
    int claim_area_slot(bool& broke_contiguity) {
        return xbase::find_free_area_for_workspace(
            &engine,
            xbase::workspace::default_table(),
            xbase::workspace::current_handle(),
            broke_contiguity);
    }

    std::vector<std::unique_ptr<Area>> areas;

    // R128. WHICH AREA, IF ANY, ALREADY HOLDS THIS FILE. The re-entry rule
    // needs it: a second OPEN of the same directory adds what is new and
    // touches nothing else. Compared by CANONICAL path, because the caller
    // holds a directory_entry path and the Area holds whatever it was opened
    // with -- comparing raw strings would answer NO for a file plainly open,
    // and a wrong NO here reopens an area someone is working in.
    Area* holding(const std::filesystem::path& want_in) {
        std::error_code ec;
        std::filesystem::path want = std::filesystem::weakly_canonical(want_in, ec);
        if (ec) want = want_in;
        for (const auto& a : areas) {
            std::error_code ec2;
            std::filesystem::path have = std::filesystem::weakly_canonical(a->path, ec2);
            if (ec2) have = a->path;
#if defined(_WIN32)
            // Windows paths are case-insensitive; comparing case-sensitively
            // would miss a file that is plainly open under another spelling.
            std::string hs = have.string();
            std::string ws = want.string();
            std::transform(hs.begin(), hs.end(), hs.begin(),
                           [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
            std::transform(ws.begin(), ws.end(), ws.begin(),
                           [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
            if (hs == ws) return a.get();
#else
            if (have == want) return a.get();
#endif
        }
        return nullptr;
    }

    std::vector<WorkspaceRelationInfo> relations;
    AreaId active_area_id {0};
    std::unique_ptr<GuiShellRuntime> shell_runtime {make_script_shell_runtime()};
};

Session::Session()
    : impl_(std::make_unique<Impl>()) {
    initialize_gui_paths();
    std::vector<StatusMessage> ignored_messages;
    for (const auto& script : existing_lifecycle_scripts({"init.ini", "dottalkpp.ini", "dotscript.ini"})) {
        RuntimeCliResult cli = impl_->shell_runtime->run(RuntimeCliRequest{
            .command = "DOTSCRIPT " + script.string(),
        });
        mirror_setpath_output_to_gui(cli.output, ignored_messages);
        if (output_clears_relations(cli.output)) {
            impl_->relations.clear();
        }
        if (!cli.ok) {
            continue;
        }
        if (const auto workspace_dir = workspace_open_dir_from_cli_output(cli.output)) {
            (void)mirror_workspace_open_directory(*workspace_dir, cli.output, {}, ignored_messages);
        }
        if (const auto schema = workspace_load_schema_from_cli_output(cli.output, script.string())) {
            (void)mirror_workspace_load_schema(*schema, ignored_messages);
        }
        for (auto relation : parse_relation_edges_from_output(cli.output, owning_workspace_now())) {
            merge_relation(impl_->relations, std::move(relation));
        }
    }
}

Session::~Session() {
    run_lifecycle_scripts(*impl_->shell_runtime, {"shutdown.ini"});
}

OpenTableResult Session::open_table(const OpenTableRequest& request) {
    OpenTableResult result;
    result.path = request.path;
    result.display_name = request.path.filename().string();

    if (request.path.empty()) {
        result.messages.push_back(warning("gui.open_table.path_missing", "No table path was provided."));
        return result;
    }

    try {
        if (auto* existing = impl_->find_area_by_path(request.path)) {
            impl_->active_area_id = existing->id;
            result.ok = true;
            result.area_id = existing->id;
            result.ordinal = impl_->ordinal_of(existing->id);
            result.workspace = gui_workspace_of_area(existing->area());
            result.path = existing->path;
            result.display_name = existing->display_name;
            result.record_count = existing->area().isOpen() ? existing->area().recCount64() : 0;
            result.messages.push_back(info("gui.open_table.already_open",
                                           "Table already open; selected existing GUI work area."));
            return result;
        }

        bool broke_contiguity = false;
        const int slot = impl_->claim_area_slot(broke_contiguity);
        if (slot < 0) {
            // The CLI already ruled this, and the GUI adopts its answer rather
            // than inventing a second spelling for the same refusal (R5).
            // cmd_use.cpp:766 -- "Deliberately NOT falling back to the current
            // area. Falling back is the silent-replacement behaviour this lane
            // exists to kill."
            throw std::runtime_error(
                "no unoccupied work area (all " + std::to_string(xbase::MAX_AREA) +
                " are in use). Nothing was opened.");
        }
        auto area = std::make_unique<Impl::Area>(impl_->engine, slot);
        area->path = request.path;
        area->display_name = result.display_name;
        area->area().open(request.path.string());
        // AIF-078. The identity is the ENGINE'S, and it does not exist until the
        // area is open -- which is why this assignment now sits BELOW open()
        // rather than above it. The old counter was spent before open() could
        // throw, so every failed open burned an id that nothing ever held.
        area->id = area->area().areaHandle();

        result.ok = true;
        result.area_id = area->id;
        // AIF-078 step 3. THE SLOT IT CLAIMED, read off the area itself.
        //
        // This used to be `impl_->areas.size()` read before the push -- the
        // index it was about to occupy. That number was correct and meant the
        // wrong thing: it answered "where in this list" when the CLI answering
        // the same question says "which engine slot". Reading it off the area
        // removes the read-order dependency as well; there is no longer a
        // before-the-push and an after-the-push answer.
        result.ordinal = static_cast<AreaOrdinal>(area->slot());
        result.record_count = area->area().recCount64();
        // Asked of the AREA, which is the only rung that can answer it.
        result.workspace = gui_workspace_of_area(area->area());
        if (result.display_name.empty()) {
            result.display_name = area->area().logicalName();
            area->display_name = result.display_name;
        }
        impl_->active_area_id = area->id;
        impl_->areas.push_back(std::move(area));
        result.messages.push_back(info("gui.open_table.opened", "Table opened in a new GUI work area."));
    } catch (const std::exception& ex) {
        result.messages.push_back(error("gui.open_table.failed", "Unable to open table.", ex.what()));
    } catch (...) {
        result.messages.push_back(error("gui.open_table.failed", "Unable to open table.", "unknown error"));
    }

    return result;
}


// ---------------------------------------------------------------------------
// R128 ON THE GUI SURFACE (owner, 2026-08-26).
//
// Two things were true here and neither was a display bug. The mirrors CLOSED
// EVERY AREA before opening, so the Workbench could not hold two workspaces at
// once; and `src/gui` called workspace::create() and set_current_handle() in
// ZERO places, so an area opened here could only ever join DEFAULT. The second
// is why `WS: DEFAULT` on every row after a load was a TRUE report -- the GUI
// had no way to be anywhere else.
//
// WHAT THIS GIVES THE GUI AND WHAT IT DOES NOT. It gets a RUNTIME workspace:
// a handle, a name, membership, and therefore an honest WS column and a
// scopeable close. It does NOT get a WS_ID. The durable birth row is written
// by ws_memo::ensure_durable_workspace in cmd_workspace.cpp, and R122 ruled
// that src/gui does not link src/cli -- the GUI reaches the engine by SPAWNING
// a dottalkpp. In the mirror case that is not a hole: the CLI subprocess this
// call is mirroring ALREADY wrote the durable row for this name. It is a hole
// for any workspace the GUI ever creates on its own, and this comment is here
// so that is found by reading rather than by surprise.
// ---------------------------------------------------------------------------
namespace {

// Enter the workspace `nm` in the GUI's OWN handle space, creating it if
// needed. Returns 0 on refusal.
std::uint64_t gui_enter_workspace(const std::string& nm,
                                  std::vector<StatusMessage>& messages) {
    if (nm.empty()) return 0;
    std::uint64_t h = xbase::workspace::find_by_name_ci(nm);
    if (h == 0) h = xbase::workspace::create(nm, 0);
    if (h == 0) {
        messages.push_back(warning("gui.workspace.create_failed",
                                   "The GUI could not create a workspace for this open.",
                                   nm));
        return 0;
    }
    if (!xbase::workspace::set_current_handle(h)) {
        messages.push_back(warning("gui.workspace.enter_failed",
                                   "The GUI created a workspace but could not enter it.",
                                   nm));
        return 0;
    }
    return h;
}


// THE LABEL IS PROVENANCE, NOT A NAME, and the first cut of this change missed
// that. mirror_workspace_posture takes `label` from three call sites and none
// of them is a workspace name: the FILE carrier passes a whole
// schema_path.string(), the memo carrier passes "memo:" + name, and the MINIDB
// carrier passes "minidb:" + name. Handing that straight to a workspace would
// have produced a handle named after an absolute path -- past WS_NAME's 32
// characters more often than not.
//
// FOUND BY RUNNING THE FIXTURE, 2026-08-26: dottalkpp_gui_area_membership_test
// went red, its own G1 guard still green (both tables opened), which is the
// signature of a placement fault rather than an open fault.
//
// A LABEL THAT YIELDS NO USABLE NAME IS NOT AN ERROR HERE. The caller stays in
// whatever workspace it was in, which is exactly the pre-R128 behaviour, and
// says so. Refusing the whole load because its provenance string is long would
// trade a naming inconvenience for a failure to open anything.
std::string gui_workspace_name_from_label(const std::string& label) {
    std::string body = label;
    for (const std::string_view prefix : {std::string_view("memo:"), std::string_view("minidb:")}) {
        if (body.rfind(prefix, 0) == 0) { body = body.substr(prefix.size()); break; }
    }
    if (body.empty()) return {};

    // Anything still carrying a separator is a path; take its stem.
    if (body.find('/') != std::string::npos || body.find('\\') != std::string::npos) {
        body = std::filesystem::path(body).stem().string();
    } else {
        const std::filesystem::path as_path(body);
        if (as_path.has_extension()) body = as_path.stem().string();
    }
    if (body.empty()) return {};
    if (body.size() > xbase::workspace::kMaxWorkspaceNameChars) return {};
    return body;
}

// The handles a scoped act covers: the current workspace and, when SET
// RECURSION is ON, its descendants. Mirrors close_workspace_tree in
// cmd_workspace.cpp -- same children(), same switch, same depth cap, same
// cycle guard -- because a GUI that meant something different by "this
// workspace" would give one question two answers across two surfaces.
void gui_collect_scope(std::uint64_t h, bool recursive, int depth,
                       std::set<std::uint64_t>& seen) {
    if (!xbase::workspace::exists(h)) return;
    if (!seen.insert(h).second) return;
    if (depth > xbase::workspace::kMaxWorkspaceDepth) return;
    if (!recursive) return;
    for (const auto c : xbase::workspace::children(h)) {
        gui_collect_scope(c, recursive, depth + 1, seen);
    }
}

}  // namespace

std::size_t Session::mirror_workspace_open_directory(const std::filesystem::path& dir,
                                                     const std::string& shell_output,
                                                     const std::string& index_mode,
                                                     std::vector<StatusMessage>& messages) {
    std::error_code ec;
    if (dir.empty() || !std::filesystem::is_directory(dir, ec)) {
        messages.push_back(warning("gui.workspace.open_dir_missing",
                                   "WORKSPACE OPEN did not mirror into GUI areas because the directory was not found.",
                                   dir.string()));
        return 0;
    }

    // R128. The close-all that stood here is gone: OPEN is additive, so a
    // second directory joins the session rather than replacing it. Relations
    // and the active area are left alone for the same reason -- clearing them
    // would discard state belonging to workspaces this open never touched.
    std::string name_err;
    const std::string ws_name = xbase::workspace::name_for_directory(dir, name_err);
    if (ws_name.empty()) {
        messages.push_back(warning("gui.workspace.open_dir_unnameable",
                                   "WORKSPACE OPEN did not mirror because the directory implies no usable workspace name.",
                                   dir.string() + ": " + name_err));
        return 0;
    }
    if (gui_enter_workspace(ws_name, messages) == 0) return 0;

    std::vector<std::filesystem::path> dbfs;
    for (const auto& entry : std::filesystem::directory_iterator(dir, ec)) {
        if (!ec && is_dbf_file(entry)) {
            dbfs.push_back(entry.path());
        }
    }
    std::sort(dbfs.begin(), dbfs.end(), workspace_dbf_path_less_like_cli);

    std::size_t opened = 0;
    std::size_t already = 0;
    for (const auto& dbf : dbfs) {
        // R128 re-entry: a second OPEN of a directory already open adds only
        // what is new. Reopening would close and reopen an area the user may
        // be sitting in, which is the destructive act this ruling stops.
        if (impl_->holding(dbf) != nullptr) { ++already; continue; }
        try {
            bool broke_contiguity = false;
            const int slot = impl_->claim_area_slot(broke_contiguity);
            if (slot < 0) {
                // The CLI already ruled this, and the GUI adopts its answer rather
                // than inventing a second spelling for the same refusal (R5).
                // cmd_use.cpp:766 -- "Deliberately NOT falling back to the current
                // area. Falling back is the silent-replacement behaviour this lane
                // exists to kill."
                throw std::runtime_error(
                    "no unoccupied work area (all " + std::to_string(xbase::MAX_AREA) +
                    " are in use). Nothing was opened.");
            }
            auto area = std::make_unique<Impl::Area>(impl_->engine, slot);
            area->path = dbf;
            area->display_name = dbf.filename().string();
            area->area().open(dbf.string());
            area->id = area->area().areaHandle();
            impl_->active_area_id = area->id;
            impl_->areas.push_back(std::move(area));
            ++opened;
        } catch (const std::exception& ex) {
            messages.push_back(warning("gui.workspace.open_table_failed",
                                       "A WORKSPACE OPEN table could not be mirrored into a GUI area.",
                                       dbf.string() + ": " + ex.what()));
        } catch (...) {
            messages.push_back(warning("gui.workspace.open_table_failed",
                                       "A WORKSPACE OPEN table could not be mirrored into a GUI area.",
                                       dbf.string()));
        }
    }

    if (!impl_->areas.empty() && impl_->active_area_id == 0) {
        impl_->active_area_id = impl_->areas.front()->id;
    }
    if (already > 0) {
        messages.push_back(info("gui.workspace.open_reentry",
                                "WORKSPACE OPEN re-entered a workspace and left its open tables alone.",
                                std::to_string(already) + " table(s) already open in " + ws_name));
    }

    std::size_t indexes_attached = 0;
    std::set<AreaId> index_attached_area_ids;
    for (const auto& attachment : workspace_open_indexes_from_cli_output(shell_output, dir)) {
        // MEASURED WHILE DOING R120, AND NOT FIXED HERE. attachment.area_ordinal
        // was parsed out of the CLI's OWN output ("Area 3 [index: ...]"), so it
        // is an address in the CLI's engine. This lookup resolves it in the
        // GUI's engine, which is a different array. The two agree only because
        // the GUI mirrors the CLI's tables in the order reported, into a fresh
        // engine, so both count up from 0 together.
        //
        // That coincidence is OLDER than step 3 -- before it, this indexed the
        // GUI's list and relied on the same ordering. The change neither fixes
        // nor worsens it; it makes it VISIBLE, because both numbers now claim
        // to be slots and a reader can finally ask "slots in which engine".
        // A gap in the CLI's report loses the attachment either way.
        //
        // The honest fix is to match on PATH, which both sides already have
        // and which is engine-independent. Deliberately a separate change: it
        // is a behaviour fix, and this commit is a rung repoint.
        auto* area = impl_->find_area_by_ordinal(attachment.area_ordinal);
        if (!area || !area->area().isOpen()) {
            continue;
        }

        std::string err;
        if (attach_gui_order_container(area->area(), attachment.container, err)) {
            ++indexes_attached;
            index_attached_area_ids.insert(area->id);
        } else {
            messages.push_back(warning("gui.workspace.index_attach_failed",
                                       "A WORKSPACE OPEN index could not be mirrored into a GUI area.",
                                       attachment.container.string() + ": " + err));
        }
    }

    const std::string mode = upper_ascii(trim_ascii(index_mode));
    if (!mode.empty() && mode != "NOINDEX" && mode != "NOINDEXES" && mode != "NONE" && mode != "PHYSICAL") {
        for (const auto& area : impl_->areas) {
            if (!area->area().isOpen() || index_attached_area_ids.count(area->id) != 0) {
                continue;
            }

            const auto candidates = default_index_candidates_for_area(area->area(), area->path, mode);
            const auto container = first_existing_regular_file(candidates);
            if (!container) {
                continue;
            }

            std::string err;
            if (attach_gui_order_container(area->area(), *container, err)) {
                ++indexes_attached;
                index_attached_area_ids.insert(area->id);
            } else {
                messages.push_back(warning("gui.workspace.index_attach_failed",
                                           "A WORKSPACE OPEN index could not be mirrored into a GUI area.",
                                           container->string() + ": " + err));
            }
        }
    }

    messages.push_back(info("gui.workspace.open_mirrored",
                            "WORKSPACE OPEN mirrored DBF tables into GUI areas.",
                            std::to_string(opened) + " table(s)"));
    if (indexes_attached > 0) {
        messages.push_back(info("gui.workspace.indexes_mirrored",
                                "WORKSPACE OPEN mirrored attached index containers into GUI areas.",
                                std::to_string(indexes_attached) + " index container(s)"));
    }
    return opened;
}

std::size_t Session::mirror_workspace_load_schema(const std::filesystem::path& schema_path,
                                                  std::vector<StatusMessage>& messages) {
    std::error_code ec;
    if (schema_path.empty() || !std::filesystem::is_regular_file(schema_path, ec) || ec) {
        messages.push_back(warning("gui.workspace.schema_missing",
                                   "WORKSPACE LOAD did not mirror into GUI areas because the schema file was not found.",
                                   schema_path.string()));
        return 0;
    }
    std::ifstream file(schema_path, std::ios::binary);
    std::ostringstream text;
    text << file.rdbuf();
    // Empty roots: resolve members through the path slots, as this form always has.
    return mirror_workspace_posture(text.str(), schema_path.string(), {}, {}, messages);
}

std::size_t Session::mirror_memo_workspace(const std::string& name,
                                           std::vector<StatusMessage>& messages) {
    std::string error;
    const auto rows = gui_list_memo_workspaces(error);
    if (!error.empty()) {
        messages.push_back(warning("gui.workspace.catalog_unavailable",
                                   "WORKSPACE LOAD could not read the workspace catalog.", error));
        return 0;
    }

    // Live rows only, matching how the CLI resolves a workspace by name. A
    // superseded row of the same name is a different snapshot and is not what
    // "load by name" means.
    const MemoWorkspaceRow* row = nullptr;
    for (const auto& r : rows) {
        if (!r.superseded && r.name == name) row = &r;
    }
    if (!row) {
        messages.push_back(warning("gui.workspace.memo_name_missing",
                                   "WORKSPACE LOAD found no live memo workspace of that name.", name));
        return 0;
    }

    const std::string payload = gui_read_memo_payload(row->snapshot, error);
    if (!error.empty()) {
        messages.push_back(warning("gui.workspace.memo_read_failed",
                                   "WORKSPACE LOAD could not read the memo payload.", error));
        return 0;
    }

    // A posture-only payload names tables that already live on disk, so the
    // path slots resolve them exactly as a file-carried posture would.
    if (!dottalk::minidb::is_container(payload)) {
        return mirror_workspace_posture(payload, "memo:" + name, {}, {}, messages);
    }

    // A MINIDB payload carries the tables themselves. They must be hydrated
    // into the RAM VFS OF THIS PROCESS: xbase::ramfs is an in-process registry,
    // so a hydration performed by the CLI bridge's child process would be
    // invisible here. See include/dottalk/minidb_hydrate.hpp.
    const auto ram_root = dottalk::paths::get_slot(dottalk::paths::Slot::RAM);
    if (ram_root.empty()) {
        messages.push_back(warning("gui.workspace.ram_slot_missing",
                                   "WORKSPACE LOAD cannot hydrate a MINIDB payload: no RAM path slot "
                                   "is configured."));
        return 0;
    }

    // AIF-120. Mount the RAM disk HERE if it is not already, and say so.
    //
    // The obvious alternative -- refusing and telling the operator to run
    // VDISK MOUNT -- would be advice that cannot work. The GUI has no handler
    // for VDISK, so the command crosses the CLI bridge into a CHILD PROCESS,
    // and xbase::ramfs is by its own header an in-process registry. The mount
    // would land in the child and this process would stay exactly as unmounted
    // as before. A RAM disk is per-process by design; the Workbench needs its
    // own, and asking for the container is asking for somewhere to put it.
    if (!xbase::ramfs::mounted(ram_root.string())) {
        std::error_code ec;
        std::filesystem::create_directories(ram_root, ec);   // sidecars land on real disk
        xbase::ramfs::mount(ram_root.string());
        if (!xbase::ramfs::mounted(ram_root.string())) {
            messages.push_back(warning("gui.workspace.vdisk_mount_failed",
                                       "WORKSPACE LOAD could not mount a RAM disk for the hydrated "
                                       "workspace.", ram_root.string()));
            return 0;
        }
        messages.push_back(info("gui.workspace.vdisk_mounted",
                                "WORKSPACE LOAD mounted this process's RAM disk. A RAM disk is "
                                "per-process, so the Workbench keeps its own.",
                                ram_root.string()));
    }
    const std::filesystem::path ram_index_root = ram_root / "indexes";

    const auto scanned = dottalk::minidb::scan(payload);
    if (!scanned.ok) {
        messages.push_back(warning("gui.workspace.minidb_unreadable",
                                   "WORKSPACE LOAD could not read the MINIDB container.", scanned.error));
        return 0;
    }

    const auto placed = dottalk::minidb::materialize(payload, scanned, ram_root, ram_index_root);
    if (!placed.ok) {
        messages.push_back(warning("gui.workspace.minidb_hydrate_failed",
                                   "WORKSPACE LOAD could not hydrate the MINIDB container.", placed.error));
        return 0;
    }
    messages.push_back(info("gui.workspace.minidb_hydrated",
                            "WORKSPACE LOAD hydrated a MINIDB container into the RAM disk.",
                            std::to_string(placed.files) + " file(s), " +
                            std::to_string(placed.bytes) + " B from the memo"));

    // The roots are passed explicitly rather than repointed into the posture
    // text, because this parser reads only AREA and RELATION lines and has
    // never honoured a v3 DBFROOT.
    return mirror_workspace_posture(scanned.posture, "minidb:" + name,
                                    ram_root, ram_index_root, messages);
}

std::size_t Session::mirror_workspace_posture(const std::string& posture,
                                              const std::string& label,
                                              const std::filesystem::path& dbf_root,
                                              const std::filesystem::path& index_root,
                                              std::vector<StatusMessage>& messages) {
    // R128. ENTERED BEFORE THE POSTURE IS PARSED, and the order is the whole
    // point: parse_relation_posture_line tags each relation with the CURRENT
    // workspace handle, so parsing first would stamp every edge with whichever
    // workspace the user happened to be in. The model is SWITCH-then-open, and
    // that applies to the relation lines as much as to the areas.
    //
    // The label is the catalog row's name, so it came OUT of WS_NAME and fits
    // in it by construction; it is not re-validated here.
    const std::string wanted = gui_workspace_name_from_label(label);
    std::uint64_t ws_handle = 0;
    if (wanted.empty()) {
        messages.push_back(info("gui.workspace.load_unnamed",
                                "WORKSPACE LOAD could not derive a workspace name from this "
                                "source, so its areas joined the current workspace.",
                                label));
        ws_handle = xbase::workspace::current_handle();
    } else {
        ws_handle = gui_enter_workspace(wanted, messages);
        if (ws_handle == 0) return 0;
    }
    const std::string ws_name = xbase::workspace::name_of(ws_handle);

    std::vector<WorkspaceRelationInfo> schema_relations;
    std::istringstream posture_stream(posture);
    const auto schema_areas = load_dtschema2_areas_from_stream(posture_stream, schema_relations);
    if (schema_areas.empty()) {
        messages.push_back(warning("gui.workspace.schema_empty",
                                   "WORKSPACE LOAD did not mirror into GUI areas because no schema areas were found.",
                                   label));
        return 0;
    }

    // R128. LOAD IS ADDITIVE. The close-all is gone; a posture loaded into one
    // workspace leaves every other workspace standing.
    //
    // RELATIONS ARE REPLACED PER WORKSPACE, NOT WHOLESALE. This line used to
    // read `impl_->relations = std::move(schema_relations)`, which was correct
    // only while one workspace could exist: made additive without this change
    // it would silently delete the edges of workspaces this load never touched
    // -- the same destruction the ruling exists to stop, one layer down. The
    // discriminator already exists and already has a writer:
    // WorkspaceRelationInfo::workspace, written from owning_workspace_now at
    // parse time. So THIS workspace's edges are dropped (a reload replaces
    // them rather than duplicating them) and everyone else's are kept.
    //
    // NOT FIXED, and R128 sec 5 names it: a SCOPED CLOSE still clears
    // relations globally in the CLI. This is the GUI's half only.
    for (auto it = impl_->areas.begin(); it != impl_->areas.end(); ) {
        if ((*it)->area().wsHandle() == ws_handle) it = impl_->areas.erase(it);
        else ++it;
    }
    impl_->relations.erase(
        std::remove_if(impl_->relations.begin(), impl_->relations.end(),
                       [&](const WorkspaceRelationInfo& r) { return r.workspace == ws_name; }),
        impl_->relations.end());
    for (auto& r : schema_relations) impl_->relations.push_back(std::move(r));
    if (impl_->areas.empty()) impl_->active_area_id = 0;

    std::size_t opened = 0;
    std::size_t indexes_attached = 0;

    for (const auto& schema_area : schema_areas) {
        // AIF-120. With a root override the member is placed, not searched.
        // A hydrated workspace lives in the RAM VFS, where std::filesystem
        // cannot see it -- xbase::ramfs keeps its own registry and DbArea
        // consults it for virtual paths -- so any existence probe here would
        // reject a table that is perfectly openable.
        const auto dbf = dbf_root.empty()
            ? resolve_schema_dbf_path(schema_area.dbf, schema_area.index_type)
            : std::optional<std::filesystem::path>(dbf_root / schema_area.dbf.filename());
        if (!dbf) {
            messages.push_back(warning("gui.workspace.schema_table_missing",
                                       "A WORKSPACE LOAD schema table could not be mirrored into a GUI area.",
                                       schema_area.dbf.string()));
            continue;
        }

        try {
            bool broke_contiguity = false;
            const int slot = impl_->claim_area_slot(broke_contiguity);
            if (slot < 0) {
                // The CLI already ruled this, and the GUI adopts its answer rather
                // than inventing a second spelling for the same refusal (R5).
                // cmd_use.cpp:766 -- "Deliberately NOT falling back to the current
                // area. Falling back is the silent-replacement behaviour this lane
                // exists to kill."
                throw std::runtime_error(
                    "no unoccupied work area (all " + std::to_string(xbase::MAX_AREA) +
                    " are in use). Nothing was opened.");
            }
            auto area = std::make_unique<Impl::Area>(impl_->engine, slot);
            area->path = *dbf;
            area->display_name = !schema_area.alias.empty()
                ? schema_area.alias + ".DBF"
                : dbf->filename().string();
            area->area().open(dbf->string());
            // AIF-078. schema_area.slot is the SAVED POSITION, and it is
            // deliberately no longer reused as this area's identity. A posture
            // records where an area SAT; where it sits now is wherever this
            // restore puts it.
            //
            // The saved ORDER is still honoured, and by the mechanism that was
            // already here: load_dtschema2_areas_from_stream sorts its result by
            // slot before returning it, so this loop runs in ascending saved-slot
            // order and the field keeps a real reader. What a posture cannot
            // promise is the same NUMBERS -- a slot is an address and this
            // session's addresses are its own.
            //
            // THE NARROWING RECORDED HERE IS HALF CLOSED (R120, step 3), and
            // the half that remains is a different one, so it is restated
            // rather than deleted.
            //
            // CLOSED: the GUI's positional rung is no longer an index into a
            // dense list, so it CAN now express a gap. Restoring a posture that
            // names slots 0 and 3 no longer forces the report to say 0 and 1.
            //
            // STILL OPEN: this loop claims a FRESH slot per area rather than
            // the saved one, so the gap it can now express is not necessarily
            // the SAVED gap. Honouring the saved slot needs a documented
            // collision fallback -- a saved slot can already be occupied in
            // this process, by the CLI or by an earlier area in this same loop
            // -- and that is a separate decision, deliberately not taken here.
            // Named so the remaining half cannot be mistaken for the closed one.
            area->id = area->area().areaHandle();

            // AIF-120. DTSHEMA writes the literal word "none" for an absent
            // index or tag (cmd_workspace.cpp:1569-1575). Testing emptiness
            // alone accepted that sentinel as data and asked the CDX backend
            // for a tag named NONE. See include/dottalk/dtschema.hpp.
            if (!dottalk::dtschema::is_absent(schema_area.index.string())) {
                const auto index = index_root.empty()
                    ? resolve_schema_index_path(schema_area.index, schema_area.index_type)
                    : std::optional<std::filesystem::path>(index_root / schema_area.index.filename());
                if (index) {
                    std::string err;
                    const bool attached = !dottalk::dtschema::is_absent(schema_area.tag)
                        ? activate_gui_order(area->area(), *index, schema_area.tag, true, err)
                        : attach_gui_order_container(area->area(), *index, err);
                    if (attached) {
                        ++indexes_attached;
                    } else {
                        messages.push_back(warning("gui.workspace.index_attach_failed",
                                                   "A WORKSPACE LOAD index could not be mirrored into a GUI area.",
                                                   index->string() + ": " + err));
                    }
                } else {
                    messages.push_back(warning("gui.workspace.index_missing",
                                               "A WORKSPACE LOAD schema index was not found.",
                                               schema_area.index.string()));
                }
            }

            if (impl_->active_area_id == 0) {
                impl_->active_area_id = area->id;
            }
            impl_->areas.push_back(std::move(area));
            ++opened;
        } catch (const std::exception& ex) {
            messages.push_back(warning("gui.workspace.open_table_failed",
                                       "A WORKSPACE LOAD table could not be mirrored into a GUI area.",
                                       dbf->string() + ": " + ex.what()));
        } catch (...) {
            messages.push_back(warning("gui.workspace.open_table_failed",
                                       "A WORKSPACE LOAD table could not be mirrored into a GUI area.",
                                       dbf->string()));
        }
    }

    messages.push_back(info("gui.workspace.load_mirrored",
                            "WORKSPACE LOAD mirrored schema areas into GUI areas.",
                            std::to_string(opened) + " table(s) from " + label));
    if (indexes_attached > 0) {
        messages.push_back(info("gui.workspace.indexes_mirrored",
                                "WORKSPACE LOAD mirrored attached index containers into GUI areas.",
                                std::to_string(indexes_attached) + " index container(s)"));
    }
    if (!impl_->relations.empty()) {
        // AIF-120. Mirroring relations into a workspace where NO table opened is
        // not neutral news, and reporting it at info severity directly beneath a
        // run of schema_table_missing warnings reads as success. Measured live:
        // m1_check.dtschema logged 43 table-missing warnings, then "mirrored
        // 58 relation(s)" as info, and the graph drew them as though live.
        if (opened == 0) {
            messages.push_back(warning("gui.workspace.relations_unbacked",
                "WORKSPACE LOAD mirrored schema relations, but no table opened -- "
                "every endpoint is missing.",
                std::to_string(impl_->relations.size()) +
                " relation(s) against 0 open area(s)"));
        } else {
            messages.push_back(info("gui.workspace.relations_mirrored",
                                    "WORKSPACE LOAD mirrored schema relations into the GUI workspace model.",
                                    std::to_string(impl_->relations.size()) + " relation(s)"));
        }
    }
    return opened;
}

bool Session::save_workspace_schema(const std::filesystem::path& schema_path,
                                    std::vector<StatusMessage>& messages,
                                    std::filesystem::path* saved_path) const {
    if (schema_path.empty()) {
        messages.push_back(warning("gui.workspace.schema_name_missing",
                                   "WORKSPACE SAVE needs a schema file name."));
        return false;
    }

    const auto target = normalize_workspace_schema_extension(schema_path);
    const auto parent = target.parent_path();
    std::error_code ec;
    if (!parent.empty()) {
        std::filesystem::create_directories(parent, ec);
        if (ec) {
            messages.push_back(error("gui.workspace.schema_dir_create_failed",
                                     "WORKSPACE SAVE could not create the schema directory.",
                                     parent.string() + ": " + ec.message()));
            return false;
        }
    }

    std::ofstream file(target, std::ios::binary | std::ios::trunc);
    if (!file) {
        messages.push_back(error("gui.workspace.schema_write_failed",
                                 "WORKSPACE SAVE could not open the schema file for writing.",
                                 target.string()));
        return false;
    }

    for (const auto& area : impl_->areas) {
        if (!area->area().isOpen()) {
            continue;
        }

        const auto index_type = schema_index_type(area->area());
        const auto dbf_root = index_type == "CDX"
            ? dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X64)
            : dottalk::paths::get_slot(dottalk::paths::Slot::DBF_X32);
        const auto index_root = index_type == "CDX"
            ? dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X64)
            : dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES_X32);

        const auto dbf_token = relativize_schema_path(area->path, dbf_root).generic_string();
        const auto alias_stem = area->display_name.empty()
            ? std::string{}
            : std::filesystem::path(area->display_name).stem().string();
        const auto path_stem = area->path.stem().string();
        const bool keep_alias = !alias_stem.empty() &&
                                lower_ascii(alias_stem) != lower_ascii(path_stem) &&
                                lower_ascii(alias_stem) != lower_ascii(area->area().logicalName());

        // R120. This writes the ENGINE SLOT, which is what the reader has
        // always called this field (WorkspaceSchemaArea::slot) and what the
        // CLI's own writer has always put there (cmd_workspace.cpp, `area0`).
        // Before step 3 the GUI wrote a list index into the same field, so one
        // line on disk meant two different things depending on which surface
        // wrote it. Postures written by the GUI BEFORE this change carry list
        // indices and will now be read as slots; the two coincide only where
        // the areas were contiguous from 0, which is the common case and not a
        // guarantee.
        file << "AREA " << impl_->visible_ordinal(area->id)
             << "|dbf=\"" << dbf_token << "\"";
        if (!index_type.empty()) {
            file << "|indextype=" << index_type;
        }
        if (orderstate::hasOrder(area->area())) {
            const auto container = relativize_schema_path(std::filesystem::path(orderstate::orderName(area->area())),
                                                          index_root)
                                       .generic_string();
            if (!container.empty()) {
                file << "|index=\"" << container << "\"";
            }
            const std::string tag = trim_ascii(orderstate::activeTag(area->area()));
            if (!tag.empty()) {
                file << "|tag=\"" << tag << "\"";
            }
        }
        if (keep_alias) {
            file << "|alias=\"" << alias_stem << "\"";
        }
        file << "\n";
    }

    // 4a, the other half. This was a `file <<` chain that wrote
    // `ON <parent_key>` and nothing else, so a relation binding
    // differently-named endpoints came back from its own posture with the
    // child side silently replaced by the parent's. It now shares one unit
    // with the reader, and the round trip is held by a fixture.
    std::string posture_line;
    for (const auto& relation : impl_->relations) {
        if (format_relation_posture_line(relation, posture_line)) {
            file << posture_line << "\n";
        }
    }

    file.flush();
    if (!file) {
        messages.push_back(error("gui.workspace.schema_write_failed",
                                 "WORKSPACE SAVE could not finish writing the schema file.",
                                 target.string()));
        return false;
    }

    if (saved_path) {
        *saved_path = target;
    }
    messages.push_back(info("gui.workspace.saved",
                            "WORKSPACE SAVE wrote the current GUI workspace schema.",
                            target.string()));
    return true;
}

bool Session::mirror_workspace_add_table(const std::filesystem::path& path,
                                         std::vector<StatusMessage>& messages) {
    std::error_code ec;
    if (path.empty() || !std::filesystem::is_regular_file(path, ec) ||
        lower_ascii(path.extension().string()) != ".dbf") {
        messages.push_back(warning("gui.workspace.add_path_missing",
                                   "WORKSPACE ADD did not mirror into GUI areas because the table was not found.",
                                   path.string()));
        return false;
    }

    OpenTableResult result = open_table(OpenTableRequest{path});
    messages.insert(messages.end(), result.messages.begin(), result.messages.end());
    if (result.ok) {
        messages.push_back(info("gui.workspace.add_mirrored",
                                "WORKSPACE ADD mirrored DBF table into GUI areas.",
                                path.string()));
    }
    return result.ok;
}

SelectAreaResult Session::select_area(const SelectAreaRequest& request) {
    SelectAreaResult result;
    result.area_id = request.area_id;

    auto* area = impl_->find_area(request.area_id);
    if (!area || !area->area().isOpen()) {
        result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open."));
        return result;
    }

    impl_->active_area_id = request.area_id;
    result.ok = true;
    result.display_name = area->display_name;
    result.messages.push_back(info("gui.area.selected", "GUI work area selected."));
    return result;
}

MoveCursorResult Session::move_cursor(const MoveCursorRequest& request) {
    MoveCursorResult result;
    result.area_id = request.area_id;
    result.record_number = request.record_number;

    auto* area = impl_->find_area(request.area_id);
    if (!area || !area->area().isOpen()) {
        result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open."));
        return result;
    }

    if (request.record_number < 1 || request.record_number > area->area().recCount64() ||
        request.record_number > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        result.messages.push_back(warning("gui.command.bad_recno", "Record number is outside the area range."));
        return result;
    }

    impl_->active_area_id = area->id;
    if (!area->area().gotoRec(static_cast<int32_t>(request.record_number)) || !area->area().readCurrent()) {
        result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
        return result;
    }

    result.ok = true;
    result.record_number = area->area().recno64();
    return result;
}

CloseAreaResult Session::close_area(const CloseAreaRequest& request) {
    CloseAreaResult result;
    result.closed_area_id = request.area_id;

    const auto it = std::find_if(impl_->areas.begin(), impl_->areas.end(), [&](const auto& area) {
        return area->id == request.area_id;
    });
    if (it == impl_->areas.end()) {
        result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open."));
        return result;
    }

    // AIF-078: THE MISSING ARM OF AN EXISTING PAIR.
    //
    // Every WHOLESALE close in this file already clears relations -- the
    // WORKSPACE OPEN mirror, WORKSPACE LOAD, and WORKSPACE CLOSE all do
    // `areas.clear()` next to `relations.clear()`. The SINGLE-area close did
    // not, so closing one table in the Workbench left edges pointing at a table
    // that is gone: the model went on counting matches for them and the posture
    // writer went on saving them.
    //
    // The CLI has the same split and says so out loud (cmd_close.cpp: "Relation
    // clearing is handled by the caller because single-area CLOSE and CLOSE ALL
    // differ there"). This is that caller, finally written.
    //
    // AND IT IS NOT A LINK TO THE RELATION ENGINE. relations_api is not in this
    // process's picture at all: the GUI's relation store IS impl_->relations,
    // filled by parsing CLI output text from an OUT-OF-PROCESS dottalkpp
    // (gui_cli_bridge _popens `dottalkpp --script`) and by DTSCHEMA2 posture.
    // Linking the engine here would add a SECOND, empty, engine-backed store
    // and close nothing -- a third answer to one question. See
    // claude/AIF078_FINDING_RELATION_CLEANUP_IS_NOT_AN_ENGINE_LINK.md.
    //
    // BEFORE the close, deliberately -- see drop_relations_naming.
    const std::size_t dropped_relations = impl_->drop_relations_naming(**it);

    (*it)->area().close();
    impl_->areas.erase(it);

    if (impl_->active_area_id == request.area_id) {
        impl_->active_area_id = impl_->areas.empty() ? 0 : impl_->areas.front()->id;
    }

    result.ok = true;
    result.active_area_id = impl_->active_area_id;
    result.messages.push_back(info("gui.area.closed", "GUI work area closed."));
    // SAID OUT LOUD, not done quietly. The steward's observation on 2026-08-24
    // was that "closing an area will break any joins and relations open" -- and
    // a cleanup that removes them silently is indistinguishable, from the
    // Workbench, from relations that were never there. The count is a VALUE a
    // spec can assert on; a cleanup that reported nothing could only be checked
    // by inspecting the model afterwards.
    if (dropped_relations > 0) {
        result.messages.push_back(info("gui.area.relations_dropped",
                                       "Relations naming the closed table were dropped.",
                                       std::to_string(dropped_relations) + " relation(s)"));
    }
    return result;
}

ListAreasResult Session::list_areas() const {
    ListAreasResult result;
    result.active_area_id = impl_->active_area_id;
    result.active_ordinal = impl_->ordinal_of(impl_->active_area_id);

    result.areas.reserve(impl_->areas.size());
    // AIF-078 step 3. The ordinal is the area's ENGINE SLOT -- the same number
    // find_area_by_ordinal searches for -- so what is shown and what can be
    // typed are the same number by construction rather than by coincidence,
    // and it is ALSO the number the CLI would print for that area.
    //
    // It is taken from the area rather than from the loop counter, and that is
    // the point of the change: a loop counter is a fact about this list, and a
    // list that skips closed areas (the isOpen guard just below) would have
    // made the counter disagree with find_area_by_ordinal the moment anything
    // was closed. There is nothing left for the two to disagree about.
    for (const auto& area : impl_->areas) {
        if (!area->area().isOpen()) {
            continue;
        }
        AreaInfo info = gui_area_info_from_dbarea(area->id,
                                                  area->id == impl_->active_area_id,
                                                  area->area(),
                                                  area->display_name);
        info.ordinal = static_cast<AreaOrdinal>(area->slot());
        result.areas.push_back(std::move(info));
    }

    return result;
}

WorkspaceModel Session::workspace_model() const {
    WorkspaceModel model;
    const auto areas = list_areas();
    model.active_area_id = areas.active_area_id;
    model.active_ordinal = areas.active_ordinal;
    model.tables = areas.areas;
    model.messages = areas.messages;
    model.relations = impl_->relations;

    // THE GUI DOES NOT COUNT MATCHES. Ruling R123, 2026-08-24.
    //
    // A ~145-line count_relation_matches lambda stood here and answered, for
    // every relation edge, "how many child rows match the parent". So did
    // relations_api::match_count_for_child, and they answered DIFFERENTLY --
    // four ways. This one counted DELETED rows where the engine skipped them,
    // scanned with a bound of its own that REL SCANLIMIT could not reach,
    // compared ONE join field where the engine matched all of them, and walked
    // PHYSICAL record order where the engine walked the active index inside a
    // ScopedEngineSelect.
    //
    // One relation, two numbers, and nothing on screen saying which one a grid
    // cell held. That is R5 -- two answers to one question IS the defect.
    //
    // IT COULD NOT BE FIXED IN PLACE, and that is what R122 settled. A match
    // count is a computation over THIS PROCESS's open areas at THIS PROCESS's
    // cursor positions. The engine's counter lives behind a process boundary
    // (gui_shell_runtime CreateProcessW / gui_cli_bridge _popen), and a
    // subprocess cannot answer a question about state it does not have without
    // replicating that state. So the choice was link the engine or stop
    // answering, and R122 ruled the link out on dependency direction.
    //
    // A NUMBER THAT DISAGREES WITH THE ENGINE IS WORSE THAN NO NUMBER, so the
    // count is now ABSENT. This needed no new type: match_count is already a
    // MaybeMatchCount and the renderers already carry an n/a state -- R6 was
    // satisfied the whole time and this code was declining to use it. The old
    // lambda already knew, too: it refused to report a TRUNCATED scan for
    // exactly this reason ("ABSENT says I could not compute this, which is
    // true"). R123 extends that honesty from the truncated case to every case.
    //
    // WHEN A COUNT COMES BACK it arrives from the producer under R122's
    // structured emission, computed once, by the engine, from the engine's own
    // state -- not recomputed here from a second copy of the rules.


    model.indexes.reserve(impl_->areas.size());
    for (const auto& area : impl_->areas) {
        if (!area->area().isOpen()) {
            continue;
        }

        WorkspaceIndexInfo index;
        index.area_id = area->id;
        index.ordinal = impl_->ordinal_of(area->id);
        index.area_name = area->display_name;
        index.kind = order_kind(area->area());
        index.active = orderstate::hasOrder(area->area());
        index.ascending = orderstate::isAscending(area->area());
        index.backend = order_backend(area->area());
        if (index.active) {
            index.container = orderstate::orderName(area->area());
            index.tag = orderstate::activeTag(area->area());
            if (const auto* manager = xindex::manager_if_attached(area->area())) {
                index.tags = manager->listTags();
            }
        }
        model.indexes.push_back(std::move(index));
    }

    return model;
}

CommandResult Session::run_command(const CommandRequest& request) {
    CommandResult result;
    const std::string command = trim_ascii(request.text);
    const std::string dispatch_command = resolve_shell_shortcut(command);

    if (command.empty()) {
        result.messages.push_back(warning("gui.command.empty", "No command text was provided."));
        return result;
    }

    const std::string verb = first_token_lower(dispatch_command);
    std::ostringstream out;
    auto mirror_cli_result_to_gui = [&](const RuntimeCliResult& cli,
                                        const std::string& command_text) -> bool {
        bool workspace_open_mirrored = false;
        mirror_setpath_output_to_gui(cli.output, result.messages);
        if (output_clears_relations(cli.output)) {
            impl_->relations.clear();
        }

        if (!cli.ok) {
            return workspace_open_mirrored;
        }

        if (const auto workspace_dir = workspace_open_dir_from_cli_output(cli.output)) {
            const auto opened = mirror_workspace_open_directory(*workspace_dir, cli.output, {}, result.messages);
            out << "\nGUI mirror: WORKSPACE OPEN created " << opened
                << " GUI area(s) from " << workspace_dir->string() << "\n";
            workspace_open_mirrored = true;
        }

        if (const auto schema = workspace_load_schema_from_cli_output(cli.output, command_text)) {
            const auto opened = mirror_workspace_load_schema(*schema, result.messages);
            out << "\nGUI mirror: WORKSPACE LOAD created " << opened
                << " GUI area(s) from " << schema->string() << "\n";
            workspace_open_mirrored = opened > 0;
        }

        for (auto relation : parse_relation_edges_from_output(cli.output, owning_workspace_now())) {
            merge_relation(impl_->relations, std::move(relation));
        }

        if (const auto cli_area = last_cli_area_from_output(cli.output)) {
            if (*cli_area >= 0) {
                // The shell reports a POSITION, and it is resolved as one.
                if (auto* selected = impl_->find_area_by_ordinal(static_cast<AreaOrdinal>(*cli_area))) {
                    impl_->active_area_id = selected->id;
                    result.messages.push_back(info("gui.area.shell_selected",
                                                   "GUI selected the work area reported by the DotTalk++ shell.",
                                                   std::to_string(*cli_area)));
                }
            }
        }

        if (const auto recno = last_cli_recno_from_output(cli.output)) {
            auto* active = impl_->active_area();
            if (active && active->area().isOpen() && *recno >= 1 &&
                *recno <= static_cast<long long>(active->area().recCount64()) &&
                *recno <= static_cast<long long>(std::numeric_limits<int32_t>::max())) {
                if (active->area().gotoRec(static_cast<int32_t>(*recno)) && active->area().readCurrent()) {
                    result.messages.push_back(info("gui.cursor.shell_synced",
                                                   "GUI cursor mirrored the record reported by the DotTalk++ shell.",
                                                   std::to_string(*recno)));
                }
            }
        }

        auto* mirror_area = impl_->active_area();
        if (mirror_area && mirror_area->area().isOpen()) {
            const auto words = split_words(command_text);
            if (!words.empty()) {
                const std::string mirror_verb = lower_ascii(words[0]);
                if (!mirror_set_index_to_gui(mirror_area->area(), words, result.messages) &&
                    !mirror_set_order_to_gui(mirror_area->area(), words, result.messages)) {
                    if (mirror_verb == "ascend") {
                        (void)mirror_order_direction_to_gui(mirror_area->area(), true, result.messages);
                    } else if (mirror_verb == "descend") {
                        (void)mirror_order_direction_to_gui(mirror_area->area(), false, result.messages);
                    }
                }
            }
        }

        return workspace_open_mirrored;
    };
    auto build_cli_request = [&](const std::string& cli_text) {
        RuntimeCliRequest cli_request;
        cli_request.command = cli_text;
        if (const auto* area = impl_->active_area(); area && area->area().isOpen()) {
            cli_request.active_table_path = area->path;
            cli_request.active_record_number = area->area().recno64();
            if (orderstate::hasOrder(area->area())) {
                cli_request.active_index_container = std::filesystem::path(orderstate::orderName(area->area()));
                cli_request.active_index_tag = orderstate::activeTag(area->area());
                cli_request.active_index_ascending = orderstate::isAscending(area->area());
            }
        }
        return cli_request;
    };

    if (verb == "help" || verb == "aiuto" || verb == "?") {
        out << "DotTalk++ Workbench command lane\n\n"
            << "Active GUI commands:\n"
            << "  help | aiuto      show this command summary\n"
            << "  about             show workbench identity\n"
            << "  area              summarize the active GUI work area\n"
            << "  areas | workspace list\n"
            << "                    list open workspace areas\n"
            << "  workspace open <dir> [CDX]\n"
            << "                    open every DBF in a directory as GUI areas\n"
            << "  workspace close   close all GUI work areas\n"
            << "  workspace load|save <name.dtschema>\n"
            << "                    load or save the current GUI workspace schema\n"
            << "  list | browse     summarize the active browse snapshot\n"
            << "  status            summarize GUI session status\n"
            << "  structure         list fields for the active area\n"
            << "  graph | workspace graph\n"
            << "                    summarize the current workspace graph\n"
            << "  paths | setpath   show GUI path roots\n"
            << "  openarch          summarize the GUI open architecture rule\n"
            << "  select <area>     select a persistent GUI work area\n"
            << "  dbarea            summarize persistent runtime area state\n"
            << "  recno             show the active area record pointer\n"
            << "  goto <n>          move the active area record pointer\n"
            << "  skip [n]          move relative in the active area\n"
            << "  top | bottom      move to first or last record\n"
            << "  set dbf|index     command skeleton for path/index settings\n"
            << "  scan ... endscan  send multiline SCAN block to the CLI bridge\n"
            << "  do | dotscript    run a DotTalk++ script through the CLI bridge\n"
            << "  loop/endloop      CLI control block family; use through the bridge\n"
            << "  var | set var     CLI variable family; use through the bridge\n"
            << "  cli <command>     force the DotTalk++ CLI bridge\n\n"
            << "Unknown commands stay in the GUI so typos do not start a throwaway CLI process.\n"
            << "Runtime lane: " << impl_->shell_runtime->description()
            << (impl_->shell_runtime->persistent() ? " (persistent).\n" : " (not persistent yet).\n")
            << "Known menu commands may use the compatibility bridge while native GUI services mature.\n"
            << "Set DOTTALKPP_GUI_CLI or DOTTALKPP_EXE to select a dottalkpp executable.";
    } else if (verb == "about") {
        out << "DotTalk++ Workbench\n"
            << "A windowed workspace for areas, tables, indexes, relations, browsers, and command lanes.";
    } else if (verb == "openarch" || verb == "architecture") {
        out << "DOTTALK++ GUI OPENARCH\n"
            << "GUI grows top-down: workbench, workspace graph, areas, projections, scripts, diagnostics.\n"
            << "Database behavior remains bottom-up and authoritative in DotTalk++ runtime services.\n"
            << "wx owns native desktop presentation; Python owns fast scripted inspection.\n"
            << "Commands and scripts flow through the CLI bridge until native GUI services own them.\n"
            << "Skeleton actions must stay explicit; widget code must not fork database semantics.";
    } else if (verb == "area") {
        const auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current GUI work area is selected.";
        } else {
            out << "ACTIVE GUI AREA\n"
                << "Area: " << impl_->visible_ordinal(area->id) << "\n"
                << "Table: " << area->display_name << "\n"
                << "Records: " << area->area().recCount64() << "\n"
                << "Fields: " << area->area().fields().size() << "\n"
                << "File type: " << dbf_flavor_label(area->area()) << "\n"
                << "Path: " << area->path.string();
        }
    } else if (verb == "areas" || dispatch_command == "workspace" || dispatch_command == "workspace list") {
        out << "WORKSPACE AREAS\n";
        if (impl_->areas.empty()) {
            out << "  No open areas.";
        } else {
            for (const auto& area : impl_->areas) {
                const bool active = area->id == impl_->active_area_id;
                out << (active ? "* " : "  ")
                    << impl_->visible_ordinal(area->id) << "  "
                    << area->display_name << "  records="
                    << (area->area().isOpen() ? area->area().recCount64() : 0)
                    << "  path=" << area->path.string() << "\n";
            }
        }
    } else if (verb == "workspace") {
        const auto words = split_words(dispatch_command);
        const std::string action = words.size() >= 2 ? lower_ascii(words[1]) : std::string{};
        if (action == "open") {
            if (words.size() < 3) {
                result.messages.push_back(warning("gui.workspace.open_usage",
                                                  "WORKSPACE OPEN needs a directory path."));
                out << "Usage: workspace open <directory> [CDX]";
            } else {
                const std::filesystem::path target(words[2]);
                std::string index_mode;
                for (auto it = words.begin() + 3; it != words.end(); ++it) {
                    const std::string flag = upper_ascii(*it);
                    if (flag == "AUTO" || flag == "CDX" || flag == "CNX" || flag == "INX" ||
                        flag == "IDX" || flag == "NOINDEX" || flag == "NONE" || flag == "PHYSICAL") {
                        index_mode = flag;
                        break;
                    }
                }
                const auto opened = mirror_workspace_open_directory(target, {}, index_mode, result.messages);
                out << "WORKSPACE OPEN\n"
                    << "Directory: " << target.string() << "\n"
                    << "Opened GUI areas: " << opened << "\n";
                if (!index_mode.empty()) {
                    out << "Index mode: " << index_mode << "\n";
                }
                if (impl_->active_area_id != 0) {
                    if (const auto* area = impl_->active_area()) {
                        out << "Active area: " << impl_->visible_ordinal(area->id)
                            << "  " << area->display_name << "\n";
                    }
                }
            }
        } else if (action == "add") {
            if (words.size() < 3) {
                result.messages.push_back(warning("gui.workspace.add_usage",
                                                  "WORKSPACE ADD needs a DBF path."));
                out << "Usage: workspace add <table.dbf>";
            } else {
                const std::filesystem::path target(words[2]);
                const bool opened = mirror_workspace_add_table(target, result.messages);
                out << "WORKSPACE ADD\n"
                    << "Table: " << target.string() << "\n"
                    << (opened ? "GUI area selected/opened." : "No GUI area opened.");
            }
        } else if (action == "close") {
            // R128. BARE CLOSE IS SCOPED, CLOSE ALL IS EVERYWHERE -- the same
            // grammar the CLI has had since AIF-078 stage 3. This branch used
            // to close every GUI area unconditionally and report "All GUI work
            // areas were closed", while the CLI verb it shadows had been scoped
            // for days: two surfaces, one verb name, two meanings.
            const bool close_all = (words.size() > 2 && lower_ascii(words[2]) == "all");
            const std::uint64_t current = xbase::workspace::current_handle();
            std::set<std::uint64_t> scope;
            if (!close_all) {
                gui_collect_scope(current, xbase::workspace::recursion_enabled(), 0, scope);
            }

            const std::size_t before = impl_->areas.size();
            for (auto it = impl_->areas.begin(); it != impl_->areas.end(); ) {
                const bool in_scope = close_all || scope.count((*it)->area().wsHandle()) != 0;
                if (in_scope) it = impl_->areas.erase(it);   // ~Area() closes it
                else ++it;
            }
            const std::size_t closed = before - impl_->areas.size();

            // Relations: only this workspace's edges, for the reason the
            // posture mirror gives -- clearing them all would delete edges
            // belonging to workspaces this close never touched.
            if (close_all) {
                impl_->relations.clear();
            } else {
                const std::string nm = xbase::workspace::name_of(current);
                impl_->relations.erase(
                    std::remove_if(impl_->relations.begin(), impl_->relations.end(),
                                   [&](const WorkspaceRelationInfo& r) { return r.workspace == nm; }),
                    impl_->relations.end());
            }

            // The active area may have been one of the closed ones. Answered by
            // LOOKING rather than by assuming: a stale id here addresses an area
            // that no longer exists, which is the dangling-handle shape.
            bool active_survives = false;
            for (const auto& a : impl_->areas) {
                if (a->id == impl_->active_area_id) { active_survives = true; break; }
            }
            if (!active_survives) {
                impl_->active_area_id = impl_->areas.empty() ? 0 : impl_->areas.front()->id;
            }

            result.messages.push_back(info("gui.workspace.closed",
                                           close_all
                                             ? "Every GUI work area was closed."
                                             : "The current workspace's GUI work areas were closed.",
                                           std::to_string(closed) + " area(s)"));
            out << "WORKSPACE CLOSE" << (close_all ? " ALL" : "") << "\n"
                << "Closed GUI areas: " << closed;
            if (!close_all && impl_->areas.size() > 0) {
                out << "\nLeft open in other workspaces: " << impl_->areas.size();
            }
        } else if (action == "graph") {
            out << "WORKSPACE GRAPH\n"
                << "Areas: " << impl_->areas.size() << "\n"
                << "Active area: ";
            if (impl_->active_area_id == 0) {
                out << "none\n";
            } else {
                out << impl_->visible_ordinal(impl_->active_area_id) << "\n";
            }
            out << "Relations: workspace graph service pending\n"
                << "Indexes: workspace graph service pending\n"
                << "Browsers/lists: workspace graph service pending\n"
                << "ERSATZ presets: workspace graph service pending\n"
                << "DTSchema load/save: runtime schema service active; graph service pending";
        } else if (action == "load" || action == "save" || action == "saveas") {
            const std::string name = trim_ascii(remove_first_tokens(dispatch_command, 2));
            if (name.empty()) {
                result.messages.push_back(warning("gui.workspace.schema_name_missing",
                                                  "WORKSPACE LOAD/SAVE needs a schema file name."));
                out << "Usage:\n"
                    << "  workspace load <name.dtschema>\n"
                    << "  workspace save <name.dtschema>";
            } else if (action == "load") {
                // AIF-120. The memo forms are not filenames. This branch used to
                // take everything after two tokens as a path, so
                // "WORKSPACE LOAD minidb_regress MEMO RAM" was reported as a
                // missing schema FILE -- a message that sends the reader hunting
                // for something that was never meant to exist.
                std::string memo_name;
                bool via_memo = false;
                for (const auto& word : split_words(name)) {
                    const std::string flag = upper_ascii(word);
                    if (flag == "MEMO") {
                        via_memo = true;
                    } else if (flag == "RAM" || flag == "PARTIAL") {
                        // residence/tolerance modifiers, not part of the name
                    } else if (memo_name.empty()) {
                        memo_name = strip_matching_quotes(word);
                    }
                }
                if (via_memo) {
                    const auto opened = mirror_memo_workspace(memo_name, result.messages);
                    out << "WORKSPACE LOAD (memo)\n"
                        << "Workspace: " << memo_name << "\n"
                        << "Opened GUI areas: " << opened << "\n";
                    if (impl_->active_area_id != 0) {
                        if (const auto* area = impl_->active_area()) {
                            out << "Active area: " << impl_->visible_ordinal(area->id)
                                << "  " << area->display_name << "\n";
                        }
                    }
                } else if (const auto schema = resolve_workspace_schema_token(
                               std::filesystem::path(strip_matching_quotes(name)));
                           !schema) {
                    result.messages.push_back(warning("gui.workspace.schema_missing",
                                                      "WORKSPACE LOAD could not find the schema file.",
                                                      name));
                    out << "WORKSPACE LOAD\n"
                        << "Schema not found: " << name;
                } else {
                    const auto opened = mirror_workspace_load_schema(*schema, result.messages);
                    out << "WORKSPACE LOAD\n"
                        << "Schema: " << schema->string() << "\n"
                        << "Opened GUI areas: " << opened << "\n";
                    if (impl_->active_area_id != 0) {
                        if (const auto* area = impl_->active_area()) {
                            out << "Active area: " << impl_->visible_ordinal(area->id)
                                << "  " << area->display_name << "\n";
                        }
                    }
                }
            } else {
                std::filesystem::path saved_path;
                const bool saved = save_workspace_schema(resolve_workspace_schema_save_target(name),
                                                         result.messages,
                                                         &saved_path);
                out << "WORKSPACE " << upper_ascii(action) << "\n"
                    << "Schema: " << normalize_workspace_schema_extension(saved_path.empty()
                        ? resolve_workspace_schema_save_target(name)
                        : saved_path).string() << "\n"
                    << (saved ? "Workspace schema saved." : "Workspace schema was not saved.");
            }
        } else {
            result.messages.push_back(warning("gui.workspace.unknown",
                                              "Unknown workspace command.",
                                              command));
            out << "WORKSPACE COMMANDS\n"
                << "  workspace list\n"
                << "  workspace open <directory> [CDX]\n"
                << "  workspace add <table.dbf>\n"
                << "  workspace close\n"
                << "  workspace load <name.dtschema>\n"
                << "  workspace save <name.dtschema>";
        }
    } else if (verb == "graph" || dispatch_command == "workspace graph") {
        out << "WORKSPACE GRAPH\n"
            << "Areas: " << impl_->areas.size() << "\n"
            << "Active area: ";
        if (impl_->active_area_id == 0) {
            out << "none\n";
        } else {
            out << impl_->visible_ordinal(impl_->active_area_id) << "\n";
        }
        out << "Relations: workspace graph service pending\n"
            << "Indexes: workspace graph service pending\n"
            << "Browsers/lists: workspace graph service pending\n"
            << "ERSATZ presets: workspace graph service pending\n"
            << "DTSchema load/save: runtime schema service active; graph service pending";
    } else if (verb == "status") {
        const auto* area = impl_->active_area();
        out << "GUI SESSION STATUS\n"
            << "Open areas: " << impl_->areas.size() << "\n"
            << "Active area: " << (area ? impl_->visible_ordinal(area->id) : std::string("none")) << "\n";
        if (area && area->area().isOpen()) {
            out << "Active table: " << area->display_name << "\n"
                << "Records: " << area->area().recCount64() << "\n"
                << "Path: " << area->path.string() << "\n";
        }
        out << "Runtime lane: " << impl_->shell_runtime->description()
            << (impl_->shell_runtime->persistent() ? " (persistent)" : " (not persistent yet)") << "\n"
            << "CLI bridge: use cli <command> to force the compatibility bridge.";
    } else if (verb == "paths" || verb == "setpath") {
        out << "GUI PATH ROOTS\n"
            << dottalk::paths::describe()
            << "Startup scripts searched: init.ini, dottalkpp.ini, dotscript.ini\n"
            << "Shutdown script searched: shutdown.ini";
    } else if (dispatch_command == "set dbf" || dispatch_command == "set database" ||
               dispatch_command == "set index" || dispatch_command == "set indexes") {
        out << "Command accepted by the Workbench command lane: " << command << "\n"
            << "SET DBF / SET INDEX GUI controls are skeletons for now.\n"
            << "Use SETPATH DBF <path> or SETPATH INDEXES <path> through the CLI bridge while the native GUI controls mature.";
        result.messages.push_back(info("gui.command.skeleton", "Command dispatch skeleton only."));
    } else if (verb == "select") {
        const std::string target = remove_first_token(dispatch_command);
        auto* area = impl_->find_area_by_user_token(target);
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open.", target));
            out << "No matching GUI work area is open: " << target;
        } else {
            impl_->active_area_id = area->id;
            out << "Selected GUI area " << impl_->visible_ordinal(area->id) << ".\n"
                << "Table: " << area->display_name << "\n"
                << "Recno: " << area->area().recno64();
        }
    } else if (verb == "dbarea") {
        const auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current GUI work area is selected.";
        } else {
            out << "DBAREA\n"
                << "Area: " << impl_->visible_ordinal(area->id) << "\n"
                << "Logical name: " << area->area().logicalName() << "\n"
                << "Table: " << area->display_name << "\n"
                << "File type: " << dbf_flavor_label(area->area()) << "\n"
                << "Path: " << area->path.string() << "\n"
                << "Open: yes\n"
                << "Records: " << area->area().recCount64() << "\n"
                << "Fields: " << area->area().fields().size() << "\n"
                << "Recno: " << area->area().recno64() << "\n"
                << "BOF: " << (area->area().bof() ? "yes" : "no") << "\n"
                << "EOF: " << (area->area().eof() ? "yes" : "no");
        }
    } else if (verb == "recno") {
        auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            const auto words = split_words(dispatch_command);
            if (words.size() == 1) {
                out << area->area().recno64();
            } else {
                long long wanted = 0;
                if (!parse_i64(words[1], wanted) || wanted < 1 ||
                    wanted > static_cast<long long>(area->area().recCount())) {
                    result.messages.push_back(warning("gui.command.bad_recno", "RECNO needs a record number in range."));
                    out << "Usage: recno <record-number>";
                } else if (!area->area().gotoRec(static_cast<int32_t>(wanted)) || !area->area().readCurrent()) {
                    result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                    out << "RECNO failed.";
                } else {
                    out << area->area().recno64();
                }
            }
        }
    } else if (verb == "goto" || verb == "go") {
        auto* area = impl_->active_area();
        long long wanted = 0;
        const auto words = split_words(dispatch_command);
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else if (words.size() < 2 || !parse_i64(words[1], wanted) || wanted < 1) {
            result.messages.push_back(warning("gui.command.bad_recno", "GOTO needs a positive record number."));
            out << "Usage: goto <record-number>";
        } else {
            if (wanted > static_cast<long long>(std::numeric_limits<int32_t>::max()) ||
                !area->area().gotoRec(static_cast<int32_t>(wanted)) || !area->area().readCurrent()) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << "GOTO failed.";
            } else {
                out << "Recno: " << area->area().recno64();
            }
        }
    } else if (verb == "skip") {
        auto* area = impl_->active_area();
        long long delta = 1;
        const auto words = split_words(dispatch_command);
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else if (words.size() >= 2 && !parse_i64(words[1], delta)) {
            result.messages.push_back(warning("gui.command.bad_skip", "SKIP needs an integer offset."));
            out << "Usage: skip [offset]";
        } else {
            if (delta > std::numeric_limits<int>::max()) {
                delta = std::numeric_limits<int>::max();
            } else if (delta < std::numeric_limits<int>::min()) {
                delta = std::numeric_limits<int>::min();
            }

            const int n = static_cast<int>(delta);
            std::string order_err;
            const bool moved = orderstate::hasOrder(area->area())
                ? skip_gui_area_ordered(area->area(), n, order_err)
                : (n == 0 ? area->area().readCurrent()
                          : (area->area().skip(n) && area->area().readCurrent()));

            if (!moved) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << "SKIP failed.";
                if (!order_err.empty()) {
                    out << " " << order_err;
                }
            } else {
                out << "Recno: " << area->area().recno64();
            }
        }
    } else if (verb == "top" || verb == "bottom") {
        auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            std::string order_err;
            const bool moved = orderstate::hasOrder(area->area())
                ? (verb == "top" ? position_gui_area_to_first_ordered(area->area(), order_err)
                                  : position_gui_area_to_last_ordered(area->area(), order_err))
                : (verb == "top" ? area->area().top() : area->area().bottom());
            if (!moved || !area->area().readCurrent()) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << (verb == "top" ? "TOP" : "BOTTOM") << " failed.";
                if (!order_err.empty()) {
                    out << " " << order_err;
                }
            } else {
                out << "Recno: " << area->area().recno64();
            }
        }
    } else if (verb == "list" || verb == "browse") {
        const auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            out << "BROWSE SUMMARY\n"
                << "Area: " << impl_->visible_ordinal(area->id) << "\n"
                << "Table: " << area->display_name << "\n"
                << "Records: " << area->area().recCount64() << "\n"
                << "Fields: " << area->area().fields().size() << "\n"
                << "Use the Browse tab for row data.";
        }
    } else if (verb == "structure") {
        const auto* area = impl_->active_area();
        if (!area || !area->area().isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            out << "STRUCTURE " << area->display_name << "\n";
            std::size_t index = 1;
            for (const auto& field : area->area().fields()) {
                out << index++ << "  " << field.name << "  "
                    << field.type << "(" << static_cast<int>(field.length)
                    << "," << static_cast<int>(field.decimals) << ")\n";
            }
        }
    } else if (verb == "cli") {
        const std::string cli_command = remove_first_token(command);
        RuntimeCliResult cli = impl_->shell_runtime->run(build_cli_request(cli_command));
        if (!cli.attempted) {
            out << cli.detail;
            result.messages.push_back(warning("gui.command.cli_unavailable",
                                              "DotTalk++ CLI bridge is not available.",
                                              cli.detail));
        } else {
            write_cli_result(out, cli);
            (void)mirror_cli_result_to_gui(cli, cli_command);
            if (!cli.ok) {
                result.messages.push_back(warning("gui.command.cli_failed",
                                                  "DotTalk++ CLI command returned a non-zero exit code.",
                                                  cli.detail));
            }
        }
    } else {
        if (!should_auto_bridge_command(verb)) {
            out << "Unknown GUI command: " << verb << "\n";
            if (const std::string suggestion = command_suggestion(verb); !suggestion.empty()) {
                out << "Did you mean: " << suggestion << "?\n";
            }
            out << "No external CLI process was started.\n"
                << "Use cli " << command << " to force the DotTalk++ CLI bridge.";
            result.messages.push_back(warning("gui.command.unknown",
                                              "Unknown GUI command; CLI bridge was not started.",
                                              command));
            result.ok = true;
            result.output = out.str();
            return result;
        }

        RuntimeCliResult cli = impl_->shell_runtime->run(build_cli_request(dispatch_command));
        if (cli.attempted) {
            write_cli_result(out, cli);
            const bool output_workspace_mirrored = mirror_cli_result_to_gui(cli, dispatch_command);
            const auto words = split_words(dispatch_command);
            if (cli.ok && !output_workspace_mirrored && words.size() >= 3 &&
                lower_ascii(words[0]) == "workspace" &&
                lower_ascii(words[1]) == "open") {
                const std::filesystem::path target(words[2]);
                std::string index_mode;
                for (auto it = words.begin() + 3; it != words.end(); ++it) {
                    const std::string flag = upper_ascii(*it);
                    if (flag == "AUTO" || flag == "CDX" || flag == "CNX" || flag == "INX" ||
                        flag == "IDX" || flag == "NOINDEX" || flag == "NONE" || flag == "PHYSICAL") {
                        index_mode = flag;
                        break;
                    }
                }
                const auto opened = mirror_workspace_open_directory(target, {}, index_mode, result.messages);
                out << "\nGUI mirror: WORKSPACE OPEN created " << opened
                    << " GUI area(s) from " << target.string() << "\n";
            } else if (cli.ok && words.size() >= 3 &&
                       lower_ascii(words[0]) == "workspace" &&
                       lower_ascii(words[1]) == "add") {
                const std::filesystem::path target(words[2]);
                const bool mirrored = mirror_workspace_add_table(target, result.messages);
                out << "\nGUI mirror: WORKSPACE ADD "
                    << (mirrored ? "selected/opened" : "did not open")
                    << " GUI area for " << target.string() << "\n";
            }
            if (!cli.ok) {
                result.messages.push_back(warning("gui.command.cli_failed",
                                                  "DotTalk++ CLI command returned a non-zero exit code.",
                                                  cli.detail));
            }
        } else {
            out << "Command accepted by the Workbench command lane: " << command << "\n"
                << "DotTalk++ CLI bridge is not available yet.\n"
                << cli.detail;
            result.messages.push_back(info("gui.command.skeleton", "Command dispatch skeleton only."));
        }
    }

    result.ok = true;
    result.output = out.str();
    return result;
}

TableSnapshot Session::snapshot_current_table(const TableSnapshotRequest& request) const {
    auto* selected = request.area_id == 0 ? impl_->active_area() : impl_->find_area(request.area_id);
    if (!selected || !selected->area().isOpen()) {
        TableSnapshot snapshot;
        snapshot.area_id = request.area_id;
        snapshot.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
        return snapshot;
    }

    return gui_snapshot_from_dbarea(selected->id,
                                    selected->area(),
                                    selected->display_name,
                                    request.first_record,
                                    request.max_records);
}

} // namespace dottalk::gui
