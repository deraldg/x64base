#!/usr/bin/env python3
"""Audit the Developer Manual authority pointers without mutating them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def normalized_repo_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def markdown_heading_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(
        1
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if re.match(r"^#{1,6}\s+\S", line)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = resolve_repo_path(repo_root, str(args.output_dir)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    root = repo_root / "docs" / "manuals" / "developer" / "manualgen"
    reader_pointer = root / "accepted_artifacts" / "ACTIVE_PRIMARY_READER_ARTIFACT.txt"
    reader_record_path = root / "accepted_artifacts" / "primary_reader_artifact_v1.json"
    manifest_pointer = root / "accepted_manifests" / "ACTIVE_MANUALGEN_MANIFEST.txt"
    publication_manifest_path = root / "manifests" / "manualgen_current_publication_manifest_v1.json"
    assembly_manifest_path = root / "manifests" / "manualgen_selected_assembly_manifest_v1.json"
    publication_role_index = root / "published" / "README.md"
    controlled_publication_status = root / "MDO-350E_DEVELOPER_MANUAL_CONTROLLED_PUBLICATION_REPLACEMENT_EXECUTION_STATUS.md"

    rows: list[dict[str, str]] = []

    def add(check_id: str, status: str, declared: object, observed: object, note: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "status": status,
                "declared": str(declared),
                "observed": str(observed),
                "note": note,
            }
        )

    required = {
        "ACTIVE_READER_POINTER_EXISTS": reader_pointer,
        "PRIMARY_READER_RECORD_EXISTS": reader_record_path,
        "ACTIVE_MANIFEST_POINTER_EXISTS": manifest_pointer,
        "LEGACY_NAMED_ASSEMBLY_MANIFEST_EXISTS": publication_manifest_path,
        "SELECTED_ASSEMBLY_MANIFEST_EXISTS": assembly_manifest_path,
    }
    for check_id, path in required.items():
        add(check_id, "PASS" if path.is_file() else "FAIL", "file", path.is_file(), normalized_repo_path(repo_root, path))

    if any(not path.is_file() for path in required.values()):
        payload = {"schema": "dottalk.fullstack.manual_pointer_audit.v1", "checks": rows}
        (output_dir / "manual_documentation_pointer_audit_v1.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return 1

    reader_target_text = reader_pointer.read_text(encoding="utf-8-sig").strip()
    reader_target = resolve_repo_path(repo_root, reader_target_text)
    reader_record = json.loads(reader_record_path.read_text(encoding="utf-8-sig"))
    manifest_target_text = manifest_pointer.read_text(encoding="utf-8-sig").strip()
    manifest_target = resolve_repo_path(repo_root, manifest_target_text)
    publication_manifest = json.loads(publication_manifest_path.read_text(encoding="utf-8-sig"))
    assembly_manifest = json.loads(assembly_manifest_path.read_text(encoding="utf-8-sig"))

    add("ACTIVE_READER_TARGET_EXISTS", "PASS" if reader_target.is_file() else "FAIL", reader_target_text, reader_target.is_file(), "Primary reader pointer target.")
    add(
        "PRIMARY_READER_RECORD_TARGET_MATCH",
        "PASS" if reader_record.get("primary_reader_artifact") == reader_target_text else "REVIEW",
        reader_record.get("primary_reader_artifact", ""),
        reader_target_text,
        "Record target should agree with the active pointer.",
    )

    reader_hash = sha256(reader_target) if reader_target.is_file() else ""
    stored_reader_hash = str(reader_record.get("artifact_sha256", "")).upper()
    add(
        "PRIMARY_READER_RECORDED_HASH_CURRENT",
        "PASS" if reader_hash and stored_reader_hash == reader_hash else "REVIEW",
        stored_reader_hash,
        reader_hash,
        "A mismatch means the pointer target changed after its evidence record was written.",
    )

    reader_lines = len(reader_target.read_text(encoding="utf-8-sig").splitlines()) if reader_target.is_file() else 0
    stored_lines = reader_record.get("artifact_lines", "")
    add(
        "PRIMARY_READER_RECORDED_LINES_CURRENT",
        "PASS" if str(stored_lines) == str(reader_lines) else "REVIEW",
        stored_lines,
        reader_lines,
        "Line-count evidence should describe the current pointer target.",
    )

    reader_headings = markdown_heading_count(reader_target)
    stored_headings = reader_record.get("artifact_heading_count", "")
    add(
        "PRIMARY_READER_RECORDED_HEADINGS_CURRENT",
        "PASS" if str(stored_headings) == str(reader_headings) else "REVIEW",
        stored_headings,
        reader_headings,
        "Heading-count evidence should describe the current pointer target.",
    )

    add("ACTIVE_MANIFEST_TARGET_EXISTS", "PASS" if manifest_target.is_file() else "FAIL", manifest_target_text, manifest_target.is_file(), "Accepted canonical manifest pointer target.")
    canonical = json.loads(manifest_target.read_text(encoding="utf-8-sig")) if manifest_target.is_file() else {}
    canonical_reference_text = str(canonical.get("current_reference_combined", ""))
    canonical_reference = resolve_repo_path(repo_root, canonical_reference_text) if canonical_reference_text else Path()
    canonical_reference_normalized = normalized_repo_path(repo_root, canonical_reference) if canonical_reference_text else ""
    add(
        "CANONICAL_REFERENCE_MATCHES_ACTIVE_READER",
        "PASS" if canonical_reference_text and canonical_reference.resolve() == reader_target.resolve() else "REVIEW",
        canonical_reference_normalized,
        normalized_repo_path(repo_root, reader_target),
        "Canonical current reference and primary reader should be intentionally reconciled.",
    )
    canonical_reference_hash = sha256(canonical_reference) if canonical_reference_text and canonical_reference.is_file() else ""
    stored_reference_hash = str(canonical.get("current_reference_sha256", "")).upper()
    add(
        "CANONICAL_REFERENCE_RECORDED_HASH_CURRENT",
        "PASS" if canonical_reference_hash and stored_reference_hash == canonical_reference_hash else "REVIEW",
        stored_reference_hash,
        canonical_reference_hash,
        "A mismatch means canonical evidence describes an earlier revision.",
    )

    publication_id = str(assembly_manifest.get("assembly_id") or assembly_manifest.get("publication_id", ""))
    publication_workspace_text = str(assembly_manifest.get("assembly_workspace") or assembly_manifest.get("publication_workspace", ""))
    publication_workspace = resolve_repo_path(repo_root, publication_workspace_text)
    publication_combined = publication_workspace / f"{publication_id}.md"
    assembly_role = str(assembly_manifest.get("manifest_role", ""))
    authority_claimed = int(assembly_manifest.get("publication_authority_claimed", 1))
    add("SELECTED_ASSEMBLY_WORKSPACE_EXISTS", "PASS" if publication_workspace.is_dir() else "FAIL", publication_workspace_text, publication_workspace.is_dir(), "Manifest-selected assembly workspace.")
    add("SELECTED_ASSEMBLY_COMBINED_EXISTS", "PASS" if publication_combined.is_file() else "FAIL", normalized_repo_path(repo_root, publication_combined), publication_combined.is_file(), "Expected combined Markdown for the selected assembly id.")
    add(
        "SELECTED_ASSEMBLY_AUTHORITY_NOT_CLAIMED",
        "PASS" if assembly_role == "selected_assembly_reference" and authority_claimed == 0 else "FAIL",
        f"role={assembly_role};publication_authority_claimed={authority_claimed}",
        "role=selected_assembly_reference;publication_authority_claimed=0",
        "Assembly selection must not silently claim reader or publication authority.",
    )

    if publication_role_index.is_file():
        role_text = publication_role_index.read_text(encoding="utf-8-sig")
        reader_role_path = reader_target.relative_to(root / "published").as_posix()
        publication_role_path = publication_workspace.relative_to(root / "published").as_posix() + "/"
        add(
            "PRIMARY_READER_ROLE_INDEXED",
            "PASS" if reader_role_path in role_text else "REVIEW",
            reader_role_path,
            reader_role_path in role_text,
            "Published-lane role index should name the active primary reader.",
        )
        supporting_indexed = publication_role_path in role_text and "Supporting publication workspaces" in role_text
        add(
            "SELECTED_ASSEMBLY_ROLE_INDEXED",
            "PASS" if supporting_indexed else "REVIEW",
            publication_role_path,
            "SUPPORTING" if supporting_indexed else "NOT_MARKED_SUPPORTING",
            "A selected supporting workspace is valid only when its non-authoritative role is explicit and indexed.",
        )
        add(
            "SELECTED_ASSEMBLY_ROLE_SEPARATE_FROM_ACTIVE_READER",
            "PASS" if supporting_indexed and authority_claimed == 0 else "REVIEW",
            normalized_repo_path(repo_root, publication_combined),
            normalized_repo_path(repo_root, reader_target),
            "Different assembly and reader targets are an intentional role split when authority is not claimed.",
        )

    if controlled_publication_status.is_file():
        controlled_text = controlled_publication_status.read_text(encoding="utf-8-sig")
        target_match = re.search(r"^- Active publication target: `([^`]+)`", controlled_text, re.MULTILINE)
        hash_match = re.search(r"^- Active hash after: `([0-9a-fA-F]+)`", controlled_text, re.MULTILINE)
        controlled_target_text = target_match.group(1) if target_match else ""
        controlled_target = resolve_repo_path(repo_root, controlled_target_text) if controlled_target_text else Path()
        controlled_hash = sha256(controlled_target) if controlled_target_text and controlled_target.is_file() else ""
        recorded_controlled_hash = hash_match.group(1).upper() if hash_match else ""
        add(
            "CONTROLLED_PUBLICATION_TARGET_EXISTS",
            "PASS" if controlled_target_text and controlled_target.is_file() else "FAIL",
            controlled_target_text,
            controlled_target.is_file() if controlled_target_text else False,
            "MDO-350E controlled publication replacement target.",
        )
        add(
            "CONTROLLED_PUBLICATION_RECORDED_HASH_CURRENT",
            "PASS" if controlled_hash and controlled_hash == recorded_controlled_hash else "REVIEW",
            recorded_controlled_hash,
            controlled_hash,
            "MDO-350E target remains byte-identical when this passes.",
        )
        add(
            "CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER",
            "PASS" if controlled_target_text and controlled_target.resolve() == reader_target.resolve() else "REVIEW",
            normalized_repo_path(repo_root, controlled_target) if controlled_target_text else "",
            normalized_repo_path(repo_root, reader_target),
            "MDO-350E and the active primary-reader pointer currently name different publication roles.",
        )

    summary = {
        "pass": sum(row["status"] == "PASS" for row in rows),
        "review": sum(row["status"] == "REVIEW" for row in rows),
        "fail": sum(row["status"] == "FAIL" for row in rows),
    }
    payload = {
        "schema": "dottalk.fullstack.manual_pointer_audit.v1",
        "repo_root": str(repo_root),
        "summary": summary,
        "active_reader": {
            "pointer": normalized_repo_path(repo_root, reader_pointer),
            "target": normalized_repo_path(repo_root, reader_target),
            "sha256": reader_hash,
            "lines": reader_lines,
            "headings": reader_headings,
        },
        "canonical_manifest": normalized_repo_path(repo_root, manifest_target),
        "legacy_named_assembly_manifest": normalized_repo_path(repo_root, publication_manifest_path),
        "selected_assembly_manifest": normalized_repo_path(repo_root, assembly_manifest_path),
        "checks": rows,
    }

    csv_path = output_dir / "manual_documentation_pointer_audit_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["check_id", "status", "declared", "observed", "note"])
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_dir / "manual_documentation_pointer_audit_v1.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Developer Manual Pointer Audit V1",
        "",
        f"- PASS: {summary['pass']}",
        f"- REVIEW: {summary['review']}",
        f"- FAIL: {summary['fail']}",
        f"- active reader: `{payload['active_reader']['target']}`",
        f"- active reader SHA-256: `{reader_hash}`",
        "",
        "| Check | Status | Declared | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        declared = row["declared"].replace("|", "\\|")
        observed = row["observed"].replace("|", "\\|")
        md_lines.append(f"| {row['check_id']} | {row['status']} | `{declared}` | `{observed}` |")
    md_lines.extend(["", "This audit is report-only. It does not promote a manifest, replace a publication, update a reader pointer, or mutate MAN* catalogs.", ""])
    (output_dir / "MANUAL_DOCUMENTATION_POINTER_AUDIT_V1.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"pointer_audit pass={summary['pass']} review={summary['review']} fail={summary['fail']}")
    print(f"active_reader_sha256={reader_hash}")
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
