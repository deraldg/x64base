#!/usr/bin/env python3
"""dotref_autogen.py -- report-only dotref candidate generator (milestone 1).

Derives what include/dotref.hpp WOULD contain from the two authorities dotref is
meant to reflect -- the central command registry (src/cli/shell_commands.cpp) and
the per-command @dottalk.usage contracts -- then diffs that against the curated
dotref.hpp. REPORT-ONLY: it never writes dotref.hpp. It emits (1) a coverage
report and (2) ready-to-review candidate Item lines for any native command that
has a contract but no dotref entry.

Routing (handler prefix -> authority):
  cmd_ / edu_ / app_ handler   -> NATIVE command    -> belongs in dotref
  a key sharing a handler with the owning command   -> alias (owner represents it)
  expression functions (function_catalog.cpp, e.g. the U* = DATE("UTC") family)
    are NOT in the registry, so they never appear here -- SYSFUNC owns them.

This is the GENERATE step of generate -> review -> promote. Later milestones:
  M2 diff curated wording (flag dotref summaries that drifted from the contract),
  M3 emit a full candidate dotref.hpp + gate promotion on refcheck_v1 (no phantoms).

Owner: member.derald . lane: AIF-067 (dotref-automation) . status: candidate
"""
from __future__ import annotations
import argparse
import re
from collections import defaultdict
from pathlib import Path

REG_RE = re.compile(r'registry\(\)\.add\(\s*"([^"]+)"\s*,\s*\[\][^{]*\{([^{}]*)\}')
HANDLER_RE = re.compile(r'\b([a-z]+)_([A-Za-z0-9_]+)\s*\(')
NAME_RE = re.compile(r'\{\s*"([^"]+)"')
NATIVE_PREFIXES = ("cmd", "edu", "app")


def norm(s: str) -> str:
    return s.upper().replace(" ", "").replace("_", "")


def registry(root: Path) -> dict[str, tuple[str, str]]:
    """KEY -> (handler_prefix, handler_base), e.g. 'EDIT' -> ('cmd','EDIT')."""
    text = (root / "src/cli/shell_commands.cpp").read_text(encoding="utf-8", errors="replace")
    out: dict[str, tuple[str, str]] = {}
    for key, body in REG_RE.findall(text):
        m = HANDLER_RE.search(body)
        out[key] = (m.group(1), m.group(2)) if m else ("", "")
    return out


def _field(b: str, k: str) -> str:
    m = re.search(rf"(?m)^\s*// {k}:\s*(.+?)\s*$", b)
    return m.group(1).strip() if m else ""


def _summary(b: str) -> str:
    grab, parts = False, []
    for ln in b.splitlines():
        if not grab:
            h = re.match(r"^\s*// summary:\s*(.*?)\s*$", ln)
            if h:
                grab = True
                if h.group(1):
                    parts.append(h.group(1))
            continue
        if re.match(r"^\s*//\s*$", ln) or re.match(r"^\s*// [a-z-]+:", ln):
            break
        parts.append(re.sub(r"^\s*//\s+", "", ln).rstrip())
    return " ".join(p for p in parts if p).strip()


def _syntax(b: str, cmd: str) -> str:
    """First non-trivial line under `usage:` (the compact syntax dotref wants)."""
    grab = False
    for ln in b.splitlines():
        if not grab:
            if re.match(r"^\s*// usage:\s*$", ln):
                grab = True
            continue
        m = re.match(r"^\s*//\s+(\S.*?)\s*$", ln)
        if not m:
            break
        s = m.group(1)
        if s.upper() in (cmd.upper(), f"{cmd.upper()} USAGE"):
            continue
        return s
    return cmd


def usage_contracts(root: Path) -> dict[str, dict]:
    """NORM(command) -> {name, summary, syntax, status, src}."""
    out: dict[str, dict] = {}
    src = root / "src"
    for p in sorted(src.rglob("*.cpp")) + sorted(src.rglob("*.hpp")):
        text = p.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        for blk in re.finditer(r"(?ms)^// @dottalk\.usage.*?(?=^// @dottalk\.usage|^\s*(?!//)\S|\Z)", text):
            b = blk.group(0)
            cmd = _field(b, "command")
            summ = _summary(b)
            if not (cmd and summ):
                continue
            for name in (n.strip() for n in cmd.split("/")):
                if name:
                    out.setdefault(norm(name), {
                        "name": name, "summary": summ, "syntax": _syntax(b, name),
                        "status": _field(b, "status"), "src": p.relative_to(root).as_posix(),
                    })
    return out


def _cstr(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()

    reg = registry(root)
    usage = usage_contracts(root)
    dref = {norm(n) for n in NAME_RE.findall((root / "include/dotref.hpp").read_text(encoding="utf-8", errors="replace"))}

    native = {k: v for k, v in reg.items() if v[0] in NATIVE_PREFIXES}
    by_handler: dict[str, list[str]] = defaultdict(list)
    for k, (_p, base) in native.items():
        by_handler[base].append(k)

    missing: list[tuple[str, dict | None]] = []
    for k, (_p, base) in sorted(native.items()):
        if norm(k) in dref:
            continue
        # covered if a sibling on the same handler already lives in dotref (alias)
        if any(norm(o) in dref for o in by_handler[base] if o != k):
            continue
        missing.append((k, usage.get(norm(k)) or usage.get(norm(base))))

    print("== dotref autogen (report-only, milestone 1) ==")
    print(f"registry commands : {len(reg)}")
    print(f"native (cmd/edu/app) : {len(native)}")
    print(f"dotref entries    : {len(dref)}")
    print(f"usage contracts   : {len(usage)}")
    print(f"native commands missing a dotref entry (candidates): {len(missing)}\n")
    if not missing:
        print("dotref is complete for native commands -- nothing to generate.")
        return 0
    print("candidate dotref Item lines (review, then paste / promote):")
    for k, c in missing:
        if c:
            print(f'        {{"{k}", "{_cstr(c["syntax"])}", "{_cstr(c["summary"])}", true}},   // from {c["src"]}')
        else:
            print(f'        {{"{k}", "{k}", "TODO: no @dottalk.usage contract found", true}},   // NEEDS CONTRACT')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
