#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_role_hotfix"


def replace_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        raise SystemExit(f"Could not find start marker: {start_marker!r}")
    end = text.find(end_marker, start)
    if end == -1:
        raise SystemExit(f"Could not find end marker after {start_marker!r}: {end_marker!r}")
    return text[:start] + replacement.rstrip() + "\n\n\n" + text[end:]


def main() -> int:
    if not TARGET.is_file():
        raise SystemExit(f"Missing target probe: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    original = text

    role_helpers = """def command_registry_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "shell_commands.cpp",
    }


def command_dispatch_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "shell.cpp",
        "shell_dispatch.cpp",
    }


def command_family_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "cmdhelp.cpp",
        "cmd_help.cpp",
        "cmd_dothelp.cpp",
        "helpdata_cmdhelp_bridge.cpp",
    }


def simple_command_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/cmd_") and name.endswith(".cpp")


def command_usage_target(path: str) -> bool:
    return simple_command_target(path) or command_family_target(path)"""
    text = replace_block(text, "def command_usage_target(path: str) -> bool:", "def recommended_family(path: str) -> str:", role_helpers)

    family_block = """def recommended_family(path: str) -> str:
    p = norm(path)
    name = fname(path)
    lane = lane_for_path(path)

    if command_registry_target(path):
        return "selfdoc.command_registry_contract"
    if command_dispatch_target(path):
        return "selfdoc.command_dispatch_contract"
    if command_family_target(path):
        return "selfdoc.help_subsystem_contract"
    if simple_command_target(path):
        return "@dottalk.usage v1"
    if lane == "expression_engine":
        return "selfdoc.function_contract" if (name.startswith("fn_") or not p.startswith("include/")) else "selfdoc.api_contract"
    if lane in {"xbase_storage_engine", "index_engine", "memo_engine"}:
        return "selfdoc.api_contract" if p.startswith("include/") else "selfdoc.engine_contract"
    if lane == "tui_tv_layer":
        return "selfdoc.ui_contract"
    if lane == "bindings_python":
        return "selfdoc.binding_contract"
    if lane == "test_dev_harness":
        return "selfdoc.test_contract"
    if lane in {"cli_headers", "public_or_shared_header"}:
        return "selfdoc.api_contract"
    return "manual_classification" """
    text = replace_block(text, "def recommended_family(path: str) -> str:", "def lifecycle_class_for_path(path: str) -> str:", family_block)

    action_block = """def action_for_alternate_family(family: str) -> str:
    if family == "selfdoc.command_registry_contract":
        return "alternate_contract_registry"
    if family == "selfdoc.command_dispatch_contract":
        return "alternate_contract_dispatch"
    if family == "selfdoc.help_subsystem_contract":
        return "action_required_add_command_family_usage_contract"
    if family == "selfdoc.command_family_contract":
        return "action_required_add_command_family_usage_contract"
    if family == "selfdoc.api_contract":
        return "alternate_contract_api_or_exclude"
    if family == "selfdoc.engine_contract":
        return "alternate_contract_engine"
    if family == "selfdoc.ui_contract":
        return "alternate_contract_ui"
    if family == "selfdoc.function_contract":
        return "alternate_contract_function"
    if family == "selfdoc.binding_contract":
        return "alternate_contract_binding"
    if family == "selfdoc.test_contract":
        return "alternate_contract_test_or_exclude"
    return "manual_classification" """
    text = replace_block(text, "def action_for_alternate_family(family: str) -> str:", "def classify_file(path: Path, root: Path) -> Record:", action_block)

    old_missing = """    if not blocks:
        action = "action_required_add_command_usage_contract" if is_command_target else action_for_alternate_family(family)
        notes = read_notes + (["true missing command/help usage candidate"] if is_command_target else [])
        return Record(rel, lane, family, lifecycle, False, 0, MARKER, "missing_contract",
                      action, is_command_target, True, False, notes=notes)"""
    new_missing = """    if not blocks:
        if command_family_target(rel):
            action = "action_required_add_command_family_usage_contract"
            actionable = True
            notes = read_notes + ["family-level command/help subsystem usage candidate"]
        elif simple_command_target(rel):
            action = "action_required_add_command_usage_contract"
            actionable = True
            notes = read_notes + ["simple command usage candidate"]
        else:
            action = action_for_alternate_family(family)
            actionable = False
            notes = read_notes + (["command infrastructure contract candidate"] if command_registry_target(rel) or command_dispatch_target(rel) else [])
        return Record(rel, lane, family, lifecycle, False, 0, MARKER, "missing_contract",
                      action, actionable, True, False, notes=notes)"""
    if old_missing not in text:
        raise SystemExit("Could not find missing-contract classification block to replace.")
    text = text.replace(old_missing, new_missing)

    old_existing = """    if is_command_target:
        if has_shape_issue:
            action = "review_existing_command_contract_shape"
            status = "shape_review"
        else:
            action = "accepted_existing_command_contract"
            status = "accepted"
    else:
        action = action_for_alternate_family(family)
        status = "alternate_contract_recommended" if family != "manual_classification" else "manual_classification"

    is_shape_review = is_command_target and has_shape_issue
    broad_escrow = (not blocks) or is_shape_review or (not is_command_target and family == "manual_classification")"""
    new_existing = """    if is_command_target:
        if has_shape_issue:
            action = "review_existing_command_contract_shape"
            status = "shape_review"
        else:
            action = "accepted_existing_command_family_contract" if command_family_target(rel) else "accepted_existing_command_contract"
            status = "accepted"
    else:
        action = action_for_alternate_family(family)
        status = "alternate_contract_recommended" if family != "manual_classification" else "manual_classification"

    is_shape_review = is_command_target and has_shape_issue
    broad_escrow = (not blocks) or is_shape_review or (not is_command_target and family == "manual_classification")"""
    if old_existing not in text:
        raise SystemExit("Could not find existing-contract classification block to replace.")
    text = text.replace(old_existing, new_existing)

    old_summary = """        "actionable_missing_command_help_usage_contracts": sum(1 for r in records if r.is_actionable_command_usage_backlog),
        "accepted_existing_command_contracts": sum(1 for r in records if r.action_class == "accepted_existing_command_contract"),
        "existing_command_contracts_needing_shape_review": sum(1 for r in records if r.is_shape_review_candidate),"""
    new_summary = """        "actionable_missing_command_help_usage_contracts": sum(1 for r in records if r.is_actionable_command_usage_backlog),
        "actionable_simple_command_usage_contracts": sum(1 for r in records if r.action_class == "action_required_add_command_usage_contract"),
        "actionable_family_command_usage_contracts": sum(1 for r in records if r.action_class == "action_required_add_command_family_usage_contract"),
        "registry_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_registry"),
        "dispatch_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_dispatch"),
        "accepted_existing_command_contracts": sum(1 for r in records if r.action_class == "accepted_existing_command_contract"),
        "accepted_existing_command_family_contracts": sum(1 for r in records if r.action_class == "accepted_existing_command_family_contract"),
        "existing_command_contracts_needing_shape_review": sum(1 for r in records if r.is_shape_review_candidate),"""
    if old_summary not in text:
        raise SystemExit("Could not find summary count fragment to replace.")
    text = text.replace(old_summary, new_summary)

    old_keys = """        "actionable_missing_command_help_usage_contracts",
        "accepted_existing_command_contracts", "existing_command_contracts_needing_shape_review","""
    new_keys = """        "actionable_missing_command_help_usage_contracts",
        "actionable_simple_command_usage_contracts",
        "actionable_family_command_usage_contracts",
        "registry_contract_candidates",
        "dispatch_contract_candidates",
        "accepted_existing_command_contracts",
        "accepted_existing_command_family_contracts", "existing_command_contracts_needing_shape_review","""
    if old_keys not in text:
        raise SystemExit("Could not find markdown summary key block to replace.")
    text = text.replace(old_keys, new_keys)

    old_console = """        print(f"Actionable missing command/help usage contracts: {summary['actionable_missing_command_help_usage_contracts']}")
        print(f"Accepted existing command contracts: {summary['accepted_existing_command_contracts']}")"""
    new_console = """        print(f"Actionable missing command/help usage contracts: {summary['actionable_missing_command_help_usage_contracts']}")
        print(f"Actionable simple command usage contracts: {summary['actionable_simple_command_usage_contracts']}")
        print(f"Actionable family command usage contracts: {summary['actionable_family_command_usage_contracts']}")
        print(f"Registry contract candidates: {summary['registry_contract_candidates']}")
        print(f"Dispatch contract candidates: {summary['dispatch_contract_candidates']}")
        print(f"Accepted existing command contracts: {summary['accepted_existing_command_contracts']}")
        print(f"Accepted existing command family contracts: {summary['accepted_existing_command_family_contracts']}")"""
    if old_console not in text:
        raise SystemExit("Could not find console output fragment to replace.")
    text = text.replace(old_console, new_console)

    if text == original:
        print("No changes needed; target already appears role-aware.")
        return 0

    BACKUP.write_text(original, encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8", newline="\n")

    print(f"Updated: {TARGET}")
    print(f"Backup written to: {BACKUP}")
    print("Role distinction added:")
    print("  shell_commands.cpp -> selfdoc.command_registry_contract / alternate_contract_registry")
    print("  cmdhelp.cpp -> selfdoc.help_subsystem_contract / action_required_add_command_family_usage_contract")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No source contracts were repaired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
