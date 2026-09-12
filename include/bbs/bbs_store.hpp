// @dottalk.file v1
// subsystem: bbs
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-052
// owner: member.derald
// status: supported

// bbs_store.hpp -- DBF-backed store for the AI-BBS board (M1). Public API.
//
// Mirrors include/identity/identity_dbf_store.hpp. All values cross the DbArea
// boundary as strings; ids are 64-bit stored as decimal text.
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace dottalk::bbs {

struct Board  { std::uint64_t id{}; std::string bkey, name; int kind{}; std::string postperm; int status{}; };
struct Thread { std::uint64_t id{}, board_id{}; std::string subject; std::uint64_t opened_by{}, open_at{}; int state{}; std::uint64_t last_post{}; };
struct Post   { std::uint64_t id{}, board_id{}, thread_id{}, author_id{}; int author_kind{}, kind{}; std::string body; std::uint64_t ref_grant{}; std::string run_id; std::uint64_t post_at{}; int status{}; };

// data/metadata/bbs/ (resolved via paths::Slot::DATA).
std::string default_bbs_dir();

// Post-permission required by a board (its stored POSTPERM); "" if the board is unknown.
// The server requires this permission before accepting a POST, so per-board post scoping
// (e.g. board.guestbook -> bbs.guest) is honored rather than a single global bbs.post.
std::string board_postperm(const std::string& dir, const std::string& board_key);

// Create the three tables if absent and seed default boards
// (board.governance, board.afb.chat, board.notice) on first creation. Idempotent.
bool ensure_bbs_tables(const std::string& dir, std::string& err);

// Reads.
bool list_boards (const std::string& dir, std::vector<Board>&  out, std::string& err);
bool read_board  (const std::string& dir, const std::string& board_key,
                  std::optional<std::uint64_t> thread_id, std::uint64_t last_n,
                  std::vector<Thread>& threads, std::vector<Post>& posts, std::string& err);

// Writes. post() opens a new thread + first post; reply() appends to an existing thread.
// author_id/author_kind come from the current identity session (0/0 if none in M1).
bool post_new  (const std::string& dir, const std::string& board_key, const std::string& subject,
                const std::string& body, std::uint64_t author_id, int author_kind,
                std::uint64_t& new_post_id, std::string& err);
bool reply_to  (const std::string& dir, std::uint64_t post_id, const std::string& body,
                std::uint64_t author_id, int author_kind, std::uint64_t& new_post_id, std::string& err);
bool close_thread(const std::string& dir, std::uint64_t thread_id, std::string& err);

// Governance projection: render pending/decided SYSGRANT rows from the identity dir
// as read-only posts on board.governance. identity_dir empty => use identity default.
bool project_governance(const std::string& identity_dir, std::vector<Post>& out, std::string& err);

} // namespace dottalk::bbs
