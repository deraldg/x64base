#!/usr/bin/env python3
"""shortcut_target_gate.py -- every ShortcutResolver target must name a real command.

Origin (AIF-074, 2026-07-29): four shortcuts -- SM, SMART, SB, WS -- expanded to
SMARTBROWSE / SIMPLEBROWSE, which are registered NOWHERE. The registry only has
SMARTBROWSER / SIMPLEBROWSER. Typing SM produced "Unknown command: SMARTBROWSE".

The defect survived because BOTH reference tables (dotref.hpp, foxref.hpp) and the
Turbo Vision menu documented the shortcuts as working, so every source of truth a
reader would consult AGREED with the maintainer's memory and disagreed with the
binary. Nothing tested that a shortcut's target resolves to a registered command.
This gate is that test. It is pure static analysis -- no build, no runtime.

Usage:
  python tools/staging/shortcut_target_gate.py [repo_root]

Exit codes:
  0  every shortcut target is registered
  1  at least one target is unregistered (with near-match suggestions)
  2  could not parse the inputs (treated as a hard failure -- a gate that
     cannot see its subject must not report success)
"""

import os
import re
import sys


def repo_root_from_argv() -> str:
    return os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def collect_shortcuts(root: str):
    """Return [(shortcut, target)] from the ShortcutResolver map literal."""
    path = os.path.join(root, "src", "cli", "shortcut_resolver.hpp")
    if not os.path.isfile(path):
        return None, "shortcut_resolver.hpp not found at " + path
    text = read(path)
    start = text.find("map = {")
    end = text.find("return map;")
    if start < 0 or end < 0 or end <= start:
        return None, "could not locate the map literal in shortcut_resolver.hpp"
    body = text[start:end]
    pairs = re.findall(r'\{\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\}', body)
    if not pairs:
        return None, "map literal parsed but contained no entries"
    return pairs, None


def collect_registered(root: str):
    """Return the set of command names the shell registry actually registers."""
    names = set()
    src = os.path.join(root, "src")
    for dirpath, _dirs, files in os.walk(src):
        for name in files:
            if not name.endswith(".cpp"):
                continue
            text = read(os.path.join(dirpath, name))
            for m in re.findall(r'registry\(\)\.add\(\s*"([^"]+)"', text):
                names.add(m.upper())
            for m in re.findall(r'add_alias\(\s*"([^"]+)"', text):
                names.add(m.upper())
    return names


def is_resolvable(target: str, registered: set) -> bool:
    t = target.upper()
    # A target may name a command directly, an underscore form, or a
    # multi-word form whose FIRST token is the registered command.
    return t in registered or t.replace(" ", "_") in registered or t.split()[0] in registered


def near_matches(target: str, registered: set, limit: int = 4):
    t = target.upper().replace(" ", "")
    if len(t) < 4:
        return []
    hits = [r for r in registered if r[:5] == t[:5]]
    return sorted(hits)[:limit]


def main() -> int:
    root = repo_root_from_argv()
    pairs, err = collect_shortcuts(root)
    if err:
        print("SHORTCUT GATE: CANNOT VERIFY -- " + err)
        print("  A gate that cannot see its subject reports failure, not success.")
        return 2

    registered = collect_registered(root)
    if not registered:
        print("SHORTCUT GATE: CANNOT VERIFY -- no registry().add(...) calls found under src/")
        return 2

    bad = [(k, v) for k, v in pairs if not is_resolvable(v, registered)]

    if not bad:
        print("SHORTCUT GATE: PASS -- {0}/{0} shortcut targets resolve "
              "against {1} registered commands.".format(len(pairs), len(registered)))
        return 0

    print("SHORTCUT GATE: FAIL -- {0} of {1} shortcut target(s) name no registered command."
          .format(len(bad), len(pairs)))
    print("  A shortcut whose target is unregistered expands to an unknown command,")
    print("  so the user sees a confusing error naming a command they never typed.")
    print("")
    for k, v in bad:
        line = '  {0:<14} -> "{1}"  NOT REGISTERED'.format(k, v)
        cand = near_matches(v, registered)
        if cand:
            line += "   did you mean: " + ", ".join(cand)
        print(line)
    print("")
    print("  Fix the target in src/cli/shortcut_resolver.hpp, and check that the")
    print("  reference tables (include/dotref.hpp, include/foxref.hpp) agree.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
