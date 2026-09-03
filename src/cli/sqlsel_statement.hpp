// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

// src/cli/sqlsel_statement.hpp -- SQLSEL set-oriented statement surface (P3/P4.1).
//
// The ONE new component of the SQLSEL lane: a SELECT statement parser.
// Everything beneath it consumes proven engine seams (area resolution,
// predicate compile/eval, tuple projection, cursor guards, and P4.1's own
// correctness-first two-table nested-loop matcher).
//
// Orthogonality (R16): a statement reads the table named in FROM. It does not
// read or disturb session state -- not the current area, not the record
// pointer, not SET FILTER, not SET RELATION. Read-only in v1 (DML is P5).
//
// Flip status to supported when gate G3 is green (the flip is the publish).

#pragma once

#include <string>

namespace sqlsel {

// Try to execute `tail` as a SELECT statement.
//   tail: everything after the SQLSEL verb.
// Returns true when the tail began with SELECT and was handled here (whether
// it succeeded or reported a corrective error). Returns false when the tail is
// not a SELECT statement, so the caller keeps its legacy predicate-scan path.
bool try_execute_select(const std::string& tail);

// The ONE runtime description of the statement grammar. Exported so the SQLSEL
// usage printer shares it instead of keeping a second copy -- three authorities
// for one command's help is how the text drifts from the code (AIF-074 caught
// this twice in one day).
void print_statement_usage();

} // namespace sqlsel
