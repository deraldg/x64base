#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MIN_PYTHON = (3, 12)
MANUAL_PATH = "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md"
PRIMARY_ARTIFACT_PATH = "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
COMMAND_ARTIFACT_PATH = "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json"
COMMAND_INDEX_PATH = "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/command_reference_v1/README.md"
PUBLIC_BASE = "https://github.com/deraldg/x64base/blob/{commit}/{path}"


ROUTE_SPECS = (
    {
        "action": "REPLACE",
        "site_path": "public/downloads/current/developer_manual_publication_v1.md",
        "route": "/downloads/current/developer_manual_publication_v1.md",
        "proof_label": "manual-reviewed",
        "source_path": MANUAL_PATH,
        "proposal": "Replace the stale website download with the exact public-commit manual blob.",
    },
    {
        "action": "UPDATE",
        "site_path": "public/downloads/current/DOWNLOAD_MANIFEST.json",
        "route": "/downloads/current/DOWNLOAD_MANIFEST.json",
        "proof_label": "generated-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Bind the manual item to the source commit, Git blob, SHA-256, line/heading counts, and 183-page reference.",
    },
    {
        "action": "UPDATE",
        "site_path": "app/downloads/page.tsx",
        "route": "/downloads",
        "proof_label": "manual-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Label the Markdown manual accepted/current, expose commit provenance, and retain source-authority wording.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/dev/important-documents.mdx",
        "route": "/docs/dev/important-documents",
        "proof_label": "manual-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Advance the manual from planned to reviewed/published and link the download plus public source anchor.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/dev/website-documentation-matrix.mdx",
        "route": "/docs/dev/website-documentation-matrix",
        "proof_label": "generated-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Record the accepted manual, 183-page command reference, current Python 3.12 validation, and remaining website gates.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/dev/selfdoc-feed-pipeline.mdx",
        "route": "/docs/dev/selfdoc-feed-pipeline",
        "proof_label": "generated-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Replace the obsolete Python 3.11 limitation with the verified Python 3.12 workflow and accepted result.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/engine/feature-crosswalk.mdx",
        "route": "/docs/engine/feature-crosswalk",
        "proof_label": "generated-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Remove the stale Python 3.11 validation failure and cite the current accepted manual evidence.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/dottalk/command-catalog.mdx",
        "route": "/docs/dottalk/command-catalog",
        "proof_label": "help-catalog-evidenced",
        "source_path": COMMAND_ARTIFACT_PATH,
        "proposal": "Keep catalog and manual scopes distinct, then link the accepted 183-page reference and its snapshot commit.",
    },
    {
        "action": "UPDATE",
        "site_path": "content/docs/dev/developer-handbook.mdx",
        "route": "/docs/dev/developer-handbook",
        "proof_label": "manual-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Add the public manual/reference entrypoint and Gate 5 publication provenance.",
    },
    {
        "action": "CREATE",
        "site_path": "content/docs/dottalk/command-reference.mdx",
        "route": "/docs/dottalk/command-reference",
        "proof_label": "manual-reviewed",
        "source_path": COMMAND_INDEX_PATH,
        "proposal": "Create a stable landing page for the 183 accepted command pages without duplicating all reference prose into site source.",
    },
    {
        "action": "CREATE",
        "site_path": "content/news/announcements/developer-manual-gate5-published.mdx",
        "route": "/news/announcements/developer-manual-gate5-published",
        "proof_label": "generated-reviewed",
        "source_path": PRIMARY_ARTIFACT_PATH,
        "proposal": "Announce the reviewed manual/reference publication with conservative counts and source links.",
    },
)


def _run(repo: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=text,
        check=False,
    )
    if result.returncode:
        stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return result.stdout


def _blob(repo: Path, commit: str, path: str) -> bytes:
    return _run(repo, "cat-file", "blob", f"{commit}:{path}", text=False)  # type: ignore[return-value]


def _blob_oid(repo: Path, commit: str, path: str) -> str:
    return str(_run(repo, "rev-parse", f"{commit}:{path}")).strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _count_markdown(data: bytes) -> tuple[int, int]:
    lines = data.splitlines()
    return len(lines), sum(line.startswith(b"#") for line in lines)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _site_state(site_root: Path) -> dict[str, Any]:
    return {
        "branch": str(_run(site_root, "branch", "--show-current")).strip(),
        "head": str(_run(site_root, "rev-parse", "HEAD")).strip(),
        "remote": str(_run(site_root, "remote", "get-url", "origin")).strip(),
        "status_rows": len(str(_run(site_root, "status", "--porcelain=v1", "--untracked-files=all")).splitlines()),
    }


