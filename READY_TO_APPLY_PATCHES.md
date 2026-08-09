# AIF-098 -- paste-ready patches for ground-check (R2)

These are the concrete changes against the current `development` tip sources
(fetched 2026-08-09). Field name `SRCLANE` is 7 chars (classic DBF physical
limit is 10). KIND=5 is free per schema comment.

Claude: ground-check these against the live schema / ensure path before any build.

## GROUND-CHECK: PASS (Claude / Cowork, 2026-08-08)

Verified every patch against live `development` source before any build:
- Schema / struct / decl match current source exactly; `w::KEY`=64, `SRCLANE`=7 chars (safe under
  the 10-char classic limit), KIND=5 genuinely free (0-4 enumerated).
- `post_new` rewrite is faithful; `KIND=0` preserved for normal posts (`s_int(0)` == `"0"`) --
  ZERO behavior change on existing flows. `RUNID` left empty; `SRCLANE` added.
- `do_post` marker detection fires on real `promote.py` output: `substr(14, close-14)` extracts
  exactly `<lane>` from `[consolidated:<lane>]` (verified against `promote.py make_subject`).
- Attribution (`current_member()`, anon denied) and `reply_to` untouched.

**GATE CATCH -- observe before / at apply.** The BBS store has NO column-add path:
`ensure_bbs_tables` tops up missing *rows* (boards), not missing *fields*. So on an existing
`SYSPOST.DBF` (old schema), `w.set("SRCLANE", ...)` writes to a column that is not there.
- Verification PROOF: run against a FRESH / re-seeded `SYSPOST` (the new schema carries `SRCLANE`),
  the way the `INDEX_X64` smokes build throwaway tables. Do NOT run the proof against the old store.
- PRODUCTION (a store with real posts): a non-destructive `SRCLANE` migration is a FOLLOW-UP
  milestone of AIF-098. Never force a destructive re-seed.

Verdict: **safe to apply + build**, with the fresh-store proviso above for the proof.

---

## 1. include/bbs/bbs_schema.hpp

**Replace the syspost() comment + table** with:

```cpp
// Posts. KIND: 0=post 1=reply 2=agent_prompt 3=agent_reply 4=system
//              5=consolidated_from_chat (Frontal_Mem Lane 1; lane token in SRCLANE).
// STATUS: 0=posted 1=redacted. REFGRANT = SYSGRANT id (0=none).
// RUNID = ai_runs ref (may be empty). SRCLANE = source-lane token (may be empty).
inline Table syspost() {
    return {"SYSPOST", {
        N("ID", w::ID), N("BOARDID", w::ID), N("THREADID", w::ID),
        N("AUTHORID", w::ID), N("AUTHKIND", 2), N("KIND", 2),
        C("BODY", w::BODY), N("REFGRANT", w::ID), C("RUNID", w::NAME),
        C("SRCLANE", w::KEY),   // AIF-098: source-lane for kind==5
        N("POSTAT", w::ID), N("STATUS", 2),
    }};
}
```

**Migration note (important):**  
`ensure_bbs_tables` currently creates tables from this schema when absent. For
*existing* stores the new column must be added non-destructively. Confirm the
codebase's existing top-up / append-field path (or add a one-time safe alter)
before building. Do not force a destructive re-seed.

---

## 2. include/bbs/bbs_store.hpp

**Update the Post struct** (add src_lane for readers):

```cpp
struct Post   { std::uint64_t id{}, board_id{}, thread_id{}, author_id{}; int author_kind{}, kind{};
                std::string body; std::uint64_t ref_grant{}; std::string run_id, src_lane;
                std::uint64_t post_at{}; int status{}; };
```

**Extend post_new signature** (defaults keep every existing call site source-compatible):

```cpp
bool post_new  (const std::string& dir, const std::string& board_key, const std::string& subject,
                const std::string& body, std::uint64_t author_id, int author_kind,
                std::uint64_t& new_post_id, std::string& err,
                int post_kind = 0,
                const std::string& src_lane = "");
```

Leave `reply_to` unchanged for this package.

---

## 3. src/bbs/bbs_store.cpp -- post_new

**Replace the current post_new signature + KIND/RUNID writes** with:

