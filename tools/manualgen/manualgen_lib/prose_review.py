from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from . import __version__
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json


RUNTIME_SLUG = "runtime_evidence_source_verification_and_canary_closure"
COMMAND_SLUG = "command_surface_dispatch_and_entry_variants"
PARTIAL_HELP_SLUG = "partial_help_reference"

PROSE_REVIEW_POLICY: dict[str, dict[str, str]] = {
    "DOT|REGRESSION": {
        "target_slug": RUNTIME_SLUG,
        "review_disposition": "ADDITIVE_PROSE",
        "anchor_after": "## Smoke tests, shakedowns, regressions, builds, and releases",
        "candidate_action": "ADD_PROOF_LAUNCHER_SUBSECTION",
        "rationale": "Document the curated launcher and its DOTSCRIPT delegation without treating launcher availability as proof of a passing run.",
    },
    "DOT|TEST": {
        "target_slug": RUNTIME_SLUG,
        "review_disposition": "ADDITIVE_PROSE",
        "anchor_after": "## Smoke tests, shakedowns, regressions, builds, and releases",
        "candidate_action": "ADD_PROOF_LAUNCHER_SUBSECTION",
        "rationale": "Document the script harness, logfile behavior, and delegated side effects without classifying it as read-only.",
    },
    "DOT|GENERIC": {
        "target_slug": COMMAND_SLUG,
        "review_disposition": "CANARY_CROSS_REFERENCE",
        "anchor_after": "## Command surface",
        "candidate_action": "ADD_DEVELOPER_UTILITY_CANARY_NOTE",
        "rationale": "Keep the supported placeholder visible as a developer-utility canary instead of polishing it into a normal public command.",
    },
    "UI|ARCTICTALK": {
        "target_slug": COMMAND_SLUG,
        "review_disposition": "ADDITIVE_PROSE",
        "anchor_after": "## Aliases and entry variants",
        "candidate_action": "ADD_CONDITIONAL_UI_ENTRY_NOTE",
        "rationale": "Describe the Turbo Vision application entry point and FOXTALK alias with a build-availability caveat.",
    },
    "UI|FOXPRO": {
        "target_slug": COMMAND_SLUG,
        "review_disposition": "ADDITIVE_PROSE",
        "anchor_after": "## Aliases and entry variants",
        "candidate_action": "ADD_CONDITIONAL_UI_ENTRY_NOTE",
        "rationale": "Describe the FoxPro-style Turbo Vision workbench entry point without implying availability in every build.",
    },
    "DOT|CANARY": {
        "target_slug": PARTIAL_HELP_SLUG,
        "review_disposition": "APPENDIX_ONLY",
        "anchor_after": "NEW CANDIDATE APPENDIX",
        "candidate_action": "ADD_UNSUPPORTED_REGISTERED_TOPIC_ENTRY",
        "rationale": "Keep registration visible while curated DOTREF support and behavior prose remain pending.",
    },
    "FOX|DO": {
        "target_slug": PARTIAL_HELP_SLUG,
        "review_disposition": "APPENDIX_ONLY",
        "anchor_after": "NEW CANDIDATE APPENDIX",
        "candidate_action": "ADD_LEGACY_SYNTAX_REDIRECT_ENTRY",
        "rationale": "Preserve the legacy syntax as compatibility reference and redirect readers to DOTSCRIPT without implying implementation.",
    },
    "FOX|RUN": {
        "target_slug": PARTIAL_HELP_SLUG,
        "review_disposition": "APPENDIX_ONLY",
        "anchor_after": "NEW CANDIDATE APPENDIX",
        "candidate_action": "ADD_LEGACY_SYNTAX_REFERENCE_ENTRY",
        "rationale": "Preserve the legacy syntax as compatibility reference without claiming current runtime support or equivalence to another launcher.",
    },
}


def _latest_section_delta_dir(paths: ManualgenPaths) -> Path | None:
    root = paths.manualgen_root / "generated" / "manualgen_section_delta_candidates"
    candidates: list[Path] = []
    for directory in root.glob("MANRUN-*") if root.exists() else []:
        manifest_path = directory / "manual_section_delta_candidate_manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        counts = manifest.get("counts", {})
        if (
            manifest.get("status") == "PASS"
            and counts.get("approved_topics") == 462
            and counts.get("used_topic_blocks") == 462
            and counts.get("target_packets") == 22
        ):
            candidates.append(directory)
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _topic_keys(path: Path) -> list[str]:
    pattern = re.compile(r"^- Key/status: `([^`]+)`", re.MULTILINE)
    return pattern.findall(path.read_text(encoding="utf-8", errors="replace"))


