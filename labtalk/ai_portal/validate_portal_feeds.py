#!/usr/bin/env python3
"""Validate the typed DotTalk++ -> AI Portal feed registry.

This validator is advisory by contract. Exit 0 means no findings, exit 3 means
the registry was evaluated and findings were reported, and exit 1 means the
registry could not be parsed or evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_REGISTRY = LABTALK_ROOT / "registries" / "portal_feeds.yaml"

SCHEMA = "dottalk.portal.feed.v1"
EVIDENCE_STATES = {"planned", "source-evidenced", "runtime-proven"}
FEED_STATUSES = {"active", "degraded", "planned", "retired"}
FRESHNESS_POLICIES = {"validate_on_change", "run_scoped", "manual_review", "immutable"}
RETENTION_CLASSES = {"tracked", "transient", "external"}
SENSITIVITY_RANK = {"public": 0, "internal": 1, "restricted": 2}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


def load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def finding(feed_id: str, field: str, issue: str) -> dict[str, str]:
    return {"feed_id": feed_id, "field": field, "issue": issue, "severity": "advisory"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_repo_path(value: Any, repo_root: Path) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "path must be a non-empty string"
    path = Path(value)
    if path.is_absolute():
        return None, "repository paths must be relative"
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None, "path escapes the repository root"
    return resolved, None


def git_path_is_tracked(repo_root: Path, relative_path: str, *, is_directory: bool = False) -> bool:
    pathspec = f"{relative_path}/**" if is_directory else relative_path
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", pathspec],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def git_commit_exists(repo_root: Path, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def validate_artifact(
    *,
    feed_id: str,
    field: str,
    artifact: Any,
    repo_root: Path,
    observations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(artifact, dict):
        return [finding(feed_id, field, "artifact must be a mapping")]

    retention = artifact.get("retention")
    if retention not in RETENTION_CLASSES:
        findings.append(finding(feed_id, f"{field}.retention", f"unsupported retention: {retention}"))
        return findings

    if retention == "external":
        uri = artifact.get("uri")
        if not isinstance(uri, str) or "://" not in uri:
            findings.append(finding(feed_id, f"{field}.uri", "external artifact requires an absolute URI"))
        if artifact.get("path") is not None:
            findings.append(finding(feed_id, f"{field}.path", "external artifact must not claim repository path validation"))
        observations.append({"feed_id": feed_id, "field": field, "retention": retention, "uri": uri})
        return findings

    resolved, path_issue = resolve_repo_path(artifact.get("path"), repo_root)
    if path_issue:
        return [finding(feed_id, f"{field}.path", path_issue)]
    assert resolved is not None
    relative = resolved.relative_to(repo_root.resolve()).as_posix()
    exists = resolved.exists()
    observation: dict[str, Any] = {
        "feed_id": feed_id,
        "field": field,
        "retention": retention,
        "path": relative,
        "exists": exists,
    }
    if not exists:
        findings.append(finding(feed_id, f"{field}.path", f"path does not exist: {relative}"))
        observations.append(observation)
        return findings

    if retention == "tracked" and not git_path_is_tracked(repo_root, relative, is_directory=resolved.is_dir()):
        findings.append(finding(feed_id, f"{field}.retention", f"path is not tracked: {relative}"))

    expected_hash = artifact.get("sha256")
    if expected_hash is not None and (not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash)):
        findings.append(finding(feed_id, f"{field}.sha256", "sha256 must contain exactly 64 hexadecimal characters"))
    if resolved.is_file():
        actual_hash = sha256_file(resolved)
        observation["sha256"] = actual_hash
        if isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash):
            if actual_hash.lower() != expected_hash.lower():
                findings.append(
                    finding(
                        feed_id,
                        f"{field}.sha256",
                        f"ATTESTATION_STALE expected {expected_hash.lower()} observed {actual_hash}",
                    )
                )
    elif expected_hash is not None:
        findings.append(finding(feed_id, f"{field}.sha256", "sha256 may pin files only"))

    observations.append(observation)
    return findings


def find_cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    active: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            start = active.index(node)
            cycle = active[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        active.append(node)
        for parent in edges.get(node, []):
            visit(parent)
        active.pop()
        visited.add(node)

    for feed_id in edges:
        visit(feed_id)
    return cycles


def validate_registry(data: dict[str, Any], repo_root: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    observations: list[dict[str, Any]] = []

    if data.get("schema") != SCHEMA:
        findings.append(finding("<registry>", "schema", f"expected {SCHEMA}"))
    feeds = data.get("feeds")
    if not isinstance(feeds, list) or not feeds:
        findings.append(finding("<registry>", "feeds", "feeds must be a non-empty list"))
        return findings, observations

    feed_ids: list[str] = []
    for index, feed in enumerate(feeds):
        if not isinstance(feed, dict):
            findings.append(finding("<registry>", f"feeds[{index}]", "feed must be a mapping"))
            continue
        feed_id = feed.get("feed_id")
        if not isinstance(feed_id, str) or not feed_id.strip():
            findings.append(finding("<registry>", f"feeds[{index}].feed_id", "feed_id must be a non-empty string"))
            continue
        feed_ids.append(feed_id)

    duplicates = sorted({feed_id for feed_id in feed_ids if feed_ids.count(feed_id) > 1})
    for feed_id in duplicates:
        findings.append(finding(feed_id, "feed_id", "duplicate feed_id"))
    known_ids = set(feed_ids)
    edges: dict[str, list[str]] = {}

    for index, feed in enumerate(feeds):
        if not isinstance(feed, dict):
            continue
        feed_id = feed.get("feed_id")
        if not isinstance(feed_id, str) or not feed_id.strip():
            continue

        status = feed.get("status")
        if status not in FEED_STATUSES:
            findings.append(finding(feed_id, "status", f"unsupported status: {status}"))
        if not isinstance(feed.get("subject_class"), str) or not feed["subject_class"].strip():
            findings.append(finding(feed_id, "subject_class", "subject_class must be a non-empty string"))

        phase = feed.get("phase")
        if not isinstance(phase, dict) or not isinstance(phase.get("canonical"), str):
            findings.append(finding(feed_id, "phase.canonical", "canonical process name is required"))

        sensitivity = feed.get("sensitivity")
        if sensitivity not in SENSITIVITY_RANK:
            findings.append(finding(feed_id, "sensitivity", f"unsupported sensitivity: {sensitivity}"))

        source_commit = feed.get("source_commit")
        if source_commit is not None:
            if not isinstance(source_commit, str) or not COMMIT_RE.fullmatch(source_commit):
                findings.append(finding(feed_id, "source_commit", "source_commit must be a 7-40 digit hexadecimal commit id"))
            elif not git_commit_exists(repo_root, source_commit):
                findings.append(finding(feed_id, "source_commit", f"commit is not available: {source_commit}"))

        sources = feed.get("source_authorities")
        if not isinstance(sources, list) or not sources:
            findings.append(finding(feed_id, "source_authorities", "at least one source authority is required"))
        else:
            for item_index, artifact in enumerate(sources):
                findings.extend(
                    validate_artifact(
                        feed_id=feed_id,
                        field=f"source_authorities[{item_index}]",
                        artifact=artifact,
                        repo_root=repo_root,
                        observations=observations,
                    )
                )

        producer = feed.get("producer")
        findings.extend(
            validate_artifact(
                feed_id=feed_id,
                field="producer",
                artifact=producer,
                repo_root=repo_root,
                observations=observations,
            )
        )
        if isinstance(producer, dict) and not isinstance(producer.get("kind"), str):
            findings.append(finding(feed_id, "producer.kind", "producer kind is required"))

        outputs = feed.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            findings.append(finding(feed_id, "outputs", "at least one output is required"))
            outputs = []
        for item_index, artifact in enumerate(outputs):
            findings.extend(
                validate_artifact(
                    feed_id=feed_id,
                    field=f"outputs[{item_index}]",
                    artifact=artifact,
                    repo_root=repo_root,
                    observations=observations,
                )
            )

        evidence = feed.get("evidence")
        proofs: list[Any] = []
        if not isinstance(evidence, dict):
            findings.append(finding(feed_id, "evidence", "evidence must be a mapping"))
            evidence_state = None
        else:
            evidence_state = evidence.get("state")
            if evidence_state not in EVIDENCE_STATES:
                findings.append(finding(feed_id, "evidence.state", f"unsupported evidence state: {evidence_state}"))
            if not isinstance(evidence.get("platform"), str) or not evidence["platform"].strip():
                findings.append(finding(feed_id, "evidence.platform", "platform qualification is required"))
            proof_value = evidence.get("proofs")
            if isinstance(proof_value, list):
                proofs = proof_value
            else:
                findings.append(finding(feed_id, "evidence.proofs", "proofs must be a list"))
        for item_index, artifact in enumerate(proofs):
            findings.extend(
                validate_artifact(
                    feed_id=feed_id,
                    field=f"evidence.proofs[{item_index}]",
                    artifact=artifact,
                    repo_root=repo_root,
                    observations=observations,
                )
            )
        if evidence_state == "runtime-proven" and not proofs:
            findings.append(finding(feed_id, "evidence.proofs", "runtime-proven feed requires a retained proof"))

        has_tracked_proof = any(isinstance(proof, dict) and proof.get("retention") == "tracked" for proof in proofs)
        for item_index, artifact in enumerate(outputs):
            if isinstance(artifact, dict) and artifact.get("retention") == "transient":
                if not isinstance(artifact.get("sha256"), str) or not SHA256_RE.fullmatch(artifact["sha256"]):
                    findings.append(finding(feed_id, f"outputs[{item_index}].sha256", "transient output requires a SHA-256 pin"))
                if not has_tracked_proof:
                    findings.append(finding(feed_id, f"outputs[{item_index}].retention", "transient output requires a tracked proof"))

        parents = feed.get("derived_from")
        if not isinstance(parents, list):
            findings.append(finding(feed_id, "derived_from", "derived_from must be a list"))
            parents = []
        string_parents = [parent for parent in parents if isinstance(parent, str)]
        if len(string_parents) != len(parents):
            findings.append(finding(feed_id, "derived_from", "every parent must be a feed_id string"))
        for parent in string_parents:
            if parent not in known_ids:
                findings.append(finding(feed_id, "derived_from", f"unknown parent feed: {parent}"))
        edges[feed_id] = string_parents

        consumers = feed.get("consumers")
        if not isinstance(consumers, list) or not consumers:
            findings.append(finding(feed_id, "consumers", "at least one consumer is required"))
            consumers = []
        for item_index, consumer in enumerate(consumers):
            field = f"consumers[{item_index}]"
            findings.extend(
                validate_artifact(
                    feed_id=feed_id,
                    field=field,
                    artifact=consumer,
                    repo_root=repo_root,
                    observations=observations,
                )
            )
            if not isinstance(consumer, dict):
                continue
            visibility = consumer.get("visibility")
            if visibility not in SENSITIVITY_RANK:
                findings.append(finding(feed_id, f"{field}.visibility", f"unsupported visibility: {visibility}"))
            elif sensitivity in SENSITIVITY_RANK and SENSITIVITY_RANK[visibility] < SENSITIVITY_RANK[sensitivity]:
                findings.append(
                    finding(
                        feed_id,
                        f"{field}.visibility",
                        f"visibility leak: {sensitivity} feed cannot flow directly to {visibility} consumer",
                    )
                )

        freshness = feed.get("freshness")
        if not isinstance(freshness, dict) or freshness.get("policy") not in FRESHNESS_POLICIES:
            policy = freshness.get("policy") if isinstance(freshness, dict) else None
            findings.append(finding(feed_id, "freshness.policy", f"unsupported freshness policy: {policy}"))

    for cycle in find_cycles(edges):
        findings.append(finding(cycle[0], "derived_from", f"lineage cycle: {' -> '.join(cycle)}"))

    return findings, observations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    try:
        data = load_registry(args.registry)
        findings, observations = validate_registry(data, args.repo_root.resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"portal-feed-validator: error -- {exc}", file=sys.stderr)
        return 1

    result = {
        "schema": "dottalk.portal.feed.validation.v1",
        "registry": str(args.registry),
        "mode": "report_only",
        "feeds": len(data.get("feeds", [])),
        "observations": observations,
        "findings": findings,
        "summary": {"findings": len(findings), "observations": len(observations)},
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if findings:
        print(f"portal-feed-validator: advisory -- {len(findings)} finding(s)")
        for item in findings:
            print(f"- {item['feed_id']} [{item['field']}]: {item['issue']}")
        return 3

    print(f"portal-feed-validator: PASS -- {result['feeds']} feed(s), {len(observations)} artifact observation(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
