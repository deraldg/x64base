"""Validate mandatory identity and provenance envelopes on AI-authored reports.

Scans two report classes:

* Session closeouts (`closeout_glob`) -- every matching file must carry a valid
  `ai_report_audit` envelope. Findings here are **hard** (non-zero exit).
* Received external-AI intake packages (`external_intake_glob`, optional) -- files
  under the intake landing zone that carry an envelope are validated with
  intake-appropriate rules. These packages are preserved **verbatim** as
  evidence, so their findings are **advisory** (reported, but do not fail the
  audit) and `report.path` agreement is not enforced against the sender's claim.

With `--emit-index`, discovered reports are append-merged into the report
discoverability index (`ai_report_index.yaml`) without clobbering curated
`topics`/`aliases`/`notes` on existing entries.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_POLICY = LABTALK_ROOT / "registries" / "ai_report_audit.yaml"

CLOSEOUT_KINDS = {"session_closeout"}
INTAKE_KINDS = {"review_needed_change_package", "intake_assessment"}


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return data


def read_markdown_front_matter(path: Path) -> tuple[dict[str, Any], str | None]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing YAML front matter"
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, "unterminated YAML front matter"
    try:
        data = yaml.safe_load("\n".join(lines[1:closing])) or {}
    except yaml.YAMLError as exc:
        return {}, f"invalid YAML front matter: {exc}"
    if not isinstance(data, dict):
        return {}, "YAML front matter must be a mapping"
    return data, None


def nested_value(data: dict[str, Any], dotted_path: str) -> Any:
    value: Any = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def relative_report_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def normalized_path(value: str, repo_root: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    return os.path.normcase(os.path.normpath(str(path.resolve())))


def project_roots(project_registry: Path) -> dict[str, str]:
    data = load_yaml_mapping(project_registry)
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        raise ValueError(f"Expected projects list in {project_registry}")
    roots: dict[str, str] = {}
    for project in projects:
        if not isinstance(project, dict):
            continue
        project_id = project.get("id")
        root = project.get("root")
        if isinstance(project_id, str) and isinstance(root, str):
            roots[project_id] = root
    return roots


def index_record(front_matter: dict[str, Any], report: str) -> dict[str, Any] | None:
    """Build a discoverability-index record from a report's envelope."""
    envelope = front_matter.get("ai_report_audit")
    if not isinstance(envelope, dict):
        return None
    report_id = envelope.get("report_id")
    if not present(report_id):
        return None
    recorded = str(nested_value(front_matter, "ai_report_audit.recorded_at_utc") or "")
    topics = front_matter.get("primary_topics")
    record: dict[str, Any] = {
        "report_id": str(report_id).strip(),
        "provider": nested_value(front_matter, "ai_report_audit.agent.provider"),
        "product": nested_value(front_matter, "ai_report_audit.agent.product"),
        "date": recorded[:10] if recorded else None,
        "kind": nested_value(front_matter, "ai_report_audit.report.kind"),
        "project": nested_value(front_matter, "ai_report_audit.project.id"),
        "path": report,
    }
    if isinstance(topics, list) and topics:
        record["topics"] = topics
    return record


