#!/usr/bin/env python3
"""contract_inventory.py -- the Command Contract Inventory, reproducibly.

WHAT THIS IS FOR
    The inventory published on 2026-09-13 was a good artifact built on two bad
    foundations, and both are fixed here rather than argued about:

      1. IT CUT THE "RECENT" WINDOW BY FILE MTIME. mtime counts a touch that
         changed nothing, counts an agent's own write, and resets on a checkout.
         `--since` here is handed to `git log`, so the window is COMMITS.

      2. IT TOOK ITS CENSUS FROM THE FILESYSTEM. Measured the same day: a
         staged copy of src/cli held 447 top-level files where the live tree
         held ~340 -- deleted files that a filesystem walk happily reports as
         present. The census here is `git ls-files`, so a file git does not
         track cannot enter the inventory.

    Everything else follows from those two. The output is deterministic: sorted
    keys, no clock in the payload except one explicit provenance block, so two
    runs on the same commit produce byte-identical JSON and the harvest phase
    can diff them.

MODES

  inventory   Emit the curated inventory (JSON always; Markdown and HTML on
              request) from the @dottalk.usage v1 blocks in tracked source.

  drift       Compare the contracts CURRENTLY IN SOURCE against the contracts
              SAVED IN THE HELP STORE (HELP_ARTIFACTS.dbf rows where
              SOURCE='USAGE_CONTRACT'). This is the gate that went missing:
              neither audit-drift.ps1 (tree parity dev<->main) nor
              prepush_gate.py (staged change set) looks at documentation
              contracts at all, so a usage block can be rewritten and published
              while the store still serves the old text. Exit 2 on drift.

THE EXTRACTOR IS A PORT, NOT A GUESS
    extract_blocks() and parse_contract() follow
    src/help/helpdata_source_miner.cpp -- extract_usage_contract_blocks() at
    ~line 1061 and parse_usage_contract() at ~line 1165. Where this file and
    that file disagree, that file is right and this one is the defect. The
    section-name set, the normalize_token rule (dash -> underscore, upper) and
    the envelope keys that must NOT continue the previous section are copied
    from it deliberately.

USAGE
  python contract_inventory.py inventory --source-root D:\\code\\ccode \\
      --since "7 days ago" \\
      --out-json tmp\\contract_inventory.json \\
      --out-md   tmp\\CONTRACT_INVENTORY.md \\
      --out-html tmp\\contract_inventory.html

  python contract_inventory.py drift --source-root D:\\code\\ccode \\
      --store D:\\code\\ccode\\dottalkpp\\data\\help
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
import struct
import subprocess
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

MARKER = "@dottalk.usage v1"
# THE VOLUNTARY MARKER IS NOT A CONTRACT AND IS NOT MINED BY ANYTHING.
# "@dottalk.usage.voluntary v1" does not CONTAIN "@dottalk.usage v1" -- the
# ".voluntary" sits between -- so helpdata_source_miner.cpp's find() never sees
# it, and neither does this tool's extractor. Measured 2026-09-13: these blocks
# reach no store, no HELP topic and no published page. They are a SEPARATE
# CENSUS here, listed rather than counted in with contracts, because "offered
# not promised" is a real distinction and promoting one to contract is an
# owner ruling, not a tooling decision.
VOLUNTARY_MARKER = "@dottalk.usage.voluntary"
END_TOKENS = {"@DOTTALK.END", "@DOTTALK.CONTRACT.END"}

# src/help/helpdata_source_miner.cpp:1130 is_contract_section_name
SECTION_NAMES = {
    "USAGE", "SYNTAX", "EXAMPLES", "EXAMPLE", "NOTES", "NOTE",
    "WARNINGS", "WARNING", "RELATED", "ALIASES", "ALIAS", "DETAIL", "DETAILS",
}
# Envelope/risk metadata: recorded, but must CLEAR the current section so it
# cannot be absorbed as continuation prose (miner ~1231).
ENVELOPE_KEYS = {"NOARGS", "EFFECT", "MUTATES", "USAGE_ACCESS", "RISK"}
SCALAR_KEYS = {"OWNER", "COMMAND", "CATALOG", "CATEGORY", "STATUS", "SUMMARY"}

SOURCE_EXT = {".cpp", ".hpp", ".h", ".cc", ".cxx"}

# THE SET FAMILY IS CANONICALIZED BY THE ENGINE AND WAS NOT BY THIS PORT.
# helpdata_source_miner.cpp canonicalize_set_family_command() /
# helpdata_cmdhelp_bridge.cpp canonicalize_set_family_command_local(): a
# contract that declares `command: SETPATH` is stored under `SET PATH`, with
# SETPATH recorded as an ALIAS. Omitting this made the first drift run report
# `+ DOT|SETPATH` and `- DOT|SET PATH` -- one rename where there was none, and
# four more TEXT DIFFERS that were the same lines seen twice under two keys.
# Six of the sixteen differences in the first live run were THIS BUG.
COMPACT_SET_FAMILY = {
    "SETCASE": "SET CASE",
    "SETCDX": "SET CDX",
    "SETCNX": "SET CNX",
    "SETFILTER": "SET FILTER",
    "SETINDEX": "SET INDEX",
    "SETLMDB": "SET LMDB",
    "SETNEAR": "SET NEAR",
    "SETORDER": "SET ORDER",
    "SETPATH": "SET PATH",
    "SETUNIQUE": "SET UNIQUE",
    "SET_UNIQUE": "SET UNIQUE",
}


def canonicalize_command(raw: str) -> tuple[str, str]:
    """-> (canonical, alias_or_empty). Mirrors the engine, both copies of it."""
    u = norm_token(raw)
    canon = COMPACT_SET_FAMILY.get(u)
    return (canon, u) if canon else (u, "")


def norm_token(s: str) -> str:
    return s.strip().replace("-", "_").upper()


# --------------------------------------------------------------------------- #
# extraction -- port of extract_usage_contract_blocks()
# --------------------------------------------------------------------------- #
@dataclass
class Block:
    body: str
    line_no: int          # 1-based line of the marker
    form: str             # "comment" | "rawstring" | "plain"


def extract_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    pos = 0
    while True:
        pos = text.find(MARKER, pos)
        if pos < 0:
            return blocks

        nl = text.rfind("\n", 0, pos)
        line_begin = 0 if nl < 0 else nl + 1
        marker_line_end = text.find("\n", line_begin)
        marker_end = len(text) if marker_line_end < 0 else marker_line_end
        marker_line = text[line_begin:marker_end].strip()
        line_no = text.count("\n", 0, line_begin) + 1

        if marker_line.startswith("//"):
            # Consecutive // lines. Stop at the first non-comment line, and at a
            # SECOND marker so two adjacent contracts do not merge.
            out: list[str] = []
            cursor = line_begin
            while cursor < len(text):
                nxt = text.find("\n", cursor)
                end = len(text) if nxt < 0 else nxt
                line = text[cursor:end].rstrip("\r")
                clean = line.strip()
                if not clean.startswith("//"):
                    break
                if cursor != line_begin and MARKER in clean:
                    break
                out.append(line)
                if nxt < 0:
                    cursor = len(text)
                    break
                cursor = nxt + 1
            blocks.append(Block("\n".join(out) + "\n", line_no, "comment"))
            pos = max(cursor, pos + len(MARKER) + 1)
            continue

        raw_begin = text.rfind('R"', 0, pos)
        if raw_begin >= 0:
            delim_start = raw_begin + 2
            open_paren = text.find("(", delim_start)
            if 0 <= open_paren < pos:
                delim = text[delim_start:open_paren]
                close = ")" + delim + '"'
                first_close = text.find(close, open_paren + 1)
                if first_close >= pos:
                    blocks.append(Block(text[open_paren + 1:first_close],
                                        line_no, "rawstring"))
                    pos = first_close + len(close)
                    continue

        # Plain-text fallback, bounded to the containing paragraph.
        stop = text.find("\n\n", pos)
        stop = len(text) if stop < 0 else stop
        blocks.append(Block(text[line_begin:stop], line_no, "plain"))
        pos = stop + 1


# --------------------------------------------------------------------------- #
# parsing -- port of parse_usage_contract()
# --------------------------------------------------------------------------- #
@dataclass
class Contract:
    file: str = ""
    line_no: int = 0
    form: str = ""
    owner: str = ""
    catalog: str = ""
    command: str = ""
    category: str = ""
    status: str = ""
    summary: str = ""
    aliases: list[str] = dc_field(default_factory=list)
    envelope: dict[str, str] = dc_field(default_factory=dict)
    sections: dict[str, list[str]] = dc_field(default_factory=dict)
    voluntary: bool = False

    @property
    def key(self) -> str:
        cat = self.catalog or "DOT"
        return f"{cat}|{self.command}" if self.command else ""


def parse_contract(body: str) -> Contract:
    c = Contract()
    current = ""
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("//"):
            line = line[2:].strip()
        if not line:
            continue
        if line.startswith("@dottalk.usage"):
            continue
        if line.upper() in END_TOKENS:
            break
        # ANY @dottalk. TOKEN ENDS THE CONTRACT -- the port lagging the engine.
        # helpdata_cmdhelp_bridge.cpp gained this on 2026-09-13 so an
        # @dottalk.location v1 block following a trailing `related:` stops being
        # absorbed; DOT|ABOUT went from 8 published RELATED entries to its
        # declared 2. THIS FILE DID NOT GET THE SAME RULE, so the very next drift
        # run reported DOT|ABOUT, DOT|BBOX and DOT|HELP as differing -- three of
        # its six remaining lines -- when the store was right and the reader was
        # wrong. Exactly the case the header clause covers: where this file and
        # the engine disagree, the engine is right and this is the defect.
        if line.lower().startswith("@dottalk."):
            break

        colon = line.find(":")
        if colon >= 0:
            key = norm_token(line[:colon])
            value = line[colon + 1:].strip()

            if key == "OWNER":
                c.owner = value
                bar = value.find("|")
                if bar >= 0:
                    c.catalog = norm_token(value[:bar])
                    if not c.command:
                        cmd, alias = canonicalize_command(value[bar + 1:])
                        c.command = cmd
                        if alias and alias not in c.aliases:
                            c.aliases.append(alias)
                current = ""
                continue
            if key == "COMMAND":
                cmd, alias = canonicalize_command(value)
                c.command = cmd
                if alias and alias not in c.aliases:
                    c.aliases.append(alias)
                current = ""
                continue
            if key == "CATALOG":
                c.catalog = norm_token(value)
                current = ""
                continue
            if key in ("CATEGORY", "STATUS"):
                setattr(c, key.lower(), value)
                current = ""
                continue
            # SUMMARY IS A SECTION, NOT A SCALAR, AND READING IT AS A SCALAR LOST
            # EVERY MULTI-LINE SUMMARY IN THE TREE.
            #
            # Almost every contract writes `summary:` bare and puts the text on
            # the indented lines beneath it. Assigning value (which is "") and
            # clearing the section dropped all of it: GROUPCOMMIT, WORKDESK and
            # TRANSACTION all reported an empty summary on 2026-09-13 and had to
            # be grepped out of source by hand, which is what exposed this.
            #
            # THE TWO ENGINE READERS DISAGREE HERE AND THE BRIDGE IS THE ONE TO
            # FOLLOW. helpdata_source_miner.cpp:1220 does `c.summary = value;
            # current_section.clear();` -- a scalar, so it only ever captures a
            # summary written on the SAME LINE as the key.
            # helpdata_cmdhelp_bridge.cpp:351 lists "summary" with usage/notes/
            # related as a SECTION and appends continuation lines.
            #
            # That single difference is the real explanation for a number this
            # tool reported and I mis-read: bridge 219 SUMMARY rows against the
            # miner's 4. I wrote that up as "the miner essentially doesn't emit
            # summaries." It does -- for the four commands whose summary happens
            # to sit on one line. The count was right and the reason was wrong.
            if key == "SUMMARY":
                current = "SUMMARY"
                if value:
                    c.sections.setdefault(current, []).append(value)
                continue
            if key in ENVELOPE_KEYS:
                c.envelope[key] = value
                current = ""
                continue
            if key in SECTION_NAMES:
                current = key
                if value:
                    c.sections.setdefault(current, []).append(value)
                continue

        if current:
            c.sections.setdefault(current, []).append(line)
    return c


def contracts_in_text(path_rel: str, text: str) -> list[Contract]:
    out: list[Contract] = []
    for b in extract_blocks(text):
        c = parse_contract(b.body)
        c.file, c.line_no, c.form = path_rel, b.line_no, b.form
        # The scalar stays populated from the section so every consumer of
        # .summary keeps working; a multi-line summary is joined, not truncated.
        if not c.summary:
            c.summary = " ".join(c.sections.get("SUMMARY", [])).strip()
        out.append(c)
    return out


# --------------------------------------------------------------------------- #
# git -- census and window
# --------------------------------------------------------------------------- #
def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


REGISTRY_ADD_RE = re.compile(r'registry\(\)\.add\("([^"]+)"')


def registry_keys(root: Path) -> set[str]:
    """Every name the shell registry dispatches, upper-cased.

    A CONTRACT IS NOT A REGISTRATION, and the inventory could not tell the
    difference until 2026-09-13. src/cli/cmd_transaction.cpp carries a complete
    @dottalk.usage v1 block and is a DECLARED STUB -- no cmd_TRANSACTION exists,
    nothing registers it, and its own header says the block "states the PLANNED
    surface". It counted here as a command under contract exactly like a live
    one, and on the strength of that count TRANSACTION was nearly seeded into
    include/dotref.hpp -- which would have minted the single-token phantom
    refcheck_v1.py (AIF-067 M2) exists to fail on, and published a planned
    surface as a supported command.

    Reading shell_commands.cpp is the same source refcheck_v1.py and
    command_catalog_sync.py both read. It is narrower than refcheck's full
    authority model (registry U SYSFUNC U subcommand forms), so `registered`
    below is reported as a FLAG and never as a verdict: refcheck stays the
    authority on what is a phantom.
    """
    p = root / "src/cli/shell_commands.cpp"
    if not p.exists():
        return set()
    return {m.upper() for m in REGISTRY_ADD_RE.findall(
        p.read_text(encoding="utf-8", errors="replace"))}


def tracked_sources(root: Path) -> list[str]:
    """THE CENSUS. git ls-files, not a filesystem walk."""
    files = git(root, "ls-files").splitlines()
    return sorted(f for f in files if Path(f).suffix.lower() in SOURCE_EXT)


def changed_since(root: Path, since: str) -> dict[str, dict]:
    """path -> {commits, last_date, last_subject}. THE WINDOW, from commits."""
    fmt = "%x01%H%x02%ad%x02%s"
    raw = git(root, "log", f"--since={since}", "--date=short",
              f"--pretty=format:{fmt}", "--name-only")
    out: dict[str, dict] = {}
    cur = None
    for line in raw.splitlines():
        if line.startswith("\x01"):
            _h, date, subject = line[1:].split("\x02", 2)
            cur = (date, subject)
            continue
        p = line.strip()
        if not p or cur is None:
            continue
        e = out.setdefault(p, {"commits": 0, "last_date": cur[0],
                               "last_subject": cur[1]})
        e["commits"] += 1
    return out


def head_commit(root: Path) -> dict:
    line = git(root, "log", "-1", "--date=iso-strict",
               "--pretty=format:%H%x02%ad%x02%s").strip()
    h, date, subject = line.split("\x02", 2)
    return {"sha": h, "date": date, "subject": subject}


# --------------------------------------------------------------------------- #
# HELP store reader (for drift)
# --------------------------------------------------------------------------- #
def read_dbt(path: Path) -> dict[int, str]:
    """helpdata_export_dbf.cpp DbtWriter: block 0 is the header; each payload is
    [4-byte LE length][text][0x1A] padded to 512. Block 0 means 'no memo'."""
    if not path.exists():
        return {}
    b = path.read_bytes()
    out: dict[int, str] = {}
    bs = 512
    blk = 1
    while blk * bs + 4 <= len(b):
        off = blk * bs
        (ln,) = struct.unpack_from("<I", b, off)
        if ln == 0 or off + 4 + ln > len(b):
            blk += 1
            continue
        out[blk] = b[off + 4:off + 4 + ln].decode("utf-8", "replace")
        blk += max(1, (4 + ln + 1 + bs - 1) // bs)
    return out


def read_store(help_dir: Path) -> list[dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dbfread  # the house reader; do not re-derive the layout

    dbf = help_dir / "HELP_ARTIFACTS.dbf"
    t = dbfread.read(dbf)
    memos = read_dbt(help_dir / "help_artifacts.dbt")

    def resolve(v: str) -> str:
        m = re.match(r"<memo:unresolved ptr='(\d+)'>", v or "")
        if m:
            return memos.get(int(m.group(1)), "")
        return v or ""

    rows = []
    for r in t.rows:
        rows.append({
            "cmdkey": (r.get("CMDKEY") or "").strip(),
            "command": (r.get("COMMAND") or "").strip(),
            "catalog": (r.get("CATALOG") or "").strip(),
            "kind": (r.get("KIND") or "").strip(),
            "source": (r.get("SOURCE") or "").strip(),
            "name": (r.get("NAME") or "").strip(),
            "ord": (r.get("ORD") or "").strip(),
            "text": resolve(r.get("TEXT", "")),
        })
    return rows


# --------------------------------------------------------------------------- #
# modes
# --------------------------------------------------------------------------- #
def gather(root: Path, since: str | None):
    census = tracked_sources(root)
    window = changed_since(root, since) if since else {}
    items: list[Contract] = []
    files_with = 0
    voluntary_files: list[str] = []
    for rel in census:
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if VOLUNTARY_MARKER in text:
            voluntary_files.append(rel)
        if MARKER not in text:
            continue
        files_with += 1
        items.extend(contracts_in_text(rel, text))
    return census, window, items, files_with, sorted(voluntary_files)


def to_payload(root: Path, since, census, window, items, files_with,
               voluntary_files) -> dict:
    reg = registry_keys(root)
    recs = []
    for c in sorted(items, key=lambda x: (x.file, x.line_no)):
        w = window.get(c.file)
        recs.append({
            "file": c.file,
            "line": c.line_no,
            "form": c.form,
            "key": c.key,
            "catalog": c.catalog,
            "command": c.command,
            "aliases": list(c.aliases),
            # A BLOCK WITH NO `command:` IS NOT AN UNREGISTERED COMMAND, it is
            # not a command at all -- the doc-tooling files carry contract-shaped
            # header blocks of their own. Flagging those put 11 non-commands in a
            # list of 15 and would have trained a reader to ignore the column.
            "registered": (not reg) or (not c.command)
                          or (c.command in reg)
                          or any(a in reg for a in c.aliases)
                          or c.command.split(" ")[0] in reg,
            "category": c.category,
            "status": c.status,
            "summary": c.summary,
            "envelope": dict(sorted(c.envelope.items())),
            "sections": {k: v for k, v in sorted(c.sections.items())},
            "section_counts": {k: len(v) for k, v in sorted(c.sections.items())},
            "in_window": bool(w),
            "window_commits": (w or {}).get("commits", 0),
            "window_last_date": (w or {}).get("last_date", ""),
            "window_last_subject": (w or {}).get("last_subject", ""),
        })
    ex_keys = ("EXAMPLES", "EXAMPLE")
    return {
        "provenance": {
            "tool": "tools/fullstack_docs/contract_inventory.py",
            "source_root": str(root),
            "head": head_commit(root),
            "since": since or "",
            "census": "git ls-files (NOT a filesystem walk)",
            "window": "git log --since (NOT file mtime)",
            "extractor": "port of helpdata_source_miner.cpp "
                         "extract_usage_contract_blocks/parse_usage_contract",
        },
        "totals": {
            "tracked_source_files": len(census),
            "files_with_contract": files_with,
            "contract_blocks": len(recs),
            "in_window": sum(1 for r in recs if r["in_window"]),
            "voluntary_files": len(voluntary_files),
            "no_examples": sum(1 for r in recs
                               if not any(r["section_counts"].get(k) for k in ex_keys)),
            "not_supported": sum(1 for r in recs
                                 if (r["status"] or "").lower() != "supported"),
            # A FLAG, NOT A VERDICT -- refcheck_v1.py is the authority on
            # phantoms; this only says shell_commands.cpp does not name it.
            "contract_without_registration": sum(1 for r in recs
                                                 if not r["registered"]),
            "empty_lane": sum(1 for r in recs if not r["catalog"]),
        },
        "contracts": recs,
        "voluntary_files": voluntary_files,
    }


def emit_md(p: dict) -> str:
    t, L = p["totals"], []
    L.append("# Command Contract Inventory\n")
    hd = p["provenance"]["head"]
    L.append(f"Cut at `{hd['sha'][:12]}` ({hd['date']}) — {hd['subject']}\n")
    L.append(f"Window: `git log --since={p['provenance']['since'] or '(none)'}`\n")
    L.append("| measure | count |\n|---|---|")
    for k, v in t.items():
        L.append(f"| {k.replace('_', ' ')} | {v} |")
    L.append("\n## Contracts\n")
    L.append("| command | status | category | examples | file | window |")
    L.append("|---|---|---|---|---|---|")
    for r in p["contracts"]:
        ex = r["section_counts"].get("EXAMPLES", 0) + r["section_counts"].get("EXAMPLE", 0)
        win = f"{r['window_commits']} commit(s), {r['window_last_date']}" if r["in_window"] else "—"
        if not r["registered"]:
            win = "**unregistered** · " + win
        L.append(f"| `{r['command'] or '(none)'}` | {r['status'] or '—'} | "
                 f"{r['category'] or '—'} | {ex} | `{r['file']}` | {win} |")
    vol = p.get("voluntary_files", [])
    L.append("\n## Voluntary descriptions — offered, not promised\n")
    L.append("`@dottalk.usage.voluntary v1` does not contain `@dottalk.usage v1`, so the "
             "miner never sees these. They reach no store and no page.\n")
    L.extend(f"- `{v}`" for v in vol) if vol else L.append("_none_")
    return "\n".join(L) + "\n"


def emit_html(p: dict) -> str:
    e = _html.escape
    rows = "".join(
        "<tr data-w='{w}' data-x='{x}' data-u='{u}'>"
        "<td><code>{c}</code></td><td>{s}</td><td>{g}</td><td class=n>{ex}</td>"
        "<td><code class=f>{f}</code></td><td>{win}</td></tr>".format(
            w=1 if r["in_window"] else 0,
            u=0 if r["registered"] else 1,
            x=0 if (r["section_counts"].get("EXAMPLES", 0)
                    + r["section_counts"].get("EXAMPLE", 0)) else 1,
            c=e(r["command"] or "(none)"), s=e(r["status"] or "—"),
            g=e(r["category"] or "—"),
            ex=r["section_counts"].get("EXAMPLES", 0) + r["section_counts"].get("EXAMPLE", 0),
            f=e(r["file"]),
            win=e(f"{r['window_commits']}× {r['window_last_date']}" if r["in_window"] else "—"))
        for r in p["contracts"])
    hd = p["provenance"]["head"]
    volrows = "".join(f"<tr><td><code class=f>{e(v)}</code></td></tr>"
                      for v in p.get("voluntary_files", [])) or \
              "<tr><td><i>none</i></td></tr>"
    stats = "".join(f"<div class=k><b>{v}</b><span>{e(k.replace('_',' '))}</span></div>"
                    for k, v in p["totals"].items())
    return f"""<title>Command Contract Inventory</title>
