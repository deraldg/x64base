#!/usr/bin/env python3
"""Step 1 of the fullstack push: is the source still the source of truth?

Owner: member.derald. Author: member.ai.claude.cowork. 2026-08-22.
Python 3 stdlib only, per AIF-085.

Source self-documentation is what the doc generators read. A file without a
contract is not "undocumented" to them -- it is INVISIBLE, which is worse,
because the pass completes and reports success while silently covering less
than it did last time. This audit exists so that shrinkage is loud.

Three questions, and they are deliberately separate:

  1. Does every C++ file carry `@dottalk.file`?
  2. Does every command file carry `@dottalk.usage`?
  3. Is every command it declares registered in `include/dotref.hpp`, so
     CMDHELP can generate a help page for it?

A file can pass 1 and fail 3. That combination is the dangerous one: the file
looks annotated, the generator reads it, and the command still has no help
page because nothing pointed CMDHELP at it.

EXEMPTIONS ARE DECLARED IN THE SOURCE, NOT HERE
  A file block carrying `layer: helper`, or a legacy usage block carrying
  `status: implementation-helper`, is exempt from the usage and dotref checks.
  Such a file deliberately does not own a command. The exemption travels with
  the file rather than living in this script, so moving the file cannot
  silently change its obligations.

USAGE
  python tools/selfdoc/audit_contracts.py            # report, exit 0
  python tools/selfdoc/audit_contracts.py --strict   # exit 1 if anything fails
  python tools/selfdoc/audit_contracts.py --root DIR # measure a named checkout
"""

import os
import re
import sys

ROOTS = ("src", "include", "gui", "bindings")
EXTS = (".cpp", ".hpp", ".h")
DOTREF = os.path.join("include", "dotref.hpp")

# `{"NAME", "TOPIC", "text", bool}` -- the first field is the command name.
DOTREF_ENTRY = re.compile(r'\{\s*"([A-Z][A-Z0-9_]*)"\s*,')

FILE_TAG = "@dottalk.file"
USAGE_TAG = "@dottalk.usage"
CMD_FIELD = re.compile(r'^\s*//\s*command:\s*(.+?)\s*$', re.M)
STATUS_FIELD = re.compile(r'^\s*//\s*status:\s*(.+?)\s*$', re.M)
LAYER_FIELD = re.compile(r'^\s*//\s*layer:\s*(.+?)\s*$', re.M)


def comment_block(text, tag):
    """Return one tagged line-comment block, ending at the first code line."""
    lines = text.split("\n")
    start = next((n for n, ln in enumerate(lines) if tag in ln), None)
    if start is None:
        return ""
    out = []
    for ln in lines[start:]:
        stripped = ln.strip()
        if stripped.startswith("//"):
            out.append(ln)
        elif stripped == "":
            continue
        else:
            break
    return "\n".join(out)


def usage_block(text):
    """The @dottalk.usage block ONLY -- from its tag to the first non-comment line.

    Scanning the whole file for `command:` and `status:` is wrong twice, and the
    first cut of this tool did it both ways:

      cmd_buildlmdb.cpp:34 declares `command: BUILDLMDB`, and line 278 carries
      `// command:` with an empty value inside a prose ASCII diagram 244 lines
      further down. A whole-file scan read the diagram and reported the file as
      declaring a command named "//".

      cmd_setpath.cpp carries TWO `status:` fields -- `supported` in its
      @dottalk.file block and `implementation-helper` in its @dottalk.usage
      block. A whole-file scan takes the first, so the helper exemption never
      fired and the audit reported 0 helpers when the repository has several.

    Both bugs share one cause: reading a structured field from unstructured
    context. Bound the block first, then read fields inside it.

    THIRD BUG, IN THIS FUNCTION, CAUGHT BY DISTRUSTING ITS OWN GOOD NEWS
      The first cut sliced with `text.find(USAGE_TAG)`, which starts mid-line at
      "@dottalk.usage v1" -- WITHOUT the leading "//". The very first line then
      failed the startswith("//") test, the loop broke immediately, and every
      block came back 0 bytes. The audit reported "commands NOT in dotref: 0",
      down from 3, and that read as a fix having worked. It had erased two real
      findings: APPGUI and TRANSACTION are genuinely absent from dotref.hpp.

      Slice from the START OF THE LINE holding the tag. And note what caught it:
      not the code, but refusing to accept a number that improved after a change
      that was not supposed to improve it.

    FOURTH BUG, SAME FAMILY, AND THE ONE THAT SURVIVED THREE FIXES
      This returned only the FIRST block. A file may carry SEVERAL
      `@dottalk.usage v1` blocks -- one per command it owns -- and 20+ files do;
      `cmd_aggs.cpp` has five, one each for SUM/AVG/MIN/MAX. Every declaration
      after the first was invisible to this audit: 18 of them, measured
      2026-08-26, including `TRANSACTION` in `cmd_transaction.cpp` block 2,
      which is genuinely absent from dotref.

      Found because the maintainer pasted `cmd_dotscript.cpp` and its second
      block was visible in the paste but not in this tool's output. The three
      earlier bugs in this function all had the same shape -- a bound taken from
      the wrong place -- and each fix narrowed the window without asking whether
      the window should be singular at all.

      `usage_blocks` (plural) is now the authority. `usage_block` is kept for the
      helper-status check, which reads the FIRST block deliberately: a file's own
      exemption belongs to its primary contract, not to a supplemental one.
    """
    return comment_block(text, USAGE_TAG)


