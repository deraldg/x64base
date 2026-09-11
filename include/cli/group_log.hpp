// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: the multi-area commit group log
// project: project.x64base.runtime
// lane: AIF-160
// owner: member.derald
// status: experimental

#pragma once

#include <string>
#include <vector>

// THE GROUP LOG: ONE ROW IS THE DECISION (AIF-160).
//
// A transaction spanning N tables cannot be made atomic by N independent
// commits: each area's journal recovers correctly for its own table, and a crash
// between them leaves every part consistent and the whole wrong. The missing
// piece is ONE durable record, outside every area's journal, saying that a named
// group committed. The instant that record is durable is the instant the group
// is true.
//
// ONLY COMMITTED GROUPS ARE WRITTEN. There is no abort row and that is the
// design: recovery is PRESUMED ABORT, so an absent key already means "did not
// commit". An abort row would put a durable write on the path that is ALREADY
// FAILING, to record what the absence of a row says better.
//
// NOT RECORDING THE ABORT IS NOT THE SAME AS DOING NOTHING. The committing
// process holds every member open and knows the group failed, so it PERFORMS the
// abort -- releases the member locks, discards the prepared spans -- rather than
// leaving them for a future USE to notice. Presumed abort stays as the RECOVERY
// rule, because a process killed between prepare and decide performs nothing.
// It is a crash handler, not the normal path.
//
// IT LIVES UNDER THE SYS SLOT, which is the whole reason that slot exists:
// engine state that cannot be rebuilt from anything and is never swept. Deleting
// a row here SILENTLY LOSES A COMMITTED TRANSACTION and nothing detects it --
// every other loss in this tree announces itself. Tables under SYS are refused
// the table buffer and skipped by journal recovery
// (`dottalk::table::is_engine_state_file`), which is what stops the group log
// from ever needing to be recovered by consulting itself.
//
// THERE IS DELIBERATELY NO PACK AND NO RETENTION VERB YET. A row is dead only
// once EVERY member's journal has been applied, and no single process can know
// that -- members may be recovered by different processes at different times,
// which is the reason the log exists. A retention rule is OWED and needs a fact
// nobody can currently establish.
namespace dottalk::group {

// The committing process's key for one group: `<current_owner().id>#<n>`.
//
// REUSES the engine's existing process identity (`xbase::locks::current_owner`,
// "host:pid:nonce") rather than minting a second spelling of the same fact. The
// owner token is a per-process singleton, so a counter is appended for
// uniqueness WITHIN the process; the token supplies uniqueness across processes
// with no coordination and no read before the write.
std::string mint_group_key();

// Where the catalog lives. Under the SYS slot; empty if that slot is unset.
std::string catalog_path();

// Record that `key` COMMITTED, durably. Returns false if the row or the durable
// sync did not land -- in which case the group did NOT commit and the caller
// must abort it. This is the single point of no return in a group commit.
bool decide_committed(const std::string& key, int members, std::string* err);

// Did `key` commit? The recovery question, asked once per member table at USE.
// FALSE for an unknown key, which is presumed abort and is the common answer.
bool is_committed(const std::string& key);

// How many decision rows the catalog holds. For arms and for an operator; no
// part of recovery reads it.
long long decision_count();

// ---------------------------------------------------------------------------
// THE MEMBERS TABLE, WHICH EXISTS SO THE DECISION ROW CAN EVER BE RETIRED.
//
// A group row is needed only while some member still carries a `P` span, and a
// `P` span lives from PREPARE to apply-complete -- MILLISECONDS for a healthy
// commit. Every long-lived row is the residue of a CRASH. Retirement therefore
// needs two facts: that the owning process is provably dead, and that every
// member has settled. The first is in GRP_KEY already; the second is this.
//
// A SEPARATE TABLE AND NOT A MEMO ON THE DECISION ROW. A memo would make the
// decision a TWO-FILE write, and cmd_workspace.cpp:3927 already puts the
// memo-payload-plus-row pair in "the class that needs write-ahead intent, and
// no journal exists". The decision staying ONE atomic append is the whole
// design; nothing is allowed to cost that.
//
// WRITTEN DURING PREPARE, AND DELIBERATELY NOT SYNCED. It is off the critical
// path, so it costs the decision nothing. And losing it is SAFE BY
// CONSTRUCTION: with no member rows, retirement cannot establish that a group
// has settled, so it keeps the decision row. The failure direction is the
// conservative one without anything having to choose it.
//
// RETIREMENT ITSELF IS NOT BUILT. It waits on the process-creation-time test
// that FINDING_THE_LOCK_RECORDS_A_STRONG_KEY_AND_ASKS_LIVENESS_WITH_A_WEAK_ONE
// describes and explicitly does not propose. Retention must ask the STRONG key
// -- the whole owner token -- because a bare pid is recycled, and that finding
// measured the permanent wedge that follows from asking the weak one. Here the
// asymmetry is sharper: a row wrongly kept is wasted bytes, a row wrongly
// retired is a committed transaction discarded in silence.

// Where the members table lives. Under SYS beside the group log; empty if that
// slot is unset.
std::string members_path();

// Record the member tables a group spans. Called at PREPARE, before any
// decision. Appending the same key twice appends rows twice -- this is a log,
// not a set, and nothing here reads it back during a commit.
bool record_members(const std::string& key,
                    const std::vector<std::string>& member_paths,
                    std::string* err);

// The member tables recorded for a group, in the order they were written.
// EMPTY for an unknown key, which retirement must read as "cannot establish
// that this group settled" and therefore as KEEP -- never as "no members".
std::vector<std::string> members_of(const std::string& key);

} // namespace dottalk::group
