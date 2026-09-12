// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <memory>
#include <string>

namespace xbase { class DbArea; }
namespace dottalk::expr { struct Expr; }

namespace filter {

// Install or replace the persistent SET FILTER expression for this area.
bool set(xbase::DbArea* area, const std::string& text, std::string& err);

// Clear the persistent SET FILTER expression for this area.
void clear(xbase::DbArea* area);

// True if this area currently has a compiled persistent filter.
bool has(xbase::DbArea* area);

// True if this area has any active persistent filter state.
// This is the query used by navigation redirection.
bool has_active_filter(xbase::DbArea* area);

// WHO DECIDES ABOUT DELETED ROWS ON THIS CALL.
//
// AIF-123, 2026-08-24. In xBase an EXPLICIT CLAUSE BEATS THE SESSION DEFAULT:
// `COUNT FOR DELETED()` must return rows even under SET DELETED ON. The gate
// cannot see a caller's clause, and a gate that filtered unconditionally would
// delete those rows out from under the clause before it ran.
//
// So the caller says which it is, exactly once, at the call. SessionDefault is
// the DEFAULT VALUE deliberately: a caller with no opinion about deleted rows
// wants the session's answer, and the twelve existing call sites all mean that.
// Making CallerHandles the default would have restored the setting to nobody.
enum class DeletedPolicy {
    SessionDefault,   // consult SET DELETED
    CallerHandles     // an explicit deleted clause is in force here; stay out
};

// IS THE LOGICAL VIEW SUBJECT TO FILTERING AT ALL?
//
// R121, 2026-08-24. This is the question navigation has to ask before it
// decides whether to traverse the visible set or the raw order, and asking it
// wrongly is the whole of the R121 defect: navsel::resolve_mode asked
// has_active_filter() instead, so SET DELETED -- the OTHER reason the logical
// view differs from the raw order -- never reached SKIP, TOP or BOTTOM.
//
// IT LIVES HERE BECAUSE visible() LIVES HERE. Both halves of visibility are
// applied in one place by design (AIF-123); a caller assembling its own
// `has_active_filter(a) || deleted_on` would be the second spelling, and the
// first thing to go stale when a third reason to hide a row arrives.
//
// NAMED FOR WHAT IT KNOWS. It says the view is SUBJECT TO a filter, not that
// any row is actually hidden -- a SET FILTER that matches everything hides
// nothing and this still answers true. A name promising more than the code
// delivers is worse than no name (owner ruling 2026-08-22, FREE vs NEXT).
bool view_is_filtered(xbase::DbArea* area);

// Visibility gate used by LIST / COUNT / SMARTLIST / LOCATE and now nav redirect.
// Applies SET DELETED (per `deleted`), the persistent SET FILTER, and an
// optional FOR expression.
bool visible(xbase::DbArea* area,
             const std::shared_ptr<dottalk::expr::Expr>& for_ast,
             DeletedPolicy deleted = DeletedPolicy::SessionDefault);

} // namespace filter