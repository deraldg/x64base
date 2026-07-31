#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REQUIRED_COLUMNS = {
    "baseline_id",
    "before_seconds",
    "after_seconds",
    "after_seconds_min",
    "after_seconds_max",
    "speedup_x",
    "speedup_min_x",
    "speedup_max_x",
    "machine_type",
    "machine_binding",
    "before_evidence_path",
    "before_evidence_sha256",
    "after_evidence_path",
    "after_evidence_sha256",
    "transcript_status",
    "proof_state",
}


def _number(value: str) -> float | None:
    return float(value) if value.strip() else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate_rows(rows: list[dict[str, str]], repo_root: Path) -> list[str]:
    findings: list[str] = []
    if len(rows) != 8:
        findings.append(f"ROW_COUNT:{len(rows)}!=8")
    ids = [row.get("baseline_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        findings.append("DUPLICATE_BASELINE_ID")
    for index, row in enumerate(rows, start=2):
        prefix = f"ROW_{index}:{row.get('baseline_id', '')}"
        before = _number(row.get("before_seconds", ""))
        after = _number(row.get("after_seconds", ""))
        after_min = _number(row.get("after_seconds_min", ""))
        after_max = _number(row.get("after_seconds_max", ""))
        if before is None or before <= 0:
            findings.append(f"{prefix}:INVALID_BEFORE")
        if not row.get("machine_type", "").strip() or not row.get("machine_binding", "").strip():
            findings.append(f"{prefix}:MACHINE_VARIABLE_MISSING")
        if not row.get("transcript_status", "").strip() or not row.get("proof_state", "").strip():
            findings.append(f"{prefix}:PROOF_CLASSIFICATION_MISSING")
        if before is not None and after is not None:
            expected = before / after
            actual = _number(row.get("speedup_x", ""))
            if actual is None or abs(expected - actual) > 0.02:
                findings.append(f"{prefix}:EXACT_SPEEDUP_MISMATCH")
        elif before is not None and after_min is not None and after_max is not None:
            expected_min = before / after_max
            expected_max = before / after_min
            actual_min = _number(row.get("speedup_min_x", ""))
            actual_max = _number(row.get("speedup_max_x", ""))
            if actual_min is None or abs(expected_min - actual_min) > 0.02:
                findings.append(f"{prefix}:MIN_SPEEDUP_MISMATCH")
            if actual_max is None or abs(expected_max - actual_max) > 0.02:
                findings.append(f"{prefix}:MAX_SPEEDUP_MISMATCH")
        else:
            findings.append(f"{prefix}:AFTER_VALUE_MISSING")
        for side in ("before", "after"):
            evidence = row.get(f"{side}_evidence_path", "")
            expected_sha = row.get(f"{side}_evidence_sha256", "").upper()
            path = repo_root / evidence
            if not evidence or not path.exists():
                findings.append(f"{prefix}:{side.upper()}_EVIDENCE_MISSING")
            elif _sha256(path) != expected_sha:
                findings.append(f"{prefix}:{side.upper()}_EVIDENCE_HASH_MISMATCH")
    return findings


def validate_profile(profile: dict[str, object]) -> list[str]:
    """Validate both the original flat profile and the enriched v1 profile.

    The enriched profile keeps processor and memory provenance as structured
    objects. Historical runs may remain UNVERIFIED, or they may be attached by
    an explicit maintainer attestation that carries its own source and honesty
    note. A post-hoc attestation is never treated as per-run auto-capture.
    """

    findings: list[str] = []
    for field in ("machine_type", "os"):
        if profile.get(field) in (None, ""):
            findings.append(f"PROFILE_FIELD_MISSING:{field}")

    cpu = profile.get("cpu")
    if isinstance(cpu, dict):
        if not cpu.get("name"):
            findings.append("PROFILE_FIELD_MISSING:cpu.name")
        logical_processors = (
            profile.get("logical_processors")
            or cpu.get("threads_total")
        )
    else:
        if cpu in (None, ""):
            findings.append("PROFILE_FIELD_MISSING:cpu")
        logical_processors = profile.get("logical_processors")
    if logical_processors in (None, ""):
        findings.append("PROFILE_FIELD_MISSING:logical_processors")

    memory = profile.get("memory")
    if isinstance(memory, dict):
        memory_gib = (
            profile.get("memory_gib")
            or memory.get("os_visible_gib")
            or memory.get("installed_gb")
        )
    else:
        memory_gib = profile.get("memory_gib")
    if memory_gib in (None, ""):
        findings.append("PROFILE_FIELD_MISSING:memory_gib")

    binding = profile.get("historical_run_binding")
    if binding == "UNVERIFIED":
        return findings
    if binding != "MAINTAINER_ATTESTED":
        findings.append("PROFILE_HISTORICAL_BINDING_INVALID")
        return findings

    attestation = profile.get("maintainer_attestation")
    if not isinstance(attestation, dict):
        findings.append("PROFILE_MAINTAINER_ATTESTATION_MISSING")
    else:
        for field in ("statement", "source", "authority"):
            if attestation.get(field) in (None, ""):
                findings.append(
                    f"PROFILE_MAINTAINER_ATTESTATION_FIELD_MISSING:{field}"
                )
    if profile.get("honesty_note") in (None, ""):
        findings.append("PROFILE_MAINTAINER_ATTESTATION_HONESTY_NOTE_MISSING")
    return findings


def validate(repo_root: Path) -> tuple[list[dict[str, str]], dict[str, object], list[str]]:
    csv_path = repo_root / "docs/maintenance/PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv"
    profile_path = repo_root / "docs/maintenance/PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        rows = list(reader)
    findings = [] if REQUIRED_COLUMNS <= columns else ["CSV_REQUIRED_COLUMNS_MISSING"]
    findings.extend(validate_rows(rows, repo_root))
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    findings.extend(validate_profile(profile))
    return rows, profile, findings


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    rows, profile, findings = validate(repo_root)
    status = "PASS" if not findings else "FAIL"
    print(
        f"pinocchio_benchmark_baseline status={status} rows={len(rows)} "
        f"machine_type={profile.get('machine_type', '')} findings={len(findings)}"
    )
    for finding in findings:
        print(f"finding={finding}")
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
