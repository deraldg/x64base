// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "relation_parse.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace dottalk::gui {
namespace {

// PRIVATE COPIES, DELIBERATELY. session.cpp keeps its own trim_ascii and
// lower_ascii because they have 49 and 39 call sites there, and this commit
// must contain NO behaviour -- sharing them would mean editing 88 call sites
// in a commit whose whole claim is that it is a move. That makes these the
// fifth and fourth copies in src/gui/core respectively (gui_cli_bridge.cpp:32,
// gui_shell_runtime.cpp:59, session.cpp:69/80 are the others). Consolidating
// all of them is real work and is NOT smuggled in here; it is named so the
// next reader knows the duplication was chosen rather than missed.
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

// Leading non-negative integer, or nothing. session.cpp's parse_i64_prefix
// also accepts a sign and is used six more times there, so it stays there;
// this is the part the relation tree actually needs.
std::optional<std::uint64_t> leading_u64(const std::string& text) {
    std::size_t index = 0;
    while (index < text.size() && std::isspace(static_cast<unsigned char>(text[index])) != 0) {
        ++index;
    }
    std::string digits;
    while (index < text.size() && std::isdigit(static_cast<unsigned char>(text[index])) != 0) {
        digits.push_back(text[index++]);
    }
    if (digits.empty()) {
        return std::nullopt;
    }
    try {
        return static_cast<std::uint64_t>(std::stoull(digits));
    } catch (...) {
        return std::nullopt;
    }
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
    return leading_u64(trim_ascii(line.substr(marker + 9)));
}

} // namespace

// TWO DEFECTS FIXED HERE, both named in AIF-078 D9 sec 4 item 5 and excluded
// from I1.2 in writing (D10 sec 8a) until the field had a writer.
//
// 1. WORKSPACE WAS NOT IN THE IDENTITY PREDICATE. Two edges differing only by
//    owning workspace fused into one. Harmless while every relation was stamped
//    DEFAULT; a silent data loss the moment the store was partitioned and the
//    field got written. This is the two-resolver defect I1.3a closed in the
//    engine, one layer up, and sec 4 item 5 predicted it by name.
//
// 2. AN EMPTY KEY WAS COMPATIBLE WITH ANYTHING, so the merge was
//    ORDER-DEPENDENT, and a keyless edge meeting more than one candidate
//    attached to whichever happened to be first in the vector. The fix was a
//    second pass that fused only a UNIQUE keyless candidate and otherwise let
//    the edge become its own row.
//
//    THAT PASS IS DELETED, 2026-08-23, and this is the record of a prediction
//    of mine that was WRONG. I wrote in claude/AIF078_FINDING_RELATION_KEY_
//    GRAMMAR.md that the refuse-to-fuse branch was producer-reachable, citing
//    the accumulation across commands. The steward asked which thing was
//    missing a persister. Measuring to answer falsified the claim:
//
//      relations_store() has exactly ONE constructor -- `Relation r;` at
//      set_relations.cpp:586, inside add_relation, which returns false at :570
//      when either field list is empty. REL LOAD does not bypass it;
//      import_relations (:841) routes every spec back through add_relation.
//
//    So no stored relation is keyless, format_on_fields (:894) never returns
//    empty, and the tree never emits a `-> child` line without ` ON `. The
//    comment this replaces claimed the tree gives "sometimes no key". No
//    relation producer in this tree can. The branch was the AIF-079 shape --
//    a mechanism with zero call sites -- and it is deleted the same way
//    gui_workspace_of_area(AreaId) was earlier the same day.
//
//    IT WAS REACHABLE, but only by accident, which is worse than dead:
//    parse_relation_edges_from_output runs on the output of EVERY command, so
//    a bare word followed by an indented `-> something` synthesised a
//    "relation" out of text that was not one. That is closed at the PRODUCER
//    below (ruling D10 R6.3, "enforce the reservation AT THE PRODUCER" --
//    the same shape as workspace::join refusing a negative engine slot)
//    rather than absorbed here, so this function no longer has to have an
//    opinion about a value it can no longer be handed.
//
// 3. THE MATCH COUNT'S ABSENCE WAS SPELLED ZERO. It is now MaybeMatchCount --
//    ruling D10 R6, and R6.3 binds retroactively by the steward's "clean
//    start". See model.hpp for why the type beats the sentinel.

void merge_relation(std::vector<WorkspaceRelationInfo>& relations, WorkspaceRelationInfo relation) {
    const auto same_edge = [&](const WorkspaceRelationInfo& existing) {
        return lower_ascii(existing.workspace) == lower_ascii(relation.workspace) &&
               lower_ascii(existing.parent) == lower_ascii(relation.parent) &&
               lower_ascii(existing.child) == lower_ascii(relation.child);
    };

    // Pass 1: the same edge on the same key. Exact, order-independent.
    auto found = std::find_if(relations.begin(), relations.end(),
                              [&](const WorkspaceRelationInfo& existing) {
        return same_edge(existing) &&
               lower_ascii(existing.parent_key) == lower_ascii(relation.parent_key);
    });

    if (found == relations.end()) {
        relations.push_back(std::move(relation));
        return;
    }

    // The parent_key fill-in went with pass 2: no producer can hand us an
    // empty one any more, so a row cannot be sitting here with one either.
    //
    // The CHILD key fill-in stays, and is NOT dead code waiting to be found.
    // It is unreachable only because all three parse sites currently assign
    // child_key = parent_key, which is finding 4a -- the ` TO ` clause the
    // producer emits and the parser does not split. gui_workspace_format.cpp
    // already measured the size of that: 190 of 1,102 RELATION lines (17.2%)
    // in the live catalog carry an explicit TO. This line goes live the day
    // 4a lands, and deleting it would have to be undone that same day.
    if (found->child_key.empty()) {
        found->child_key = relation.child_key;
    }
    if (!found->match_count) {
        found->match_count = relation.match_count;
    }
    if (!relation.source.empty()) {
        found->source = relation.source;
    }
}

std::vector<WorkspaceRelationInfo> parse_relation_edges_from_output(
        const std::string& output,
        const std::string& owning_workspace) {
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
            relation.workspace = owning_workspace;
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
        relation.workspace = owning_workspace;
        relation.parent = tree_stack.back().second;
        relation.child = on == std::string::npos ? trim_ascii(rest) : trim_ascii(rest.substr(0, on));
        relation.parent_key = on == std::string::npos ? std::string{} : trim_ascii(rest.substr(on + 4));
        relation.child_key = relation.parent_key;
        // R6: the count keeps its absence. "(matches: n/a)" is what the
        // producer prints when it could not compute one (set_relations.cpp
        // :1010), and value_or(0) used to turn that into a zero the wx grid
        // then showed the user as "0".
        relation.match_count = matches;
        relation.source = "DotTalk++ shell";
        // R6.3, ENFORCED AT THE PRODUCER. No relation in this tree is keyless
        // -- add_relation refuses empty field lists -- so a `-> something`
        // line with no ` ON ` is not a relation, it is arbitrary command
        // output that happens to be shaped like one. It is dropped WHOLE:
        // no row, and no tree_stack push either, so nothing nests under a
        // parent that was never a parent.
        if (relation.parent_key.empty()) {
            continue;
        }
        if (!relation.parent.empty() && !relation.child.empty()) {
            const std::string child = relation.child;
            merge_relation(relations, std::move(relation));
            tree_stack.push_back({indent + 2, child});
        }
    }
    return relations;
}
} // namespace dottalk::gui
