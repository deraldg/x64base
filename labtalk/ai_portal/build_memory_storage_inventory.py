#!/usr/bin/env python3
"""Build the read-only AIF-136 Portal memory and storage inventory.

The scanner never follows symlinks or Windows reparse points, never opens a
database, and never moves or deletes an artifact. Small files may be hashed for
identity; large files are measured but hashing is deferred by policy.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_JSON = LABTALK_ROOT / "reports" / "portal" / "memory_storage_inventory_latest.json"
DEFAULT_MARKDOWN = LABTALK_ROOT / "reports" / "portal" / "memory_storage_inventory_latest.md"
DEFAULT_SCHEMA = Path(__file__).resolve().parent / "schemas" / "portal_memory_inventory_v1.schema.json"
SCHEMA_ID = "dottalk.portal.memory-inventory.v1"
INVENTORY_LANE = "AIF-136"

BOOTSTRAP_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "labtalk/ai_portal/AI_TIER1_SEED_V1.md",
)
FRONTAL_PATHS = (
    "AI_README.md",
    "AI_PORTAL.md",
    "docs/agents/CURRENT_TARGET.md",
)
SUMMARY_ROOTS = ("docs", "dottalkpp", "tmp", "build", ".git")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def posix(path: Path) -> str:
    return path.as_posix()


def relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return posix(path.resolve(strict=False).relative_to(repo_root.resolve()))
    except ValueError:
        return posix(path.resolve(strict=False))


def is_reparse_point(path: Path, entry: os.DirEntry[str] | None = None) -> bool:
    try:
        if entry is not None and entry.is_symlink():
            return True
        if entry is None and path.is_symlink():
            return True
        info = entry.stat(follow_symlinks=False) if entry is not None else path.stat(follow_symlinks=False)
    except OSError:
        return False
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def walk_files(
    root: Path,
    *,
    reparse_detector: Callable[[Path, os.DirEntry[str] | None], bool] = is_reparse_point,
) -> tuple[list[Path], list[str], list[str]]:
    """Return files, skipped aliases, and read errors without following aliases."""
    root = root.resolve(strict=False)
    if not root.exists():
        return [], [], [f"missing root: {posix(root)}"]
    files: list[Path] = []
    skipped: list[str] = []
    errors: list[str] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda item: item.name.lower())
        except OSError as exc:
            errors.append(f"cannot scan {posix(current)}: {exc}")
            continue
        directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            if reparse_detector(path, entry):
                skipped.append(posix(path))
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    directories.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
            except OSError as exc:
                errors.append(f"cannot classify {posix(path)}: {exc}")
        stack.extend(reversed(directories))
    return sorted(files, key=lambda item: posix(item).lower()), sorted(skipped), sorted(errors)


def allocated_size(path: Path, info: os.stat_result | None = None) -> int | None:
    """Best-effort allocated bytes; never substitutes logical size silently."""
    try:
        info = info or path.stat()
    except OSError:
        return None
    blocks = getattr(info, "st_blocks", 0)
    if blocks:
        return int(blocks) * 512
    if os.name != "nt":
        return None
    try:
        high = ctypes.c_ulong(0)
        ctypes.set_last_error(0)
        low = ctypes.windll.kernel32.GetCompressedFileSizeW(str(path), ctypes.byref(high))
        if low == 0xFFFFFFFF and ctypes.get_last_error() != 0:
            return None
        return (int(high.value) << 32) | int(low)
    except (AttributeError, OSError, ValueError):
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_paths(repo_root: Path) -> tuple[set[str], set[str]]:
    if not (repo_root / ".git").exists():
        return set(), set()

    def run(*args: str) -> set[str]:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(repo_root), *args],
            check=False,
            capture_output=True,
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
        return {
            item.decode("utf-8", errors="surrogateescape").replace("\\", "/").lower()
            for item in result.stdout.split(b"\0")
            if item
        }

    tracked = run("ls-files", "-z")
    ignored = run("ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    return tracked, ignored


def git_posture(path: Path, repo_root: Path, tracked: set[str], ignored: set[str]) -> str:
    try:
        relative = posix(path.resolve(strict=False).relative_to(repo_root.resolve())).lower()
    except ValueError:
        return "external"
    if relative in tracked:
        return "tracked"
    if relative in ignored:
        return "ignored"
    return "untracked"


def artifact_kind(path: Path, collection: str) -> str:
    lower = path.name.lower()
    if lower == "data.mdb":
        return "database_derived"
    if lower.endswith(".claim"):
        return "governance_claim"
    if path.suffix.lower() in {".py", ".ps1", ".cpp", ".hpp", ".h", ".c"}:
        return "source"
    if path.suffix.lower() in {".md", ".txt", ".html", ".svg", ".docx"}:
        return "documentation"
    if collection == "portal_core" and path.suffix.lower() in {".yaml", ".yml", ".json"}:
        return "registry_or_schema"
    return "other"


def proposed_classification(path: Path, collection: str) -> dict[str, str]:
    relative = posix(path).lower()
    if collection == "bootstrap":
        return {
            "authority_class": "reviewed_derivative",
            "storage_tier": "F0",
            "sensitivity": "development_only",
            "retention_policy": "keep",
            "reason": "Always-read safety invariant or vendor shim.",
        }
    if collection in {"frontal", "claims"}:
        return {
            "authority_class": "governance_authority" if collection == "claims" else "reviewed_derivative",
            "storage_tier": "F1",
            "sensitivity": "development_only",
            "retention_policy": "keep",
            "reason": "Current routing or coordination surface.",
        }
    if collection == "docs_lmdb" or relative.endswith("/data.mdb"):
        return {
            "authority_class": "generated_projection",
            "storage_tier": "R4",
            "sensitivity": "development_only",
            "retention_policy": "owner_ruling_required",
            "reason": "LMDB environment is derived; exact reconstruction remains unverified for this specimen.",
        }
    if collection == "frontal_mem_external":
        return {
            "authority_class": "unknown",
            "storage_tier": "C3",
            "sensitivity": "private",
            "retention_policy": "owner_ruling_required",
            "reason": "Owner-controlled long-term-memory body outside the tracked repository.",
        }
    return {
        "authority_class": "unknown",
        "storage_tier": "W2",
        "sensitivity": "development_only",
        "retention_policy": "owner_ruling_required",
        "reason": "Recall body proposed for warm classification; authority review is incomplete.",
    }


def memory_id(source_uri: str) -> str:
    digest = hashlib.sha256(source_uri.lower().encode("utf-8")).hexdigest()[:20]
    return f"memory.file.{digest}"


def make_record(
    path: Path,
    *,
    repo_root: Path,
    collection: str,
    tracked: set[str],
    ignored: set[str],
    hash_max_bytes: int,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        info = path.stat()
    except OSError as exc:
        return None, f"cannot stat {posix(path)}: {exc}"
    source_uri = relative_or_absolute(path, repo_root)
    logical = int(info.st_size)
    digest: str | None = None
    hash_state = "deferred_size_policy"
    if logical <= hash_max_bytes:
        try:
            digest = sha256(path)
            hash_state = "computed"
        except OSError as exc:
            hash_state = "unreadable"
            return None, f"cannot hash {source_uri}: {exc}"
    classification = proposed_classification(path, collection)
    record = {
        "memory_id": memory_id(source_uri),
        "title": path.name,
        "project_id": "project.ai_friendly.agent_memory" if collection != "docs_lmdb" else "project.x64base.runtime",
        "inventory_lane_id": INVENTORY_LANE,
        "lane_ids": [],
        "collection": collection,
        "artifact_kind": artifact_kind(path, collection),
        "authority_class": classification["authority_class"],
        "evidence_state": "source-evidenced",
        "storage_tier": classification["storage_tier"],
        "classification_state": "heuristic_proposal",
        "classification_reason": classification["reason"],
        "source_uri": source_uri,
        "stored_uri": None,
        "sha256": digest,
        "hash_state": hash_state,
        "logical_size_bytes": logical,
        "allocated_size_bytes": allocated_size(path, info),
        "modified_at_utc": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_posture": git_posture(path, repo_root, tracked, ignored),
        "retention_policy": classification["retention_policy"],
        "sensitivity": classification["sensitivity"],
        "retrieval_trigger": "trigger.memory_retention",
        "recovery_state": "unverified",
        "recovery_method": "Owner-approved retrieval or reconstruction proof required before physical reclamation.",
        "portal_summary": f"{collection} artifact measured by AIF-136; classification is a proposal, not an owner ruling.",
    }
    return record, None


def add_candidate(
    candidates: dict[str, tuple[Path, str]], path: Path, collection: str, repo_root: Path
) -> None:
    key = relative_or_absolute(path, repo_root).lower()
    candidates.setdefault(key, (path, collection))


def collect_candidates(repo_root: Path, *, include_external: bool) -> tuple[list[tuple[Path, str]], list[str], list[str]]:
    candidates: dict[str, tuple[Path, str]] = {}
    skipped: list[str] = []
    errors: list[str] = []
    for relative in BOOTSTRAP_PATHS:
        path = repo_root / relative
        if path.is_file():
            add_candidate(candidates, path, "bootstrap", repo_root)
        else:
            errors.append(f"missing bootstrap path: {relative}")
    for relative in FRONTAL_PATHS:
        path = repo_root / relative
        if path.is_file():
            add_candidate(candidates, path, "frontal", repo_root)
        else:
            errors.append(f"missing frontal path: {relative}")

    for root, collection in (
        (repo_root / "labtalk" / "ai_portal", "portal_core"),
        (repo_root / "docs" / "ai-friendly", "ai_friendly"),
        (repo_root / "coordination" / "aif", "claims"),
    ):
        files, aliases, scan_errors = walk_files(root)
        skipped.extend(aliases)
        errors.extend(scan_errors)
        for path in files:
            if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"}:
                continue
            if collection == "claims" and path.suffix.lower() != ".claim":
                continue
            add_candidate(candidates, path, collection, repo_root)

    docs_files, aliases, scan_errors = walk_files(repo_root / "docs")
    skipped.extend(aliases)
    errors.extend(scan_errors)
    for path in docs_files:
        if path.name.lower() == "data.mdb":
            add_candidate(candidates, path, "docs_lmdb", repo_root)

    if include_external:
        external = repo_root.parent / "Frontal_Mem"
        if external.exists():
            files, aliases, scan_errors = walk_files(external)
            skipped.extend(aliases)
            errors.extend(scan_errors)
            for path in files:
                add_candidate(candidates, path, "frontal_mem_external", repo_root)
        else:
            errors.append(f"optional external root absent: {posix(external)}")

    return [candidates[key] for key in sorted(candidates)], sorted(set(skipped)), sorted(set(errors))


def summarize_root(path: Path, repo_root: Path) -> dict[str, Any]:
    files, skipped, errors = walk_files(path)
    logical = 0
    allocated = 0
    allocated_known = 0
    measured = 0
    for item in files:
        try:
            info = item.stat()
        except OSError as exc:
            errors.append(f"cannot stat {posix(item)}: {exc}")
            continue
        measured += 1
        logical += int(info.st_size)
        physical = allocated_size(item, info)
        if physical is not None:
            allocated += physical
            allocated_known += 1
    return {
        "collection_id": f"collection.workspace.{path.name.lower().replace('.', 'dot_')}",
        "source_uri": relative_or_absolute(path, repo_root),
        "files_measured": measured,
        "logical_size_bytes": logical,
        "allocated_size_bytes": allocated if allocated_known else None,
        "allocated_size_known_files": allocated_known,
        "reparse_points_skipped": len(skipped),
        "scan_errors": sorted(errors),
    }


def hierarchy_counts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count Portal-facing records by directory, both direct and recursive."""
    rows: dict[str, dict[str, int | str]] = {}

    def ensure(path: str) -> dict[str, int | str]:
        return rows.setdefault(
            path,
            {
                "path": path,
                "direct_records": 0,
                "recursive_records": 0,
                "direct_documents": 0,
                "recursive_documents": 0,
                "recursive_logical_size_bytes": 0,
            },
        )

    for record in records:
        if record["collection"] == "docs_lmdb":
            continue
        uri = record["source_uri"].replace("\\", "/")
        parent = posix(Path(uri).parent)
        if parent == ".":
            parent = "repo-root"
        document = record["artifact_kind"] in {
            "documentation", "governance_claim", "registry_or_schema"
        }
        direct = ensure(parent)
        direct["direct_records"] = int(direct["direct_records"]) + 1
        if document:
            direct["direct_documents"] = int(direct["direct_documents"]) + 1

        if record["git_posture"] == "external":
            ancestors = [parent]
        else:
            parts = Path(uri).parent.parts
            ancestors = [posix(Path(*parts[:index])) for index in range(1, len(parts) + 1)]
            if not ancestors:
                ancestors = ["repo-root"]
        for ancestor in ancestors:
            row = ensure(ancestor)
            row["recursive_records"] = int(row["recursive_records"]) + 1
            row["recursive_logical_size_bytes"] = int(row["recursive_logical_size_bytes"]) + int(
                record["logical_size_bytes"]
            )
            if document:
                row["recursive_documents"] = int(row["recursive_documents"]) + 1

    return [rows[key] for key in sorted(rows, key=str.lower)]


