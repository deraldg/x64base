"""Versioned native DDICT feed, normalized identities and candidate renderers.

No DBF parser here: ddict_export uses the engine's shared read-only view.
No live imports, acceptance or publication. Output directories must be new.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

SCHEMA = "dottalk.ddict.feed.v1"
PRODUCERS = (
    "src/tools/ddict_export_main.cpp", "src/datadict/ddict_catalog_view.cpp",
    "src/datadict/ddict_dbf_reader.cpp", "src/memo/memostore.cpp",
    "include/datadict/ddict_catalog_view.hpp", "tools/datadict/catalog/ddict_feed.py",
    "docs/datadict/schemas/ddict_native_v1.schema.json", "docs/datadict/schemas/ddict_feed_v1.schema.json",
)
DOMAINS = ("DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
           "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE")
DISPOSITION_ARTIFACT = "DDICT_DIAGNOSTIC_DISPOSITION.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {name}")
    return path


def snapshot(directory: Path) -> list[dict]:
    return [{"name": p.name, "bytes": p.stat().st_size,
             "mtime_ns": p.stat().st_mtime_ns, "sha256": sha(p)}
            for p in sorted(directory.iterdir()) if p.is_file()]


def normalize(value: str) -> str:
    return " ".join(value.upper().split())


def reference_key(kind: str, name: str, owner: str = "", owner_kind: str = "", argument_kind: str = "") -> str:
    """Canonical reference contract; argument kind is part of its identity."""
    kind, name, owner = normalize(kind), normalize(name), normalize(owner)
    if kind == "COMMAND":
        return "CMD:" + name if name else ""
    if kind == "FUNCTION":
        return "FN:" + name if name else ""
    if kind == "SUBCOMMAND" and owner and name:
        return f"SUBCMD:{owner}::{name}"
    if kind == "ARGUMENT" and all((owner, name, owner_kind, argument_kind)):
        return f"ARG:{normalize(owner_kind)}:{owner}:{normalize(argument_kind)}:{name}"
    return ""  # COMMAND_SURFACE is not silently converted to COMMAND.


def crosswalk(data: dict) -> list[dict]:
    result = []
    for domain in DOMAINS:
        for row in data["tables"][domain]:
            identity = [row["_DD_FAMILY"], row["_DD_TABLE"], row["_DD_ID"]]
            key = "DDICT:" + ":".join(quote(s, safe="") for s in identity)
            reference = reference_key(row.get("OBJTYPE", ""), row.get("NAME", ""), row.get("OWNER", "")) if domain == "DDOBJECT" else ""
            result.append({"dictionary_key": key, "domain": domain,
                           "family": identity[0], "physical_table": identity[1],
                           "original_id": identity[2], "reference_key": reference,
                           "mapping_state": "SOURCE_DECLARED_CANDIDATE" if reference else "UNMAPPED"})
    counts = {}
    for item in result:
        if item["reference_key"]:
            counts[item["reference_key"]] = counts.get(item["reference_key"], 0) + 1
    for item in result:
        if counts.get(item["reference_key"], 0) > 1:
            item["mapping_state"] = "AMBIGUOUS_REFERENCE_REVIEW"
    return result


def feed_status(data: dict, mapping: list[dict]) -> str:
    return "REVIEW" if data["diagnostics"] or any(m["mapping_state"] == "AMBIGUOUS_REFERENCE_REVIEW" for m in mapping) else "READY"


def diagnostic_disposition(diagnostics: list[str]) -> list[dict]:
    """Classify every native finding without repairing or suppressing it."""
    result = []
    occurrences: dict[str, int] = {}
    for sequence, message in enumerate(diagnostics, 1):
        occurrences[message] = occurrences.get(message, 0) + 1
        occurrence = occurrences[message]
        token = hashlib.sha256(f"{message}\n{occurrence}".encode("utf-8")).hexdigest()[:16].upper()
        table, _, detail = message.partition(": ")
        row = {
            "diagnostic_id": f"DDICT-DIAG-{token}",
            "sequence": sequence,
            "category": "UNCLASSIFIED",
            "source_table": table,
            "source_field": "",
            "endpoint_role": "",
            "reference_id": "",
            "affected_cells": 0,
            "severity": "BLOCKS_READY",
            "disposition": "OWNER_REVIEW_REQUIRED",
            "auto_fix": False,
            "message": message,
        }
        memo = re.fullmatch(r"([^:]+): (.+) \(cells=(\d+)\)", detail)
        endpoint = re.fullmatch(r"unresolved (source|target) (.+)", detail)
        if memo:
            row["source_field"] = memo.group(1)
            row["affected_cells"] = int(memo.group(3))
            if ("memo object not found or unreadable" in memo.group(2)
                    or "memo sidecar missing or unreadable" in memo.group(2)):
                row["category"] = "MEMO_PAYLOAD_UNAVAILABLE"
                row["disposition"] = "RECOVER_OR_RECREATE_MEMO_PAYLOAD"
            elif "invalid space-filled x64 memo link" in memo.group(2):
                row["category"] = "MEMO_LINK_INVALID"
                row["disposition"] = "REPAIR_OR_NULL_MEMO_LINK_WITH_OWNER_APPROVAL"
        elif endpoint:
            row["category"] = "RELATION_ENDPOINT_UNRESOLVED"
            row["endpoint_role"] = endpoint.group(1).upper()
            row["reference_id"] = endpoint.group(2)
            row["disposition"] = "RESTORE_ENDPOINT_OR_REMOVE_EDGE_WITH_OWNER_APPROVAL"
        result.append(row)
    return result


def validate_native(data: dict) -> None:
    if set(data) != {"schema", "physical_tables", "tables", "diagnostics"}:
        raise ValueError("Native export shape mismatch")
    if data.get("schema") != "dottalk.ddict.native.v1":
        raise ValueError("Unsupported native export schema")
    if set(data.get("tables", {})) != set(DOMAINS):
        raise ValueError("Native table domains incomplete or unknown")
    if not isinstance(data.get("diagnostics"), list) or not all(isinstance(x, str) for x in data["diagnostics"]):
        raise ValueError("Invalid diagnostics")
    physical = {}
    for table in data["physical_tables"]:
        name = table["physical_name"]
        if not re.fullmatch(r"[A-Z0-9_]+", name) or name in physical:
            raise ValueError("Invalid or duplicate physical table")
        if table["state"] not in {"READY", "MISSING", "ERROR"}:
            raise ValueError("Invalid table state")
        if table["family"] not in {"LEGACY", "X64"} or not isinstance(table["rows"], int) or table["rows"] < 0:
            raise ValueError("Invalid physical table family or row count")
        names = set()
        for field in table["fields"]:
            if not isinstance(field["name"], str) or field["name"] in names or not isinstance(field["width"], int) or field["width"] < 0 or len(field["type"]) != 1:
                raise ValueError("Invalid or duplicate physical field")
            names.add(field["name"])
        physical[name] = table
    if not physical or not any(t["state"] == "READY" for t in physical.values()):
        raise ValueError("No readable physical tables")
    seen = set()
    for domain in DOMAINS:
        for row in data["tables"][domain]:
            if not isinstance(row, dict) or not all(isinstance(v, str) for v in row.values()):
                raise ValueError("Invalid native row")
            identity = (row["_DD_FAMILY"], row["_DD_TABLE"], row["_DD_ID"])
            if not identity[2] or identity in seen:
                raise ValueError("Empty or duplicate dictionary identity")
            seen.add(identity)
            table = physical[identity[1]]
            if table["state"] != "READY" or table["family"] != identity[0]:
                raise ValueError("Row/physical table mismatch")
            for field in table["fields"]:
                if field["type"] == "M" and row.get("_DD_MEMO_STATE:" + field["name"]) not in {"NULL", "RESOLVED", "INVALID", "UNAVAILABLE"}:
                    raise ValueError("Memo state missing or invalid")


def render(data: dict, mappings: list[dict], dispositions: list[dict], status: str) -> str:
    def cell(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\r", "").replace("\n", "<br>")
    lines = ["# Data dictionary candidate", "", f"Status: {status}. Internal, unaccepted, not published.", "",
             "This snapshot preserves native names and explicit memo failures. Reference mappings are source declarations, not runtime reachability proof.", "",
             "## Review diagnostics", ""]
    if dispositions:
        lines += ["| ID | Category | Scope | Cells | Disposition |", "| --- | --- | --- | ---: | --- |"]
        lines += [f"| {d['diagnostic_id']} | {d['category']} | {cell(d['source_table'])} | {d['affected_cells']} | {d['disposition']} |" for d in dispositions]
    else:
        lines += ["No native review diagnostics."]
    lines += ["", "## Physical schemas", ""]
    for table in data["physical_tables"]:
        lines += ["### " + cell(table["physical_name"]), "",
                  f"Logical name: {cell(table['logical_name'])}; family: {table['family']}; state: {table['state']}; rows: {table['rows']}.", "",
                  "| Field | Type | Width |", "| --- | --- | --- |"]
        lines += [f"| {cell(f['name'])} | {cell(f['type'])} | {f['width']} |" for f in table["fields"]]
        lines.append("")
    lines += ["## Identity crosswalk", "", "| Dictionary identity | Reference identity | Mapping |", "| --- | --- | --- |"]
    lines += [f"| {cell(m['dictionary_key'])} | {cell(m['reference_key'])} | {m['mapping_state']} |" for m in mappings]
    # Keep every exported cell and its memo state; no bounded CLI display limit.
    for domain in ("DDOBJECT", "DDATTR", "DDEDGE", "DDEVID"):
        lines += ["", "## " + domain, ""]
        for row in data["tables"][domain]:
            lines += ["### " + cell(row["_DD_FAMILY"] + ":" + row["_DD_ID"]), "",
                      "| Property | Value |", "| --- | --- |"]
            lines += [f"| {cell(k)} | {cell(v)} |" for k, v in sorted(row.items())]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def validate_bundle(directory: Path, repo: Path, *, check_sources: bool = True) -> dict:
    manifest = json.loads((directory / "DDICT_MANIFEST.json").read_text(encoding="utf-8"))
    required = {"schema", "run_id", "generated_at_utc", "status", "acceptance", "sensitivity", "catalog", "source_files", "producer_hashes", "binary", "artifacts", "diagnostics"}
    if set(manifest) != required or manifest["sensitivity"] != "internal" or not manifest["run_id"]:
        raise ValueError("Dictionary manifest shape or sensitivity mismatch")
    datetime.fromisoformat(manifest["generated_at_utc"])
    if set(manifest["producer_hashes"]) != set(PRODUCERS):
        raise ValueError("Producer membership mismatch")
    if manifest.get("schema") != SCHEMA or manifest.get("acceptance") != "CANDIDATE":
        raise ValueError("Unsupported or incorrectly accepted dictionary feed")
    expected = {"DDICT_NATIVE.json", "DDICT_CROSSWALK.json", DISPOSITION_ARTIFACT, "dictionary.md", "dictionary.html"}
    if set(manifest["artifacts"]) != expected:
        raise ValueError("Dictionary artifact membership mismatch")
    for name, digest in manifest["artifacts"].items():
        if sha(contained(directory, name)) != digest:
            raise ValueError(f"Artifact hash mismatch: {name}")
    native = json.loads((directory / "DDICT_NATIVE.json").read_text(encoding="utf-8"))
    validate_native(native)
    if manifest["diagnostics"] != native["diagnostics"]:
        raise ValueError("Manifest/native diagnostics mismatch")
    dispositions = json.loads((directory / DISPOSITION_ARTIFACT).read_text(encoding="utf-8"))
    if dispositions != diagnostic_disposition(native["diagnostics"]):
        raise ValueError("Diagnostic disposition differs from native diagnostics")
    if any(d["category"] == "UNCLASSIFIED" for d in dispositions):
        raise ValueError("Unclassified dictionary diagnostic")
    mapping = json.loads((directory / "DDICT_CROSSWALK.json").read_text(encoding="utf-8"))
    if mapping != crosswalk(native):
        raise ValueError("Identity crosswalk differs from native rows")
    expected_status = feed_status(native, mapping)
    if manifest["status"] != expected_status:
        raise ValueError("Diagnostics/status mismatch")
    if check_sources:
        catalog = contained(repo, manifest["catalog"])
        if snapshot(catalog) != manifest["source_files"]:
            raise ValueError("Stale catalog snapshot (members, bytes or modification time changed)")
        for name, digest in manifest["producer_hashes"].items():
            if sha(contained(repo, name)) != digest:
                raise ValueError(f"Stale producer: {name}")
        if sha(contained(repo, manifest["binary"]["path"])) != manifest["binary"]["sha256"]:
            raise ValueError("Exporter binary changed")
    return {"status": manifest["status"], "acceptance": "CANDIDATE", "manifest_sha256": sha(directory / "DDICT_MANIFEST.json"),
            "object_count": len(native["tables"]["DDOBJECT"]), "identity_count": len(mapping),
            "diagnostic_count": len(native["diagnostics"]), "source_check": check_sources,
            "source_state": "FULLY_VERIFIED" if check_sources else "SNAPSHOT_ONLY"}


def catalog_source_present(directory: Path, repo: Path) -> bool:
    """True when the source catalog exists; its presence requires full proof."""
    manifest = json.loads((directory / "DDICT_MANIFEST.json").read_text(encoding="utf-8"))
    return contained(repo, manifest["catalog"]).is_dir()


def build(repo: Path, executable: Path, catalog: Path, output: Path) -> dict:
    repo, executable, catalog, output = (p.resolve() for p in (repo, executable, catalog, output))
    for path in (executable, catalog, output):
        if not path.is_relative_to(repo):
            raise ValueError("All paths must remain in the development repository")
    if output.is_relative_to(repo / "dottalkpp" / "data") or output.is_relative_to(catalog) or output == repo:
        raise ValueError("Candidate output cannot be a live data directory")
    if output.exists():
        raise ValueError("Candidate output must be new; overwrite refused")
    before = snapshot(catalog)
    binary_hash = sha(executable)
    producers = {name: sha(repo / name) for name in PRODUCERS}
    process = subprocess.run([str(executable), str(catalog)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode not in (0, 2):
        raise ValueError("Native export failed: " + process.stderr.decode("utf-8", errors="replace"))
    data = json.loads(process.stdout.decode("utf-8-sig"))
    validate_native(data)
    if (process.returncode == 2) != bool(data["diagnostics"]):
        raise ValueError("Native exit code and review diagnostics disagree")
    if before != snapshot(catalog) or binary_hash != sha(executable) or producers != {name: sha(repo / name) for name in PRODUCERS}:
        raise ValueError("Inputs changed during export")
    mapping = crosswalk(data)
    dispositions = diagnostic_disposition(data["diagnostics"])
    if any(d["category"] == "UNCLASSIFIED" for d in dispositions):
        raise ValueError("Native export contains an unclassified diagnostic")
    status = feed_status(data, mapping)
    report = render(data, mapping, dispositions, status)
    output.mkdir(parents=True, exist_ok=False)
    (output / "DDICT_NATIVE.json").write_bytes(process.stdout)
    (output / "DDICT_CROSSWALK.json").write_text(json.dumps(mapping, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (output / DISPOSITION_ARTIFACT).write_text(json.dumps(dispositions, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (output / "dictionary.md").write_text(report, encoding="utf-8")
    # A safe, self-contained reader; no untrusted HTML/JS from catalog values.
    (output / "dictionary.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Data dictionary candidate</title><style>body{max-width:1100px;margin:2rem auto;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Data dictionary candidate</h1><p>Internal review snapshot. Not accepted or published.</p><pre>' + html.escape(report) + '</pre></html>', encoding="utf-8")
    artifacts = {p.name: sha(p) for p in sorted(output.iterdir())}
    manifest = {"schema": SCHEMA, "run_id": output.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": status, "acceptance": "CANDIDATE", "sensitivity": "internal",
                "catalog": catalog.relative_to(repo).as_posix(), "source_files": before,
                "producer_hashes": producers, "binary": {"path": executable.relative_to(repo).as_posix(), "sha256": binary_hash},
                "artifacts": artifacts, "diagnostics": data["diagnostics"]}
    (output / "DDICT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return validate_bundle(output, repo)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--catalog", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "build":
            if not args.executable or not args.catalog:
                parser.error("build requires --executable and --catalog")
            result = build(args.repo_root, args.executable, args.catalog, args.out)
        else:
            result = validate_bundle(args.out, args.repo_root)
        print(json.dumps(result, indent=2))
        return 2 if result["status"] == "REVIEW" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
