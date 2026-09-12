// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: AIF-078
// owner: member.derald
// status: supported
#pragma once

#include <string>

// DURABILITY: THE DIFFERENCE BETWEEN flush() AND fsync(), AND WHY THIS EXISTS.
//
// MEASURED 2026-08-31 across src/xbase and include/xbase: SIX calls to
// std::ostream::flush() and ZERO calls to fsync / FlushFileBuffers. DbArea holds
// a std::fstream and exposes only std::iostream& io(), so no native handle was
// reachable from the write path at all.
//
// flush() pushes the stream buffer into the OPERATING SYSTEM. That survives a
// crash of dottalkpp.exe and nothing more. The bytes are in the page cache; a
// power cut or an OS crash loses them, and the file that comes back is a
// partially written record with a header that says otherwise.
//
// This is the one syscall that was missing. It is deliberately NOT wired into
// DbArea::writeCurrent(): syncing every record write would pay a platter round
// trip per REPLACE across every table in the tree, and durability is not wanted
// per-record -- it is wanted at COMMIT POINTS, where an operation has finished
// and a reader could next observe it.
//
// ORDERING IS PART OF THE GUARANTEE AND CANNOT BE ADDED LATER.
// A memo save writes TWO files: the payload into the sidecar, then the row into
// the table (cmd_workspace.cpp puts the payload first on purpose, so a crash
// leaves an orphan payload -- wasted bytes -- rather than a row whose token
// points at nothing). SYNCS MUST MIRROR THAT ORDER. Sync the sidecar, THEN the
// table. Reversed, the row can reach the platter before the payload it names
// and the crash-safe direction is undone by the very call meant to secure it.
//
// NOT COVERED, stated so it is not assumed: this syncs a file's CONTENTS. It
// does not sync the DIRECTORY, which is what makes a CREATE or a RENAME durable.
// That is the compaction case (R136's multi-file class) and it needs its own
// answer along with the journal.

namespace xbase {

// Force this file's contents to durable media.
//
// Returns true on success. Returns true WITHOUT doing anything for a ramfs
// virtual path: an in-memory table has no platter, and reporting failure there
// would make every RAM-resident caller look broken (R6 -- absent must not be
// spelled with a failure value).
//
// Never throws. On failure `err` receives a platform detail when non-null.
bool durable_sync(const std::string& path, std::string* err = nullptr) noexcept;

} // namespace xbase
