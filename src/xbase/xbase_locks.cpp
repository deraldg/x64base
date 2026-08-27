// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "xbase_locks.hpp"
#include "xbase.hpp"
#include "xbase/ramfs.hpp"

#include <filesystem>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <chrono>
#include <string>
#include <sstream>
#include <locale>   // AIF-116: imbue(classic) on the owner-string and sidecar writers

#ifdef _WIN32
  #include <windows.h>
  #include <lmcons.h>
#else
  #include <unistd.h>
  #include <sys/utsname.h>
  #include <signal.h>
  #include <cerrno>
#endif

namespace fs = std::filesystem;

namespace xbase::locks {

// ---------------- process/session owner --------------------------------------

static std::string make_owner_string() {
#ifdef _WIN32
    char cname[MAX_COMPUTERNAME_LENGTH + 1]{0};
    DWORD sz = MAX_COMPUTERNAME_LENGTH + 1;
    std::string host;
    if (::GetComputerNameA(cname, &sz)) host.assign(cname, sz); else host = "winhost";
    const unsigned long pid = static_cast<unsigned long>(::GetCurrentProcessId());
#else
    utsname u{};
    std::string host;
    if (::uname(&u) == 0) host = u.nodename; else host = "unixhost";
    const unsigned long pid = static_cast<unsigned long>(::getpid());
#endif

    const auto now = std::chrono::system_clock::now().time_since_epoch();
    const auto ms  = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();

    // AIF-116 / AIF-031: this string is an IDENTITY TOKEN that is parsed back,
    // not display text. It must never carry locale digit grouping -- a stray
    // "16,984" makes the pid unparseable and every live lock look stale.
    // Imbued here as defence in depth; the cause is fixed in
    // include/runtime/utf8_init.hpp.
    std::ostringstream os;
    os.imbue(std::locale::classic());
    os << host << ":" << pid << ":" << ms;
    return os.str();
}

// The process owner token. `id` is minted once and never changes. `member` is
// pushed in by the shell (see set_current_member) and may change during a
// session; it is attribution, never equality.
static Owner& mutable_current_owner() {
    static Owner g_owner{ make_owner_string(), std::string() };
    return g_owner;
}

const Owner& current_owner() { return mutable_current_owner(); }

void set_current_member(std::string member) {
    mutable_current_owner().member = std::move(member);
}

// ---------------- in-memory bookkeeping (this process only) -------------------

struct LockBook {
    bool table{false};
    std::unordered_set<std::uint64_t> recs;
};

static std::unordered_map<const DbArea*, LockBook>& book() {
    static std::unordered_map<const DbArea*, LockBook> g;
    return g;
}

// ---------------- paths -------------------------------------------------------

static std::string resolved_db_path(const DbArea& a) {
    return a.filename();
}

static std::string table_lock_path(const DbArea& a) {
    fs::path p = resolved_db_path(a);
    p += ".lock";
    return p.string();
}

static std::string record_lock_path(const DbArea& a, std::uint64_t recno) {
    fs::path p = resolved_db_path(a);
    p += ".lock.";
    p += std::to_string(recno);
    return p.string();
}

// ---------------- lock file metadata -----------------------------------------

struct LockMeta {
    std::string owner;
    unsigned long pid{0};
    long long ms{0};
    // AIF-116: distinguishes "the owner's pid was read cleanly" from "the pid
    // could not be determined". pid==0 cannot carry that distinction, because
    // is_pid_alive(0) is false and would make an unreadable owner look dead.
    bool pid_valid{false};
    std::string member;              // AIF-144 stage 1; empty means none recorded
    bool has_member{false};
};

// Trailing CR / stray whitespace tolerated; anything else is a parse failure.
static std::string trim_ascii_ws(std::string s) {
    const auto is_ws = [](char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };
    while (!s.empty() && is_ws(s.front())) s.erase(s.begin());
    while (!s.empty() && is_ws(s.back()))  s.pop_back();
    return s;
}

static bool read_lock_meta(const std::string& path, LockMeta& meta) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;