def _primary_section(paths: ManualgenPaths, slug: str) -> Path:
    return (
        paths.manualgen_root
        / "published"
        / "developer_manual_publication_v1"
        / "sections"
        / "sections"
        / f"{slug}.md"
    )


def _render_runtime_candidate(source_packet: str, source_sha256: str) -> str:
    return f"""<!-- Candidate-only prose review fragment. Not publication. -->
# Runtime Evidence — Prose Delta Candidate

- Target: `{RUNTIME_SLUG}`
- Suggested anchor after: `## Smoke tests, shakedowns, regressions, builds, and releases`
- Source packet: `{source_packet}`
- Source packet SHA-256: `{source_sha256}`
- Topics: `DOT|REGRESSION`, `DOT|TEST`
- Replacement authorized: 0
- Publication authority claimed: 0

## REGRESSION and TEST as proof launchers

`REGRESSION` and `TEST` make repeatable proof entry points discoverable, but
neither command makes a run self-proving. Retain the exact command, selected
script or suite, build identity, transcript, and result counts when using either
launcher as evidence.

### REGRESSION

`REGRESSION [USAGE|LIST|SHOW <name>|RUN <name>|<name>|ALL]` selects from a
curated set of stable regression and shakedown scripts. `LIST` and `SHOW` expose
the curated entries; `RUN <name>` and the compact `<name>` form launch one
entry; `ALL` launches the defined ordered set. The command delegates execution
to `DOTSCRIPT`, so it is a catalogued launcher rather than a separate test
engine. Developer reproduction canaries that are not in the curated set remain
outside `ALL`.

### TEST

`TEST <scriptfile> [<logfile>] [VERBOSE]` runs a specified test script through
the shell test harness. The harness resolves the script path, handles supported
inline comments and continued logical commands, executes those commands, and
reports processed and error counts. A supplied logfile may be created or
truncated. The script controls the resulting side effects, so `TEST` must not be
classified as read-only merely because it is used for verification.

### Evidence boundary

Launcher availability proves only that the entry surface exists. A proof claim
still requires the retained run inputs and outcome. Cross-reference the
Scripting and Control Flow section for script semantics and Runtime Operation,
Invocation, and Automation for entry-path behavior.
"""


def _render_command_candidate(source_packet: str, source_sha256: str) -> str:
    return f"""<!-- Candidate-only prose review fragment. Not publication. -->
# Command Surface — Prose Delta Candidate

- Target: `{COMMAND_SLUG}`
- Source packet: `{source_packet}`
- Source packet SHA-256: `{source_sha256}`
- Topics: `DOT|GENERIC`, `UI|ARCTICTALK`, `UI|FOXPRO`
- Replacement authorized: 0
- Publication authority claimed: 0

## Candidate insertion A

- Suggested anchor after: `## Command surface`

### GENERIC remains a developer-utility canary

`GENERIC` is present in the supported DOTREF surface as a developer utility
placeholder. Keep it visible for dispatch and metadata reconciliation, but do
not present it as a normal user workflow until runtime behavior and intended
audience are separately established. Its current value is as a command-surface
canary: registration, HELP identity, handler ownership, and runtime availability
can be compared without inventing stronger behavior prose.

## Candidate insertion B

- Suggested anchor after: `## Aliases and entry variants`

### Application-style UI entry points

`ARCTICTALK` and `FOXPRO` are application launch entries rather than ordinary
data commands. When Turbo Vision support is present, `ARCTICTALK` opens the
ArcticTalk shell and `FOXPRO` opens the FoxPro-style workbench. `FOXTALK` is the
legacy alias for `ARCTICTALK`.

These names may be registered or documented even when a particular build does
not contain the corresponding Turbo Vision surface. Describe availability from
the selected build and runtime evidence; do not infer universal availability
from registration alone. Neither entry currently exposes a separate usage
branch, so the bare command form is the documented launch surface.
"""


