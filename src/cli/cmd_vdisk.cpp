// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_vdisk.cpp
// @dottalk.usage v1
// owner: DOT|VDISK
// command: VDISK
// category: storage
// status: supported
// noargs: report
// effect: mixed
// mutates: ramfs path-slots ephemeral-memory
// usage-access: VDISK USAGE
// summary:
//   Manage the in-process RAM virtual disk used by in-memory X64 DBF tables,
//   native CDX-V64 indexes, and related transient storage (AIF-043).
//
// usage:
//   VDISK USAGE
//   VDISK MOUNT
//   VDISK ON
//   VDISK UNMOUNT
//   VDISK OFF
//   VDISK CLEAR
//   VDISK STATUS
//   VDISK CONFIG
//
// notes:
//   MOUNT points DBF, INDEXES, and LMDB path slots under the relocatable RAM
//   slot, then mounts that root through xbase::ramfs.
//   CREATE X64, USE, CDX, SET ORDER, and REINDEX can then operate entirely in
//   process memory with no corresponding table or index file on disk.
//   UNMOUNT, OFF, and CLEAR drop every resident RAM file; VDISK is ephemeral.
//   STATUS reports the RAM root, mount state, byte use, and resident file list.
//   The default RAM root is <DATA>/ram; SET PATH RAM <path> relocates it before
//   mounting. The optional bin/vdisk.ini admin configuration is a local,
//   review-required extension until its source/config files are committed.
//   VDISK changes storage and path state but does not mutate records in an
//   already-open table merely by reporting status or configuration.
//
// risk:
//   loses_ephemeral_data: UNMOUNT, OFF, CLEAR
//   mutates_path_state: MOUNT, ON, UNMOUNT, OFF, CLEAR
//   writes_filesystem: no for RAM-resident table/index operations
//
// related:
//   SET PATH
//   CDX
//   SET ORDER
//   REINDEX
//
// @dottalk.end
//
// VDISK is the in-process RAM virtual disk for in-memory tables (AIF-043).
// Curated catalog entry: include/dotref.hpp (DOT|VDISK).

#include "xbase.hpp"
#include "xbase/ramfs.hpp"
#include "cli/command_output.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/vdisk_config.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

std::string up_(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

// bin/vdisk.ini -- sits alongside dottalkpp.ini / init.ini.
std::string vdisk_ini_path()
{
    return (dottalk::paths::get_slot(dottalk::paths::Slot::BIN) / "vdisk.ini").string();
}

std::string fmt_bytes(std::uint64_t n)
{
    const double b = static_cast<double>(n);
    char buf[64];
    if (b >= 1024.0 * 1024.0 * 1024.0)      std::snprintf(buf, sizeof buf, "%.2f GB", b / (1024.0*1024.0*1024.0));
    else if (b >= 1024.0 * 1024.0)          std::snprintf(buf, sizeof buf, "%.1f MB", b / (1024.0*1024.0));
    else if (b >= 1024.0)                   std::snprintf(buf, sizeof buf, "%.1f KB", b / 1024.0);
    else                                    std::snprintf(buf, sizeof buf, "%llu B", (unsigned long long)n);
    return buf;
}

} // namespace

