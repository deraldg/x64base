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

bool ensure_catalog(const fs::path& path, std::string* err) {
    std::error_code ec;
    if (fs::exists(path, ec)) return true;

    fs::create_directories(path.parent_path(), ec);
    if (ec) {
        if (err) *err = "cannot create the SYS directory: " + ec.message();
        return false;
    }

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

    std::string cerr;
    if (!xbase::dbf_create::create_dbf(path.string(), f,
                                       xbase::dbf_create::Flavor::X64, cerr)) {
        if (err) *err = "cannot create the group log: " + cerr;
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

    // A LINEAR SCAN, AND THE DESIGN SAYS THIS IS NOT GOOD ENOUGH FOR LONG.
    // The catalog is append-only and never packed, so this is O(rows) per member
    // table per USE and grows without bound. An index on GRP_KEY is OWED before
    // this carries real traffic; it is left out of the first cut so the decision
    // path can be measured and graded without index machinery in the way.
    bool found = false;
    const std::uint64_t total = a.recCount64();
    for (std::uint64_t rn = 1; rn <= total && !found; ++rn) {
        if (!a.gotoRec64(rn) || !a.readCurrent()) continue;
        if (trim(a.get(F_GRP_KEY)) == want) found = true;
    }
    a.close();
    return found;
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
