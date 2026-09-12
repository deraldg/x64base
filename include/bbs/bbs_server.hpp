// @dottalk.file v1
// subsystem: bbs
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-052
// owner: member.derald
// status: supported

// bbs_server.hpp -- localhost, token-authenticated BBS/agent server (M4). Public API.
//
// SECURITY (load-bearing):
//   - binds 127.0.0.1 ONLY (never 0.0.0.0). In mirrored-mode WSL the loopback is shared with
//     Windows, so the *token* (M3 Argon2id) is the trust boundary, not the bind address.
//   - token auth is a hard gate before any capability; capabilities are RBAC-checked per request.
//   - the identity session is process-global and unlocked, so the accept loop is SERIALIZED
//     (one connection at a time). Requires M3 (real token crypto). Depends on M1 (board store).
#pragma once

#include <cstdint>
#include <string>

namespace dottalk::bbs {

// Blocking, single-threaded server. Binds 127.0.0.1:<port>, serves authenticated connections,
// bridges CHAT to the local Ollama at 127.0.0.1:11434 using <model>. Returns when a shutdown is
// requested by an owner connection (or on fatal socket error); `err` set on failure.
// The caller's identity session is saved on entry and restored on return.
bool serve(std::uint16_t port, const std::string& model, std::string& err);

} // namespace dottalk::bbs
