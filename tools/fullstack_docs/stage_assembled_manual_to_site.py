#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage the assembled developer manual to the website at a STABLE 'latest' route.

MANUAL-ASSEMBLY lane, M5 (downloads staging). Copies the assembler's outputs
(.md/.pdf/.html) into the site's public/downloads/current/ under FIXED filenames
so the public link is a permalink: every rebuild overwrites the same files, so
`/downloads/current/developer-manual-latest.md` always points at the newest
build. Also writes DEVELOPER_MANUAL_LATEST.json (build provenance).

Honesty: the assembled manual is a CANDIDATE build regenerated from source; it is
distinct from the gated, accepted `developer_manual_publication_v1.md`. The
manifest and the site label it as such.

Usage:
    python3 tools/fullstack_docs/stage_assembled_manual_to_site.py --site-root <path-to-x64base-site>

Target Python 3.12. Writes only under <site-root>/public/downloads/current/.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
import subprocess
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSEMBLED = os.path.join(ROOT, "docs/manuals/developer/manualgen/generated/assembled")

# stable public names -> the link never changes
STABLE = {
    "developer_manual_assembled_v1.md": "developer-manual-latest.md",
    "developer_manual_v1.pdf": "developer-manual-latest.pdf",
    "developer_manual_v1.html": "developer-manual-latest.html",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def main():
    if sys.version_info[:2] != (3, 12):
        print(
            "ERROR: Python 3.12 required; observed %d.%d"
            % sys.version_info[:2],
            file=sys.stderr,
        )
        return 2
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-root", required=True, help="path to the x64base-site checkout")
    args = ap.parse_args()

    dest_dir = os.path.join(args.site_root, "public", "downloads", "current")
    if not os.path.isdir(dest_dir):
        print("ERROR: not a site downloads dir: %s" % dest_dir, file=sys.stderr)
        return 2

    report_path = os.path.join(ASSEMBLED, "assembly_report_v1.json")
    report = json.load(open(report_path, encoding="utf-8")) if os.path.exists(report_path) else {}

    source_paths = {
        src_name: os.path.join(ASSEMBLED, src_name) for src_name in STABLE
    }
    missing = [name for name, path in source_paths.items() if not os.path.isfile(path)]
    if missing:
        print(
            "ERROR: incomplete assembled format set: %s" % ", ".join(missing),
            file=sys.stderr,
        )
        return 2
    markdown_mtime = os.path.getmtime(
        source_paths["developer_manual_assembled_v1.md"]
    )
    stale = [
        name
        for name, path in source_paths.items()
        if name != "developer_manual_assembled_v1.md"
        and os.path.getmtime(path) < markdown_mtime
    ]
    if stale:
        print(
            "ERROR: assembled companion format older than Markdown: %s"
            % ", ".join(stale),
            file=sys.stderr,
        )
        return 2

    expected_md_sha = str(report.get("output_md_sha256", "")).upper()
    observed_md_sha = sha256(source_paths["developer_manual_assembled_v1.md"])
    if not expected_md_sha or observed_md_sha != expected_md_sha:
        print(
            "ERROR: assembly report does not bind the current Markdown bytes",
            file=sys.stderr,
        )
        return 2

    staged = []
    for src_name, pub_name in STABLE.items():
        src = os.path.join(ASSEMBLED, src_name)
        dst = os.path.join(dest_dir, pub_name)
        shutil.copyfile(src, dst)
        staged.append(
            {
                "file": pub_name,
                "route": "/downloads/current/%s" % pub_name,
                "bytes": os.path.getsize(dst),
                "sha256": sha256(dst),
            }
        )
        print("staged %-32s -> %s" % (src_name, pub_name))

    manifest = {
        "schema": "x64base.developer-manual-latest.v1",
        "status": "assembled-candidate",
        "proof_label": "generated-reviewed",
        "note": (
            "Latest manifest-driven ASSEMBLED build of the developer manual, "
            "regenerated from source by tools/manualgen/assemble_manual.py. This is "
            "a candidate build; the gated 'accepted' manual "
            "(developer_manual_publication_v1.md) remains the reviewed baseline."
        ),
        "generated_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_commit": report.get("commit", git_commit()),
        "source_commit_role": "repository-head-context-only",
        "source_state": "assembled-candidate-from-local-worktree",
        "source_assembly_sha256": expected_md_sha,
        "source_assembly_report_sha256": sha256(report_path),
        "format_freshness": "PASS_ALL_FORMATS_AT_OR_AFTER_MARKDOWN",
        "counts": report.get("counts", {}),
        "total_lines": report.get("total_lines"),
        "drift_gate": "tools/manualgen/check_manual_drift.py",
        "assembler": report.get("assembler"),
        "artifacts": staged,
    }
    mpath = os.path.join(dest_dir, "DEVELOPER_MANUAL_LATEST.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", os.path.relpath(mpath, args.site_root))
    print("staged %d artifact(s) at /downloads/current/ (stable 'latest' links)" % len(staged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