def validate_report(
    path: Path,
    repo_root: Path,
    policy: dict[str, Any],
    registered_projects: dict[str, str],
    *,
    allowed_kinds: set[str],
    enforce_report_path: bool,
) -> tuple[list[dict[str, str]], str | None, dict[str, Any] | None]:
    report = relative_report_path(path, repo_root)
    front_matter, parse_issue = read_markdown_front_matter(path)
    if parse_issue:
        return [{"report": report, "field": "front_matter", "issue": parse_issue}], None, None

    findings: list[dict[str, str]] = []
    required_fields = policy.get("required_fields", [])
    if not isinstance(required_fields, list):
        raise ValueError("report_audit.required_fields must be a list")
    for field in required_fields:
        if not isinstance(field, str):
            raise ValueError("report_audit.required_fields entries must be strings")
        if not present(nested_value(front_matter, field)):
            findings.append({"report": report, "field": field, "issue": "required field missing"})

    envelope = front_matter.get("ai_report_audit")
    if not isinstance(envelope, dict):
        return findings, None, None

    expected_schema = str(policy.get("schema", ""))
    if envelope.get("schema") != expected_schema:
        findings.append(
            {"report": report, "field": "ai_report_audit.schema", "issue": f"expected {expected_schema}"}
        )

    access_mode = nested_value(front_matter, "ai_report_audit.agent.access_mode")
    allowed_modes = policy.get("allowed_access_modes", [])
    if present(access_mode) and access_mode not in allowed_modes:
        findings.append(
            {"report": report, "field": "ai_report_audit.agent.access_mode", "issue": f"unregistered access mode: {access_mode}"}
        )

    project_id = nested_value(front_matter, "ai_report_audit.project.id")
    declared_root = nested_value(front_matter, "ai_report_audit.project.root")
    if present(project_id) and project_id not in registered_projects:
        findings.append(
            {"report": report, "field": "ai_report_audit.project.id", "issue": f"unknown project id: {project_id}"}
        )
    elif present(project_id) and present(declared_root):
        expected_root = registered_projects[str(project_id)]
        if normalized_path(str(declared_root), repo_root) != normalized_path(expected_root, repo_root):
            findings.append(
                {"report": report, "field": "ai_report_audit.project.root", "issue": f"does not match project registry root: {expected_root}"}
            )

    if enforce_report_path:
        declared_report = nested_value(front_matter, "ai_report_audit.report.path")
        if present(declared_report) and str(declared_report).replace("\\", "/") != report:
            findings.append(
                {"report": report, "field": "ai_report_audit.report.path", "issue": f"does not match file path: {report}"}
            )

    report_kind = nested_value(front_matter, "ai_report_audit.report.kind")
    if present(report_kind) and report_kind not in allowed_kinds:
        findings.append(
            {"report": report, "field": "ai_report_audit.report.kind", "issue": f"expected one of {sorted(allowed_kinds)}, got {report_kind}"}
        )

    report_id = envelope.get("report_id")
    resolved_id = str(report_id).strip() if present(report_id) else None
    return findings, resolved_id, index_record(front_matter, report)


# Backwards-compatible wrapper: closeouts enforce report.path and the closeout kind.
def validate_closeout(
    path: Path,
    repo_root: Path,
    policy: dict[str, Any],
    registered_projects: dict[str, str],
) -> tuple[list[dict[str, str]], str | None]:
    findings, report_id, _record = validate_report(
        path, repo_root, policy, registered_projects,
        allowed_kinds=CLOSEOUT_KINDS, enforce_report_path=True,
    )
    return findings, report_id


