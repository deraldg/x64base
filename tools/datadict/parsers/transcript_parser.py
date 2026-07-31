#!/usr/bin/env python3
"""
DD-015 DotTalk++ transcript parser skeleton.

Report-only parser for controlled transcripts created by DD-014-style proof runs.
It does not launch DotTalk++, open DBFs, mutate repo files, or promote catalog rows.

Supported input styles:
  1. Explicit markers:
       ### DD015 CMD seq=1 phase=DD014B command="WORKSPACE USAGE"
       ... output ...
       ### DD015 END
  2. Prompt-style commands:
       . WORKSPACE USAGE
       ... output ...
       dottalk> RELATIONS ALL
       ... output ...

Output: JSON manifest with parsed command blocks, hashes, marker observations,
        and promotion-candidate rows for later human review.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PARSER_VERSION = "0.1.0-dd015-report-only"

EXPLICIT_CMD_RE = re.compile(
    r"^###\s+DD015\s+CMD\s+(?P<attrs>.*)$", re.IGNORECASE
)
EXPLICIT_END_RE = re.compile(r"^###\s+DD015\s+END\s*$", re.IGNORECASE)
PROMPT_RE = re.compile(
    r"^(?:(?P<prompt>dottalk(?:pp)?|fox|x64base)>|[.>])\s*(?P<cmd>[A-Za-z][A-Za-z0-9_]*(?:\s+.*)?)\s*$",
    re.IGNORECASE,
)

MARKER_PATTERNS = {
    "workspace_usage": re.compile(r"\bWORKSPACE\b.*\b(OPEN|CLOSE|SAVE|LOAD|TUPLES|USAGE)\b", re.IGNORECASE),
    "relations_usage": re.compile(r"\b(RELATIONS|SET\s+RELATION|SET\s+RELATIONS)\b", re.IGNORECASE),
    "tuple_usage": re.compile(r"\b(TUPLE|TUPVALIDATE)\b", re.IGNORECASE),
    "open_area": re.compile(r"\b(area|workarea)\b.*\b(open|opened|alias|dbf)\b", re.IGNORECASE),
    "relation_graph": re.compile(r"\b(parent|child|relation|relations|into|on)\b", re.IGNORECASE),
    "save_load": re.compile(r"\b(save|saved|load|loaded|restore|restored)\b", re.IGNORECASE),
    "memo_backend": re.compile(r"\b(memo|dbt|backend|attached|sidecar)\b", re.IGNORECASE),
    "error_or_warning": re.compile(r"\b(error|warning|failed|unknown|usage:)\b", re.IGNORECASE),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def normalize_command(command: str) -> str:
    s = re.sub(r"\s+", " ", command.strip())
    return s.upper()


def first_token(command: str) -> str:
    norm = normalize_command(command)
    return norm.split(" ", 1)[0] if norm else ""


def parse_attrs(attr_text: str) -> dict[str, str]:
    # Simple key=value parser. Quoted strings are supported for command="...".
    attrs: dict[str, str] = {}
    for match in re.finditer(r"(\w+)=('([^']*)'|\"([^\"]*)\"|([^\s]+))", attr_text):
        key = match.group(1).lower()
        value = match.group(3) or match.group(4) or match.group(5) or ""
        attrs[key] = value
    return attrs


@dataclass
class CommandBlock:
    seq: int
    phase_id: str
    command_text: str
    normalized_command: str
    command_token: str
    input_style: str
    start_line: int
    end_line: int
    output_line_count: int
    output_hash: str
    observed_markers: list[str]
    warning_markers: list[str]
    catalog_targets: str = ""
    expected_evidence_marker: str = ""
    status: str = "parsed_review_required"


def detect_markers(output: str) -> tuple[list[str], list[str]]:
    observed: list[str] = []
    warnings: list[str] = []
    for name, pattern in MARKER_PATTERNS.items():
        if pattern.search(output):
            if name == "error_or_warning":
                warnings.append(name)
            else:
                observed.append(name)
    return observed, warnings


def load_plan(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def match_plan(command_text: str, plan_rows: list[dict]) -> dict | None:
    norm = normalize_command(command_text)
    token = first_token(command_text)
    best: dict | None = None
    best_score = 0
    for row in plan_rows:
        cand = normalize_command(row.get("command_or_step", ""))
        if not cand:
            continue
        score = 0
        if cand == norm:
            score = 100
        elif norm.startswith(cand) or cand.startswith(norm):
            score = 80
        elif cand.split(" ", 1)[0] == token:
            score = 40
        if score > best_score:
            best_score = score
            best = row
    return best if best_score >= 40 else None


def parse_transcript(text: str, plan_rows: list[dict]) -> list[CommandBlock]:
    lines = text.splitlines()
    blocks: list[CommandBlock] = []
    current_cmd: str | None = None
    current_style = ""
    current_phase = ""
    current_start = 0
    current_output: list[str] = []
    seq_override: int | None = None

    def flush(end_line: int) -> None:
        nonlocal current_cmd, current_style, current_phase, current_start, current_output, seq_override
        if current_cmd is None:
            return
        output = "\n".join(current_output).rstrip("\n")
        observed, warning = detect_markers(output)
        seq = seq_override if seq_override is not None else len(blocks) + 1
        plan = match_plan(current_cmd, plan_rows)
        blocks.append(CommandBlock(
            seq=seq,
            phase_id=current_phase or (plan.get("phase_id", "") if plan else ""),
            command_text=current_cmd,
            normalized_command=normalize_command(current_cmd),
            command_token=first_token(current_cmd),
            input_style=current_style,
            start_line=current_start,
            end_line=end_line,
            output_line_count=len([ln for ln in current_output if ln.strip()]),
            output_hash=sha256_text(output),
            observed_markers=observed,
            warning_markers=warning,
            catalog_targets=plan.get("catalog_targets", "") if plan else "",
            expected_evidence_marker=plan.get("expected_evidence_marker", "") if plan else "",
        ))
        current_cmd = None
        current_style = ""
        current_phase = ""
        current_start = 0
        current_output = []
        seq_override = None

    for idx, line in enumerate(lines, start=1):
        m = EXPLICIT_CMD_RE.match(line)
        if m:
            flush(idx - 1)
            attrs = parse_attrs(m.group("attrs"))
            current_cmd = attrs.get("command", "")
            current_phase = attrs.get("phase", "")
            try:
                seq_override = int(attrs.get("seq", "")) if attrs.get("seq") else None
            except ValueError:
                seq_override = None
            current_style = "explicit_marker"
            current_start = idx
            current_output = []
            continue
        if EXPLICIT_END_RE.match(line):
            flush(idx)
            continue
        p = PROMPT_RE.match(line)
        if p and not current_style == "explicit_marker":
            flush(idx - 1)
            current_cmd = p.group("cmd").strip()
            current_phase = ""
            current_style = "prompt"
            current_start = idx
            current_output = []
            continue
        if current_cmd is not None:
            current_output.append(line)
    flush(len(lines))
    return blocks


def build_manifest(input_path: Path, plan_path: Path | None = None) -> dict:
    data = input_path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    plan_rows = load_plan(plan_path)
    blocks = parse_transcript(text, plan_rows)
    diagnostics = []
    if not blocks:
        diagnostics.append({
            "severity": "warning",
            "code": "NO_COMMAND_BLOCKS_PARSED",
            "message": "No explicit DD015 markers or prompt-style command lines were found.",
        })
    for block in blocks:
        if not block.catalog_targets:
            diagnostics.append({
                "severity": "review",
                "code": "NO_DD014_PLAN_MATCH",
                "seq": block.seq,
                "command": block.command_text,
                "message": "Parsed command did not match DD014 command plan strongly enough.",
            })
        if block.warning_markers:
            diagnostics.append({
                "severity": "review",
                "code": "WARNING_MARKER_OBSERVED",
                "seq": block.seq,
                "command": block.command_text,
                "markers": block.warning_markers,
            })
    return {
        "manifest_kind": "dottalkpp_transcript_parse_manifest",
        "schema_version": "0.1.0-dd015",
        "parser_version": PARSER_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(input_path),
            "sha256": sha256_bytes(data),
            "byte_count": len(data),
            "line_count": len(text.splitlines()),
        },
        "plan": {
            "path": str(plan_path) if plan_path else "",
            "rows_loaded": len(plan_rows),
        },
        "boundary": {
            "runtime_launched": False,
            "repo_mutated": False,
            "catalog_mutated": False,
            "evidence_status": "parsed_transcript_only_review_required",
        },
        "commands": [asdict(b) for b in blocks],
        "summary": {
            "command_blocks": len(blocks),
            "blocks_with_plan_match": sum(1 for b in blocks if b.catalog_targets),
            "blocks_with_warning_marker": sum(1 for b in blocks if b.warning_markers),
            "unique_command_tokens": sorted(set(b.command_token for b in blocks if b.command_token)),
        },
        "diagnostics": diagnostics,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-015 report-only DotTalk++ transcript parser skeleton")
    ap.add_argument("transcript", type=Path, help="Transcript text file to parse")
    ap.add_argument("--plan", type=Path, default=None, help="Optional DD014 command plan CSV")
    ap.add_argument("--out", type=Path, default=Path("dd015_transcript_manifest.json"), help="Output manifest JSON")
    args = ap.parse_args()
    manifest = build_manifest(args.transcript, args.plan)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DD015: wrote {args.out}")
    print(f"DD015: command_blocks={manifest['summary']['command_blocks']} plan_matches={manifest['summary']['blocks_with_plan_match']} warnings={manifest['summary']['blocks_with_warning_marker']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
