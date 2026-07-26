// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/cli/vdisk_config.hpp
#pragma once
//
// [vdisk] admin config (AIF-043). A small, optional true-INI file — bin/vdisk.ini —
// parsed into a VDiskConfig. It governs the RAM virtual disk: an optional root
// override, the Layer-1 sizing recommendation (advisory), and the Layer-2 soft
// budget (warn high-water + on_full policy) applied against xbase::ramfs used bytes.
//
// The engine's .ini files (dottalkpp.ini / init.ini) are DotTalk *command scripts*,
// not key=value INI, so this config lives in its own file with its own parser.
//
// Entirely optional: a missing file or missing [vdisk] block => present=false =>
// feature off, existing setups unaffected. Spec: VDISK_RAM_SIZING_AND_ADMIN_CONFIG_V1.
//
#include <cstdint>
#include <string>

namespace dottalk::vdisk {

enum class Mode   { Auto, Fixed, Percent };
enum class OnFull { Warn, Spill, Fail };

struct VDiskConfig {
    bool          present  = false;  // a [vdisk] block was found and parsed
    bool          enabled  = true;   // enabled = 0 turns RAM residency off (admin off-switch)
    std::string   root;              // symlink/junction target (RAM volume); empty = use Slot::RAM
    Mode          mode     = Mode::Auto;
    std::uint64_t size_mb  = 512;    // mode = fixed
    std::uint64_t percent  = 25;     // mode = percent (of available RAM)
    std::uint64_t floor_mb = 64;     // clamps even fixed/percent overrides
    std::uint64_t ceil_mb  = 2048;   // clamps even fixed/percent overrides
    std::uint64_t warn_pct = 80;     // Layer-2 high-water warning
    OnFull        on_full  = OnFull::Warn;
};

const char* mode_name(Mode m) noexcept;
const char* on_full_name(OnFull f) noexcept;

// Parse an INI file for the [vdisk] block. Missing file/block => present=false.
// Comments: lines beginning with ; # or *; inline ;/# after a value are trimmed.
// Unknown keys ignored; missing keys keep the defaults above.
VDiskConfig load_vdisk_config(const std::string& ini_path);

// Layer-1 sizing recommendation (bytes): honors mode, then clamps to
// [floor_mb, ceil_mb], then caps at half of physical RAM (never starve the host).
// Advisory only — the OS mount is the hard limit.
std::uint64_t recommended_budget_bytes(const VDiskConfig& cfg);

// Platform physical / available RAM (bytes); 0 if unavailable.
std::uint64_t physical_ram_bytes();
std::uint64_t available_ram_bytes();

} // namespace dottalk::vdisk
