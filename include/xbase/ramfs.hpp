#pragma once
//
// xbase::ramfs — in-process RAM filesystem (AIF-043, in-memory tables, drop V1)
// ----------------------------------------------------------------------------
// Path-keyed byte files served from process memory. This is the self-owned
// substitute for a RAM-disk driver: the 1980s RAMDRIVE.SYS / VDISK.SYS concept,
// but owned by the engine instead of the OS — no signed kernel driver, no drive
// letter, no third-party license to vet for redistribution.
//
// Model: a process-global registry maps normalized absolute paths to RamFiles
// (growable byte buffers). A path is "virtual" iff it lives under a mounted
// virtual root. The DBF and native-CDX file layers consult this registry: for a
// virtual path they read/write a RamFile; for a real path they use the OS.
//
// LMDB is out of scope here (it must mmap a real OS file) — that stays on the
// optional symlink/RAM-disk add-on. This VFS covers the DBF + native-CDX lane.
//
// Lifetime: RamFiles persist in the registry across stream open/close (so USE
// can reopen a table and its sibling .cdx resolves), and are dropped by erase()
// or clear() — the ephemeral CLOSE/exit behavior for M1.
//
// Threading: M1 is single-process/single-area; calls are not internally locked.
// A future milestone can add a mutex if concurrent areas share the registry.
//
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <iostream>

namespace xbase::ramfs {

// ---- virtual-root registration ------------------------------------------------
// Roots are absolute, lexically-normalized directory prefixes. `DO mem` mounts
// the DBF/INDEXES slot roots; anything created under them lives in RAM.
void mount(const std::string& abs_root);
void unmount(const std::string& abs_root);
bool mounted(const std::string& abs_root);

// True iff `abs_path` resolves under any currently-mounted virtual root.
// Callers normalize to an absolute path first (same rule as DbArea::open).
bool is_virtual(const std::string& abs_path);

// ---- file operations (only meaningful for virtual paths) ----------------------
bool           exists(const std::string& abs_path);
std::uint64_t  size(const std::string& abs_path);   // 0 if absent
bool           erase(const std::string& abs_path);  // drop one RAM file; true if removed

// Enumerate virtual files under a root (for WSREPORT / RAM-residency reporting
// and the "zero real files" proof). Returns absolute paths.
std::vector<std::string> list(const std::string& abs_root);

// Drop every RAM file and unmount every root — the ephemeral teardown at
// session close. Sizes/roots reset to empty.
void clear();

// Aggregate bytes currently held across all RAM files — feeds the Layer-2 soft
// budget monitor (warn_pct / on_full) from VDISK_RAM_SIZING_AND_ADMIN_CONFIG.
std::uint64_t used_bytes();

// ---- stream access ------------------------------------------------------------
// Open a virtual file as a binary in|out iostream positioned at the start.
//   create=true  : make the file if absent (CREATE / append path)
//   create=false : nullptr if the file does not exist (USE / open path)
// Returns nullptr if `abs_path` is not virtual. The returned stream holds a
// shared reference to the underlying RamFile, so bytes survive stream close.
std::unique_ptr<std::iostream> open(const std::string& abs_path, bool create);

} // namespace xbase::ramfs
