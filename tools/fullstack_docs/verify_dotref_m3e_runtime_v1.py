#!/usr/bin/env python3
"""Run the AIF-171 DOTREF M3E build, runtime, parity, and rollback proof."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.m3e_verification.v1"
EXPECTED_POST_HEADER_SHA256 = "0FAB5B3AAED1B6C0AA0AAE81C1F0C6406CFFD597A2DF6555824DD9DBB9D91243"
EXPECTED_PRE_HEADER_SHA256 = "F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5"
EXPECTED_CANDIDATE_CSV_SHA256 = "70E3AE34B43105E3EB0818731107E9DCEC5E7189B4CB9B9240C3C3BA5F38AF73"


class VerificationError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require_file(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"PATH_OUTSIDE_REPOSITORY:{path}") from exc
    if not path.is_file():
        raise VerificationError(f"INPUT_MISSING:{path}")
    return path


def write_text_new(path: Path, value: str) -> None:
    if path.exists():
        raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_bytes_new(path: Path, value: bytes) -> None:
    if path.exists():
        raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    write_text_new(
        path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    )


def run_capture(command: list[str], cwd: Path, log: Path) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    write_bytes_new(log, completed.stdout)
    if completed.returncode != 0:
        raise VerificationError(
            f"COMMAND_FAILED:{completed.returncode}:{' '.join(command)}:{log}"
        )
    return completed


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [{(key or "").strip().upper(): (value or "") for key, value in row.items()}
                for row in csv.DictReader(handle)]
    names = [row.get("NAME", "").strip() for row in rows]
    if len(names) != 268 or len(set(names)) != 268 or any(not name for name in names):
        raise VerificationError(f"INVALID_CANDIDATE_MEMBER_SET:{len(names)}:{len(set(names))}")
    return rows


def extract_structured_members(text: str, rows: list[dict[str, str]]) -> list[str]:
    syntax_by_name = {row["NAME"]: row["SYNTAX"] for row in rows}
    lines = text.splitlines()
    observed: list[str] = []
    for index, line in enumerate(lines[:-1]):
        syntax = syntax_by_name.get(line)
        if syntax is not None and lines[index + 1] == "  " + syntax:
            observed.append(line)
    return observed


def run_member_probe(
    root: Path, out: Path, executable: Path, rows: list[dict[str, str]],
    command_prefix: str, stem: str, allowed_missing: set[str] | None = None,
) -> dict[str, Any]:
    names = [row["NAME"] for row in rows]
    allowed_missing = allowed_missing or set()
    script = out / f"{stem}.dts"
    alternate = out / f"{stem}.log"
    console = out / f"{stem}.console.log"
    relative_alt = str(alternate.relative_to(root)).replace("/", "\\")
    lines = [
        "* AIF-171 M3E generated read-only member probe.",
        f"SET ALTERNATE TO {relative_alt}",
        "SET ALTERNATE ON",
    ]
    lines.extend(f"{command_prefix} {name}" for name in names)
    lines.extend(["SET ALTERNATE OFF", "QUIT"])
    write_text_new(script, "\n".join(lines) + "\n")
    run_capture([str(executable), "--script", str(script)], root, console)
    if not alternate.is_file():
        raise VerificationError(f"ALTERNATE_LOG_MISSING:{alternate}")
    text = alternate.read_text(encoding="utf-8", errors="replace")
    expected = [name for name in names if name not in allowed_missing]
    expected_set = set(expected)
    observed = extract_structured_members(text, rows)
    observed = [name for name in observed if name not in allowed_missing]
    if set(observed) != expected_set:
        raise VerificationError(
            f"{stem.upper()}_MEMBER_SET_DIFF:"
            f"missing={sorted(expected_set - set(observed))}:"
            f"unexpected={sorted(set(observed) - expected_set)}"
        )
    if observed != expected:
        raise VerificationError(f"{stem.upper()}_MEMBER_ORDER_DIFF")
    return {
        "members": len(observed),
        "allowed_router_exceptions": sorted(allowed_missing),
        "script_sha256": sha256_file(script),
        "alternate_sha256": sha256_file(alternate),
        "console_sha256": sha256_file(console),
    }


def verify_representative_consumers(
    log: Path, rows: list[dict[str, str]]
) -> dict[str, Any]:
    text = log.read_text(encoding="utf-8", errors="replace")
    forbidden = ["could not load current HELP DATA", "Unknown command:"]
    present_forbidden = [needle for needle in forbidden if needle in text]
    if present_forbidden:
        raise VerificationError(f"REPRESENTATIVE_RUNTIME_ERRORS:{present_forbidden}")
    required = [
        "(documented, but not fully supported yet)",
        "DOT|AUTODBF",
        "AUTODBF [USAGE|<source> [TO <dbf>]]",
        "DOT|COPY",
        "COPY USAGE | COPY TO <DBFNAME>",
        "DOT|DDICT",
        "DDICT OBJECTS [TYPE <type>] [PROFILE <profile>] [FAMILY LEGACY|X64]",
        "OK no structural issues found",
    ]
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise VerificationError(f"REPRESENTATIVE_RUNTIME_EVIDENCE_MISSING:{missing}")
    first_seen: list[str] = []
    seen: set[str] = set()
    for name in extract_structured_members(text, rows):
        if name not in seen:
            seen.add(name)
            first_seen.append(name)
    expected = [row["NAME"] for row in rows]
    if set(first_seen) != set(expected) or first_seen != expected:
        raise VerificationError(
            "DOTHELP_FULL_LIST_MEMBER_DIFF:"
            f"missing={sorted(set(expected) - set(first_seen))}:"
            f"unexpected={sorted(set(first_seen) - set(expected))}"
        )
    return {
        "sha256": sha256_file(log),
        "bytes": log.stat().st_size,
        "required_markers": len(required),
        "forbidden_markers": 0,
        "dothelp_full_list_members": len(first_seen),
    }


def run_rollback_drill(root: Path, out: Path, apply_tool: Path, header: Path, backup: Path) -> dict[str, Any]:
    drill = out / "rollback_drill"
    if drill.exists():
        raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{drill}")
    (drill / "include").mkdir(parents=True)
    (drill / "backup/include").mkdir(parents=True)
    shutil.copyfile(header, drill / "include/dotref.hpp")
    shutil.copyfile(backup, drill / "backup/include/dotref.hpp")
    manifest = {
        "schema": "dottalk.dotref.m3e_promotion.v1",
        "status": "APPLIED_AND_READ_BACK",
        "pre_header_sha256": EXPECTED_PRE_HEADER_SHA256,
        "post_header_sha256": EXPECTED_POST_HEADER_SHA256,
        "backup_path": "backup/include/dotref.hpp",
    }
    (drill / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    rollback_log = out / "g9_rollback_drill.log"
    run_capture(
        [sys.executable, str(apply_tool), "--root", str(drill), "--rollback",
         "--manifest", "manifest.json"],
        root, rollback_log,
    )
    restored = drill / "include/dotref.hpp"
    if sha256_file(restored) != EXPECTED_PRE_HEADER_SHA256:
        raise VerificationError("ROLLBACK_DRILL_READBACK_MISMATCH")
    updated = json.loads((drill / "manifest.json").read_text(encoding="utf-8"))
    if updated.get("status") != "ROLLED_BACK_AND_READ_BACK":
        raise VerificationError("ROLLBACK_DRILL_MANIFEST_NOT_CLOSED")
    return {
        "status": updated["status"],
        "restored_sha256": sha256_file(restored),
        "log_sha256": sha256_file(rollback_log),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidate-csv", required=True)
    ap.add_argument("--promotion-manifest", required=True)
    ap.add_argument("--representative-log", required=True)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    out = (root / args.out).resolve()
    try:
        out.relative_to(root)
        if not out.is_dir():
            raise VerificationError(f"OUTPUT_DIRECTORY_MISSING:{out}")
        summary_path = out / "m3e_verification_summary.json"
        if summary_path.exists():
            raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{summary_path}")

        candidate_csv = require_file(root, args.candidate_csv)
        manifest_path = require_file(root, args.promotion_manifest)
        representative_log = require_file(root, args.representative_log)
        header = require_file(root, "include/dotref.hpp")
        apply_tool = require_file(root, "tools/fullstack_docs/apply_dotref_m3e_promotion_v1.py")
        executable = require_file(root, "build/src/Release/dottalkpp.exe")
        metacollect = require_file(root, "build/Release/metacollect.exe")
        if sha256_file(candidate_csv) != EXPECTED_CANDIDATE_CSV_SHA256:
            raise VerificationError("CANDIDATE_CSV_HASH_MISMATCH")
        if sha256_file(header) != EXPECTED_POST_HEADER_SHA256:
            raise VerificationError("POST_APPLY_HEADER_HASH_MISMATCH")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "APPLIED_AND_READ_BACK":
            raise VerificationError("PROMOTION_MANIFEST_NOT_APPLIED")
        backup = require_file(root, manifest["backup_path"])
        if sha256_file(backup) != EXPECTED_PRE_HEADER_SHA256:
            raise VerificationError("PROMOTION_BACKUP_HASH_MISMATCH")

        build_logs = {}
        for target, log_name in (
            ("metacollect", "g8_build_metacollect.log"),
            ("dottalkpp", "g8_build_dottalkpp.log"),
        ):
            log = out / log_name
            run_capture(
                ["cmake", "--build", str(root / "build"), "--config", "Release",
                 "--target", target, "--parallel", "4"],
                root, log,
            )
            build_logs[target] = {"sha256": sha256_file(log), "bytes": log.stat().st_size}

        rows = read_rows(candidate_csv)
        names = [row["NAME"] for row in rows]
        dothelp = run_member_probe(
            root, out, executable, rows, "DOTHELP", "g8_dothelp_members",
            allowed_missing={"HELP", "VAR"},
        )
        browser = run_member_probe(
            root, out, executable, rows, "HELP /DOT", "g8_help_dot_members",
            allowed_missing={"PREDICATES"},
        )
        representative = verify_representative_consumers(representative_log, rows)

        test_commands = [
            ([sys.executable, "-m", "unittest",
              "tools.fullstack_docs.tests.test_build_sysref_harvest_manifest_v1",
              "tools.fullstack_docs.tests.test_generate_sysref_candidate_v1",
              "tools.fullstack_docs.tests.test_classify_dotref_migration_v1",
              "tools.fullstack_docs.tests.test_build_dotref_migration_closure_v1",
              "tools.fullstack_docs.tests.test_emit_dotref_m3d_candidate_v1",
              "tools.fullstack_docs.tests.test_apply_dotref_m3e_promotion_v1", "-v"],
             "g8_focused_unittests.log"),
            ([sys.executable, "tools/fullstack_docs/refcheck_v1.py", "--root", ".", "--selftest"],
             "g8_refcheck_selftest.log"),
            ([sys.executable, "tools/fullstack_docs/refcheck_v1.py", "--root", "."],
             "g8_refcheck_live.log"),
            ([sys.executable, "tools/fullstack_docs/normcheck_v1.py", "."],
             "g8_normcheck.log"),
        ]
        validation_logs = {}
        for command, log_name in test_commands:
            log = out / log_name
            run_capture(command, root, log)
            validation_logs[log_name] = {"sha256": sha256_file(log), "bytes": log.stat().st_size}

        rollback = run_rollback_drill(root, out, apply_tool, header, backup)
        if sha256_file(header) != EXPECTED_POST_HEADER_SHA256:
            raise VerificationError("LIVE_HEADER_CHANGED_BY_ROLLBACK_DRILL")

        summary = {
            "schema": SCHEMA,
            "run_id": "DOCFLUSH-20261013-002",
            "status": "M3E_G8_G9_PASS",
            "gates": {
                "G8_BUILD_AND_RUNTIME_PARITY": "PASS",
                "G9_PROMOTION_AND_ROLLBACK": "PASS",
            },
            "header_sha256": sha256_file(header),
            "backup_sha256": sha256_file(backup),
            "promotion_manifest_sha256": sha256_file(manifest_path),
            "candidate_csv_sha256": sha256_file(candidate_csv),
            "metacollect_sha256": sha256_file(metacollect),
            "dottalkpp_sha256": sha256_file(executable),
            "build_logs": build_logs,
            "dothelp_member_probe": dothelp,
            "help_dot_member_probe": browser,
            "representative_consumers": representative,
            "validation_logs": validation_logs,
            "rollback_drill": rollback,
            "member_set_count": len(names),
            "approved_field_difference_count": 22,
            "runtime_advisories": [
                "DOTHELP HELP is reserved by DOTHELP as its usage token; HELP /DOT HELP resolves it.",
                "DOTHELP VAR is intercepted by try_handle_var_command because it treats any second token VAR as SET/SHOW/CLEAR VAR; HELP /DOT VAR resolves it.",
                "HELP /DOT PREDICATES is diverted by help_router predOnly precedence; the full DOTHELP list still carries the member.",
            ],
            "live_help_meta_manual_website_mutation": False,
            "commit_or_push": False,
        }
        write_json_new(summary_path, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (VerificationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