def build_inventory(
    *,
    repo_root: Path,
    observed_at_utc: str,
    hash_max_bytes: int = 8 * 1024 * 1024,
    include_external: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    tracked, ignored = git_paths(repo_root)
    candidates, skipped, findings = collect_candidates(repo_root, include_external=include_external)
    records: list[dict[str, Any]] = []
    for path, collection in candidates:
        record, error = make_record(
            path,
            repo_root=repo_root,
            collection=collection,
            tracked=tracked,
            ignored=ignored,
            hash_max_bytes=hash_max_bytes,
        )
        if record is not None:
            records.append(record)
        if error:
            findings.append(error)
    records.sort(key=lambda item: item["source_uri"].lower())

    collection_summaries = []
    for relative in SUMMARY_ROOTS:
        root = repo_root / relative
        if root.exists():
            collection_summaries.append(summarize_root(root, repo_root))

    tiers = Counter(record["storage_tier"] for record in records)
    postures = Counter(record["git_posture"] for record in records)
    kinds = Counter(record["artifact_kind"] for record in records)
    lmdb_records = [record for record in records if record["collection"] == "docs_lmdb"]
    lmdb_sizes = Counter(record["logical_size_bytes"] for record in lmdb_records)
    lmdb_areas: dict[str, dict[str, int]] = {}
    for record in lmdb_records:
        parts = Path(record["source_uri"]).parts
        area = parts[1] if len(parts) > 1 and parts[0].lower() == "docs" else "other"
        row = lmdb_areas.setdefault(area, {"records": 0, "logical_size_bytes": 0})
        row["records"] += 1
        row["logical_size_bytes"] += record["logical_size_bytes"]
    logical = sum(record["logical_size_bytes"] for record in records)
    known_allocated = [record["allocated_size_bytes"] for record in records if record["allocated_size_bytes"] is not None]
    return {
        "schema": SCHEMA_ID,
        "generated_at_utc": observed_at_utc,
        "mode": "development_read_only",
        "inventory_lane_id": INVENTORY_LANE,
        "repo_root": posix(repo_root),
        "policy": {
            "follows_reparse_points": False,
            "opens_database_payloads": False,
            "moves_or_deletes": False,
            "hash_max_bytes": hash_max_bytes,
            "classification_authority": "proposal_only",
        },
        "summary": {
            "records": len(records),
            "logical_size_bytes": logical,
            "allocated_size_bytes_known": sum(known_allocated),
            "allocated_size_known_records": len(known_allocated),
            "hashes_computed": sum(record["hash_state"] == "computed" for record in records),
            "hashes_deferred": sum(record["hash_state"] == "deferred_size_policy" for record in records),
            "reparse_points_skipped": len(skipped) + sum(item["reparse_points_skipped"] for item in collection_summaries),
            "findings": len(findings) + sum(len(item["scan_errors"]) for item in collection_summaries),
            "by_storage_tier": dict(sorted(tiers.items())),
            "by_git_posture": dict(sorted(postures.items())),
            "by_artifact_kind": dict(sorted(kinds.items())),
            "docs_lmdb": {
                "records": len(lmdb_records),
                "logical_size_bytes": sum(record["logical_size_bytes"] for record in lmdb_records),
                "allocated_size_bytes_known": sum(
                    record["allocated_size_bytes"]
                    for record in lmdb_records
                    if record["allocated_size_bytes"] is not None
                ),
                "size_distribution": [
                    {"logical_size_bytes": size, "records": count}
                    for size, count in sorted(lmdb_sizes.items(), reverse=True)
                ],
                "by_docs_area": dict(sorted(lmdb_areas.items())),
            },
        },
        "collections": collection_summaries,
        "hierarchy": hierarchy_counts(records),
        "records": records,
        "skipped_reparse_points": skipped,
        "findings": sorted(findings),
    }


def gib(value: int | None) -> str:
    return "--" if value is None else f"{value / (1024 ** 3):.2f}"


def mib(value: int | None) -> str:
    return "--" if value is None else f"{value / (1024 ** 2):.2f}"


def render_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    lines = [
        "# AI Portal Memory and Storage Inventory",
        "",
        "Generated by AIF-136 from a read-only, no-reparse-point scan. Do not hand-edit.",
        "",
        f"Observed UTC: `{inventory['generated_at_utc']}`",
        "",
        "## Boundary",
        "",
        "This report proposes cognitive/storage classifications. It does not approve a move, archive, deletion, publication, or authority change. Database payloads were measured as files and were not opened.",
        "",
        "## Summary",
        "",
        f"- Inventory records: {summary['records']}",
        f"- Logical size represented: {gib(summary['logical_size_bytes'])} GiB",
        f"- Allocated size known: {gib(summary['allocated_size_bytes_known'])} GiB across {summary['allocated_size_known_records']} records",
        f"- Hashes computed: {summary['hashes_computed']}; deferred by size policy: {summary['hashes_deferred']}",
        f"- Reparse points skipped: {summary['reparse_points_skipped']}",
        f"- Scan findings: {summary['findings']}",
        "",
        "## Proposed storage tiers",
        "",
        "| Tier | Records |",
        "| --- | ---: |",
    ]
    for tier, count in summary["by_storage_tier"].items():
        lines.append(f"| `{tier}` | {count} |")
    lmdb = summary["docs_lmdb"]
    lines.extend(
        [
            "",
            "## Ignored LMDB population under docs",
            "",
            f"- Records: {lmdb['records']}",
            f"- Logical size: {gib(lmdb['logical_size_bytes'])} GiB",
            f"- Allocated size known: {gib(lmdb['allocated_size_bytes_known'])} GiB",
            "",
            "### Size distribution",
            "",
            "| Logical bytes per file | MiB per file | Records |",
            "| ---: | ---: | ---: |",
        ]
    )
    for item in lmdb["size_distribution"]:
        lines.append(
            f"| {item['logical_size_bytes']} | {mib(item['logical_size_bytes'])} | {item['records']} |"
        )
    lines.extend(
        [
            "",
            "### Grouped by docs area",
            "",
            "| Area | Records | Logical GiB |",
            "| --- | ---: | ---: |",
        ]
    )
    for area, item in lmdb["by_docs_area"].items():
        lines.append(f"| `{area}` | {item['records']} | {gib(item['logical_size_bytes'])} |")
    lines.extend(
        [
            "",
            "## Portal-facing hierarchy",
            "",
            "LMDB payload records are excluded from this document hierarchy and reported above.",
            "",
            "| Directory | Direct records | Recursive records | Direct documents | Recursive documents | Recursive MiB |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in inventory["hierarchy"]:
        path = str(item["path"]).replace("|", "\\|")
        lines.append(
            f"| `{path}` | {item['direct_records']} | {item['recursive_records']} | "
            f"{item['direct_documents']} | {item['recursive_documents']} | "
            f"{mib(item['recursive_logical_size_bytes'])} |"
        )
    lines.extend(
        [
            "",
            "## Workspace collection measurements",
            "",
            "| Collection | Files | Logical GiB | Allocated GiB | Allocation known | Aliases skipped | Errors |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in inventory["collections"]:
        lines.append(
            f"| `{item['source_uri']}` | {item['files_measured']} | {gib(item['logical_size_bytes'])} | "
            f"{gib(item['allocated_size_bytes'])} | {item['allocated_size_known_files']} | "
            f"{item['reparse_points_skipped']} | {len(item['scan_errors'])} |"
        )

    largest = sorted(inventory["records"], key=lambda item: item["logical_size_bytes"], reverse=True)[:20]
    lines.extend(
        [
            "",
            "## Largest measured inventory records",
            "",
            "| Source | Collection | Tier | Git | Logical MiB | Allocated MiB | Hash |",
            "| --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for record in largest:
        digest = record["sha256"][:12] if record["sha256"] else record["hash_state"]
        source = record["source_uri"].replace("|", "\\|")
        lines.append(
            f"| `{source}` | `{record['collection']}` | `{record['storage_tier']}` | "
            f"`{record['git_posture']}` | {mib(record['logical_size_bytes'])} | "
            f"{mib(record['allocated_size_bytes'])} | `{digest}` |"
        )

    lines.extend(["", "## Findings", ""])
    all_findings = list(inventory["findings"])
    for collection in inventory["collections"]:
        all_findings.extend(collection["scan_errors"])
    if all_findings:
        lines.extend(f"- {finding}" for finding in sorted(all_findings))
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Next gate",
            "",
            "Owner review selects the M2 classification population. Unknown or recovery-unproven artifacts remain Q5 or remain physically in place. Full hashing of large payloads is not implied by this report.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_inventory(inventory: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    """Validate the emitted contract with stdlib only; return every finding."""
    findings: list[str] = []
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read inventory schema {schema_path}: {exc}"]

    required_top = set(schema.get("required", []))
    missing_top = sorted(required_top - set(inventory))
    if missing_top:
        findings.append(f"inventory missing top-level field(s): {', '.join(missing_top)}")
    if inventory.get("schema") != SCHEMA_ID:
        findings.append(f"schema must be {SCHEMA_ID}")
    if inventory.get("inventory_lane_id") != INVENTORY_LANE:
        findings.append(f"inventory_lane_id must be {INVENTORY_LANE}")

    records = inventory.get("records")
    if not isinstance(records, list):
        return findings + ["records must be an array"]
    record_schema = schema["properties"]["records"]["items"]
    record_properties = record_schema["properties"]
    record_required = set(record_schema["required"])
    ids: set[str] = set()
    uris: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            findings.append(f"{prefix} must be an object")
            continue
        missing = sorted(record_required - set(record))
        extra = sorted(set(record) - set(record_properties))
        if missing:
            findings.append(f"{prefix} missing field(s): {', '.join(missing)}")
        if extra:
            findings.append(f"{prefix} has unsupported field(s): {', '.join(extra)}")
        for field, definition in record_properties.items():
            if field not in record:
                continue
            value = record[field]
            if "enum" in definition and value not in definition["enum"]:
                findings.append(f"{prefix}.{field} unsupported value: {value}")
            pattern = definition.get("pattern")
            if pattern and value is not None and (not isinstance(value, str) or re.fullmatch(pattern, value) is None):
                findings.append(f"{prefix}.{field} does not match {pattern}")
            if definition.get("minimum") == 0 and value is not None:
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    findings.append(f"{prefix}.{field} must be a non-negative integer or null")
        memory = record.get("memory_id")
        uri = record.get("source_uri")
        if memory in ids:
            findings.append(f"duplicate memory_id: {memory}")
        if uri in uris:
            findings.append(f"duplicate source_uri: {uri}")
        if isinstance(memory, str):
            ids.add(memory)
        if isinstance(uri, str):
            uris.add(uri)

    summary = inventory.get("summary", {})
    if not isinstance(summary, dict) or summary.get("records") != len(records):
        findings.append("summary.records does not equal the number of successful records")

    hierarchy = inventory.get("hierarchy")
    hierarchy_schema = schema["properties"]["hierarchy"]["items"]
    if not isinstance(hierarchy, list):
        findings.append("hierarchy must be an array")
    else:
        required_hierarchy = set(hierarchy_schema["required"])
        for index, row in enumerate(hierarchy):
            if not isinstance(row, dict):
                findings.append(f"hierarchy[{index}] must be an object")
                continue
            missing = sorted(required_hierarchy - set(row))
            if missing:
                findings.append(f"hierarchy[{index}] missing field(s): {', '.join(missing)}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--observed-at", default=None)
    parser.add_argument("--hash-max-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--no-external", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.hash_max_bytes < 0:
        print("memory-inventory: error -- hash-max-bytes must be non-negative", file=sys.stderr)
        return 2
    observed_at = args.observed_at
    if observed_at is None and args.check and args.out_json.is_file():
        try:
            prior = json.loads(args.out_json.read_text(encoding="utf-8"))
            observed_at = prior.get("generated_at_utc")
        except (OSError, ValueError, AttributeError):
            observed_at = None
    observed_at = observed_at or utc_now()
    try:
        inventory = build_inventory(
            repo_root=args.repo_root,
            observed_at_utc=observed_at,
            hash_max_bytes=args.hash_max_bytes,
            include_external=not args.no_external,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"memory-inventory: error -- {exc}", file=sys.stderr)
        return 1
    validation_findings = validate_inventory(inventory, args.schema)
    if validation_findings:
        print(
            f"memory-inventory: contract FAIL -- {len(validation_findings)} finding(s)",
            file=sys.stderr,
        )
        for finding in validation_findings:
            print(f"  - {finding}", file=sys.stderr)
        return 2
    json_text = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(inventory)
    if args.check:
        stale = []
        if not args.out_json.is_file() or args.out_json.read_text(encoding="utf-8") != json_text:
            stale.append(str(args.out_json))
        if not args.out_markdown.is_file() or args.out_markdown.read_text(encoding="utf-8") != markdown_text:
            stale.append(str(args.out_markdown))
        if stale:
            print(f"memory-inventory: stale -- {', '.join(stale)}")
            return 3
        print("memory-inventory: PASS -- generated reports are current")
        return 0
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json_text, encoding="utf-8")
    args.out_markdown.write_text(markdown_text, encoding="utf-8")
    print(
        f"memory-inventory: wrote {args.out_json} and {args.out_markdown} "
        f"({inventory['summary']['records']} records, "
        f"{inventory['summary']['hashes_computed']} hashes, "
        f"{inventory['summary']['reparse_points_skipped']} aliases skipped)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
