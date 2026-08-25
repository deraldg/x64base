#!/usr/bin/env python3
"""
refcheck_v1 -- the `*ref` existence guard (AIF-067 / dotref-automation lane, M2).

WHY THIS EXISTS
    The `*ref.hpp` reference catalogs (`dotref`, `foxref`, `edref`, `devref`,
    `pshell_ref`, `sql_ref`) are hand-authored today and mined by `cmdhelp` as
    `registry U foxref U dotref U edref`. A hand-authored catalog can name a command
    that does not exist -- e.g. `SIMPLEBROWSER` while the command registered as
    `SIMPLEBROWSE` (fixed 2026-07-27 by renaming the command to `SIMPLEBROWSER`).
    Nothing caught that until it was read by eye. This guard catches it.

THE AUTHORITY MODEL (measured 2026-07-27, see the lane scope doc M2 section)
    A `*ref` entry is NOT required to be a top-level command. The family mixes:
      - commands            -> the live registry
      - subcommand forms    -> "PARENT SUB" whose PARENT is a registered command
                               (SET ORDER, REL ENUM, ...)
      - expression funcs    -> SYSFUNC (ALLTRIM, TRIM, ...)
    So an entry RESOLVES if it is any of those. Only `dotref` and `foxref` (the
    native + legacy COMMAND references) are guarded; `edref` (education topics),
    `pshell_ref` and `sql_ref` (PSHELL/SQL sub-form namespaces) are their own
    authorities and are reported informationally, not failed.

    A true PHANTOM is a single-token `dotref`/`foxref` entry that is neither a
    command, nor a function, nor a sub-form of a command. That is the defect class
    this guard fails on.

EXIT: 0 clean; 1 phantom(s) found; 2 could not resolve authorities.
Read-only. No mutation.
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_syscmd as g   # reuse registry_map()
import dbfread

NAME_RE = re.compile(r'(?m)^\s*\{\s*"([^"]+)"')
GUARDED = ("dotref", "foxref")
NAMESPACES = ("dotref", "foxref", "edref", "devref", "pshell_ref", "sql_ref")


STATUS_RE = re.compile(r'^//\s*status:\s*(\S+)', re.M)


def catalog_state(root: Path, ns: str) -> tuple[str, list[str], str | None]:
    """Return (state, names, declared_status).

    state is 'absent' | 'empty' | 'populated'.

    THE THREE STATES ARE REPORTED SEPARATELY, AND THAT IS THE WHOLE POINT.
    Until 2026-08-15 catalog_names() returned [] for a missing file and [] for
    an empty one, and the caller printed "(empty)" and moved on for both. So
    include/devref.hpp sat empty for months while declaring `status: supported`
    and while AI_TIER1_SEED_V1.md named it as one of six reference authorities
    that "own a namespace" -- told to every agent, contradicted by the file, and
    invisible to the guard whose job was exactly this. Zero findings and zero
    content produced identical output.

    The declared status is returned because it is what makes an empty catalog
    judgeable. Empty is legitimate for a RESERVED namespace and a defect for a
    SUPPORTED one. Checking the file against its own claim is cheaper and
    truer than maintaining a hand-kept list of which emptiness is allowed.
    """
    p = root / "include" / f"{ns}.hpp"
    if not p.exists():
        return "absent", [], None
    text = p.read_text(encoding="utf-8", errors="replace")
    m = STATUS_RE.search(text)
    status = m.group(1).strip().lower() if m else None
    if "catalog()" not in text:
        return "empty", [], status
    seg = text.split("catalog()", 1)[-1]
    names = [
        m.group(1).strip().upper()
        for m in NAME_RE.finditer(seg)
        if m.group(1).strip()
    ]
    return ("populated" if names else "empty"), names, status


def catalog_names(root: Path, ns: str) -> list[str]:
    """Names only. Kept for callers that do not care about state."""
    return catalog_state(root, ns)[1]


def function_state(root: Path) -> tuple[str, set[str]]:
    """Return (state, names) from the seeded SYSFUNC catalog.
    state is 'absent' | 'empty' | 'populated'.

    Three states, separately, for the reason catalog_state() gives forty lines
    above -- and this function did not have them until 2026-08-25. It returned
    set() for a missing file AND swallowed every exception, so absent, empty and
    UNREADABLE were one answer. That is the stronger form of the defect
    catalog_state() was written to fix, sitting immediately beneath it.

    The caller unions this with ext_functions() and implemented_core_functions(),
    so a silent empty here does not zero the authority count -- it shrinks it,
    and the printed label still says "(SYSFUNC)" while no SYSFUNC was read. The
    consequence is a misreported authority rather than a missed phantom, which
    is why this is quieter than the FN_IDENTITY lane in normcheck_v1.py and
    still wrong.

    dottalkpp/data/metadata/ is UNTRACKED and not gitignored, so 'absent' is the
    state of every fresh clone.
    """
    dbf = root / "dottalkpp/data/metadata/SYSFUNC.dbf"
    if not dbf.exists():
        return "absent", set()
    t = dbfread.read(dbf)        # unreadable must RAISE, not read as empty
    col = "CAN_NAME" if any(f.name == "CAN_NAME" for f in t.fields) else t.fields[1].name
    names = {r[col].strip().upper() for r in t.rows if r[col].strip()}
    return ("populated" if names else "empty"), names


def function_names(root: Path) -> set[str]:
    """Names only. Kept for callers that do not care about state."""
    return function_state(root)[1]


EXT_FN_RE = re.compile(r'\bstatic\s+std::string\s+fn_([A-Z_][A-Z0-9_]*)\s*\(')
FN_SPEC_RE = re.compile(r'\{\s*"([A-Z_][A-Z0-9_]*)"\s*,\s*\d+\s*,\s*\d+\s*,\s*&')
FUNCDOC_RE = re.compile(r'FunctionDoc\s*\{[^"]*?"([A-Z_][A-Z0-9_]*)"', re.DOTALL)


def implemented_core_functions(root: Path) -> set[str]:
    """Functions that actually evaluate NOW, from source (BuiltinFnSpec arrays +
    function_catalog FunctionDocs) -- source truth, ahead of the SYSFUNC re-harvest."""
    out: set[str] = set()
    exprdir = root / "src/cli/expr"
    if exprdir.exists():
        for p in exprdir.glob("*.cpp"):
            text = p.read_text(errors="replace")
            out |= {m.group(1).upper() for m in FN_SPEC_RE.finditer(text)}
            if p.name == "function_catalog.cpp":
                out |= {m.group(1).upper() for m in FUNCDOC_RE.finditer(text)}
    return out


def ext_functions(root: Path) -> set[str]:
    """Extension functions (e.g. student STU_*) defined in src/ext/fn/*.cpp -- real
    functions that are not part of the core SYSFUNC catalog."""
    d = root / "src/ext/fn"
    if not d.exists():
        return set()
    out: set[str] = set()
    for p in d.glob("*.cpp"):
        out |= {m.group(1).upper() for m in EXT_FN_RE.finditer(p.read_text(errors="replace"))}
    return out


def shortcut_aliases(root: Path) -> set[str]:
    p = root / "src/cli/shortcut_resolver.hpp"
    if not p.exists():
        return set()
    return {m.group(1).upper() for m in
            re.finditer(r'\{\s*"([^"]+)"\s*,\s*"[^"]+"\s*\}', p.read_text(errors="replace"))}


def routed_aliases(root: Path) -> set[str]:
    """Routed/compat aliases registered in reference_collection.cpp add("NAME", ...)."""
    p = root / "src/cli/reference_collection.cpp"
    if not p.exists():
        return set()
    return {m.group(1).upper() for m in
            re.finditer(r'add\(\s*"([A-Za-z_][A-Za-z0-9_]*)"', p.read_text(errors="replace"))}


def classify(name: str, commands: set[str], funcs: set[str]) -> str:
    if name in commands:
        return "command"
    if name in funcs:
        return "function"
    if " " in name and name.split()[0] in commands:
        return "subform"           # "SET ORDER", "REL ENUM", ...
    return "PHANTOM"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true",
                    help="inject a synthetic phantom and confirm the guard flags it")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    commands_reg = set(g.registry_map(root))
    commands_alias = shortcut_aliases(root) | routed_aliases(root)
    commands = commands_reg | commands_alias
    fn_state, fn_seed = function_state(root)
    fn_ext = ext_functions(root)
    fn_core = implemented_core_functions(root)
    funcs = fn_seed | fn_ext | fn_core
    # TEST THE AUTHORITY, NOT THE UNION -- AIF-128, 2026-08-25.
    #
    # This guard used to read `if not commands:` -- the UNION of the registry
    # with the two alias sources. So it answered "fine" whenever ANY of the
    # three resolved, including when the one it names in its own message was
    # the one that failed. Same answer for "registry absent" as for "registry
    # fine": the AIF-118 shape, in the guard whose whole job is to catch that.
    #
    # PROVEN 2026-08-25 by injecting an empty registry_map with the alias
    # sources intact: this message never printed, and refcheck instead
    # reported "GUARDED phantoms (dotref+foxref): 270" and failed with
    # "a native/legacy reference entry names no command" -- exit 1. That is
    # worse than silence. It is a confident, precise accusation against 270
    # hand-authored dotref/foxref entries that were never wrong, and it sends
    # the next reader to edit the catalogs instead of the registry.
    #
    # The aliases are REPORTED rather than counted toward the verdict: a name
    # scraped from an alias table is not a registry, however many of them
    # there are.
    if not commands_reg:
        print("refcheck: could not resolve the command registry -- "
              f"alias sources contributed {len(commands_alias)} name(s), "
              "which is not a registry; refusing to judge the *ref catalogs "
              "against it", file=sys.stderr)
        return 2

    if fn_state != "populated":
        # Do not print "(SYSFUNC)" over a number no SYSFUNC contributed to.
        print(f"refcheck: SYSFUNC catalogue is {fn_state.upper()} "
              f"({'dottalkpp/data/metadata/SYSFUNC.dbf'}) -- the function authority "
              "below is source-derived only", file=sys.stderr)
    # THE LABEL NAMES WHAT IS IN THE NUMBER, added 2026-08-25.
    #
    # This line used to read "77 functions (SYSFUNC)" while normcheck_v1.py, one
    # line below it in the same gate output, reported "CATALOG(SYSFUNC) 75".
    # TWO NUMBERS FOR ONE AUTHORITY, ADJACENT, IN THE SAME RUN. Both were right:
    # this total is a UNION of SYSFUNC with the source-derived sets, and the two
    # extras are STU_REPEAT and STU_UPPER -- student extension functions that
    # will never have a SYSFUNC row, exactly as check_dotref_coverage's own note
    # about fn_STU_* says. The number was never wrong; the parenthetical
    # attributed all of it to SYSFUNC.
    #
    # Same defect as counting COMMANDS.dbf's function-bridge entries as
    # commands: a noun doing work it has not earned. See stack_audit_v1.py
    # check G (COUNT_KINDS), which exists because that mistake was made three
    # times in one session -- including in this very line, by the author of the
    # check, on the same day.
    extra = len(funcs) - len(fn_seed)
    if fn_state == "populated":
        seedlabel = f"SYSFUNC {len(fn_seed)}"
    else:
        seedlabel = f"SYSFUNC {fn_state.upper()}"
    if extra:
        seedlabel += f" + {extra} source-derived"
    # THE SAME DISCIPLINE ON THE COMMAND HALF, added 2026-08-25 (see 3d85320d3).
    #
    # This line read "300 commands/aliases" while normcheck_v1.py, four lines
    # below it in the same gate output, reported "REGISTRY 246". Weaker than
    # the SYSFUNC case: "commands/aliases" does disclose that two KINDS are in
    # the number -- it just never gave the split, so 300 and 246 were left for
    # the reader to reconcile unaided. Disclosing the kinds is not the same as
    # disclosing the proportions.
    #
    # Measured 2026-08-25 on this tree: registry_map 246, shortcut_aliases 44
    # (38 not in the registry), routed_aliases 65 (16 more), union 300, so 54
    # of the 300 are alias forms with no registry entry of their own.
    alias_only = len(commands) - len(commands_reg)
    cmdlabel = f"REGISTRY {len(commands_reg)}"
    if alias_only:
        cmdlabel += f" + {alias_only} alias forms"
    print(f"authorities: {len(commands)} commands/aliases ({cmdlabel}), "
          f"{len(funcs)} functions ({seedlabel})\n")
    print(f"{'catalog':<12} {'entries':>7} {'cmd':>5} {'fn':>4} {'sub':>5} {'PHANTOM':>8}   phantoms")
    total_phantoms = 0
    contradictions: list[str] = []
    for ns in NAMESPACES:
        state, names, status = catalog_state(root, ns)
        if state == "absent":
            print(f"{ns:<12} {'ABSENT':>7}   include/{ns}.hpp does not exist")
            contradictions.append(
                f"{ns}: named in NAMESPACES but include/{ns}.hpp is not there"
            )
            continue
        if state == "empty":
            # Empty is fine if the header SAID it would be. It is a defect when
            # the header claims to be supported, because then the file and its
            # own contract disagree and every reader believes the contract.
            if status in ("reserved", "planned", "stub"):
                print(f"{ns:<12} {'(empty)':>7}   status: {status} -- empty by declaration")
            else:
                print(f"{ns:<12} {'EMPTY':>7}   status: {status or 'unset'}")
                contradictions.append(
                    f"{ns}: catalog is EMPTY but the header declares "
                    f"status: {status or 'unset'!r}. Either populate it or "
                    f"declare it 'reserved'. An empty catalog claiming support "
                    f"is what hid devref while the Tier 1 seed advertised it."
                )
            continue
        counts = {"command": 0, "function": 0, "subform": 0, "PHANTOM": 0}
        phantoms = []
        for n in names:
            k = classify(n, commands, funcs)
            counts[k] += 1
            if k == "PHANTOM":
                phantoms.append(n)
        guarded = ns in GUARDED
        shown = (", ".join(phantoms[:8]) if phantoms else "-")
        if not guarded and phantoms:
            shown = f"[{ns} owns its namespace; not failed] " + shown
        print(f"{ns:<12} {len(names):>7} {counts['command']:>5} {counts['function']:>4} "
              f"{counts['subform']:>5} {counts['PHANTOM']:>8}   {shown}")
        if guarded:
            total_phantoms += counts["PHANTOM"]

    if a.selftest:
        planted = classify("ZZ_PLANTED_PHANTOM", commands, funcs)
        ok = planted == "PHANTOM"
        print(f"\nselftest: planted 'ZZ_PLANTED_PHANTOM' -> classified '{planted}' "
              f"({'CAUGHT' if ok else 'MISSED -- guard is broken'})")
        if not ok:
            return 2

    if contradictions:
        print("\nCATALOG STATE contradictions:")
        for c in contradictions:
            print(f"  {c}")

    print(f"\nGUARDED phantoms (dotref+foxref): {total_phantoms}")
    if total_phantoms or contradictions:
        if total_phantoms:
            print("FAIL: a native/legacy reference entry names no command, function, or sub-form.")
        if contradictions:
            print(f"FAIL: {len(contradictions)} catalog(s) disagree with their own declared status.")
        return 1
    print("PASS: every dotref/foxref entry resolves to a command, function, or sub-form.")
    print("PASS: every catalog's content agrees with its declared status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
