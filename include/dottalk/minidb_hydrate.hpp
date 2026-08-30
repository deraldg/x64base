// @dottalk.file v1
// subsystem: dottalk
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#pragma once

// AIF-120. Materialising a MINIDB 1 container, separated from whoever asks.
//
// This is the second half of the split R102 began. The scanner
// (dottalk/minidb.hpp) stays PURE -- no I/O, no dependencies -- and lives in
// its own header so that stays true. This header does the writing, so it
// depends on xbase::ramfs, and is deliberately not folded into the scanner.
//
// WHY IT HAD TO COME OUT OF THE CLI. hydrate_minidb lived in
// src/cli/cmd_workspace.cpp and reported through std::cout, so the only way to
// hydrate was to be the CLI. The GUI's shell bridge runs dottalkpp as a CHILD
// PROCESS, and xbase::ramfs is by its own header "an in-process RAM
// filesystem" with "a process-global registry" -- so a container hydrated
// across that bridge lands in the child's memory, where the Workbench can
// never open it. Opening a MINIDB workspace in a window is therefore not a
// wiring problem; it requires hydrating in the caller's own process. Hence
// this header: same code, no process boundary, no std::cout.

#include "dottalk/minidb.hpp"
#include "xbase/ramfs.hpp"

#include <cctype>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <system_error>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace dottalk::minidb {

struct MaterializeResult {
    bool ok = false;
    std::string error;                    // set when !ok
    std::size_t files = 0;
    std::uint64_t bytes = 0;              // every member written, RAM and disk

    // REPORTED SEPARATELY BECAUSE THEY WENT TO DIFFERENT PLACES. Until
    // 2026-08-30 the caller printed `bytes` under the words "zero disk reads",
    // one line after this function had written some of them to a disk. The
    // split is not new information -- it is the branch below, finally counted.
    std::uint64_t ram_bytes = 0;          // landed in xbase::ramfs
    std::uint64_t sidecar_bytes = 0;      // landed on the real filesystem

    std::vector<std::string> notes;       // non-fatal remarks, caller may print
};

// Write every member of a scanned container into the RAM VFS rooted at
// `ram_root`, with "indexes/" members going to `ram_index_root`.
//
// Memo sidecars (.dtx/.dbt/.fpt) land on the REAL filesystem, not the VFS,
// so a sidecar written into the VFS would sit exactly where memo I/O never
// looks.
//
// CITATION CORRECTED 2026-08-30. This read "AIF-108 [SIDECAR] -- the DTX layer
// bypasses ramfs (bypass-ledger member 1)", and BOTH halves misdirect.
// AIF-108 is a TEST-DESIGN lane whose own status column reads "chartered -- NO
// engine change proposed"; the [SIDECAR] tag came from its challenge list and
// was carried into code as though it were a design authority. This file's own
// header says lane: AIF-120, which is where the finding is now recorded.
// AIF-108 is asleep until 2026-09-29 (OI-021). And "bypass-ledger member 1" is
// cited four times in this tree, always as member 1, with no member 2 and NO
// LEDGER DOCUMENT -- a confident pointer at a register nobody wrote.
//
// THE SPLIT IS DECIDED HERE, NOT BY "THE DTX LAYER". materialize() below
// branches on a three-extension whitelist. Anyone reading the old comment went
// looking in the memo backend for a behaviour that lives twenty lines from the
// budget check that does not know about it. The mount directory exists physically, so the sidecar is
// disk-resident beside the virtual DBF. When ramfs memo coverage lands, that
// branch collapses into the ordinary one.
inline MaterializeResult materialize(const std::string& payload,
                                    const Scan& scan,
                                    const std::filesystem::path& ram_root,
                                    const std::filesystem::path& ram_index_root) {
    MaterializeResult r;
    for (const auto& member : scan.files) {
        const std::string& rel = member.relpath;
        if (member.offset + member.length > payload.size()) {
            r.error = "member '" + rel + "' lies outside the payload";
            return r;
        }
        const std::filesystem::path dst = (rel.rfind("indexes/", 0) == 0)
            ? ram_index_root / std::filesystem::path(rel.substr(8))
            : ram_root / std::filesystem::path(rel);

        // ONE predicate, shared with the scanner (minidb.hpp). It used to be a
        // three-extension literal here and nowhere else, so the budget upstream
        // could not know this branch existed.
        const bool memo_sidecar = is_memo_sidecar(rel);

        if (memo_sidecar) {
            std::error_code ec;
            std::filesystem::create_directories(dst.parent_path(), ec);
            std::ofstream out(dst, std::ios::binary | std::ios::trunc);
            if (!out) {
                r.error = "cannot create sidecar file " + dst.string();
                return r;
            }
            out.write(payload.data() + member.offset,
                      static_cast<std::streamsize>(member.length));
            out.flush();
        } else {
            auto out = xbase::ramfs::open(dst.string(), /*create*/true);
            if (!out) {
                r.error = "cannot create RAM file " + dst.string();
                return r;
            }
            out->write(payload.data() + member.offset,
                       static_cast<std::streamsize>(member.length));
            out->flush();
        }
        ++r.files;
        r.bytes += member.length;
        (memo_sidecar ? r.sidecar_bytes : r.ram_bytes) += member.length;
    }
    r.ok = true;
    return r;
}

// Return the container's posture with its DBFROOT/IDXROOT/LMDBROOT lines
// replaced by the RAM roots, ready to be loaded.
//
// LMDBROOT is dropped and NOT re-added, which is correct rather than an
// oversight: LMDB is disk-backed, and a .cdx under a mounted ramfs root is
// served by the LMDB-free native CDX-V64 backend instead
// (xindex/index_manager.cpp routes on ramfs::is_virtual). The CLI says the
// same thing on every load -- "LMDBROOT: <path> (recorded, not applied)".
inline std::string repoint_posture_to_ram(const std::string& posture,
                                          const std::filesystem::path& ram_root,
                                          const std::filesystem::path& ram_index_root) {
    std::string out;
    std::istringstream scan(posture);
    std::string line;
    bool first = true;
    while (std::getline(scan, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        std::string low;
        low.reserve(line.size());
        for (char ch : line) {
            if (std::isspace(static_cast<unsigned char>(ch)) && low.empty()) continue;
            low.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
        }
        if (low.rfind("dbfroot ", 0) == 0 || low.rfind("idxroot ", 0) == 0 ||
            low.rfind("lmdbroot ", 0) == 0) {
            continue;
        }
        out += line;
        out += "\n";
        if (first) {
            out += "DBFROOT " + ram_root.string() + "\n";
            out += "IDXROOT " + ram_index_root.string() + "\n";
            first = false;
        }
    }
    return out;
}

} // namespace dottalk::minidb
