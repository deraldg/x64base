from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# Licensing was UNDECIDED when this gate was written (2026-07-14): it asserted that
# LICENSE read exactly "To be determined." and that README said the same. The project
# decided on 2026-08-08 (LICENSING.md, "decided 2026-08-08"), GPL-3.0 text landed
# 2026-08-11 in 2dbc29c8f -- and nobody came back here. The gate then failed CI on
# public main for the correct repository state, which is the worst way for a gate to
# fail: it was not reporting drift, it WAS the drift.
#
# So these checks now assert the decided posture. They are deliberately still checks
# and not deletions -- the point of the gate is that the public repo's license story
# cannot quietly change, and that is as true after a decision as before one.
OBSOLETE_LICENSE_WORDING = ("To be determined.", "To be defined", "All rights reserved")

license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
require("GNU GENERAL PUBLIC LICENSE" in license_text, "LICENSE must carry the GNU GPL text")
require("Version 3, 29 June 2007" in license_text, "LICENSE must be GPL version 3 specifically")
for phrase in OBSOLETE_LICENSE_WORDING:
    require(phrase not in license_text, f"LICENSE contains obsolete wording: {phrase!r}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("`main` is the canonical public source" in readme, "README must identify public main as canonical")
require("dual-licensed" in readme, "README must state that the project is dual-licensed")
require("GPL-3.0-only" in readme, "README must name the open license exactly")
require("LICENSING.md" in readme, "README must point to the full licensing terms")
for phrase in OBSOLETE_LICENSE_WORDING:
    require(phrase not in readme, f"README contains obsolete license wording: {phrase!r}")

# The two files have to agree with each other, not merely each be well-formed.
licensing = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
require("GPL-3.0" in licensing, "LICENSING.md must name the same open license as README")
require("commercial" in licensing.lower(), "LICENSING.md must describe the commercial arm of the dual license")

cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
require("C:/Users/" not in cmake and "D:/code/" not in cmake, "CMake contains a personal machine path")
match = re.search(r"cmake_minimum_required\(VERSION\s+(\d+)\.(\d+)", cmake)
require(match is not None, "CMake minimum version was not found")

presets = json.loads((ROOT / "CMakePresets.json").read_text(encoding="utf-8"))
minimum = presets["cmakeMinimumRequired"]
if match:
    require(
        (int(match.group(1)), int(match.group(2)))
        == (minimum["major"], minimum["minor"]),
        "CMakeLists and CMakePresets minimum versions disagree",
    )

commit = (ROOT / "src/cli/cmd_commit.cpp").read_text(encoding="utf-8")
require("buffer retained for retry" in commit, "COMMIT does not document retained retry state")
require("(void)auto_reindex_if_needed" not in commit, "COMMIT discards the index finalization result")
memo_failure = commit.find("failed during memo flush")
buffer_clear = commit.find("tb.clear()", memo_failure)
require(memo_failure >= 0 and buffer_clear > memo_failure, "COMMIT clears state before handling memo failure")

sftp = (ROOT / "src/cli/cmd_sftp.cpp").read_text(encoding="utf-8")
require(
    'authorize_external_process("SFTP", true)' in sftp,
    "SFTP bypasses the shared external-process/network policy",
)

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("Public-source policy checks passed.")
