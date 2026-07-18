from __future__ import annotations

import html
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from . import __version__
from .runlog import utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json


COMMAND_LINK_RE = re.compile(
    r"(?<!!)\[([^\]]+)\]\(([^)]*command_reference_v1/commands/([^)/#]+\.md)(?:#[^)]*)?)\)"
)
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
CATALOG_PRIORITY = {name: index for index, name in enumerate(("DOT", "FOX", "ED", "EDU", "EXT", "UI", "DEV", "INTERNAL", "SYSTEM"))}
KIND_ORDER = ("STATUS", "SUMMARY", "SYNTAX", "USAGE", "ARGUMENT", "EXAMPLE", "NOTE", "WARNING", "ERROR", "HINT", "ALIAS", "RELATED", "DEPRECATION", "MESSAGE")
CONFIDENCE_PRIORITY = {"CURATED": 0, "AUTHORITATIVE": 1, "CATALOG": 2, "REFLECTED": 3, "INFERRED": 4}


def _normal_identity(value: str) -> str:
    return re.sub(r"[\s_]+", " ", value.strip().upper())


def _extract_command_links(text: str) -> list[dict[str, str | int]]:
    grouped: dict[str, dict[str, str | int]] = {}
    for match in COMMAND_LINK_RE.finditer(text):
        label = html.unescape(match.group(1).strip())
        destination = unquote(match.group(2).strip()).replace("\\", "/")
        file_name = match.group(3)
        slug = Path(file_name).stem.lower()
        row = grouped.setdefault(
            slug,
            {
                "slug": slug,
                "label": label,
                "current_destination": destination,
                "occurrences": 0,
            },
        )
        row["occurrences"] = int(row["occurrences"]) + 1
        if row["label"] != label or row["current_destination"] != destination:
            raise ValueError(f"conflicting link identity for slug {slug}")
    return [grouped[key] for key in sorted(grouped)]


def _resolve_topic(label: str, slug: str, topics: list[dict[str, str]]) -> tuple[dict[str, str] | None, str, int]:
    identities = {_normal_identity(label), _normal_identity(slug)}
    matches = [row for row in topics if _normal_identity(row.get("TOPIC", "")) in identities]
    if not matches:
        return None, "UNRESOLVED", 0
    matches.sort(key=lambda row: (CATALOG_PRIORITY.get(row.get("CATALOG", "").upper(), 99), row.get("TOPICKEY", "")))
    best_rank = CATALOG_PRIORITY.get(matches[0].get("CATALOG", "").upper(), 99)
    best = [row for row in matches if CATALOG_PRIORITY.get(row.get("CATALOG", "").upper(), 99) == best_rank]
    if len(best) != 1:
        return None, "AMBIGUOUS_SAME_PRIORITY", len(matches)
    rule = "EXACT_LABEL_OR_SLUG_PREFERRED_CATALOG"
    return best[0], rule, len(matches)


def _line_inclusion(row: dict[str, str]) -> tuple[bool, str]:
    if row.get("KIND", "").upper() == "SOURCE_FACT":
        return False, "EXCLUDE_SOURCE_FACT_FROM_PUBLIC_BODY"
    if LOCAL_PATH_RE.search(row.get("TEXT", "")):
        return False, "EXCLUDE_LOCAL_PATH_FROM_PUBLIC_BODY"
    if not row.get("TEXT", "").strip():
        return False, "EXCLUDE_BLANK_TEXT"
    text = row.get("TEXT", "").strip()
    if row.get("SOURCE", "").upper() == "USAGE_CONTRACT" and row.get("NAME", "").upper() == "USAGE_CONTRACT":
        if text.lower().endswith(" usage contract") or re.match(r"^(?:category|status)=", text, re.IGNORECASE):
            return False, "EXCLUDE_CONTRACT_ENVELOPE_FROM_PUBLIC_BODY"
    if row.get("KIND", "").upper() == "RELATED" and re.match(r"^include\s+<[^>]+>$", text, re.IGNORECASE):
        return False, "EXCLUDE_SOURCE_INCLUDE_FROM_PUBLIC_BODY"
    return True, "INCLUDE_PUBLIC_HELP_EVIDENCE"


