// @dottalk.file v1
// path: src/bbs/bbs_store.cpp
// subsystem: bbs
// layer: engine-core
// owns: 
// project: project.x64base.runtime
// status: supported
// provenance: prov://src/bbs/bbs_store.cpp

// bbs_store.cpp -- DBF-backed store for the AI-BBS board (M1).
// Mirrors src/identity/identity_dbf_store.cpp idioms (RowW/RowR, create_dbf X64,
// 1-based DbArea slots vs 0-based findFieldCI, string-boundary encoding).
#include "bbs/bbs_store.hpp"
#include "bbs/bbs_schema.hpp"

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_name_policy.hpp"
#include "xbase/fields.hpp"
#include "xbase_locks.hpp"
#include "common/path_state.hpp"

#include <ctime>
#include <cstdlib>
#include <filesystem>
#include <system_error>

namespace fs = std::filesystem;

namespace dottalk::bbs {
namespace {

using schema::Table;

std::string join(const std::string& dir, const char* table) {
    return (fs::path(dir) / (std::string(table) + ".dbf")).string();
}
std::string s_u64(std::uint64_t v) { return std::to_string(v); }
std::string s_int(int v)           { return std::to_string(v); }
std::uint64_t now_epoch()          { return static_cast<std::uint64_t>(std::time(nullptr)); }

// Row writer over a freshly appended record.
struct RowW {
    xbase::DbArea& a; std::string& err; bool ok = true;
    void set(const char* col, const std::string& v) {
        if (!ok) return;
        int i = fields::findFieldCI(a, col);   // 0-based; -1 = missing
        if (i < 0) { ok = false; err = std::string("bbs save: missing column ") + col; return; }
        a.set(i + 1, v);                              // DbArea slots are 1-based
    }
};
// Row reader over the current record.
struct RowR {
    const xbase::DbArea& a;
    std::string str(const char* col) const {
        int i = fields::findFieldCI(a, col);
        return i >= 0 ? a.get(i + 1) : std::string();
    }
    std::uint64_t u64(const char* col) const {
        std::string v = str(col);
        return v.empty() ? 0ULL : std::strtoull(v.c_str(), nullptr, 10);
    }
    int i(const char* col) const { return static_cast<int>(u64(col)); }
};

bool create_table(const std::string& dir, const Table& t, std::string& err) {
    const std::string path = join(dir, t.name);
    std::error_code ec;
    fs::remove(path, ec);
    fs::remove(fs::path(path).replace_extension(".dbt"), ec);
    fs::remove(fs::path(path).replace_extension(".fpt"), ec);
    std::vector<xbase::dbf_create::FieldSpec> fields = t.fields;
    std::vector<std::string> names; names.reserve(fields.size());
    for (const auto& f : fields) names.push_back(f.name);
    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);
    for (std::size_t k = 0; k < fields.size() && k < plans.size(); ++k)
        fields[k].descriptor_name = plans[k].descriptor_name;
    return xbase::dbf_create::create_dbf(path, fields, xbase::dbf_create::Flavor::X64, err);
}

bool open_table(const std::string& dir, const char* name, xbase::DbArea& a, std::string& err) {
    try { a.open(join(dir, name)); return true; }
    catch (const std::exception& e) { err = std::string("bbs: cannot open ") + name + ": " + e.what(); return false; }
}

// RAII whole-table lock for a write op. Uses the engine's cooperative FLOCK (cross-process,
// pid-stamped, stale-owner recovering) so dottalkpp and dottalk_bbsd can append to the shared
// board store concurrently and be serialized by the engine, not by convention. Appends grow the
// record-count header, so a whole-table lock (not a per-record lock) is the correct granularity.
// Release happens in the destructor while the area is still open (table_lock_path uses filename()).
struct TableLock {
    xbase::DbArea& a; bool held = false;
    TableLock(xbase::DbArea& area, std::string& err) : a(area) {
        std::string lerr;
        held = xbase::locks::try_lock_table(a, &lerr);
        if (!held && err.empty())
            err = "bbs: table busy (locked by another process)" + (lerr.empty() ? std::string() : ": " + lerr);
    }
    ~TableLock() { if (held) xbase::locks::unlock_table(a); }
    explicit operator bool() const { return held; }
    TableLock(const TableLock&) = delete;
    TableLock& operator=(const TableLock&) = delete;
};

// max(ID)+1 over a table; 1 if empty. Table must exist.
std::uint64_t next_id(const std::string& dir, const char* name, std::string& err) {
    xbase::DbArea a;
    if (!open_table(dir, name, a, err)) return 0;
    std::uint64_t mx = 0, n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a}; mx = std::max(mx, r.u64("ID")); }
    a.close();
    return mx + 1;
}

