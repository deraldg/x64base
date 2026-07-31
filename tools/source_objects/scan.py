from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.source_objects.parser import parse_source_file
    from tools.source_objects.history import git_history
else:
    from .parser import parse_source_file
    from .history import git_history


DEFAULT_EXTENSIONS = ".c,.cc,.cpp,.cxx,.h,.hpp,.hxx,.inl,.ipp"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Turn source files into dottalk.source-object/v1 JSON and report location contracts."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--roots", nargs="+", default=["src", "include", "bindings"])
    parser.add_argument("--extensions", default=DEFAULT_EXTENSIONS)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strict-location", action="store_true")
    parser.add_argument(
        "--no-git-history",
        action="store_true",
        help="Do not enrich author and date fields from committed Git history.",
    )
    return parser.parse_args()


def discover(repo: Path, roots: list[str], extensions: set[str]) -> list[Path]:
    found: set[Path] = set()
    for root_name in roots:
        candidate = (repo / root_name).resolve()
        if candidate.is_file() and candidate.suffix.lower() in extensions:
            found.add(candidate)
            continue
        if not candidate.is_dir():
            continue
        for path in candidate.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            lowered = {part.lower() for part in path.parts}
            if lowered.intersection({".git", ".vs", "packages", "_stage", "__pycache__"}):
                continue
            if any(part.lower().startswith("build") for part in path.parts):
                continue
            found.add(path.resolve())
    return sorted(found, key=lambda item: item.relative_to(repo).as_posix().lower())


def scan(repo: Path, roots: list[str], extensions: set[str], use_git: bool = True) -> list:
    objects = []
    for path in discover(repo, roots, extensions):
        relpath = path.relative_to(repo).as_posix()
        history = git_history(repo, relpath) if use_git else {}
        objects.append(parse_source_file(path, repo, history=history))
    return objects


def write_reports(objects: list, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    objects_path = output / "source_objects.jsonl"
    with objects_path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in objects:
            handle.write(json.dumps(item.to_dict(), sort_keys=True) + "\n")

    location_path = output / "location_contract_report.csv"
    fields = [
        "SOURCE_ID", "PATH", "PROJECT", "ROLE", "DECLARED_HOME", "ACTUAL_HOME",
        "CANONICAL_PATH", "LOCATION_STATUS", "AUTHOR", "CREATED",
        "LAST_MODIFIED_BY", "LAST_MODIFIED", "WORKING_TREE_STATE",
        "USAGE_CONTRACTS", "FINDINGS",
    ]
    with location_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in objects:
            writer.writerow({
                "SOURCE_ID": item.source_id,
                "PATH": item.path,
                "PROJECT": item.project or "",
                "ROLE": item.role or "",
                "DECLARED_HOME": item.declared_home or "",
                "ACTUAL_HOME": item.actual_home,
                "CANONICAL_PATH": item.canonical_path or "",
                "LOCATION_STATUS": item.location_status,
                "AUTHOR": item.author or "",
                "CREATED": item.date or "",
                "LAST_MODIFIED_BY": item.last_modified_by or "",
                "LAST_MODIFIED": item.last_modified_date or "",
                "WORKING_TREE_STATE": item.working_tree_state,
                "USAGE_CONTRACTS": len(item.usage_contracts),
                "FINDINGS": ";".join(item.findings),
            })

    ledger_path = output / "source_location_ledger.jsonl"
    prior: dict[str, dict] = {}
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            prior[event.get("source_id", "")] = event
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_events = []
    for item in objects:
        previous = prior.get(item.source_id)
        state = (item.path, item.declared_home, item.location_status)
        previous_state = None if previous is None else (
            previous.get("path"), previous.get("declared_home"), previous.get("location_status")
        )
        if state == previous_state:
            continue
        new_events.append({
            "schema": "dottalk.source-location-event/v1",
            "observed_at": observed_at,
            "source_id": item.source_id,
            "identity_status": item.identity_status,
            "path": item.path,
            "previous_path": previous.get("path") if previous else None,
            "declared_home": item.declared_home,
            "actual_home": item.actual_home,
            "location_status": item.location_status,
        })
    if new_events:
        with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            for event in new_events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    statuses = Counter(item.location_status for item in objects)
    summary = {
        "schema": "dottalk.source-object-scan/v1",
        "files_scanned": len(objects),
        "usage_contracts": sum(len(item.usage_contracts) for item in objects),
        "location_status": dict(sorted(statuses.items())),
        "source_objects": str(objects_path),
        "location_report": str(location_path),
        "location_ledger": str(ledger_path),
        "location_events_appended": len(new_events),
    }
    (output / "scan_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    args = _args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    extensions = {value.strip().lower() for value in args.extensions.split(",") if value.strip()}
    objects = scan(repo, args.roots, extensions, use_git=not args.no_git_history)
    summary = write_reports(objects, output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    failures = sum(
        1 for item in objects if item.location_status in {"UNDECLARED", "INCOMPLETE", "MISMATCH"}
    )
    return 2 if args.strict_location and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