def _deduplicate_lines(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    ordered = sorted(
        rows,
        key=lambda row: (
            KIND_ORDER.index(row.get("KIND", "").upper()) if row.get("KIND", "").upper() in KIND_ORDER else 99,
            CONFIDENCE_PRIORITY.get(row.get("CONFID", "").upper(), 99),
            int(row.get("LINEID", "0").strip() or 0),
        ),
    )
    selected: list[dict[str, str]] = []
    disposition: dict[str, str] = {}
    seen: set[tuple[str, str]] = set()
    for row in ordered:
        line_id = row.get("LINEID", "").strip()
        include, reason = _line_inclusion(row)
        if not include:
            disposition[line_id] = reason
            continue
        key = (row.get("KIND", "").upper(), re.sub(r"\s+", " ", row.get("TEXT", "").strip()).casefold())
        if key in seen:
            disposition[line_id] = "EXCLUDE_DUPLICATE_PUBLIC_TEXT"
            continue
        seen.add(key)
        selected.append(row)
        disposition[line_id] = reason
    return selected, disposition


def _render_page(topic: dict[str, str], label: str, selected: list[dict[str, str]], reference_run: str, disposition_run: str) -> str:
    status = topic.get("STATUS", "unverified").strip() or "unverified"
    supported = topic.get("SUPPORTED", "").strip() or "unknown"
    implemented = topic.get("IMPLEMENT", "").strip() or "unknown"
    attention = status.lower() not in {"supported", "current"} or supported.upper() not in {"T", "TRUE", "YES", "1"}
    lines = [
        "<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->",
        f"# {label}",
        "",
    ]
    if attention:
        lines.extend([f"> Status notice: **{status.upper()}**; supported=`{supported}`. Treat this page as limited or review-required evidence.", ""])
    lines.extend(
        [
            f"- Catalog/topic: `{topic.get('CATALOG', '')}` / `{topic.get('TOPIC', '')}`",
            f"- Status: `{status}`",
            f"- Implemented/supported: `{implemented}` / `{supported}`",
            f"- Primary/confidence: `{topic.get('PRIMARY', '')}` / `{topic.get('CONFID', '')}`",
            "",
        ]
    )
    by_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        by_kind[row.get("KIND", "").upper()].append(row)
    summary = topic.get("SUMMARY", "").strip()
    summary_rows = by_kind.pop("SUMMARY", [])
    distinct_summaries: list[str] = []
    summary_seen: set[str] = set()
    for value in [summary, *(row.get("TEXT", "").strip() for row in summary_rows)]:
        normalized = re.sub(r"\s+", " ", value).casefold()
        if value and normalized not in summary_seen:
            summary_seen.add(normalized)
            distinct_summaries.append(value)
    if distinct_summaries:
        lines.extend(["## Summary", ""])
        for index, value in enumerate(distinct_summaries):
            escaped = "<br>".join(html.escape(part, quote=False) for part in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
            if index == 0:
                lines.append(escaped)
            else:
                if index == 1:
                    lines.append("")
                lines.append(f"- {escaped}")
        lines.append("")
    ordered_kinds = [kind for kind in KIND_ORDER if kind in by_kind]
    ordered_kinds.extend(sorted(set(by_kind) - set(ordered_kinds)))
    for kind in ordered_kinds:
        rows = by_kind[kind]
        if not rows:
            continue
        lines.extend([f"## {kind.replace('_', ' ').title()}", ""])
        for row in rows:
            text = row.get("TEXT", "").strip().replace("\r\n", "\n").replace("\r", "\n")
            text = "<br>".join(html.escape(part, quote=False) for part in text.split("\n"))
            lines.append(f"- {text}")
        lines.append("")
    lines.extend(
        [
            "## Provenance",
            "",
            f"- Topic key: `{topic.get('TOPICKEY', '')}`",
            f"- Included HELP rows: `{len(selected)}`",
            f"- HELP reference run: `{reference_run}`",
            f"- Disposition run: `{disposition_run}`",
            "- Authority: `candidate_only`; `publication_authority_claimed=0`",
            "",
        ]
    )
    return "\n".join(lines)


def _shift_markdown_headings(text: str, levels: int = 1) -> str:
    def replace(match: re.Match[str]) -> str:
        return "#" * min(6, len(match.group(1)) + levels) + match.group(2)

    return re.sub(r"^(#{1,6})(\s+)", replace, text, flags=re.MULTILINE)


def _load_bound_manifest(path: Path, schema: str, run_id: str) -> dict:
    if not path.is_file():
        raise ValueError(f"missing bound manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema") != schema or payload.get("run_id") != run_id:
        raise ValueError(f"manifest identity mismatch: {path}")
    if payload.get("candidate_only") != 1 or payload.get("publication_authority_claimed") != 0:
        raise ValueError(f"manifest boundary mismatch: {path}")
    return payload


def build_command_reference_candidate(paths, reference_run: str, disposition_run: str, logger=None):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("build-command-reference-candidate requires Python 3.12.x")
    manualgen = paths.manualgen_root
    reference_dir = manualgen / "generated" / "manualgen_reference_candidates" / reference_run
    disposition_dir = manualgen / "generated" / "manualgen_disposition_candidates" / disposition_run
    reference_manifest_path = reference_dir / "help_topic_reference_manifest.json"
    disposition_manifest_path = disposition_dir / "manual_disposition_manifest.json"
    reference = _load_bound_manifest(reference_manifest_path, "dottalk.manualgen.help_topic_reference_candidate.v1", reference_run)
    disposition = _load_bound_manifest(disposition_manifest_path, "dottalk.manualgen.review_disposition_candidate.v1", disposition_run)
    if reference.get("transform_status") != "PASS" or disposition.get("status") != "PASS":
        raise ValueError("source transform is not PASS")

    input_findings: list[str] = []
    for key in ("markdown", "lineage", "command_resolution"):
        artifact = paths.repo_root / reference["artifacts"][key]
        if not artifact.is_file() or sha256_file(artifact) != reference["artifacts"][key + "_sha256"]:
            input_findings.append(f"REFERENCE_ARTIFACT_HASH:{key}")
    for key in ("approved_topics", "disposition_ledger"):
        artifact = paths.repo_root / disposition["artifacts"][key]
        if not artifact.is_file() or sha256_file(artifact) != disposition["artifacts"][key + "_sha256"]:
            input_findings.append(f"DISPOSITION_ARTIFACT_HASH:{key}")
    harvest_files = {row["file_name"]: row for row in reference["harvest"]["files"]}
    for name in ("HELP_HELP_TOPIC.csv", "HELP_HELP_LINE.csv"):
        row = harvest_files.get(name)
        if not row:
            input_findings.append(f"MISSING_HARVEST_BINDING:{name}")
            continue
        artifact = paths.repo_root / row["relative_path_posix"]
        if not artifact.is_file() or sha256_file(artifact) != row["sha256"]:
            input_findings.append(f"HARVEST_HASH:{name}")
    if input_findings:
        raise ValueError(";".join(input_findings))

    pointer = manualgen / "accepted_artifacts" / "ACTIVE_PRIMARY_READER_ARTIFACT.txt"
    reader_record_path = manualgen / "accepted_artifacts" / "primary_reader_artifact_v1.json"
    reader_record = json.loads(reader_record_path.read_text(encoding="utf-8-sig"))
    reader_path = paths.repo_root / pointer.read_text(encoding="utf-8-sig").strip()
    reader_before_hash = sha256_file(reader_path)
    if reader_before_hash != str(reader_record.get("artifact_sha256", "")).upper():
        raise ValueError("accepted reader hash does not match its record")
    links = _extract_command_links(reader_path.read_text(encoding="utf-8-sig"))

    topics = read_csv(paths.repo_root / harvest_files["HELP_HELP_TOPIC.csv"]["relative_path_posix"])
    help_lines = read_csv(paths.repo_root / harvest_files["HELP_HELP_LINE.csv"]["relative_path_posix"])
    approved = {row.get("topic_key", ""): row for row in read_csv(paths.repo_root / disposition["artifacts"]["approved_topics"])}
    review_dispositions = {row.get("topic_key", ""): row for row in read_csv(paths.repo_root / disposition["artifacts"]["disposition_ledger"])}
    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in help_lines:
        lines_by_topic[row.get("TOPICKEY", "")].append(row)

    output_dir = manualgen / "generated" / "manualgen_command_reference_candidates" / logger.run_id
    commands_dir = output_dir / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    ledger_rows: list[dict[str, object]] = []
    lineage_rows: list[dict[str, object]] = []
    rewrite_rows: list[dict[str, object]] = []
    findings: list[str] = []
    attention_pages = 0
    for link in links:
        slug, label = str(link["slug"]), str(link["label"])
        topic, rule, match_count = _resolve_topic(label, slug, topics)
        if topic is None:
            findings.append(f"{rule}:{slug}")
            continue
        topic_key = topic.get("TOPICKEY", "")
        if topic_key not in approved:
            findings.append(f"NOT_APPROVED_BY_DISPOSITION:{slug}:{topic_key}")
            continue
        selected, line_dispositions = _deduplicate_lines(lines_by_topic.get(topic_key, []))
        page_path = commands_dir / f"{slug}.md"
        page_path.write_text(_render_page(topic, label, selected, reference_run, disposition_run), encoding="utf-8")
        local_path_hits = len(LOCAL_PATH_RE.findall(page_path.read_text(encoding="utf-8")))
        if local_path_hits:
            findings.append(f"LOCAL_PATH_LEAK:{slug}:{local_path_hits}")
        status = topic.get("STATUS", "").lower()
        supported = topic.get("SUPPORTED", "").upper()
        attention = status not in {"supported", "current"} or supported not in {"T", "TRUE", "YES", "1"}
        attention_pages += int(attention)
        review_row = review_dispositions.get(topic_key, {})
        ledger_rows.append(
            {
                "slug": slug,
                "label": label,
                "topic_key": topic_key,
                "catalog": topic.get("CATALOG", ""),
                "topic": topic.get("TOPIC", ""),
                "resolution_rule": rule,
                "identity_match_count": match_count,
                "status": topic.get("STATUS", ""),
                "implemented": topic.get("IMPLEMENT", ""),
                "supported": topic.get("SUPPORTED", ""),
                "attention_label": int(attention),
                "disposition": review_row.get("disposition", approved[topic_key].get("disposition", "")),
                "source_help_rows": len(lines_by_topic.get(topic_key, [])),
                "included_help_rows": len(selected),
                "excluded_help_rows": len(lines_by_topic.get(topic_key, [])) - len(selected),
                "candidate_path": relpath_posix(page_path, paths.repo_root),
                "candidate_sha256": sha256_file(page_path),
                "local_path_hits": local_path_hits,
                "occurrences": link["occurrences"],
            }
        )
        for row in lines_by_topic.get(topic_key, []):
            line_id = row.get("LINEID", "").strip()
            disposition_text = line_dispositions.get(line_id, "EXCLUDE_UNCLASSIFIED")
            lineage_rows.append(
                {
                    "slug": slug,
                    "topic_key": topic_key,
                    "line_id": line_id,
                    "kind": row.get("KIND", ""),
                    "source": row.get("SOURCE", ""),
                    "confidence": row.get("CONFID", ""),
                    "name": row.get("NAME", ""),
                    "included": int(disposition_text == "INCLUDE_PUBLIC_HELP_EVIDENCE"),
                    "disposition": disposition_text,
                    "text_sha256": hashlib.sha256(row.get("TEXT", "").encode("utf-8")).hexdigest().upper(),
                }
            )
        rewrite_rows.append(
            {
                "slug": slug,
                "label": label,
                "current_section_destination": link["current_destination"],
                "required_section_destination": f"../../command_reference_v1/commands/{slug}.md",
                "required_reader_destination": f"command_reference_v1/commands/{slug}.md",
                "section_projection": f"docs/manuals/developer/manualgen/published/developer_manual_publication_v1/command_reference_v1/commands/{slug}.md",
                "reader_current_context": "BROKEN_FROM_COMBINED_READER",
                "acceptance_action": "PROJECT_PAGE_AND_REWRITE_COMBINED_READER_LINK_ONLY",
            }
        )

    expected_pages = len(links)
    if expected_pages != 164:
        findings.append(f"EXPECTED_164_LINKS:{expected_pages}")
    if len(ledger_rows) != expected_pages:
        findings.append(f"PAGE_COVERAGE:{len(ledger_rows)}/{expected_pages}")
    if len(list(commands_dir.glob("*.md"))) != len(ledger_rows):
        findings.append("PAGE_FILE_COUNT_MISMATCH")
    reader_after_hash = sha256_file(reader_path)
    if reader_after_hash != reader_before_hash:
        findings.append("ACCEPTED_READER_MUTATED")

    ledger_path = output_dir / "command_reference_candidate_ledger.csv"
    lineage_path = output_dir / "command_reference_lineage.csv"
    rewrite_path = output_dir / "link_context_rewrite_ledger.csv"
    review_path = output_dir / "COMMAND_REFERENCE_CANDIDATE_REVIEW.md"
    index_path = output_dir / "COMMAND_REFERENCE_CANDIDATE_INDEX.md"
    combined_path = output_dir / "COMMAND_REFERENCE_CANDIDATE_COMBINED.md"
    manifest_path = output_dir / "command_reference_candidate_manifest.json"
    write_csv(ledger_path, ledger_rows)
    write_csv(lineage_path, lineage_rows)
    write_csv(rewrite_path, rewrite_rows)
    status = "PASS_CANDIDATE_ONLY" if not findings else "FAIL_CANDIDATE"
    index_lines = [
        "<!-- CANDIDATE ONLY: human review index; no publication authority. -->",
        "# Command Reference Candidate Index",
        "",
        f"This index exposes all **{len(ledger_rows)}** generated pages for human review.",
        "",
        "- [Open the single combined review book](COMMAND_REFERENCE_CANDIDATE_COMBINED.md)",
        "- [Open the candidate package summary](COMMAND_REFERENCE_CANDIDATE_REVIEW.md)",
        "",
        "| # | Command page | Topic | Status | Evidence rows |",
        "| ---: | --- | --- | --- | ---: |",
    ]
    for number, row in enumerate(ledger_rows, 1):
        notice = " ⚠" if int(row["attention_label"]) else ""
        index_lines.append(
            f"| {number} | [{row['label']}](commands/{row['slug']}.md){notice} | `{row['topic_key']}` | `{row['status']}` | {row['included_help_rows']} |"
        )
    index_lines.extend(["", "⚠ indicates a partial, pending, or unsupported source status.", ""])
    index_path.write_text("\n".join(index_lines), encoding="utf-8")

    combined_lines = [
        "<!-- CANDIDATE ONLY: combined human review book; no publication authority. -->",
        "# Command Reference Candidate — Combined Review Book",
        "",
        f"This report-only book contains all **{len(ledger_rows)}** candidate command pages in alphabetical order.",
        "",
        "[Open the page index](COMMAND_REFERENCE_CANDIDATE_INDEX.md)",
        "",
    ]
    for row in ledger_rows:
        page_path = paths.repo_root / str(row["candidate_path"])
        combined_lines.extend(["---", "", _shift_markdown_headings(page_path.read_text(encoding="utf-8").rstrip()), ""])
    combined_path.write_text("\n".join(combined_lines).rstrip() + "\n", encoding="utf-8")

    review_lines = [
        "# Command Reference Candidate Review",
        "",
        f"- Status: `{status}`",
        f"- Pages: `{len(ledger_rows)}/{expected_pages}`",
        f"- Attention-labelled pages: `{attention_pages}`",
        f"- Accepted reader before/after: `{reader_before_hash}` / `{reader_after_hash}`",
        f"- Reference run: `{reference_run}`",
        f"- Disposition run: `{disposition_run}`",
        "- Publication authority: `0`",
        "",
        "## Human review products",
        "",
        "- [Index of all 164 command pages](COMMAND_REFERENCE_CANDIDATE_INDEX.md)",
        "- [Single combined command-reference review book](COMMAND_REFERENCE_CANDIDATE_COMBINED.md)",
        "",
        "The section-source links remain valid after projecting the candidate pages into the publication workspace. The combined reader uses those section links in a different directory context, so acceptance must rewrite only the combined-reader destinations to `command_reference_v1/commands/<slug>.md`.",
        "",
        "## Findings",
        "",
    ]
    review_lines.extend([f"- `{finding}`" for finding in findings] or ["- None."])
    review_lines.extend(["", "This package is report-only. It does not mutate the accepted reader, its pointer, source staging, or website.", ""])
    review_path.write_text("\n".join(review_lines), encoding="utf-8")
    manifest = {
        "schema": "dottalk.manualgen.command_reference_candidate.v1",
        "created_utc": utc_now_iso(),
        "run_id": logger.run_id,
        "manualgen_version": __version__,
        "status": status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "accepted_reader_mutated": int(reader_after_hash != reader_before_hash),
        "website_mutated": 0,
        "source_staging_mutated": 0,
        "bindings": {
            "accepted_reader": relpath_posix(reader_path, paths.repo_root),
            "accepted_reader_sha256": reader_before_hash,
            "reader_record": relpath_posix(reader_record_path, paths.repo_root),
            "reader_record_sha256": sha256_file(reader_record_path),
            "reference_run": reference_run,
            "reference_manifest": relpath_posix(reference_manifest_path, paths.repo_root),
            "reference_manifest_sha256": sha256_file(reference_manifest_path),
            "disposition_run": disposition_run,
            "disposition_manifest": relpath_posix(disposition_manifest_path, paths.repo_root),
            "disposition_manifest_sha256": sha256_file(disposition_manifest_path),
            "help_topic_sha256": harvest_files["HELP_HELP_TOPIC.csv"]["sha256"],
            "help_line_sha256": harvest_files["HELP_HELP_LINE.csv"]["sha256"],
        },
        "counts": {
            "reader_link_destinations": expected_pages,
            "candidate_pages": len(ledger_rows),
            "lineage_rows": len(lineage_rows),
            "attention_labelled_pages": attention_pages,
            "findings": len(findings),
            "local_path_hits": sum(int(row["local_path_hits"]) for row in ledger_rows),
            "index_page_links": len(ledger_rows),
            "combined_book_pages": len(ledger_rows),
        },
        "findings": findings,
        "artifacts": {
            "ledger": relpath_posix(ledger_path, paths.repo_root),
            "ledger_sha256": sha256_file(ledger_path),
            "lineage": relpath_posix(lineage_path, paths.repo_root),
            "lineage_sha256": sha256_file(lineage_path),
            "link_context_rewrite_ledger": relpath_posix(rewrite_path, paths.repo_root),
            "link_context_rewrite_ledger_sha256": sha256_file(rewrite_path),
            "review": relpath_posix(review_path, paths.repo_root),
            "review_sha256": sha256_file(review_path),
            "index": relpath_posix(index_path, paths.repo_root),
            "index_sha256": sha256_file(index_path),
            "combined": relpath_posix(combined_path, paths.repo_root),
            "combined_sha256": sha256_file(combined_path),
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("command_reference_candidate_manifest", manifest_path, "Hash-bound report-only command-reference package.")
        logger.artifact("command_reference_candidate_ledger", ledger_path, "One row per requested reader link and generated page.")
        logger.artifact("command_reference_lineage", lineage_path, "Included and excluded HELP row audit trail.")
        logger.artifact("link_context_rewrite_ledger", rewrite_path, "Section and combined-reader link-context proof.")
        logger.artifact("command_reference_candidate_review", review_path, "Human review entrypoint.")
        logger.artifact("command_reference_candidate_index", index_path, "Human index linking every candidate page.")
        logger.artifact("command_reference_candidate_combined", combined_path, "Single-file combined human review book.")
        logger.boundary("accepted_reader_mutated", int(reader_after_hash != reader_before_hash), "PASS" if reader_after_hash == reader_before_hash else "FAIL", "Report-only generator must preserve accepted reader bytes.")
        logger.boundary("publication_authority_claimed", 0, "PASS", "Candidate package has no publication authority.")
        logger.boundary("website_mutated", 0, "PASS", "No website write path exists in this command.")
    state = {"status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "manifest": relpath_posix(manifest_path, paths.repo_root)}
    return state, manifest["counts"]
