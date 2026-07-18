from __future__ import annotations

import argparse
import sys

from . import __version__
from .dry_run import build_dry_run
from .curation import build_curation_candidate
from .disposition import build_disposition_candidate
from .structural_reconciliation import build_structural_reconciliation
from .section_delta import build_section_delta_candidates
from .prose_review import build_prose_review_batch
from .selective_merge import build_selective_merge_candidate
from .controlled_acceptance import build_controlled_acceptance_plan
from .controlled_acceptance_apply import apply_controlled_acceptance
from .command_reference_candidate import build_command_reference_candidate
from .command_reference_review_book import build_command_reference_review_book
from .publication_structure_candidate import build_publication_structure_candidate
from .gate4_acceptance import build_gate4_acceptance_plan
from .gate4_acceptance_apply import apply_gate4_acceptance
from .gate5_source_gap import build_gate5_source_gap_candidate
from .gate5_development_plan import build_gate5_development_plan
from .gate5_development_apply import apply_gate5_development_plan
from .parity import parity_review
from .reference_candidate import build_reference_candidate
from .inventory import collect_inventory
from .manifest_export import export_manifests, write_inventory_reports, write_validate_reports
from .paths import ManualgenPaths, resolve_repo_root
from .runlog import RunLogger
from .validation import validate_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manualgen", description="DotTalk++ / x64base manual regeneration helper")
    parser.add_argument("--repo-root", default=None, help="Repository root. Defaults to current directory.")
    parser.add_argument("--manual", default="developer", help="Manual id. Default: developer.")
    parser.add_argument(
        "--publication-workspace",
        default=None,
        help="Explicit published workspace id or repo-relative path used as an assembly reference.",
    )
    parser.add_argument(
        "--harvest-workspace",
        default=None,
        help="Explicit repo-relative or absolute HELP/META CSV evidence directory. It is attached by hash; never promoted.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="Print manualgen and Python versions.")
    sub.add_parser("inventory", help="Inventory current manual publication, media, appendices, and manifests.")
    sub.add_parser("validate", help="Validate current manualgen state without mutating protected systems.")
    sub.add_parser("export-manifest", help="Export machine manifests and hardened structured logs.")
    sub.add_parser("build-dry-run", help="Assemble a generated dry-run manual artifact without replacing publication.")
    sub.add_parser("parity-review", help="Compare latest dry-run artifact against current combined publication without replacing publication.")
    sub.add_parser("build-reference-candidate", help="Project an explicit HELP/META harvest into a candidate-only human topic reference with lineage.")
    sub.add_parser("build-curation-candidate", help="Partition all harvested topics and lines into candidate-only manual review shelves.")
    sub.add_parser("build-disposition-candidate", help="Apply the explicit review-topic policy and generate approved section-factory candidates.")
    sub.add_parser("build-structural-reconciliation", help="Map approved topics onto the governed manual topology and emit a non-mutating delta proposal.")
    sub.add_parser("build-section-delta-candidates", help="Repackage approved topic blocks into per-section additive candidate packets without editing the manual.")
    sub.add_parser("build-prose-review-batch", help="Draft anchored prose for the risk-ordered smallest candidate packets without editing the manual.")
    sub.add_parser("build-selective-merge-candidate", help="Apply approved prose to copied sections and a non-published contextual reader candidate.")
    acceptance = sub.add_parser(
        "build-controlled-acceptance-plan",
        help="Validate one selective merge and emit an exact report-only acceptance package with no apply path.",
    )
    acceptance.add_argument("--candidate-run", required=True, help="Exact passing selective-merge MANRUN id.")
    acceptance.add_argument("--pointer-audit", required=True, help="Repo-relative green pointer-audit JSON.")
    acceptance.add_argument("--context-decision", required=True, help="Repo-relative canonical-preflight context decision.")
    apply_acceptance = sub.add_parser(
        "apply-controlled-acceptance",
        help="Apply one authorized eight-row controlled-acceptance package after backup and exact preflight.",
    )
    apply_acceptance.add_argument("--plan-run", required=True, help="Exact passing controlled-acceptance plan MANRUN id.")
    apply_acceptance.add_argument("--authorization-record", required=True, help="Repo-relative durable authorization record.")
    command_reference = sub.add_parser(
        "build-command-reference-candidate",
        help="Build the accepted reader's linked command pages as a hash-bound report-only candidate.",
    )
    command_reference.add_argument("--reference-run", required=True, help="Exact passing HELP topic-reference MANRUN id.")
    command_reference.add_argument("--disposition-run", required=True, help="Exact passing review-disposition MANRUN id.")
    review_book = sub.add_parser(
        "build-command-reference-review-book",
        help="Build a human index and combined review book from one passing command-reference candidate.",
    )
    review_book.add_argument("--candidate-run", required=True, help="Exact passing command-reference candidate MANRUN id.")
    sub.add_parser(
        "build-publication-structure-candidate",
        help="Build report-only marker normalization and status-disposition previews from the accepted reader.",
    )
    gate4 = sub.add_parser(
        "build-gate4-acceptance-plan",
        help="Build an exact plan-only package for command-page projection and approved publication-structure changes.",
    )
    gate4.add_argument("--command-run", required=True, help="Exact passing command-reference candidate MANRUN id.")
    gate4.add_argument("--structure-run", required=True, help="Exact passing publication-structure candidate MANRUN id.")
    gate4.add_argument("--status-approval", required=True, help="Repo-relative all-row status approval JSON.")
    apply_gate4 = sub.add_parser(
        "apply-gate4-acceptance",
        help="Apply one exactly authorized Gate 4 plan after backup and fail-closed preflight.",
    )
    apply_gate4.add_argument("--plan-run", required=True, help="Exact passing Gate 4 plan MANRUN id.")
    apply_gate4.add_argument("--authorization-record", required=True, help="Repo-relative exact Gate 4 apply authorization JSON.")
    gate5 = sub.add_parser(
        "build-gate5-source-gap-candidate",
        help="Build a report-only 19-page standalone-source reconciliation and staging-manifest review package.",
    )
    gate5.add_argument("--reference-run", required=True, help="Exact passing HELP topic-reference MANRUN id.")
    gate5.add_argument("--disposition-run", required=True, help="Exact passing review-disposition MANRUN id.")
    gate5.add_argument("--gap-ledger", required=True, help="Repo-relative 19-row standalone source-gap ledger.")
    gate5.add_argument("--status-ledger", required=True, help="Repo-relative seven-occurrence held-status ledger.")
    gate5_plan = sub.add_parser(
        "build-gate5-development-plan",
        help="Build an exact plan-only package for the approved 19-page source reconciliation and PROMOTE.manifest delta.",
    )
    gate5_plan.add_argument("--candidate-run", required=True, help="Exact passing Gate 5 source-gap MANRUN id.")
    gate5_plan.add_argument("--decision-record", required=True, help="Repo-relative hash-bound Gate 5 disposition approval JSON.")
    apply_gate5 = sub.add_parser(
        "apply-gate5-development-plan",
        help="Apply one exactly authorized 25-row Gate 5 development documentation plan after backup and fail-closed preflight.",
    )
    apply_gate5.add_argument("--plan-run", required=True, help="Exact passing Gate 5 development-plan MANRUN id.")
    apply_gate5.add_argument("--authorization-record", required=True, help="Repo-relative exact Gate 5 development-apply authorization JSON.")
    return parser


def make_paths(args: argparse.Namespace) -> ManualgenPaths:
    return ManualgenPaths(
        repo_root=resolve_repo_root(args.repo_root),
        manual_id=args.manual,
        publication_workspace=args.publication_workspace,
        harvest_workspace=args.harvest_workspace,
    )


def cmd_version(args: argparse.Namespace) -> int:
    print(f"manualgen {__version__}")
    print(f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "inventory")
    logger.start()
    inv = collect_inventory(paths)
    write_inventory_reports(paths, inv, "mdo_226")
    logger.event("INFO", "inventory", "counts", sections=len(inv.get("sections", [])), media=len(inv.get("media", [])), appendices=len(inv.get("appendices", [])), manifests=len(inv.get("machine_manifests", [])), harvest_files=inv.get("harvest", {}).get("present_file_count", 0))
    logger.artifact("inventory_summary", paths.reports_dir / "mdo_226_inventory_summary_v1.csv", "Inventory summary.")
    logger.artifact("inventory_sections", paths.reports_dir / "mdo_226_inventory_sections_v1.csv", "Section inventory.")
    logger.close("PASS")
    print(f"[manualgen] inventory run_id={logger.run_id}")
    print(f"[manualgen] selected_assembly_workspace={inv.get('selected_assembly_workspace', '')} selection_mode={inv.get('assembly_selection_mode', '')} role={inv.get('selected_workspace_role', '')}")
    print(f"[manualgen] selected_harvest_workspace={inv.get('harvest', {}).get('workspace', '')} selection_mode={inv.get('harvest', {}).get('selection_mode', '')} files={inv.get('harvest', {}).get('present_file_count', 0)}/{inv.get('harvest', {}).get('required_file_count', 0)}")
    print(f"[manualgen] sections={len(inv.get('sections', []))} media={len(inv.get('media', []))} appendices={len(inv.get('appendices', []))} manifests={len(inv.get('machine_manifests', []))}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "validate")
    logger.start()
    inv = collect_inventory(paths)
    checks = validate_inventory(paths, inv)
    counts = write_validate_reports(paths, checks, "mdo_226")
    logger.event("INFO", "validate", "counts", **counts)
    logger.artifact("validate_summary", paths.reports_dir / "mdo_226_validate_summary_v1.csv", "Validation summary.")
    logger.artifact("validate_checks", paths.reports_dir / "mdo_226_validate_checks_v1.csv", "Validation checks.")
    logger.close("PASS" if counts.get("validation_fail_rows", 0) == 0 else "FAIL")
    print(f"[manualgen] validate run_id={logger.run_id}")
    print(f"[manualgen] selected_assembly_workspace={inv.get('selected_assembly_workspace', '')} selection_mode={inv.get('assembly_selection_mode', '')} role={inv.get('selected_workspace_role', '')}")
    print(f"[manualgen] selected_harvest_workspace={inv.get('harvest', {}).get('workspace', '')} selection_mode={inv.get('harvest', {}).get('selection_mode', '')} files={inv.get('harvest', {}).get('present_file_count', 0)}/{inv.get('harvest', {}).get('required_file_count', 0)}")
    print(f"[manualgen] validation_fail_rows={counts.get('validation_fail_rows', 0)} validation_review_rows={counts.get('validation_review_rows', 0)} boundary_fail_rows={counts.get('boundary_fail_rows', 0)}")
    return 0 if counts.get("validation_fail_rows", 0) == 0 and counts.get("boundary_fail_rows", 0) == 0 else 2


def cmd_export_manifest(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "export-manifest")
    logger.start()
    for row in [
        ("manual_publication_rebuilt", 0, "PASS", "Export does not rebuild publication."),
        ("media_files_copied_moved_renamed_deleted", 0, "PASS", "Export does not alter media files."),
        ("x64base_tables_created", 0, "PASS", "Export does not create x64base tables."),
        ("cpp_files_created", 0, "PASS", "Export does not create C++ files."),
        ("help_meta_cmdhelpchk_mutations", 0, "PASS", "No protected-system mutation performed."),
    ]:
        logger.boundary(*row)
    state, counts = export_manifests(paths, logger)
    status = "PASS" if counts.get("validation_fail_rows", 0) == 0 and counts.get("boundary_fail_rows", 0) == 0 else "FAIL"
    logger.event("INFO", "export", "counts", sections=state.get("section_count", 0), media=state.get("media_count", 0), appendices=state.get("appendix_count", 0), validation_fail_rows=counts.get("validation_fail_rows", 0))
    logger.close(status)
    print(f"[manualgen] export-manifest run_id={logger.run_id}")
    print(f"[manualgen] selected_assembly_workspace={state.get('selected_assembly_workspace', '')} selection_mode={state.get('assembly_selection_mode', '')} role={state.get('selected_workspace_role', '')}")
    print(f"[manualgen] sections={state.get('section_count', 0)} media={state.get('media_count', 0)} appendices={state.get('appendix_count', 0)} manifests_after_export={len(list(paths.manifests_dir.glob('*.json')))}")
    print(f"[manualgen] validation_fail_rows={counts.get('validation_fail_rows', 0)} boundary_fail_rows={counts.get('boundary_fail_rows', 0)}")
    return 0 if status == "PASS" else 2


def cmd_build_dry_run(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-dry-run")
    logger.start()
    state, counts = build_dry_run(paths, logger)
    status = "PASS" if counts.get("validation_fail_rows", 0) == 0 and counts.get("boundary_fail_rows", 0) == 0 else "FAIL"
    logger.close(status)
    print(f"[manualgen] build-dry-run run_id={logger.run_id}")
    print(f"[manualgen] selected_assembly_id={state.get('selected_assembly_id', state.get('publication_id', ''))} selection_mode={state.get('assembly_selection_mode', '')} role={state.get('selected_workspace_role', '')}")
    print(f"[manualgen] selected_harvest_workspace={state.get('selected_harvest_workspace', '')} selection_mode={state.get('harvest_selection_mode', '')} files={state.get('harvest_present_file_count', 0)}/{state.get('harvest_required_file_count', 0)}")
    print(f"[manualgen] sections={counts.get('section_count', 0)} media={counts.get('media_count', 0)} appendices={counts.get('appendix_count', 0)}")
    print(f"[manualgen] dry_run_markdown={state.get('dry_run_markdown', '')}")
    print(f"[manualgen] validation_fail_rows={counts.get('validation_fail_rows', 0)} boundary_fail_rows={counts.get('boundary_fail_rows', 0)}")
    print(f"[manualgen] dry_run_hash_matches_current_combined={counts.get('hash_match', 0)}")
    return 0 if status == "PASS" else 2


def cmd_parity_review(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "parity-review")
    logger.start()
    state, counts = parity_review(paths, logger)
    status = "PASS" if counts.get("validation_fail_rows", 0) == 0 and counts.get("boundary_fail_rows", 0) == 0 and counts.get("section_parity_fail_rows", 0) == 0 else "FAIL"
    logger.close(status)
    print(f"[manualgen] parity-review run_id={logger.run_id}")
    print(f"[manualgen] selected_assembly_id={state.get('selected_assembly_id', state.get('publication_id', ''))} selection_mode={state.get('assembly_selection_mode', '')} role={state.get('selected_workspace_role', '')}")
    print(f"[manualgen] sections={counts.get('section_count', 0)} media={counts.get('media_count', 0)} appendices={counts.get('appendix_count', 0)}")
    print(f"[manualgen] exact_hash_match={counts.get('exact_hash_match', 0)} section_parity_fail_rows={counts.get('section_parity_fail_rows', 0)} diff_review_rows={counts.get('diff_review_rows', 0)}")
    print(f"[manualgen] validation_fail_rows={counts.get('validation_fail_rows', 0)} boundary_fail_rows={counts.get('boundary_fail_rows', 0)}")
    return 0 if status == "PASS" else 2


def cmd_build_reference_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-reference-candidate")
    logger.start()
    state, counts = build_reference_candidate(paths, logger)
    complete_lineage = counts.get("included_help_lines") == counts.get("help_lines")
    status = "PASS" if state.get("created") and not counts.get("validation_fail_rows") and not counts.get("duplicate_topic_keys") and complete_lineage and not counts.get("unclassified_unassigned_lines") and not counts.get("command_without_topic") else "FAIL"
    logger.close(status)
    print(f"[manualgen] build-reference-candidate run_id={logger.run_id}")
    print(f"[manualgen] reference_markdown={state.get('reference_markdown', '')}")
    print(f"[manualgen] topics={counts.get('topics', 0)} lines={counts.get('included_help_lines', 0)}/{counts.get('help_lines', 0)} commands={counts.get('commands', 0)} args={counts.get('command_arguments', 0)} syscmd={counts.get('syscmd_rows', 0)}")
    print(f"[manualgen] non_topic_global_messages={counts.get('global_shared_message_lines', 0)} non_topic_source_facts={counts.get('unscoped_source_message_fact_lines', 0)} unclassified={counts.get('unclassified_unassigned_lines', 0)}")
    print(f"[manualgen] compact_aliases_resolved={counts.get('compact_command_aliases_resolved', 0)} command_without_topic={counts.get('command_without_topic', 0)} status={status}")
    return 0 if status != "FAIL" else 2


def cmd_build_curation_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-curation-candidate")
    logger.start()
    state, counts = build_curation_candidate(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-curation-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] topics={counts.get('topic_ledger_rows', 0)}/{counts.get('topics', 0)} lines={counts.get('line_ledger_rows', 0)}/{counts.get('lines', 0)} shelves={counts.get('shelf_packets', 0)}")
    print(f"[manualgen] duplicate_topics={counts.get('duplicate_topic_keys', 0)} duplicate_lines={counts.get('duplicate_line_ids', 0)} unclassified_topics={counts.get('unclassified_topics', 0)} unclassified_lines={counts.get('unclassified_lines', 0)} status={status}")
    return 0 if status == "PASS" else 2


def cmd_build_disposition_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-disposition-candidate")
    logger.start()
    state, counts = build_disposition_candidate(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-disposition-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] dispositions={counts.get('disposition_rows', 0)}/{counts.get('review_topics', 0)} approved_section_topics={counts.get('approved_section_topics', 0)}")
    print(f"[manualgen] missing_policy={counts.get('missing_policy_rows', 0)} extra_policy={counts.get('extra_policy_rows', 0)} invalid_targets={counts.get('invalid_targets', 0)} invalid_runtime={counts.get('invalid_runtime_includes', 0)} invalid_help={counts.get('invalid_help_includes', 0)} status={status}")
    return 0 if status == "PASS" else 2


def cmd_build_structural_reconciliation(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-structural-reconciliation")
    logger.start()
    state, counts = build_structural_reconciliation(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-structural-reconciliation run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] baseline primary={counts.get('primary_sections', 0)} media={counts.get('media_revision_sections', 0)} controlled_runtime={counts.get('controlled_runtime_sections', 0)} union={counts.get('union_section_surfaces', 0)}")
    print(f"[manualgen] mapped_topics={counts.get('mapped_topics', 0)}/{counts.get('approved_topics', 0)} section_mentions={counts.get('exact_existing_section_mentions', 0)} appendix_mentions={counts.get('exact_existing_appendix_mentions', 0)} review_resolved={counts.get('structural_review_resolved_rows', 0)}/{counts.get('structural_review_policy_rows', 0)} remaining_review={counts.get('review_fallback_topics', 0)} unplaced={counts.get('unplaced_fallback_topics', 0)}")
    print(f"[manualgen] duplicate_topics={counts.get('duplicate_topic_keys', 0)} missing_targets={counts.get('missing_structural_targets', 0)} status={status}")
    return 0 if status == "PASS" else 2


def cmd_build_section_delta_candidates(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-section-delta-candidates")
    logger.start()
    state, counts = build_section_delta_candidates(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-section-delta-candidates run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] topic_blocks={counts.get('used_topic_blocks', 0)}/{counts.get('approved_topics', 0)} mapped={counts.get('mapped_topics', 0)} packets={counts.get('target_packets', 0)}")
    print(f"[manualgen] missing={counts.get('missing_topic_blocks', 0)} duplicates={counts.get('duplicate_topic_blocks', 0)} unused={counts.get('unused_topic_blocks', 0)} status={status}")
    return 0 if status == "PASS" else 2


def cmd_build_prose_review_batch(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-prose-review-batch")
    logger.start()
    state, counts = build_prose_review_batch(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-prose-review-batch run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] topics={counts.get('input_topics', 0)}/{counts.get('policy_topics', 0)} candidates={counts.get('candidate_files', 0)}")
    print(f"[manualgen] additive={counts.get('additive_prose_topics', 0)} canary={counts.get('canary_cross_reference_topics', 0)} appendix={counts.get('appendix_only_topics', 0)}")
    print(f"[manualgen] missing={counts.get('missing_topics', 0)} unexpected={counts.get('unexpected_topics', 0)} duplicates={counts.get('duplicate_topics', 0)} packet_hash_failures={counts.get('invalid_packet_hashes', 0)} missing_anchors={counts.get('missing_anchors', 0)} status={status}")
    return 0 if status == "PASS" else 2


def cmd_build_selective_merge_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-selective-merge-candidate")
    logger.start()
    state, counts = build_selective_merge_candidate(paths, logger)
    status = state.get("status", "FAIL")
    logger.close(status)
    print(f"[manualgen] build-selective-merge-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] reviewed_topics={counts.get('reviewed_topics', 0)} sections={counts.get('section_candidates', 0)} appendices={counts.get('appendix_candidates', 0)} readers={counts.get('reader_candidates', 0)} diffs={counts.get('diff_files', 0)}")
    print(f"[manualgen] hash_failures={counts.get('hash_failures', 0)} anchor_failures={counts.get('anchor_failures', 0)} extraction_failures={counts.get('extraction_failures', 0)} section_deletions={counts.get('section_deletions', 0)} canonical_hash_changes={counts.get('canonical_hash_changes', 0)} status={status}")
    print(f"[manualgen] reader_candidate={state.get('reader_candidate', '')}")
    return 0 if status == "PASS" else 2


def cmd_build_controlled_acceptance_plan(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-controlled-acceptance-plan")
    logger.start()
    state, counts = build_controlled_acceptance_plan(
        paths,
        args.candidate_run,
        args.pointer_audit,
        args.context_decision,
        logger,
    )
    status = state.get("status", "FAIL")
    logger.close("PASS" if status == "PASS_PLAN_ONLY" else "FAIL")
    print(f"[manualgen] build-controlled-acceptance-plan run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] planned_mutation_rows={counts.get('planned_mutation_rows', 0)} validation_findings={counts.get('validation_findings', 0)} reviewed_topics={counts.get('reviewed_topics', 0)}")
    print(f"[manualgen] apply_available=0 canonical_files_mutated=0 status={status}")
    return 0 if status == "PASS_PLAN_ONLY" else 2


def cmd_apply_controlled_acceptance(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "apply-controlled-acceptance")
    logger.start()
    state, counts = apply_controlled_acceptance(
        paths,
        args.plan_run,
        args.authorization_record,
        logger,
    )
    status = state.get("status", "FAIL_PREFLIGHT")
    logger.close("PASS" if status == "PASS_APPLIED" else "FAIL")
    print(f"[manualgen] apply-controlled-acceptance run_id={logger.run_id}")
    print(f"[manualgen] backup_root={state.get('backup_root', '')}")
    print(f"[manualgen] applied_rows={counts.get('applied_rows', 0)} validation_findings={counts.get('validation_findings', 0)} rollback_findings={counts.get('rollback_findings', 0)}")
    print(f"[manualgen] reader_pointer_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_APPLIED" else 2


def cmd_build_command_reference_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-command-reference-candidate")
    logger.start()
    state, counts = build_command_reference_candidate(
        paths,
        args.reference_run,
        args.disposition_run,
        logger,
    )
    status = state.get("status", "FAIL_CANDIDATE")
    logger.close("PASS" if status == "PASS_CANDIDATE_ONLY" else "FAIL")
    print(f"[manualgen] build-command-reference-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] pages={counts.get('candidate_pages', 0)}/{counts.get('reader_link_destinations', 0)} lineage_rows={counts.get('lineage_rows', 0)} attention={counts.get('attention_labelled_pages', 0)}")
    print(f"[manualgen] findings={counts.get('findings', 0)} local_path_hits={counts.get('local_path_hits', 0)} accepted_reader_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_CANDIDATE_ONLY" else 2


def cmd_build_command_reference_review_book(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-command-reference-review-book")
    logger.start()
    state, counts = build_command_reference_review_book(paths, args.candidate_run, logger)
    status = state.get("status", "FAIL_REVIEW_BOOK")
    logger.close("PASS" if status == "PASS_REVIEW_ONLY" else "FAIL")
    print(f"[manualgen] build-command-reference-review-book run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] pages={counts.get('verified_pages', 0)} index_links={counts.get('index_links', 0)} combined_pages={counts.get('combined_pages', 0)} hash_failures={counts.get('page_hash_failures', 0)} status={status}")
    return 0 if status == "PASS_REVIEW_ONLY" else 2


def cmd_build_publication_structure_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-publication-structure-candidate")
    logger.start()
    state, counts = build_publication_structure_candidate(paths, logger)
    status = state.get("status", "FAIL_CANDIDATE")
    logger.close("PASS" if status == "PASS_CANDIDATE_ONLY" else "FAIL")
    print(f"[manualgen] build-publication-structure-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(f"[manualgen] markers={counts.get('inserted_end_markers', 0)} balance={counts.get('candidate_begin_markers', 0)}/{counts.get('candidate_end_markers', 0)} statuses={counts.get('status_dispositions', 0)} remaining={counts.get('remaining_review_statuses', 0)} findings={counts.get('findings', 0)} status={status}")
    return 0 if status == "PASS_CANDIDATE_ONLY" else 2


def cmd_build_gate4_acceptance_plan(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-gate4-acceptance-plan")
    logger.start()
    state, counts = build_gate4_acceptance_plan(
        paths,
        args.command_run,
        args.structure_run,
        args.status_approval,
        logger,
    )
    status = state.get("status", "FAIL_PLAN")
    logger.close("PASS" if status == "PASS_PLAN_ONLY" else "FAIL")
    print(f"[manualgen] build-gate4-acceptance-plan run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(
        f"[manualgen] mutations={counts.get('planned_mutation_rows', 0)} "
        f"create={counts.get('planned_create_rows', 0)} replace={counts.get('planned_replace_rows', 0)} "
        f"pages={counts.get('command_pages', 0)} index={counts.get('command_indexes', 0)}"
    )
    print(
        f"[manualgen] sections={counts.get('section_status_files', 0)} "
        f"reader_links={counts.get('reader_link_rewrites', 0)} "
        f"markers={counts.get('reader_begin_markers', 0)}/{counts.get('reader_end_markers', 0)} "
        f"findings={counts.get('findings', 0)} canonical_files_mutated=0 status={status}"
    )
    return 0 if status == "PASS_PLAN_ONLY" else 2


def cmd_apply_gate4_acceptance(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "apply-gate4-acceptance")
    logger.start()
    state, counts = apply_gate4_acceptance(
        paths, args.plan_run, args.authorization_record, logger
    )
    status = state.get("status", "FAIL_PREFLIGHT")
    logger.close("PASS" if status == "PASS_APPLIED" else "FAIL")
    print(f"[manualgen] apply-gate4-acceptance run_id={logger.run_id}")
    print(f"[manualgen] backup_root={state.get('backup_root', '')}")
    print(
        f"[manualgen] applied_rows={counts.get('applied_rows', 0)} "
        f"validation_findings={counts.get('validation_findings', 0)} "
        f"rollback_findings={counts.get('rollback_findings', 0)}"
    )
    print(f"[manualgen] reader_pointer_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_APPLIED" else 2


def cmd_build_gate5_source_gap_candidate(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-gate5-source-gap-candidate")
    logger.start()
    state, counts = build_gate5_source_gap_candidate(
        paths,
        args.reference_run,
        args.disposition_run,
        args.gap_ledger,
        args.status_ledger,
        logger,
    )
    status = state.get("status", "FAIL_CANDIDATE")
    logger.close("PASS" if status == "PASS_CANDIDATE_ONLY" else "FAIL")
    print(f"[manualgen] build-gate5-source-gap-candidate run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(
        f"[manualgen] pages={counts.get('candidate_pages', 0)}/19 "
        f"lineage={counts.get('lineage_rows', 0)} attention={counts.get('attention_pages', 0)} "
        f"statuses={counts.get('logical_status_decisions', 0)}/{counts.get('status_occurrences', 0)} "
        f"findings={counts.get('findings', 0)}"
    )
    print(f"[manualgen] accepted_manual_mutated=0 source_staging_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_CANDIDATE_ONLY" else 2


def cmd_build_gate5_development_plan(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "build-gate5-development-plan")
    logger.start()
    state, counts = build_gate5_development_plan(
        paths,
        args.candidate_run,
        args.decision_record,
        logger,
    )
    status = state.get("status", "FAIL_PLAN")
    logger.close("PASS" if status == "PASS_PLAN_ONLY" else "FAIL")
    print(f"[manualgen] build-gate5-development-plan run_id={logger.run_id}")
    print(f"[manualgen] output_dir={state.get('output_dir', '')}")
    print(
        f"[manualgen] mutations={counts.get('planned_mutation_rows', 0)} "
        f"create={counts.get('planned_create_rows', 0)} replace={counts.get('planned_replace_rows', 0)} "
        f"pages={counts.get('supplemental_pages', 0)}/19 index={counts.get('accepted_index_links', 0)}/183 "
        f"findings={counts.get('findings', 0)}"
    )
    print(f"[manualgen] accepted_reader_mutated=0 source_staging_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_PLAN_ONLY" else 2


def cmd_apply_gate5_development_plan(args: argparse.Namespace) -> int:
    paths = make_paths(args)
    paths.ensure_output_dirs()
    logger = RunLogger(paths, "apply-gate5-development-plan")
    logger.start()
    state, counts = apply_gate5_development_plan(
        paths,
        args.plan_run,
        args.authorization_record,
        logger,
    )
    status = state.get("status", "FAIL_PREFLIGHT")
    logger.close("PASS" if status == "PASS_APPLIED" else "FAIL")
    print(f"[manualgen] apply-gate5-development-plan run_id={logger.run_id}")
    print(f"[manualgen] backup_root={state.get('backup_root', '')}")
    print(
        f"[manualgen] applied_rows={counts.get('applied_rows', 0)} "
        f"validation_findings={counts.get('validation_findings', 0)} "
        f"rollback_findings={counts.get('rollback_findings', 0)}"
    )
    print(f"[manualgen] source_staging_mutated=0 git_mutated=0 website_mutated=0 status={status}")
    return 0 if status == "PASS_APPLIED" else 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        return cmd_version(args)
    if args.command == "inventory":
        return cmd_inventory(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "export-manifest":
        return cmd_export_manifest(args)
    if args.command == "build-dry-run":
        return cmd_build_dry_run(args)
    if args.command == "parity-review":
        return cmd_parity_review(args)
    if args.command == "build-reference-candidate":
        return cmd_build_reference_candidate(args)
    if args.command == "build-curation-candidate":
        return cmd_build_curation_candidate(args)
    if args.command == "build-disposition-candidate":
        return cmd_build_disposition_candidate(args)
    if args.command == "build-structural-reconciliation":
        return cmd_build_structural_reconciliation(args)
    if args.command == "build-section-delta-candidates":
        return cmd_build_section_delta_candidates(args)
    if args.command == "build-prose-review-batch":
        return cmd_build_prose_review_batch(args)
    if args.command == "build-selective-merge-candidate":
        return cmd_build_selective_merge_candidate(args)
    if args.command == "build-controlled-acceptance-plan":
        return cmd_build_controlled_acceptance_plan(args)
    if args.command == "apply-controlled-acceptance":
        return cmd_apply_controlled_acceptance(args)
    if args.command == "build-command-reference-candidate":
        return cmd_build_command_reference_candidate(args)
    if args.command == "build-command-reference-review-book":
        return cmd_build_command_reference_review_book(args)
    if args.command == "build-publication-structure-candidate":
        return cmd_build_publication_structure_candidate(args)
    if args.command == "build-gate4-acceptance-plan":
        return cmd_build_gate4_acceptance_plan(args)
    if args.command == "apply-gate4-acceptance":
        return cmd_apply_gate4_acceptance(args)
    if args.command == "build-gate5-source-gap-candidate":
        return cmd_build_gate5_source_gap_candidate(args)
    if args.command == "build-gate5-development-plan":
        return cmd_build_gate5_development_plan(args)
    if args.command == "apply-gate5-development-plan":
        return cmd_apply_gate5_development_plan(args)
    parser.error(f"unknown command: {args.command}")
    return 2
