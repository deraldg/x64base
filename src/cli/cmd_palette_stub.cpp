// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: PALETTE
// project: project.x64base.runtime
// lane: AIF-122
// owner: member.derald
// status: supported

// src/cli/cmd_palette_stub.cpp -- PALETTE is not available in this build.
//
// AIF-122. This was GENERATED at configure time by file(WRITE) in
// src/CMakeLists.txt, into ${CMAKE_CURRENT_BINARY_DIR}/generated. Two problems
// with that, both measured 2026-08-22:
//
//   1. file(WRITE) is NOT copy-if-different. It rewrote byte-identical content
//      with a fresh mtime on EVERY configure, so every configure cost one
//      recompile. The same configure emitted build_vectors.hpp through
//      configure_file() -- copy-if-different -- and that cost zero. One build
//      log, two CMake commands, 1 file against 0.
//   2. The generated body was a CMake BRACKET argument ([=[ ... ]=]), which
//      performs no variable expansion, and contained nothing to expand anyway.
//      It was a constant. Seven fixed lines of C++ were being generated per
//      build tree -- thirteen copies existed across eight trees, at two
//      different byte counts, because file(WRITE) writes native line endings
//      and the WSL trees got LF where the Windows trees got CRLF.
//
// A constant belongs in source, where a person can find it. It is picked up by
// the GLOB_RECURSE over src/ like every other command, so nothing lists it.

#include <sstream>
#include <iostream>

namespace xbase { class DbArea; }

extern "C" void cmd_PALETTE(xbase::DbArea&, std::istringstream&) {
    std::cerr << "PALETTE not available in this build.\n";
}
