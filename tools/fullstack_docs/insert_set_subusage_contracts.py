#!/usr/bin/env python3
"""
AIF-067 M1 -- insert @dottalk.subusage v1 contract blocks into the SET ladder.

WHY THIS IS A SCRIPT AND NOT 31 HAND EDITS
    The blocks are hand-authored (see CONTRACTS below); only the INSERTION is
    mechanical. Doing the insertion by hand 31 times is how anchors drift.
    Re-running is safe: a block is skipped if its arm already carries one.

AUTHORITY NOTE
    Every `usage:` line below was derived by reading the PARSING CODE of its
    ladder arm, not by copying `MessageId::SetUsageText`. That literal is the
    drifted artifact this lane exists to retire (AIF-067 sec 3); copying it
    would launder the defect into the contract layer and the guard would then
    agree with itself forever.

BUILD GATES ARE PART OF THE CONTRACT
    Nine arms sit behind #if guards. `SetUsageText` lists them unconditionally,
    so a build without DOTTALK_WITH_DEV advertises SET FILTER / SET RELATION /
    SET RELATIONS while dispatching none of them. `build-gate:` records the
    condition so the generator can mark the row conditional rather than absent.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TARGET = Path("src/cli/cmd_set.cpp")

# (anchor_predicate, fields, summary_lines, usage_lines)
# `anchor` is the exact source text of the arm's `if` line, matched verbatim.
CONTRACTS: list[dict] = [
    dict(
        anchor='if (opt == "USAGE" || opt == "HELP" || opt == "?") {',
        sub="USAGE", aliases="HELP; ?", category="help", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Print the SET subcommand surface. Also the bare-SET behaviour:",
                 "SET with no option prints the same text."],
        usage=["SET", "SET USAGE", "SET HELP", "SET ?"],
    ),
    dict(
        anchor='if (opt == "LANGUAGE" || opt == "LOCALE") {',
        sub="LANGUAGE", aliases="LOCALE", category="locale", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Select the active message-rendering locale. Does NOT localize",
                 "command keywords; it selects message text templates (AIF-066).",
                 "Bare form reports current locale rather than erroring."],
        usage=["SET LANGUAGE",
               "SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>",
               "SET LANGUAGE CHECK|VALIDATE|CATALOG",
               "SET LANGUAGE REPORT|EXPORT [locale]",
               "SET LANGUAGE STATUS"],
    ),
    dict(
        anchor='if (opt == "MESSAGE") {',
        sub="MESSAGE", aliases="", category="messaging", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Inspect and exercise the message catalog: provider status,",
                 "routing proof, and single-symbol emission for a given locale."],
        usage=["SET MESSAGE CATALOG CHECK|STATUS",
               "SET MESSAGE PROOF <args>",
               "SET MESSAGE EMIT <symbol> [LOCALE <locale>]"],
    ),
    dict(
        anchor='if (opt == "TABLE") {',
        sub="TABLE", aliases="", category="buffer", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Enable or disable table buffering for the current work area, or",
                 "for every open area with ALL. Requires an engine; reports the",
                 "area number it acted on."],
        usage=["SET TABLE BUFFER ON|OFF", "SET TABLE BUFFER ON|OFF ALL"],
    ),
    dict(
        anchor='if (opt == "CONSOLE") {',
        sub="CONSOLE", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Fox-style alias for PRN TO CONSOLE / PRN TO NULL."],
        usage=["SET CONSOLE ON|OFF"],
    ),
    dict(
        anchor='if (opt == "PRINT") {',
        sub="PRINT", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Fox-style alias for PRN TO FILE / PRN OFF. SET PRINT ON with no",
                 "prior TO <file> reports that a file is required rather than",
                 "silently doing nothing."],
        usage=["SET PRINT ON|OFF", "SET PRINT TO <file>"],
    ),
    dict(
        anchor='if (opt == "ALTERNATE") {',
        sub="ALTERNATE", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Echo session output to a secondary transcript file."],
        usage=["SET ALTERNATE ON|OFF", "SET ALTERNATE TO <file>"],
    ),
    dict(
        anchor='if (opt == "TALK") {',
        sub="TALK", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Show or suppress per-command progress chatter."],
        usage=["SET TALK ON|OFF"],
    ),
    dict(
        anchor='if (opt == "ECHO") {',
        sub="ECHO", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Echo each input line before executing it. Primarily for scripts."],
        usage=["SET ECHO ON|OFF"],
    ),
    dict(
        anchor='if (opt == "PAGING") {',
        sub="PAGING", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Page long output at the console."],
        usage=["SET PAGING ON|OFF"],
    ),
    dict(
        anchor='if (opt == "WRAP") {',
        sub="WRAP", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Wrap output lines at the console width instead of truncating."],
        usage=["SET WRAP ON|OFF"],
    ),
    dict(
        anchor='if (opt == "DEVDIAG") {',
        sub="DEVDIAG", aliases="", category="diagnostics", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Control PASSIVE startup/shutdown/relation diagnostics in dev",
                 "builds. Explicit command traces stay under their own surfaces.",
                 "Bare form reports current state."],
        usage=["SET DEVDIAG", "SET DEVDIAG ON|OFF", "SET DEVDIAG STATUS|CHECK"],
    ),
    dict(
        anchor='if (opt == "TIMER") {',
        sub="TIMER", aliases="", category="diagnostics", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Report elapsed time per command. Routed through the canonical",
                 "executor so in-script timing matches interactive timing."],
        usage=["SET TIMER ON|OFF"],
    ),
    dict(
        anchor='if (opt == "POLLING") {',
        sub="POLLING", aliases="", category="diagnostics", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Enable background polling behaviour."],
        usage=["SET POLLING ON|OFF"],
    ),
    dict(
        anchor='if (opt == "DELETED") {',
        sub="DELETED", aliases="", category="navigation", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Hide (ON) or show (OFF) records flagged deleted. Note the sense:",
                 "ON means HIDE, which the status line spells out because the",
                 "polarity is a routine source of confusion."],
        usage=["SET DELETED ON|OFF"],
    ),
    dict(
        anchor='if (opt == "INDEXTXN") {',
        sub="INDEXTXN", aliases="", category="index", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Transactional in-COMMIT index maintenance. Default OFF keeps the",
                 "legacy batch behaviour (BUILDLMDB / REBUILD / REINDEX); ON enables",
                 "incremental maintenance inside COMMIT for the active CDX/LMDB",
                 "backend. Deliberately message-catalog-free (print_line), so it is",
                 "NOT localized -- unlike its ladder siblings.",
                 "AIF-067: absent from SetUsageText, so previously undiscoverable."],
        usage=["SET INDEXTXN", "SET INDEXTXN ON|OFF",
               "SET INDEXTXN STATUS|CHECK", "SET INDEXTXN USAGE|HELP|?"],
    ),
    dict(
        anchor='if (opt == "ERRORSTOP") {',
        sub="ERRORSTOP", aliases="", category="script", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Compatibility form of the native STOP_ON_ERROR command. Sets the",
                 "severity at which a running DotScript aborts, compared against the",
                 "severity carried by the recorded canonical error code. Strips an",
                 "inline && comment before parsing. Bare form reports the threshold.",
                 "AIF-067: absent from SetUsageText, so previously undiscoverable."],
        usage=["SET ERRORSTOP", "SET ERRORSTOP [TO] OFF|WARNING|ERROR"],
    ),
    dict(
        anchor='if (opt == "CASE" || opt == "SETCASE") {',
        sub="CASE", aliases="SETCASE", category="settings", tier="public",
        disp="routed", handler="cmd_SETCASE", gate="",
        summary=["Fox-style spelling routed to the SETCASE handler. Direct SETCASE",
                 "remains independently registered in the command registry, which is",
                 "why it resolves through two paths."],
        usage=["SET CASE ON|OFF"],
    ),
    dict(
        anchor='if (opt == "NEAR" || opt == "SETNEAR") {',
        sub="NEAR", aliases="SETNEAR", category="navigation", tier="public",
        disp="routed", handler="cmd_SETNEAR", gate="",
        summary=["SEEK stays exact while NEAR is OFF. When ON, SEEK/FIND may use",
                 "nearest greater-or-equal ordered-key behaviour."],
        usage=["SET NEAR ON|OFF"],
    ),
    dict(
        anchor='if (opt == "EDITOR") {',
        sub="EDITOR", aliases="", category="settings", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Choose the external editor. TO is REQUIRED here, unlike LANGUAGE",
                 "or ERRORSTOP where it is optional."],
        usage=["SET EDITOR TO <command>", "SET EDITOR TO DEFAULT", "SET EDITOR TO OFF"],
    ),
    dict(
        anchor='if (opt == "DEVICE") {',
        sub="DEVICE", aliases="", category="output", tier="public",
        disp="inline", handler="cmd_SET", gate="",
        summary=["Fox-style alias for PRN. TO is required. PRINTER with no name",
                 "stages the default printer.",
                 "CONSOLE is accepted as a synonym for SCREEN, and OFF for NULL;",
                 "neither synonym appears in SetUsageText."],
        usage=["SET DEVICE TO SCREEN|CONSOLE",
               "SET DEVICE TO FILE <path>",
               "SET DEVICE TO PRINTER [name]",
               "SET DEVICE TO NULL|OFF"],
    ),
    dict(
        anchor='if (opt == "UNIQUE") {',
        sub="UNIQUE", aliases="", category="index", tier="public",
        disp="routed", handler="cmd_SET_UNIQUE", gate="",
        summary=["Routed to the SET_UNIQUE handler; see that command for argument",
                 "detail."],
        usage=["SET UNIQUE FIELD <name> ON|OFF"],
    ),
    dict(
        anchor='if (opt == "PATH") {',
        sub="PATH", aliases="", category="workspace", tier="public",
        disp="routed", handler="cmd_SETPATH", gate="",
        summary=["Routed to the SETPATH handler. Governs the DBF path protocol:",
                 "SETPATH DBF <dir> then BARE table names."],
        usage=["SET PATH <slot> <path>"],
    ),
    dict(
        anchor='if (opt == "INDEX") {',
        sub="INDEX", aliases="", category="index", tier="public",
        disp="routed", handler="cmd_SETINDEX", gate="DOTTALK_HAS_XINDEX",
        summary=["Routed to the SETINDEX handler. Present only when the index",
                 "subsystem is compiled in."],
        usage=["SET INDEX TO <file>"],
    ),
    dict(
        anchor='if (opt == "ORDER") {',
        sub="ORDER", aliases="", category="index", tier="public",
        disp="routed", handler="cmd_SETORDER", gate="DOTTALK_HAS_XINDEX",
        summary=["Routed to the SETORDER handler. Tag 0 clears the controlling",
                 "order. Present only when the index subsystem is compiled in."],
        usage=["SET ORDER TO <tag|0>"],
    ),
    dict(
        anchor='if (opt == "FILTER") {',
        sub="FILTER", aliases="", category="navigation", tier="developer",
        disp="routed", handler="cmd_SETFILTER", gate="DOTTALK_WITH_DEV",
        summary=["Routed to the SETFILTER handler. Developer/transitional surface."],
        usage=["SET FILTER TO <expr>"],
    ),
    dict(
        anchor='if (opt == "RELATION") {',
        sub="RELATION", aliases="", category="relations", tier="developer",
        disp="routed", handler="cmd_SET_RELATION", gate="DOTTALK_WITH_DEV",
        summary=["Singular form, routed to cmd_SET_RELATION. Distinct handler from",
                 "the plural SET RELATIONS -- they are not spellings of one another."],
        usage=["SET RELATION <args...>"],
    ),
    dict(
        anchor='if (opt == "RELATIONS") {',
        sub="RELATIONS", aliases="", category="relations", tier="developer",
        disp="routed", handler="cmd_SET_RELATIONS", gate="DOTTALK_WITH_DEV",
        summary=["Plural form, routed to cmd_SET_RELATIONS. Distinct handler from",
                 "the singular SET RELATION."],
        usage=["SET RELATIONS <args...>"],
    ),
    dict(
        anchor='if (opt == "CNX") {',
        sub="CNX", aliases="", category="index", tier="developer",
        disp="routed", handler="cmd_SETCNX", gate="DOTTALK_HAS_XINDEX",
        summary=["Available in BOTH legacy and LMDB index profiles, unlike CDX and",
                 "LMDB which are LMDB-profile only."],
        usage=["SET CNX [TO] <container.cnx>"],
    ),
    dict(
        anchor='if (opt == "CDX") {',
        sub="CDX", aliases="", category="index", tier="developer",
        disp="routed", handler="cmd_SETCDX", gate="DOTTALK_WITH_INDEX",
        summary=["LMDB-index-profile command, routed to the SETCDX handler."],
        usage=["SET CDX [TO] <container.cdx>"],
    ),
    dict(
        anchor='if (opt == "LMDB") {',
        sub="LMDB", aliases="", category="index", tier="developer",
        disp="routed", handler="cmd_SETLMDB", gate="DOTTALK_WITH_INDEX",
        summary=["LMDB-index-profile command, routed to the SETLMDB handler.",
                 "See AIF-065 for the mapsize ladder defect on the writer side."],
        usage=["SET LMDB <args...>"],
    ),
]


def render(c: dict) -> str:
    L = ["// @dottalk.subusage v1",
         "// parent: SET",
         f"// sub: {c['sub']}"]
    if c["aliases"]:
        L.append(f"// aliases: {c['aliases']}")
    L += [f"// category: {c['category']}",
          f"// tier: {c['tier']}",
          "// status: supported",
          f"// disp-style: {c['disp']}",
          f"// handler: {c['handler']}"]
    if c["gate"]:
        L.append(f"// build-gate: {c['gate']}")
    L.append("// usage-access: SET USAGE")
    L.append("// summary:")
    L += [f"//   {s}" for s in c["summary"]]
    L.append("// usage:")
    L += [f"//   {u}" for u in c["usage"]]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true",
                    help="apply; default is a dry run that only reports")
    a = ap.parse_args()

    path = Path(a.root) / TARGET
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    lines = text.split("\n")

    inserted = skipped = missing = 0
    for c in CONTRACTS:
        hits = [i for i, l in enumerate(lines) if l.strip() == c["anchor"]]
        if len(hits) != 1:
            print(f"  MISSING/AMBIGUOUS ({len(hits)}): SET {c['sub']}")
            missing += 1
            continue
        i = hits[0]
        # Idempotence: walk back over the contiguous comment run above the arm.
        j = i - 1
        while j >= 0 and (lines[j].strip().startswith("//") or not lines[j].strip()):
            if "@dottalk.subusage" in lines[j]:
                break
            j -= 1
        if j >= 0 and "@dottalk.subusage" in lines[j]:
            skipped += 1
            continue

        indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
        block = "\n".join(indent + b for b in render(c).split("\n"))
        lines.insert(i, block)
        inserted += 1

    print(f"contracts: {len(CONTRACTS)}  inserted {inserted}  "
          f"already-present {skipped}  unmatched {missing}")
    if missing:
        print("REFUSING to write: an anchor did not match exactly once.")
        return 2
    if a.write:
        path.write_text("\n".join(lines), encoding="utf-8", errors="surrogateescape")
        print(f"wrote {path}")
    else:
        print("dry run -- pass --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
