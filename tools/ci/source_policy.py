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


license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
require("TENTATIVE MIT LICENSE" in license_text, "LICENSE must retain its tentative status")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
require("`main` is the canonical public source" in readme, "README must identify public main as canonical")
require("To be defined" not in readme, "README contains obsolete undefined-license wording")

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