// Locate the 1-based record whose <idcol> == target; 0 if not found.
std::uint64_t find_rec(xbase::DbArea& a, const char* idcol, std::uint64_t target) {
    std::uint64_t n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) {
        if (!a.gotoRec64(i)) continue;
        RowR r{a};
        if (r.u64(idcol) == target) return i;
    }
    return 0;
}

std::uint64_t board_id_for(const std::string& dir, const std::string& board_key, std::string& err) {
    xbase::DbArea a;
    if (!open_table(dir, "SYSBOARD", a, err)) return 0;
    std::uint64_t id = 0, n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a}; if (r.str("BKEY") == board_key) { id = r.u64("ID"); break; } }
    a.close();
    return id;
}

void seed_board(xbase::DbArea& a, std::string& err, std::uint64_t id, const char* bkey,
                const char* name, int kind, const char* postperm) {
    a.appendBlank(); RowW w{a, err};
    w.set("ID", s_u64(id)); w.set("BKEY", bkey); w.set("NAME", name); w.set("KIND", s_int(kind));
    w.set("POSTPERM", postperm); w.set("STATUS", "0");
    w.set("VFROM", s_u64(now_epoch())); w.set("VTHRU", "0"); w.set("ROWVER", "1");
    if (w.ok) a.writeCurrent();
}

// The default rooms every BBS starts with. This list is the single source of truth; append to
// it to add a standing room. ensure_bbs_tables() seeds these on a fresh store AND tops up any
// that are missing on an existing store, so a newly-added room (e.g. board.lounge) reaches
// already-populated installs without a destructive re-seed. KIND: 0=governance projection,
// 1=chat, 2=notice. POSTPERM: permission required to post ("" = system/read-only).
struct DefaultBoard { const char* bkey; const char* name; int kind; const char* postperm; };
inline const DefaultBoard kDefaultBoards[] = {
    { "board.governance", "Governance (grant requests)", 0, ""          },
    { "board.afb.chat",   "AFB local chat",              1, "bbs.post"  },
    { "board.notice",     "Notices",                     2, "bbs.post"  },
    { "board.lounge",     "The Lounge",                  1, "bbs.post"  },  // Derald + AI partners
    { "board.guestbook",  "Guestbook (leave a message)", 2, "bbs.guest" },  // guests: leave-a-message only
    { "board.worklog",    "Agent worklog / handoffs",    2, "bbs.post"  },  // AIF-057: async pickup/dropoff
};

// True if a row with this BKEY already exists (idempotency guard for top-up).
bool board_key_present(xbase::DbArea& a, const char* bkey) {
    std::uint64_t n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a}; if (r.str("BKEY") == bkey) return true; }
    return false;
}

} // namespace

std::string default_bbs_dir() {
    return (dottalk::paths::get_slot(dottalk::paths::Slot::DATA) / "metadata" / schema::kBbsDir).string();
}

std::string board_postperm(const std::string& dir, const std::string& board_key) {
    std::string err;
    xbase::DbArea a;
    if (!open_table(dir, "SYSBOARD", a, err)) return {};
    std::string perm;
    std::uint64_t n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) {
        if (!a.gotoRec64(i)) continue;
        RowR r{a};
        if (r.str("BKEY") == board_key) { perm = r.str("POSTPERM"); break; }
    }
    a.close();
    return perm;
}

