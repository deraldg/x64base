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

// Visibility gate used by LIST / COUNT / SMARTLIST / LOCATE and now nav redirect.
// Applies SET DELETED (per `deleted`), the persistent SET FILTER, and an
// optional FOR expression.
bool visible(xbase::DbArea* area,
             const std::shared_ptr<dottalk::expr::Expr>& for_ast,
             DeletedPolicy deleted = DeletedPolicy::SessionDefault);

} // namespace filter