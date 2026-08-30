// @dottalk.file v1
// subsystem: xindex
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported


// src/cli/order_display.cpp
#include "xindex/order_display.hpp"
#include "cli/cli_bridge.hpp"
#include <sstream>

namespace orderdisplay {

std::string summarize(const xbase::DbArea& area) {
    std::ostringstream os;
    const bool attached = xindex_cli::db_index_attached(area);
    const bool asc      = xindex_cli::db_order_asc(area);
    const bool natural  = xindex_cli::db_order_is_natural(area);

    // AIF-148 residue: this line had NO ORDER PREDICATE AT ALL -- it printed
    // the DIRECTION flag, which defaults true -- so a table with no index
    // rendered `Order: ASCEND  (no index)`, contradicting itself in one line.
    // This is BROWSE's banner (app_simple_browser.cpp:544 and :740), so the
    // wrong word was on screen for the whole of a browse session.
    //
    // `attached` still decides the "(no index)" suffix and whether a path is
    // printed: that is the ATTACHMENT question and it is answered correctly.
    // Only the order WORD moves to the predicate that answers the question
    // the word is making a claim about.
    os << "Order: " << (natural ? "NATURAL" : (asc ? "ASCEND" : "DESCEND"));
    if (!attached) {
        os << "  (no index)";
        return os.str();
    }
    const std::string path = xindex_cli::db_index_path(area);
    os << "  File: " << path;
    // If CNX: show tag
    if (path.size() >= 4) {
        auto suf = path.substr(path.size()-4);
        for (auto& c : suf) c = (char)toupper((unsigned char)c);
        if (suf == ".CNX") {
            const std::string tag = xindex_cli::db_active_cnx_tag(area);
            if (!tag.empty()) {
                os << "  CNX TAG: " << tag;
            } else {
                os << "  CNX TAG: (none)";
            }
        }
    }
    return os.str();
}

} // namespace orderdisplay



