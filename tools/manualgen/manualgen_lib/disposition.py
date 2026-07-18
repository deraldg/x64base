from __future__ import annotations

from collections import defaultdict
from typing import Any

from . import __version__
from .curation import classify_topic
from .inventory import collect_inventory
from .paths import ManualgenPaths
from .reference_candidate import KIND_ORDER, _int_value, _read_harvest, _render_text
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json
from .validation import summarize_validation, validate_inventory


def _d(disposition: str, targets: str = "", rationale: str = "") -> dict[str, str]:
    return {"disposition": disposition, "targets": targets, "rationale": rationale}


REVIEW_DISPOSITIONS = {
    "DOT|CANARY": _d("INCLUDE_PARTIAL_HELP_REFERENCE", rationale="Physical HELP command exists; retain partial status and do not claim SYSCMD runtime authority."),
    "DOT|HELP RESOLVER": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Source-mined phrase, not a registered command identity."),
    "DOT|REPLACE MULTI": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|MULTIREP", "Internal handler phrase resolves to the public MULTIREP command."),
    "DOT|SAMPLE": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Source-mined generic sample marker without command authority."),
    "DOT|WAMREPORT": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="No HELP command or active public SYSCMD identity."),
    "DOT|FOX PALETTE COMMAND": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Source-mined UI phrase without command authority."),
    "DOT|PALETTE": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Source-mined UI phrase without command authority."),
    "DOT|POLLING": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "MINER:SOURCE": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Collector-owned source marker, not a command topic."),
    "DOT|APPEND BLANK": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|APPEND_BLANK", "Spaced source-mined phrase resolves to the supported underscored command topic."),
    "DOT|CATALOGCANARY": _d("ROUTE_DEVELOPER_DIAGNOSTIC_APPENDIX", rationale="Authoritative diagnostic usage contract without public command identity."),
    "DOT|CC PRINT": _d("ROUTE_SOURCE_FACT_APPENDIX", rationale="Source-mined phrase without command authority."),
    "DOT|CODAYSL": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|CODASYL", "Source-mined transposition resolves to the supported CODASYL topic."),
    "DOT|FOXREF": _d("ROUTE_DEVELOPER_DIAGNOSTIC_APPENDIX", rationale="Documentation-provider usage contract, not a public runtime command."),
    "DOT|ASCEND/DESCEND": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|ASCEND;DOT|DESCEND", "Family usage contract resolves to two supported command topics."),
    "DOT|RPG": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|TRIGGER": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|TTESTAPP": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|VALIDATE UNIQUE": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|VMWARE": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|VT200": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "DOT|CMDREL": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists; retain usage-contract catalog lineage."),
    "FOX|BROWSE": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Physical HELP command and active public SYSCMD identity exist; retain partial HELP status."),
    "FOX|APPEND BLANK": _d("MERGE_ALIAS_TO_CANONICAL", "FOX|APPEND_BLANK", "Spaced FOX phrase resolves to the supported underscored topic."),
    "FOX|DO": _d("INCLUDE_PARTIAL_HELP_REFERENCE", rationale="Physical FOX HELP command exists; retain partial status without runtime claim."),
    "FOX|RUN": _d("INCLUDE_PARTIAL_HELP_REFERENCE", rationale="Physical FOX HELP command exists; retain partial status without runtime claim."),
    "EDU|ASCII": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|BIBLETALK": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|BOOLEAN": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|NONE": _d("DEFER_NO_RUNTIME_IDENTITY", rationale="Usage contract exists but no HELP command or active public SYSCMD identity."),
    "EDU|CASE": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|CHRISTMAS": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|COBOL": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|EDIT": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|ERP / EDU_ERP": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|ERP", "Education handler phrase resolves to the supported ERP command topic."),
    "EDU|EVALUATE": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|FORMULA": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|HANUKKAH": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|IDX": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|TEXT/EDIT/COBOL SHIM ALIASES": _d("MERGE_ALIAS_TO_CANONICAL", "EDU|TEXT;EDU|EDIT;EDU|COBOL", "Shim-family contract resolves to three individually governed topics."),
    "EDU|NORMALIZE": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|SIX": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EDU|TEXT": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EXT|STUDENTECHO": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "EXT|STUDENTHELLO": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "UI|FOXPRO": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "UI|ARCTICTALK": _d("INCLUDE_WITH_RUNTIME_EVIDENCE", rationale="Active public SYSCMD identity exists."),
    "UI|GENERIC": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|GENERIC;FOX|GENERIC", "UI contract resolves to existing supported command topics."),
    "UI|BROWSETV": _d("MERGE_ALIAS_TO_CANONICAL", "DOT|BROWSETV;FOX|BROWSETV", "UI contract resolves to existing supported command topics."),
}


