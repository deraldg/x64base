#!/usr/bin/env python3
"""Validate the AI Portal identifier model and render an advisory crosswalk.

The validator classifies legacy fields without rewriting history. Structural
identity defects are findings; incomplete historical backfill is reported as
an observation until the owner promotes this advisory lane to a hard gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_MODEL = LABTALK_ROOT / "registries" / "portal_identifier_model.yaml"
DEFAULT_JSON = LABTALK_ROOT / "reports" / "portal" / "portal_identifier_status_latest.json"
DEFAULT_MARKDOWN = LABTALK_ROOT / "reports" / "portal" / "portal_identifier_status_latest.md"
AIF_ROW_RE = re.compile(r"^\|\s*AIF-0*(\d+)\b", re.MULTILINE)
AIF_CLAIM_RE = re.compile(r"^AIF-0*(\d+)\.claim$")
R_ROW_RE = re.compile(r"^\|\s*R0*(\d+)\s*\|", re.MULTILINE)
AIF_VALUE_RE = re.compile(r"^AIF-0*(\d+)$", re.IGNORECASE)


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping in {path}")
    return value


def canon_aif(value: str | int) -> str:
    return f"AIF-{int(value):03d}"


def finding(subject: str, field: str, issue: str) -> dict[str, str]:
    return {"subject": subject, "field": field, "issue": issue}


def duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def yaml_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.yaml") if path.name != "_header.yaml")


def validate_model(data: dict[str, Any], root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    observations: list[dict[str, Any]] = []
    if data.get("schema") != "dottalk.portal.identifiers.v1":
        findings.append(finding("<model>", "schema", "expected dottalk.portal.identifiers.v1"))

    classes = data.get("identifier_classes")
    if not isinstance(classes, list):
        findings.append(finding("<model>", "identifier_classes", "must be a list"))
        classes = []
    class_ids = [item.get("class_id") for item in classes if isinstance(item, dict)]
    for class_id in duplicates([item for item in class_ids if isinstance(item, str)]):
        findings.append(finding(class_id, "class_id", "duplicate identifier class"))
    required_classes = {"project", "lane", "lifecycle", "ruling", "run", "work_item", "proof", "report"}
    for class_id in sorted(required_classes - set(class_ids)):
        findings.append(finding(class_id, "class_id", "required identifier class is missing"))
    for item in classes:
        if not isinstance(item, dict):
            continue
        class_id = str(item.get("class_id", "<unknown>"))
        pattern = item.get("pattern")
        if pattern is not None:
            try:
                re.compile(pattern)
            except re.error as exc:
                findings.append(finding(class_id, "pattern", f"invalid regular expression: {exc}"))
        authority = item.get("authority")
        if isinstance(authority, str) and not (root / authority).exists():
            findings.append(finding(class_id, "authority", f"path does not exist: {authority}"))
        for path_field in ("allocator", "claim_ledger", "collision_gate"):
            value = item.get(path_field)
            if isinstance(value, str) and not (root / value).exists():
                findings.append(finding(class_id, path_field, f"path does not exist: {value}"))

    sources = data.get("sources") or {}
    if not isinstance(sources, dict):
        findings.append(finding("<model>", "sources", "must be a mapping"))
        sources = {}

    def source(name: str) -> Path:
        value = sources.get(name)
        if not isinstance(value, str):
            findings.append(finding("<model>", f"sources.{name}", "path is required"))
            return root / "__missing__"
        path = root / value
        if not path.exists():
            findings.append(finding("<model>", f"sources.{name}", f"path does not exist: {value}"))
        return path

    projects_path = source("projects")
    tasks_path = source("tasks")
    intake_path = source("aif_intake")
    claims_path = source("aif_claims")
    rulings_path = source("rulings")
    runs_path = source("runs")
    proofs_path = source("proofs")

    projects_data = load_yaml(projects_path) if projects_path.is_file() else {}
    project_rows = projects_data.get("projects") or []
    project_ids = [row.get("id") for row in project_rows if isinstance(row, dict) and isinstance(row.get("id"), str)]
    for project_id in duplicates(project_ids):
        findings.append(finding(project_id, "project_id", "duplicate project identity"))

    intake_text = intake_path.read_text(encoding="utf-8", errors="replace") if intake_path.is_file() else ""
    intake_ids = [canon_aif(value) for value in AIF_ROW_RE.findall(intake_text)]
    for lane_id in duplicates(intake_ids):
        findings.append(finding(lane_id, "lane_id", "duplicate AIF intake row"))
    claim_ids = []
    if claims_path.is_dir():
        for path in claims_path.glob("AIF-*.claim"):
            match = AIF_CLAIM_RE.match(path.name)
            if match:
                claim_ids.append(canon_aif(match.group(1)))

    ruling_text = rulings_path.read_text(encoding="utf-8", errors="replace") if rulings_path.is_file() else ""
    ruling_ids = [f"R{int(value)}" for value in R_ROW_RE.findall(ruling_text)]
    for ruling_id in duplicates(ruling_ids):
        findings.append(finding(ruling_id, "ruling_id", "duplicate global R register row"))

    tasks_data = load_yaml(tasks_path) if tasks_path.is_file() else {}
    task_rows = tasks_data.get("tasks") or []
    task_ids = [row.get("id") for row in task_rows if isinstance(row, dict) and isinstance(row.get("id"), str)]
    for task_id in duplicates(task_ids):
        findings.append(finding(task_id, "work_item_id", "duplicate task identity"))
    legacy_ticket_counts: Counter[str] = Counter()
    task_lane_refs: set[str] = set()
    unknown_project_refs: set[str] = set()
    for row in task_rows:
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("id", "<task>"))
        if not task_id.startswith("task."):
            findings.append(finding(task_id, "id", "work item must use the task.* namespace"))
        for project_id in row.get("project_ids") or []:
            if project_id not in project_ids:
                unknown_project_refs.add(str(project_id))
                findings.append(finding(task_id, "project_ids", f"unknown project: {project_id}"))
        ticket = row.get("ticket")
        if isinstance(ticket, str):
            match = AIF_VALUE_RE.fullmatch(ticket.strip())
            if match:
                lane_id = canon_aif(match.group(1))
                task_lane_refs.add(lane_id)
                legacy_ticket_counts["lane_id"] += 1
                if lane_id not in intake_ids:
                    findings.append(finding(task_id, "ticket", f"AIF lane has no intake row: {lane_id}"))
            else:
                legacy_ticket_counts["external_ticket_id"] += 1
        else:
            legacy_ticket_counts["missing"] += 1

    run_ids: list[str] = []
    run_lane_refs: set[str] = set()
    report_ids_in_run_field = 0
    for path in yaml_files(runs_path):
        row = load_yaml(path)
        run_id = row.get("run_id")
        if not isinstance(run_id, str):
            findings.append(finding(path.name, "run_id", "run_id is required"))
            continue
        run_ids.append(run_id)
        if run_id.startswith("AIPR-"):
            report_ids_in_run_field += 1
        project_id = row.get("project")
        if isinstance(project_id, str) and project_id not in project_ids:
            findings.append(finding(run_id, "project", f"unknown project: {project_id}"))
        for value in row.get("lanes") or []:
            match = AIF_VALUE_RE.fullmatch(str(value))
            if not match:
                findings.append(finding(run_id, "lanes", f"invalid AIF lane reference: {value}"))
                continue
            run_lane_refs.add(canon_aif(match.group(1)))
    for run_id in duplicates(run_ids):
        findings.append(finding(run_id, "run_id", "duplicate run identity"))

    proof_ids: list[str] = []
    for path in yaml_files(proofs_path):
        row = load_yaml(path)
        proof_id = row.get("id")
        if not isinstance(proof_id, str):
            findings.append(finding(path.name, "proof_id", "proof id is required"))
        else:
            proof_ids.append(proof_id)
    for proof_id in duplicates(proof_ids):
        findings.append(finding(proof_id, "proof_id", "duplicate proof identity"))

    intake_set, claim_set = set(intake_ids), set(claim_ids)
    observations.extend([
        {"kind": "aif_claim_backfill", "intake_without_claim": len(intake_set - claim_set), "claim_without_intake": len(claim_set - intake_set)},
        {"kind": "legacy_ticket_crosswalk", **dict(sorted(legacy_ticket_counts.items()))},
        {"kind": "run_report_compatibility", "report_ids_in_run_id_field": report_ids_in_run_field},
        {"kind": "lane_references", "task_lanes": len(task_lane_refs), "run_lanes": len(run_lane_refs), "task_lanes_without_claim": len(task_lane_refs - claim_set), "run_lanes_without_intake": len(run_lane_refs - intake_set)},
    ])
    summary = {
        "identifier_classes": len(class_ids),
        "projects": len(project_ids),
        "aif_intake_rows": len(intake_ids),
        "aif_claims": len(claim_ids),
        "rulings": len(ruling_ids),
        "runs": len(run_ids),
        "work_items": len(task_ids),
        "proofs": len(proof_ids),
        "findings": len(findings),
    }
    return {"summary": summary, "observations": observations}, findings


def render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# AI Portal Identifier Normalization Status",
        "",
        "Generated from the typed identifier model and maintained authorities. Do not hand-edit.",
        "",
        "## Inventory",
        "",
        "| Class | Records |",
        "| --- | ---: |",
    ]
    for key in ("identifier_classes", "projects", "aif_intake_rows", "aif_claims", "rulings", "runs", "work_items", "proofs"):
        lines.append(f"| `{key}` | {summary[key]} |")
    lines.extend(["", "## Compatibility observations", ""])
    for item in result["observations"]:
        kind = item["kind"]
        detail = ", ".join(f"{key}={value}" for key, value in item.items() if key != "kind")
        lines.append(f"- `{kind}`: {detail}")
    lines.extend(["", "## Findings", ""])
    if result["findings"]:
        for item in result["findings"]:
            lines.append(f"- `{item['subject']}` [{item['field']}]: {item['issue']}")
    else:
        lines.append("No structural identifier findings.")
    lines.extend([
        "",
        "## Boundary",
        "",
        "Legacy fields are classified, not rewritten. Backfill gaps remain advisory until an owner ruling promotes them to a hard gate.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        model = load_yaml(args.model)
        body, findings = validate_model(model, args.repo_root.resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"portal-identifier-validator: error -- {exc}", file=sys.stderr)
        return 1
    result = {"schema": "dottalk.portal.identifier.status.v1", "mode": "development_advisory", **body, "findings": findings}
    json_text = json.dumps(result, indent=2) + "\n"
    markdown_text = render_markdown(result)
    if args.check:
        stale = []
        if not args.out_json.is_file() or args.out_json.read_text(encoding="utf-8") != json_text:
            stale.append(str(args.out_json))
        if not args.out_markdown.is_file() or args.out_markdown.read_text(encoding="utf-8") != markdown_text:
            stale.append(str(args.out_markdown))
        if stale:
            print(f"portal-identifier-validator: stale -- {', '.join(stale)}")
            return 3
    else:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json_text, encoding="utf-8")
        args.out_markdown.write_text(markdown_text, encoding="utf-8")
    if findings:
        print(f"portal-identifier-validator: advisory -- {len(findings)} structural finding(s)")
        return 3
    print("portal-identifier-validator: PASS -- identifier model is structurally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
