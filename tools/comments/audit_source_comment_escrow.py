from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


AUDIT_VERSION = "1.0"
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".hxx",
    ".inl",
    ".ipp",
    ".py",
    ".ps1",
    ".md",
    ".txt",
    ".cmake",
    ".json",
}
C_FAMILY_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".inl", ".ipp"}
EXCLUDED_DIR_NAMES = {
    ".git",
    ".vs",
    "build",
    "build-msvc",
    "node_modules",
    "packages",
    "__pycache__",
    "_drops",
    "backups",
    "generated",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report-only audit of the preserved source-comment escrow baseline "
            "against current source files. No source, DBF, HELP, or metadata writes."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Escrow unique-inventory CSV. Defaults to the preserved baseline copy.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for new CSV, JSON, and Markdown audit reports.",
    )
    parser.add_argument(
        "--staging-root",
        type=Path,
        help="Optional staging tree used only for byte-parity checks of comments DBFs.",
    )
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def contiguous_hash_lines(lines: list[str], start: int, prefix: str) -> tuple[list[str], int]:
    captured: list[str] = []
    index = start
    while index < len(lines):
        stripped = lines[index].lstrip()
        if stripped.startswith(prefix):
            captured.append(lines[index])
            index += 1
            continue
        if stripped == "":
            probe = index + 1
            while probe < len(lines) and lines[probe].strip() == "":
                probe += 1
            if probe < len(lines) and lines[probe].lstrip().startswith(prefix):
                captured.append(lines[index])
                index += 1
                continue
        break
    return captured, index


def extract_c_family_leading(lines: list[str], start: int) -> tuple[list[str], str]:
    stripped = lines[start].lstrip()
    if stripped.startswith("//"):
        block, _ = contiguous_hash_lines(lines, start, "//")
        return block, "doc-line" if stripped.startswith("///") else "line"
    if stripped.startswith("/*"):
        block: list[str] = []
        for line in lines[start:]:
            block.append(line)
            if "*/" in line:
                return block, "doc-block" if stripped.startswith(("/**", "/*!")) else "block"
        return block, "unterminated-block"
    return [], "none"


def extract_python_leading(lines: list[str], start: int) -> tuple[list[str], str]:
    stripped = lines[start].lstrip()
    if stripped.startswith("#"):
        block, _ = contiguous_hash_lines(lines, start, "#")
        return block, "python-line"
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            block: list[str] = []
            for offset, line in enumerate(lines[start:]):
                block.append(line)
                occurrences = line.count(quote)
                if (offset == 0 and occurrences >= 2) or (offset > 0 and quote in line):
                    return block, "python-docstring"
            return block, "python-docstring-unterminated"
    return [], "none"


def extract_powershell_leading(lines: list[str], start: int) -> tuple[list[str], str]:
    stripped = lines[start].lstrip()
    if stripped.startswith("#"):
        block, _ = contiguous_hash_lines(lines, start, "#")
        return block, "powershell-line"
    if stripped.startswith("<#"):
        block: list[str] = []
        for line in lines[start:]:
            block.append(line)
            if "#>" in line:
                return block, "powershell-block"
        return block, "powershell-block-unterminated"
    return [], "none"


def extract_document_leading(lines: list[str], start: int) -> tuple[list[str], str]:
    if lines[start].lstrip().startswith("#"):
        return [lines[start]], "document-heading"
    block: list[str] = []
    for line in lines[start:]:
        if line.strip() == "":
            break
        block.append(line)
    return (block, "document-paragraph") if block else ([], "none")


