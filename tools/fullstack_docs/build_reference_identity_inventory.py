from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")
CATALOG_RE = re.compile(
    r"inline\s+const\s+std::vector<Item>\s*&\s*catalog\s*\(\s*\)\s*\{(?P<body>.*?)\n\s*return\s+k\s*;",
    re.DOTALL,
)
ITEM_RE = re.compile(r"\{\s*\"(?P<name>(?:\\.|[^\"\\])*)\"\s*,", re.DOTALL)
REGISTRY_PATTERNS = [
    re.compile(r"registry\s*\(\s*\)\s*\.\s*add\s*\(\s*\"([^\"]+)\""),
    re.compile(r"register_(?:extension_)?command\s*\(\s*\"([^\"]+)\""),
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Join reference, registry, and harvested usage identities.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "reference_inventory")
    ap.add_argument(
        "--usage-catalog", "--usage-srcfile",
        dest="usage_catalog",
        type=Path,
        default=DEFAULT_RUN / "comments_reharvest/post_messaging_20260716/candidate_source_comment_metadata_import_v2/SRCUSAGE_IMPORT.csv",
        help="SRCUSAGE catalog (preferred); legacy SRCFILE catalogs remain readable.",
    )
    return ap.parse_args()


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def catalog_items(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = CATALOG_RE.search(text)
    if not match:
        raise RuntimeError(f"Could not isolate Item catalog in {path}")
    body = match.group("body")
    offset = match.start("body")
    rows = []
    for item in ITEM_RE.finditer(body):
        name = bytes(item.group("name"), "utf-8").decode("unicode_escape")
        line = text.count("\n", 0, offset + item.start()) + 1
        rows.append({"identity": norm(name), "source": path.name, "line": str(line)})
    return rows


def registry_items(repo: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted((repo / "src").rglob("*.cpp")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in REGISTRY_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                rows.append({
                    "identity": norm(match.group(1)),
                    "source": path.relative_to(repo).as_posix(),
                    "line": str(line),
                })
    return rows


def usage_items(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        source_rows = list(csv.DictReader(fh))

    file_evidence: dict[str, str] = {}
    block_evidence: dict[str, str] = {}
    if source_rows and "COMMAND" in source_rows[0]:
        srcfile = path.with_name("SRCFILE_IMPORT.csv")
        srcblock = path.with_name("SRCBLOCK_IMPORT.csv")
        if srcfile.exists():
            with srcfile.open("r", encoding="utf-8-sig", newline="") as fh:
                file_evidence = {row["FILEID"]: row["RELPATH"] for row in csv.DictReader(fh)}
        if srcblock.exists():
            with srcblock.open("r", encoding="utf-8-sig", newline="") as fh:
                block_evidence = {row["BLOCKID"]: row.get("STARTLN", "") for row in csv.DictReader(fh)}

    for row in source_rows:
        command = norm(row.get("COMMAND", row.get("DET_CMD", "")))
        if command:
            source = row.get("RELPATH", "") or file_evidence.get(row.get("FILEID", ""), path.name)
            line = row.get("FIRST_HDR", "") or block_evidence.get(row.get("BLOCKID", ""), "")
            rows.append({"identity": command, "source": source, "line": line})
    return rows


def evidence_map(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        evidence = f"{row['source']}:{row['line']}" if row["line"] else row["source"]
        if evidence not in result[row["identity"]]:
            result[row["identity"]].append(evidence)
    return result


def classify(in_dot: bool, in_fox: bool, in_ed: bool, in_registry: bool, in_usage: bool) -> str:
    in_ref = in_dot or in_fox
    if in_ed and not (in_ref or in_registry or in_usage):
        return "EDUCATIONAL_TOPIC"
    if in_registry and in_ref and in_usage:
        return "ALIGNED_COMMAND"
    if in_registry and in_ref and not in_usage:
        return "REGISTERED_REF_MISSING_USAGE"
    if in_registry and in_usage and not in_ref:
        return "REGISTERED_USAGE_MISSING_REF"
    if in_registry and not in_ref and not in_usage:
        return "REGISTERED_ONLY"
    if in_usage and not in_registry and not in_ref:
        return "USAGE_CONTRACT_ONLY"
    if in_ref and not in_registry and not in_usage:
        return "CURATED_REF_ONLY"
    if in_ref and in_usage and not in_registry:
        return "REF_USAGE_NOT_STATIC_REGISTRY"
    return "MIXED_REVIEW"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    usage_path = args.usage_catalog if args.usage_catalog.is_absolute() else repo / args.usage_catalog
    refs = {
        "dotref": catalog_items(repo / "include/dotref.hpp"),
        "foxref": catalog_items(repo / "include/foxref.hpp"),
        "edref": catalog_items(repo / "include/edref.hpp"),
    }
    registry = registry_items(repo)
    usage = usage_items(usage_path)
    maps = {name: evidence_map(rows) for name, rows in refs.items()}
    maps["registry"] = evidence_map(registry)
    maps["usage"] = evidence_map(usage)
    identities = sorted(set().union(*(set(value) for value in maps.values())))

    rows: list[dict[str, str]] = []
    for identity in identities:
        flags = {name: identity in mapping for name, mapping in maps.items()}
        classification = classify(
            flags["dotref"], flags["foxref"], flags["edref"], flags["registry"], flags["usage"]
        )
        rows.append({
            "identity": identity,
            "in_dotref": str(flags["dotref"]),
            "in_foxref": str(flags["foxref"]),
            "in_edref": str(flags["edref"]),
            "in_static_registry": str(flags["registry"]),
            "in_usage_contract": str(flags["usage"]),
            "classification": classification,
            "dotref_evidence": " | ".join(maps["dotref"].get(identity, [])),
            "foxref_evidence": " | ".join(maps["foxref"].get(identity, [])),
            "edref_evidence": " | ".join(maps["edref"].get(identity, [])),
            "registry_evidence": " | ".join(maps["registry"].get(identity, [])),
            "usage_evidence": " | ".join(maps["usage"].get(identity, [])),
        })
    fields = list(rows[0]) if rows else []
    inventory_path = output / "fullstack_reference_identity_inventory_v2.csv"
    write_csv(inventory_path, rows, fields)

    duplicates: list[dict[str, str]] = []
    for layer, source_rows in {**refs, "registry": registry, "usage": usage}.items():
        counts = Counter(row["identity"] for row in source_rows)
        evidence = evidence_map(source_rows)
        for identity, count in sorted(counts.items()):
            if count > 1:
                duplicates.append({
                    "layer": layer,
                    "identity": identity,
                    "count": str(count),
                    "evidence": " | ".join(evidence[identity]),
                    "review_disposition": "REVIEW_ALIAS_OR_DUPLICATE",
                })
    duplicate_path = output / "fullstack_reference_duplicate_inventory_v2.csv"
    write_csv(duplicate_path, duplicates, ["layer", "identity", "count", "evidence", "review_disposition"])

    counts = Counter(row["classification"] for row in rows)
    payload = {
        "contract": "fullstack-reference-identity-inventory-v2",
        "usage_authority_input": "SRCUSAGE preferred; legacy SRCFILE compatible",
        "static_scan_only": True,
        "catalog_counts": {name: len(value) for name, value in refs.items()},
        "catalog_unique_counts": {name: len(evidence_map(value)) for name, value in refs.items()},
        "static_registry_rows": len(registry),
        "static_registry_unique": len(evidence_map(registry)),
        "usage_rows": len(usage),
        "usage_unique": len(evidence_map(usage)),
        "joined_identities": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "duplicate_rows": len(duplicates),
        "input_hashes": {
            "include/dotref.hpp": sha256(repo / "include/dotref.hpp"),
            "include/foxref.hpp": sha256(repo / "include/foxref.hpp"),
            "include/edref.hpp": sha256(repo / "include/edref.hpp"),
            "usage_catalog": sha256(usage_path),
        },
        "inventory_sha256": sha256(inventory_path),
        "duplicates_sha256": sha256(duplicate_path),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "fullstack_reference_identity_manifest_v2.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# Full-stack Reference Identity Inventory v2", "",
        "Status: REPORT_ONLY / STATIC_SCAN", "",
        f"- DOTREF rows: `{payload['catalog_counts']['dotref']}`",
        f"- FOXREF rows: `{payload['catalog_counts']['foxref']}`",
        f"- EDREF rows: `{payload['catalog_counts']['edref']}`",
        f"- Static registry identities: `{payload['static_registry_unique']}`",
        f"- Usage-contract identities: `{payload['usage_unique']}`",
        f"- Joined identities: `{payload['joined_identities']}`", "",
        "## Classification counts", "",
    ]
    md += [f"- `{key}`: {value}" for key, value in sorted(counts.items())]
    md += [
        "", "This is a lexical source inventory. Dynamic extension/function registration and runtime routing require separate proof.",
    ]
    (output / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
