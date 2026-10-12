#!/usr/bin/env python3
"""Refresh or check the generated AI Portal state as one bounded operation.

The default set is the fast onboarding/control plane. The AIF-136 physical
storage inventory is deliberately opt-in because it walks large workspace
populations (without opening database payloads or following reparse points).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RefreshStep:
    label: str
    relative_script: str
    write_args: tuple[str, ...] = ()
    check_args: tuple[str, ...] = ()
    storage: bool = False


STEPS = (
    RefreshStep(
        "tier-0 state",
        "labtalk/ai_portal/generate_tier0_state.py",
        ("--write",),
        ("--check",),
    ),
    # F0 is useful only while it stays bounded and clone-visible. These gates
    # consume their own maintained declarations instead of copying thresholds
    # or mandatory path lists into this orchestrator.
    RefreshStep("seed budget", "tools/staging/check_seed_budget.py"),
    RefreshStep("mandatory tracked onboarding", "labtalk/ai_portal/check_mandatory_tracked.py"),
    RefreshStep("identifier status", "labtalk/ai_portal/validate_portal_identifiers.py", (), ("--check",)),
    RefreshStep("feed status", "labtalk/ai_portal/build_portal_feed_status.py", (), ("--check",)),
    RefreshStep("Portal truth audit", "labtalk/portal/labtalk_portal.py", ("--audit-write",), ("--audit",)),
    # The generated history summary lives inside labtalk/ai_portal and is
    # therefore an M1 inventory input. Build it before the inventory or a
    # nominal refresh makes its own inventory stale later in the same pass.
    RefreshStep("history summary", "labtalk/ai_portal/build_portal_history_summary.py", (), ("--check",)),
    RefreshStep("memory inventory", "labtalk/ai_portal/build_memory_storage_inventory.py", (), ("--check",), True),
    RefreshStep("memory classification", "labtalk/ai_portal/build_memory_storage_classification.py", (), ("--check",), True),
    RefreshStep("memory pilot manifest", "labtalk/ai_portal/validate_memory_pilot_manifest.py"),
    RefreshStep("memory pilot recall", "labtalk/ai_portal/verify_memory_pilot_recall.py"),
    RefreshStep("recall graph tracked targets", "labtalk/portal/tests/test_recall_coverage.py"),
)


def selected_steps(include_storage: bool) -> tuple[RefreshStep, ...]:
    return tuple(step for step in STEPS if include_storage or not step.storage)


def clipped(text: str, limit: int = 4000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return text[:head] + "\n... output clipped ...\n" + text[-tail:]


def run_step(step: RefreshStep, check: bool) -> bool:
    args = step.check_args if check else step.write_args
    command = [sys.executable, str(REPO_ROOT / step.relative_script), *args]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        detail = result.stdout.strip()
        if check:
            print(f"PASS  {step.label}", flush=True)
        else:
            print(
                f"DONE  {step.label}" + (f" -- {detail}" if detail else ""),
                flush=True,
            )
        return True

    print(f"FAIL  {step.label} (exit {result.returncode})", file=sys.stderr)
    if result.stdout.strip():
        print(clipped(result.stdout), file=sys.stderr)
    if result.stderr.strip():
        print(clipped(result.stderr), file=sys.stderr)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report every stale/invalid projection; run the truth audit read-only",
    )
    parser.add_argument(
        "--include-storage",
        action="store_true",
        help="also scan and classify the AIF-136 storage population",
    )
    args = parser.parse_args(argv)

    mode = "check" if args.check else "refresh"
    scope = "control + storage" if args.include_storage else "control plane"
    steps = selected_steps(args.include_storage)
    print(f"portal-state: {mode} ({scope})", flush=True)
    failed: list[str] = []
    passed = 0
    for step in steps:
        if run_step(step, args.check):
            passed += 1
        else:
            failed.append(step.label)
            # A refresh is ordered: do not derive later outputs from a failed
            # prerequisite. A read-only check should report the whole posture.
            if not args.check:
                print(
                    f"portal-state: stopped -- {passed}/{len(steps)} step(s) passed; "
                    f"failed: {step.label}",
                    file=sys.stderr,
                )
                return 1
    if failed:
        print(
            f"portal-state: {passed}/{len(steps)} step(s) passed; failed: "
            + ", ".join(failed),
            file=sys.stderr,
        )
        return 1
    print(f"portal-state: PASS -- {passed}/{len(steps)} step(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