bool ensure_bbs_tables(const std::string& dir, std::string& err) {
    std::error_code ec;
    fs::create_directories(dir, ec);
    if (ec) { err = "bbs: cannot create dir " + dir + ": " + ec.message(); return false; }

    // Create the tables only on a fresh store; otherwise leave existing data untouched.
    if (!fs::exists(join(dir, "SYSBOARD"))) {
        for (const auto& t : schema::all_tables())
            if (!create_table(dir, t, err)) return false;
    }

    // Seed (fresh) or top-up (existing) the default rooms. Idempotent by BKEY: existing boards
    // keep their ids and are never duplicated; a newly-added default is appended with the next
    // free id. This is what lets board.lounge appear on an already-seeded install with no
    // re-seed and no data loss.
    xbase::DbArea a;
    if (!open_table(dir, "SYSBOARD", a, err)) return false;
    {
        TableLock lk(a, err);                   // serialize the append against the other process
        if (!lk) { a.close(); return false; }
        std::uint64_t nextid = 0, n = a.recCount64();
        for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a}; nextid = std::max(nextid, r.u64("ID")); }
        ++nextid;                               // 1 on an empty table, else max(ID)+1
        for (const auto& b : kDefaultBoards) {
            if (board_key_present(a, b.bkey)) continue;
            seed_board(a, err, nextid++, b.bkey, b.name, b.kind, b.postperm);
            if (!err.empty()) break;
        }
    }                                           // release FLOCK while the area is still open
    a.close();
    return err.empty();
}

bool list_boards(const std::string& dir, std::vector<Board>& out, std::string& err) {
    out.clear();
    if (!ensure_bbs_tables(dir, err)) return false;
    xbase::DbArea a;
    if (!open_table(dir, "SYSBOARD", a, err)) return false;
    std::uint64_t n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) {
        if (!a.gotoRec64(i)) continue; RowR r{a};
        out.push_back(Board{ r.u64("ID"), r.str("BKEY"), r.str("NAME"), r.i("KIND"), r.str("POSTPERM"), r.i("STATUS") });
    }
    a.close();
    return true;
}

bool read_board(const std::string& dir, const std::string& board_key,
                std::optional<std::uint64_t> thread_id, std::uint64_t last_n,
                std::vector<Thread>& threads, std::vector<Post>& posts, std::string& err) {
    threads.clear(); posts.clear();
    if (!ensure_bbs_tables(dir, err)) return false;
    const std::uint64_t bid = board_id_for(dir, board_key, err);
    if (bid == 0) { err = "bbs: no such board " + board_key; return false; }

    { xbase::DbArea a;
      if (!open_table(dir, "SYSTHREAD", a, err)) return false;
      std::uint64_t n = a.recCount64();
      for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a};
          if (r.u64("BOARDID") != bid) continue;
          threads.push_back(Thread{ r.u64("ID"), r.u64("BOARDID"), r.str("SUBJECT"), r.u64("OPENEDBY"), r.u64("OPENAT"), r.i("STATE"), r.u64("LASTPOST") }); }
      a.close(); }

    { xbase::DbArea a;
      if (!open_table(dir, "SYSPOST", a, err)) return false;
      std::uint64_t n = a.recCount64();
      for (std::uint64_t i = 1; i <= n; ++i) { if (!a.gotoRec64(i)) continue; RowR r{a};
          if (r.u64("BOARDID") != bid) continue;
          if (thread_id && r.u64("THREADID") != *thread_id) continue;
          posts.push_back(Post{ r.u64("ID"), r.u64("BOARDID"), r.u64("THREADID"), r.u64("AUTHORID"),
                                r.i("AUTHKIND"), r.i("KIND"), r.str("BODY"), r.u64("REFGRANT"),
                                r.str("RUNID"), r.u64("POSTAT"), r.i("STATUS") }); }
      a.close(); }

    // Governance board also projects live SYSGRANT rows (read-only).
    if (board_key == "board.governance") {
        std::vector<Post> gov;
        std::string gerr;
        if (project_governance("", gov, gerr)) for (auto& p : gov) posts.push_back(std::move(p));
    }

    if (last_n > 0 && posts.size() > last_n) posts.erase(posts.begin(), posts.end() - static_cast<long>(last_n));
    return true;
}

