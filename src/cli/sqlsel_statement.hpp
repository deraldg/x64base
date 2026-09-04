// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

// src/cli/sqlsel_statement.hpp -- SQLSEL set-oriented statement surface.
//
// This is the SQL statement coordinator. Everything beneath it consumes house
// engine seams: workspace-scoped area resolution, typed TupleRows, expression
// compile/eval, cursor guards, locks, table buffers, TBJ1 WAL, and COMMIT.
//
// SELECT does not read or disturb the current area, record pointers, SET FILTER,
// or SET RELATION. DML deliberately mutates one workspace-local target through
// the same storage and transaction machinery as native xBase commands.

#pragma once

#include <string>

namespace sqlsel {

// Try to execute `tail` as a SELECT statement. Returns false only when the text
// is not statement-shaped, allowing the caller's legacy predicate-scan path.
bool try_execute_select(const std::string& tail);

// Execute any canonical SQLsel statement. SELECT remains backward-compatible
// with the keyword-optional SQLSEL form; INSERT/UPDATE/DELETE and transaction
// control require their SQL keyword.
bool try_execute_statement(const std::string& statement);

// SET MODE uses this to prevent a live SQL transaction from being orphaned by
// changing command languages before COMMIT or ROLLBACK.
bool transaction_active() noexcept;

// The ONE runtime description of the statement grammar. Exported so the SQLSEL
// usage printer shares it instead of keeping a second copy -- three authorities
// for one command's help is how the text drifts from the code (AIF-074 caught
// this twice in one day).
void print_statement_usage();

} // namespace sqlsel
