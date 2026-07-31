#!/usr/bin/env python3
"""PHASE23H HELP locale consumer integration plan.

Report-only behavior:
- Scans repo files for existing locale/message/help seams.
- Writes candidate planning artifacts under docs/locale/candidates.
- Does not modify source, active HELP DATA, CMDHELP, CMDHELPCHK, DBF, CDX, LMDB,
  workspace schemas, or latest pointers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Any

PHASE = "PHASE23H"
PHASE_SLUG = "PHASE23H-HELP-LOCALE-CONSUMER-INTEGRATION-PLAN"
STATUS_GREEN = "PHASE23H_HELP_LOCALE_CONSUMER_INTEGRATION_PLAN_GREEN_REPORT_ONLY"
STATUS_REVIEW = "PHASE23H_HELP_LOCALE_CONSUMER_INTEGRATION_PLAN_REVIEW_REQUIRED_REPORT_ONLY"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING"

SOURCE_EXTS = {".cpp", ".hpp", ".h", ".cxx", ".cc", ".md", ".txt", ".dts", ".dtschema", ".json", ".csv"}
SCAN_DIRS = ["src", "include", "docs", "tools", "scripts", "dottalkpp"]

STARTER_LOCALE_PATTERNS = ["en-US", "es", "fr", "de", "it", "es-MX", "en", "fr-FR", "de-DE", "it-IT"]
MESSAGE_SEAMS = [
    "SYSTEM_MESSAGES",
    "SYSTEM_MESSAGE_TEXT",
    "MESSAGE_LOCALE_SET",
    "SET LANGUAGE",
    "SET LOCALE",
    "SET MESSAGE CATALOG CHECK",
    "SET MESSAGE EMIT",
    "message catalog",
    "locale",
]
HELP_SEAMS = [
    "HELP_TOPIC",
    "HELP_SECTION",
    "HELP_LINE",
    "HELP_ARTIFACTS",
    "CMDHELP",
    "CMDHELPCHK",
    "dotref",
    "foxref",
    "edref",
    "usage_contract",
    "@dottalk.usage",
]
LOCALE_SPINE_SEAMS = [
    "SYSTEM_LOCALES",
    "SYSTEM_LOCALE_FALLBACK",
    "LOCALE_ID",
    "BASE_LOCALE",
    "SOURCE_LOCALE",
    "FALLBACK_ALLOWED",
    "TEXT_DIR",
    "LOCALE_STATUS",
    "TRANSL_STATUS",
    "SOURCE_HASH",
    "LOCALIZED_HASH",
    "REVIEW_STATUS",
]

CANONICAL_HELP_TABLES = ["HELP_TOPIC", "HELP_SECTION", "HELP_LINE", "HELP_ARTIFACTS"]

PROPOSED_COMPANION_TABLES = [
    {
        "table": "HELP_TOPIC_LOCALE",
        "canonical_parent": "HELP_TOPIC",
        "join_key": "TOPICKEY + LOCALE_ID",
        "purpose": "Localized topic title/summary metadata attached to canonical topic identity.",
        "mutation_phase": "PHASE23I staging only",
    },
    {
        "table": "HELP_SECTION_LOCALE",
        "canonical_parent": "HELP_SECTION",
        "join_key": "TOPICKEY + SECTION_ID + LOCALE_ID",
        "purpose": "Localized section headings and section-level display labels.",
        "mutation_phase": "PHASE23I staging only",
    },
    {
        "table": "HELP_LINE_LOCALE",
        "canonical_parent": "HELP_LINE",
        "join_key": "TOPICKEY + SECTION_ID + LINE_ID + LOCALE_ID",
        "purpose": "Localized help body lines tied to stable canonical line identity and source hash.",
        "mutation_phase": "PHASE23I staging only",
    },
    {
        "table": "HELP_ARTIFACT_LOCALE",
        "canonical_parent": "HELP_ARTIFACTS",
        "join_key": "ARTIFACT_ID + LOCALE_ID",
        "purpose": "Localized artifact labels/descriptions without duplicating canonical artifacts.",
        "mutation_phase": "PHASE23I staging only",
    },
]

PROPOSED_FIELDS = [
    ("LOCALE_ID", "character", "Locale key from SYSTEM_LOCALES."),
    ("SOURCE_LOCALE", "character", "Locale of canonical/source text, normally en-US."),
    ("TEXT_DIR", "character", "ltr or rtl, inherited from SYSTEM_LOCALES."),
    ("SOURCE_HASH", "character", "Hash of canonical source text/identity used for stale detection."),
    ("LOCALIZED_HASH", "character", "Hash of localized text."),
    ("TRANSL_STATUS", "character", "draft, machine, reviewed, approved, stale, missing."),
    ("REVIEW_STATUS", "character", "review state separate from translation status if needed."),
    ("REVIEWED_BY", "character", "Optional reviewer id."),
    ("REVIEWED_AT", "datetime", "Optional review timestamp."),
    ("FALLBACK_ALLOWED", "logical", "Whether fallback is allowed for this row/locale."),
]

CMDHELPCHK_CHECKS = [
    ("LOCALE_ID_VALID", "Every localized HELP row references SYSTEM_LOCALES."),
    ("FALLBACK_PATH_VALID", "Each requested locale has a reachable fallback path."),
    ("SOURCE_HASH_MATCH", "Localized row is not stale after CMDHELP BUILD changes canonical source text."),
    ("ORPHAN_LOCALIZED_ROW", "Localized rows must have live canonical parent rows."),
    ("MISSING_REQUIRED_TRANSLATION", "Required user-facing HELP rows missing for a locale."),
    ("TEXT_DIR_COMPAT", "RTL/LTR metadata is available before rendering locale-specific output."),
    ("REVIEW_STATUS_READY", "Release locale rows require reviewed/approved status."),
    ("DUPLICATE_LOCALE_ROW", "No duplicate localized row for the same canonical key and LOCALE_ID."),
]

COMMAND_SURFACES = [
    ("CMDHELP LOCALES", "Report supported HELP/message locales and fallback chain."),
    ("CMDHELP <topic> LOCALE <locale>", "Display localized HELP with fallback evidence."),
    ("CMDHELP USAGE <topic> LOCALE <locale>", "Display localized usage-only HELP."),
    ("CMDHELPCHK LOCALE <locale>", "Validate localized HELP rows for a target locale."),
    ("CMDHELPCHK LOCALES", "Validate all locales configured in SYSTEM_LOCALES."),
    ("HELP <topic> LOCALE <locale>", "Possible future user-facing alias after CMDHELP proof is green."),
]

@dataclass
class EvidenceHit:
    category: str
    pattern: str
    path: str
    line: int
    excerpt: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except ValueError:
        return str(path).replace("/", "\\")


def iter_scan_files(root: Path) -> Iterable[Path]:
    for dirname in SCAN_DIRS:
        base = root / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in SOURCE_EXTS:
                if any(part in {".git", "build", "node_modules", "__pycache__"} for part in path.parts):
                    continue
                yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def find_patterns(root: Path, patterns: list[str], category: str, max_hits_per_pattern: int = 25) -> list[EvidenceHit]:
    hits: list[EvidenceHit] = []
    counts: dict[str, int] = {p: 0 for p in patterns}
    lowered_patterns = [(p, p.lower()) for p in patterns]
    for path in iter_scan_files(root):
        text = read_text(path)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            for pattern, lp in lowered_patterns:
                if counts[pattern] >= max_hits_per_pattern:
                    continue
                if lp in lower:
                    hits.append(EvidenceHit(category, pattern, repo_rel(path, root), line_no, line.strip()[:240]))
                    counts[pattern] += 1
    return hits


def discover_locales(hits: list[EvidenceHit]) -> list[dict[str, str]]:
    found: set[str] = set()
    rx = re.compile(r"\b([a-z]{2}(?:-[A-Z]{2})?)\b")
    for hit in hits:
        for match in rx.findall(hit.excerpt):
            if match in STARTER_LOCALE_PATTERNS:
                found.add(match)
        for loc in STARTER_LOCALE_PATTERNS:
            if loc.lower() in hit.excerpt.lower() or loc.lower() == hit.pattern.lower():
                found.add(loc)
    if not found:
        # Starter set based on known lane intent; report as proposed/expected when not discovered.
        found.update(["en-US", "es", "fr", "de", "it"])
    preferred = ["en-US", "es", "fr", "de", "it"]
    ordered = [x for x in preferred if x in found] + sorted(x for x in found if x not in preferred)
    rows = []
    for loc in ordered:
        rows.append({
            "locale_id": loc,
            "role": "starter_runtime_locale" if loc in preferred else "discovered_or_alias_locale",
            "status": "observed_or_expected",
            "fallback_to": "" if loc == "en-US" else (loc.split("-")[0] if "-" in loc and loc.split("-")[0] != loc else "en-US"),
        })
    return rows


def active_help_inventory(root: Path) -> list[dict[str, Any]]:
    candidates = [
        root / "dottalkpp" / "data" / "help",
        root / "dottalkpp" / "data" / "HELP",
    ]
    rows = []
    seen = set()
    for base in candidates:
        if str(base).lower() in seen:
            continue
        seen.add(str(base).lower())
        for table in ["COMMANDS", "CMD_ARGS", "HELP_TOPIC", "HELP_SECTION", "HELP_LINE", "HELP_ARTIFACTS"]:
            for name in {f"{table}.dbf", f"{table.lower()}.dbf"}:
                path = base / name
                if path.exists():
                    rows.append({
                        "table": table,
                        "path": repo_rel(path, root),
                        "exists": 1,
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    })
                    break
            else:
                rows.append({
                    "table": table,
                    "path": repo_rel(base / f"{table}.dbf", root),
                    "exists": 0,
                    "size_bytes": 0,
                    "sha256": "",
                })
    if not rows:
        for table in CANONICAL_HELP_TABLES:
            rows.append({"table": table, "path": "not_found_in_repo_snapshot", "exists": 0, "size_bytes": 0, "sha256": ""})
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def make_markdown(
    manifest: dict[str, Any],
    locales: list[dict[str, str]],
    help_inventory: list[dict[str, Any]],
    hits_by_category: dict[str, list[EvidenceHit]],
) -> str:
    lines: list[str] = []
    lines.append("# PHASE23H HELP Locale Consumer Integration Plan")
    lines.append("")
    lines.append(f"Status: `{manifest['status']}`")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Define how CMDHELP/HELP should consume the shared locale spine and message-locale work without changing active HELP tables yet.")
    lines.append("This is a report-only package. It writes only candidate planning artifacts.")
    lines.append("")
    lines.append("## Boundaries")
    lines.append("")
    for item in manifest["boundary_contract"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Observed or expected starter locales")
    lines.append("")
    lines.append("| LOCALE_ID | Role | Fallback | Status |")
    lines.append("|---|---|---|---|")
    for row in locales:
        lines.append(f"| {row['locale_id']} | {row['role']} | {row['fallback_to']} | {row['status']} |")
    lines.append("")
    lines.append("## Canonical HELP inventory")
    lines.append("")
    lines.append("| Table | Exists | Path | Size bytes |")
    lines.append("|---|---:|---|---:|")
    for row in help_inventory:
        lines.append(f"| {row['table']} | {row['exists']} | `{row['path']}` | {row['size_bytes']} |")
    lines.append("")
    lines.append("## Proposed companion tables")
    lines.append("")
    lines.append("| Table | Canonical parent | Join key | Purpose |")
    lines.append("|---|---|---|---|")
    for row in PROPOSED_COMPANION_TABLES:
        lines.append(f"| {row['table']} | {row['canonical_parent']} | `{row['join_key']}` | {row['purpose']} |")
    lines.append("")
    lines.append("## Common localized-row fields")
    lines.append("")
    lines.append("| Field | Type | Purpose |")
    lines.append("|---|---|---|")
    for name, typ, purpose in PROPOSED_FIELDS:
        lines.append(f"| {name} | {typ} | {purpose} |")
    lines.append("")
    lines.append("## CMDHELPCHK locale checks")
    lines.append("")
    lines.append("| Check | Meaning |")
    lines.append("|---|---|")
    for check, meaning in CMDHELPCHK_CHECKS:
        lines.append(f"| {check} | {meaning} |")
    lines.append("")
    lines.append("## Future command surfaces")
    lines.append("")
    lines.append("These are proposed surfaces only. PHASE23H does not implement them.")
    lines.append("")
    lines.append("| Surface | Purpose |")
    lines.append("|---|---|")
    for surface, purpose in COMMAND_SURFACES:
        lines.append(f"| `{surface}` | {purpose} |")
    lines.append("")
    lines.append("## Evidence hit counts")
    lines.append("")
    lines.append("| Category | Hits |")
    lines.append("|---|---:|")
    for category, hits in hits_by_category.items():
        lines.append(f"| {category} | {len(hits)} |")
    lines.append("")
    lines.append("## Integration doctrine")
    lines.append("")
    lines.append("- Canonical HELP remains generated from source/catalog evidence: registry, dotref/foxref/edref, usage contracts, curated docs, shared messages, and source miner output.")
    lines.append("- Locale text attaches as companion rows keyed to stable HELP identities. The localized layer should not fork or replace canonical HELP.")
    lines.append("- Stale translation detection depends on SOURCE_HASH changing after CMDHELP BUILD.")
    lines.append("- Fallback behavior must be visible in reports and transcript proof, not silent magic.")
    lines.append("- Runtime command keywords remain English/system command tokens for now; SET LANGUAGE / SET LOCALE selects message/help text, not command syntax.")
    lines.append("")
    lines.append("## Next gate")
    lines.append("")
    lines.append(f"`{NEXT_GATE}`")
    lines.append("")
    lines.append("Recommended next step: review this plan, then stage PHASE23I schema candidates for HELP locale companion tables without touching active HELP until review is green.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage PHASE23H HELP locale consumer integration plan.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not root.exists():
        raise SystemExit(f"repo root not found: {root}")

    out_dir = root / "docs" / "locale" / "candidates" / PHASE_SLUG
    out_dir.mkdir(parents=True, exist_ok=True)

    message_hits = find_patterns(root, MESSAGE_SEAMS + STARTER_LOCALE_PATTERNS, "message_locale_surface")
    help_hits = find_patterns(root, HELP_SEAMS, "help_surface")
    spine_hits = find_patterns(root, LOCALE_SPINE_SEAMS, "shared_locale_spine")
    all_hits = message_hits + help_hits + spine_hits
    locales = discover_locales(message_hits + spine_hits)
    help_inventory = active_help_inventory(root)

    status = STATUS_GREEN
    warnings: list[str] = []
    if not message_hits:
        warnings.append("No message/locale surface evidence found in scanned files; plan still staged from expected contract.")
    if not help_hits:
        warnings.append("No HELP/CMDHELP evidence found in scanned files; plan still staged from expected contract.")
    if not spine_hits:
        warnings.append("No shared locale spine evidence found in scanned files; plan still staged from expected contract.")
    if warnings:
        status = STATUS_REVIEW

    boundary_contract = [
        "source_files_written = 0",
        "active_help_dbf_written = 0",
        "active_help_cdx_written = 0",
        "active_help_lmdb_written = 0",
        "cmdhelp_behavior_changed = 0",
        "cmdhelpchk_behavior_changed = 0",
        "runtime_execution = 0",
        "latest_pointer_changed = 0",
        "candidate_plan_artifacts_written_only = 1",
    ]

    manifest = {
        "phase": PHASE,
        "phase_slug": PHASE_SLUG,
        "status": status,
        "generated_at_utc": now_iso(),
        "repo_root": str(root),
        "candidate_dir": repo_rel(out_dir, root),
        "next_gate": NEXT_GATE,
        "warnings": warnings,
        "counts": {
            "message_locale_hits": len(message_hits),
            "help_surface_hits": len(help_hits),
            "shared_locale_spine_hits": len(spine_hits),
            "starter_locale_rows": len(locales),
            "help_inventory_rows": len(help_inventory),
            "proposed_companion_tables": len(PROPOSED_COMPANION_TABLES),
            "cmdhelpchk_locale_checks": len(CMDHELPCHK_CHECKS),
            "future_command_surfaces": len(COMMAND_SURFACES),
        },
        "boundary_contract": boundary_contract,
    }

    write_csv(out_dir / "phase23h_evidence_hits.csv", [asdict(h) for h in all_hits])
    write_csv(out_dir / "phase23h_locale_inventory.csv", locales)
    write_csv(out_dir / "phase23h_active_help_inventory.csv", help_inventory)
    write_csv(out_dir / "phase23h_proposed_help_locale_companion_tables.csv", PROPOSED_COMPANION_TABLES)
    write_csv(out_dir / "phase23h_proposed_help_locale_fields.csv", [
        {"field": n, "type": t, "purpose": p} for n, t, p in PROPOSED_FIELDS
    ])
    write_csv(out_dir / "phase23h_cmdhelpchk_locale_checks.csv", [
        {"check": c, "meaning": m} for c, m in CMDHELPCHK_CHECKS
    ])
    write_csv(out_dir / "phase23h_future_command_surfaces.csv", [
        {"surface": s, "purpose": p} for s, p in COMMAND_SURFACES
    ])
    write_json(out_dir / "phase23h_manifest.json", manifest)

    hits_by_category = {
        "message_locale_surface": message_hits,
        "help_surface": help_hits,
        "shared_locale_spine": spine_hits,
    }
    md = make_markdown(manifest, locales, help_inventory, hits_by_category)
    md_hash = sha256_text(md)
    (out_dir / "PHASE23H_HELP_LOCALE_CONSUMER_INTEGRATION_PLAN.md").write_text(md, encoding="utf-8")

    manifest["artifacts"] = [
        repo_rel(out_dir / "PHASE23H_HELP_LOCALE_CONSUMER_INTEGRATION_PLAN.md", root),
        repo_rel(out_dir / "phase23h_manifest.json", root),
        repo_rel(out_dir / "phase23h_evidence_hits.csv", root),
        repo_rel(out_dir / "phase23h_locale_inventory.csv", root),
        repo_rel(out_dir / "phase23h_active_help_inventory.csv", root),
        repo_rel(out_dir / "phase23h_proposed_help_locale_companion_tables.csv", root),
        repo_rel(out_dir / "phase23h_proposed_help_locale_fields.csv", root),
        repo_rel(out_dir / "phase23h_cmdhelpchk_locale_checks.csv", root),
        repo_rel(out_dir / "phase23h_future_command_surfaces.csv", root),
    ]
    manifest["plan_markdown_sha256"] = md_hash
    write_json(out_dir / "phase23h_manifest.json", manifest)

    print(status)
    print(f"candidate_dir: {repo_rel(out_dir, root)}")
    print(f"message_locale_hits: {len(message_hits)}")
    print(f"help_surface_hits: {len(help_hits)}")
    print(f"shared_locale_spine_hits: {len(spine_hits)}")
    print(f"starter_locale_rows: {len(locales)}")
    print(f"proposed_companion_tables: {len(PROPOSED_COMPANION_TABLES)}")
    print(f"cmdhelpchk_locale_checks: {len(CMDHELPCHK_CHECKS)}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print(f"next_gate: {NEXT_GATE}")
    return 0 if status == STATUS_GREEN else 2


if __name__ == "__main__":
    raise SystemExit(main())
