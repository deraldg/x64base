// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// xbase_cli.hpp
// CLI / shell integration extensions for xbase.
// This header must not be included by non-CLI consumers such as pydottalk
// unless they intentionally provide compatible implementations.

#pragma once

#include <string>
#include "xbase.hpp"

// THE NATIVE FIELD-WRITE FUNNEL.
//
// This header declared replaceFieldStored() with the contract below on
// 2026-07-30 and NOTHING EVER DEFINED IT. A session manifest recorded it that
// same day -- "a link error waiting for its first caller" -- and the header
// reachability gate independently found the file unreachable on 2026-09-06,
// where it sits at line 71 of tools/staging/header_reachability_baseline.txt.
// Two detections, six weeks, no caller. Meanwhile cmd_replace.cpp and
// cmd_calcwrite.cpp each hand-rolled the TABLE ON / TABLE OFF fork this
// contract describes, which is how one logical write became several doors that
// no single check could stand in front of. Built out under AIF-156.
//
// WHY A FUNNEL AND NOT A CHECK IN EVERY COMMAND. A per-command check is only
// as good as the roll call of commands, and that roll call is not knowable at
// runtime -- a regression marker can prove a route refuses, but no marker can
// prove there are no other routes. One funnel plus a static gate over the
// callers can: the funnel is where the refusal lives, the gate is what says
// nobody went around it.
//
// EXEMPTION IS BY ROUTE, NOT BY FLAG. Two writers must be able to write a
// PRIMARY key and both do it by calling DbArea:: directly, BELOW this funnel:
// the key generator in append_support, and VALIDATE UNIQUE ... REPAIR, which
// exists to renumber inherited data. There is deliberately no bypass parameter
// here, because a parameter can be passed by anyone and a route cannot. Same
// shape as PACK being the only thing that removes a deleted row.
namespace xbase::cli {

// Buffered/shell-aware replace entry point.
// Contract:
// - field1 is 1-based and already resolved by caller
// - stored_value is already normalized into on-disk form
// - field constraints are enforced HERE; a write to a declared PRIMARY key is
//   refused with a reason in *err, and nothing is buffered or written
// - in TABLE ON mode, this buffers only and does not lock/write
// - in TABLE OFF mode, this delegates to DbArea::replaceFieldStored()
// - may update CLI-side dirty/stale state
// - may use shell/work-area context if needed
//
// RETURNS TRUE WITH A NON-EMPTY *err TO MEAN "WRITTEN, INDEX NOT MAINTAINED".
// That three-state return is DbArea::replaceFieldStored()'s contract and it is
// inherited verbatim rather than flattened, because a caller that treats a
// warning as a failure prints a clean-looking error over a record that is
// already on disk. Callers must test the bool AND the string.
bool replaceFieldStored(DbArea& area, int field1, const std::string& stored_value, std::string* err = nullptr);

// Buffered/shell-aware NULL entry point. Same funnel, same constraint gate.
//
// A NULL IS NOT A VALUE AND CANNOT SHARE THE VALUE PATH. It must not be
// evaluated, currency-normalized, memo-encoded or width-validated, and every
// one of those steps would happily turn it into the string "NULL" -- which is
// why REPLACE intercepts it before the value pipeline. That interception is
// correct and it is also a SECOND DOOR: without this sibling, a constraint
// gate on the value path alone lets REPLACE <pk> WITH NULL through, and a
// nulled key is worse than an overwritten one -- the row keeps its place and
// loses its identity.
//
// Refuses while TABLE buffering is ON: the buffer stages one string per field
// and has no way to say NULL, so buffering one would commit a blank that reads
// back as not-null -- a wrong answer wearing a success message.
bool replaceFieldNull(DbArea& area, int field1, bool make_null = true, std::string* err = nullptr);

// Optional helper for CLI-side stale-field marking after a core mutation.
// Safe to call from command code; non-CLI consumers should not depend on it.
void mark_all_fields_stale_best_effort(DbArea& area, int area0);

// Optional helper for CLI-side area resolution when shell work-area context exists.
// Returns -1 when unavailable.
int resolve_current_index(DbArea& area);

} // namespace xbase::cli