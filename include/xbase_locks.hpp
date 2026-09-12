// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <string>
#include <cstdint>

namespace xbase { class DbArea; }

namespace xbase::locks {

// -------- Owner identity -----------------------------------------------------
// TWO FIELDS, AND ONLY ONE OF THEM IS COMPARED. AIF-144 stage 1.
//
// `id` is the LIVENESS token -- "host:pid:ms", minted once per process. It is
// what mutual exclusion and stale-lock reclamation are built on, and it is the
// ONLY thing operator== looks at. Classic xBase holds locks per workstation and
// that remains correct here; AIF-116/AIF-031 hardened the parse of this token
// after locale digit grouping made every live lock look stale.
//
// `member` is ATTRIBUTION and is NEVER compared. It answers "who is
// responsible", which the lock layer previously could not answer at all: LOCK
// WHO printed a pid at a person who asked who. Measured 2026-08-27, an AI
// member the RBAC layer annotates "must ask for limited permission" released a
// lock taken by the OWNER, and nothing could see it, because the member was
// nowhere in the record.
//
// WHY NOT FOLD IT INTO THE COMPARISON. Making equality mean "same member AND
// same process" sounds stricter and sets a trap: sudo to another member, take a
// lock, sudo back, and the principal can no longer release it -- deadlock by
// design. A refusal rule ("only the principal may release across a member
// switch") belongs ON TOP of this, as policy, not inside identity. Recording
// the member first is what makes that rule expressible at all.
struct Owner {
    std::string id;            // liveness token, e.g. "host:pid:nonce"
    std::string member;        // attribution only -- NEVER part of equality
    bool operator==(const Owner& o) const noexcept { return id == o.id; }
    bool operator!=(const Owner& o) const noexcept { return id != o.id; }
};

// Returns the process/session owner token (singleton per process).
const Owner& current_owner();

// Set the member recorded on this process's owner token.
//
// THE ENGINE DOES NOT RESOLVE MEMBERS AND MUST NOT LEARN HOW. This translation
// unit includes no identity header; the shell pushes the value in. That keeps
// the dependency pointing one way (identity -> xbase) and leaves `xbase`
// linkable by consumers that have no identity subsystem at all.
//
// KNOWN, AND DELIBERATE: this mutates a process-global, which is the same shape
// as the identity layer's own `g_acting`. It is not made worse here and it is
// not made better -- AIF-144 stage 2 is where identity acquires a SESSION scope
// and both stop being process globals. Recorded rather than discovered later.
//
// A SECOND KNOWN GAP, NAMED BECAUSE IT IS VISIBLE IN OUTPUT. The identity
// layer's acting member is initialised STATICALLY to the anonymous member and
// only reaches here when something CHANGES it -- login, logout, USER AS. So a
// session that takes a lock before any of those has happened records NO member,
// and LOCK WHO says "(no member recorded)".
//
// That is TRUE OF THE FILE and is not a lie; it just understates what the
// session knew. Closing it properly means either a startup contract nobody has
// today (identity bootstraps lazily, on first access) or inverting this to a
// provider the engine CALLS at lock time. The provider is the better design and
// is deliberately NOT taken here: it wants a place to be installed, and that
// place is the session object AIF-144 stage 2 creates. Fixing it now would mean
// inventing an init hook that stage 2 would immediately replace.
void set_current_member(std::string member);

// -------- Reading who holds a lock -------------------------------------------
// R6: "the writer recorded no member" and "the member is an empty string" are
// different facts and must not share a representation. `has_member` is the
// discriminator; an empty member is never written, so has_member==true always
// carries a real name. A lock file written by a build that predates AIF-144
// stage 1 yields has_member==false, which is CORRECT rather than degraded.
struct LockHolder {
    std::string owner_id;
    std::string member;
    bool        has_member{false};
};

bool table_lock_holder (const DbArea& a, LockHolder* out);
bool record_lock_holder(const DbArea& a, std::uint64_t recno, LockHolder* out);

// -------- Table locks --------------------------------------------------------
// New owner-aware API:
bool try_lock_table(DbArea& a, const Owner& owner, std::string* err = nullptr);
bool unlock_table   (DbArea& a, const Owner& owner, std::string* err = nullptr);
bool is_table_locked(const DbArea& a, std::string* owner_out); // owner string if locked

// Back-compat shims (behave as "current_owner"):
bool try_lock_table(DbArea& a, std::string* err = nullptr);
void unlock_table   (DbArea& a);                 // best-effort: ignores failures
bool is_table_locked(const DbArea& a);           // no owner info

// -------- Record locks -------------------------------------------------------
// Record numbers are 64-bit (RECNO64 lane). Widening conversions from the
// classic 32-bit callers are implicit and lossless.
// New owner-aware API:
bool try_lock_record(DbArea& a, std::uint64_t recno, const Owner& owner, std::string* err = nullptr);
bool unlock_record  (DbArea& a, std::uint64_t recno, const Owner& owner, std::string* err = nullptr);
bool is_record_locked(const DbArea& a, std::uint64_t recno, std::string* owner_out); // owner string if locked

// Back-compat shims:
bool try_lock_record(DbArea& a, std::uint64_t recno, std::string* err = nullptr);
void unlock_record  (DbArea& a, std::uint64_t recno); // best-effort
bool is_record_locked(const DbArea& a, std::uint64_t recno);

// -------- Admin / recovery (optional) ---------------------------------------
// Force unlock ignores ownership (use sparingly / logged by caller).
bool force_unlock_table (DbArea& a, std::string* err = nullptr);
bool force_unlock_record(DbArea& a, std::uint64_t recno, std::string* err = nullptr);

// Cleanup any locks created by this process for this area (best-effort)
void release_held(DbArea& a);

} // namespace xbase::locks
