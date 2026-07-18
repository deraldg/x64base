from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json


def _latest_structural_dir(paths: ManualgenPaths) -> Path | None:
    root = paths.manualgen_root / "generated" / "manualgen_structural_reconciliations"
    candidates = []
    for directory in root.glob("MANRUN-*") if root.exists() else []:
        manifest = directory / "manual_structural_reconciliation_manifest.json"
        mapping = directory / "manual_topic_structural_mapping.csv"
        if manifest.exists() and mapping.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("status") == "PASS" and data.get("counts", {}).get("review_fallback_topics") == 0:
                candidates.append(directory)
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _parse_topic_blocks(disposition_dir: Path) -> tuple[dict[str, str], list[str]]:
    blocks: dict[str, str] = {}
    duplicates: list[str] = []
    key_pattern = re.compile(r"^- Key/status: `([^`]+)`", re.MULTILINE)
    for path in sorted(disposition_dir.glob("0[1-5]_*.md")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        starts = [index for index, line in enumerate(lines) if line.startswith("## ")]
        for pos, start in enumerate(starts):
            end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
            block = "\n".join(lines[start:end]).rstrip() + "\n"
            match = key_pattern.search(block)
            if not match:
                continue
            key = match.group(1)
            if key in blocks:
                duplicates.append(key)
            blocks[key] = block
    return blocks, duplicates


def build_section_delta_candidates(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    structural_dir = _latest_structural_dir(paths)
    if not structural_dir:
        return {"created": 0, "status": "FAIL"}, {"approved_topics": 0, "mapped_topics": 0, "missing_topic_blocks": 1, "duplicate_topic_blocks": 0, "target_packets": 0}
    structural_manifest_path = structural_dir / "manual_structural_reconciliation_manifest.json"
    structural_manifest = json.loads(structural_manifest_path.read_text(encoding="utf-8"))
    mapping_path = structural_dir / "manual_topic_structural_mapping.csv"
    mapping_rows = read_csv(mapping_path)
    disposition_dir = paths.repo_root / structural_manifest["input"]["approved_topics"]
    disposition_dir = disposition_dir.parent
    blocks, duplicate_blocks = _parse_topic_blocks(disposition_dir)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    missing_blocks = []
    for row in mapping_rows:
        key = row.get("topic_key", "")
        if key not in blocks:
            missing_blocks.append(key)
            continue
        grouped[row.get("target_slug", "")].append(row)

    run_id = logger.run_id if logger else "MANRUN-SECTION-DELTA-CANDIDATE"
    output_dir = paths.manualgen_root / "generated" / "manualgen_section_delta_candidates" / run_id
    packet_dir = output_dir / "sections"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_rows = []
    used_keys: list[str] = []
    for target in sorted(grouped):
        rows = sorted(grouped[target], key=lambda row: (row.get("catalog", ""), row.get("topic", ""), row.get("topic_key", "")))
        refresh = sum(row.get("delta_action") == "REFRESH_EXISTING_TOPIC" for row in rows)
        additions = len(rows) - refresh
        kind = "candidate_appendix" if target == "partial_help_reference" else "existing_section_delta"
        path = packet_dir / f"{target}_ADDITIVE_DELTA_CANDIDATE.md"
        body = [
            "<!-- Candidate-only additive delta packet. Not publication. -->",
            f"# {target.replace('_', ' ').title()} — Additive Delta Candidate",
            "",
            f"- Target: `{target}`",
            f"- Target kind: `{kind}`",
            f"- Topics: {len(rows)}",
            f"- Existing-topic refreshes: {refresh}",
            f"- Additions: {additions}",
            "- Replacement authorized: 0",
            "- Publication authority claimed: 0",
            "",
            "Every topic block below is copied intact from the approved disposition packets and remains subject to human prose review.",
            "",
        ]
        for row in rows:
            key = row["topic_key"]
            used_keys.append(key)
            body.extend([
                f"<!-- structural-map key={key} action={row.get('delta_action', '')} basis={row.get('mapping_basis', '')} confidence={row.get('mapping_confidence', '')} -->",
                blocks[key].rstrip(),
                "",
            ])
        path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        packet_rows.append({"target_slug": target, "target_kind": kind, "topic_count": len(rows), "refresh_existing_count": refresh, "add_topic_count": additions, "relative_path": relpath_posix(path, paths.repo_root), "sha256": sha256_file(path)})

    duplicate_used = len(used_keys) - len(set(used_keys))
    unused_blocks = sorted(set(blocks) - set(used_keys))
    status = "PASS" if len(mapping_rows) == 462 and len(blocks) == 462 and len(used_keys) == 462 and not missing_blocks and not duplicate_blocks and not duplicate_used and not unused_blocks and len(packet_rows) == 22 else "FAIL"
    packet_ledger = output_dir / "manual_section_delta_packet_ledger.csv"
    manifest_path = output_dir / "manual_section_delta_candidate_manifest.json"
    write_csv(packet_ledger, packet_rows)
    manifest = {
        "schema": "dottalk.manualgen.section_delta_candidate.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "status": status,
        "candidate_only": 1,
        "canonical_manual_mutated": 0,
        "reader_pointer_mutated": 0,
        "publication_authority_claimed": 0,
        "input": {
            "structural_run_id": structural_dir.name,
            "structural_manifest": relpath_posix(structural_manifest_path, paths.repo_root),
            "structural_manifest_sha256": sha256_file(structural_manifest_path),
            "topic_mapping": relpath_posix(mapping_path, paths.repo_root),
            "topic_mapping_sha256": sha256_file(mapping_path),
            "disposition_run_id": disposition_dir.name,
        },
        "counts": {
            "approved_topics": len(blocks),
            "mapped_topics": len(mapping_rows),
            "used_topic_blocks": len(used_keys),
            "target_packets": len(packet_rows),
            "missing_topic_blocks": len(missing_blocks),
            "duplicate_topic_blocks": len(duplicate_blocks) + duplicate_used,
            "unused_topic_blocks": len(unused_blocks),
        },
        "artifacts": {
            "packet_ledger": relpath_posix(packet_ledger, paths.repo_root),
            "packet_ledger_sha256": sha256_file(packet_ledger),
            "packets": packet_rows,
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("manual_section_delta_packet_ledger", packet_ledger, "Per-target additive delta packet ledger.")
        logger.artifact("manual_section_delta_candidate_manifest", manifest_path, "Hash-bound additive section delta candidate manifest.")
        for row in packet_rows:
            logger.artifact(f"section_delta_{row['target_slug']}", paths.repo_root / row["relative_path"], "Candidate-only additive delta packet.")
        for boundary in ("canonical_manual_mutated", "reader_pointer_mutated", "publication_authority_claimed", "source_help_metadata_mutated"):
            logger.boundary(boundary, 0, "PASS", "Candidate packet generation does not cross this boundary.")
    state = {"created": 1, "status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "manifest": relpath_posix(manifest_path, paths.repo_root)}
    return state, manifest["counts"]