void cmd_VDISK(xbase::DbArea&, std::istringstream& iss)
{
    using dottalk::paths::Slot;
    using dottalk::paths::get_slot;
    using dottalk::paths::set_slot;

    std::string sub;
    iss >> sub;
    const std::string u = up_(sub);

    // Optional admin config (bin/vdisk.ini). Absent/commented => cfg.present=false
    // and everything below behaves exactly as it did without the file.
    const dottalk::vdisk::VDiskConfig cfg =
        dottalk::vdisk::load_vdisk_config(vdisk_ini_path());

    // A configured `root` relocates the RAM root before we read Slot::RAM.
    if ((u == "MOUNT" || u == "ON") && cfg.present && !cfg.root.empty()) {
        set_slot(Slot::RAM, fs::path(cfg.root));
    }
    const fs::path ram = get_slot(Slot::RAM);

    if (u == "MOUNT" || u == "ON") {
        if (cfg.present && !cfg.enabled) {
            cli::cmdout::print_note("VDISK",
                "vdisk.ini: enabled=0 — RAM residency disabled by admin; not mounting");
            return;
        }
        if (ram.empty()) {
            cli::cmdout::print_note("VDISK", "RAM slot is empty; SET PATH RAM <path> first");
            return;
        }
        // Tables live directly under the RAM root; indexes/lmdb in siblings.
        const fs::path idx  = ram / "indexes";
        const fs::path lmdb = ram / "lmdb";
        set_slot(Slot::DBF, ram);
        set_slot(Slot::INDEXES, idx);
        set_slot(Slot::LMDB, lmdb);
        xbase::ramfs::mount(ram.string());

        cli::cmdout::print_note("VDISK", "RAM disk mounted (in-process VFS): " + ram.string());
        cli::cmdout::print_note("VDISK", "  DBF     -> " + ram.string());
        cli::cmdout::print_note("VDISK", "  INDEXES -> " + idx.string());
        cli::cmdout::print_note("VDISK", "  LMDB    -> " + lmdb.string());
        if (cfg.present) {
            cli::cmdout::print_note("VDISK", "  budget  ~ " +
                fmt_bytes(dottalk::vdisk::recommended_budget_bytes(cfg)) +
                " (mode=" + dottalk::vdisk::mode_name(cfg.mode) +
                ", on_full=" + dottalk::vdisk::on_full_name(cfg.on_full) + ")");
        }
        return;
    }

    if (u == "UNMOUNT" || u == "OFF" || u == "CLEAR") {
        xbase::ramfs::clear();
        cli::cmdout::print_note("VDISK", "RAM disk unmounted; all RAM files dropped");
        return;
    }

    if (u == "USAGE" || u == "HELP" || u == "?") {
        cli::cmdout::print_line("Usage:");
        cli::cmdout::print_line("  VDISK USAGE");
        cli::cmdout::print_line("  VDISK MOUNT | ON");
        cli::cmdout::print_line("  VDISK UNMOUNT | OFF | CLEAR");
        cli::cmdout::print_line("  VDISK STATUS");
        cli::cmdout::print_line("  VDISK CONFIG");
        cli::cmdout::print_line("Notes:");
        cli::cmdout::print_line("  - MOUNT points the DBF/INDEXES/LMDB path slots under the RAM slot");
        cli::cmdout::print_line("    (default data\\ram) and mounts it as an in-process xbase::ramfs root.");
        cli::cmdout::print_line("  - While mounted, CREATE X64, USE, and native CDX-V64 live in RAM;");
        cli::cmdout::print_line("    no files are written to disk.");
        cli::cmdout::print_line("  - UNMOUNT drops all RAM files and unmounts (ephemeral teardown).");
        cli::cmdout::print_line("  - STATUS reports the RAM root, mount state, bytes, and resident files.");
        cli::cmdout::print_line("  - Relocate the RAM root with SET PATH RAM <path> before MOUNT.");
        cli::cmdout::print_line("  - Typically activated via DO mem.");
        return;
    }

    if (u == "CONFIG" || u == "CONF") {
        cli::cmdout::print_note("VDISK", "config file = " + vdisk_ini_path());
        if (!cfg.present) {
            cli::cmdout::print_note("VDISK", "no [vdisk] block found — feature off (defaults in effect)");
            cli::cmdout::print_note("VDISK", "physical RAM = " + fmt_bytes(dottalk::vdisk::physical_ram_bytes()) +
                                    ", available = " + fmt_bytes(dottalk::vdisk::available_ram_bytes()));
            return;
        }
        cli::cmdout::print_note("VDISK", std::string("enabled   = ") + (cfg.enabled ? "1" : "0"));
        cli::cmdout::print_note("VDISK", "root      = " + (cfg.root.empty() ? std::string("(Slot::RAM default)") : cfg.root));
        cli::cmdout::print_note("VDISK", std::string("mode      = ") + dottalk::vdisk::mode_name(cfg.mode));
        cli::cmdout::print_note("VDISK", "size_mb   = " + std::to_string(cfg.size_mb) +
                                ", percent = " + std::to_string(cfg.percent));
        cli::cmdout::print_note("VDISK", "floor_mb  = " + std::to_string(cfg.floor_mb) +
                                ", ceil_mb = " + std::to_string(cfg.ceil_mb));
        cli::cmdout::print_note("VDISK", "warn_pct  = " + std::to_string(cfg.warn_pct) +
                                ", on_full = " + dottalk::vdisk::on_full_name(cfg.on_full));
        cli::cmdout::print_note("VDISK", "physical RAM = " + fmt_bytes(dottalk::vdisk::physical_ram_bytes()) +
                                ", available = " + fmt_bytes(dottalk::vdisk::available_ram_bytes()));
        cli::cmdout::print_note("VDISK", "Layer-1 recommended budget ~ " +
                                fmt_bytes(dottalk::vdisk::recommended_budget_bytes(cfg)));
        return;
    }

    if (u == "STATUS" || u.empty()) {
        const bool is_mounted = !ram.empty() && xbase::ramfs::mounted(ram.string());
        cli::cmdout::print_note("VDISK", "RAM root  = " + ram.string() +
                                (is_mounted ? "  [mounted]" : "  [not mounted]"));
        const std::uint64_t used = xbase::ramfs::used_bytes();
        cli::cmdout::print_note("VDISK", "RAM bytes = " + std::to_string(used) +
                                " (" + fmt_bytes(used) + ")");
        if (cfg.present) {
            // Layer-2 soft budget: warn when over the high-water mark.
            const std::uint64_t budget = dottalk::vdisk::recommended_budget_bytes(cfg);
            cli::cmdout::print_note("VDISK", "budget    = " + fmt_bytes(budget) +
                                    " (mode=" + dottalk::vdisk::mode_name(cfg.mode) + ")");
            if (budget) {
                const std::uint64_t pct = used * 100 / budget;
                if (pct >= cfg.warn_pct) {
                    cli::cmdout::print_note("VDISK", "WARNING: RAM disk " + std::to_string(pct) +
                        "% full (" + fmt_bytes(used) + " / " + fmt_bytes(budget) +
                        ") — on_full=" + dottalk::vdisk::on_full_name(cfg.on_full));
                }
            }
        }
        if (is_mounted) {
            const auto files = xbase::ramfs::list(ram.string());
            cli::cmdout::print_note("VDISK", "RAM files = " + std::to_string(files.size()));
            for (const auto& f : files) {
                cli::cmdout::print_note("VDISK", "  " + f);
            }
        }
        return;
    }

    cli::cmdout::print_note("VDISK", "usage: VDISK MOUNT | UNMOUNT | STATUS | CONFIG");
}
