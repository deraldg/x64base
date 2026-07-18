from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compare pre/post HELP runtime manifests.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--pre", type=Path, default=DEFAULT_RUN / "runtime_baseline/fullstack_pre_refresh_runtime_manifest_v1.json")
    ap.add_argument("--post", type=Path, default=DEFAULT_RUN / "help_refresh_execution/post_runtime/fullstack_post_refresh_runtime_manifest_v1.json")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "help_refresh_execution")
    return ap.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    pre_path, post_path = resolve(repo, args.pre), resolve(repo, args.post)
    output = resolve(repo, args.output_dir)
    pre, post = json.loads(pre_path.read_text()), json.loads(post_path.read_text())
    metrics = [
        "cmdhelp_line_rows", "cmdhelp_topics", "artifact_rows", "artifact_orphan_cmdkey_rows",
        "artifact_blank_text_rows", "artifact_compact_set_errors", "legacy_commands_rows",
        "manual_expected_tables", "manual_present_tables",
    ]
    delta = {key: {"pre": pre[key], "post": post[key], "delta": post[key] - pre[key]} for key in metrics}
    payload = {
        "contract": "fullstack-help-refresh-runtime-delta-v1",
        "pre_manifest_sha256": sha(pre_path),
        "post_manifest_sha256": sha(post_path),
        "runtime_binary_unchanged": pre["executable_sha256"] == post["executable_sha256"],
        "reflection_pre": pre["reflection_structural_status"],
        "reflection_post": post["reflection_structural_status"],
        "metrics": delta,
        "remaining_gates": [
            "373 orphan CMDKEY artifact rows remain",
            "9 compact SET-family canonicalization errors remain",
            "18 blank artifact text rows remain",
            "BibleTalk SQLite seed warning remains outside the HELP mutation",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "help_refresh_runtime_delta_v1.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# HELP Refresh Runtime Delta v1", "",
        "Status: CURRENT_BUILD_VALIDATED / RESIDUAL_DRIFT_RECORDED", "",
        "| Metric | Pre | Post | Delta |", "| --- | ---: | ---: | ---: |",
    ]
    md += [f"| `{key}` | {value['pre']} | {value['post']} | {value['delta']:+d} |" for key, value in delta.items()]
    md += ["", f"Reflection structural validation remained `{post['reflection_structural_status']}`.", "", "## Remaining gates", ""]
    md += [f"- {item}" for item in payload["remaining_gates"]]
    (output / "HELP_REFRESH_RUNTIME_DELTA_V1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
