#pragma once

#include <cstdint>

namespace xbase {

enum class AreaKind : std::uint8_t;

// Canonical short token used in diagnostics and metadata.
//
// Runtime kind is the internal route/capability family, not the physical
// on-disk DBF flavor.
const char* area_kind_token(AreaKind k) noexcept;

// Human-friendly label if you ever want more descriptive runtime reporting.
const char* area_kind_label(AreaKind k) noexcept;

// Physical DBF version-byte reporting.
//
// This is intentionally separate from AreaKind.  A VFP DBF version byte can
// use the V64-capable runtime path while still being physically VFP, not x64.
const char* dbf_version_token(std::uint8_t ver) noexcept;
const char* dbf_version_label(std::uint8_t ver) noexcept;

} // namespace xbase
