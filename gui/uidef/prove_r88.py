#!/usr/bin/env python3
"""R88's guard: a container KIND is not finished when it renders.

WHY THIS EXISTS

    R88 ended with a rule this lane had paid for three times and a hole nobody
    was watching:

        "A new container KIND is not finished when it renders. It is finished
         when its owner knows how to let go of it. CONTAINER_KINDS and
         destroy_container() are two lists that must move together, and nothing
         enforces that."

    This is that enforcement. It is a GUARD, not a fix -- it changes no
    behaviour, and R88 is explicit that a patch to destroy_container() whose
    effect the author cannot explain is a second unknown stacked on the first.

    Measured 2026-09-16, the situation is one worse than R88 stated. There are
    not two lists. There are FOUR, and they disagree three ways:

        uidef_text.py  form panel page pageset group splitter
        uidef_tk.py    form panel group page pageset splitter
        uidef_wx.py    form group panel page pageset            <-- no splitter
        destroy_container()  wxBookCtrlBase | wxStaticBox | fallthrough

    The backend whose CONTAINER_KINDS omits `splitter` is wx -- the one that
    segfaults when an inner splitter is torn down under --dispatch.

WHAT IT ENFORCES

    Every kind in ANY backend's CONTAINER_KINDS must appear in REMOVAL below,
    which says HOW its owner lets go of it. Adding a container kind without
    saying that is the R88 defect, and it fails here.

    A kind may legitimately be removed by the generic fallthrough. What it may
    not do is REACH that fallthrough silently -- `fallthrough` is a claim
    somebody made, citable and reviewable, not an absence of thought.

EXIT CODES
    0  every container kind declares its removal
    1  a kind is undeclared, or a declared branch has vanished from uidef_rt.h
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BACKENDS = ("uidef_text.py", "uidef_tk.py", "uidef_wx.py")
RUNTIME = "uidef_rt.h"

# HOW EACH CONTAINER KIND'S OWNER LETS GO OF IT.
#
# `branch` names a wxDynamicCast target that must still be present in
# destroy_container(); if that branch is deleted, this guard fails rather than
# silently passing on a kind whose removal verb no longer exists.
#
# `fallthrough` means Destroy() + parent Layout() is correct for this kind and
# somebody says so on the record. It is an assertion, not a default.
REMOVAL = {
    "form":     ("fallthrough", "A top-level frame has no owner inside the document."),
    "panel":    ("fallthrough", "A plain wxPanel is owned by a sizer that Layout() re-runs. R45 covers the wxStaticBox case; a bare panel is not that case."),
    "group":    ("branch:wxStaticBox", "R45 -- owned by its wxStaticBoxSizer. Destroy() then Layout() is a segfault; detach from the sizer."),
    "page":     ("branch:wxBookCtrlBase", "R46 -- the book owns its pages. DeletePage, not Destroy."),
    "pageset":  ("fallthrough", "The book itself is owned by its parent's sizer, not by another book."),
    "splitter": ("UNPROVEN", "R88 -- a splitter's panes enter through Split*(), never a sizer. It is the FOURTH owner and it has no verb. Tearing down an inner splitter under --dispatch is exit 139; three orderings were tried and all crash. Proven for layout, unproven for lifetime."),
}


def die(msg: str) -> None:
    print(f"prove_r88: {msg}", file=sys.stderr)
    raise SystemExit(1)


def container_kinds(root: Path) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for name in BACKENDS:
        p = root / name
        if not p.is_file():
            die(f"missing backend {name}")
        m = re.search(r"CONTAINER_KINDS\s*=\s*\(([^)]*)\)", p.read_text(encoding="utf-8"))
        if not m:
            die(f"{name}: no CONTAINER_KINDS tuple found")
        out[name] = tuple(re.findall(r"'([a-z]+)'", m.group(1)))
    return out


def destroy_branches(root: Path) -> set[str]:
    p = root / RUNTIME
    if not p.is_file():
        die(f"missing {RUNTIME}")
    src = p.read_text(encoding="utf-8")
    m = re.search(r"destroy_container\s*\([^)]*\)\s*\{(.*?)\n\}", src, re.S)
    if not m:
        die(f"{RUNTIME}: destroy_container() not found")
    return set(re.findall(r"wxDynamicCast\s*\([^,]+,\s*(wx\w+)\s*\)", m.group(1)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uidef", default=str(Path(__file__).resolve().parent),
                    help="the gui/uidef directory (default: this script's own)")
    a = ap.parse_args()
    root = Path(a.uidef).resolve()

    kinds = container_kinds(root)
    branches = destroy_branches(root)
    every = sorted({k for v in kinds.values() for k in v})

    print(f"prove_r88: {len(every)} container kind(s) across {len(kinds)} backend(s); "
          f"destroy_container() carries {len(branches)} branch(es): {', '.join(sorted(branches))}")

    # -- the cross-backend disagreement, reported because R88 did not know about it
    union, common = set(every), set.intersection(*(set(v) for v in kinds.values()))
    if union != common:
        print("  BACKENDS DISAGREE about what a container is:")
        for name, v in kinds.items():
            missing = sorted(union - set(v))
            print(f"    {name:16s} {len(v)} kind(s)" + (f"   MISSING: {', '.join(missing)}" if missing else ""))

    failures, unproven = [], []
    for k in every:
        if k not in REMOVAL:
            failures.append(f"container kind {k!r} is in CONTAINER_KINDS and declares no removal. "
                            f"Add it to REMOVAL, saying how its owner lets go of it.")
            continue
        how, why = REMOVAL[k]
        if how.startswith("branch:"):
            want = how.split(":", 1)[1]
            if want not in branches:
                failures.append(f"{k!r} declares removal via {want}, which destroy_container() no longer casts to.")
        elif how == "UNPROVEN":
            unproven.append((k, why))

    for k, why in unproven:
        print(f"  UNPROVEN LIFETIME  {k} -- {why}")

    if failures:
        for f in failures:
            print(f"  FAIL  {f}", file=sys.stderr)
        print("\nprove_r88: FAIL -- a container kind renders and nothing says how it is destroyed.",
              file=sys.stderr)
        return 1

    print("prove_r88: PASS -- every container kind declares how its owner lets go of it.")
    if unproven:
        print(f"           {len(unproven)} declared UNPROVEN and listed above; that is a known hole, not a green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
