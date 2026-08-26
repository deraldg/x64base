#!/usr/bin/env python3
"""Validate structured Portal assertions without interpreting free prose."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_REGISTRY = LABTALK_ROOT / "registries" / "portal_assertions.yaml"
SCHEMA = "dottalk.portal.assertions.v1"
VALIDITIES = {"invariant", "perishable"}
STATUSES = {"active", "retired"}
CHECK_KINDS = {"yaml_value", "yaml_collection_has"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def parse_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


def resolve_path(repo_root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "path must be a non-empty string"
    candidate = Path(value)
    if candidate.is_absolute():
        return None, "repository path must be relative"
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None, "path escapes repository root"
    return resolved, None


def is_tracked(repo_root: Path, relative: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def nested_value(data: Any, selector: str) -> tuple[Any, str | None]:
    value = data
    if not isinstance(selector, str) or not selector:
        return None, "selector must be a non-empty dotted path"
    for part in selector.split("."):
        if not isinstance(value, dict) or part not in value:
            return None, f"selector not found: {selector}"
        value = value[part]
    return value, None


def issue(claim_id: str, field: str, message: str) -> dict[str, str]:
    return {"claim_id": claim_id, "field": field, "issue": message, "severity": "advisory"}


def validate_assertions(
    data: dict[str, Any],
    repo_root: Path,
    *,
    now: datetime | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    observations: list[dict[str, Any]] = []
    current_time = now or datetime.now(timezone.utc)

    if data.get("schema") != SCHEMA:
        findings.append(issue("<registry>", "schema", f"expected {SCHEMA}"))
    assertions = data.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        findings.append(issue("<registry>", "assertions", "assertions must be a non-empty list"))
        return findings, observations

    claim_ids = [item.get("claim_id") for item in assertions if isinstance(item, dict)]
    for claim_id in sorted({value for value in claim_ids if claim_ids.count(value) > 1 and isinstance(value, str)}):
        findings.append(issue(claim_id, "claim_id", "duplicate claim_id"))

    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict):
            findings.append(issue("<registry>", f"assertions[{index}]", "assertion must be a mapping"))
            continue
        claim_id = assertion.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            findings.append(issue("<registry>", f"assertions[{index}].claim_id", "claim_id is required"))
            continue
        status = assertion.get("status")
        if status not in STATUSES:
            findings.append(issue(claim_id, "status", f"unsupported status: {status}"))
        validity = assertion.get("validity")
        if validity not in VALIDITIES:
            findings.append(issue(claim_id, "validity", f"unsupported validity: {validity}"))
        for field in ("subject", "predicate", "platform"):
            if not isinstance(assertion.get(field), str) or not assertion[field].strip():
                findings.append(issue(claim_id, field, f"{field} is required"))

        if validity == "perishable":
            measured = parse_utc(assertion.get("measured_at_utc"))
            expires = parse_utc(assertion.get("expires_at_utc"))
            if measured is None:
                findings.append(issue(claim_id, "measured_at_utc", "perishable assertion requires UTC measurement time"))
            if expires is None:
                findings.append(issue(claim_id, "expires_at_utc", "perishable assertion requires UTC expiry"))
            elif expires <= current_time:
                findings.append(issue(claim_id, "expires_at_utc", f"ASSERTION_EXPIRED at {assertion.get('expires_at_utc')}"))
            if measured is not None and expires is not None and expires <= measured:
                findings.append(issue(claim_id, "expires_at_utc", "expiry must be after measurement"))

        evidence = assertion.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(issue(claim_id, "evidence", "at least one evidence artifact is required"))
            evidence = []
        for evidence_index, artifact in enumerate(evidence):
            field = f"evidence[{evidence_index}]"
            if not isinstance(artifact, dict):
                findings.append(issue(claim_id, field, "evidence artifact must be a mapping"))
                continue
            resolved, path_issue = resolve_path(repo_root, artifact.get("path"))
            if path_issue:
                findings.append(issue(claim_id, f"{field}.path", path_issue))
                continue
            assert resolved is not None
            relative = resolved.relative_to(repo_root.resolve()).as_posix()
            if not resolved.is_file():
                findings.append(issue(claim_id, f"{field}.path", f"evidence file does not exist: {relative}"))
                continue
            if artifact.get("retention") != "tracked" or not is_tracked(repo_root, relative):
                findings.append(issue(claim_id, f"{field}.retention", f"evidence is not tracked: {relative}"))
            anchor = artifact.get("anchor")
            if anchor is not None:
                if not isinstance(anchor, str) or not anchor:
                    findings.append(issue(claim_id, f"{field}.anchor", "anchor must be a non-empty string"))
                else:
                    count = resolved.read_text(encoding="utf-8").count(anchor)
                    if count != 1:
                        findings.append(issue(claim_id, f"{field}.anchor", f"anchor must occur exactly once; observed {count}"))

        check = assertion.get("check")
        if not isinstance(check, dict):
            findings.append(issue(claim_id, "check", "check must be a mapping"))
            continue
        kind = check.get("kind")
        if kind not in CHECK_KINDS:
            findings.append(issue(claim_id, "check.kind", f"unsupported structured check: {kind}"))
            continue
        resolved, path_issue = resolve_path(repo_root, check.get("path"))
        if path_issue:
            findings.append(issue(claim_id, "check.path", path_issue))
            continue
        assert resolved is not None
        if not resolved.is_file():
            findings.append(issue(claim_id, "check.path", f"check source does not exist: {check.get('path')}"))
            continue
        try:
            source = load_yaml(resolved)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(issue(claim_id, "check.path", f"cannot load structured source: {exc}"))
            continue
        selected, selector_issue = nested_value(source, check.get("selector"))
        if selector_issue:
            findings.append(issue(claim_id, "check.selector", selector_issue))
            continue
        expected = check.get("expected")
        passed = False
        actual: Any = selected
        if kind == "yaml_value":
            if check.get("operator") != "equals":
                findings.append(issue(claim_id, "check.operator", "yaml_value supports only equals"))
            else:
                passed = selected == expected
        elif kind == "yaml_collection_has":
            match_field = check.get("match_field")
            if not isinstance(selected, list):
                findings.append(issue(claim_id, "check.selector", "selected value must be a list"))
            elif not isinstance(match_field, str) or not match_field:
                findings.append(issue(claim_id, "check.match_field", "match_field is required"))
            else:
                actual = [item.get(match_field) for item in selected if isinstance(item, dict)]
                passed = expected in actual
        if not passed:
            findings.append(issue(claim_id, "check", f"ASSERTION_FALSE expected {expected!r} observed {actual!r}"))
        observations.append(
            {
                "claim_id": claim_id,
                "kind": kind,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "validity": validity,
            }
        )

    return findings, observations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = load_yaml(args.registry)
        findings, observations = validate_assertions(data, args.repo_root.resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"portal-assertion-validator: error -- {exc}", file=sys.stderr)
        return 1
    result = {
        "schema": "dottalk.portal.assertion.validation.v1",
        "mode": "structured_only",
        "assertions": len(data.get("assertions", [])),
        "observations": observations,
        "findings": findings,
        "summary": {"findings": len(findings), "observations": len(observations)},
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if findings:
        print(f"portal-assertion-validator: advisory -- {len(findings)} finding(s)")
        for item in findings:
            print(f"- {item['claim_id']} [{item['field']}]: {item['issue']}")
        return 3
    print(f"portal-assertion-validator: PASS -- {len(observations)} structured assertion(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
