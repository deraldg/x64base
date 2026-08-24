// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

// MOVED HERE FROM src/gui/core/relation_parse.cpp on 2026-08-24 by rulings
// R124 and R125. BEHAVIOUR IS UNCHANGED: the bodies below are the same text,
// operating on RelationRecord instead of the GUI's WorkspaceRelationInfo, and
// the round-trip fixture that held them (dottalkpp_relation_merge_test) moved
// with them rather than being rewritten.
//
// WHAT DID CHANGE, and it is one thing: parse_relation_posture_line takes a
// workspace HANDLE where it used to take a NAME. See R125 and the note on
// RelationRecord::workspace.
//
// STANDARD LIBRARY ONLY, on purpose. This file is filed under src/xbase because
// that is where both consumers can reach it -- not because it needs anything
// here. It includes no engine header and touches no filesystem, so a fixture
// can compile it directly and link nothing, which is exactly how the unit it
// came from was already being tested.

#include "xbase/relation_wire.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

namespace xbase::relwire {
namespace {

// A PRIVATE COPY, AND THE SIXTH IN THE TREE, DECLARED RATHER THAN MISSED.
// src/gui/core alone holds four more (session.cpp, gui_cli_bridge.cpp,
// gui_shell_runtime.cpp, relation_parse.cpp). Consolidating them is real work
// with 88+ call sites and it is NOT smuggled into a move whose whole claim is
// that it carries no behaviour. It is named here so the next reader knows the
// duplication was chosen.
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

} // namespace

void split_relation_keys(const std::string& on_clause,
                         std::string& parent_key,
                         std::string& child_key) {
    const std::string clause = trim_ascii(on_clause);
    const auto to = clause.find(" TO ");
    if (to == std::string::npos) {
        parent_key = clause;
        child_key = clause;
        return;
    }
    parent_key = trim_ascii(clause.substr(0, to));
    child_key = trim_ascii(clause.substr(to + 4));
    if (child_key.empty()) {
        child_key = parent_key;
    }
}

bool format_relation_posture_line(const RelationRecord& relation,
                                  std::string& out) {
    if (relation.parent.empty() || relation.child.empty() ||
        relation.parent_key.empty()) {
        return false;
    }
    out = "RELATION " + relation.parent + " " + relation.child +
          " ON " + relation.parent_key;
    // Only when the two sides actually differ, so a file full of ordinary
    // same-name relations does not churn.
    if (!relation.child_key.empty() && relation.child_key != relation.parent_key) {
        out += " TO " + relation.child_key;
    }
    return true;
}

bool parse_relation_posture_line(const std::string& line,
                                 std::uint64_t owning_workspace,
                                 RelationRecord& out) {
    constexpr const char* prefix = "RELATION ";
    const std::string text = trim_ascii(line);
    if (text.rfind(prefix, 0) != 0) {
        return false;
    }
    const std::string rest =
        trim_ascii(text.substr(std::char_traits<char>::length(prefix)));
    const auto on = rest.find(" ON ");
    if (on == std::string::npos) {
        return false;
    }

    RelationRecord relation;
    relation.workspace = owning_workspace;
    std::istringstream head(rest.substr(0, on));
    head >> relation.parent >> relation.child;
    split_relation_keys(rest.substr(on + 4), relation.parent_key, relation.child_key);
    if (relation.parent.empty() || relation.child.empty() ||
        relation.parent_key.empty()) {
        return false;
    }
    out = std::move(relation);
    return true;
}

} // namespace xbase::relwire
