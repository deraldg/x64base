#pragma once

// ENGINE SCRATCH TABLES, AND THE ONE PLACE THAT NAMES THEM.
//
// A FIELDMGR restructure writes two extra tables beside the real one:
//
//     STUDENTS.dbf  ->  STUDENTS.__fldtmp.dbf   (the rewrite in progress)
//                       STUDENTS.__fldbak.dbf   (the pre-change backup, KEPT)
//
// Both keep the .dbf extension, so every extension-only scan saw them as
// tables. Measured 2026-08-26: `git grep fldbak -- src/` returned exactly one
// line outside a test comment -- the line that CREATES it. The convention had
// a writer and no readers.
//
// What that cost, measured by running the pre-change binary against a
// directory holding REALTAB.dbf plus the two scratch forms:
//
//     Area 0: opened 'REALTAB.__fldbak.dbf'    <- the BACKUP is the ACTIVE area
//     Area 1: opened 'REALTAB.__FLDTMP.dbf'
//     Area 2: opened 'REALTAB.dbf'
//
// The scan sorts by filename and `.__fldbak` sorts before `.dbf`, so the backup
// did not merely tag along -- it took area 0 and shifted every area number
// after it. A posture saved from that state records a backup as the active
// table; a MINIDB save then carries its bytes into the container
// (STUDENTS.__fldbak.dbf, 22,425 bytes, 17% of one observed payload) and
// WRITEBACK puts it back on disk.
//
// The markers live here so the WRITER and every READER share one spelling. Add
// a new scratch form by adding it HERE, not beside its writer -- that is the
// whole point of this header.

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <string>
#include <string_view>

namespace dottalk {

inline constexpr std::string_view kFieldMgrBackupMarker = ".__fldbak";
inline constexpr std::string_view kFieldMgrTempMarker   = ".__fldtmp";

/// True when this path names a table the ENGINE wrote for its own use.
///
/// The marker is a trailing segment of the STEM, not of the extension:
/// `STUDENTS.__fldbak.dbf` has stem `STUDENTS.__fldbak` and extension `.dbf`.
/// Compared case-insensitively -- these live on a case-insensitive filesystem
/// and a guard that missed `.__FLDBAK.DBF` would have a hole in exactly the
/// case nobody tests. The verification run used one upper-case form for that
/// reason.
inline bool is_engine_scratch_table(const std::filesystem::path& path)
{
    std::string stem = path.stem().string();
    std::transform(stem.begin(), stem.end(), stem.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

    for (const std::string_view marker : {kFieldMgrBackupMarker, kFieldMgrTempMarker}) {
        if (stem.size() >= marker.size() &&
            stem.compare(stem.size() - marker.size(), marker.size(), marker) == 0) {
            return true;
        }
    }
    return false;
}

}  // namespace dottalk
