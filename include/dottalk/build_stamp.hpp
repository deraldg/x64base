// @dottalk.file v1
// subsystem: dottalk
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>

// WHICH BINARY IS THIS -- the question the version stamp structurally cannot
// answer, given its own home (2026-09-11).
//
// dottalk/version.hpp carries the COMMIT: a label and a SHA, captured by
// configure_file at CMake configure time. That is the right answer to "which
// code", and it is not an answer to "which build". `cmake --build` does not
// re-configure, so a rebuild of an unchanged commit -- a restored file, a
// touched header, a different generator, a second worktree -- produces a NEW
// executable wearing the OLD stamp, byte for byte identical in the banner.
//
// MEASURED, and it cost a day. On 2026-09-11 a REGRESSION suite went red, then
// green, then red again with no commit in between, and the question "was that
// the same binary" could not be answered from any line either run had printed.
// Both would have said `02337ee0`. The same gap is already recorded one layer
// up: tools/staging/check_soak_evidence.py proves two runs shared ONE build by
// comparing banners, so a restored-file rebuild is INVISIBLE to it and a soak
// taken either side of one reads as a single build when it was two.
//
// The answer is the running executable's own mtime, which no configure can
// stale because it is read from the file that is executing. GetModuleFileNameW
// / _NSGetExecutablePath / /proc/self/exe, then last_write_time.
//
// THIS EXISTS AS ONE FUNCTION BECAUSE IT HAD TWO CALLERS THE DAY IT WAS
// WRITTEN, and this tree has a long record of what the second copy does: six
// field-name matchers, two lock reclaimers wearing one name, two generators
// sharing one buffer. A build stamp that could disagree with itself between
// VERSION and a regression log would be worse than none -- the whole point is
// that a reader can compare two transcripts and trust the comparison.
namespace dottalk {

// The running executable's build time, formatted "%b %d %Y %H:%M:%S" to match
// what the VERSION banner has always printed.
//
// FALLS BACK TO THE TRANSLATION UNIT'S OWN COMPILE TIME when the executable
// path or its mtime cannot be read. That fallback is WEAKER and knowably so:
// __DATE__/__TIME__ freeze when THIS file last compiled, which an incremental
// build may skip entirely. It is preserved because it is what cmd_version.cpp
// has always done on this path, and losing a weak answer for no answer would
// be a regression in a banner nobody was complaining about.
std::string build_stamp();

// The running executable's path, empty if it cannot be determined. Exposed
// because "which binary" is more usefully answered by WHERE than by WHEN when
// two of them wear one name in different directories.
std::string executable_path();

// dottalk::version::display_version() -- the label and SHA -- re-exported here
// so a caller can have the run's identity WITHOUT including
// dottalk/version.hpp.
//
// That indirection is not tidiness, it is AIF-122's budget being kept. The
// version stamp arrives as a generated header whose mtime moves on every
// commit, so every TU that includes dottalk/version.hpp recompiles on every
// commit. AIF-122 took that cost from ~400 TUs down to two by moving the
// values off the command line, and the note in config/version_stamp.hpp.in
// records the two by name. cmd_regression.cpp is 5,500 lines and wanted the
// identity for its log header; including the stamp there would have quietly
// spent a large part of what AIF-122 bought. This file is a hundred lines and
// is already a stamp reader, so it absorbs the third include and the budget
// holds at two large TUs plus this one.
std::string version_identity();

} // namespace dottalk