bool post_new(const std::string& dir, const std::string& board_key, const std::string& subject,
              const std::string& body, std::uint64_t author_id, int author_kind,
              std::uint64_t& new_post_id, std::string& err) {
    if (!ensure_bbs_tables(dir, err)) return false;
    if (board_key == "board.governance") { err = "bbs: board.governance is a read-only projection; use USER REQUEST"; return false; }
    const std::uint64_t bid = board_id_for(dir, board_key, err);
    if (bid == 0) { err = "bbs: no such board " + board_key; return false; }

    const std::uint64_t tid = next_id(dir, "SYSTHREAD", err); if (!err.empty()) return false;
    const std::uint64_t pid = next_id(dir, "SYSPOST", err);   if (!err.empty()) return false;
    const std::uint64_t now = now_epoch();

    { xbase::DbArea a; if (!open_table(dir, "SYSTHREAD", a, err)) return false;
      bool wrote = false;
      { TableLock lk(a, err);
        if (lk) { a.appendBlank(); RowW w{a, err};
          w.set("ID", s_u64(tid)); w.set("BOARDID", s_u64(bid)); w.set("SUBJECT", subject);
          w.set("OPENEDBY", s_u64(author_id)); w.set("OPENAT", s_u64(now)); w.set("STATE", "0"); w.set("LASTPOST", s_u64(pid));
          if (w.ok) { a.writeCurrent(); wrote = true; } } }
      a.close(); if (!wrote) return false; }

    { xbase::DbArea a; if (!open_table(dir, "SYSPOST", a, err)) return false;
      bool wrote = false;
      { TableLock lk(a, err);
        if (lk) { a.appendBlank(); RowW w{a, err};
          w.set("ID", s_u64(pid)); w.set("BOARDID", s_u64(bid)); w.set("THREADID", s_u64(tid));
          w.set("AUTHORID", s_u64(author_id)); w.set("AUTHKIND", s_int(author_kind)); w.set("KIND", "0");
          w.set("BODY", body); w.set("REFGRANT", "0"); w.set("RUNID", ""); w.set("POSTAT", s_u64(now)); w.set("STATUS", "0");
          if (w.ok) { a.writeCurrent(); wrote = true; } } }
      a.close(); if (!wrote) return false; }

    new_post_id = pid;
    return true;
}

