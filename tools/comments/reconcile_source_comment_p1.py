from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Reconcile P1 source-comment drift with Git and closeout evidence.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--queue", type=Path, default=DEFAULT_RUN / "comments_audit/source_comment_escrow_review_queue_v1.csv")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "comments_audit/p1_reconciliation")
    ap.add_argument("--since", default="2026-05-18T00:00:00")
    return ap.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return cp.stdout.decode("utf-8", errors="replace")


def worktree_map(repo: Path) -> dict[str, str]:
    raw = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    result: dict[str, str] = {}
    parts = raw.split("\0")
    i = 0
    while i < len(parts):
        item = parts[i]
        i += 1
        if not item:
            continue
        code, path = item[:2], item[3:]
        if code[0] in "RC" or code[1] in "RC":
            if i < len(parts):
                original = parts[i]
                i += 1
                normalized_path = path.replace("\\", "/")
                result[original.replace("\\", "/")] = f"{code}:renamed-to:{normalized_path}"
        result[path.replace("\\", "/")] = code
    return result


def history_map(repo: Path, since: str) -> dict[str, list[dict[str, str]]]:
    raw = git(
        repo,
        "log",
        f"--since={since}",
        "--date=iso-strict",
        "--format=%x1e%H%x1f%ad%x1f%s",
        "--name-only",
        "--",
        "src",
        "include",
        "bindings",
        "CMakeLists.txt",
        "CMakePresets.json",
    )
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        lines = record.splitlines()
        meta = lines[0].split("\x1f", 2)
        if len(meta) != 3:
            continue
        commit, date, subject = meta
        for line in lines[1:]:
            path = line.strip().replace("\\", "/")
            if path:
                result[path].append({"commit": commit, "date": date, "subject": subject})
    return result


def closeout_files(repo: Path) -> list[Path]:
    candidates = list((repo / "docs/maintenance").glob("SESSION_CLOSEOUT_*.md"))
    candidates += list((repo / "docs/agents").glob("HANDOFF_*.md"))
    labtalk = repo / "labtalk"
    if labtalk.exists():
        candidates += [
            p for p in labtalk.rglob("*.md")
            if "closeout" in p.name.lower() or "handoff" in p.name.lower()
        ]
    return sorted(set(candidates))


def closeout_mentions(repo: Path, paths: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    docs: list[tuple[str, str]] = []
    for doc in closeout_files(repo):
        try:
            text = doc.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        docs.append((doc.relative_to(repo).as_posix(), text))
    for path in paths:
        basename = Path(path).name
        for rel, text in docs:
            if path in text or basename in text:
                result[path].append(rel)
                if len(result[path]) == 5:
                    break
    return result


def disposition(status: str, wt: str, commits: list[dict[str, str]]) -> str:
    if wt:
        return "ACTIVE_WORKTREE_REVIEW"
    if status == "MISSING_CURRENT" and commits:
        return "GIT_HISTORY_PRESENT_MISSING_REVIEW"
    if status == "NEW_CURRENT" and commits:
        return "NEW_TRACKED_SINCE_BASELINE"
    if commits:
        return "GIT_HISTORY_PRESENT"
    return "UNEXPLAINED_REVIEW_REQUIRED"


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    queue = args.queue if args.queue.is_absolute() else repo / args.queue
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    with queue.open("r", encoding="utf-8-sig", newline="") as fh:
        p1 = [row for row in csv.DictReader(fh) if row["priority"] == "P1"]
    paths = [row["path"] for row in p1]
    wt = worktree_map(repo)
    history = history_map(repo, args.since)
    mentions = closeout_mentions(repo, paths)

    rows: list[dict[str, str]] = []
    for row in p1:
        path = row["path"]
        commits = history.get(path, [])
        latest = commits[0] if commits else {}
        rows.append({
            "priority": "P1",
            "path": path,
            "drift_status": row["status"],
            "worktree_status": wt.get(path, ""),
            "commits_since_cutoff": str(len(commits)),
            "latest_commit": latest.get("commit", ""),
            "latest_commit_date": latest.get("date", ""),
            "latest_commit_subject": latest.get("subject", ""),
            "closeout_mentions": " | ".join(mentions.get(path, [])),
            "evidence_disposition": disposition(row["status"], wt.get(path, ""), commits),
            "authorization_conclusion": "NOT_INFERRED",
        })

    fields = list(rows[0]) if rows else []
    csv_path = output / "source_comment_p1_reconciliation_v1.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["evidence_disposition"] for row in rows)
    payload = {
        "contract": "source-comment-p1-reconciliation-v1",
        "cutoff": args.since,
        "queue_sha256": sha256(queue),
        "row_count": len(rows),
        "disposition_counts": dict(sorted(counts.items())),
        "authorization_policy": "Evidence labels do not establish authorization or documentary intent.",
        "rows": rows,
    }
    json_path = output / "source_comment_p1_reconciliation_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = [
        "# Source Comment P1 Reconciliation v1",
        "",
        f"- Cutoff: `{args.since}`",
        f"- P1 rows: `{len(rows)}`",
        f"- Queue SHA-256: `{payload['queue_sha256']}`",
        "- Authorization: `NOT_INFERRED` for every row.",
        "",
        "## Evidence dispositions",
        "",
    ]
    md += [f"- `{key}`: {value}" for key, value in sorted(counts.items())]
    md += [
        "",
        "Git history and closeout mentions explain where a change may have entered the repository; they do not prove that a source comment or contract mutation was reviewed or authorized.",
    ]
    (output / "source_comment_p1_reconciliation_v1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "dispositions": dict(sorted(counts.items())), "csv_sha256": sha256(csv_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