SECTION_GROUPS = {
    "01_developer_command_reference": "Developer Command Reference",
    "02_fox_compatibility_reference": "FOX Compatibility Reference",
    "03_education_concepts": "Education Concepts",
    "04_runtime_supplement": "Runtime-Evidenced Supplemental Topics",
    "05_partial_help_reference": "Partial HELP Reference",
}


def _section_group(topic: dict[str, str], disposition: str) -> str:
    if disposition == "INCLUDE_PARTIAL_HELP_REFERENCE":
        return "05_partial_help_reference"
    if topic.get("CATALOG") == "DOT":
        return "01_developer_command_reference"
    if topic.get("CATALOG") == "FOX":
        return "02_fox_compatibility_reference"
    if topic.get("CATALOG") == "ED":
        return "03_education_concepts"
    return "04_runtime_supplement"


def build_disposition_candidate(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    inv = collect_inventory(paths)
    validation = summarize_validation(validate_inventory(paths, inv))
    if validation["validation_fail_rows"]:
        return {"created": 0}, {**validation, "boundary_fail_rows": 0}
    topics = _read_harvest(paths, inv, "HELP_HELP_TOPIC.csv")
    lines = _read_harvest(paths, inv, "HELP_HELP_LINE.csv")
    commands = _read_harvest(paths, inv, "HELP_COMMANDS.csv")
    syscmd = _read_harvest(paths, inv, "META_SYSCMD.csv")
    topics.sort(key=lambda row: (_int_value(row, "TOPICID"), row.get("TOPICKEY", "")))
    topic_by_key = {row.get("TOPICKEY", ""): row for row in topics}
    command_keys = {row.get("CMDKEY", "") for row in commands}
    syscmd_by_name = {row.get("CAN_NAME", "").strip().upper(): row for row in syscmd}
    review_topics = {row.get("TOPICKEY", ""): row for row in topics if classify_topic(row)[0] in {"02_dot_command_review", "04_fox_command_review", "06_supplemental_public_candidates"}}

    missing_policy = sorted(set(review_topics) - set(REVIEW_DISPOSITIONS))
    extra_policy = sorted(set(REVIEW_DISPOSITIONS) - set(review_topics))
    disposition_rows: list[dict[str, Any]] = []
    invalid_targets = 0
    invalid_runtime_includes = 0
    invalid_help_includes = 0
    for key, topic in review_topics.items():
        policy = REVIEW_DISPOSITIONS.get(key, _d("UNRESOLVED_POLICY"))
        meta = syscmd_by_name.get(topic.get("TOPIC", "").strip().upper())
        targets = [target for target in policy["targets"].split(";") if target]
        missing_targets = [target for target in targets if target not in topic_by_key]
        invalid_targets += len(missing_targets)
        if policy["disposition"] == "INCLUDE_WITH_RUNTIME_EVIDENCE" and not (meta and meta.get("VIS") == "public" and meta.get("ACTIVE", "").lower() == "t"):
            invalid_runtime_includes += 1
        if policy["disposition"] == "INCLUDE_PARTIAL_HELP_REFERENCE" and key not in command_keys:
            invalid_help_includes += 1
        disposition_rows.append({
            "topic_id": topic.get("TOPICID", ""),
            "topic_key": key,
            "catalog": topic.get("CATALOG", ""),
            "topic": topic.get("TOPIC", ""),
            "status": topic.get("STATUS", ""),
            "primary": topic.get("PRIMARY", ""),
            "confidence": topic.get("CONFID", ""),
            "help_command_exact": 1 if key in command_keys else 0,
            "syscmd_public_active": 1 if meta and meta.get("VIS") == "public" and meta.get("ACTIVE", "").lower() == "t" else 0,
            "syscmd_handler": meta.get("HANDLER", "") if meta else "",
            "disposition": policy["disposition"],
            "canonical_targets": policy["targets"],
            "rationale": policy["rationale"],
            "target_validation": "PASS" if not missing_targets else "FAIL:" + ";".join(missing_targets),
        })

    include_dispositions = {"INCLUDE_WITH_RUNTIME_EVIDENCE", "INCLUDE_PARTIAL_HELP_REFERENCE"}
    approved: dict[str, dict[str, Any]] = {}
    for topic in topics:
        shelf, _ = classify_topic(topic)
        if shelf in {"01_dot_supported_commands", "03_fox_supported_commands", "05_education_concepts"}:
            approved[topic["TOPICKEY"]] = {"topic": topic, "basis": "SUPPORTED_BASE_SHELF", "disposition": "INCLUDE_BASE_CANDIDATE"}
    for row in disposition_rows:
        if row["disposition"] in include_dispositions:
            approved[row["topic_key"]] = {"topic": review_topics[row["topic_key"]], "basis": "REVIEW_DISPOSITION", "disposition": row["disposition"]}

    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for line in lines:
        if line.get("TOPICKEY", ""):
            lines_by_topic[line["TOPICKEY"]].append(line)
    group_topics: dict[str, list[dict[str, Any]]] = defaultdict(list)
    approved_rows: list[dict[str, Any]] = []
    for key, item in approved.items():
        group = _section_group(item["topic"], item["disposition"])
        group_topics[group].append(item)
        approved_rows.append({
            "topic_key": key,
            "catalog": item["topic"].get("CATALOG", ""),
            "topic": item["topic"].get("TOPIC", ""),
            "status": item["topic"].get("STATUS", ""),
            "section_group": group,
            "approval_basis": item["basis"],
            "disposition": item["disposition"],
            "line_count": len(lines_by_topic.get(key, [])),
        })

    run_id = logger.run_id if logger else "MANRUN-DISPOSITION-CANDIDATE"
    output_dir = paths.manualgen_root / "generated" / "manualgen_disposition_candidates" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    disposition_ledger = output_dir / "manual_review_topic_disposition_ledger.csv"
    approved_ledger = output_dir / "manual_section_factory_approved_topics.csv"
    manifest_path = output_dir / "manual_disposition_manifest.json"
    write_csv(disposition_ledger, disposition_rows)
    write_csv(approved_ledger, approved_rows)
    section_artifacts = []
    for group, title in SECTION_GROUPS.items():
        path = output_dir / f"{group}.md"
        body = [
            "<!-- Candidate-only section-factory input. Not publication. -->",
            f"<!-- group: {group} -->",
            "",
            f"# {title}",
            "",
            f"Topics: {len(group_topics[group])}.",
            "",
        ]
        for item in sorted(group_topics[group], key=lambda x: _int_value(x["topic"], "TOPICID")):
            topic = item["topic"]
            key = topic.get("TOPICKEY", "")
            body.extend([
                f"## {_render_text(topic.get('CATALOG', ''))}: {_render_text(topic.get('TITLE') or topic.get('TOPIC') or key)}",
                "",
                f"- Key/status: `{_render_text(key)}` / `{_render_text(topic.get('STATUS', ''))}`",
                f"- Selection: `{item['basis']}` / `{item['disposition']}`",
                f"- Primary/confidence: `{_render_text(topic.get('PRIMARY', ''))}` / `{_render_text(topic.get('CONFID', ''))}`",
                "",
            ])
            by_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
            for line in lines_by_topic.get(key, []):
                by_kind[line.get("KIND", "")].append(line)
            ordered = [kind for kind in KIND_ORDER if kind in by_kind]
            ordered.extend(sorted(set(by_kind) - set(ordered)))
            for kind in ordered:
                body.extend([f"### {kind.replace('_', ' ').title()}", ""])
                for line in by_kind[kind]:
                    body.append(f"- {_render_text(line.get('TEXT', ''))} <small>({_render_text(line.get('SOURCE', ''))}/{_render_text(line.get('CONFID', ''))}; line {_render_text(line.get('LINEID', ''))})</small>")
                body.append("")
        path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        section_artifacts.append({"group": group, "topic_count": len(group_topics[group]), "path": relpath_posix(path, paths.repo_root), "sha256": sha256_file(path)})

    disposition_counts: dict[str, int] = defaultdict(int)
    for row in disposition_rows:
        disposition_counts[row["disposition"]] += 1
    status = "PASS" if len(review_topics) == 49 and not missing_policy and not extra_policy and not invalid_targets and not invalid_runtime_includes and not invalid_help_includes and len(approved) == 462 else "FAIL"
    manifest = {
        "schema": "dottalk.manualgen.review_disposition_candidate.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "status": status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "canonical_harvest_replaced": 0,
        "counts": {
            "review_topics": len(review_topics),
            "disposition_rows": len(disposition_rows),
            "approved_section_topics": len(approved),
            "missing_policy_rows": len(missing_policy),
            "extra_policy_rows": len(extra_policy),
            "invalid_targets": invalid_targets,
            "invalid_runtime_includes": invalid_runtime_includes,
            "invalid_help_includes": invalid_help_includes,
        },
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "section_groups": section_artifacts,
        "artifacts": {
            "disposition_ledger": relpath_posix(disposition_ledger, paths.repo_root),
            "disposition_ledger_sha256": sha256_file(disposition_ledger),
            "approved_topics": relpath_posix(approved_ledger, paths.repo_root),
            "approved_topics_sha256": sha256_file(approved_ledger),
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("manual_review_topic_dispositions", disposition_ledger, "Explicit 49-topic disposition ledger.")
        logger.artifact("manual_section_factory_approved_topics", approved_ledger, "Approved candidate-only section inputs.")
        logger.artifact("manual_disposition_manifest", manifest_path, "Disposition and section-factory manifest.")
        for artifact in section_artifacts:
            logger.artifact(f"section_factory_{artifact['group']}", paths.repo_root / artifact["path"], artifact["group"])
    state = {"created": 1, "status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "manifest": relpath_posix(manifest_path, paths.repo_root)}
    counts = {**validation, "boundary_fail_rows": 0, **manifest["counts"]}
    return state, counts
