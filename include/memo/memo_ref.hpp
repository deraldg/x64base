#pragma once
// @dottalk.contract
// file: include/memo/memo_ref.hpp
// subsystem: memo
// role: Declares memo or large-object interfaces for DotTalk++ storage workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

// memo_ref.hpp
//
// Canonical memo reference for the live DotTalk++ memo system.
//
// Important:
//   There must be only one dottalk::memo::MemoRef type in the build.
//   The live x64 memo backend is the DTX backend declared in memo_backend.hpp,
//   where MemoRef is a backend-neutral token stored by the DBF/x64 layer.
//
// This header intentionally reuses that MemoRef instead of defining a second
// object-id-based MemoRef.  OO memo objects may describe type/capabilities, but
// persistence still resolves through the backend token.

#include "memo/memo_backend.hpp"

#include <cstdint>
#include <string>

namespace dottalk::memo {

// Return the backend-neutral external token.
std::string to_string(const MemoRef& ref);

// Parse a textual memo reference into the canonical token ref.
// Accepted transition forms:
//   ""                         -> null ref
//   "0000000000000001"         -> DTX token
//   "1"                        -> object id, converted to DTX token
//   "memo:v1:x64:1:0"          -> older OO skeleton form, converted to token
bool parse_memo_ref(const std::string& text, MemoRef& out);

// Create a canonical DTX/x64 token from an object id.
MemoRef make_x64_ref(std::uint64_t object_id);

// Decode a canonical token or transition form into an object id.
bool try_object_id_from_ref(const MemoRef& ref, std::uint64_t& out_object_id) noexcept;

} // namespace dottalk::memo