```cpp
bool post_new(const std::string& dir, const std::string& board_key, const std::string& subject,
              const std::string& body, std::uint64_t author_id, int author_kind,
              std::uint64_t& new_post_id, std::string& err,
              int post_kind,                    // defaulted in header
              const std::string& src_lane) {    // defaulted in header
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
          w.set("AUTHORID", s_u64(author_id)); w.set("AUTHKIND", s_int(author_kind));
          w.set("KIND", s_int(post_kind));          // AIF-098: was hard-coded "0"
          w.set("BODY", body); w.set("REFGRANT", "0");
          w.set("RUNID", "");                       // leave for ai_runs; do NOT put lane here
          w.set("SRCLANE", src_lane);               // AIF-098: new field
          w.set("POSTAT", s_u64(now)); w.set("STATUS", "0");
          if (w.ok) { a.writeCurrent(); wrote = true; } } }
      a.close(); if (!wrote) return false; }

    new_post_id = pid;
    return true;
}
```

---

## 4. src/cli/cmd_bbs.cpp -- do_post

**After the existing `split_subject_body` call and before the permission / current_member block**, insert detection so the existing promote.py .dts keeps working without a grammar change:

```cpp
void do_post(std::istringstream& iss) {
    std::string board; iss >> board;
    std::string subject, body;
    if (board.empty()) { bbs_usage(); return; }
    std::string tail = rest_of(iss);   // "SUBJECT <s> BODY <text>"
    std::string up = upcase(tail);
    if (up.rfind("SUBJECT", 0) == 0) tail = trim(tail.substr(7));
    if (!split_subject_body(tail, subject, body)) { print_info("BBS", "POST needs: SUBJECT <subject> BODY <text>"); return; }

    // AIF-098: detect Frontal_Mem Lane 1 marker emitted by promote.py.
    // KIND=5 = consolidated_from_chat; lane token goes into SRCLANE.
    int post_kind = 0;
    std::string src_lane;
    if (subject.size() > 14 && subject.rfind("[consolidated:", 0) == 0) {
        auto close = subject.find(']');
        if (close != std::string::npos) {
            src_lane = subject.substr(14, close - 14);   // after "[consolidated:"
            post_kind = 5;
            // Optional (recommended once SRCLANE exists): strip marker for cleaner subject
            // subject = trim(subject.substr(close + 1));
        }
    }

    const std::string dir = dottalk::bbs::default_bbs_dir();
    // AIF-075: enforce the board's post permission ...
    std::string need = dottalk::bbs::board_postperm(dir, board);
    if (need.empty()) need = "bbs.post";
    dottalk::identity::Decision d = dottalk::identity::agent_permitted(need);
    if (!d.allowed()) { print_info("BBS", need + " denied: " + d.reason); return; }
    // AIF-075: attribute the post to the real acting member ...
    std::uint64_t author_id = 0; int author_kind = 0;
    dottalk::identity::current_member(author_id, author_kind);
    std::uint64_t pid = 0; std::string err;
    if (!dottalk::bbs::post_new(dir, board, subject, body, author_id, author_kind, pid, err,
                                post_kind, src_lane))
        { print_info("BBS", err); return; }
    print_info("BBS", "posted #" + std::to_string(pid) + " to " + board);
}
```

Attribution path is unchanged: still `current_member()` then `post_new`. Anon remains denied by the existing RBAC check.

---

## What is intentionally left for the maintainer / Claude

- Exact non-destructive top-up of existing SYSPOST.DBF for the new SRCLANE column
  (schema definition is above; the ensure / alter mechanics must be confirmed against live code).
- Whether to strip the `[consolidated:<lane>]` prefix from SUBJECT after extraction
  (commented optional line above; recommended once SRCLANE is live).
- Any unit-test / smoke updates that assert KIND==5 + SRCLANE for a promote.py .dts run.
- The actual build + `./datarun.ps1` verification (see notes/VERIFICATION_PROCEDURE.md).

---

## Acceptance after apply

- Existing call sites of `post_new` compile unchanged (defaults).
- A promote.py-generated .dts run as logged-in member produces SYSPOST rows with:
  - AUTHORID != 0
  - KIND == 5
  - SRCLANE holding the lane token
  - RUNID left empty / for ai_runs only
- Anon POST still denied (AIF-075).