    std::string line;
    while (std::getline(f, line)) {
        if (line.rfind("owner=", 0) == 0) {
            meta.owner = line.substr(6);
        } else if (line.rfind("member=", 0) == 0) {
            // AIF-144 stage 1. An older writer emits no such line, and this
            // reader then leaves has_member false -- which is the honest
            // answer, not a degraded one. Conversely an OLDER READER skips this
            // line entirely, because the loop only recognises keys it knows:
            // the tolerate-unknown precedent (R130's posture KEY lines). So the
            // sidecar format needs no version bump in either direction.
            const std::string m = trim_ascii_ws(line.substr(7));
            if (!m.empty()) { meta.member = m; meta.has_member = true; }
        } else if (line.rfind("pid=", 0) == 0) {
            // AIF-116: parse STRICTLY, and require the WHOLE field to be
            // consumed. std::stoul takes the longest valid prefix and does
            // NOT throw on trailing junk, so a locale-grouped "pid=16,984"
            // silently yielded 16 -- a pid that is not alive, which sent
            // every live lock down the stale-recovery path and defeated
            // mutual exclusion. Leaving pid_valid false on failure is what
            // makes the caller fail closed instead of open.
            const std::string raw = trim_ascii_ws(line.substr(4));
            try {
                std::size_t consumed = 0;
                const unsigned long v = std::stoul(raw, &consumed);
                if (!raw.empty() && consumed == raw.size()) {
                    meta.pid       = v;
                    meta.pid_valid = true;
                }
            } catch (...) {
                // pid_valid stays false: owner is UNKNOWN, not dead.
            }
        } else if (line.rfind("ms=", 0) == 0) {
            try {
                meta.ms = std::stoll(line.substr(3));
            } catch (...) {
                meta.ms = 0;
            }
        }
    }

    return !meta.owner.empty();
}

static bool read_owner_from_file(const std::string& path, std::string& out_owner) {
    LockMeta meta;
    if (!read_lock_meta(path, meta)) {
        out_owner.clear();
        return false;
    }

    out_owner = meta.owner;
    return true;
}

static bool write_lock_file(const std::string& path, const Owner& owner, std::string* err) {
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) {
        if (err) *err = "cannot create lock";
        return false;
    }

    // AIF-116: the sidecar is a machine-read protocol file, not output. Its
    // numbers are parsed back by read_lock_meta and must be locale-immune.
    f.imbue(std::locale::classic());

#ifdef _WIN32
    const unsigned long pid = static_cast<unsigned long>(::GetCurrentProcessId());
#else
    const unsigned long pid = static_cast<unsigned long>(::getpid());
#endif

    const auto now = std::chrono::system_clock::now().time_since_epoch();
    const auto ms  = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();

    f << "DotTalk++ lock\n";
    f << "owner=" << owner.id << "\n";
    // Written ONLY when non-empty, so a reader can tell "no member recorded"
    // from "a member whose name is blank". R6 at the file format.
    if (!owner.member.empty()) f << "member=" << owner.member << "\n";
    f << "pid="   << pid      << "\n";
    f << "ms="    << ms       << "\n";
    f.flush();

    const bool ok = static_cast<bool>(f);
    if (!ok && err) *err = "write failed";
    return ok;
}

static bool force_remove(const std::string& path, std::string* err) {
    // In-memory tables (AIF-043 V3): a RAM table is process-local/single-area --
    // there is no OS lock file to touch, so locking is a no-op success.
    if (xbase::ramfs::is_virtual(path)) return true;
    std::error_code ec;
    fs::remove(path, ec);
    if (ec && fs::exists(path)) {
        if (err) *err = "force unlock failed";
        return false;
    }
    return true;
}

static bool is_pid_alive(unsigned long pid) {
    if (pid == 0) return false;

#ifdef _WIN32
    HANDLE h = ::OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, static_cast<DWORD>(pid));
    if (!h) return false;

    DWORD exit_code = 0;
    const BOOL ok = ::GetExitCodeProcess(h, &exit_code);
    ::CloseHandle(h);

    if (!ok) return false;
    return exit_code == STILL_ACTIVE;
#else
    const int rc = ::kill(static_cast<pid_t>(pid), 0);
    if (rc == 0) return true;
    if (errno == EPERM) return true;   // exists, but no permission
    return false;
#endif
}