def _render_partial_help_candidate(source_packet: str, source_sha256: str) -> str:
    return f"""<!-- Candidate-only appendix prose. Not publication. -->
# Partial HELP Reference — Prose Appendix Candidate

- Target: `{PARTIAL_HELP_SLUG}`
- Target kind: `new_candidate_appendix`
- Source packet: `{source_packet}`
- Source packet SHA-256: `{source_sha256}`
- Topics: `DOT|CANARY`, `FOX|DO`, `FOX|RUN`
- Replacement authorized: 0
- Publication authority claimed: 0

## Reading this appendix

This appendix preserves command identities whose collected HELP evidence is
partial. An entry here is not a support promise. `registered` means a name is
visible in a command surface; `legacy syntax` preserves a compatibility form;
`unsupported` means the current evidence does not authorize behavior prose or
runtime availability claims.

## CANARY

Status: registered; unsupported pending curated DOTREF review.

`CANARY` is a registered DotTalk++ command, but its curated support status and
help summary are pending. Keep the identity visible for audit and reconciliation
without documenting an inferred behavior. Move it to a normal command section
only after the support contract and runtime evidence agree.

## FOX DO

Status: legacy compatibility syntax; not currently implemented or supported.

Legacy form: `DO <program> [WITH <args>]`.

Retain this form only to help readers interpret older FoxPro-style material.
Use `DOTSCRIPT` for current script execution. The redirect does not claim that
`DOTSCRIPT` reproduces every historical `DO` semantic.

## FOX RUN

Status: legacy compatibility syntax; not currently implemented or supported.

Legacy forms: `RUN /N <command>` and `RUN <file>`.

Retain these forms only as compatibility reference. Do not infer current
runtime support, background-process semantics, or equivalence to another shell
launcher until separately established by contract and runtime proof.

## Promotion boundary

Partial entries remain segregated from supported command prose. Promotion out
of this appendix requires an explicit support decision, source/HELP identity
agreement, and appropriate runtime evidence.
"""


def render_prose_candidates(packet_info: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        f"{RUNTIME_SLUG}_PROSE_DELTA_CANDIDATE.md": _render_runtime_candidate(
            packet_info[RUNTIME_SLUG]["relative_path"], packet_info[RUNTIME_SLUG]["sha256"]
        ),
        f"{COMMAND_SLUG}_PROSE_DELTA_CANDIDATE.md": _render_command_candidate(
            packet_info[COMMAND_SLUG]["relative_path"], packet_info[COMMAND_SLUG]["sha256"]
        ),
        f"{PARTIAL_HELP_SLUG}_PROSE_APPENDIX_CANDIDATE.md": _render_partial_help_candidate(
            packet_info[PARTIAL_HELP_SLUG]["relative_path"], packet_info[PARTIAL_HELP_SLUG]["sha256"]
        ),
    }


