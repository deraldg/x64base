#pragma once
// @dottalk.contract
// file: include/memo/memo_context.hpp
// subsystem: memo
// role: Declares memo or large-object interfaces for DotTalk++ storage workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <cstdint>
#include <string>

namespace dottalk::memo {

enum class MemoBackendKind : std::uint8_t {
    None = 0,
    V32Stub,
    V64Dtx
};

enum class MemoMode : std::uint8_t {
    Detached = 0,
    ReadOnly,
    ReadWrite
};

struct MemoContext {
    std::string container_path;
    MemoBackendKind backend{MemoBackendKind::None};
    MemoMode mode{MemoMode::Detached};
    std::uint32_t page_size{0};
    bool attached{false};
    bool needs_pack{false};

    bool has_memo() const noexcept {
        return attached && backend != MemoBackendKind::None;
    }

    bool is_v64() const noexcept {
        return backend == MemoBackendKind::V64Dtx;
    }

    bool writable() const noexcept {
        return mode == MemoMode::ReadWrite;
    }

    void clear() noexcept {
        container_path.clear();
        backend = MemoBackendKind::None;
        mode = MemoMode::Detached;
        page_size = 0;
        attached = false;
        needs_pack = false;
    }
};

} // namespace dottalk::memo