// AIF-144 stage 1b. ONE PLACE DECIDES WHETHER A LOCK IS MINE.
//
// Four sites used to compare the recorded owner field against this process's
// token by hand -- remove_if_owned, create_or_validate_owned, and twice in the
// table-lock check inside try_lock_record. Four hand-written implementations of
// one rule, and nothing forced them to agree: unspell any single one and no
// test would notice.
//
// This comment deliberately DESCRIBES that comparison instead of quoting it, so
// a maintainer grepping for the old spelling to confirm none survive does not
// match the paragraph explaining that none survive. Three separate documents
// today were caught spelling the pattern they were warning about.
//
// It also left Owner::operator== with ZERO CALLERS in the whole tree, which is
// the AIF-079 shape (registered and unreachable) and made stage 1's stated
// decision -- "the member is deliberately outside operator==" -- a decision
// about an operator nobody invoked. The rule was real; it was enforced by four
// string comparisons rather than by the operator that claimed to express it.
//
// Today this is EXACTLY the liveness token, byte for byte what it replaced.
// Its value is that AIF-144 sec 7's member-aware refusal rule -- "only the
// principal may release across a member switch" -- now has ONE site to land in
// rather than four to be applied consistently across.
static bool lock_is_mine(const LockMeta& meta, const Owner& me) {
    return Owner{meta.owner, meta.member} == me;
}

static bool remove_if_owned(const std::string& path, const Owner& me, std::string* err) {
    if (xbase::ramfs::is_virtual(path)) return true;  // RAM table: no OS lock file
    if (!fs::exists(path)) return true;

    LockMeta meta;
    if (!read_lock_meta(path, meta)) {
        if (err) *err = "unknown owner";
        return false;
    }

    if (!lock_is_mine(meta, me)) {
        if (err) *err = "not lock owner";
        return false;
    }

    std::error_code ec;
    fs::remove(path, ec);
    if (ec && fs::exists(path)) {
        if (err) *err = "unlock failed";
        return false;
    }
    return true;
}

static bool create_or_validate_owned(const std::string& path, const Owner& me, std::string* err) {
    if (xbase::ramfs::is_virtual(path)) return true;  // RAM table: lock is a no-op success
    if (!fs::exists(path)) {
        return write_lock_file(path, me, err);
    }

    LockMeta meta;
    if (!read_lock_meta(path, meta)) {
        if (err) *err = "lock exists";
        return false;
    }

    // Re-entrant lock in same process/session.
    if (lock_is_mine(meta, me)) {
        return true;
    }

    // Stale lock: owner process is PROVABLY gone.
    // AIF-116: fail CLOSED. Only an owner whose pid was parsed cleanly may be
    // declared stale. An unreadable or malformed owner is presumed ALIVE and
    // its lock is respected. The old test treated "cannot tell" as "go ahead",
    // which is how a grouped pid turned every live lock into a free one.
    if (meta.pid_valid && !is_pid_alive(meta.pid)) {
        std::string ignored;
        if (!force_remove(path, &ignored)) {
            if (err) *err = "stale lock exists";
            return false;
        }
        return write_lock_file(path, me, err);
    }

    if (err) *err = "lock exists";
    return false;
}

// ---------------- Public API: Table ------------------------------------------

bool try_lock_table(DbArea& a, const Owner& me, std::string* err) {
    const std::string lp = table_lock_path(a);
    if (!create_or_validate_owned(lp, me, err)) return false;
    book()[&a].table = true;
    return true;
}

bool unlock_table(DbArea& a, const Owner& me, std::string* err) {
    const std::string lp = table_lock_path(a);
    const bool ok = remove_if_owned(lp, me, err);
    if (ok) book()[&a].table = false;
    return ok;
}

bool is_table_locked(const DbArea& a, std::string* owner_out) {
    const std::string lp = table_lock_path(a);
    if (!fs::exists(lp)) {
        if (owner_out) owner_out->clear();
        return false;
    }

    if (owner_out) {
        (void)read_owner_from_file(lp, *owner_out);
    }

    return true;
}

// Back-compat shims

bool try_lock_table(DbArea& a, std::string* err) {
    return try_lock_table(a, current_owner(), err);
}

void unlock_table(DbArea& a) {
    std::string ignored;
    (void)unlock_table(a, current_owner(), &ignored);
}

bool is_table_locked(const DbArea& a) {
    return fs::exists(table_lock_path(a));
}

// ---------------- Public API: Record -----------------------------------------

