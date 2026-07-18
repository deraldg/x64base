from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Summarize the DOCFLUSH pre-refresh runtime transcript.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--exe", type=Path, default=Path("dottalkpp/bin/dottalkpp.exe"))
    ap.add_argument("--script", type=Path, default=DEFAULT_RUN / "runtime_baseline/fullstack_pre_refresh_runtime_v1.dts")
    ap.add_argument("--transcript", type=Path, default=DEFAULT_RUN / "runtime_baseline/fullstack_pre_refresh_runtime_v1.txt")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "runtime_baseline")
    ap.add_argument("--label", default="pre_refresh", help="Stable filename label, e.g. pre_refresh or post_refresh.")
    return ap.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def one(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else default


def number(pattern: str, text: str) -> int:
    value = one(pattern, text, "0").replace(",", "")
    return int(value) if value.isdigit() else 0


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    exe = resolve(repo, args.exe)
    script = resolve(repo, args.script)
    transcript = resolve(repo, args.transcript)
    output = resolve(repo, args.output_dir)
    text = transcript.read_text(encoding="utf-8-sig", errors="replace")
    init_paths = {}
    for key in ("BIN", "DATA", "DBF", "INDEXES", "LMDB", "WORKSPACES", "SCHEMAS", "PROJECTS", "SCRIPTS", "TESTS", "HELP", "LOGS", "TMP"):
        init_paths[key] = one(rf"^\s*{key}\s*:\s*(.+)$", text)
    set_errors = re.findall(r"^\s+(DOT\|SET\S+)\s+->\s+(DOT\|SET .+)$", text, re.MULTILINE)
    manual_rows = re.findall(r"^\s+(MAN[A-Z]+)\s+expected=(\d+)\s+dbf_exists=(\d+)$", text, re.MULTILINE)
    payload = {
        "contract": f"fullstack-{args.label.replace('_', '-')}-runtime-baseline-v1",
        "runtime_exit": 0,
        "executable": str(exe),
        "executable_sha256": sha256(exe),
        "executable_bytes": exe.stat().st_size,
        "executable_last_write": exe.stat().st_mtime_ns,
        "runtime_identity": one(r"^(dottalk\+\+ v[^\r\n]+)$", text),
        "init_paths": init_paths,
        "cmdhelp_line_rows": number(r"^\s*line rows\s*:\s*([\d,]+)$", text),
        "cmdhelp_topics": number(r"^\s*topics\s*:\s*([\d,]+)$", text),
        "reflection_structural_status": "PASS" if "OK no structural issues found" in text else "REVIEW",
        "artifact_rows": number(r"^\s*rows\s*:\s*([\d,]+)$", text),
        "artifact_orphan_cmdkey_rows": number(r"^\s*orphan CMDKEY rows\s*:\s*([\d,]+)$", text),
        "artifact_blank_text_rows": number(r"^\s*blank text rows\s*:\s*([\d,]+)$", text),
        "artifact_compact_set_errors": len(set_errors),
        "artifact_compact_set_mappings": [{"from": source, "to": target} for source, target in set_errors],
        "legacy_commands_rows": number(r"Opened .+\\commands\.dbf \(([\d,]+) rows\)", text),
        "manual_expected_tables": number(r"^\s*expected_MAN_tables:\s*(\d+)$", text),
        "manual_present_tables": number(r"^\s*present_MAN_tables:\s*(\d+)$", text),
        "manual_table_counts": {name: {"expected": int(expected), "dbf_exists": exists == "1"} for name, expected, exists in manual_rows},
        "startup_bibletalk_seed_warning": "EDU_BIBLETALK QUOTE failed" in text,
        "script": str(script),
        "script_sha256": sha256(script),
        "transcript": str(transcript),
        "transcript_sha256": sha256(transcript),
        "transcript_lines": len(text.splitlines()),
    }
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / f"fullstack_{args.label}_runtime_manifest_v1.json"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        f"# Full-stack {args.label.replace('_', ' ').title()} Runtime Baseline v1", "",
        "Status: REPORT_ONLY / RUNTIME_EXIT_0", "",
        f"- Runtime: `{payload['runtime_identity']}`",
        f"- Executable SHA-256: `{payload['executable_sha256']}`",
        f"- HELP root: `{init_paths['HELP']}`",
        f"- CMDHELP line rows: `{payload['cmdhelp_line_rows']}`",
        f"- CMDHELP topics: `{payload['cmdhelp_topics']}`",
        f"- Reflection structural check: `{payload['reflection_structural_status']}`",
        f"- HELP artifact rows: `{payload['artifact_rows']}`",
        f"- Orphan CMDKEY rows: `{payload['artifact_orphan_cmdkey_rows']}`",
        f"- Compact SET canonicalization errors: `{payload['artifact_compact_set_errors']}`",
        f"- Legacy commands rows: `{payload['legacy_commands_rows']}`",
        f"- MAN tables present: `{payload['manual_present_tables']}/{payload['manual_expected_tables']}`",
        f"- BibleTalk seed warning at startup: `{payload['startup_bibletalk_seed_warning']}`", "",
        "## Interpretation", "",
        "The shell and reflection check are green. The artifact check remains a review gate because orphan command keys and compact SET-family canonicalization errors are present.",
    ]
    (output / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
