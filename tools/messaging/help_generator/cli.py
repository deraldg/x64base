#!/usr/bin/env python3
"""CLI for cross-platform generated HELP maintenance helpers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .candidate_rows import CommandCandidate, build_generated_candidate_rows
    from .runtime_smoke import write_runtime_smoke
    from .schema import validate_rows_by_table
    from .status import write_json
    from .transcript_review import review_runtime_transcript
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from help_generator.candidate_rows import CommandCandidate, build_generated_candidate_rows
    from help_generator.runtime_smoke import write_runtime_smoke
    from help_generator.schema import validate_rows_by_table
    from help_generator.status import write_json
    from help_generator.transcript_review import review_runtime_transcript


def _selftest_candidates() -> list[CommandCandidate]:
    return [
        CommandCandidate("CTB_NATIVE_CREATE", "CTB.NATIVE.CREATE", "Generated source-locale HELP candidate for CTB.NATIVE.CREATE; dry-run only."),
        CommandCandidate("CTB_NATIVE_IMPORT", "CTB.NATIVE.IMPORT", "Generated source-locale HELP candidate for CTB.NATIVE.IMPORT; dry-run only."),
        CommandCandidate("CTB_NATIVE_READBACK", "CTB.NATIVE.READBACK", "Generated source-locale HELP candidate for CTB.NATIVE.READBACK; dry-run only."),
    ]


def _smoke_rows_from_candidates(rows: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    smoke: list[dict[str, object]] = []
    for row in rows["HELP_ARTIFACTS"]:
        smoke.append({"table": "HELP_ARTIFACTS", "recno": row["ID"], "topic_key": row["CMDKEY"]})
    for row in rows["HELP_LINE"]:
        smoke.append({"table": "HELP_LINE", "recno": row["LINEID"], "topic_key": row["TOPICKEY"]})
    for row in rows["HELP_SECTION"]:
        smoke.append({"table": "HELP_SECTION", "recno": row["SECTID"], "topic_key": row["TOPICKEY"]})
    for row in rows["HELP_TOPIC"]:
        smoke.append({"table": "HELP_TOPIC", "recno": row["TOPICID"], "topic_key": row["TOPICKEY"]})
    return smoke


def cmd_selftest(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    rows = build_generated_candidate_rows(_selftest_candidates(), first_topic_id=482, first_artifact_id=5485, first_line_id=8229)
    issues = validate_rows_by_table(rows)
    output = Path(args.output) if args.output else repo_root / "docs" / "messaging" / "tmp" / "generated_help_selftest.dts"
    write_runtime_smoke(output, repo_root=repo_root, smoke_rows=_smoke_rows_from_candidates(rows))
    dts = output.read_text(encoding="ascii")
    checks = {
        "schema_issues": len(issues),
        "dts_contains_setpath_dbf": int("SETPATH DBF" in dts),
        "dts_contains_setpath_indexes": int("SETPATH INDEXES" in dts),
        "dts_contains_do_cmdhelp": int("DO cmdhelp" in dts or "DO CMDHELP" in dts),
        "dts_contains_goto_placeholder": int("GOTO <n>" in dts),
        "dts_contains_real_recno_5485": int("GOTO 5485" in dts),
        "dts_contains_real_recno_8229": int("GOTO 8229" in dts),
        "rows_by_table": {k: len(v) for k, v in rows.items()},
    }
    green = int(
        checks["schema_issues"] == 0
        and checks["dts_contains_setpath_dbf"] == 1
        and checks["dts_contains_setpath_indexes"] == 1
        and checks["dts_contains_do_cmdhelp"] == 0
        and checks["dts_contains_goto_placeholder"] == 0
        and checks["dts_contains_real_recno_5485"] == 1
        and checks["dts_contains_real_recno_8229"] == 1
    )
    result = {"green": green, "checks": checks, "output": str(output)}
    if args.json_out:
        write_json(Path(args.json_out), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if green else 2


def cmd_review_transcript(args: argparse.Namespace) -> int:
    result = review_runtime_transcript(
        Path(args.transcript),
        expected_keys=args.expected_key,
        expected_recnos=[int(x) for x in args.expected_recno],
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("green") == 1 else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generated HELP maintenance CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("selftest", help="build complete candidate rows and a self-contained runtime smoke")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--output")
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_selftest)
    p = sub.add_parser("review-transcript", help="review a DotTalk++ DOTSCRIPT OUT transcript")
    p.add_argument("--transcript", required=True)
    p.add_argument("--expected-key", action="append", default=[])
    p.add_argument("--expected-recno", action="append", default=[])
    p.set_defaults(func=cmd_review_transcript)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
