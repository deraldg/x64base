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
#include <vector>

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

// The field name with any `table.` qualifier stripped, upper-cased. Matches
// set_relations.cpp's naked_field + up_copy, which is the behaviour being
// preserved rather than redesigned.
std::string naked_upper(std::string s) {
    const auto dot = s.find('.');
    if (dot != std::string::npos) s = s.substr(dot + 1);
    s = trim_ascii(std::move(s));
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

std::string join_csv(const std::vector<std::string>& fields) {
    std::string out;
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (i) out += ",";
        out += fields[i];
    }
    return out;
}

} // namespace

bool relation_field_lists_match(const std::vector<std::string>& a,
                                const std::vector<std::string>& b) {
    // LENGTH FIRST, and a different length is a different key -- the shipped
    // grammar requires the two sides to be the same LENGTH, not the same names.
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (naked_upper(a[i]) != naked_upper(b[i])) return false;
    }
    return true;
}

RelationRecord make_relation_record(std::uint64_t workspace,
                                    std::string parent,
                                    std::string child,
                                    const std::vector<std::string>& parent_fields,
                                    const std::vector<std::string>& child_fields) {
    RelationRecord record;
    record.workspace  = workspace;
    record.parent     = std::move(parent);
    record.child      = std::move(child);
    record.parent_key = join_csv(parent_fields);
    // MIRRORING IS THE SIGNAL. format_relation_posture_line emits ` TO ` only
    // when the two keys DIFFER as text, so making them identical here is how
    // "these name the same key" travels -- and it is why the naked comparison
    // has to happen on this side rather than inside the formatter, which sees
    // only the finished strings.
    record.child_key  = (child_fields.empty() ||
                         relation_field_lists_match(parent_fields, child_fields))
                            ? record.parent_key
                            : join_csv(child_fields);
    return record;
}

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