def audit_closeouts(repo_root: Path = REPO_ROOT, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    policy_data = load_yaml_mapping(policy_path)
    policy = policy_data.get("report_audit")
    if not isinstance(policy, dict):
        raise ValueError(f"Expected report_audit mapping in {policy_path}")

    project_registry = repo_root / str(policy.get("project_registry", ""))
    registered_projects = project_roots(project_registry)
    closeout_glob = str(policy.get("closeout_glob", ""))
    intake_glob = str(policy.get("external_intake_glob", "")).strip()
    template = str(policy.get("template", "")).replace("\\", "/")
    grandfathered = {
        str(entry).replace("\\", "/")
        for entry in policy.get("grandfathered_closeouts", [])
        if isinstance(entry, str)
    }

    findings: list[dict[str, str]] = []
    enforced_count = 0
    grandfathered_count = 0
    valid_count = 0
    report_ids: dict[str, str] = {}
    reports: list[dict[str, Any]] = []
    closeouts = sorted(repo_root.glob(closeout_glob)) if closeout_glob else []

    for path in closeouts:
        report = relative_report_path(path, repo_root)
        if report == template:
            continue
        if report in grandfathered:
            grandfathered_count += 1
            continue
        enforced_count += 1
        report_findings, report_id, record = validate_report(
            path, repo_root, policy, registered_projects,
            allowed_kinds=CLOSEOUT_KINDS, enforce_report_path=True,
        )
        if report_id:
            if report_id in report_ids:
                report_findings.append(
                    {"report": report, "field": "ai_report_audit.report_id", "issue": f"duplicate report id also used by {report_ids[report_id]}"}
                )
            else:
                report_ids[report_id] = report
        findings.extend(report_findings)
        if not report_findings:
            valid_count += 1
        if record:
            reports.append(record)

    existing_reports = {relative_report_path(path, repo_root) for path in closeouts}
    for report in sorted(grandfathered - existing_reports):
        findings.append(
            {"report": report, "field": "grandfathered_closeouts", "issue": "grandfathered path does not exist"}
        )

    # Received external-AI intake packages: advisory, verbatim-preserved.
    intake_findings: list[dict[str, str]] = []
    intake_enforced_count = 0
    intake_files = sorted(repo_root.glob(intake_glob)) if intake_glob else []
    for path in intake_files:
        front_matter, parse_issue = read_markdown_front_matter(path)
        if parse_issue or not isinstance(front_matter.get("ai_report_audit"), dict):
            continue  # intake dirs hold non-report files (README, SUMMARY, proposed_*)
        intake_enforced_count += 1
        report = relative_report_path(path, repo_root)
        pkg_findings, report_id, record = validate_report(
            path, repo_root, policy, registered_projects,
            allowed_kinds=INTAKE_KINDS, enforce_report_path=False,
        )
        if report_id:
            if report_id in report_ids:
                pkg_findings.append(
                    {"report": report, "field": "ai_report_audit.report_id", "issue": f"duplicate report id also used by {report_ids[report_id]}"}
                )
            else:
                report_ids[report_id] = report
        intake_findings.extend(pkg_findings)
        if record:
            reports.append(record)

    return {
        "schema": str(policy.get("schema", "")),
        "status": str(policy.get("status", "")),
        "policy_path": relative_report_path(policy_path, repo_root),
        "project_registry": relative_report_path(project_registry, repo_root),
        "closeout_count": len(closeouts) - (1 if template in existing_reports else 0),
        "grandfathered_count": grandfathered_count,
        "enforced_count": enforced_count,
        "valid_count": valid_count,
        "finding_count": len(findings),
        "findings": findings,
        "intake_enforced_count": intake_enforced_count,
        "intake_finding_count": len(intake_findings),
        "intake_findings": intake_findings,
        "reports": reports,
    }


def emit_index(reports: list[dict[str, Any]], index_path: Path) -> dict[str, int]:
    """Append-merge discovered reports into the discoverability index.

    Existing entries (with curated topics/aliases/notes) are preserved verbatim;
    only report_ids not already indexed are appended.
    """
    if index_path.exists():
        index = load_yaml_mapping(index_path)
    else:
        index = {"schema": "ai-report-index-v1", "status": "active_seed", "reports": []}
    existing = index.get("reports")
    if not isinstance(existing, list):
        existing = []
    known = {r.get("report_id") for r in existing if isinstance(r, dict)}
    added = 0
    for record in reports:
        rid = record.get("report_id")
        if not rid or rid in known:
            continue
        entry = {k: v for k, v in record.items() if v is not None}
        entry.setdefault("status", "indexed")
        existing.append(entry)
        known.add(rid)
        added += 1
    index["reports"] = existing
    index["generated_by"] = "audit_trail.py --emit-index"
    with index_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(index, handle, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return {"appended": added, "total": len(existing)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full audit result as JSON")
    parser.add_argument(
        "--emit-index", type=Path, nargs="?",
        const=DEFAULT_POLICY.parent / "ai_report_index.yaml",
        help="append-merge discovered reports into the discoverability index "
             "(default: labtalk/registries/ai_report_index.yaml)",
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()

    audit = audit_closeouts(args.repo_root, args.policy)
    if args.json:
        print(json.dumps(audit, indent=2))
    else:
        print(
            "ai_report_audit "
            f"enforced={audit['enforced_count']} "
            f"valid={audit['valid_count']} "
            f"grandfathered={audit['grandfathered_count']} "
            f"findings={audit['finding_count']} "
            f"intake={audit['intake_enforced_count']} "
            f"intake_findings={audit['intake_finding_count']}"
        )
        for finding in audit["findings"]:
            print(f"- {finding['report']} [{finding['field']}]: {finding['issue']}")
        for finding in audit["intake_findings"]:
            print(f"- (advisory) {finding['report']} [{finding['field']}]: {finding['issue']}")

    if args.emit_index is not None:
        result = emit_index(audit["reports"], args.emit_index)
        print(f"index: appended={result['appended']} total={result['total']} -> {args.emit_index}")

    return 1 if audit["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
