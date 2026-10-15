#!/usr/bin/env python3
"""Apply or roll back the hash-bound AIF-171 DOTREF M3E promotion.

The apply path replaces only the catalog initializer row region in
include/dotref.hpp. It preserves the existing prefix and suffix byte content,
writes an exact backup, and refuses drift in the repository revision, reviewed
artifacts, live header, member order, or approved field-difference set.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.m3e_promotion.v1"
RUN_ID = "DOCFLUSH-20261013-002"
EXPECTED_REPO_SHA = "A48A709E968D8C208B6C19BD699028F0D25ADE3E"
EXPECTED_BRANCH = "development"
EXPECTED_GATE_SHA256 = "DEEC42244DC5FC2A193F8E53F5348750DBAB86234458F5DC4A06C26FC2C9035B"
EXPECTED_AUTHORIZATION_SHA256 = "AFA2FA0A7713EEB7184180A0422098F4ECE233B91B68C9903543D947EC075164"
EXPECTED_VERIFICATION_SHA256 = "69F5E037C28418AF21CFF6E0DE1525BB8F1D7EA07175F766AB0AD4400B7F7034"
EXPECTED_CANDIDATE_SHA256 = "2184A0085DA4D617863EC01373E16191B3D7FE86E466D4BDC756A077CAE2DCD3"
EXPECTED_FIELD_DIFF_SHA256 = "B58671A1429F6FEBEF7FD59125D560A76D314AAA4E3FA15630DCBA250496E1B0"
EXPECTED_PRE_HEADER_SHA256 = "F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5"


class PromotionError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_hash(label: str, measured: str, expected: str) -> None:
    if measured != expected:
        raise PromotionError(f"{label.upper()}_HASH_MISMATCH:{measured}:{expected}")


def validate_repo_binding(repo_sha: str, branch: str) -> None:
    if repo_sha != EXPECTED_REPO_SHA:
        raise PromotionError(f"REPOSITORY_REVISION_MISMATCH:{repo_sha}:{EXPECTED_REPO_SHA}")
    if branch != EXPECTED_BRANCH:
        raise PromotionError(f"BRANCH_MISMATCH:{branch}:{EXPECTED_BRANCH}")


def require_file(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PromotionError(f"PATH_OUTSIDE_REPOSITORY:{path}") from exc
    if not path.is_file():
        raise PromotionError(f"INPUT_MISSING:{path}")
    return path


def require_new_directory(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PromotionError(f"PATH_OUTSIDE_REPOSITORY:{path}") from exc
    if path.exists():
        raise PromotionError(f"OUTPUT_ALREADY_EXISTS:{path}")
    return path


def load_parser(root: Path):
    path = root / "dottalkpp/tools/help/generate_dotref_from_metadata_v1.py"
    spec = importlib.util.spec_from_file_location("dotref_parser_for_m3e_v1", path)
    if spec is None or spec.loader is None:
        raise PromotionError(f"PARSER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {(key or "").strip().upper(): (value or "") for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def tf(value: bool) -> str:
    return "T" if value else "F"


def validate_projection(
    current_items: list[Any], candidate_items: list[Any], diff_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    current_names = [item.name for item in current_items]
    candidate_names = [item.name for item in candidate_items]
    if current_names != candidate_names:
        raise PromotionError("MEMBER_ORDER_OR_IDENTITY_DRIFT")
    if len(candidate_items) != 268:
        raise PromotionError(f"CANDIDATE_MEMBER_COUNT:{len(candidate_items)}")

    expected: set[tuple[str, str, str, str]] = set()
    for row in diff_rows:
        if row.get("FIELD") != "SUPPORTED" or row.get("DISPOSITION") != "APPROVED_M3D_CANDIDATE":
            raise PromotionError(f"UNAPPROVED_FIELD_DIFF:{row}")
        expected.add((row["NAME"], row["FIELD"], row["CURRENT"], row["CANDIDATE"]))
    if len(expected) != 22 or len(expected) != len(diff_rows):
        raise PromotionError(f"APPROVED_DIFF_COUNT:{len(expected)}")

    actual: list[dict[str, str]] = []
    for current, candidate in zip(current_items, candidate_items):
        for field, before, after in (
            ("SYNTAX", current.syntax, candidate.syntax),
            ("SUMMARY", current.summary, candidate.summary),
            ("SUPPORTED", tf(current.supported), tf(candidate.supported)),
        ):
            if before != after:
                actual.append({
                    "NAME": current.name,
                    "FIELD": field,
                    "CURRENT": before,
                    "CANDIDATE": after,
                })
    actual_set = {
        (row["NAME"], row["FIELD"], row["CURRENT"], row["CANDIDATE"])
        for row in actual
    }
    if actual_set != expected or len(actual) != len(expected):
        unexpected = sorted(actual_set - expected)
        missing = sorted(expected - actual_set)
        raise PromotionError(
            "FIELD_DIFF_DOES_NOT_MATCH_APPROVAL:"
            f"unexpected={unexpected}:missing={missing}"
        )
    return actual


def candidate_items(parser: Any, text: str) -> list[Any]:
    return [parser._parse_entry(entry) for entry in parser._iter_entries(text)]


def render_header(prefix: str, suffix: str, candidate_text: str, newline: str) -> str:
    row_lines = [line for line in candidate_text.splitlines() if line.startswith("        {")]
    if len(row_lines) != 268:
        raise PromotionError(f"CANDIDATE_ROW_LINE_COUNT:{len(row_lines)}")
    marker = [
        "",
        "        // ===== GENERATED DOTREF ROWS -- AIF-171 M3E =====",
        "        // generator: tools/fullstack_docs/emit_dotref_m3d_candidate_v1.py",
        f"        // run: {RUN_ID}",
        f"        // approved gate sha256: {EXPECTED_GATE_SHA256}",
        "        // generated rows below; edit REFVOICE/source authority, not this region",
        "",
    ]
    body = newline.join(marker + row_lines) + newline
    return prefix + body + suffix


def git_value(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args], cwd=root, check=True,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(
        path,
        (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8"),
    )


def validate_inputs(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    authorization = require_file(root, args.authorization_record)
    verification = require_file(root, args.verification_summary)
    candidate = require_file(root, args.candidate_include)
    field_diff = require_file(root, args.field_diff)
    header = require_file(root, args.header)

    expected_hashes = {
        "authorization": (authorization, EXPECTED_AUTHORIZATION_SHA256),
        "verification": (verification, EXPECTED_VERIFICATION_SHA256),
        "candidate": (candidate, EXPECTED_CANDIDATE_SHA256),
        "field_diff": (field_diff, EXPECTED_FIELD_DIFF_SHA256),
        "pre_header": (header, EXPECTED_PRE_HEADER_SHA256),
    }
    measured: dict[str, str] = {}
    for label, (path, expected) in expected_hashes.items():
        measured[label] = sha256_file(path)
        validate_hash(label, measured[label], expected)

    repo_sha = git_value(root, "rev-parse", "HEAD").upper()
    branch = git_value(root, "branch", "--show-current")
    validate_repo_binding(repo_sha, branch)

    approval_text = authorization.read_text(encoding="utf-8")
    for required in (
        EXPECTED_GATE_SHA256, EXPECTED_VERIFICATION_SHA256,
        EXPECTED_CANDIDATE_SHA256, EXPECTED_PRE_HEADER_SHA256,
        "It does not authorize HELP or META mutation",
    ):
        if required not in approval_text:
            raise PromotionError(f"AUTHORIZATION_BINDING_MISSING:{required}")

    verification_payload = json.loads(verification.read_text(encoding="utf-8"))
    if verification_payload.get("status") != "M3D_REPORT_ONLY_G0_G7_PASS":
        raise PromotionError("M3D_VERIFICATION_STATUS_NOT_PASS")
    gates = verification_payload.get("gates", {})
    if set(gates.values()) != {"PASS"} or len(gates) != 8:
        raise PromotionError(f"M3D_GATE_SET_NOT_PASS:{gates}")
    if verification_payload.get("counts", {}).get("dotref") != 268:
        raise PromotionError("M3D_DOTREF_COUNT_NOT_268")

    original_bytes = header.read_bytes()
    if original_bytes.startswith(b"\xef\xbb\xbf"):
        raise PromotionError("LIVE_HEADER_BOM_NOT_SUPPORTED")
    original_text = original_bytes.decode("utf-8")
    candidate_text = candidate.read_text(encoding="utf-8")
    parser = load_parser(root)
    prefix, current_items, suffix = parser.parse_header(original_text)
    proposed_items = candidate_items(parser, candidate_text)
    actual_diffs = validate_projection(current_items, proposed_items, read_csv(field_diff))
    newline = "\r\n" if original_bytes.count(b"\r\n") > original_bytes.count(b"\n") // 2 else "\n"
    promoted_text = render_header(prefix, suffix, candidate_text, newline)
    promoted_bytes = promoted_text.encode("utf-8")
    new_prefix, promoted_items, new_suffix = parser.parse_header(promoted_text)
    if new_prefix != prefix or new_suffix != suffix:
        raise PromotionError("HEADER_PREFIX_OR_SUFFIX_DRIFT")
    if [
        (item.name, item.syntax, item.summary, item.supported) for item in promoted_items
    ] != [
        (item.name, item.syntax, item.summary, item.supported) for item in proposed_items
    ]:
        raise PromotionError("PROMOTED_HEADER_ROUNDTRIP_MISMATCH")

    return {
        "root": root,
        "header": header,
        "original_bytes": original_bytes,
        "promoted_bytes": promoted_bytes,
        "post_hash": sha256_bytes(promoted_bytes),
        "measured": measured,
        "repo_sha": repo_sha,
        "branch": branch,
        "actual_diffs": actual_diffs,
    }


def apply(args: argparse.Namespace) -> int:
    state = validate_inputs(args)
    root: Path = state["root"]
    out = require_new_directory(root, args.out)
    header: Path = state["header"]
    backup = out / "backup/include/dotref.hpp"
    manifest = out / "promotion_manifest.json"
    out.mkdir(parents=True)
    backup.parent.mkdir(parents=True)
    atomic_write(backup, state["original_bytes"])
    if sha256_file(backup) != EXPECTED_PRE_HEADER_SHA256:
        raise PromotionError("BACKUP_READBACK_HASH_MISMATCH")

    payload = {
        "schema": SCHEMA,
        "run_id": RUN_ID,
        "status": "PREPARED",
        "authorized_mutation": "include/dotref.hpp catalog row region only",
        "branch": state["branch"],
        "repo_sha": state["repo_sha"],
        "pre_header_sha256": EXPECTED_PRE_HEADER_SHA256,
        "post_header_sha256": state["post_hash"],
        "backup_path": str(backup.relative_to(root)).replace("\\", "/"),
        "backup_sha256": sha256_file(backup),
        "approved_field_differences": state["actual_diffs"],
        "input_hashes": state["measured"],
        "rollback_command": (
            "python tools/fullstack_docs/apply_dotref_m3e_promotion_v1.py "
            f"--root . --rollback --manifest {str(manifest.relative_to(root)).replace(chr(92), '/')}"
        ),
        "forbidden_mutations": [
            "HELP", "META", "manuals", "website", "publication staging", "commit", "push"
        ],
    }
    write_json(manifest, payload)
    try:
        atomic_write(header, state["promoted_bytes"])
        if sha256_file(header) != state["post_hash"]:
            raise PromotionError("LIVE_HEADER_READBACK_HASH_MISMATCH")
        payload["status"] = "APPLIED_AND_READ_BACK"
        write_json(manifest, payload)
    except Exception:
        atomic_write(header, state["original_bytes"])
        if sha256_file(header) != EXPECTED_PRE_HEADER_SHA256:
            raise PromotionError("APPLY_FAILED_AND_AUTOMATIC_ROLLBACK_FAILED")
        raise

    print(json.dumps({
        "status": payload["status"],
        "pre_header_sha256": EXPECTED_PRE_HEADER_SHA256,
        "post_header_sha256": state["post_hash"],
        "backup_sha256": payload["backup_sha256"],
        "approved_differences": len(state["actual_diffs"]),
        "manifest": str(manifest),
    }, indent=2, sort_keys=True))
    return 0


def rollback(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest = require_file(root, args.manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or payload.get("status") != "APPLIED_AND_READ_BACK":
        raise PromotionError("ROLLBACK_MANIFEST_NOT_APPLIED")
    header = require_file(root, "include/dotref.hpp")
    backup = require_file(root, payload["backup_path"])
    if sha256_file(header) != payload.get("post_header_sha256"):
        raise PromotionError("ROLLBACK_LIVE_HEADER_HASH_MISMATCH")
    if sha256_file(backup) != payload.get("pre_header_sha256"):
        raise PromotionError("ROLLBACK_BACKUP_HASH_MISMATCH")
    atomic_write(header, backup.read_bytes())
    if sha256_file(header) != payload.get("pre_header_sha256"):
        raise PromotionError("ROLLBACK_READBACK_HASH_MISMATCH")
    payload["status"] = "ROLLED_BACK_AND_READ_BACK"
    write_json(manifest, payload)
    print(f"ROLLED_BACK_AND_READ_BACK:{payload['pre_header_sha256']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    ap.add_argument("--authorization-record")
    ap.add_argument("--verification-summary")
    ap.add_argument("--candidate-include")
    ap.add_argument("--field-diff")
    ap.add_argument("--header", default="include/dotref.hpp")
    ap.add_argument("--out")
    ap.add_argument("--manifest")
    args = ap.parse_args(argv)
    try:
        if args.rollback:
            if not args.manifest:
                raise PromotionError("ROLLBACK_MANIFEST_REQUIRED")
            return rollback(args)
        required = {
            "authorization_record": args.authorization_record,
            "verification_summary": args.verification_summary,
            "candidate_include": args.candidate_include,
            "field_diff": args.field_diff,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise PromotionError(f"REQUIRED_ARGUMENTS_MISSING:{missing}")
        state = validate_inputs(args)
        if args.check_only:
            print(json.dumps({
                "status": "CHECK_ONLY_PASS",
                "post_header_sha256": state["post_hash"],
                "approved_differences": len(state["actual_diffs"]),
            }, indent=2, sort_keys=True))
            return 0
        if not args.out:
            raise PromotionError("APPLY_OUTPUT_DIRECTORY_REQUIRED")
        return apply(args)
    except (PromotionError, OSError, ValueError, KeyError, json.JSONDecodeError,
            subprocess.CalledProcessError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