def leading_comment(path: Path) -> tuple[str, str, str, bool, int]:
    text = read_text(path)
    lines = text.splitlines()
    start = 0
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    if start >= len(lines):
        return "", "none", "", False, 0

    suffix = path.suffix.lower()
    if suffix in C_FAMILY_SUFFIXES:
        block, style = extract_c_family_leading(lines, start)
    elif suffix == ".py":
        block, style = extract_python_leading(lines, start)
    elif suffix == ".ps1" or path.name.lower().startswith("cmakelists") or suffix == ".cmake":
        block, style = extract_powershell_leading(lines, start)
    elif suffix in {".md", ".txt"}:
        block, style = extract_document_leading(lines, start)
    else:
        block, style = [], "none"

    comment_text = os.linesep.join(block)
    comment_hash = sha256_text(comment_text) if block else ""
    usage_index = next(
        (index for index, line in enumerate(block) if "@dottalk.usage v1" in line.lower()),
        -1,
    )
    usage_text = os.linesep.join(block[usage_index:]) if usage_index >= 0 else ""
    usage_hash = sha256_text(usage_text) if usage_text else ""
    marker_count = len(re.findall(r"@dottalk\.(?:usage|contract)\b", text, flags=re.IGNORECASE))
    return comment_hash, style, usage_hash, usage_index >= 0, marker_count


def classify(
    baseline_file_hash: str,
    current_file_hash: str,
    baseline_comment_hash: str,
    current_comment_hash: str,
    baseline_comment_ambiguous: bool,
) -> str:
    if not current_file_hash:
        return "MISSING_CURRENT"
    if not baseline_file_hash:
        return "BASELINE_FILE_HASH_MISSING"
    if baseline_file_hash == current_file_hash:
        return "FILE_MATCH"
    if baseline_comment_ambiguous:
        return "FILE_DRIFT_BASELINE_COMMENT_AMBIGUOUS"
    if baseline_comment_hash and current_comment_hash:
        if baseline_comment_hash == current_comment_hash:
            return "FILE_DRIFT_COMMENT_MATCH"
        return "FILE_DRIFT_COMMENT_CHANGED"
    if baseline_comment_hash and not current_comment_hash:
        return "FILE_DRIFT_COMMENT_REMOVED"
    if not baseline_comment_hash and current_comment_hash:
        return "FILE_DRIFT_COMMENT_ADDED"
    return "FILE_DRIFT_NO_LEADING_COMMENT"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def is_excluded(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part.lower() in EXCLUDED_DIR_NAMES for part in relative.parts[:-1])


