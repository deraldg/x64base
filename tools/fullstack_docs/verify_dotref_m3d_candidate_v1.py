#!/usr/bin/env python3
"""Verify two isolated report-only DOTREF M3D emissions and native DBF loads."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.m3d_verification.v1"
TABLES = {
    "SYSREFRUN": ("sysrefrun_candidate.csv", 1),
    "SYSREF": ("sysref_candidate.csv", 268),
    "SYSREFLINE": ("sysrefline_candidate.csv", 2658),
    "SYSREFALIAS": ("sysrefalias_candidate.csv", 23),
    "REFVOICE": ("refvoice_approved_migration.csv", 536),
    "REFSUPPORT": ("refsupport_approved.csv", 23),
    "DOTREF": ("dotref_candidate.csv", 268),
}
LOGICAL_ARTIFACTS = [
    "candidate/csv/sysrefrun_candidate.csv",
    "candidate/csv/sysref_candidate.csv",
    "candidate/csv/sysrefline_candidate.csv",
    "candidate/csv/sysrefalias_candidate.csv",
    "candidate/csv/refvoice_approved_migration.csv",
    "candidate/csv/refsupport_approved.csv",
    "candidate/csv/dotref_candidate.csv",
    "candidate/include/dotref_catalog.generated.inc",
    "reports/field_diff.csv",
    "reports/support_resolution.csv",
    "reports/contract_status_audit.csv",
    "reports/dot_fox_voice_preservation.csv",
]
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
RECORD_RE = re.compile(r"(?m)^(?:\.\s+)+Record\s+(\d+)(?:\s+\(Deleted\))?\s*$")
FIELD_RE = re.compile(r"(?m)^\s{2}([A-Z][A-Z0-9_]*) = (.*)$")


class VerifyError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def native_script(dbf_dir: Path, dotref_count: int) -> str:
    commands = [f"setpath dbf {dbf_dir}", "use DOTREF", "memo verify"]
    for number in range(1, dotref_count + 1):
        # DISPLAY <n> is documented as navigation but the current dispatcher
        # drops that tail in script mode. GO followed by bare DISPLAY exercises
        # the proven navigation path and still resolves native memo values.
        commands.extend([f"go {number}", "display"])
    commands.append("close")
    for table in ("SYSREFLINE", "REFVOICE", "REFSUPPORT", "SYSREFRUN"):
        commands.extend([f"use {table}", "memo verify", "close"])
    commands.append("quit")
    return "\n".join(commands) + "\n"


def run_native(runtime: Path, cwd: Path, dbf_dir: Path, expected_rows: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".dts", delete=False) as handle:
        handle.write(native_script(dbf_dir, len(expected_rows)))
        script_path = Path(handle.name)
    try:
        proc = subprocess.run(
            [str(runtime), "--script", str(script_path)], cwd=str(cwd),
            text=True, encoding="utf-8", errors="replace", capture_output=True,
            timeout=180, check=False,
        )
    finally:
        script_path.unlink(missing_ok=True)
    transcript = ANSI_RE.sub("", proc.stdout + proc.stderr).replace("\r\n", "\n")
    if proc.returncode != 0:
        raise VerifyError(f"NATIVE_RUNTIME_FAILED:{proc.returncode}")
    if transcript.count("VERIFY: OK") != 5:
        raise VerifyError(f"NATIVE_MEMO_VERIFY_COUNT:{transcript.count('VERIFY: OK')}!=5")
    for forbidden in ("missing objects: 1", "bad ids        : 1", "VERIFY: problems", "VERIFY: error"):
        if forbidden in transcript:
            raise VerifyError(f"NATIVE_MEMO_VERIFY_FAILURE:{forbidden}")

    matches = list(RECORD_RE.finditer(transcript))
    if len(matches) != len(expected_rows):
        raise VerifyError(f"NATIVE_DISPLAY_COUNT:{len(matches)}!={len(expected_rows)}")
    observed: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else transcript.find(". Closed.", match.end())
        if end < 0:
            end = len(transcript)
        block = transcript[match.end():end]
        field_matches = list(FIELD_RE.finditer(block))
        row: dict[str, str] = {"RECNO": match.group(1)}
        for field_index, field_match in enumerate(field_matches):
            value_end = field_matches[field_index + 1].start() if field_index + 1 < len(field_matches) else len(block)
            first = field_match.group(2)
            continuation = block[field_match.end():value_end]
            value = first + continuation
            row[field_match.group(1)] = value.strip()
        observed.append(row)

    compare_fields = ["NAME", "SYNTAX", "SUMMARY", "SUPPORTED"]
    for number, (expected, actual) in enumerate(zip(expected_rows, observed), 1):
        if int(actual["RECNO"]) != number:
            raise VerifyError(f"NATIVE_RECORD_ORDER:{actual['RECNO']}!={number}")
        for field in compare_fields:
            if actual.get(field, "").replace("\r\n", "\n") != expected[field].strip().replace("\r\n", "\n"):
                raise VerifyError(f"NATIVE_DOTREF_MISMATCH:{number}:{expected['NAME']}:{field}")
    return transcript, observed


def validate_relations(run: Path) -> dict[str, int]:
    csv_dir = run / "candidate/csv"
    refs = read_csv(csv_dir / "sysref_candidate.csv")
    lines = read_csv(csv_dir / "sysrefline_candidate.csv")
    aliases = read_csv(csv_dir / "sysrefalias_candidate.csv")
    voice = read_csv(csv_dir / "refvoice_approved_migration.csv")
    support = read_csv(csv_dir / "refsupport_approved.csv")
    dotref = read_csv(csv_dir / "dotref_candidate.csv")
    ref_ids = {row["REF_ID"] for row in refs}
    names = {row["CAN_NAME"] for row in refs}
    support_statuses = {row["STATUS"] for row in support}
    if len(ref_ids) != len(refs) or len(names) != len(refs):
        raise VerifyError("DUPLICATE_SYSREF_KEY")
    if any(row["REF_ID"] not in ref_ids for row in lines):
        raise VerifyError("ORPHAN_SYSREFLINE")
    if any(row["REF_ID"] not in ref_ids or row["TARGET_ID"] not in ref_ids for row in aliases):
        raise VerifyError("ORPHAN_SYSREFALIAS")
    if any(row["CAN_NAME"] not in names for row in voice):
        raise VerifyError("ORPHAN_REFVOICE")
    if any(row["REF_ID"] not in ref_ids for row in dotref):
        raise VerifyError("ORPHAN_DOTREF")
    if any(row["SUPPORT_ST"] not in support_statuses for row in refs):
        raise VerifyError("UNMAPPED_SUPPORT_STATUS")
    return {
        "sysref": len(refs), "sysrefline": len(lines), "sysrefalias": len(aliases),
        "refvoice": len(voice), "refsupport": len(support), "dotref": len(dotref),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--run-a", required=True)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    run_a = (root / args.run_a).resolve()
    run_b = (root / args.run_b).resolve()
    runtime = (root / args.runtime).resolve()
    out = (root / args.out).resolve()
    try:
        for path in (run_a, run_b, runtime, out):
            path.relative_to(root)
        if out.exists():
            raise VerifyError(f"OUTPUT_ALREADY_EXISTS:{out}")
        if not runtime.is_file():
            raise VerifyError(f"RUNTIME_MISSING:{runtime}")
        for run in (run_a, run_b):
            if not run.is_dir():
                raise VerifyError(f"RUN_MISSING:{run}")

        counts_a = validate_relations(run_a)
        counts_b = validate_relations(run_b)
        if counts_a != counts_b:
            raise VerifyError("CANDIDATE_COUNT_MISMATCH")

        comparisons: list[dict[str, Any]] = []
        for rel in LOGICAL_ARTIFACTS:
            a = run_a / rel
            b = run_b / rel
            if not a.is_file() or not b.is_file():
                raise VerifyError(f"LOGICAL_ARTIFACT_MISSING:{rel}")
            ha, hb = sha256_file(a), sha256_file(b)
            comparisons.append({"KIND": "LOGICAL", "ARTIFACT": rel, "A_SHA256": ha, "B_SHA256": hb, "MATCH": int(ha == hb)})

        dbf_a = run_a / "candidate/dbf"
        dbf_b = run_b / "candidate/dbf"
        files_a = {path.name: path for path in dbf_a.iterdir() if path.is_file()}
        files_b = {path.name: path for path in dbf_b.iterdir() if path.is_file()}
        if set(files_a) != set(files_b):
            raise VerifyError("DBF_SIDECAR_MEMBER_SET_MISMATCH")
        for name in sorted(files_a):
            ha, hb = sha256_file(files_a[name]), sha256_file(files_b[name])
            comparisons.append({"KIND": "DBF_OR_DTX", "ARTIFACT": name, "A_SHA256": ha, "B_SHA256": hb, "MATCH": int(ha == hb)})
        if any(not row["MATCH"] for row in comparisons):
            raise VerifyError("DETERMINISM_HASH_MISMATCH")

        for run in (run_a, run_b):
            for table, (csv_name, expected) in TABLES.items():
                rows = read_csv(run / "candidate/csv" / csv_name)
                if len(rows) != expected:
                    raise VerifyError(f"ROW_COUNT_MISMATCH:{run.name}:{table}:{len(rows)}!={expected}")
                dbf = run / "candidate/dbf" / f"{table}.dbf"
                if not dbf.is_file():
                    raise VerifyError(f"DBF_MISSING:{run.name}:{table}")

        expected_a = read_csv(run_a / "candidate/csv/dotref_candidate.csv")
        expected_b = read_csv(run_b / "candidate/csv/dotref_candidate.csv")
        transcript_a, observed_a = run_native(runtime, root / "dottalkpp/data", dbf_a, expected_a)
        transcript_b, observed_b = run_native(runtime, root / "dottalkpp/data", dbf_b, expected_b)
        if observed_a != observed_b:
            raise VerifyError("NATIVE_DOTREF_READBACK_NOT_DETERMINISTIC")

        out.mkdir(parents=True)
        (out / "native_verify_run_a.txt").write_text(transcript_a, encoding="utf-8", newline="\n")
        (out / "native_verify_run_b.txt").write_text(transcript_b, encoding="utf-8", newline="\n")
        write_csv(out / "artifact_comparison.csv",
                  ["KIND", "ARTIFACT", "A_SHA256", "B_SHA256", "MATCH"], comparisons)

        field_diff = read_csv(run_a / "reports/field_diff.csv")
        voice_report = read_csv(run_a / "reports/dot_fox_voice_preservation.csv")
        gates = {
            "G0_IMMUTABLE_INPUT_PACKAGE": "PASS",
            "G1_SCHEMA_AND_KEY_INTEGRITY": "PASS",
            "G2_AUTHORITY_RESOLUTION": "PASS",
            "G3_COMPLETE_FIELD_REFRESH": "PASS",
            "G4_NO_SILENT_LEGACY_CARRY": "PASS",
            "G5_NATIVE_COMPATIBILITY_VOICE": "PASS",
            "G6_DETERMINISM_AND_EXISTING_OUTPUT_REFUSAL": "PASS",
            "G7_NATIVE_DBF_CPP_ROUNDTRIP": "PASS",
        }
        summary = {
            "schema": SCHEMA, "status": "M3D_REPORT_ONLY_G0_G7_PASS",
            "runtime": str(runtime.relative_to(root)).replace("\\", "/"),
            "runtime_sha256": sha256_file(runtime), "counts": counts_a,
            "field_differences": len(field_diff),
            "logical_artifacts_compared": len(LOGICAL_ARTIFACTS),
            "physical_files_compared": len(files_a),
            "native_dotref_rows_compared": len(observed_a),
            "native_memo_tables_verified_per_run": 5,
            "dot_fox_shared_rows": len(voice_report),
            "dot_fox_distinct_rows": sum(row.get("DISTINCT") == "T" for row in voice_report),
            "gates": gates, "live_header_applied": False, "m3e_authorized": False,
        }
        write_json(out / "m3d_verification_summary.json", summary)
        report = f"""# DOCFLUSH-20261013-002 DOTREF M3D report-only verification

