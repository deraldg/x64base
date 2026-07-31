"""Review DotTalk++ runtime smoke transcripts for generated HELP candidates.

EO-B v1.1 repair: the first reviewer was too strict about blank TEXT memo display.
HELP_ARTIFACTS.TEXT may legitimately render as "" in a TUP display; that is not the
old malformed generated-candidate pattern. The old bad pattern is blank critical row
output such as repeated empty fields after failed SELECT/GOTO, placeholder `GOTO <n>`,
or missing target HELP workspace/key/recno markers.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence, Any


def _norm_path_text(text: str) -> str:
    return text.replace("/", "\\").lower()


def _has_active_help_workspace(text: str) -> int:
    lower = text.lower()
    norm = _norm_path_text(text)
    return int("workspace open: scanning directory" in lower and "data\\help" in norm)


def _count_expected_markers(text: str, markers: Sequence[str]) -> int:
    return sum(1 for marker in markers if str(marker) in text)


def _count_expected_recnos(text: str, recnos: Sequence[int]) -> int:
    hits = 0
    for recno in recnos:
        if re.search(rf"(?<!\d){int(recno)}(?!\d)", text):
            hits += 1
    return hits


def _old_blank_generated_candidate_pattern_seen(text: str) -> int:
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('"" | ""') or line.count('"" |') >= 3:
            return 1
        if "DOT|CTB_NATIVE" in line and re.search(r'^""\s*\|', line):
            return 1
    return 0


def review_runtime_transcript(transcript: Path, *, expected_keys: Sequence[str], expected_recnos: Sequence[int]) -> dict[str, Any]:
    text = transcript.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    key_hits = _count_expected_markers(text, expected_keys)
    recno_hits = _count_expected_recnos(text, expected_recnos)
    result: dict[str, Any] = {
        "runtime_started_marker_seen_optional": int("dottalk++ build" in lower or "dottalk++ beta" in lower),
        "active_help_workspace_open_marker_seen": _has_active_help_workspace(text),
        "target_keys_seen": key_hits,
        "target_keys_expected": len(expected_keys),
        "target_recnos_seen": recno_hits,
        "target_recnos_expected": len(expected_recnos),
        "msg22ae_marker_seen": int("MSG22AE" in text),
        "candidate_marker_seen": int("CANDIDATE" in text),
        "bad_goto_placeholder_seen": int("GOTO <n>" in text),
        "old_blank_generated_candidate_pattern_seen": _old_blank_generated_candidate_pattern_seen(text),
        "artifact_text_empty_allowed": 1,
    }
    result["green"] = int(
        result["active_help_workspace_open_marker_seen"] == 1
        and result["target_keys_seen"] == result["target_keys_expected"]
        and result["target_recnos_seen"] == result["target_recnos_expected"]
        and result["msg22ae_marker_seen"] == 1
        and result["candidate_marker_seen"] == 1
        and result["bad_goto_placeholder_seen"] == 0
        and result["old_blank_generated_candidate_pattern_seen"] == 0
    )
    return result
