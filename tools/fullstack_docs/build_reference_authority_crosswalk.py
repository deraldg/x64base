#!/usr/bin/env python3
"""Build a provenance-bearing command/function/argument identity crosswalk."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")
FIELDS = ["logical_id", "entity_type", "canonical_name", "owner_kind", "owner_name", "kind", "arg_name", "legacy_id", "primary_authority", "contributing_authorities", "evidence_paths", "source_state", "validation_state", "conflict_disposition", "contract", "authority_map_sha256"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def command_row(row: dict[str, str], map_hash: str, contract: str) -> dict[str, str] | None:
    if row["classification"] == "EDUCATIONAL_TOPIC":
        return None
    name = norm(row["identity"])
    authorities: list[str] = []
    if truth(row["in_static_registry"]): authorities.append("AUTH-SOURCE-COMMAND-REGISTRY")
    if truth(row["in_usage_contract"]): authorities.append("AUTH-SOURCE-USAGE-CONTRACT")
    if any(truth(row[key]) for key in ("in_dotref", "in_foxref", "in_edref")): authorities.append("AUTH-SOURCE-REF-CATALOGS")
    authorities.append("AUTH-IDENTITY-JOIN")
    primary = next((value for value in ("AUTH-SOURCE-COMMAND-REGISTRY", "AUTH-SOURCE-USAGE-CONTRACT", "AUTH-SOURCE-REF-CATALOGS") if value in authorities), "AUTH-IDENTITY-JOIN")
    aligned = row["classification"] == "ALIGNED_COMMAND"
    evidence = [f"dotref={row['dotref_evidence']}", f"foxref={row['foxref_evidence']}", f"edref={row['edref_evidence']}", f"registry={row['registry_evidence']}", f"usage={row['usage_evidence']}"]
    return {"logical_id": f"CMD:{name}", "entity_type": "COMMAND", "canonical_name": name, "owner_kind": "", "owner_name": "", "kind": "", "arg_name": "", "legacy_id": name, "primary_authority": primary, "contributing_authorities": " | ".join(authorities), "evidence_paths": " | ".join(item for item in evidence if not item.endswith("=")), "source_state": row["classification"], "validation_state": "ALIGNED" if aligned else "REVIEW", "conflict_disposition": "" if aligned else "PRESENCE_GAP_REVIEW", "contract": contract, "authority_map_sha256": map_hash}


def function_row(row: dict[str, str], map_hash: str, contract: str) -> dict[str, str]:
    name = norm(row["CAN_NAME"])
    primary = "AUTH-SOURCE-FUNCTION-CATALOG" if row["SRC_AUTH"] == "function_catalog" else "AUTH-RUNTIME-BUILTIN-SPECS"
    return {"logical_id": f"FN:{name}", "entity_type": "FUNCTION", "canonical_name": name, "owner_kind": "", "owner_name": row["OWNER"], "kind": row["FUNC_CAT"], "arg_name": "", "legacy_id": row["FUNC_ID"], "primary_authority": primary, "contributing_authorities": f"{primary} | AUTH-METACOLLECT", "evidence_paths": row["SRC_FILE"], "source_state": row["IMPL_STAT"], "validation_state": "CANDIDATE_SOURCE_DEFINED", "conflict_disposition": "RUNTIME_PROOF_PENDING", "contract": contract, "authority_map_sha256": map_hash}


def argument_row(row: dict[str, str], map_hash: str, contract: str) -> dict[str, str]:
    owner_kind, owner_name, kind, arg_name = (norm(row[key]) for key in ("OWNER_KND", "OWNER_NAM", "ARG_KIND", "ARG_NAME"))
    primary = "AUTH-SOURCE-USAGE-CONTRACT" if row["SRC_AUTH"] == "usage_contract_v1" else "AUTH-METACOLLECT"
    return {"logical_id": f"ARG:{owner_kind}:{owner_name}:{kind}:{arg_name}", "entity_type": "ARGUMENT", "canonical_name": "", "owner_kind": owner_kind, "owner_name": owner_name, "kind": kind, "arg_name": arg_name, "legacy_id": row["ARG_ID"], "primary_authority": primary, "contributing_authorities": f"{primary} | AUTH-METACOLLECT", "evidence_paths": row["SRC_FILE"], "source_state": f"required={row['REQUIRED']};repeatable={row['REPEAT']};shape={row['VAL_SHAPE']}", "validation_state": "CANDIDATE_SOURCE_DEFINED", "conflict_disposition": "RUNTIME_PROOF_PENDING", "contract": contract, "authority_map_sha256": map_hash}


def build(repo: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    authority_path = repo / "selfdoc/reference_identity_authority_v1.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    inputs = {row["evidence_id"]: repo / row["path"] for row in authority["evidence_inputs"]}
    map_hash = sha256(authority_path)
    contract = authority["contract"]
    refs = read_csv(inputs["joined_reference_inventory"])
    funcs = read_csv(inputs["sysfunc_candidate"])
    args = read_csv(inputs["sysargs_candidate"])
    rows: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for ref in refs:
        converted = command_row(ref, map_hash, contract)
        if converted is None:
            excluded.append({"identity": ref["identity"], "classification": ref["classification"], "evidence": ref["edref_evidence"], "disposition": "OUTSIDE_REFERENCE_IDENTITY_ENTITY_TYPES"})
        else:
            rows.append(converted)
    rows.extend(function_row(row, map_hash, contract) for row in funcs)
    rows.extend(argument_row(row, map_hash, contract) for row in args)
    rows.sort(key=lambda row: (row["entity_type"], row["logical_id"]))
    duplicates = [key for key, count in Counter(row["logical_id"] for row in rows).items() if count > 1]
    manifest = {"schema_version": "reference_authority_crosswalk_v1", "run_id": "DOCFLUSH-20260716-001", "report_only": True, "contract": contract, "authority_map": str(authority_path.relative_to(repo)).replace("\\", "/"), "authority_map_sha256": map_hash, "input_hashes": {key: sha256(path) for key, path in inputs.items()}, "row_count": len(rows), "entity_counts": dict(sorted(Counter(row["entity_type"] for row in rows).items())), "validation_counts": dict(sorted(Counter(row["validation_state"] for row in rows).items())), "excluded_reference_topics": len(excluded), "duplicate_logical_ids": duplicates, "promotion_authorized": False}
    return rows, excluded, manifest


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=RUN / "identity_crosswalk_phase")
    args = parser.parse_args(); repo = args.repo_root.resolve(); out = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    rows, excluded, manifest = build(repo); out.mkdir(parents=True, exist_ok=True)
    crosswalk = out / "reference_identity_authority_crosswalk_v1.csv"; excluded_path = out / "excluded_reference_topics_v1.csv"
    write_csv(crosswalk, rows, FIELDS); write_csv(excluded_path, excluded, ["identity", "classification", "evidence", "disposition"])
    manifest["crosswalk_sha256"] = sha256(crosswalk); manifest["excluded_sha256"] = sha256(excluded_path)
    (out / "reference_identity_authority_crosswalk_manifest_v1.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True)); return 1 if manifest["duplicate_logical_ids"] else 0


if __name__ == "__main__": raise SystemExit(main())