<style>
:root{{--bg:#fbfaf8;--fg:#1c1a17;--mut:#6b6660;--line:#e3ded6;--acc:#8a5a2b}}
:root:not([data-theme=light]) {{}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#15140f;--fg:#ece8e0;--mut:#9a938a;--line:#302c26;--acc:#d9a066}}}}
:root[data-theme=dark]{{--bg:#15140f;--fg:#ece8e0;--mut:#9a938a;--line:#302c26;--acc:#d9a066}}
body{{background:var(--bg);color:var(--fg);font:15px/1.55 ui-sans-serif,system-ui,sans-serif;padding-block:32px;padding-left:20px;padding-right:20px;max-width:1100px;margin:0 auto}}
h1{{font-size:1.5rem;margin:0 0 4px}}
.sub{{color:var(--mut);font-size:.85rem;margin-bottom:20px}}
.ks{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}}
.k{{border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:96px}}
.k b{{display:block;font-size:1.3rem;color:var(--acc)}}
.k span{{font-size:.72rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}}
.ctl{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
button{{font:inherit;font-size:.85rem;padding:5px 11px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--fg);cursor:pointer}}
button[aria-pressed=true]{{background:var(--acc);border-color:var(--acc);color:var(--bg)}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:.85rem}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);position:sticky;top:0;background:var(--bg)}}
td.n{{text-align:right}}
code{{font:12px ui-monospace,Menlo,Consolas,monospace}}
code.f{{color:var(--mut)}}
tr[hidden]{{display:none}}
</style>
<h1>Command Contract Inventory</h1>
<div class=sub>Cut at <code>{e(hd['sha'][:12])}</code> · {e(hd['date'])} · {e(hd['subject'])}<br>
Census from <code>git ls-files</code>; window from <code>git log --since={e(p['provenance']['since'] or '(none)')}</code>. Neither uses file mtime.</div>
<div class=ks>{stats}</div>
<div class=ctl>
<button id=b0 aria-pressed=true>All</button>
<button id=b1 aria-pressed=false>Changed in window</button>
<button id=b2 aria-pressed=false>No examples</button>
<button id=b3 aria-pressed=false>Contract, not registered</button>
</div>
<div class=wrap><table><thead><tr>
<th>Command</th><th>Status</th><th>Category</th><th>Ex.</th><th>File</th><th>Window</th>
</tr></thead><tbody id=tb>{rows}</tbody></table></div>
<script>
const tb=document.getElementById('tb'),bs=[b0,b1,b2,b3],attr=[null,'w','x','u'];
let cur=0;
function apply(){{for(const tr of tb.rows){{tr.hidden = cur? tr.dataset[attr[cur]]!=='1' : false;}}
bs.forEach((b,i)=>b.setAttribute('aria-pressed', String(i===cur)));}}
bs.forEach((b,i)=>b.onclick=()=>{{cur=i;apply();}});
apply();
</script>
<h2 style="font-size:1rem;margin:26px 0 6px">Voluntary descriptions — offered, not promised</h2>
<div class=sub>These files carry <code>@dottalk.usage.voluntary v1</code>. That marker does
<b>not</b> contain <code>@dottalk.usage v1</code>, so the engine's miner never sees it:
these blocks reach no store, no HELP topic and no published page. Promoting one to
contract is an owner ruling.</div>
<div class=wrap><table><tbody>{volrows}</tbody></table></div>
"""


def mode_inventory(a) -> int:
    root = Path(a.source_root).resolve()
    census, window, items, files_with, vol = gather(root, a.since)
    p = to_payload(root, a.since, census, window, items, files_with, vol)
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(p, indent=2, sort_keys=False) + "\n",
                                    encoding="utf-8")
    if a.out_md:
        Path(a.out_md).write_text(emit_md(p), encoding="utf-8")
    if a.out_html:
        Path(a.out_html).write_text(emit_html(p), encoding="utf-8")
    t = p["totals"]
    print("CONTRACT INVENTORY")
    print(f"  head            : {p['provenance']['head']['sha'][:12]}  {p['provenance']['head']['date']}")
    print(f"  window          : {a.since or '(none)'}")
    for k, v in t.items():
        print(f"  {k:<22}: {v}")
    return 0


def mode_drift(a) -> int:
    root = Path(a.source_root).resolve()
    store_dir = Path(a.store).resolve()
    _c, _w, items, _f, _v = gather(root, None)

    src_keys = {c.key for c in items if c.key}
    rows = read_store(store_dir)
    contract_rows = [r for r in rows if r["source"] == "USAGE_CONTRACT"]
    store_keys = {r["cmdkey"] for r in contract_rows if r["cmdkey"]}

    new_in_source = sorted(src_keys - store_keys)
    gone_from_source = sorted(store_keys - src_keys)

    # ---- THE COMPARISON IS SET-WISE AND DEDUPED, AND THAT IS NOT LAZINESS ---
    # Measured 2026-09-13 on the live store: the same contract line is written
    # TWICE under two NAMEs, by two passes that both run --
    #
    #     CONTRACT_*        5,196 rows   helpdata_source_miner.cpp
    #     USAGE_CONTRACT*   3,817 rows   helpdata_cmdhelp_bridge.cpp
    #
    # THE NAMES ARE THE WRONG WAY ROUND FROM WHAT THEY LOOK LIKE, and this
    # comment said the opposite until it was checked against the emitters on
    # 2026-09-13: "CONTRACT_" rows are written by the MINER (miner:1373-1455)
    # and "USAGE_CONTRACT" rows by the BRIDGE (bridge:442-473). Anyone
    # attributing a defect from the row name alone will blame the wrong file.
    #
    # -- and 3,302 distinct (cmdkey, kind, text) triples appear in both, so a
    # sequence compare against either family alone reports drift on nearly every
    # command and means nothing. Neither family is a superset either: 1,869
    # triples are only in CONTRACT_* and 495 only in USAGE_CONTRACT*, so the
    # comparison is against the UNION, deduped. The duplication is reported
    # below as STRUCTURE, not as drift, because it is a property of the writer
    # rather than a difference from source.
    #
    # A source usage: line also reaches the store as SYNTAX (CONTRACT_SYNTAX
    # restates CONTRACT_USAGE_LINE), so USAGE is compared against USAGE u SYNTAX.
    # SUMMARY is deliberately absent from this map. The store carries it at
    # ORD 0, which the ORD>=1 rule below already drops on the store side; mapping
    # it here would put source summaries against an empty store set and report
    # drift on all 221 commands.
    kind_of = {"USAGE": "USAGE", "SYNTAX": "USAGE", "EXAMPLES": "EXAMPLE",
               "EXAMPLE": "EXAMPLE", "NOTES": "NOTE", "NOTE": "NOTE",
               "WARNINGS": "WARNING", "WARNING": "WARNING",
               "RELATED": "RELATED", "ALIAS": "ALIAS", "ALIASES": "ALIAS"}

    src_lines: dict[tuple[str, str], set[str]] = {}
    for c in items:
        if not c.key:
            continue
        for sec, lines in c.sections.items():
            k = kind_of.get(sec)
            if not k:
                continue
            src_lines.setdefault((c.key, k), set()).update(
                x.strip() for x in lines if x.strip())
        # The compact spelling is an ALIAS row in the store, synthesized by
        # add_set_family_alias_if_needed(); source declares it only implicitly.
        for al in c.aliases:
            src_lines.setdefault((c.key, "ALIAS"), set()).add(al)

    # ORD 0 IS A HEADER THE WRITER SYNTHESIZES, NOT A CONTRACT LINE. It reads
    # "<COMMAND> usage contract" and has no counterpart in source, so counting
    # it makes every single command report drift forever. Body lines are ORD>=1.
    store_lines: dict[tuple[str, str], set[str]] = {}
    for r in contract_rows:
        if not r["cmdkey"]:
            continue
        k = kind_of.get(r["kind"])
        if not k:
            continue
        if (r["ord"] or "").strip() in ("", "0"):
            continue
        t = (r["text"] or "").strip()
        if t:
            store_lines.setdefault((r["cmdkey"], k), set()).add(t)

    changed = []
    for k in sorted(set(src_lines) | set(store_lines)):
        s_set = src_lines.get(k, set())
        d_set = store_lines.get(k, set())
        if s_set == d_set:
            continue
        changed.append({
            "cmdkey": k[0], "kind": k[1],
            "only_in_source": sorted(s_set - d_set),
            "only_in_store": sorted(d_set - s_set),
        })

    # ---- structural report (NOT drift) -----------------------------------
    fam_c = [r for r in contract_rows if r["name"].startswith("CONTRACT_")]
    fam_u = [r for r in contract_rows if r["name"].startswith("USAGE_CONTRACT")]
    trip = lambda rs: {(r["cmdkey"], r["kind"], (r["text"] or "").strip()) for r in rs}
    tc, tu = trip(fam_c), trip(fam_u)

    print("CONTRACT DRIFT  (source  vs  saved HELP store)")
    print(f"  store            : {store_dir}")
    print(f"  source           : {root}")
    print(f"  contracts in src : {len(src_keys)} commands, {len(items)} blocks")
    print(f"  USAGE_CONTRACT   : {len(contract_rows)} rows, {len(store_keys)} commands")
    print()
    print("  STORE STRUCTURE (not drift -- a property of the writer)")
    print("    NOTE: the family names are the wrong way round from what they look")
    print("    like -- CONTRACT_* is written by the MINER, USAGE_CONTRACT* by the")
    print("    BRIDGE. Verified against the emitters, not guessed from the name.")
    print(f"    CONTRACT_*      (miner)  rows : {len(fam_c)}")
    print(f"    USAGE_CONTRACT* (bridge) rows : {len(fam_u)}")
    print(f"    content in BOTH families      : {len(tc & tu)}")
    print(f"    only CONTRACT_*               : {len(tc - tu)}")
    print(f"    only USAGE_CONTRACT*          : {len(tu - tc)}")
    print(f"    deduped union                 : {len(tc | tu)}")
    print()
    print(f"  NEW in source    : {len(new_in_source)}")
    for k in new_in_source[:a.limit]:
        print(f"      + {k}")
    print(f"  GONE from source : {len(gone_from_source)}")
    for k in gone_from_source[:a.limit]:
        print(f"      - {k}")
    print(f"  TEXT DIFFERS     : {len(changed)}  (command x kind)")
    for c in changed[:a.limit]:
        print(f"      ~ {c['cmdkey']} [{c['kind']}]")
        for x in c["only_in_source"][:4]:
            print(f"          source only : {x[:88]}")
        for x in c["only_in_store"][:4]:
            print(f"          store  only : {x[:88]}")

    if a.out_json:
        Path(a.out_json).write_text(json.dumps({
            "store": str(store_dir), "source_root": str(root),
            "head": head_commit(root),
            "structure": {
                "contract_family_rows": len(fam_c),
                "usage_contract_family_rows": len(fam_u),
                "content_in_both": len(tc & tu),
                "only_contract_family": len(tc - tu),
                "only_usage_contract_family": len(tu - tc),
                "deduped_union": len(tc | tu),
            },
            "new_in_source": new_in_source,
            "gone_from_source": gone_from_source,
            "text_differs": changed,
        }, indent=2) + "\n", encoding="utf-8")

    bad = len(new_in_source) + len(gone_from_source) + len(changed)
    print()
    print("CONTRACT DRIFT:", "CLEAN" if not bad else f"{bad} DIFFERENCE(S)")
    if bad:
        print("  The saved store no longer matches source. Rebuild it (CMDHELP) and")
        print("  re-run, or account for each line above. THIS IS NOT A BUILD FAILURE.")
        print("  It is documentation that moved since the store was last built --")
        print("  the one thing neither audit-drift.ps1 nor prepush_gate.py measures.")
    if a.report_only:
        return 0
    return 2 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    i = sub.add_parser("inventory")
    i.add_argument("--source-root", required=True)
    i.add_argument("--since", default=None,
                   help="git log --since expression, e.g. '7 days ago'")
    i.add_argument("--out-json")
    i.add_argument("--out-md")
    i.add_argument("--out-html")
    i.set_defaults(fn=mode_inventory)

    d = sub.add_parser("drift")
    d.add_argument("--source-root", required=True)
    d.add_argument("--store", required=True,
                   help="directory holding HELP_ARTIFACTS.dbf + help_artifacts.dbt")
    d.add_argument("--report-only", action="store_true")
    d.add_argument("--out-json")
    d.add_argument("--limit", type=int, default=40,
                   help="how many entries to print per section (default 40)")
    d.set_defaults(fn=mode_drift)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
