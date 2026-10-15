#!/usr/bin/env python3
"""Build the immutable authority manifest consumed by SYSREF M3B.

The command accepts only explicit role-to-file bindings. It hashes exact bytes,
binds all harvested roles to one DOCFLUSH run, records the source revision, and
refuses overwrite or paths outside the repository. It does not harvest, infer a
"latest" file, or mutate any catalog.
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


SCHEMA = "dottalk.sysref.harvest_manifest.v1"
REQUIRED_ROLES = {"SYSCMD", "SYSARGS", "SRCUSAGE", "REFVOICE"}
OPTIONAL_ROLES = {"SYSSUBCMD", "SYSFUNC", "REFALIASES"}
ALLOWED_ROLES = REQUIRED_ROLES | OPTIONAL_ROLES
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ManifestError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def within(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ManifestError(f"{label}_OUTSIDE_REPO:{resolved}") from exc
    return resolved


def parse_bindings(root: Path, values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ManifestError(f"INPUT_BINDING_INVALID:{value}")
        role, raw_path = value.split("=", 1)
        role = role.strip().upper()
        if role not in ALLOWED_ROLES:
            raise ManifestError(f"INPUT_ROLE_UNKNOWN:{role}")
        if role in result:
            raise ManifestError(f"INPUT_ROLE_DUPLICATE:{role}")
        path = Path(raw_path.strip())
        path = within(root, path if path.is_absolute() else root / path, f"INPUT_{role}")
        if not path.is_file():
            raise ManifestError(f"INPUT_MISSING:{role}:{path}")
        result[role] = path
    missing = sorted(REQUIRED_ROLES - set(result))
    if missing:
        raise ManifestError(f"INPUT_ROLES_MISSING:{','.join(missing)}")
    return result


def repo_sha(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip().upper()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ManifestError(f"REPO_SHA_UNAVAILABLE:{exc}") from exc


def build_manifest(
    root: Path,
    harvest_run_id: str,
    created_utc: str,
    created_by: str,
    collector_id: str,
    collector_paths: list[Path],
    inputs: dict[str, Path],
) -> dict[str, Any]:
    if not harvest_run_id.strip():
        raise ManifestError("HARVEST_RUN_ID_EMPTY")
    if not created_by.strip():
        raise ManifestError("CREATED_BY_EMPTY")
    if not collector_id.strip():
        raise ManifestError("COLLECTOR_ID_EMPTY")
    if not UTC_RE.fullmatch(created_utc):
        raise ManifestError(f"CREATED_UTC_INVALID:{created_utc}")
    if not collector_paths:
        raise ManifestError("COLLECTOR_PATHS_EMPTY")

    members = []
    for path in collector_paths:
        path = within(root, path if path.is_absolute() else root / path, "COLLECTOR")
        if not path.is_file():
            raise ManifestError(f"COLLECTOR_MISSING:{path}")
        members.append({"path": path.relative_to(root).as_posix(), "sha256": sha256(path)})
    members.sort(key=lambda row: row["path"])
    collector = {
        "id": collector_id.strip(),
        "sha256": canonical_hash(members),
        "members": members,
    }
    input_rows = []
    for role in sorted(inputs):
        path = inputs[role]
        input_rows.append({
            "role": role,
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256(path),
            "producer_run_id": "CANONICAL" if role == "REFVOICE" else harvest_run_id,
        })
    return {
        "schema": SCHEMA,
        "harvest_run_id": harvest_run_id,
        "repo_sha": repo_sha(root),
        "created_utc": created_utc,
        "created_by": created_by,
        "collector": collector,
        "inputs": input_rows,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hash explicit SYSREF authority inputs into one immutable M3B manifest.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--harvest-run-id", required=True)
    parser.add_argument("--created-utc", required=True, help="RFC 3339 UTC at whole-second precision, ending in Z")
    parser.add_argument("--created-by", required=True)
    parser.add_argument("--collector-id", required=True)
    parser.add_argument("--collector-path", action="append", type=Path, default=[], required=True)
    parser.add_argument("--input", action="append", default=[], required=True, help="ROLE=repo-relative-path")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    try:
        out = within(root, args.out if args.out.is_absolute() else root / args.out, "OUTPUT")
        if out.exists():
            raise ManifestError(f"OUTPUT_ALREADY_EXISTS:{out}")
        inputs = parse_bindings(root, args.input)
        payload = build_manifest(
            root=root,
            harvest_run_id=args.harvest_run_id,
            created_utc=args.created_utc,
            created_by=args.created_by,
            collector_id=args.collector_id,
            collector_paths=args.collector_path,
            inputs=inputs,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    except (ManifestError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"SYSREF manifest: {out}")
    print(f"inputs={len(payload['inputs'])} collector_members={len(payload['collector']['members'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
