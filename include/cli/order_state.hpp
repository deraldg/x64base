// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// include/cli/order_state.hpp
// Per-area, CLI-visible order state.
//
// Notes:
// - This is intentionally lightweight: it does NOT own index backends.
// - It only tracks what the CLI considers the "active order container" and
//   (for tag containers) the active tag name.

#include <string>

namespace xbase { class DbArea; }

namespace orderstate {

// Sets/clears active order container path (e.g., "<name>.inx", "<name>.cnx", "<name>.cdx", "<name>.six", "<name>.snx").
// Opening one index implicitly closes the other for the same area.
void setOrder(xbase::DbArea& area, const std::string& container_path);
void clearOrder(xbase::DbArea& area);

// Query the attached container.
//
// hasOrder() answers "IS A CONTAINER ATTACHED", not "is an order active".
// The two are different and the difference is not cosmetic: WORKSPACE OPEN
// attaches a .cdx to every table it lands and selects NO TAG, so hasOrder()
// is true while the table is still in natural order.  Callers asking about
// ATTACHMENT (detach-the-other-container, cache invalidation, "which file")
// want this one.  Callers asking WHICH ORDER THE CURSOR MUST FOLLOW want
// isNaturalOrder() below.  AIF-148.
bool hasOrder(const xbase::DbArea& area);
std::string orderName(const xbase::DbArea& area);

// Is the area traversed in NATURAL (physical) order?
//
// PHYSICAL IS AN ORDER IN THIS HOUSE (owner, 2026-08-29: "it has been our
// house usage") -- OrderBackend::Natural is a member of the enum, SET ORDER
// PHYSICAL|NATURAL|PHYS are typeable order names, and the engine prints
// "Order: NATURAL".  So this predicate NEVER means "there is no order".  It
// names WHICH order is in force, and both of its values are an answer:
//
//   true  -> the natural (physical) order.  No container attached, OR a tag
//            container (.cdx/.cnx) is attached with no tag selected.
//   false -> the attached container's order.  A tag container with a tag, or
//            a non-tag container (.inx/.isx/.csx/.six/.snx), which IS its own
//            order and needs no tag.
//
// There is deliberately no third state and no way to spell "none": a caller
// that reaches this function always leaves it with a traversal to perform.
bool isNaturalOrder(const xbase::DbArea& area);

// Direction helpers (default: ASCEND).
void setAscending(xbase::DbArea& area, bool ascending);
bool isAscending(const xbase::DbArea& area);

// Tag helpers for tag-container index formats (CNX, CDX).
// For non-tag formats (INX/ISX/CSX/SIX/SNX), the stored tag is cleared.
void setActiveTag(xbase::DbArea& area, const std::string& tag_name);
std::string activeTag(const xbase::DbArea& area);

// Container-type helpers.
// These classify the currently active order container by suffix.
bool isInx(const xbase::DbArea& area);
bool isCnx(const xbase::DbArea& area);
bool isCdx(const xbase::DbArea& area);
bool isIsx(const xbase::DbArea& area);
bool isCsx(const xbase::DbArea& area);
bool isSix(const xbase::DbArea& area);
bool isSnx(const xbase::DbArea& area);

} // namespace orderstate