def current_scope_files(repo_root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for root_name in ("src", "include", "bindings"):
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or is_excluded(path, repo_root):
                continue
            if path.suffix.lower() in SOURCE_SUFFIXES or path.name.lower() == "cmakelists.txt":
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield resolved
    for name in ("CMakeLists.txt", "CMakePresets.json"):
        path = repo_root / name
        if path.is_file() and path.resolve() not in seen:
            yield path.resolve()


def verify_preserved_bundle(repo_root: Path) -> dict[str, int]:
    baseline_dir = (
        repo_root
        / "dottalkpp"
        / "docs"
        / "generated"
        / "baselines"
        / "source_comment_escrow_baseline_v1"
    )
    manifest = baseline_dir / "BASELINE_MANIFEST.csv"
    result = {"manifest_rows": 0, "hash_matches": 0, "hash_mismatches": 0, "missing": 0}
    if not manifest.is_file():
        result["missing"] = 1
        return result
    rows = read_csv(manifest)
    result["manifest_rows"] = len(rows)
    for row in rows:
        preserved = repo_root / "dottalkpp" / row.get("PreservedPath", "")
        if not preserved.is_file():
            result["missing"] += 1
            continue
        if sha256_file(preserved) == row.get("PreservedSha256", "").upper():
            result["hash_matches"] += 1
        else:
            result["hash_mismatches"] += 1
    return result


def dbf_record_count(path: Path) -> int:
    with path.open("rb") as handle:
        header = handle.read(12)
    return struct.unpack("<I", header[4:8])[0] if len(header) >= 12 else 0


def find_dbf_field(path: Path, field_name: str) -> tuple[int, int, int, int] | None:
    data = path.read_bytes()
    if len(data) < 128:
        return None
    record_count = struct.unpack("<I", data[4:8])[0]
    header_length = struct.unpack("<H", data[8:10])[0]
    record_length = struct.unpack("<H", data[10:12])[0]

    descriptors: list[tuple[str, int]] = []
    start = -1
    for candidate in range(32, min(header_length, len(data) - 32), 32):
        name = data[candidate : candidate + 11].split(b"\0", 1)[0].decode("ascii", errors="ignore").strip()
        if name == "FILEID":
            start = candidate
            break
    if start < 0:
        return None

    position = start
    while position < header_length and data[position] != 0x0D:
        name = data[position : position + 11].split(b"\0", 1)[0].decode("ascii", errors="ignore").strip()
        length = data[position + 16]
        descriptors.append((name, length))
        position += 32

    offset = 1
    for name, length in descriptors:
        if name.upper() == field_name.upper():
            return record_count, header_length, record_length, offset
        offset += length
    return None


def dbf_nonempty_count(path: Path, field_name: str, field_length: int) -> int | None:
    location = find_dbf_field(path, field_name)
    if location is None:
        return None
    record_count, header_length, record_length, offset = location
    data = path.read_bytes()
    populated = 0
    for index in range(record_count):
        start = header_length + index * record_length + offset
        value = data[start : start + field_length].decode("ascii", errors="ignore").strip()
        if value:
            populated += 1
    return populated


def comments_dbf_summary(repo_root: Path, staging_root: Path | None) -> list[dict[str, object]]:
    comments_root = repo_root / "dottalkpp" / "data" / "comments"
    rows: list[dict[str, object]] = []
    if not comments_root.is_dir():
        return rows
    for path in sorted(comments_root.glob("*.dbf")):
        current_hash = sha256_file(path)
        staging_hash = ""
        parity = "NOT_CHECKED"
        if staging_root:
            staged = staging_root / "dottalkpp" / "data" / "comments" / path.name
            if staged.is_file():
                staging_hash = sha256_file(staged)
                parity = "MATCH" if current_hash == staging_hash else "DRIFT"
            else:
                parity = "MISSING_STAGING"
        rows.append(
            {
                "table": path.stem,
                "records": dbf_record_count(path),
                "sha256": current_hash,
                "staging_sha256": staging_hash,
                "staging_parity": parity,
            }
        )
    return rows


def review_routing(row: dict[str, object]) -> tuple[str, str]:
    status = str(row["status"])
    usage_present = int(row["current_usage_present"]) == 1
    marker_count = int(row["current_contract_marker_count"])
    has_contract = usage_present or marker_count > 0

    if status == "FILE_MATCH":
        return "NONE", "No baseline drift."
    if status == "MISSING_CURRENT":
        return "P1", "Baseline path is missing; classify move, deletion, or scope change before restoration."
    if status == "FILE_DRIFT_COMMENT_REMOVED":
        return "P1", "Baseline leading comment is absent from the current file."
    if status == "FILE_DRIFT_COMMENT_CHANGED" and has_contract:
        return "P1", "A source comment or usage/contract-bearing header changed."
    if status == "FILE_DRIFT_COMMENT_MATCH" and has_contract:
        return "P1", "Implementation file changed while its usage/contract-bearing header stayed unchanged."
    if status == "NEW_CURRENT" and has_contract:
        return "P1", "New source file carries usage/contract markers and is absent from the baseline."
    if status == "FILE_DRIFT_BASELINE_COMMENT_AMBIGUOUS":
        return "P2", "Legacy scanners disagreed about leading-comment state; inspect source reports before inference."
    if status in {"FILE_DRIFT_COMMENT_ADDED", "FILE_DRIFT_COMMENT_CHANGED"}:
        return "P2", "Leading-comment state changed and needs documentary-intent review."
    if status == "FILE_DRIFT_NO_LEADING_COMMENT":
        return "P2", "File changed with no leading-comment evidence in either state."
    if status == "NEW_CURRENT":
        return "P2", "New in-scope file is absent from the baseline."
    if status == "FILE_DRIFT_COMMENT_MATCH":
        return "P3", "File changed while its leading comment stayed unchanged; review only if behavior/documentation impact exists."
    return "P2", "Unclassified drift requires manual review."


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = args.baseline
    if baseline is None:
        baseline = (
            repo_root
            / "dottalkpp"
            / "docs"
            / "generated"
            / "baselines"
            / "source_comment_escrow_baseline_v1"
            / "docs__generated__reports__source_comment_escrow_unique_inventory_v1.csv"
        )
    elif not baseline.is_absolute():
        baseline = repo_root / baseline
    baseline = baseline.resolve()
    if not baseline.is_file():
        raise SystemExit(f"Baseline inventory not found: {baseline}")

    baseline_rows = read_csv(baseline)
    baseline_paths = {row.get("WorkspaceRelativePath", "").replace("\\", "/") for row in baseline_rows}
    audit_rows: list[dict[str, object]] = []

    for row in baseline_rows:
        relpath = row.get("WorkspaceRelativePath", "").replace("\\", "/")
        current_path = repo_root / Path(relpath)
        exists = current_path.is_file()
        current_file_hash = sha256_file(current_path) if exists else ""
        if exists:
            current_comment_hash, comment_style, usage_hash, usage_present, marker_count = leading_comment(current_path)
            size = current_path.stat().st_size
            modified = datetime.fromtimestamp(current_path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        else:
            current_comment_hash = ""
            comment_style = "missing"
            usage_hash = ""
            usage_present = False
            marker_count = 0
            size = 0
            modified = ""

        baseline_file_hash = row.get("FileSha256", "").upper()
        baseline_comment_hash = row.get("LeadingCommentHash", "").upper()
        escrow_lanes = row.get("EscrowLanes", "").lower()
        baseline_comment_ambiguous = "comment-present" in escrow_lanes and "comment-missing" in escrow_lanes
        status = classify(
            baseline_file_hash,
            current_file_hash,
            baseline_comment_hash,
            current_comment_hash,
            baseline_comment_ambiguous,
        )
        audit_rows.append(
            {
                "path": relpath,
                "status": status,
                "baseline_file_sha256": baseline_file_hash,
                "current_file_sha256": current_file_hash,
                "baseline_comment_sha256": baseline_comment_hash,
                "current_comment_sha256": current_comment_hash,
                "current_usage_sha256": usage_hash,
                "current_usage_present": int(usage_present),
                "current_contract_marker_count": marker_count,
                "baseline_comment_style": row.get("LeadingCommentStyle", ""),
                "baseline_comment_ambiguous": int(baseline_comment_ambiguous),
                "current_comment_style": comment_style,
                "restore_candidate_baseline": row.get("RestoreCandidate", ""),
                "baseline_last_write": row.get("LastWriteTime", ""),
                "current_last_write": modified,
                "baseline_size": row.get("FileSize", ""),
                "current_size": size,
                "review_disposition": "UNREVIEWED_DRIFT" if status != "FILE_MATCH" else "NOT_REQUIRED",
            }
        )

    for current_path in current_scope_files(repo_root):
        relpath = current_path.relative_to(repo_root).as_posix()
        if relpath in baseline_paths:
            continue
        comment_hash, comment_style, usage_hash, usage_present, marker_count = leading_comment(current_path)
        audit_rows.append(
            {
                "path": relpath,
                "status": "NEW_CURRENT",
                "baseline_file_sha256": "",
                "current_file_sha256": sha256_file(current_path),
                "baseline_comment_sha256": "",
                "current_comment_sha256": comment_hash,
                "current_usage_sha256": usage_hash,
                "current_usage_present": int(usage_present),
                "current_contract_marker_count": marker_count,
                "baseline_comment_style": "",
                "baseline_comment_ambiguous": 0,
                "current_comment_style": comment_style,
                "restore_candidate_baseline": "",
                "baseline_last_write": "",
                "current_last_write": datetime.fromtimestamp(current_path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                "baseline_size": "",
                "current_size": current_path.stat().st_size,
                "review_disposition": "UNREVIEWED_NEW_FILE",
            }
        )

    audit_rows.sort(key=lambda item: (str(item["status"]), str(item["path"]).lower()))
    audit_fields = [
        "path",
        "status",
        "baseline_file_sha256",
        "current_file_sha256",
        "baseline_comment_sha256",
        "current_comment_sha256",
        "current_usage_sha256",
        "current_usage_present",
        "current_contract_marker_count",
        "baseline_comment_style",
        "baseline_comment_ambiguous",
        "current_comment_style",
        "restore_candidate_baseline",
        "baseline_last_write",
        "current_last_write",
        "baseline_size",
        "current_size",
        "review_disposition",
    ]
    csv_path = output_dir / "source_comment_escrow_drift_audit_v1.csv"
    write_csv(csv_path, audit_rows, audit_fields)

    queue_rows: list[dict[str, object]] = []
    for row in audit_rows:
        priority, reason = review_routing(row)
        if priority == "NONE":
            continue
        queue_rows.append(
            {
                "priority": priority,
                "path": row["path"],
                "status": row["status"],
                "review_reason": reason,
                "current_usage_present": row["current_usage_present"],
                "current_contract_marker_count": row["current_contract_marker_count"],
                "restore_candidate_baseline": row["restore_candidate_baseline"],
                "review_disposition": "UNREVIEWED",
                "evidence_row": row["path"],
            }
        )
    priority_order = {"P1": 1, "P2": 2, "P3": 3}
    queue_rows.sort(key=lambda item: (priority_order[str(item["priority"])], str(item["path"]).lower()))
    queue_path = output_dir / "source_comment_escrow_review_queue_v1.csv"
    write_csv(
        queue_path,
        queue_rows,
        [
            "priority",
            "path",
            "status",
            "review_reason",
            "current_usage_present",
            "current_contract_marker_count",
            "restore_candidate_baseline",
            "review_disposition",
            "evidence_row",
        ],
    )

    bundle = verify_preserved_bundle(repo_root)
    staging_root = args.staging_root.resolve() if args.staging_root else None
    dbfs = comments_dbf_summary(repo_root, staging_root)
    srcfile_dbf = repo_root / "dottalkpp" / "data" / "comments" / "SRCFILE.dbf"
    live_hash_populated = dbf_nonempty_count(srcfile_dbf, "HASH", 64) if srcfile_dbf.is_file() else None

    staged_srcfile = (
        repo_root
        / "dottalkpp"
        / "docs"
        / "generated"
        / "staging"
        / "source_comment_metadata_import_v1"
        / "SRCFILE_IMPORT.csv"
    )
    staged_rows = read_csv(staged_srcfile) if staged_srcfile.is_file() else []
    staged_hash_populated = sum(1 for row in staged_rows if row.get("HASH", "").strip())

    counts = Counter(str(row["status"]) for row in audit_rows)
    priority_counts = Counter(str(row["priority"]) for row in queue_rows)
    summary = {
        "audit_version": AUDIT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo_root": str(repo_root),
        "baseline": str(baseline),
        "baseline_sha256": sha256_file(baseline),
        "output_csv": str(csv_path),
        "baseline_rows": len(baseline_rows),
        "audit_rows": len(audit_rows),
        "status_counts": dict(sorted(counts.items())),
        "review_queue": {
            "path": str(queue_path),
            "rows": len(queue_rows),
            "priority_counts": dict(sorted(priority_counts.items())),
        },
        "preserved_bundle": bundle,
        "comments_dbfs": dbfs,
        "srcfile_live_records": dbf_record_count(srcfile_dbf) if srcfile_dbf.is_file() else 0,
        "srcfile_live_hash_populated": live_hash_populated,
        "srcfile_staged_rows": len(staged_rows),
        "srcfile_staged_hash_populated": staged_hash_populated,
        "mutation_boundary": {
            "source_writes": 0,
            "dbf_writes": 0,
            "help_writes": 0,
            "metadata_writes": 0,
            "baseline_writes": 0,
            "report_writes": 4,
        },
    }
    json_path = output_dir / "source_comment_escrow_drift_audit_v1.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    markdown: list[str] = [
        "# Source Comment Escrow Drift Audit v1",
        "",
        "Status: REPORT-ONLY / UNREVIEWED DRIFT INVENTORY",
        "",
        f"Generated UTC: {summary['generated_utc']}",
        f"Baseline: `{baseline}`",
        f"Baseline SHA-256: `{summary['baseline_sha256']}`",
        "",
        "## Authority Boundary",
        "",
        "This report identifies differences. It does not classify any change as unauthorized,",
        "authorize source restoration, or mutate source, DBFs, HELP, metadata, or the baseline.",
        "",
        "## Drift Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in sorted(counts.items()):
        markdown.append(f"| `{status}` | {count} |")

    markdown.extend(
        [
            "",
            "## Review Queue",
            "",
            "| Priority | Count |",
            "| --- | ---: |",
        ]
    )
    for priority, count in sorted(priority_counts.items()):
        markdown.append(f"| `{priority}` | {count} |")
    markdown.extend(
        [
            "",
            "P1 routes missing files, contract/comment changes, implementation drift beneath unchanged",
            "contracts, and new contract-bearing source. Queue rows remain unreviewed and are not mutation authority.",
        ]
    )

    markdown.extend(
        [
            "",
            "## Preserved Baseline Integrity",
            "",
            "| Check | Count |",
            "| --- | ---: |",
            f"| Manifest rows | {bundle['manifest_rows']} |",
            f"| Hash matches | {bundle['hash_matches']} |",
            f"| Hash mismatches | {bundle['hash_mismatches']} |",
            f"| Missing artifacts | {bundle['missing']} |",
            "",
            "## COMMENTS DBF Snapshot",
            "",
            "| Table | Records | Staging parity |",
            "| --- | ---: | --- |",
        ]
    )
    for row in dbfs:
        markdown.append(f"| `{row['table']}` | {row['records']} | {row['staging_parity']} |")

    markdown.extend(
        [
            "",
            "## SRCFILE Hash Seam",
            "",
            f"- Live `SRCFILE` records: {summary['srcfile_live_records']}",
            f"- Live populated `HASH` values: {summary['srcfile_live_hash_populated']}",
            f"- Staged `SRCFILE_IMPORT.csv` rows: {summary['srcfile_staged_rows']}",
            f"- Staged populated `HASH` values: {summary['srcfile_staged_hash_populated']}",
            "",
            "The DBF/content lane is therefore a semantic snapshot, while the escrow inventory",
            "currently carries the effective file/comment hash evidence.",
            "",
            "## Review Rule",
            "",
            "- `FILE_MATCH` needs no drift review.",
            "- `FILE_DRIFT_COMMENT_MATCH` indicates non-leading-comment file drift.",
            "- `FILE_DRIFT_COMMENT_CHANGED`, `...REMOVED`, or `...ADDED` requires comment/contract review.",
            "- `FILE_DRIFT_BASELINE_COMMENT_AMBIGUOUS` preserves a legacy scanner conflict for review.",
            "- `MISSING_CURRENT` and `NEW_CURRENT` require move/delete/addition classification.",
            "- No drift status is evidence of unauthorized mutation until reviewed against Git,",
            "  task closeouts, contracts, and maintainer intent.",
            "",
            "## Outputs",
            "",
            f"- `{csv_path.name}`",
            f"- `{queue_path.name}`",
            f"- `{json_path.name}`",
            "- `source_comment_escrow_drift_audit_v1.md`",
            "",
            "## Mutation Confirmation",
            "",
            "- Source writes: 0",
            "- DBF/CDX/LMDB writes: 0",
            "- HELP/metadata writes: 0",
            "- Baseline writes: 0",
            "- New report files: 4",
        ]
    )
    md_path = output_dir / "source_comment_escrow_drift_audit_v1.md"
    md_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")

    print(f"Audit rows: {len(audit_rows)}")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    print(f"Preserved bundle: {bundle['hash_matches']} matching, {bundle['hash_mismatches']} mismatched, {bundle['missing']} missing")
    print(f"Live SRCFILE HASH populated: {live_hash_populated}")
    print(f"Report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