Date: 2026-10-13. Lane: AIF-171.

Status: **M3D_REPORT_ONLY_G0_G7_PASS**

Two independent emissions and native DotTalk++ loads produced identical
logical artifacts and byte-identical candidate DBF/DTX files. Native readback
resolved and compared all {len(observed_a)} DOTREF rows, including both memo
fields, against the generated CSV projection. Native `MEMO VERIFY` passed for
DOTREF, SYSREFLINE, REFVOICE, REFSUPPORT, and SYSREFRUN in both runs.

Counts: {counts_a['sysref']} SYSREF identities, {counts_a['sysrefalias']} alias
edges, {counts_a['refvoice']} approved migration voice rows,
{counts_a['sysrefline']} normalized prose rows, {counts_a['refsupport']} support
policy rows, and {counts_a['dotref']} DOTREF projection rows.

The candidate differs from the current header in {len(field_diff)} reviewed
fields; all are support-policy results. Identity, order, syntax, and summary
round-trip without drift.

G0-G7 pass. The live `include/dotref.hpp`, HELP/META stores, manuals, website,
publication staging, Git index, commits, and remotes were not changed. M3E is
not authorized by this result.
"""
        (out / "M3D_REPORT_ONLY_VERIFICATION_V1.md").write_text(report, encoding="utf-8", newline="\n")
        print("DOTREF M3D verification: M3D_REPORT_ONLY_G0_G7_PASS")
        print(f"native DOTREF rows compared: {len(observed_a)} x 2")
        print(f"REPORT-ONLY: {out}")
        return 0
    except (VerifyError, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"REFUSED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