def usage_blocks(text):
    """EVERY @dottalk.usage block in the file, in order. See usage_block's
    fourth-bug note for why this exists and why the singular form is not enough.
    """
    lines = text.split("\n")
    out = []
    for n, ln in enumerate(lines):
        if USAGE_TAG not in ln:
            continue
        blk = []
        for cur in lines[n:]:
            stripped = cur.strip()
            if stripped.startswith("//"):
                blk.append(cur)
            elif stripped == "":
                continue
            else:
                break
        out.append("\n".join(blk))
    return out


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def dotref_names(root):
    text = read(os.path.join(root, DOTREF))
    if not text:
        return None                      # absent is NOT the same as empty
    return set(DOTREF_ENTRY.findall(text))


def is_command_file(rel):
    base = os.path.basename(rel)
    return base.endswith(".cpp") and (base.startswith("cmd_") or base.startswith("app_"))


def walk(root):
    out = []
    for r in ROOTS:
        base = os.path.join(root, r)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for f in sorted(files):
                if f.endswith(EXTS):
                    full = os.path.join(dirpath, f)
                    out.append(os.path.relpath(full, root).replace("\\", "/"))
    return sorted(out)


def audit(root):
    """Measure file, usage, and dotref coverage without printing or exiting."""
    names = dotref_names(root)
    if names is None:
        return None

    files = walk(root)
    no_file, no_usage, unregistered, helpers = [], [], [], []

    for rel in files:
        text = read(os.path.join(root, rel))
        if FILE_TAG not in text:
            no_file.append(rel)
        if not is_command_file(rel):
            continue
        file_block = comment_block(text, FILE_TAG)
        layer = LAYER_FIELD.search(file_block)
        if layer and layer.group(1).strip().lower() == "helper":
            helpers.append(rel)
            continue
        if USAGE_TAG not in text:
            no_usage.append(rel)
            continue
        block_text = usage_block(text)
        status = STATUS_FIELD.search(block_text)
        if status and "implementation-helper" in status.group(1):
            helpers.append(rel)
            continue
        # EVERY block, not just the first -- see usage_block's fourth-bug note.
        # A supplemental block declaring its own `command:` is a declaration like
        # any other, and 18 of them were unchecked until 2026-08-26.
        seen_here = set()
        for blk in usage_blocks(text):
            for m in CMD_FIELD.finditer(blk):
                for cmd in re.split(r'[,\s|]+', m.group(1).strip()):
                    cmd = cmd.strip().upper()
                    if cmd and cmd not in names and cmd not in seen_here:
                        seen_here.add(cmd)
                        unregistered.append((rel, cmd))

    return {
        "files": files,
        "dotref_names": names,
        "helpers": helpers,
        "no_file": no_file,
        "no_usage": no_usage,
        "unregistered": unregistered,
    }


def main(argv):
    root = os.getcwd()
    if "--root" in argv:
        index = argv.index("--root")
        if index + 1 >= len(argv):
            print("FAIL: --root requires a directory")
            return 2
        root = os.path.abspath(argv[index + 1])
    strict = "--strict" in argv
    result = audit(root)
    if result is None:
        print("FAIL: %s not found. Refusing to report a clean dotref check "
              "against a file that is not there." % DOTREF)
        return 2

    files = result["files"]
    names = result["dotref_names"]
    helpers = result["helpers"]
    no_file = result["no_file"]
    no_usage = result["no_usage"]
    unregistered = result["unregistered"]

    print("=== contract audit ===")
    print("  C++ files scanned      : %d" % len(files))
    print("  dotref.hpp entries     : %d" % len(names))
    print("  declared helpers       : %d  (exempt from the dotref check by their own header)"
          % len(helpers))
    print()

    def block(title, rows, fmt=lambda x: x):
        print("  %-44s %d" % (title, len(rows)))
        for r in rows:
            print("      %s" % fmt(r))
        if rows:
            print()

    block("files with NO @dottalk.file", no_file)
    block("command files with NO @dottalk.usage", no_usage)
    block("commands NOT in dotref.hpp (no help page)", unregistered,
          lambda t: "%-52s declares %s" % (t[0], t[1]))

    bad = len(no_file) + len(no_usage) + len(unregistered)
    print("SUMMARY file_missing=%d usage_missing=%d unregistered=%d helpers=%d"
          % (len(no_file), len(no_usage), len(unregistered), len(helpers)))
    if bad == 0:
        print("  PASS -- every file carries a contract and every declared command is registered.")
        return 0
    print("  %d problem(s). A missing contract makes a file INVISIBLE to the doc" % bad)
    print("  pass, not merely undocumented: the generator still reports success.")
    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
