#!/usr/bin/env python3
"""Build the non-destructive AIF-136 M2 classification and lineage report.

This tool consumes the M1 inventory. It does not open database payloads, hash
deferred files, select a duplicate survivor, declare supersession, move data,
or authorize reclamation. Its classifications and lineage links are proposals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from ai_portal.build_memory_storage_inventory import REPO_ROOT, walk_files
except ModuleNotFoundError:  # Direct script execution from this directory.
    from build_memory_storage_inventory import REPO_ROOT, walk_files


LABTALK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = LABTALK_ROOT / "reports" / "portal" / "memory_storage_inventory_latest.json"
DEFAULT_JSON = LABTALK_ROOT / "reports" / "portal" / "memory_storage_classification_latest.json"
DEFAULT_MARKDOWN = LABTALK_ROOT / "reports" / "portal" / "memory_storage_classification_latest.md"
DEFAULT_SCHEMA = Path(__file__).resolve().parent / "schemas" / "portal_memory_classification_v1.schema.json"
DEFAULT_PILOT_MANIFEST = LABTALK_ROOT / "registries" / "aif136_memory_pilot_manifest_v1.json"
SCHEMA_ID = "dottalk.portal.memory-classification.v1"
LANE_ID = "AIF-136"

AUTHORITY_VALUES = {
    "authority", "governance_authority", "reviewed_derivative",
    "generated_projection", "unknown",
}
TIER_VALUES = {"F0", "F1", "W2", "C3", "R4", "Q5"}
SENSITIVITY_VALUES = {"public", "development_only", "private", "secret", "unknown"}
RECOVERY_POSTURES = {
    "not_applicable", "candidate_inputs_found", "container_candidate_only",
    "source_candidate_only", "inputs_not_found",
}


def stable_id(prefix: str, values: list[str]) -> str:
    body = "\n".join(sorted(values, key=str.lower)).encode("utf-8")
    return f"{prefix}.{hashlib.sha256(body).hexdigest()[:16]}"


def classify_record(record: dict[str, Any]) -> tuple[str, str, str, list[str]]:
    """Return proposed authority, tier, sensitivity, and explicit rationale."""
    uri = str(record["source_uri"]).replace("\\", "/")
    lower = uri.lower()
    collection = record["collection"]
    kind = record["artifact_kind"]
    sensitivity = record.get("sensitivity", "unknown")
    rationale: list[str] = []

    if collection == "docs_lmdb":
        return (
            "generated_projection", "R4", "development_only",
            ["LMDB data.mdb is a generated projection; reconstruction is not yet proven per specimen."],
        )
    if collection == "claims":
        return (
            "governance_authority", "F1", "development_only",
            ["Active AIF claim files coordinate lane ownership and must remain rapidly reachable."],
        )
    if collection == "frontal_mem_external":
        return (
            "unknown", "Q5", "private",
            ["External owner-controlled memory needs an explicit authority and custody ruling before demotion."],
        )
    if lower == "labtalk/ai_portal/ai_tier1_seed_v1.md":
        return (
            "governance_authority", "F0", "development_only",
            ["Canonical Tier 1 onboarding seed named by the repository role instructions."],
        )
    if lower in {"agents.md", "claude.md"}:
        return (
            "reviewed_derivative", "F0", "development_only",
            ["Always-read agent shim; authoritative details remain behind maintained pointers."],
        )
    if collection == "frontal":
        return (
            "reviewed_derivative", "F1", "development_only",
            ["Current routing surface intended for fast onboarding; underlying authorities remain cited."],
        )
    if collection == "ai_friendly":
        return (
            "governance_authority", "W2", "development_only",
            ["Tracked AI-friendly governance or operating body; retain warm until an owner narrows its role."],
        )
    if collection == "portal_core" and kind in {"source", "registry_or_schema"}:
        return (
            "authority", "W2", "development_only",
            ["Tracked Portal source, registry, or schema is authoritative for the behavior it defines."],
        )
    if collection == "portal_core":
        rationale.append("Tracked Portal document is a reviewed derivative unless a narrower authority is registered.")
        return "reviewed_derivative", "W2", "development_only", rationale

    return (
        "unknown", "Q5", sensitivity if sensitivity in SENSITIVITY_VALUES else "unknown",
        ["No conservative authority rule matched; quarantine is a classification state, not a file move."],
    )


def exact_duplicate_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        digest = record.get("sha256")
        if record.get("hash_state") == "computed" and isinstance(digest, str):
            by_hash[digest].append(record)
    groups = []
    for digest, members in sorted(by_hash.items()):
        if len(members) < 2:
            continue
        ids = sorted((item["memory_id"] for item in members), key=str.lower)
        groups.append({
            "group_id": stable_id("duplicate", ids),
            "sha256": digest,
            "logical_size_bytes": members[0]["logical_size_bytes"],
            "memory_ids": ids,
            "decision_state": "candidate_only",
        })
    return groups


_VERSION_TOKEN = re.compile(
    r"(?ix)(?:^|[_-])(?:v(?:er(?:sion)?)?\d+(?:\.\d+)*|20\d{6}(?:[_-]\d{6})?|copy\d*)(?=$|[_-])"
)


def normalized_family_key(uri: str) -> str | None:
    path = PurePosixPath(uri.replace("\\", "/"))
    stem = path.stem.lower()
    normalized = _VERSION_TOKEN.sub("_", stem)
    normalized = re.sub(r"[_-]+", "_", normalized).strip("_")
    if not normalized or normalized == stem:
        return None
    return f"{str(path.parent).lower()}|{normalized}|{path.suffix.lower()}"


def version_family_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("artifact_kind") == "database_derived":
            continue
        key = normalized_family_key(str(record["source_uri"]))
        if key:
            families[key].append(record)
    groups = []
    for key, members in sorted(families.items()):
        if len(members) < 2:
            continue
        ids = sorted((item["memory_id"] for item in members), key=str.lower)
        groups.append({
            "group_id": stable_id("family", ids),
            "family_key": key,
            "memory_ids": ids,
            "decision_state": "candidate_only",
        })
    return groups


def lmdb_expected_names(source_uri: str) -> tuple[str | None, str | None]:
    parent = PurePosixPath(source_uri.replace("\\", "/")).parent.name
    parent = re.sub(r"_20\d{6}(?:_\d{6})?$", "", parent, flags=re.IGNORECASE)
    if not parent.lower().endswith(".d"):
        return None, None
    container = parent[:-2]
    if not container.lower().endswith((".cdx", ".cnx")):
        return None, None
    return container.lower(), f"{PurePosixPath(container).stem.lower()}.dbf"


def common_prefix_depth(left: str, right: str) -> int:
    left_parts = [part.lower() for part in PurePosixPath(left).parts]
    right_parts = [part.lower() for part in PurePosixPath(right).parts]
    depth = 0
    for first, second in zip(left_parts, right_parts):
        if first != second:
            break
        depth += 1
    return depth


def rank_candidates(source_uri: str, candidates: list[str], limit: int = 5) -> list[str]:
    return sorted(
        candidates,
        key=lambda item: (-common_prefix_depth(source_uri, item), len(item), item.lower()),
    )[:limit]


def build_recovery_index(repo_root: Path) -> tuple[dict[str, list[str]], list[str]]:
    files, _skipped, errors = walk_files(repo_root / "docs")
    index: dict[str, list[str]] = defaultdict(list)
    for path in files:
        if path.suffix.lower() not in {".cdx", ".cnx", ".dbf"}:
            continue
        try:
            uri = path.resolve(strict=False).relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            continue
        index[path.name.lower()].append(uri)
    return {key: sorted(values, key=str.lower) for key, values in index.items()}, errors


def recovery_for(record: dict[str, Any], index: dict[str, list[str]]) -> dict[str, Any]:
    if record.get("collection") != "docs_lmdb":
        return {
            "posture": "not_applicable", "container_candidates": [],
            "source_candidates": [], "state": "not_applicable",
        }
    container_name, source_name = lmdb_expected_names(record["source_uri"])
    containers = rank_candidates(record["source_uri"], index.get(container_name or "", []))
    sources = rank_candidates(record["source_uri"], index.get(source_name or "", []))
    if containers and sources:
        posture = "candidate_inputs_found"
    elif containers:
        posture = "container_candidate_only"
    elif sources:
        posture = "source_candidate_only"
    else:
        posture = "inputs_not_found"
    return {
        "posture": posture,
        "container_candidates": containers,
        "source_candidates": sources,
        "state": "unverified",
    }


def apply_approved_pilot(
    classifications: list[dict[str, Any]], pilot_manifest: dict[str, Any] | None
) -> int:
    """Apply only exact owner-approved cognitive overrides; return applied count."""
    if not pilot_manifest or pilot_manifest.get("ruling_state") != "approved":
        return 0
    if pilot_manifest.get("operation") != "cognitive_demotion_only":
        raise ValueError("approved pilot operation must remain cognitive_demotion_only")
    if pilot_manifest.get("physical_action") != "none_authorized":
        raise ValueError("approved pilot cannot authorize physical action")
    by_id = {item["memory_id"]: item for item in classifications}
    items = pilot_manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("approved pilot must contain exact items")
    applied = 0
    for item in items:
        memory_id = item.get("memory_id")
        row = by_id.get(memory_id)
        if row is None:
            raise ValueError(f"approved pilot memory_id is absent from classification: {memory_id}")
        if row["source_uri"] != item.get("source_uri"):
            raise ValueError(f"approved pilot source mismatch for {memory_id}")
        if item.get("current_tier") != "W2" or item.get("proposed_tier") != "C3":
            raise ValueError(f"approved pilot tier transition must be W2 to C3 for {memory_id}")
        if item.get("physical_move") is not False or item.get("source_deletion") is not False:
            raise ValueError(f"approved pilot attempts physical mutation for {memory_id}")
        row["proposed_storage_tier"] = "C3"
        row["classification_state"] = "owner_confirmed"
        row["owner_ruling_manifest"] = "labtalk/registries/aif136_memory_pilot_manifest_v1.json"
        row["rationale"] = list(row["rationale"]) + [item["reason"]]
        applied += 1
    return applied


def build_classification(
    inventory: dict[str, Any], *, repo_root: Path,
    pilot_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if inventory.get("schema") != "dottalk.portal.memory-inventory.v1":
        raise ValueError("input is not a dottalk.portal.memory-inventory.v1 inventory")
    records = inventory.get("records")
    if not isinstance(records, list):
        raise ValueError("input inventory records must be an array")

    duplicate_groups = exact_duplicate_groups(records)
    family_groups = version_family_groups(records)
    duplicate_by_id = {
        memory_id: group["group_id"] for group in duplicate_groups for memory_id in group["memory_ids"]
    }
    family_by_id = {
        memory_id: group["group_id"] for group in family_groups for memory_id in group["memory_ids"]
    }
    recovery_index, scan_findings = build_recovery_index(repo_root)

    classifications = []
    for record in sorted(records, key=lambda item: item["source_uri"].lower()):
        authority, tier, sensitivity, rationale = classify_record(record)
        duplicate_id = duplicate_by_id.get(record["memory_id"])
        family_id = family_by_id.get(record["memory_id"])
        related = []
        for groups, group_id in ((duplicate_groups, duplicate_id), (family_groups, family_id)):
            if group_id:
                group = next(item for item in groups if item["group_id"] == group_id)
                related.extend(item for item in group["memory_ids"] if item != record["memory_id"])
        if duplicate_id and family_id:
            lineage_state = "exact_duplicate_and_version_family_candidate"
        elif duplicate_id:
            lineage_state = "exact_duplicate_candidate"
        elif family_id:
            lineage_state = "version_family_candidate"
        else:
            lineage_state = "no_candidate"
        recovery = recovery_for(record, recovery_index)
        classifications.append({
            "memory_id": record["memory_id"],
            "source_uri": record["source_uri"],
            "collection": record["collection"],
            "artifact_kind": record["artifact_kind"],
            "proposed_authority_class": authority,
            "proposed_storage_tier": tier,
            "sensitivity": sensitivity,
            "classification_state": "heuristic_proposal",
            "owner_ruling_manifest": None,
            "rationale": rationale,
            "exact_duplicate_group_id": duplicate_id,
            "version_family_group_id": family_id,
            "lineage_state": lineage_state,
            "related_memory_ids": sorted(set(related), key=str.lower),
            "recovery_posture": recovery["posture"],
            "recovery_state": recovery["state"],
            "container_candidates": recovery["container_candidates"],
            "source_candidates": recovery["source_candidates"],
            "physical_action": "none_authorized",
        })

    owner_confirmed = apply_approved_pilot(classifications, pilot_manifest)

    authority_counts = Counter(item["proposed_authority_class"] for item in classifications)
    tier_counts = Counter(item["proposed_storage_tier"] for item in classifications)
    sensitivity_counts = Counter(item["sensitivity"] for item in classifications)
    recovery_counts = Counter(item["recovery_posture"] for item in classifications)
    return {
        "schema": SCHEMA_ID,
        "generated_at_utc": inventory["generated_at_utc"],
        "mode": "development_read_only",
        "classification_lane_id": LANE_ID,
        "source_inventory": DEFAULT_INVENTORY.relative_to(LABTALK_ROOT.parent).as_posix(),
        "source_inventory_generated_at_utc": inventory["generated_at_utc"],
        "policy": {
            "classification_authority": "proposal_with_exact_owner_overrides",
            "opens_database_payloads": False,
            "hashes_deferred_payloads": False,
            "declares_supersession": False,
            "selects_duplicate_survivor": False,
            "moves_or_deletes": False,
        },
        "summary": {
            "records": len(classifications),
            "owner_confirmed_records": owner_confirmed,
            "unknown_authority_records": authority_counts.get("unknown", 0),
            "quarantine_tier_records": tier_counts.get("Q5", 0),
            "exact_duplicate_groups": len(duplicate_groups),
            "exact_duplicate_records": sum(len(item["memory_ids"]) for item in duplicate_groups),
            "version_family_groups": len(family_groups),
            "version_family_records": sum(len(item["memory_ids"]) for item in family_groups),
            "by_authority_class": dict(sorted(authority_counts.items())),
            "by_storage_tier": dict(sorted(tier_counts.items())),
            "by_sensitivity": dict(sorted(sensitivity_counts.items())),
            "by_recovery_posture": dict(sorted(recovery_counts.items())),
            "scan_findings": len(scan_findings),
        },
        "exact_duplicate_groups": duplicate_groups,
        "version_family_groups": family_groups,
        "classifications": classifications,
        "findings": sorted(scan_findings),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# AI Portal Memory Classification and Lineage",
        "",
        "Generated by AIF-136 M2 from the M1 inventory. Do not hand-edit.",
        "",
        f"Inventory observation UTC: `{report['source_inventory_generated_at_utc']}`",
        "",
        "## Boundary",
        "",
        "Every classification, duplicate link, version-family link, and recovery input is a review candidate. This report does not declare a document superseded, choose a survivor, approve a move, reclaim storage, or open a database payload.",
        "",
        "## Summary",
        "",
        f"- Records classified: {summary['records']}",
        f"- Owner-confirmed cognitive overrides: {summary['owner_confirmed_records']}",
        f"- Unknown authority / Q5: {summary['unknown_authority_records']} / {summary['quarantine_tier_records']}",
        f"- Exact duplicate candidates: {summary['exact_duplicate_groups']} groups across {summary['exact_duplicate_records']} records",
        f"- Version-family candidates: {summary['version_family_groups']} groups across {summary['version_family_records']} records",
        f"- Recovery-index scan findings: {summary['scan_findings']}",
        "",
        "## Classification counts",
        "",
        "| Dimension | Value | Records |",
        "| --- | --- | ---: |",
    ]
    for dimension in ("by_authority_class", "by_storage_tier", "by_sensitivity", "by_recovery_posture"):
        for value, count in summary[dimension].items():
            lines.append(f"| `{dimension[3:]}` | `{value}` | {count} |")

    lines.extend(["", "## Exact duplicate candidates", ""])
    if report["exact_duplicate_groups"]:
        lines.extend(["| Group | Records | Bytes each | SHA-256 |", "| --- | ---: | ---: | --- |"]) 
        for group in report["exact_duplicate_groups"]:
            lines.append(f"| `{group['group_id']}` | {len(group['memory_ids'])} | {group['logical_size_bytes']} | `{group['sha256'][:16]}...` |")
    else:
        lines.append("- None among M1-computed hashes. Deferred hashes were not grouped.")

    lines.extend(["", "## Version-family candidates", ""])
    if report["version_family_groups"]:
        lines.extend(["| Group | Records | Conservative family key |", "| --- | ---: | --- |"])
        for group in report["version_family_groups"]:
            key = group["family_key"].replace("|", "\\|")
            lines.append(f"| `{group['group_id']}` | {len(group['memory_ids'])} | `{key}` |")
    else:
        lines.append("- None.")

    lmdb_rows = [
        item for item in report["classifications"]
        if item["collection"] == "docs_lmdb" and item["recovery_posture"] != "candidate_inputs_found"
    ]
    lines.extend([
        "", "## LMDB reconstruction-input candidates", "",
        "A matching CDX/CNX or DBF path is only a name-and-locality candidate. It is not reconstruction proof.",
        "The full candidate lists are in the JSON report; this frontal summary shows exceptions only.",
        "", "| LMDB exception | Posture | Container candidates | Source candidates |",
        "| --- | --- | ---: | ---: |",
    ])
    if lmdb_rows:
        for item in lmdb_rows:
            source = item["source_uri"].replace("|", "\\|")
            lines.append(f"| `{source}` | `{item['recovery_posture']}` | {len(item['container_candidates'])} | {len(item['source_candidates'])} |")
    else:
        lines.append("| None | -- | -- | -- |")

    lines.extend([
        "", "## Next gate", "",
        "The approved three-item M3 manifest is projected as owner-confirmed C3 cognitive tiering. No physical action is authorized. Unknown authority remains Q5.", "",
    ])
    return "\n".join(lines)


def validate_classification(report: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    findings: list[str] = []
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read classification schema {schema_path}: {exc}"]
    missing_top = sorted(set(schema["required"]) - set(report))
    extra_top = sorted(set(report) - set(schema["properties"]))
    if missing_top:
        findings.append(f"report missing top-level field(s): {', '.join(missing_top)}")
    if extra_top:
        findings.append(f"report has unsupported top-level field(s): {', '.join(extra_top)}")
    if report.get("schema") != SCHEMA_ID:
        findings.append(f"schema must be {SCHEMA_ID}")
    rows = report.get("classifications")
    if not isinstance(rows, list):
        return findings + ["classifications must be an array"]
    definition = schema["properties"]["classifications"]["items"]
    required = set(definition["required"])
    properties = definition["properties"]
    ids: set[str] = set()
    uris: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"classifications[{index}]"
        if not isinstance(row, dict):
            findings.append(f"{prefix} must be an object")
            continue
        missing = sorted(required - set(row))
        extra = sorted(set(row) - set(properties))
        if missing:
            findings.append(f"{prefix} missing field(s): {', '.join(missing)}")
        if extra:
            findings.append(f"{prefix} has unsupported field(s): {', '.join(extra)}")
        for field, allowed in (
            ("proposed_authority_class", AUTHORITY_VALUES),
            ("proposed_storage_tier", TIER_VALUES),
            ("sensitivity", SENSITIVITY_VALUES),
            ("recovery_posture", RECOVERY_POSTURES),
        ):
            if row.get(field) not in allowed:
                findings.append(f"{prefix}.{field} unsupported value: {row.get(field)}")
        memory_id = row.get("memory_id")
        source_uri = row.get("source_uri")
        if memory_id in ids:
            findings.append(f"duplicate memory_id: {memory_id}")
        if source_uri in uris:
            findings.append(f"duplicate source_uri: {source_uri}")
        if isinstance(memory_id, str):
            ids.add(memory_id)
        if isinstance(source_uri, str):
            uris.add(source_uri)
        if row.get("proposed_authority_class") == "unknown" and row.get("proposed_storage_tier") != "Q5":
            findings.append(f"{prefix}: unknown authority must remain Q5")
        if row.get("physical_action") != "none_authorized":
            findings.append(f"{prefix}: physical_action must remain none_authorized")
        if row.get("classification_state") == "owner_confirmed" and not row.get("owner_ruling_manifest"):
            findings.append(f"{prefix}: owner_confirmed requires owner_ruling_manifest")
        if row.get("classification_state") != "owner_confirmed" and row.get("owner_ruling_manifest") is not None:
            findings.append(f"{prefix}: unconfirmed classification cannot cite an owner ruling")
        related = row.get("related_memory_ids", [])
        if isinstance(memory_id, str) and memory_id in related:
            findings.append(f"{prefix}: related_memory_ids must not contain self")
    if report.get("summary", {}).get("records") != len(rows):
        findings.append("summary.records does not equal classifications length")

    group_ids: dict[str, set[str]] = {}
    for field, id_prefix in (("exact_duplicate_groups", "duplicate."), ("version_family_groups", "family.")):
        groups = report.get(field)
        if not isinstance(groups, list):
            findings.append(f"{field} must be an array")
            continue
        group_schema = schema["properties"][field]["items"]
        required_group = set(group_schema["required"])
        group_properties = set(group_schema["properties"])
        for index, group in enumerate(groups):
            prefix = f"{field}[{index}]"
            if not isinstance(group, dict):
                findings.append(f"{prefix} must be an object")
                continue
            missing = sorted(required_group - set(group))
            extra = sorted(set(group) - group_properties)
            if missing:
                findings.append(f"{prefix} missing field(s): {', '.join(missing)}")
            if extra:
                findings.append(f"{prefix} has unsupported field(s): {', '.join(extra)}")
            group_id = group.get("group_id")
            members = group.get("memory_ids")
            if not isinstance(group_id, str) or not group_id.startswith(id_prefix):
                findings.append(f"{prefix}.group_id must begin {id_prefix}")
                continue
            if group_id in group_ids:
                findings.append(f"duplicate lineage group_id: {group_id}")
            if not isinstance(members, list) or len(members) < 2 or len(members) != len(set(members)):
                findings.append(f"{prefix}.memory_ids must contain at least two unique values")
                continue
            missing_members = sorted(set(members) - ids)
            if missing_members:
                findings.append(f"{prefix} references unknown memory_id(s): {', '.join(missing_members)}")
            if group.get("decision_state") != "candidate_only":
                findings.append(f"{prefix}.decision_state must remain candidate_only")
            group_ids[group_id] = set(members)

    for index, row in enumerate(rows):
        memory_id = row.get("memory_id")
        for field in ("exact_duplicate_group_id", "version_family_group_id"):
            group_id = row.get(field)
            if group_id is not None and (group_id not in group_ids or memory_id not in group_ids[group_id]):
                findings.append(f"classifications[{index}].{field} has a dangling or inconsistent group reference")
        related = row.get("related_memory_ids", [])
        if isinstance(related, list):
            missing_related = sorted(set(related) - ids)
            if missing_related:
                findings.append(f"classifications[{index}] references unknown related memory_id(s): {', '.join(missing_related)}")

    summary = report.get("summary", {})
    expected = {
        "unknown_authority_records": sum(row.get("proposed_authority_class") == "unknown" for row in rows),
        "quarantine_tier_records": sum(row.get("proposed_storage_tier") == "Q5" for row in rows),
        "exact_duplicate_groups": len(report.get("exact_duplicate_groups", [])),
        "version_family_groups": len(report.get("version_family_groups", [])),
        "owner_confirmed_records": sum(row.get("classification_state") == "owner_confirmed" for row in rows),
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            findings.append(f"summary.{field} must equal {value}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--pilot-manifest", type=Path, default=DEFAULT_PILOT_MANIFEST)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        pilot_manifest = json.loads(args.pilot_manifest.read_text(encoding="utf-8"))
        report = build_classification(
            inventory, repo_root=args.repo_root.resolve(), pilot_manifest=pilot_manifest
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"memory-classification: error -- {exc}", file=sys.stderr)
        return 1
    findings = validate_classification(report, args.schema)
    if findings:
        print(f"memory-classification: contract FAIL -- {len(findings)} finding(s)", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 2
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(report)
    if args.check:
        stale = []
        if not args.out_json.is_file() or args.out_json.read_text(encoding="utf-8") != json_text:
            stale.append(str(args.out_json))
        if not args.out_markdown.is_file() or args.out_markdown.read_text(encoding="utf-8") != markdown_text:
            stale.append(str(args.out_markdown))
        if stale:
            print(f"memory-classification: stale -- {', '.join(stale)}")
            return 3
        print("memory-classification: PASS -- generated reports are current")
        return 0
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json_text, encoding="utf-8")
    args.out_markdown.write_text(markdown_text, encoding="utf-8")
    print(f"memory-classification: wrote {len(report['classifications'])} records; no physical action authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
