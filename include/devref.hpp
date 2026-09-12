// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: reserved

//devref.hpp
//
// RESERVED, NOT UNFINISHED. Corrected 2026-08-15 from `status: supported`.
//
// The namespace is intentionally empty. It is held for the split of the
// x64base builds, where developer-facing reference material gets its own
// authority; developer options are already gated, so the seam exists and this
// is the catalog that will sit behind it.
//
// Why the header lied, and why it matters: `status: supported` on an empty
// file, while AI_TIER1_SEED_V1.md names devref among the six reference
// authorities that "own a namespace", told every agent that reads the seed --
// which is every agent -- that this was a working catalog. Nothing caught it,
// because refcheck_v1.catalog_names() returns [] for a MISSING file and []
// for an EMPTY one, so zero content and zero findings are the same answer.
// tools/fullstack_docs/edrefcheck_v1.py now reports those three states apart
// for the education catalog; refcheck_v1 has not been given the same
// treatment yet, and pshell_ref and sql_ref have not been looked at.
//
// Until the build split lands: no source file includes this, and none should.

#pragma once

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>
#include <vector>

namespace devref {



} // namespace devref