// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: the multi-area commit group log
// project: project.x64base.runtime
// lane: AIF-160
// owner: member.derald
// status: experimental

#include "cli/group_log.hpp"

#include "common/path_state.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/durable.hpp"
#include "xbase_locks.hpp"

#include <atomic>
#include <cctype>
#include <ctime>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;

namespace dottalk::group {
namespace {

// FIVE COLUMNS, AND THE COUNT IS THE POINT. Every column here sits on a durable
// write that gates a commit, so a column recovery does not read is latency paid
// by every grouped transaction forever. WORKSPACES.dbf carries twenty-odd; this
// carries what the decision needs and what an operator needs to read it.
//
// Field names are all ten bytes or fewer, so the x64 descriptor token equals the
// logical name and no name planning is required. Stated because the workspaces
// catalog DOES plan (it has names past ten), and the difference is a property of
// these names rather than a shortcut.
constexpr int F_GRP_KEY    = 1;   // C(64) THE key. Recovery matches this whole.
constexpr int F_DECIDED_AT = 2;   // C(19) stamp, never the authority
constexpr int F_MEMBERS    = 3;   // N(4)  areas the group spanned
constexpr int F_AUTHOR     = 4;   // C(48) attribution, as every catalog carries
constexpr int F_HOST       = 5;   // C(48) split out of the key for READING only

// The members table: two columns and no more. It answers exactly one question
// -- which tables did this group span -- and every column that is not part of
// that answer is a column retirement would have to skip.
constexpr int M_GRP_KEY    = 1;   // C(64) the group, matched whole
constexpr int M_MEMBER     = 2;   // C(180) the member table path, as opened

std::string trim(std::string s) {
    const auto sp = [](char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; };
    while (!s.empty() && sp(s.front())) s.erase(s.begin());
    while (!s.empty() && sp(s.back()))  s.pop_back();
    return s;
}

std::string stamp_now() {
    const std::time_t tt = std::time(nullptr);
    std::tm tm_buf{};
#if defined(_WIN32)
    if (localtime_s(&tm_buf, &tt) != 0) return {};
#else
    if (localtime_r(&tt, &tm_buf) == nullptr) return {};
#endif
    std::ostringstream oss;
    oss << std::put_time(&tm_buf, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

// The owner token is "host:pid:nonce"; HOST is everything before the first
// colon. It is a CONVENIENCE COLUMN and never a discriminator -- recovery
// matches the whole GRP_KEY and nothing else. A split-out column that recovery
// consulted would be a second spelling of one fact.
std::string host_of(const std::string& owner_id) {
    const auto colon = owner_id.find(':');
    return colon == std::string::npos ? owner_id : owner_id.substr(0, colon);
}

// One creator for both SYS tables, because they differ only in their columns.
// A second hand-written create would be a second place for the flavor ruling and
// the directory-sync note to drift apart.
bool ensure_table(const fs::path& path,
                  const std::vector<xbase::dbf_create::FieldSpec>& fields,
                  const char* what,
                  std::string* err) {
    std::error_code ec;
    if (fs::exists(path, ec)) return true;

    fs::create_directories(path.parent_path(), ec);
    if (ec) {
        if (err) *err = "cannot create the SYS directory: " + ec.message();
        return false;
    }

    // x64 BY THE SYS RULING (owner, 2026-09-11): every table under the SYS slot
    // is x64 unless a stated reason says otherwise. The default is declared in
    // the slot's own doctrine in common/path_state.hpp rather than re-argued
    // here. Nothing about these schemas requires it -- 32 bits is four billion
    // rows, every field name is under ten bytes, and no VFP feature is used.
    std::string cerr;
    if (!xbase::dbf_create::create_dbf(path.string(), fields,
                                       xbase::dbf_create::Flavor::X64, cerr)) {
        if (err) *err = std::string("cannot create the ") + what + ": " + cerr;
        return false;
    }

    // THE DIRECTORY SYNC IS REAL AND IS PAID EXACTLY ONCE, HERE. durable_sync
    // syncs a file's CONTENTS and not its directory entry, so a freshly CREATED
    // file can be lost by a crash the contents sync survived (R136's class,
    // still open in this tree). Every later write APPENDS to a file that exists,
    // so the question is answered at creation and never again -- which is the
    // argument for a DBF catalog over a flat log, whose every span creates a new
    // file and would owe the directory answer on the critical path each time.
    //
    // NOT CLAIMED: that this call answers it. durable_sync does the CONTENTS,
    // and the directory entry is UNADDRESSED here as it is everywhere else in
    // this tree. Named so the hole is inherited knowingly rather than assumed
    // closed.
    std::string serr;
    (void)xbase::durable_sync(path.string(), &serr);
    return true;
}

bool ensure_catalog(const fs::path& path, std::string* err) {
    std::vector<xbase::dbf_create::FieldSpec> f;
    auto C = [&](const char* n, std::uint32_t len) {
        xbase::dbf_create::FieldSpec s; s.name = n; s.type = 'C'; s.len = len; s.dec = 0;
        f.push_back(s);
    };
    auto N = [&](const char* n, std::uint32_t len) {
        xbase::dbf_create::FieldSpec s; s.name = n; s.type = 'N'; s.len = len; s.dec = 0;
        f.push_back(s);
    };
    C("GRP_KEY", 64);
    C("DECIDED_AT", 19);
    N("MEMBERS", 4);
    C("AUTHOR", 48);
    C("HOST", 48);
    return ensure_table(path, f, "group log", err);
}

bool ensure_members(const fs::path& path, std::string* err) {
    std::vector<xbase::dbf_create::FieldSpec> f;
    auto C = [&](const char* n, std::uint32_t len) {
        xbase::dbf_create::FieldSpec s; s.name = n; s.type = 'C'; s.len = len; s.dec = 0;
        f.push_back(s);
    };
    C("GRP_KEY", 64);
    // 180 matches DBF_ROOT in the workspaces catalog. A member is named by the
    // path it was OPENED as, because that is the string a `.tbj` sidecar sits
    // beside and therefore the only spelling retirement can check.
    C("MEMBER", 180);
    return ensure_table(path, f, "group members table", err);
}

bool open_catalog(xbase::DbArea& a, std::string* err) {
    const std::string p = catalog_path();
    if (p.empty()) {
        if (err) *err = "the SYS path slot is not set";
        return false;
    }
    if (!ensure_catalog(fs::path(p), err)) return false;
    try { a.open(p); }
    catch (const std::exception& e) {
        if (err) *err = std::string("cannot open the group log: ") + e.what();
        return false;
    }
    catch (...) { if (err) *err = "cannot open the group log"; return false; }
    return a.isOpen();
}

} // namespace

std::string catalog_path() {
    fs::path sys;
    try { sys = dottalk::paths::get_slot(dottalk::paths::Slot::SYS); }
    catch (...) { return {}; }
    if (sys.empty()) return {};
    return (sys / "GROUPS.dbf").string();
}

std::string mint_group_key() {
    static std::atomic<unsigned long long> counter{0};
    const unsigned long long n = counter.fetch_add(1) + 1;
    return xbase::locks::current_owner().id + "#" + std::to_string(n);
}

bool decide_committed(const std::string& key, int members, std::string* err) {
    if (trim(key).empty()) {
        if (err) *err = "an empty group key cannot be decided";
        return false;
    }

    xbase::DbArea a;
    if (!open_catalog(a, err)) return false;

    const auto& owner = xbase::locks::current_owner();

    bool ok = a.appendBlank() && a.readCurrent();
    if (ok) {
        ok = a.set(F_GRP_KEY, key)
          && a.set(F_DECIDED_AT, stamp_now())
          && a.set(F_MEMBERS, std::to_string(members))
          && a.set(F_AUTHOR, owner.member)
          && a.set(F_HOST, host_of(owner.id));
    }
    if (ok) ok = a.writeCurrent();

    const std::string path = a.filename();
    a.close();

    if (!ok) {
        if (err) *err = "the decision row did not write";
        return false;
    }

    // THE ONE DURABLE WRITE. Until this returns the group has NOT committed, and
    // a caller that treats a failure here as anything other than "abort the
    // group" has converted a refused commit into a silent partial one.
    std::string serr;
    if (!xbase::durable_sync(path, &serr)) {
        if (err) *err = "the decision row was written but NOT made durable (" + serr
                      + "); this group did NOT commit";
        return false;
    }
    return true;
}

bool is_committed(const std::string& key) {
    const std::string want = trim(key);
    if (want.empty()) return false;

    // NO CATALOG MEANS NO DECISION EVER LANDED, which is presumed abort and the
    // correct answer. ensure_catalog is deliberately NOT called from the read
    // path: a lookup must never CREATE the authority it is asking.
    const std::string p = catalog_path();
    std::error_code ec;
    if (p.empty() || !fs::exists(p, ec)) return false;

    xbase::DbArea a;
    try { a.open(p); } catch (...) { return false; }
    if (!a.isOpen()) return false;

    // A LINEAR SCAN, AND IT IS NOT ON THE PATH THIS COMMENT USED TO CLAIM.
    //
    // It said "O(rows) per member table per USE" and that an index on GRP_KEY
    // was OWED. The first half is false and the second followed from it.
    // Recovery runs at every USE; recovery REACHES THIS FUNCTION only when a
    // member journal carries a P prepare marker and no local C -- nothing else
    // in recover_table_buffer_journal can call it.
    //
    // And a P span surviving to recovery is a CRASH ARTIFACT. The committing
    // process discards the journals of a group it knows failed (the eager-abort
    // ruling), and a healthy commit removes its own journal in
    // journal_note_commit. So this is a per-crash cost, once per member table
    // of the group that was in flight -- not a per-open one.
    //
    // MEASURED: 12.2 us/row, so 100,000 rows is about 1.2 seconds, once, on a
    // machine that has already failed. The index is DEFERRED rather than owed.
    // If a measurement ever asks for one, the catalog is a DBF and cdx ships;
    // nothing here blocks it. Corrected 2026-09-11, owner accepted.
    bool found = false;
    const std::uint64_t total = a.recCount64();
    for (std::uint64_t rn = 1; rn <= total && !found; ++rn) {
        if (!a.gotoRec64(rn) || !a.readCurrent()) continue;
        if (trim(a.get(F_GRP_KEY)) == want) found = true;
    }
    a.close();
    return found;
}

std::string members_path() {
    fs::path sys;
    try { sys = dottalk::paths::get_slot(dottalk::paths::Slot::SYS); }
    catch (...) { return {}; }
    if (sys.empty()) return {};
    return (sys / "GROUPMEM.dbf").string();
}

bool record_members(const std::string& key,
                    const std::vector<std::string>& member_paths,
                    std::string* err) {
    if (trim(key).empty()) {
        if (err) *err = "an empty group key has no members to record";
        return false;
    }
    if (member_paths.empty()) return true;   // nothing to say; not an error

    const std::string p = members_path();
    if (p.empty()) {
        if (err) *err = "the SYS path slot is not set";
        return false;
    }
    if (!ensure_members(fs::path(p), err)) return false;

    xbase::DbArea a;
    try { a.open(p); }
    catch (const std::exception& e) {
        if (err) *err = std::string("cannot open the group members table: ") + e.what();
        return false;
    }
    catch (...) { if (err) *err = "cannot open the group members table"; return false; }
    if (!a.isOpen()) { if (err) *err = "the group members table would not open"; return false; }

    bool ok = true;
    for (const auto& m : member_paths) {
        if (!a.appendBlank() || !a.readCurrent()) { ok = false; break; }
        if (!a.set(M_GRP_KEY, key) || !a.set(M_MEMBER, m) || !a.writeCurrent()) {
            ok = false;
            break;
        }
    }
    a.close();

    // DELIBERATELY NO durable_sync. This is written at PREPARE, off the critical
    // path, and losing it is SAFE BY CONSTRUCTION: retirement that finds no
    // member rows cannot establish that a group has settled, so it keeps the
    // decision row. Syncing here would buy nothing and would put an fsync on a
    // path whose whole value is that it costs the decision nothing.
    if (!ok && err) *err = "a member row did not write";
    return ok;
}

std::vector<std::string> members_of(const std::string& key) {
    std::vector<std::string> out;
    const std::string want = trim(key);
    if (want.empty()) return out;

    // As with is_committed: the read path must NEVER create the table it is
    // asking. A members table minted by the asking would answer "no members" to
    // everything, and retirement reads "no members" as KEEP -- so this would
    // fail safe today and become a silent trap the moment that reading changes.
    const std::string p = members_path();
    std::error_code ec;
    if (p.empty() || !fs::exists(p, ec)) return out;

    xbase::DbArea a;
    try { a.open(p); } catch (...) { return out; }
    if (!a.isOpen()) return out;

    // Linear, and owed the same index GRP_KEY is owed on the decision table.
    const std::uint64_t total = a.recCount64();
    for (std::uint64_t rn = 1; rn <= total; ++rn) {
        if (!a.gotoRec64(rn) || !a.readCurrent()) continue;
        if (trim(a.get(M_GRP_KEY)) == want) out.push_back(trim(a.get(M_MEMBER)));
    }
    a.close();
    return out;
}

long long decision_count() {
    const std::string p = catalog_path();
    std::error_code ec;
    if (p.empty() || !fs::exists(p, ec)) return 0;

    xbase::DbArea a;
    try { a.open(p); } catch (...) { return 0; }
    if (!a.isOpen()) return 0;
    const long long n = static_cast<long long>(a.recCount64());
    a.close();
    return n;
}

} // namespace dottalk::group
