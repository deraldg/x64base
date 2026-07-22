// src/cli/cmd_vdisk.cpp
// VDISK — the in-process RAM virtual disk for in-memory tables (AIF-043).
//
//   VDISK USAGE          -> print the structured usage/notes contract.
//   VDISK MOUNT | ON     -> point DBF/INDEXES/LMDB under the RAM slot and mount it
//                           as a ramfs virtual root. CREATE/USE/CDX then live in RAM.
//   VDISK UNMOUNT | OFF  -> drop all RAM files + unmount (ephemeral teardown).
//   VDISK STATUS |       -> report the RAM root, mount state, file count, bytes.
//
// The RAM root is the relocatable Slot::RAM (default <DATA>/ram). Relocate with
//   SET PATH RAM <path>
// before VDISK MOUNT. Curated command contract: include/dotref.hpp (DOT|VDISK).

#include "xbase.hpp"
#include "xbase/ramfs.hpp"
#include "cli/command_output.hpp"
#include "cli/cmd_setpath.hpp"

#include <algorithm>
#include <cctype>
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

} // namespace

void cmd_VDISK(xbase::DbArea&, std::istringstream& iss)
{
    using dottalk::paths::Slot;
    using dottalk::paths::get_slot;
    using dottalk::paths::set_slot;

    std::string sub;
    iss >> sub;
    const std::string u = up_(sub);

    const fs::path ram = get_slot(Slot::RAM);

    if (u == "MOUNT" || u == "ON") {
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

    if (u == "STATUS" || u.empty()) {
        const bool is_mounted = !ram.empty() && xbase::ramfs::mounted(ram.string());
        cli::cmdout::print_note("VDISK", "RAM root  = " + ram.string() +
                                (is_mounted ? "  [mounted]" : "  [not mounted]"));
        cli::cmdout::print_note("VDISK", "RAM bytes = " +
                                std::to_string(xbase::ramfs::used_bytes()));
        if (is_mounted) {
            const auto files = xbase::ramfs::list(ram.string());
            cli::cmdout::print_note("VDISK", "RAM files = " + std::to_string(files.size()));
            for (const auto& f : files) {
                cli::cmdout::print_note("VDISK", "  " + f);
            }
        }
        return;
    }

    cli::cmdout::print_note("VDISK", "usage: VDISK MOUNT | UNMOUNT | STATUS");
}
