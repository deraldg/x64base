#pragma once
// @dottalk.contract
// file: include/memo/memo_store.hpp
// subsystem: memo
// role: Declares memo or large-object interfaces for DotTalk++ storage workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

// memo_store.hpp
//
// Retired experimental OO store interface.
//
// The live x64 memo persistence backend is the existing DTX backend:
//   memo_backend.hpp / memostore.hpp / memostore.cpp
//
// Keep this header as a compatibility include only while the tree is cleaned up.
// Do not add a second x64 memo backend here.

#include "memo/memo_backend.hpp"
#include "memo/memo_object.hpp"

namespace dottalk::memo {

struct MemoVerifyResult {
    bool ok{true};
    std::string message;
};

} // namespace dottalk::memo

