#!/usr/bin/env python3
"""
normcheck_v1 -- cross-authority normalization gate for the COMMAND surface.

THE PROBLEM (member.derald: "working with multiple AI programs is like herding cats")
    One command surface is described in FOUR places, each authored by a different
    hand at a different time, none forced to agree:
        REGISTRY    -- the live dispatch map (registry().add)          [does it run]
        CATALOG     -- SYSCMD.dbf                                       [is it catalogued]
        HELP        -- the dotref/foxref/edref `*ref` catalogs          [is it documented]
        REFLECTION  -- command_catalog.cpp (dottalk::doc CommandDoc)    [CMDHELPCHK view]
    They drift because nothing checks that a command has exactly ONE row in each.
    This gate turns "trust the AIs to stay in sync" into "the build sees the drift".

    Companion: refcheck_v1 asks "is every `*ref` entry a real thing?". normcheck
    asks the dual: "is every real command described once, consistently, everywhere?".

RATCHET SEVERITY (member.derald, 2026-07-27: warn now, hard-fail per lane at parity)
    Each check is a LANE with a severity in LANE_SEVERITY below. Flip a lane to
    'fail' when that surface reaches parity; leave 'warn' while normalization is in
    flight. Exit is nonzero ONLY if a 'fail' lane has findings -- so the gate
    ratchets tighter instead of blocking work in progress.

EXIT: 0 clean (no 'fail'-lane findings); 1 a 'fail' lane has findings; 2 setup error.
Read-only. No mutation.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_syscmd as g
import dbfread
import refcheck_v1 as rc   # reuse authority harvesters

# --- RATCHET CONFIG: flip a lane to 'fail' when its surface reaches parity ---------
LANE_SEVERITY = {
    "IDENTITY":   "fail",   # SYSCMD names a command the registry cannot dispatch (already at parity)
    "HANDLER":    "warn",   # SYSCMD.HANDLER disagrees with the registry handler
    "HELP":       "warn",   # a registered command has no *ref help entry
    "REFLECTION": "warn",   # a command_catalog doc names a command the registry lacks
    # --- function surface (parallel to the command surface) ---
    "FN_IDENTITY": "fail",  # SYSFUNC names a function the engine does not implement
    "FN_COVERAGE": "warn",  # an implemented function is missing from SYSFUNC
}

SYSFUNC = "dottalkpp/data/metadata/SYSFUNC.dbf"
FN_SPEC_RE = re.compile(r'\{\s*"([A-Z_][A-Z0-9_]*)"\s*,\s*\d+\s*,\s*\d+\s*,\s*&')


FUNCDOC_RE = re.compile(r'FunctionDoc\s*\{[^"]*?"([A-Z_][A-Z0-9_]*)"', re.DOTALL)


def implemented_functions(root: Path) -> set[str]:
    """Functions that actually evaluate: runtime BuiltinFnSpec arrays PLUS the
    FunctionDoc entries defined directly in function_catalog.cpp (e.g. ATC, LIKE)."""
    out: set[str] = set()
    exprdir = root / "src/cli/expr"
    if exprdir.exists():
        for p in exprdir.glob("*.cpp"):
            text = p.read_text(errors="replace")
            out |= {m.group(1).upper() for m in FN_SPEC_RE.finditer(text)}
            if p.name == "function_catalog.cpp":
                out |= {m.group(1).upper() for m in FUNCDOC_RE.finditer(text)}
    return out


def sysfunc_names(root: Path) -> set[str]:
    p = root / SYSFUNC
    if not p.exists():
        return set()
    t = dbfread.read(p)
    return {r["CAN_NAME"].strip().upper() for r in t.rows if r["CAN_NAME"].strip()}

SYSCMD = "dottalkpp/data/metadata/SYSCMD.dbf"
CATALOG_CPP = "src/cli/command_catalog.cpp"
DOC_RE = re.compile(r'static const CommandDoc \w+\s*=\s*\{\s*"([^"]+)"')


def catalog_rows(root: Path) -> dict[str, str]:
    t = dbfread.read(root / SYSCMD)
    return {r["CAN_NAME"].strip().upper(): r["HANDLER"].strip() for r in t.rows
            if r["CAN_NAME"].strip()}


def reflection_names(root: Path) -> set[str]:
    p = root / CATALOG_CPP
    if not p.exists():
        return set()
    return {m.group(1).strip().upper() for m in DOC_RE.finditer(p.read_text(errors="replace"))}


def help_names(root: Path) -> set[str]:
    out = set()
    for ns in ("dotref", "foxref", "edref"):
        out |= set(rc.catalog_names(root, ns))
    return out


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    reg = g.registry_map(root)                       # name -> handler
    aliases = rc.shortcut_aliases(root) | rc.routed_aliases(root)
    reg_names = set(reg) | aliases
    cat = catalog_rows(root)                          # SYSCMD name -> handler
    helpn = help_names(root)
    refl = reflection_names(root)
    if not reg or not cat:
        print("normcheck: could not load registry or SYSCMD", file=sys.stderr)
        return 2

    # commands = single-token registered names (subcommand-forms handled elsewhere)
    cmds = sorted(n for n in reg if " " not in n)

    findings: dict[str, list[str]] = {k: [] for k in LANE_SEVERITY}

    # IDENTITY: a SYSCMD row that the registry cannot dispatch
    for name in sorted(cat):
        if " " in name:
            continue
        if name not in reg_names:
            findings["IDENTITY"].append(f"{name} (SYSCMD row, handler={cat[name]}) not registered")

    # HANDLER: SYSCMD.HANDLER vs registry handler
    for name in sorted(set(cat) & set(reg)):
        rh, ch = (reg.get(name) or "").upper(), cat[name].upper()
        if rh and ch and rh != ch:
            findings["HANDLER"].append(f"{name}: SYSCMD={cat[name]} vs registry={reg[name]}")

    # HELP: registered command with no *ref help entry
    for name in cmds:
        if name not in helpn and name not in aliases:
            findings["HELP"].append(name)

    # REFLECTION: registered command with no command_catalog doc
    #   (command_catalog is a CURATED subset by design; report as coverage, warn only)
    # command_catalog is a CURATED SUBSET by design, so "a command missing from it"
    # is NOT drift (reported as coverage below). The drift signal is the dual: a
    # curated doc whose command does not dispatch.
    for name in sorted(refl):
        if " " in name:
            continue
        if name not in reg_names:
            findings["REFLECTION"].append(f"{name} (command_catalog doc) not registered")

    # --- FUNCTION SURFACE: implemented specs vs SYSFUNC catalog ---
    fn_impl = implemented_functions(root)
    fn_cat = sysfunc_names(root)
    for name in sorted(fn_cat - fn_impl):
        findings["FN_IDENTITY"].append(f"{name} (SYSFUNC row) not implemented in any fn spec")
    for name in sorted(fn_impl - fn_cat):
        findings["FN_COVERAGE"].append(name)

    # informational: registered commands absent from SYSCMD (policy: dev/subcmd exclusions)
    not_catalogued = sorted(n for n in cmds if n not in cat and n not in aliases)

    print("cross-authority normalization gate")
    print(f"  commands : REGISTRY {len(reg)}  CATALOG(SYSCMD) {len(cat)}  HELP(*ref) {len(helpn)}"
          f"  REFLECTION(command_catalog) {len(refl)}")
    print(f"  functions: IMPLEMENTED(fn specs) {len(fn_impl)}  CATALOG(SYSFUNC) {len(fn_cat)}\n")
    print(f"{'lane':<12} {'sev':<5} {'findings':>8}")
    fail = 0
    for lane, sev in LANE_SEVERITY.items():
        n = len(findings[lane])
        print(f"{lane:<12} {sev:<5} {n:>8}")
        if sev == "fail":
            fail += n
    refl_cmds = len([n for n in refl if n in reg_names])
    print(f"\n(informational) registered commands absent from SYSCMD: {len(not_catalogued)}"
          f"  -- policy exclusions (dev/subcmd), not gated")
    print(f"(informational) command_catalog curated-doc coverage: {refl_cmds}/{len(cmds)}"
          f" registered commands ({100*refl_cmds/max(len(cmds),1):.0f}%) -- curated subset by design")

    for lane, items in findings.items():
        if items:
            print(f"\n[{LANE_SEVERITY[lane].upper()}] {lane} ({len(items)}):")
            for x in items[:30]:
                print(f"    {x}")
            if len(items) > 30:
                print(f"    ... +{len(items)-30} more")

    print()
    if fail:
        print(f"FAIL: {fail} finding(s) in a 'fail'-severity lane.")
        return 1
    print("PASS: no findings in any 'fail'-severity lane (warn lanes may still have items).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
