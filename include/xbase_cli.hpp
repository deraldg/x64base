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
#include <utility>
#include <vector>
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

// THE GATE ON ITS OWN, AND IT EXISTS BECAUSE REPLACE_MULTI MUST NOT CALL
// replaceFieldStored() ONCE PER FIELD.
//
// replaceFieldStored() bundles three things -- ask the gate, stage or write,
// maintain the index -- which is exactly right for a caller writing ONE field.
// REPLACE_MULTI writes MANY fields under ONE record lock, with ONE physical
// writeCurrent() and ONE before/after index snapshot pair. Calling the
// single-field funnel N times would replace that with N locks, N writes and N
// snapshot pairs: slower, and far worse, NOT ATOMIC -- a refusal on the third
// field would leave the first two already on disk and the record half-written
// under a message saying the write failed.
//
// So the funnel is SPLIT rather than DUPLICATED. This is the same gate
// replaceFieldStored() asks, exposed so a multi-field writer can ask it about
// EVERY field BEFORE writing ANY of them. One definition of "may this field be
// written", two callers whose write strategies legitimately differ.
//
// ALL OR NOTHING, AND THAT IS THE WHOLE POINT. It returns false on the FIRST
// refusal and nothing has been written, because by contract the caller has not
// written yet. `refused_field1` receives the 1-based field that refused so the
// caller can name it; pass nullptr if the message does not need it.
//
// THE VALUE IS PASSED BUT NOT CONSULTED TODAY. The only constraint enforced
// here is PRIMARY, which refuses a write to the field regardless of what is
// being written. Callers therefore pass whatever they are ABOUT to store --
// for a memo field that is the payload, not the handle it will become. That is
// safe only while the gate ignores the value, and this sentence is the marker
// for whoever adds a constraint that does not.
bool gateFieldWrites(const DbArea& area,
                     const std::vector<std::pair<int, std::string>>& writes,
                     std::string* err = nullptr,
                     int* refused_field1 = nullptr);


// THE KEY TRAVELS ONLY IF THE DESTINATION CAN HOLD IT.
//
// R142 -- "the key declaration travels, the key values are the operator's
// call." COPY and SORT are two of the NINETEEN row-creating paths the primary
// key charter records as minting no key at all. They build their destination
// through dbf_create::create_dbf(), and the only writer of the x64 metadata
// block on that path -- x64_build_name_metadata() -- has NO FLAGS PARAMETER
// and writes X64FieldMetaEntry.flags as a hardcoded zero. A destination is
// therefore born with no designation, and nothing in the creation path can
// give it one. This is the shared disposition that decides whether the
// source's designation follows, and it is ONE function rather than a rule per
// verb for the same reason the write funnel is one door.
//
// IT IS CALLED AFTER THE ROWS ARE WRITTEN, NEVER BEFORE, AND THAT ORDER IS
// LOAD-BEARING. COPY and SORT populate their destination with DbArea::set() --
// the engine primitive, BELOW this funnel. Stamping first would copy cleanly
// on today's build only because the immutability rule does not yet live in
// DbArea::set(); the charter's own rule table records that cell as "nothing,
// anywhere". On the day it does, a pre-stamped destination refuses its own
// rows and the failure reads as a key bug rather than as an ordering bug.
// Stamping last also means the designation lands on a column the source has
// already filled.
//
// A BLANK OR DUPLICATED COLUMN IS REFUSED, INCLUDING WHEN THE OPERATOR ASKS
// FOR IT. FINDING_A_FRESH_PROCESS_ENFORCES_A_KEY_IT_WILL_NOT_MINT measured
// what such a table does: the row is born with a blank key, the funnel then
// refuses every attempt to fill it, and it can never be completed. SORT makes
// this reachable -- SORT ... UNIQUE de-duplicates on the SORT KEYS, not on the
// key column, so a sort keyed on any other column can emit duplicates beneath
// a stamp claiming there are none. THE OPERATOR MAY CHOOSE TO DROP A KEY. THEY
// MAY NOT CHOOSE TO MINT A FALSE ONE.
//
// THIS IS NOT THE BYPASS PARAMETER THE CHARTER REFUSED, and the distinction
// has to be stated or it will be misread. "A parameter can be passed by anyone
// and a route cannot" governs BYPASSING THE FUNNEL'S REFUSAL. These options
// govern OPERATOR INTENT ABOUT A KEY ON A NEW TABLE -- a question the funnel
// does not answer and cannot. Nothing here licenses a bypass parameter.
enum class KeyTravel {
    // Carry the designation when it can be carried truthfully; REFUSE the
    // operation when it cannot. The default, because both quiet alternatives
    // are worse: dropping in silence loses a key the operator believed in,
    // and stamping in silence mints one the engine cannot honour.
    RefuseIfBlocked = 0,

    // Proceed without the designation, by explicit request. The destination is
    // a plain table. Reported, never silent.
    Drop,
};

struct KeyTravelResult {
    bool        proceed{false};  // may the operation report success
    bool        stamped{false};  // the designation was written to the destination
    std::string detail;          // what happened, for the CALLER to render
};

// dst must be OPEN AND FULLY POPULATED: this scans it and then stamps it.
// Returns rather than prints, like everything else in this funnel -- COPY and
// SORT say different things about the same outcome.
KeyTravelResult carryPrimaryKey(const DbArea& src, DbArea& dst, KeyTravel choice);

// Optional helper for CLI-side stale-field marking after a core mutation.
// Safe to call from command code; non-CLI consumers should not depend on it.
void mark_all_fields_stale_best_effort(DbArea& area, int area0);

// Optional helper for CLI-side area resolution when shell work-area context exists.
// Returns -1 when unavailable.
int resolve_current_index(DbArea& area);

} // namespace xbase::cli