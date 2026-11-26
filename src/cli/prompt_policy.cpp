// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: the prompt-suppression flag's single definition
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#include "cli/prompt_policy.hpp"

namespace cli::prompt {

namespace {
// ONE definition, process-wide. It was `static bool g_suppress_prompts` in
// src/cli/dirty_prompt.cpp before 2026-09-25; see the header for why it moved.
bool g_suppressed = false;
}

bool suppressed() { return g_suppressed; }

void set_suppressed(bool value) { g_suppressed = value; }

SuppressScope::SuppressScope(bool value) : prev_(g_suppressed) { g_suppressed = value; }

SuppressScope::~SuppressScope() { g_suppressed = prev_; }

} // namespace cli::prompt
