#!/usr/bin/env python3
"""Classify current dotref.hpp against one hash-bound SYSREF candidate.

M3C is report-only. It reuses the existing brace/quote-aware header parser,
folds the normalized SYSREF/SYSREFLINE CSVs into the current four-field DOTREF
shape, and emits field-level review rows. It never writes a header or live
metadata. Any member or field difference is review-required and therefore
blocks M3D emission until a later reviewed-disposition input exists.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.m3c_migration_report.v1"
PROJECTION_FIELDS = [
    "NAME", "SYNTAX", "SUMMARY", "SUPPORTED", "SRC_HASH", "REVIEW_ST", "ACTIVE",
]
DIFF_FIELDS = [
    "NAME", "MEMBER_CLASS", "FIELD", "CURRENT_VALUE", "CANDIDATE_VALUE",
    "CLASSIFICATION", "BLOCKING", "DETAIL",
]


class MigrationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_header_parser():
    path = Path(__file__).resolve().parents[2] / "dottalkpp/tools/help/generate_dotref_from_metadata_v1.py"
    spec = importlib.util.spec_from_file_location("dotref_metadata_parser_v1", path)
    if spec is None or spec.loader is None:
        raise MigrationError(f"HEADER_PARSER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{(key or "").strip().upper(): (value or "") for key, value in row.items()}
                for row in csv.DictReader(handle)]


def fold_projection(assembly: Path) -> list[dict[str, str]]:
    refs_path = assembly / "candidate/sysref_candidate.csv"
    lines_path = assembly / "candidate/sysrefline_candidate.csv"
    if not refs_path.is_file() or not lines_path.is_file():
        raise MigrationError("ASSEMBLY_CANDIDATE_MISSING")
    refs = read_csv(refs_path)
    lines = read_csv(lines_path)
    by_ref: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in lines:
        if row.get("ACTIVE", "").upper() in {"T", "TRUE", "1", "YES"}:
            by_ref[row.get("REF_ID", "")].append(row)

    out: list[dict[str, str]] = []
    for ref in sorted(refs, key=lambda row: row.get("CAN_NAME", "")):
        if ref.get("ACTIVE", "").upper() not in {"T", "TRUE", "1", "YES"}:
            continue
        children = sorted(
            by_ref.get(ref.get("REF_ID", ""), []),
            key=lambda row: (row.get("KIND", ""), int(row.get("ORDINAL", "0") or 0)),
        )
        syntax = " | ".join(row["TEXT"] for row in children if row.get("KIND") == "SYNTAX")
        summaries = [row["TEXT"] for row in children if row.get("KIND") == "SUMMARY"]
        summary = " ".join(summaries)
        contribution = json.dumps(
            {"ref": ref, "lines": children}, sort_keys=True, ensure_ascii=True, separators=(",", ":")
        ).encode("utf-8")
        out.append({
            "NAME": ref.get("CAN_NAME", ""),
            "SYNTAX": syntax,
            "SUMMARY": summary,
            "SUPPORTED": ref.get("SUPPORTED", "F"),
            "SRC_HASH": hashlib.sha256(contribution).hexdigest().upper(),
            "REVIEW_ST": "CANDIDATE",
            "ACTIVE": "T",
        })
    return out


def classify(current_items: list[Any], candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    current = {item.name.strip().upper(): item for item in current_items}
    proposed = {row["NAME"].strip().upper(): row for row in candidates}
    rows: list[dict[str, str]] = []
    for name in sorted(set(current) | set(proposed)):
        old = current.get(name)
        new = proposed.get(name)
        if old is None:
            rows.append({
                "NAME": name, "MEMBER_CLASS": "CANDIDATE_ONLY", "FIELD": "MEMBER",
                "CURRENT_VALUE": "", "CANDIDATE_VALUE": "present",
                "CLASSIFICATION": "NEW_IDENTITY_REVIEW_REQUIRED", "BLOCKING": "T",
                "DETAIL": "Source-derived identity is absent from the current compiled header.",
            })
            continue
        if new is None:
            rows.append({
                "NAME": name, "MEMBER_CLASS": "HEADER_ONLY", "FIELD": "MEMBER",
                "CURRENT_VALUE": "present", "CANDIDATE_VALUE": "",
                "CLASSIFICATION": "HEADER_ONLY_REVIEW_REQUIRED", "BLOCKING": "T",
                "DETAIL": "Current header evidence is not represented by this command-only candidate.",
            })
            continue
        pairs = (
            ("SYNTAX", old.syntax, new["SYNTAX"]),
            ("SUMMARY", old.summary, new["SUMMARY"]),
            ("SUPPORTED", "T" if old.supported else "F", new["SUPPORTED"]),
        )
        for field, old_value, new_value in pairs:
            same = old_value == new_value
            rows.append({
                "NAME": name, "MEMBER_CLASS": "BOTH", "FIELD": field,
                "CURRENT_VALUE": old_value, "CANDIDATE_VALUE": new_value,
                "CLASSIFICATION": "ALIGNED" if same else "FIELD_REVIEW_REQUIRED",
                "BLOCKING": "F" if same else "T",
                "DETAIL": "Exact field match." if same else "Current compiled wording/state differs from source-derived candidate.",
            })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--assembly", required=True)
    parser.add_argument("--header", default="include/dotref.hpp")
    parser.add_argument("--out", required=True)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    assembly = (root / args.assembly).resolve()
    header = (root / args.header).resolve()
    out = (root / args.out).resolve()
    try:
        assembly.relative_to(root)
        header.relative_to(root)
        out.relative_to(root)
        if out.exists():
            raise MigrationError(f"OUTPUT_ALREADY_EXISTS:{out}")
        if not header.is_file():
            raise MigrationError(f"HEADER_MISSING:{header}")
        gate_path = assembly / "reports/gate_results.json"
        gates = json.loads(gate_path.read_text(encoding="utf-8"))
        if gates.get("gates", {}).get("G2_AUTHORITY_RESOLUTION") != "PASS":
            raise MigrationError("ASSEMBLY_G2_NOT_PASS")

        parser_module = load_header_parser()
        _prefix, current_items, _suffix = parser_module.parse_header(header.read_text(encoding="utf-8"))
        projection = fold_projection(assembly)
        diffs = classify(current_items, projection)
        blockers = sum(1 for row in diffs if row["BLOCKING"] == "T")
        out.mkdir(parents=True)
        write_csv(out / "candidate/dotref_projection_candidate.csv", PROJECTION_FIELDS, projection)
        write_csv(out / "reports/current_header_migration.csv", DIFF_FIELDS, diffs)
        write_csv(out / "reports/field_diff.csv", DIFF_FIELDS, [row for row in diffs if row["CLASSIFICATION"] != "ALIGNED"])
        report = {
            "schema": SCHEMA,
            "mode": "REPORT_ONLY",
            "live_mutation": False,
            "assembly": Path(args.assembly).as_posix(),
            "assembly_gate_sha256": sha256_file(gate_path),
            "header": Path(args.header).as_posix(),
            "header_sha256": sha256_file(header),
            "current_members": len(current_items),
            "candidate_members": len(projection),
            "field_rows": len(diffs),
            "blocking_review_rows": blockers,
            "status": "REVIEW_REQUIRED" if blockers else "READY_FOR_M3D",
            "generated_header": False,
        }
        (out / "reports/migration_summary.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        print(
            f"DOTREF M3C: {report['status']} -- current={len(current_items)} "
            f"candidate={len(projection)} blocking_rows={blockers}"
        )
        print(f"REPORT-ONLY: {out}")
        return 0 if not blockers else 2
    except (MigrationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
