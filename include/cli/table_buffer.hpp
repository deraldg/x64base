// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <sstream>
#include <cstddef>
#include <string>

namespace xbase { class DbArea; }

// TABLE buffering (planned). Phase 0: command stubs + help.
// Now includes table_buffer support (auto-init on TABLE ON, COMMIT/ROLLBACK stubs)
void cmd_TABLE_BUFFER(xbase::DbArea& A, std::istringstream& in);
void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);
void cmd_ROLLBACK(xbase::DbArea& A, std::istringstream& in);

// ---------------------------------------------------------------------------
// AIF-159: a COMMIT verdict a caller can read.
//
// commit_one_area() inside cmd_commit.cpp has always produced a verdict. Only
// cmd_COMMIT ever saw it, and cmd_COMMIT returns void, so every other caller
// had to guess. SQLsel guessed by asking whether the table buffer was empty
// afterwards and calling that success -- a proxy that holds today only because
// every failing arm happens to retain the buffer. Retention is not part of the
// contract, so the day a failure path clears the buffer, SQLsel reports a
// commit that did not happen. Worse, the proxy names retention as the cause of
// every refusal, which is the wrong cause for a trigger veto.
//
// This is additive by design. cmd_COMMIT keeps its exact signature: it is a
// catalogued command (SYSCMD row CMD_COMMIT -> cmd_COMMIT), it is dispatched
// by function pointer, and TABLE BUFFER applications call it. Its observable
// behaviour is unchanged -- same messages, same SET TALK handling, same state.
// ---------------------------------------------------------------------------
namespace cli { namespace commit {

enum class Verdict {
    NoChanges,            // nothing was buffered; there was nothing to apply
    Complete,             // every buffered change is durable and de-buffered
    PartialRecordFailure, // some records applied; the rest stay buffered for retry
    FinalizeFailure,      // records applied, a finalize step failed, buffer restored
    RefusedByTrigger,     // a BEFORE trigger vetoed; nothing applied, nothing journaled
    AreaUnknown           // the work area could not be resolved; nothing attempted
};

struct Outcome {
    Verdict verdict{Verdict::NoChanges};
    int applied_ok{0};
    int applied_fail{0};

    bool complete()  const noexcept { return verdict == Verdict::Complete; }
    bool attempted() const noexcept { return verdict != Verdict::NoChanges; }

    // "Nothing is left unwritten." Complete wrote everything that was staged;
    // NoChanges had nothing staged to write. Both leave the table in the state
    // the caller asked for, which is the question a transaction needs answered.
    // Every other verdict leaves work undone.
    bool durable() const noexcept {
        return verdict == Verdict::Complete || verdict == Verdict::NoChanges;
    }
};

// One sentence naming what actually happened, for a caller that must report a
// refusal to a person. Never empty.
std::string describe(const Outcome& outcome);

// Commit the buffered changes of ONE area and report the verdict.
//
// This is the body a bare COMMIT runs, minus the argument parsing. It prints
// exactly what COMMIT prints and honours SET TALK the same way; the only
// difference is that the verdict comes back instead of being dropped.
void commit_area(xbase::DbArea& A, bool interactive_rebuild, Outcome& out);

}} // namespace cli::commit

// ---------------------------------------------------------------------------
// AIF-159 section 7.6 -- the ROLLBACK twin of the above.
//
// cmd_ROLLBACK had the identical blindness: it never consulted
// sql_transaction_state, so a native ROLLBACK DISCARDED THE BUFFER and left the
// SQL scope open. Same shape as the COMMIT half, and worse in one respect --
// COMMIT at least wrote the data before leaking the scope; ROLLBACK throws the
// user's staged work away and still leaves them inside a transaction they never
// opened.
//
// It could not be guarded in place. rollback_sql_transaction calls cmd_ROLLBACK
// DIRECTLY, so a guard on the command would refuse the SQL path itself. Hence
// the same split commit_area() got: the body lives here and the SQL path calls
// it, while the command wraps it behind the guard.
// ---------------------------------------------------------------------------
namespace cli { namespace rollback {

struct Outcome {
    std::size_t discarded_changes{0};
    int areas_touched{0};
};

// Discard the buffered changes of ONE area and report what was thrown away.
//
// This is the body a bare ROLLBACK runs, minus the argument parsing. It prints
// exactly what ROLLBACK prints; the only difference is that the counts come
// back instead of being dropped.
void rollback_area(xbase::DbArea& A, Outcome& out);

}} // namespace cli::rollback
