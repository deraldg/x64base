#include "gui/core/session.hpp"

#include "common/path_resolver.hpp"
#include "common/path_state.hpp"
#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"
#include "gui/core/gui_command_catalog.hpp"
#include "gui/core/gui_runtime_adapter.hpp"
#include "gui_shell_runtime.hpp"
#include "gui_cli_bridge.hpp"
#include "cli/shell_shortcuts.hpp"
#include "xbase.hpp"
#include "xindex/index_manager.hpp"

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
    AreaId area_id {0};
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
            attachment.area_id = static_cast<AreaId>(area0 + 1);
            attachment.container = std::move(*container);
            attachments.push_back(std::move(attachment));
        }
    }
    return attachments;
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

void merge_relation(std::vector<WorkspaceRelationInfo>& relations, WorkspaceRelationInfo relation);

std::vector<WorkspaceSchemaArea> load_dtschema2_areas(const std::filesystem::path& schema_path,
                                                      std::vector<WorkspaceRelationInfo>& relations) {
    std::ifstream file(schema_path);
    std::vector<WorkspaceSchemaArea> areas;
    if (!file) {
        return areas;
    }

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

        if (line.rfind("RELATION ", 0) == 0) {
            std::string rest = trim_ascii(line.substr(9));
            const auto on = rest.find(" ON ");
            if (on == std::string::npos) {
                continue;
            }
            std::istringstream head(rest.substr(0, on));
            WorkspaceRelationInfo relation;
            head >> relation.parent >> relation.child;
            relation.parent_key = trim_ascii(rest.substr(on + 4));
            relation.child_key = relation.parent_key;
            relation.source = "DTSchema";
            if (!relation.parent.empty() && !relation.child.empty()) {
                merge_relation(relations, std::move(relation));
            }
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

    area.indexManager().close();
    orderstate::clearOrder(area);
    orderstate::setOrder(area, container_text);
    orderstate::setActiveTag(area, tag_upper);
    orderstate::setAscending(area, ascending);

    bool opened = false;
    if (ends_with_ci(container_text, ".cdx")) {
        opened = area.indexManager().openCdx(container_text, tag_upper, &err);
    } else if (ends_with_ci(container_text, ".cnx")) {
        opened = area.indexManager().openCnx(container_text, tag_upper, &err);
    } else {
        err = "GUI ordered browse supports CDX/CNX activation in this bridge pass.";
    }

    if (!opened) {
        area.indexManager().close();
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
    area.indexManager().close();
    orderstate::clearOrder(area);
    orderstate::setOrder(area, container_text);
    orderstate::setActiveTag(area, "");
    orderstate::setAscending(area, true);

    bool opened = false;
    if (ends_with_ci(container_text, ".cdx")) {
        opened = area.indexManager().openCdx(container_text, {}, &err);
    } else if (ends_with_ci(container_text, ".cnx")) {
        opened = area.indexManager().openCnx(container_text, {}, &err);
    } else {
        err = "GUI workspace index mirror supports CDX/CNX containers.";
    }

    if (!opened) {
        area.indexManager().close();
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
        area.indexManager().close();
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
    if (const auto* index = area.indexManagerPtr(); index && index->hasBackend()) {
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

std::size_t leading_space_count(const std::string& text) {
    std::size_t count = 0;
    while (count < text.size() && text[count] == ' ') {
        ++count;
    }
    return count;
}

std::optional<std::uint64_t> match_count_from_relation_line(const std::string& line) {
    const auto marker = line.find("(matches:");
    if (marker == std::string::npos) {
        return std::nullopt;
    }
    const std::string tail = trim_ascii(line.substr(marker + 9));
    long long value = 0;
    if (!parse_i64_prefix(tail, value) || value < 0) {
        return std::nullopt;
    }
    return static_cast<std::uint64_t>(value);
}

void merge_relation(std::vector<WorkspaceRelationInfo>& relations, WorkspaceRelationInfo relation) {
    const auto same_relation = [&](const WorkspaceRelationInfo& existing) {
        const bool same_tables = lower_ascii(existing.parent) == lower_ascii(relation.parent) &&
                                 lower_ascii(existing.child) == lower_ascii(relation.child);
        const bool compatible_key = existing.parent_key.empty() || relation.parent_key.empty() ||
                                    lower_ascii(existing.parent_key) == lower_ascii(relation.parent_key);
        return same_tables && compatible_key;
    };

    const auto found = std::find_if(relations.begin(), relations.end(), same_relation);
    if (found == relations.end()) {
        relations.push_back(std::move(relation));
        return;
    }

    if (found->parent_key.empty()) {
        found->parent_key = relation.parent_key;
    }
    if (found->child_key.empty()) {
        found->child_key = relation.child_key;
    }
    if (found->match_count == 0) {
        found->match_count = relation.match_count;
    }
    if (!relation.source.empty()) {
        found->source = relation.source;
    }
}

std::vector<WorkspaceRelationInfo> parse_relation_edges_from_output(const std::string& output) {
    std::vector<WorkspaceRelationInfo> relations;
    std::istringstream stream(output);
    std::string line;
    std::vector<std::pair<std::size_t, std::string>> tree_stack;
    while (std::getline(stream, line)) {
        const std::string original_line = line;
        line = trim_ascii(line);
        if (line.empty()) {
            continue;
        }

        constexpr const char* rooted_marker = "Relations (tree) rooted at:";
        if (line.rfind(rooted_marker, 0) == 0) {
            const std::string root = trim_ascii(line.substr(std::char_traits<char>::length(rooted_marker)));
            if (!root.empty()) {
                tree_stack.clear();
                tree_stack.push_back({0, root});
            }
            continue;
        }

        constexpr const char* parent_marker = "Relations for parent:";
        if (line.rfind(parent_marker, 0) == 0) {
            const std::string root = trim_ascii(line.substr(std::char_traits<char>::length(parent_marker)));
            if (!root.empty()) {
                tree_stack.clear();
                tree_stack.push_back({0, root});
            }
            continue;
        }

        constexpr const char* prefix = "REL:";
        if (line.rfind(prefix, 0) == 0) {
            std::string rest = trim_ascii(line.substr(std::char_traits<char>::length(prefix)));
            const auto arrow = rest.find("->");
            const auto on = rest.find(" ON ");
            if (arrow == std::string::npos || on == std::string::npos || on <= arrow) {
                continue;
            }

            WorkspaceRelationInfo relation;
            relation.parent = trim_ascii(rest.substr(0, arrow));
            relation.child = trim_ascii(rest.substr(arrow + 2, on - (arrow + 2)));
            relation.parent_key = trim_ascii(rest.substr(on + 4));
            relation.child_key = relation.parent_key;
            relation.source = "DotTalk++ shell";
            if (!relation.parent.empty() && !relation.child.empty()) {
                merge_relation(relations, std::move(relation));
            }
            continue;
        }

        if (line.find(" ") == std::string::npos && line.find("->") == std::string::npos) {
            tree_stack.clear();
            tree_stack.push_back({0, line});
            continue;
        }

        if (line.rfind("->", 0) != 0 || tree_stack.empty()) {
            continue;
        }

        const std::size_t indent = leading_space_count(original_line);
        while (tree_stack.size() > 1 && tree_stack.back().first >= indent) {
            tree_stack.pop_back();
        }

        std::string rest = trim_ascii(line.substr(2));
        const auto arrow = rest.find("->");
        if (arrow != std::string::npos) {
            continue;
        }

        const auto matches = match_count_from_relation_line(rest);
        const auto match_marker = rest.find("(matches:");
        if (match_marker != std::string::npos) {
            rest = trim_ascii(rest.substr(0, match_marker));
        }
        const auto on = rest.find(" ON ");

        WorkspaceRelationInfo relation;
        relation.parent = tree_stack.back().second;
        relation.child = on == std::string::npos ? trim_ascii(rest) : trim_ascii(rest.substr(0, on));
        relation.parent_key = on == std::string::npos ? std::string{} : trim_ascii(rest.substr(on + 4));
        relation.child_key = relation.parent_key;
        relation.match_count = matches.value_or(0);
        relation.source = "DotTalk++ shell";
        if (!relation.parent.empty() && !relation.child.empty()) {
            const std::string child = relation.child;
            merge_relation(relations, std::move(relation));
            tree_stack.push_back({indent + 2, child});
        }
    }
    return relations;
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

std::string visible_area_id(AreaId id) {
    return id == 0 ? std::string("none") : std::to_string(id - 1);
}

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
    return lower_ascii(entry.path().extension().string()) == ".dbf";
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
            "DOTSCRIPT " + script.string(),
            {}
        });
        (void)ignored;
    }
}

} // namespace

struct Session::Impl {
    struct Area {
        AreaId id {0};
        xbase::DbArea area;
        std::filesystem::path path;
        std::string display_name;
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
            return find_area(static_cast<AreaId>(visible + 1));
        }

        const std::string wanted = lower_ascii(token);
        for (const auto& area : areas) {
            std::vector<std::string> names {
                area->display_name,
                area->path.filename().string(),
                area->path.stem().string(),
                area->area.logicalName()
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

    std::vector<std::unique_ptr<Area>> areas;
    std::vector<WorkspaceRelationInfo> relations;
    AreaId active_area_id {0};
    AreaId next_area_id {1};
    std::unique_ptr<GuiShellRuntime> shell_runtime {make_script_shell_runtime()};
};

Session::Session()
    : impl_(std::make_unique<Impl>()) {
    initialize_gui_paths();
    std::vector<StatusMessage> ignored_messages;
    for (const auto& script : existing_lifecycle_scripts({"init.ini", "dottalkpp.ini", "dotscript.ini"})) {
        RuntimeCliResult cli = impl_->shell_runtime->run(RuntimeCliRequest{
            "DOTSCRIPT " + script.string(),
            {}
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
        for (auto relation : parse_relation_edges_from_output(cli.output)) {
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
            result.path = existing->path;
            result.display_name = existing->display_name;
            result.record_count = existing->area.isOpen() ? existing->area.recCount64() : 0;
            result.messages.push_back(info("gui.open_table.already_open",
                                           "Table already open; selected existing GUI work area."));
            return result;
        }

        auto area = std::make_unique<Impl::Area>();
        area->id = impl_->next_area_id++;
        area->path = request.path;
        area->display_name = result.display_name;
        area->area.open(request.path.string());

        result.ok = true;
        result.area_id = area->id;
        result.record_count = area->area.recCount64();
        if (result.display_name.empty()) {
            result.display_name = area->area.logicalName();
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

    for (auto& area : impl_->areas) {
        area->area.close();
    }
    impl_->areas.clear();
    impl_->relations.clear();
    impl_->active_area_id = 0;
    impl_->next_area_id = 1;

    std::vector<std::filesystem::path> dbfs;
    for (const auto& entry : std::filesystem::directory_iterator(dir, ec)) {
        if (!ec && is_dbf_file(entry)) {
            dbfs.push_back(entry.path());
        }
    }
    std::sort(dbfs.begin(), dbfs.end(), workspace_dbf_path_less_like_cli);

    std::size_t opened = 0;
    for (const auto& dbf : dbfs) {
        try {
            auto area = std::make_unique<Impl::Area>();
            area->id = impl_->next_area_id++;
            area->path = dbf;
            area->display_name = dbf.filename().string();
            area->area.open(dbf.string());
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

    if (!impl_->areas.empty()) {
        impl_->active_area_id = impl_->areas.front()->id;
    }

    std::size_t indexes_attached = 0;
    std::set<AreaId> index_attached_area_ids;
    for (const auto& attachment : workspace_open_indexes_from_cli_output(shell_output, dir)) {
        auto* area = impl_->find_area(attachment.area_id);
        if (!area || !area->area.isOpen()) {
            continue;
        }

        std::string err;
        if (attach_gui_order_container(area->area, attachment.container, err)) {
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
            if (!area->area.isOpen() || index_attached_area_ids.count(area->id) != 0) {
                continue;
            }

            const auto candidates = default_index_candidates_for_area(area->area, area->path, mode);
            const auto container = first_existing_regular_file(candidates);
            if (!container) {
                continue;
            }

            std::string err;
            if (attach_gui_order_container(area->area, *container, err)) {
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

    std::vector<WorkspaceRelationInfo> schema_relations;
    const auto schema_areas = load_dtschema2_areas(schema_path, schema_relations);
    if (schema_areas.empty()) {
        messages.push_back(warning("gui.workspace.schema_empty",
                                   "WORKSPACE LOAD did not mirror into GUI areas because no schema areas were found.",
                                   schema_path.string()));
        return 0;
    }

    for (auto& area : impl_->areas) {
        area->area.close();
    }
    impl_->areas.clear();
    impl_->relations = std::move(schema_relations);
    impl_->active_area_id = 0;
    impl_->next_area_id = 1;

    std::size_t opened = 0;
    std::size_t indexes_attached = 0;
    AreaId max_area_id = 0;

    for (const auto& schema_area : schema_areas) {
        const auto dbf = resolve_schema_dbf_path(schema_area.dbf, schema_area.index_type);
        if (!dbf) {
            messages.push_back(warning("gui.workspace.schema_table_missing",
                                       "A WORKSPACE LOAD schema table could not be mirrored into a GUI area.",
                                       schema_area.dbf.string()));
            continue;
        }

        try {
            auto area = std::make_unique<Impl::Area>();
            area->id = static_cast<AreaId>(schema_area.slot + 1);
            max_area_id = std::max(max_area_id, area->id);
            area->path = *dbf;
            area->display_name = !schema_area.alias.empty()
                ? schema_area.alias + ".DBF"
                : dbf->filename().string();
            area->area.open(dbf->string());

            if (!schema_area.index.empty()) {
                if (const auto index = resolve_schema_index_path(schema_area.index, schema_area.index_type)) {
                    std::string err;
                    const bool attached = !trim_ascii(schema_area.tag).empty()
                        ? activate_gui_order(area->area, *index, schema_area.tag, true, err)
                        : attach_gui_order_container(area->area, *index, err);
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

    impl_->next_area_id = std::max<AreaId>(max_area_id + 1, 1);

    messages.push_back(info("gui.workspace.load_mirrored",
                            "WORKSPACE LOAD mirrored schema areas into GUI areas.",
                            std::to_string(opened) + " table(s) from " + schema_path.string()));
    if (indexes_attached > 0) {
        messages.push_back(info("gui.workspace.indexes_mirrored",
                                "WORKSPACE LOAD mirrored attached index containers into GUI areas.",
                                std::to_string(indexes_attached) + " index container(s)"));
    }
    if (!impl_->relations.empty()) {
        messages.push_back(info("gui.workspace.relations_mirrored",
                                "WORKSPACE LOAD mirrored schema relations into the GUI workspace model.",
                                std::to_string(impl_->relations.size()) + " relation(s)"));
    }
    return opened;
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
    if (!area || !area->area.isOpen()) {
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
    if (!area || !area->area.isOpen()) {
        result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open."));
        return result;
    }

    if (request.record_number < 1 || request.record_number > area->area.recCount64() ||
        request.record_number > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        result.messages.push_back(warning("gui.command.bad_recno", "Record number is outside the area range."));
        return result;
    }

    impl_->active_area_id = area->id;
    if (!area->area.gotoRec(static_cast<int32_t>(request.record_number)) || !area->area.readCurrent()) {
        result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
        return result;
    }

    result.ok = true;
    result.record_number = area->area.recno64();
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

    (*it)->area.close();
    impl_->areas.erase(it);

    if (impl_->active_area_id == request.area_id) {
        impl_->active_area_id = impl_->areas.empty() ? 0 : impl_->areas.front()->id;
    }

    result.ok = true;
    result.active_area_id = impl_->active_area_id;
    result.messages.push_back(info("gui.area.closed", "GUI work area closed."));
    return result;
}

ListAreasResult Session::list_areas() const {
    ListAreasResult result;
    result.active_area_id = impl_->active_area_id;

    result.areas.reserve(impl_->areas.size());
    for (const auto& area : impl_->areas) {
        if (!area->area.isOpen()) {
            continue;
        }
        result.areas.push_back(gui_area_info_from_dbarea(area->id,
                                                         area->id == impl_->active_area_id,
                                                         area->area,
                                                         area->display_name));
    }

    return result;
}

WorkspaceModel Session::workspace_model() const {
    WorkspaceModel model;
    const auto areas = list_areas();
    model.active_area_id = areas.active_area_id;
    model.tables = areas.areas;
    model.messages = areas.messages;
    model.relations = impl_->relations;

    auto relation_name = [](const Impl::Area& area) {
        std::vector<std::string> names {
            area.area.logicalName(),
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
    };

    auto find_relation_area = [&](const std::string& relation_table) -> Impl::Area* {
        const std::string wanted = lower_ascii(trim_ascii(relation_table));
        for (const auto& candidate : impl_->areas) {
            if (!candidate->area.isOpen()) {
                continue;
            }
            for (const auto& name : relation_name(*candidate)) {
                if (name == wanted) {
                    return candidate.get();
                }
            }
        }
        return nullptr;
    };

    auto field_index = [](const xbase::DbArea& area, const std::string& field_name) {
        const std::string wanted = lower_ascii(trim_ascii(field_name));
        const auto& fields = area.fields();
        for (std::size_t i = 0; i < fields.size(); ++i) {
            if (lower_ascii(trim_ascii(fields[i].name)) == wanted) {
                return static_cast<int>(i + 1);
            }
        }
        return 0;
    };

    auto count_relation_matches = [&](WorkspaceRelationInfo& relation) {
        if (relation.match_count != 0 || relation.parent.empty() || relation.child.empty()) {
            return;
        }

        auto* parent = find_relation_area(relation.parent);
        auto* child = find_relation_area(relation.child);
        if (!parent || !child) {
            return;
        }

        const int parent_field = field_index(parent->area, relation.parent_key);
        const int child_field = field_index(child->area, relation.child_key.empty()
            ? relation.parent_key
            : relation.child_key);
        if (parent_field <= 0 || child_field <= 0) {
            return;
        }

        const auto parent_recno = parent->area.recno64();
        const auto child_recno = child->area.recno64();
        std::string parent_value;
        try {
            if (parent_recno < 1 || parent_recno > parent->area.recCount64()) {
                if (!parent->area.gotoRec(1) || !parent->area.readCurrent()) {
                    return;
                }
            }
            if (!parent->area.readCurrent()) {
                return;
            }
            parent_value = trim_ascii(parent->area.get(parent_field));
        } catch (...) {
            return;
        }

        std::uint64_t count = 0;
        const auto child_count = child->area.recCount64();
        const auto limit = std::min<std::uint64_t>(
            child_count,
            static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max()));
        for (std::uint64_t recno = 1; recno <= limit; ++recno) {
            try {
                if (!child->area.gotoRec(static_cast<int32_t>(recno)) || !child->area.readCurrent()) {
                    continue;
                }
                if (trim_ascii(child->area.get(child_field)) == parent_value) {
                    ++count;
                }
            } catch (...) {
            }
        }

        if (child_recno >= 1 && child_recno <= child_count &&
            child_recno <= static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
            (void)child->area.gotoRec(static_cast<int32_t>(child_recno));
            (void)child->area.readCurrent();
        }
        if (parent_recno >= 1 && parent_recno <= parent->area.recCount64() &&
            parent_recno <= static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
            (void)parent->area.gotoRec(static_cast<int32_t>(parent_recno));
            (void)parent->area.readCurrent();
        }
        relation.match_count = count;
    };

    for (auto& relation : model.relations) {
        count_relation_matches(relation);
    }

    model.indexes.reserve(impl_->areas.size());
    for (const auto& area : impl_->areas) {
        if (!area->area.isOpen()) {
            continue;
        }

        WorkspaceIndexInfo index;
        index.area_id = area->id;
        index.area_name = area->display_name;
        index.kind = order_kind(area->area);
        index.active = orderstate::hasOrder(area->area);
        index.ascending = orderstate::isAscending(area->area);
        index.backend = order_backend(area->area);
        if (index.active) {
            index.container = orderstate::orderName(area->area);
            index.tag = orderstate::activeTag(area->area);
            if (const auto* manager = area->area.indexManagerPtr()) {
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

        for (auto relation : parse_relation_edges_from_output(cli.output)) {
            merge_relation(impl_->relations, std::move(relation));
        }

        if (const auto cli_area = last_cli_area_from_output(cli.output)) {
            if (*cli_area >= 0) {
                const AreaId area_id = static_cast<AreaId>(*cli_area + 1);
                if (auto* selected = impl_->find_area(area_id)) {
                    impl_->active_area_id = selected->id;
                    result.messages.push_back(info("gui.area.shell_selected",
                                                   "GUI selected the work area reported by the DotTalk++ shell.",
                                                   std::to_string(*cli_area)));
                }
            }
        }

        if (const auto recno = last_cli_recno_from_output(cli.output)) {
            auto* active = impl_->active_area();
            if (active && active->area.isOpen() && *recno >= 1 &&
                *recno <= static_cast<long long>(active->area.recCount64()) &&
                *recno <= static_cast<long long>(std::numeric_limits<int32_t>::max())) {
                if (active->area.gotoRec(static_cast<int32_t>(*recno)) && active->area.readCurrent()) {
                    result.messages.push_back(info("gui.cursor.shell_synced",
                                                   "GUI cursor mirrored the record reported by the DotTalk++ shell.",
                                                   std::to_string(*recno)));
                }
            }
        }

        auto* mirror_area = impl_->active_area();
        if (mirror_area && mirror_area->area.isOpen()) {
            const auto words = split_words(command_text);
            if (!words.empty()) {
                const std::string mirror_verb = lower_ascii(words[0]);
                if (!mirror_set_index_to_gui(mirror_area->area, words, result.messages) &&
                    !mirror_set_order_to_gui(mirror_area->area, words, result.messages)) {
                    if (mirror_verb == "ascend") {
                        (void)mirror_order_direction_to_gui(mirror_area->area, true, result.messages);
                    } else if (mirror_verb == "descend") {
                        (void)mirror_order_direction_to_gui(mirror_area->area, false, result.messages);
                    }
                }
            }
        }

        return workspace_open_mirrored;
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
            << "                    DTSchema contract skeletons\n"
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
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current GUI work area is selected.";
        } else {
            out << "ACTIVE GUI AREA\n"
                << "Area: " << visible_area_id(area->id) << "\n"
                << "Table: " << area->display_name << "\n"
                << "Records: " << area->area.recCount64() << "\n"
                << "Fields: " << area->area.fields().size() << "\n"
                << "File type: " << dbf_flavor_label(area->area) << "\n"
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
                    << visible_area_id(area->id) << "  "
                    << area->display_name << "  records="
                    << (area->area.isOpen() ? area->area.recCount64() : 0)
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
                        out << "Active area: " << visible_area_id(area->id)
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
            const std::size_t closed = impl_->areas.size();
            for (auto& area : impl_->areas) {
                area->area.close();
            }
            impl_->areas.clear();
            impl_->relations.clear();
            impl_->active_area_id = 0;
            impl_->next_area_id = 1;
            result.messages.push_back(info("gui.workspace.closed", "All GUI work areas were closed."));
            out << "WORKSPACE CLOSE\n"
                << "Closed GUI areas: " << closed;
        } else if (action == "graph") {
            out << "WORKSPACE GRAPH\n"
                << "Areas: " << impl_->areas.size() << "\n"
                << "Active area: ";
            if (impl_->active_area_id == 0) {
                out << "none\n";
            } else {
                out << visible_area_id(impl_->active_area_id) << "\n";
            }
            out << "Relations: workspace graph service pending\n"
                << "Indexes: workspace graph service pending\n"
                << "Browsers/lists: workspace graph service pending\n"
                << "ERSATZ presets: workspace graph service pending\n"
                << "DTSchema load/save: bootstrap menu active; graph service pending";
        } else if (action == "load" || action == "save" || action == "saveas") {
            const std::string name = remove_first_tokens(dispatch_command, 2);
            result.messages.push_back(info("gui.workspace.dtschema_skeleton",
                                           "DTSchema load/save is registered as a GUI workspace contract skeleton."));
            out << "WORKSPACE " << lower_ascii(action) << "\n"
                << "DTSchema: " << (name.empty() ? std::string("(not provided)") : name) << "\n"
                << "The .dtschema graph service is pending; this command is now reserved by the workbench.";
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
            out << visible_area_id(impl_->active_area_id) << "\n";
        }
        out << "Relations: workspace graph service pending\n"
            << "Indexes: workspace graph service pending\n"
            << "Browsers/lists: workspace graph service pending\n"
            << "ERSATZ presets: workspace graph service pending\n"
            << "DTSchema load/save: bootstrap menu active; graph service pending";
    } else if (verb == "status") {
        const auto* area = impl_->active_area();
        out << "GUI SESSION STATUS\n"
            << "Open areas: " << impl_->areas.size() << "\n"
            << "Active area: " << (area ? visible_area_id(area->id) : std::string("none")) << "\n";
        if (area && area->area.isOpen()) {
            out << "Active table: " << area->display_name << "\n"
                << "Records: " << area->area.recCount64() << "\n"
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
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.area.not_open", "Requested GUI work area is not open.", target));
            out << "No matching GUI work area is open: " << target;
        } else {
            impl_->active_area_id = area->id;
            out << "Selected GUI area " << visible_area_id(area->id) << ".\n"
                << "Table: " << area->display_name << "\n"
                << "Recno: " << area->area.recno64();
        }
    } else if (verb == "dbarea") {
        const auto* area = impl_->active_area();
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current GUI work area is selected.";
        } else {
            out << "DBAREA\n"
                << "Area: " << visible_area_id(area->id) << "\n"
                << "Logical name: " << area->area.logicalName() << "\n"
                << "Table: " << area->display_name << "\n"
                << "File type: " << dbf_flavor_label(area->area) << "\n"
                << "Path: " << area->path.string() << "\n"
                << "Open: yes\n"
                << "Records: " << area->area.recCount64() << "\n"
                << "Fields: " << area->area.fields().size() << "\n"
                << "Recno: " << area->area.recno64() << "\n"
                << "BOF: " << (area->area.bof() ? "yes" : "no") << "\n"
                << "EOF: " << (area->area.eof() ? "yes" : "no");
        }
    } else if (verb == "recno") {
        auto* area = impl_->active_area();
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            const auto words = split_words(dispatch_command);
            if (words.size() == 1) {
                out << area->area.recno64();
            } else {
                long long wanted = 0;
                if (!parse_i64(words[1], wanted) || wanted < 1 ||
                    wanted > static_cast<long long>(area->area.recCount())) {
                    result.messages.push_back(warning("gui.command.bad_recno", "RECNO needs a record number in range."));
                    out << "Usage: recno <record-number>";
                } else if (!area->area.gotoRec(static_cast<int32_t>(wanted)) || !area->area.readCurrent()) {
                    result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                    out << "RECNO failed.";
                } else {
                    out << area->area.recno64();
                }
            }
        }
    } else if (verb == "goto" || verb == "go") {
        auto* area = impl_->active_area();
        long long wanted = 0;
        const auto words = split_words(dispatch_command);
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else if (words.size() < 2 || !parse_i64(words[1], wanted) || wanted < 1) {
            result.messages.push_back(warning("gui.command.bad_recno", "GOTO needs a positive record number."));
            out << "Usage: goto <record-number>";
        } else {
            if (wanted > static_cast<long long>(std::numeric_limits<int32_t>::max()) ||
                !area->area.gotoRec(static_cast<int32_t>(wanted)) || !area->area.readCurrent()) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << "GOTO failed.";
            } else {
                out << "Recno: " << area->area.recno64();
            }
        }
    } else if (verb == "skip") {
        auto* area = impl_->active_area();
        long long delta = 1;
        const auto words = split_words(dispatch_command);
        if (!area || !area->area.isOpen()) {
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
            const bool moved = orderstate::hasOrder(area->area)
                ? skip_gui_area_ordered(area->area, n, order_err)
                : (n == 0 ? area->area.readCurrent()
                          : (area->area.skip(n) && area->area.readCurrent()));

            if (!moved) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << "SKIP failed.";
                if (!order_err.empty()) {
                    out << " " << order_err;
                }
            } else {
                out << "Recno: " << area->area.recno64();
            }
        }
    } else if (verb == "top" || verb == "bottom") {
        auto* area = impl_->active_area();
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            std::string order_err;
            const bool moved = orderstate::hasOrder(area->area)
                ? (verb == "top" ? position_gui_area_to_first_ordered(area->area, order_err)
                                  : position_gui_area_to_last_ordered(area->area, order_err))
                : (verb == "top" ? area->area.top() : area->area.bottom());
            if (!moved || !area->area.readCurrent()) {
                result.messages.push_back(warning("gui.command.nav_failed", "Could not move the active record pointer."));
                out << (verb == "top" ? "TOP" : "BOTTOM") << " failed.";
                if (!order_err.empty()) {
                    out << " " << order_err;
                }
            } else {
                out << "Recno: " << area->area.recno64();
            }
        }
    } else if (verb == "list" || verb == "browse") {
        const auto* area = impl_->active_area();
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            out << "BROWSE SUMMARY\n"
                << "Area: " << visible_area_id(area->id) << "\n"
                << "Table: " << area->display_name << "\n"
                << "Records: " << area->area.recCount64() << "\n"
                << "Fields: " << area->area.fields().size() << "\n"
                << "Use the Browse tab for row data.";
        }
    } else if (verb == "structure") {
        const auto* area = impl_->active_area();
        if (!area || !area->area.isOpen()) {
            result.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
            out << "No current table is selected.";
        } else {
            out << "STRUCTURE " << area->display_name << "\n";
            std::size_t index = 1;
            for (const auto& field : area->area.fields()) {
                out << index++ << "  " << field.name << "  "
                    << field.type << "(" << static_cast<int>(field.length)
                    << "," << static_cast<int>(field.decimals) << ")\n";
            }
        }
    } else if (verb == "cli") {
        const std::string cli_command = remove_first_token(command);
        const auto* area = impl_->active_area();
        RuntimeCliResult cli = impl_->shell_runtime->run(RuntimeCliRequest{
            cli_command,
            area ? area->path : std::filesystem::path{},
            area ? area->area.recno64() : 0
        });
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

        const auto* area = impl_->active_area();
        RuntimeCliResult cli = impl_->shell_runtime->run(RuntimeCliRequest{
            dispatch_command,
            area ? area->path : std::filesystem::path{},
            area ? area->area.recno64() : 0
        });
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
    if (!selected || !selected->area.isOpen()) {
        TableSnapshot snapshot;
        snapshot.area_id = request.area_id;
        snapshot.messages.push_back(warning("gui.snapshot.no_current_table", "No current table is selected."));
        return snapshot;
    }

    return gui_snapshot_from_dbarea(selected->id,
                                    selected->area,
                                    selected->display_name,
                                    request.first_record,
                                    request.max_records);
}

} // namespace dottalk::gui