def build(public_repo: Path, public_commit: str, site_root: Path, output_dir: Path) -> dict[str, Any]:
    if sys.version_info < MIN_PYTHON:
        raise RuntimeError("Python 3.12 or newer is required")
    public_repo = public_repo.resolve()
    site_root = site_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    commit = str(_run(public_repo, "rev-parse", f"{public_commit}^{{commit}}")).strip()
    public_head = str(_run(public_repo, "rev-parse", "HEAD")).strip()
    ancestor = subprocess.run(
        ["git", "-C", str(public_repo), "merge-base", "--is-ancestor", commit, public_head],
        check=False,
    ).returncode == 0
    if not ancestor:
        raise RuntimeError("public source commit is not an ancestor of current public staging HEAD")

    site_before = _site_state(site_root)
    if site_before["status_rows"] != 0:
        raise RuntimeError("website repository must be clean for a report-only baseline")

    manual = _blob(public_repo, commit, MANUAL_PATH)
    primary = json.loads(_blob(public_repo, commit, PRIMARY_ARTIFACT_PATH))
    command = json.loads(_blob(public_repo, commit, COMMAND_ARTIFACT_PATH))
    manual_lines, manual_headings = _count_markdown(manual)
    tree = str(
        _run(
            public_repo,
            "ls-tree",
            "-r",
            "--name-only",
            commit,
            "--",
            "docs/manuals/developer/manualgen/published/developer_manual_publication_v1",
        )
    ).splitlines()
    command_pages = sum("/command_reference_v1/commands/" in path and path.endswith(".md") for path in tree)
    sections = sum("/sections/sections/" in path and path.endswith(".md") for path in tree)
    appendices = sum("/appendices/" in path and path.endswith(".md") for path in tree)

    site_manual_path = site_root / "public/downloads/current/developer_manual_publication_v1.md"
    site_manual = site_manual_path.read_bytes()
    site_lines, site_headings = _count_markdown(site_manual)
    manual_sha = _sha256_bytes(manual)
    manual_oid = _blob_oid(public_repo, commit, MANUAL_PATH)

    route_rows: list[dict[str, Any]] = []
    for spec in ROUTE_SPECS:
        current = site_root / spec["site_path"]
        exists = current.exists()
        if spec["action"] == "CREATE" and exists:
            raise RuntimeError(f"proposed CREATE target already exists: {spec['site_path']}")
        if spec["action"] != "CREATE" and not exists:
            raise RuntimeError(f"proposed update target missing: {spec['site_path']}")
        route_rows.append(
            {
                "action": spec["action"],
                "route": spec["route"],
                "site_path": spec["site_path"],
                "target_exists": int(exists),
                "current_site_sha256": _sha256_file(current) if exists else "ABSENT",
                "proof_label": spec["proof_label"],
                "source_commit": commit,
                "source_path": spec["source_path"],
                "source_git_blob_oid": _blob_oid(public_repo, commit, spec["source_path"]),
                "public_source_url": PUBLIC_BASE.format(commit=commit, path=spec["source_path"]),
                "proposal": spec["proposal"],
                "gate7_mutation_authorized": 0,
            }
        )

    payload = {
        "schema": "dottalk.website.documentation_feed.v1",
        "status": "GATE6_REPORT_ONLY_CANDIDATE",
        "source": {
            "repository": "https://github.com/deraldg/x64base.git",
            "commit": commit,
            "current_public_head_observed": public_head,
            "manual_path": MANUAL_PATH,
            "manual_git_blob_oid": manual_oid,
            "manual_blob_sha256": manual_sha,
            "manual_lines": manual_lines,
            "manual_headings": manual_headings,
            "manual_artifact_worktree_sha256": primary["artifact_sha256"],
            "command_reference_pages": command_pages,
            "reader_linked_command_pages": command["reader_linked_pages"],
            "supplemental_command_pages": command["supplemental_standalone_pages"],
            "command_lineage_rows": command["lineage_rows"],
            "sections": sections,
            "appendices": appendices,
        },
        "current_website": {
            "baseline_commit": site_before["head"],
            "branch": site_before["branch"],
            "manual_sha256": _sha256_bytes(site_manual),
            "manual_lines": site_lines,
            "manual_headings": site_headings,
            "manual_exact_to_public_source": site_manual == manual,
            "download_manifest_generated_on": json.loads(
                (site_root / "public/downloads/current/DOWNLOAD_MANIFEST.json").read_text(encoding="utf-8")
            )["generated_on"],
        },
        "routes": route_rows,
        "boundaries": {
            "website_files_mutated": 0,
            "website_build_run": 0,
            "website_commit_created": 0,
            "website_push_performed": 0,
            "website_deployment_performed": 0,
            "metacollect_mission_mutated": 0,
        },
    }

    payload_path = output_dir / "website_feed_payload_v1.json"
    ledger_path = output_dir / "website_feed_route_ledger_v1.csv"
    packet_path = output_dir / "WEBSITE_FEED_EXPORT_PACKET_V1.md"
    validation_path = output_dir / "website_feed_validation_v1.json"
    manifest_path = output_dir / "website_feed_manifest_v1.json"
    _write_json(payload_path, payload)
    _write_csv(ledger_path, route_rows)

    action_counts = {name: sum(row["action"] == name for row in route_rows) for name in ("CREATE", "UPDATE", "REPLACE")}
    packet_lines = [
        "# Gate 6 website feed/export packet v1",
        "",
        f"- Status: `GATE6_REPORT_ONLY_CANDIDATE`",
        f"- Public source commit: `{commit}`",
        f"- Website baseline: `{site_before['head']}` on `{site_before['branch']}`",
        f"- Proposed routes/files: {len(route_rows)} ({action_counts['CREATE']} create, {action_counts['UPDATE']} update, {action_counts['REPLACE']} replace)",
        "- Website mutation/build/commit/push/deploy: `0 / 0 / 0 / 0 / 0`",
        "",
        "## Source product",
        "",
        f"The reviewed manual has {manual_lines:,} lines, {manual_headings} headings, {sections} sections, {appendices} appendices, and {command_pages} accepted standalone command pages.",
        f"Its public Git blob is `{manual_oid}` and blob SHA-256 is `{manual_sha}`.",
        f"The website download is not exact: it has {site_lines:,} lines and {site_headings} headings, with SHA-256 `{_sha256_bytes(site_manual)}`.",
        "",
        "The accepted artifact also records 164 reader-linked command pages plus 19 supplemental standalone pages. The website must not collapse those scopes into the broader registry-derived command catalog.",
        "",
        "## Proposed route disposition",
        "",
        "| Action | Route | Proof label | Proposal |",
        "| --- | --- | --- | --- |",
    ]
    for row in route_rows:
        packet_lines.append(f"| {row['action']} | `{row['route']}` | `{row['proof_label']}` | {row['proposal']} |")
    packet_lines.extend(
        [
            "",
            "## Gate 7 handoff boundary",
            "",
            "Gate 7 may implement only reviewed rows from the route ledger. It must recheck the public source commit and website baseline, preserve public-source URLs and proof labels, run `npm run build` from the website repository, and produce a separate exact mutation plan before any website commit or push.",
            "",
            "This packet does not authorize site edits, artifact replacement, build, commit, push, GitHub Pages publication, or live verification.",
            "",
        ]
    )
    packet_path.write_text("\n".join(packet_lines), encoding="utf-8")

    site_after = _site_state(site_root)
    findings: list[str] = []
    if site_after != site_before:
        findings.append("WEBSITE_REPOSITORY_STATE_CHANGED")
    if command_pages != 183 or sections != 24 or appendices != 4:
        findings.append("PUBLIC_MANUAL_COUNTS_UNEXPECTED")
    if primary.get("artifact_lines") != 4118 or primary.get("artifact_heading_count") != 237:
        findings.append("PRIMARY_ARTIFACT_COUNTS_UNEXPECTED")
    if site_manual == manual:
        findings.append("EXPECTED_STALE_WEBSITE_MANUAL_NOT_STALE")
    if len(route_rows) != 11 or action_counts != {"CREATE": 2, "UPDATE": 8, "REPLACE": 1}:
        findings.append("ROUTE_DISPOSITION_COUNTS_UNEXPECTED")
    validation = {
        "schema": "dottalk.website.documentation_feed_validation.v1",
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "counts": {
            "routes": len(route_rows),
            "create": action_counts["CREATE"],
            "update": action_counts["UPDATE"],
            "replace": action_counts["REPLACE"],
            "public_command_pages": command_pages,
            "public_sections": sections,
            "public_appendices": appendices,
        },
        "website_state_before": site_before,
        "website_state_after": site_after,
        "website_state_unchanged": site_before == site_after,
    }
    _write_json(validation_path, validation)
    manifest = {
        "schema": "dottalk.website.documentation_feed_manifest.v1",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": validation["status"],
        "public_source_commit": commit,
        "website_baseline_commit": site_before["head"],
        "python": ".".join(map(str, sys.version_info[:3])),
        "artifacts": {
            path.name: {"sha256": _sha256_file(path), "bytes": path.stat().st_size}
            for path in (packet_path, payload_path, ledger_path, validation_path)
        },
        "boundaries": payload["boundaries"],
    }
    _write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a report-only Gate 6 website documentation feed packet.")
    parser.add_argument("--public-repo", type=Path, required=True)
    parser.add_argument("--public-commit", required=True)
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = build(args.public_repo, args.public_commit, args.site_root, args.output_dir)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"website_feed status=FAIL error={exc}")
        return 2
    print(
        "website_feed status={} source={} site={} routes=11 website_mutated=0".format(
            manifest["status"], manifest["public_source_commit"][:12], manifest["website_baseline_commit"][:12]
        )
    )
    return 0 if manifest["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