def build_prose_review_batch(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    section_delta_dir = _latest_section_delta_dir(paths)
    empty_counts = {
        "policy_topics": len(PROSE_REVIEW_POLICY),
        "input_topics": 0,
        "candidate_files": 0,
        "missing_topics": len(PROSE_REVIEW_POLICY),
        "duplicate_topics": 0,
        "invalid_packet_hashes": 0,
        "missing_anchors": 0,
    }
    if not section_delta_dir:
        return {"created": 0, "status": "FAIL"}, empty_counts

    source_manifest_path = section_delta_dir / "manual_section_delta_candidate_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    manifest_packets = {
        row["target_slug"]: row for row in source_manifest.get("artifacts", {}).get("packets", [])
    }
    selected_slugs = (RUNTIME_SLUG, COMMAND_SLUG, PARTIAL_HELP_SLUG)
    packet_info: dict[str, dict[str, Any]] = {}
    all_input_keys: list[str] = []
    invalid_packet_hashes = 0
    for slug in selected_slugs:
        row = manifest_packets.get(slug, {})
        relative_path = row.get("relative_path", "")
        packet_path = paths.repo_root / relative_path if relative_path else Path()
        actual_sha = sha256_file(packet_path) if relative_path and packet_path.exists() else ""
        if not actual_sha or actual_sha != row.get("sha256", ""):
            invalid_packet_hashes += 1
        keys = _topic_keys(packet_path) if relative_path and packet_path.exists() else []
        all_input_keys.extend(keys)
        packet_info[slug] = {
            "relative_path": relative_path,
            "sha256": actual_sha,
            "topic_count": len(keys),
        }

    key_counts = Counter(all_input_keys)
    policy_keys = set(PROSE_REVIEW_POLICY)
    input_keys = set(all_input_keys)
    missing_topics = sorted(policy_keys - input_keys)
    unexpected_topics = sorted(input_keys - policy_keys)
    duplicate_topics = sorted(key for key, count in key_counts.items() if count != 1)

    canonical_targets: dict[str, dict[str, str]] = {}
    missing_anchors: list[str] = []
    for slug in (RUNTIME_SLUG, COMMAND_SLUG):
        target = _primary_section(paths, slug)
        text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
        anchors = sorted(
            {
                row["anchor_after"]
                for row in PROSE_REVIEW_POLICY.values()
                if row["target_slug"] == slug
            }
        )
        for anchor in anchors:
            if text.count(anchor) != 1:
                missing_anchors.append(f"{slug}:{anchor}")
        canonical_targets[slug] = {
            "relative_path": relpath_posix(target, paths.repo_root),
            "sha256": sha256_file(target) if target.exists() else "",
        }

    run_id = logger.run_id if logger else "MANRUN-PROSE-REVIEW-BATCH"
    output_dir = paths.manualgen_root / "generated" / "manualgen_prose_review_batches" / run_id
    fragment_dir = output_dir / "candidates"
    fragment_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows = []
    rendered = render_prose_candidates(packet_info)
    for filename, body in rendered.items():
        path = fragment_dir / filename
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        candidate_rows.append(
            {
                "candidate_file": filename,
                "relative_path": relpath_posix(path, paths.repo_root),
                "sha256": sha256_file(path),
            }
        )

    ledger_rows = []
    for topic_key, policy in PROSE_REVIEW_POLICY.items():
        source = packet_info[policy["target_slug"]]
        ledger_rows.append(
            {
                "topic_key": topic_key,
                "target_slug": policy["target_slug"],
                "review_disposition": policy["review_disposition"],
                "anchor_after": policy["anchor_after"],
                "candidate_action": policy["candidate_action"],
                "rationale": policy["rationale"],
                "source_packet": source["relative_path"],
                "source_packet_sha256": source["sha256"],
            }
        )
    ledger_path = output_dir / "manual_prose_review_ledger.csv"
    write_csv(ledger_path, ledger_rows)

    status = "PASS" if (
        len(PROSE_REVIEW_POLICY) == 8
        and len(all_input_keys) == 8
        and not missing_topics
        and not unexpected_topics
        and not duplicate_topics
        and invalid_packet_hashes == 0
        and not missing_anchors
        and len(candidate_rows) == 3
    ) else "FAIL"
    disposition_counts = Counter(row["review_disposition"] for row in ledger_rows)
    manifest_path = output_dir / "manual_prose_review_batch_manifest.json"
    manifest = {
        "schema": "dottalk.manualgen.prose_review_batch.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "status": status,
        "review_order": "risk_ordered_smallest_packets_first",
        "candidate_only": 1,
        "canonical_manual_mutated": 0,
        "accepted_appendix_mutated": 0,
        "reader_pointer_mutated": 0,
        "publication_authority_claimed": 0,
        "input": {
            "section_delta_run_id": section_delta_dir.name,
            "section_delta_manifest": relpath_posix(source_manifest_path, paths.repo_root),
            "section_delta_manifest_sha256": sha256_file(source_manifest_path),
            "packets": packet_info,
            "canonical_targets": canonical_targets,
        },
        "counts": {
            "policy_topics": len(PROSE_REVIEW_POLICY),
            "input_topics": len(all_input_keys),
            "candidate_files": len(candidate_rows),
            "additive_prose_topics": disposition_counts.get("ADDITIVE_PROSE", 0),
            "canary_cross_reference_topics": disposition_counts.get("CANARY_CROSS_REFERENCE", 0),
            "appendix_only_topics": disposition_counts.get("APPENDIX_ONLY", 0),
            "missing_topics": len(missing_topics),
            "unexpected_topics": len(unexpected_topics),
            "duplicate_topics": len(duplicate_topics),
            "invalid_packet_hashes": invalid_packet_hashes,
            "missing_anchors": len(missing_anchors),
        },
        "findings": {
            "missing_topics": missing_topics,
            "unexpected_topics": unexpected_topics,
            "duplicate_topics": duplicate_topics,
            "missing_anchors": missing_anchors,
        },
        "artifacts": {
            "review_ledger": relpath_posix(ledger_path, paths.repo_root),
            "review_ledger_sha256": sha256_file(ledger_path),
            "candidate_files": candidate_rows,
        },
    }
    write_json(manifest_path, manifest)

    if logger:
        logger.artifact("manual_prose_review_ledger", ledger_path, "Topic-level human prose review dispositions and anchors.")
        logger.artifact("manual_prose_review_batch_manifest", manifest_path, "Hash-bound smallest-packet prose review manifest.")
        for row in candidate_rows:
            logger.artifact(row["candidate_file"], paths.repo_root / row["relative_path"], "Candidate-only anchored prose fragment.")
        for boundary in (
            "canonical_manual_mutated",
            "accepted_appendix_mutated",
            "reader_pointer_mutated",
            "publication_authority_claimed",
            "source_help_metadata_mutated",
        ):
            logger.boundary(boundary, 0, "PASS", "Prose review batch generation does not cross this boundary.")

    state = {
        "created": 1,
        "status": status,
        "output_dir": relpath_posix(output_dir, paths.repo_root),
        "manifest": relpath_posix(manifest_path, paths.repo_root),
    }
    return state, manifest["counts"]