bool try_lock_record(DbArea& a, std::uint64_t recno, const Owner& me, std::string* err) {
    if (recno == 0) {
        if (err) *err = "bad recno";
        return false;
    }

    // If table is locked by someone else and still alive, deny.
    const std::string tlp = table_lock_path(a);
    if (fs::exists(tlp)) {
        LockMeta tmeta;
        if (read_lock_meta(tlp, tmeta)) {
            // AIF-116: deny when the foreign owner is alive OR UNKNOWN.
            // With an unparseable pid the old test evaluated is_pid_alive(0)
            // == false and fell straight through to the reclaim below, so a
            // malformed table lock granted a record lock underneath it.
            if (!lock_is_mine(tmeta, me) && (!tmeta.pid_valid || is_pid_alive(tmeta.pid))) {
                if (err) *err = "table locked";
                return false;
            }

            // Stale table lock cleanup -- only when PROVABLY dead.
            if (!lock_is_mine(tmeta, me) && tmeta.pid_valid && !is_pid_alive(tmeta.pid)) {
                std::string ignored;
                (void)force_remove(tlp, &ignored);
            }
        } else {
            if (err) *err = "table locked";
            return false;
        }
    }

    const std::string rp = record_lock_path(a, recno);
    if (!create_or_validate_owned(rp, me, err)) return false;

    book()[&a].recs.insert(recno);
    return true;
}

bool unlock_record(DbArea& a, std::uint64_t recno, const Owner& me, std::string* err) {
    if (recno == 0) {
        if (err) *err = "bad recno";
        return false;
    }

    const std::string rp = record_lock_path(a, recno);
    const bool ok = remove_if_owned(rp, me, err);
    if (ok) book()[&a].recs.erase(recno);
    return ok;
}

// -------- who holds it (AIF-144 stage 1) -------------------------------------
static bool holder_from_file(const std::string& path, LockHolder* out) {
    LockMeta meta;
    if (!read_lock_meta(path, meta)) return false;
    if (out) {
        out->owner_id   = meta.owner;
        out->member     = meta.member;
        out->has_member = meta.has_member;
    }
    return true;
}

bool is_record_locked(const DbArea& a, std::uint64_t recno, std::string* owner_out) {
    if (recno == 0) {
        if (owner_out) owner_out->clear();
        return false;
    }

    const std::string rp = record_lock_path(a, recno);
    if (!fs::exists(rp)) {
        if (owner_out) owner_out->clear();
        return false;
    }

    if (owner_out) {
        (void)read_owner_from_file(rp, *owner_out);
    }

    return true;
}

// AIF-144 stage 1. These mirror the two predicates above exactly -- same
// existence guard, same recno==0 rejection -- and differ only in reading the
// member alongside the owner id. Deliberately NOT folded into the existing
// signatures: `is_*_locked(..., std::string*)` has callers throughout the
// tree, and widening a predicate everyone already uses to answer a question
// only one caller asks is how a small addition becomes a sweep.
bool table_lock_holder(const DbArea& a, LockHolder* out) {
    if (out) *out = LockHolder{};
    const std::string lp = table_lock_path(a);
    if (!fs::exists(lp)) return false;
    (void)holder_from_file(lp, out);
    return true;
}

bool record_lock_holder(const DbArea& a, std::uint64_t recno, LockHolder* out) {
    if (out) *out = LockHolder{};
    if (recno == 0) return false;
    const std::string rp = record_lock_path(a, recno);
    if (!fs::exists(rp)) return false;
    (void)holder_from_file(rp, out);
    return true;
}

// Back-compat shims

bool try_lock_record(DbArea& a, std::uint64_t recno, std::string* err) {
    return try_lock_record(a, recno, current_owner(), err);
}

void unlock_record(DbArea& a, std::uint64_t recno) {
    std::string ignored;
    (void)unlock_record(a, recno, current_owner(), &ignored);
}

bool is_record_locked(const DbArea& a, std::uint64_t recno) {
    return fs::exists(record_lock_path(a, recno));
}

// ---------------- Admin -------------------------------------------------------

bool force_unlock_table(DbArea& a, std::string* err) {
    const std::string lp = table_lock_path(a);
    const bool ok = force_remove(lp, err);
    if (ok) book()[&a].table = false;
    return ok;
}

bool force_unlock_record(DbArea& a, std::uint64_t recno, std::string* err) {
    if (recno == 0) {
        if (err) *err = "bad recno";
        return false;
    }

    const std::string rp = record_lock_path(a, recno);
    const bool ok = force_remove(rp, err);
    if (ok) book()[&a].recs.erase(recno);
    return ok;
}

// ---------------- Cleanup -----------------------------------------------------

void release_held(DbArea& a) {
    const Owner& me = current_owner();
    auto it = book().find(&a);
    if (it == book().end()) return;

    for (auto r : it->second.recs) {
        std::string ignored;
        (void)unlock_record(a, r, me, &ignored);
    }
    it->second.recs.clear();

    if (it->second.table) {
        std::string ignored;
        (void)unlock_table(a, me, &ignored);
        it->second.table = false;
    }
}

} // namespace xbase::locks