bool reply_to(const std::string& dir, std::uint64_t post_id, const std::string& body,
              std::uint64_t author_id, int author_kind, std::uint64_t& new_post_id, std::string& err) {
    if (!ensure_bbs_tables(dir, err)) return false;
    // Resolve the parent post's board + thread.
    std::uint64_t bid = 0, tid = 0;
    { xbase::DbArea a; if (!open_table(dir, "SYSPOST", a, err)) return false;
      std::uint64_t rec = find_rec(a, "ID", post_id);
      if (rec == 0) { a.close(); err = "bbs: no such post " + std::to_string(post_id); return false; }
      a.gotoRec64(rec); RowR r{a}; bid = r.u64("BOARDID"); tid = r.u64("THREADID"); a.close(); }

    const std::uint64_t pid = next_id(dir, "SYSPOST", err); if (!err.empty()) return false;
    const std::uint64_t now = now_epoch();
    { xbase::DbArea a; if (!open_table(dir, "SYSPOST", a, err)) return false;
      bool wrote = false;
      { TableLock lk(a, err);
        if (lk) { a.appendBlank(); RowW w{a, err};
          w.set("ID", s_u64(pid)); w.set("BOARDID", s_u64(bid)); w.set("THREADID", s_u64(tid));
          w.set("AUTHORID", s_u64(author_id)); w.set("AUTHKIND", s_int(author_kind)); w.set("KIND", "1");
          w.set("BODY", body); w.set("REFGRANT", "0"); w.set("RUNID", ""); w.set("POSTAT", s_u64(now)); w.set("STATUS", "0");
          if (w.ok) { a.writeCurrent(); wrote = true; } } }
      a.close(); if (!wrote) return false; }

    // Update thread LASTPOST (under the table lock as well).
    { xbase::DbArea a; if (!open_table(dir, "SYSTHREAD", a, err)) return false;
      { TableLock lk(a, err);
        if (lk) { std::uint64_t rec = find_rec(a, "ID", tid);
          if (rec) { a.gotoRec64(rec); RowW w{a, err};
                     int idx = fields::findFieldCI(a, "LASTPOST"); if (idx >= 0) a.set(idx + 1, s_u64(pid)); a.writeCurrent(); } } }
      a.close(); }

    new_post_id = pid;
    return true;
}

bool close_thread(const std::string& dir, std::uint64_t thread_id, std::string& err) {
    if (!ensure_bbs_tables(dir, err)) return false;
    xbase::DbArea a; if (!open_table(dir, "SYSTHREAD", a, err)) return false;
    bool done = false;
    { TableLock lk(a, err);
      if (lk) { std::uint64_t rec = find_rec(a, "ID", thread_id);
        if (rec == 0) { err = "bbs: no such thread " + std::to_string(thread_id); }
        else { a.gotoRec64(rec);
          int idx = fields::findFieldCI(a, "STATE");
          if (idx >= 0) a.set(idx + 1, "2");   // 2 = closed
          a.writeCurrent(); done = true; } } }
    a.close();
    return done;
}

bool project_governance(const std::string& identity_dir_in, std::vector<Post>& out, std::string& err) {
    out.clear();
    // Default to the identity metadata dir if not supplied.
    std::string identity_dir = identity_dir_in;
    if (identity_dir.empty())
        identity_dir = (dottalk::paths::get_slot(dottalk::paths::Slot::DATA) / "metadata" / "identity").string();
    const std::string grant = (fs::path(identity_dir) / "SYSGRANT.dbf").string();
    if (!fs::exists(grant)) return true;   // no grants yet -> empty projection (not an error)

    xbase::DbArea a;
    try { a.open(grant); } catch (const std::exception& e) { err = std::string("bbs: cannot open SYSGRANT: ") + e.what(); return false; }
    std::uint64_t n = a.recCount64();
    for (std::uint64_t i = 1; i <= n; ++i) {
        if (!a.gotoRec64(i)) continue; RowR r{a};
        // Render a grant row as a read-only governance post.
        Post p;
        p.id        = r.u64("ID");
        p.board_id  = 1;                    // board.governance
        p.thread_id = r.u64("ID");          // one thread per grant
        p.author_id = r.u64("REQBY");
        p.author_kind = 0;
        p.kind      = 2;                    // agent_prompt
        p.ref_grant = r.u64("ID");
        p.post_at   = r.u64("GRANTAT");
        p.status    = 0;
        // STATUS codes in SYSGRANT: 0=Requested 1=Granted 2=Denied 3=Expired 4=Revoked (per identity enum order).
        const int gs = r.i("STATUS");
        const char* label = gs == 0 ? "REQUESTED" : gs == 1 ? "GRANTED" : gs == 2 ? "DENIED" : gs == 3 ? "EXPIRED" : "REVOKED";
        p.body = std::string("[grant ") + label + "] scope=" + r.str("ACTSCOPE") + " reason=" + r.str("REASON");
        out.push_back(std::move(p));
    }
    a.close();
    return true;
}

} // namespace dottalk::bbs
