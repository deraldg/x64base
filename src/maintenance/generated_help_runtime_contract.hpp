
#pragma once

#include <string>
#include <vector>

// @dottalk.contract generated-help-runtime-maintenance v1
// Purpose: Define a tiny, behavior-neutral contract surface for generated HELP
// runtime smoke support. This file is staged by Phase 22AE.6.5.10ER-B as a
// compile-ready contract only. It is not registered as a command and does not
// mutate HELP, CMDHELPCHK, source documentation, latest pointers, CDX, or LMDB.
//
// Maintenance doctrine:
// - Python 3.12 remains the repeatable orchestration engine.
// - C++ exposes small deterministic helpers only when runtime behavior needs
//   native proof instead of Python inference.
// - Temporary runtime smokes use explicit SETPATH DBF/INDEXES and DOTSCRIPT OUT.
// - No temporary proof package should copy or modify system .dts scripts.
// - No placeholder recnos such as GOTO <n> are valid in a generated smoke.

namespace dottalk::maintenance::generated_help {

struct RuntimeSmokeCommandSet {
    std::vector<std::string> lines;
};

// Return the canonical setup lines for a generated HELP runtime smoke.
// This is behavior-neutral until a later, separately authorized package wires it
// into a command or build/runtime surface.
RuntimeSmokeCommandSet make_help_runtime_smoke_setup(
    const std::string& help_dbf_root,
    const std::string& help_index_root);

// Validate that a generated DotScript smoke body avoids known brittle patterns.
// It intentionally checks text only and performs no runtime I/O.
bool generated_help_smoke_contract_ok(const std::vector<std::string>& lines,
                                      std::string* reason_out = nullptr);

}  // namespace dottalk::maintenance::generated_help
