#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manifest-driven manual assembler -- MANUAL-ASSEMBLY lane, M3.

Reads tools/manualgen/manual_assembly_manifest.yaml (the bill of materials) and
emits a single assembled developer manual plus an assembly report. Dispatches on
each part's `region_mode`:

    whole-file  generate + own the region (hand-edits forbidden)
    candidate   include the existing reviewed file (regeneration is gated elsewhere)
    authored    include the existing hand-authored file verbatim (no anchor)
    append      append a provenance/evidence snapshot
    bind        bind a SET of external files (command pages, diagrams)

Generated regions are delimited with MAN:BEGIN/MAN:END anchors so the M4 drift
gate can find exactly what the assembler owns. Acceptance stays human-gated: this
tool produces a candidate assembled artifact under generated/, never touching
published/.

Target runtime: Python 3.12 (repo standard); uses only stdlib + PyYAML.
"""

import os
import re
import sys
import json
import csv
import hashlib
import subprocess
from datetime import datetime, timezone

import yaml

ASSEMBLER_VERSION = "manual-assembler/0.1.0 (MANUAL-ASSEMBLY M3)"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))          # tools/manualgen -> repo root
MANIFEST = os.path.join(HERE, "manual_assembly_manifest.yaml")
PUB_ROOT = os.path.join(ROOT, "docs/manuals/developer/manualgen/published/developer_manual_publication_v1")
OUT_DIR = os.path.join(ROOT, "docs/manuals/developer/manualgen/generated/assembled")
OUT_MD = os.path.join(OUT_DIR, "developer_manual_assembled_v1.md")
OUT_REPORT = os.path.join(OUT_DIR, "assembly_report_v1.json")

# Parts whose content depends on the assembled heading tree -> rendered last.
DEFERRED = {"fm-toc", "bm-index"}


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def rd(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def path_label(path):
    """Return a repo-relative label, or an absolute label across Windows drives."""
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def slug(text):
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s or "section"


def demote(md, n):
    """Add n levels to every ATX heading (cap at 6) for clean hierarchy."""
    if n <= 0:
        return md
    out = []
    for line in md.splitlines():
        m = re.match(r"^(#{1,6})(\s+.*)$", line)
        if m:
            hashes = "#" * min(6, len(m.group(1)) + n)
            out.append(hashes + m.group(2))
        else:
            out.append(line)
    return "\n".join(out)


def anchor_begin(pid, gen, src):
    return "<!-- MAN:BEGIN id=%s gen=%s src=%s -->" % (pid, gen or "-", src)


def anchor_end(pid):
    return "<!-- MAN:END id=%s -->" % pid


def anchor_append(pid):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "<!-- MAN:APPEND id=%s at=%s -->" % (pid, now)


def anchor_bind(pid, set_path, n):
    return "<!-- MAN:BIND id=%s set=%s count=%d -->" % (pid, set_path, n)


def src_label(sor):
    if isinstance(sor, list):
        return ",".join(str(x) for x in sor)
    return str(sor)


def load_json(rel):
    try:
        return json.load(open(os.path.join(ROOT, rel), "r", encoding="utf-8"))
    except Exception:
        return {}


def git_commit():
    try:
        out = subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------- #
# generators (assembler:*) -- each returns a markdown region body
# --------------------------------------------------------------------------- #
def gen_frontmatter_title(ctx):
    acc = ctx["accepted"]
    mp = ctx["machine"]
    title = acc.get("first_heading", "DotTalk++ / x64base Developer Manual")
    sha = (acc.get("artifact_sha256") or "")[:12]
    machine = mp.get("machine_type", "unattested machine")
    cpu = (mp.get("cpu") or {}).get("name") if isinstance(mp.get("cpu"), dict) else None
    lines = [
        "# %s" % title,
        "",
        "> **Assembled artifact** — produced by the manifest-driven assembler from the",
        "> declared bill of materials. This is a candidate build; acceptance is gated.",
        "",
        "| | |",
        "| --- | --- |",
        "| Manual id | `%s` |" % ctx["manifest"]["manual_id"],
        "| Repository HEAD (context only) | `%s` |" % ctx["commit"],
        "| Accepted reader baseline | `%s` (accepted %s) |"
        % (sha or "n/a", acc.get("accepted_utc", "n/a")),
        "| Command-reference pages | %s |" % acc.get("command_reference_pages", "n/a"),
        "| Build date (UTC) | %s |" % ctx["build_utc"],
        "| Machine (maintainer-attested) | %s%s |"
        % (machine, (" / %s" % cpu) if cpu else ""),
    ]
    return "\n".join(lines)


def gen_frontmatter_provenance(ctx):
    acc = ctx["accepted"]
    mp = ctx["machine"]
    lines = [
        "## Provenance & attestation",
        "",
        "This manual is assembled from source, HELP/metadata, SelfDoc reports, and",
        "reviewed manualgen sections. Proof labels travel with each part.",
        "",
        "- Accepted reader baseline: `%s`, %s lines, %s headings (%s)."
        % (
            (acc.get("artifact_sha256") or "")[:12] or "n/a",
            acc.get("artifact_lines", "n/a"),
            acc.get("artifact_heading_count", "n/a"),
            acc.get("accepted_utc", "n/a"),
        ),
        "- Command reference: %s pages (%s reader-linked + %s supplemental + %s post-baseline repair)."
        % (
            acc.get("command_reference_pages", "n/a"),
            acc.get("reader_linked_command_reference_pages", "n/a"),
            acc.get("supplemental_standalone_command_reference_pages", "n/a"),
            acc.get("postbaseline_repair_command_reference_pages", "n/a"),
        ),
        "- MDO lane: `%s`." % acc.get("mdo", "n/a"),
        "- Machine attestation: %s (%s). %s"
        % (
            mp.get("historical_run_binding", "n/a"),
            mp.get("machine_type", "n/a"),
            mp.get("honesty_note", ""),
        ),
    ]
    return "\n".join(lines)


def gen_toc(ctx):
    lines = ["## Table of Contents", ""]
    seen = set()
    for level, text, sslug, pid in ctx["headings"]:
        if level < 2 or level > 3:
            continue
        if text.strip().lower() == "table of contents":
            continue
        key = (sslug, level)
        if key in seen:
            continue
        seen.add(key)
        indent = "  " * (level - 2)
        lines.append("%s- [%s](#%s)" % (indent, text, sslug))
    if len(lines) == 2:
        lines.append("_(no headings collected)_")
    return "\n".join(lines)


def _parse_function_docs(src):
    """Positional parse of FunctionDoc{...} aggregate initialisers."""
    funcs = []
    i = 0
    while True:
        j = src.find("FunctionDoc{", i)
        if j < 0:
            break
        # brace-match the block
        depth = 0
        k = src.find("{", j)
        start = k
        while k < len(src):
            c = src[k]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        block = src[start + 1 : k]
        i = k + 1
        # name = first string literal
        mname = re.search(r'"((?:[^"\\]|\\.)*)"', block)
        if not mname:
            continue
        name = mname.group(1)
        cat = None
        mc = re.search(r"FunctionCategory::(\w+)", block)
        if mc:
            cat = mc.group(1)
        # arity line: `N, N,`
        marity = re.search(r"^\s*(\d+)\s*,\s*(-?\d+)\s*,\s*$", block, re.M)
        arity = "%s..%s" % (marity.group(1), marity.group(2)) if marity else ""
        # summary = first string after the arity line (fallback: 2nd string)
        summary = ""
        if marity:
            tail = block[marity.end():]
            ms = re.search(r'"((?:[^"\\]|\\.)*)"', tail)
            if ms:
                summary = ms.group(1)
        if not summary:
            strs = re.findall(r'"((?:[^"\\]|\\.)*)"', block)
            summary = strs[1] if len(strs) > 1 else ""
        funcs.append((name, cat or "", arity, summary))
    return funcs


def gen_function_reference(ctx):
    path = os.path.join(ROOT, "src/cli/expr/function_catalog.cpp")
    lines = ["## Function Reference", ""]
    if not os.path.exists(path):
        return "\n".join(lines + ["_source not found: src/cli/expr/function_catalog.cpp_"])
    funcs = _parse_function_docs(rd(path))
    ctx["function_names"] = [f[0] for f in funcs]
    lines.append(
        "%d core functions harvested from `function_catalog.cpp` "
        "(`FunctionDoc` table). Student/extension functions self-register from "
        "`src/ext/fn` and are not enumerated here." % len(funcs)
    )
    lines += ["", "| Function | Category | Args | Summary |", "| --- | --- | --- | --- |"]
    for name, cat, arity, summary in sorted(funcs):
        summary = summary.replace("|", "\\|")
        lines.append("| `%s` | %s | %s | %s |" % (name, cat, arity, summary))
    return "\n".join(lines)


def gen_message_catalog(ctx):
    path = os.path.join(ROOT, "src/cli/xbase_error_codes.cpp")
    lines = ["## Error / Message Catalog", ""]
    facilities = []
    severities = []
    if os.path.exists(path):
        src = rd(path)
        mfac = re.search(r"enum class facility[^{]*\{([^}]*)\}", src, re.S)
        if mfac:
            for m in re.finditer(r"(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)", mfac.group(1)):
                facilities.append((m.group(1), m.group(2)))
        msev = re.search(r"enum class severity[^{]*\{([^}]*)\}", src, re.S)
        if msev:
            for m in re.finditer(r"(\w+)\s*=\s*(\d+)", msev.group(1)):
                severities.append((m.group(1), m.group(2)))
    lines.append(
        "Canonical error codes use an HRESULT-style 32-bit packing "
        "(severity · facility · code) defined in `src/cli/xbase_error_codes.cpp`."
    )
    if severities:
        lines += ["", "**Severities:** " + ", ".join("`%s`=%s" % s for s in severities) + "."]
    if facilities:
        lines += ["", "**Facilities (subsystems):**", "", "| Facility | Value |", "| --- | --- |"]
        for n, v in facilities:
            lines.append("| `%s` | %s |" % (n, v))
    lines += [
        "",
        "<!-- MAN:BEGIN id=spine-error-catalog-messages gen=assembler:message-catalog src=message_catalog.cpp -->",
        "> **Review candidate.** The full code→message enumeration is sourced from",
        "> `src/cli/message_catalog.cpp`, `src/cli/help_errors.cpp`, and",
        "> `src/help/helpdata_messages.cpp`; harvesting the complete message table is a",
        "> later refinement of `assembler:message-catalog`. The severity/facility",
        "> taxonomy above is source-derived and final.",
        "<!-- MAN:END id=spine-error-catalog-messages -->",
    ]
    return "\n".join(lines)


def gen_diagrams(ctx):
    rel = ctx["manifest"]["provenance"]["diagram_matrix"]
    path = os.path.join(ROOT, rel)
    lines = ["## Diagrams", ""]
    if not os.path.exists(path):
        return "\n".join(lines + ["_diagram matrix not found: %s_" % rel])
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("review_status") or "").strip().lower() == "promoted":
                rows.append(row)
    ctx["diagram_count"] = len(rows)
    lines.append(
        "%d promoted diagrams bound from the attachment matrix (`%s`), each placed "
        "at its manual target and carrying its proof level." % (len(rows), rel)
    )
    lines += ["", "| Diagram | Source asset | Manual target | Proof |", "| --- | --- | --- | --- |"]
    for r in rows:
        lines.append(
            "| `%s` | `%s` | %s | %s |"
            % (
                r.get("diagram_id", ""),
                r.get("source_asset_path", ""),
                (r.get("manual_targets", "") or "").replace("|", "\\|"),
                r.get("proof_level", ""),
            )
        )
    return "\n".join(lines)


def gen_glossary(ctx):
    lines = ["## Glossary", ""]
    lines.append(
        "> **Review candidate** — terms harvested from command/function names and "
        "section headings; definitions are pending maintainer review (`candidate` "
        "mode). Note: the DotTalk++ `GLOSSARY` *command* is documented in the "
        "Command Reference, distinct from this back-matter glossary."
    )
    terms = set()
    for n in ctx.get("command_names", []):
        terms.add(n.upper())
    for n in ctx.get("function_names", []):
        terms.add(n.upper())
    curated = {
        "CDX": "Compound index file (multiple ordered tags).",
        "LMDB": "Lightning Memory-Mapped Database backend used for index/order acceleration.",
        "DBF": "dBASE-family table file; x64base uses a 64-bit-widened variant (DBF_64).",
        "FPT": "Memo (variable-length field) file paired with a DBF; x64base uses FPT64.",
        "WAL": "Write-ahead log providing durability for buffered mutations.",
        "RECNO": "Record number; x64base widens record addressing to 64-bit (RECNO64).",
        "SelfDoc": "The report-only documentation-generation subsystem.",
        "MDO": "Master Documentation Organizer — lane/section/promotion structure.",
    }
    lines += ["", "| Term | Definition |", "| --- | --- |"]
    for t in sorted(curated):
        lines.append("| **%s** | %s |" % (t, curated[t]))
    # a bounded sample of harvested terms as review candidates
    sample = sorted(t for t in terms if t not in curated)[:40]
    for t in sample:
        lines.append("| `%s` | _definition — review_ |" % t)
    if len(terms) > 40:
        lines.append("| … | _%d further harvested terms pending review_ |" % (len(terms) - 40))
    return "\n".join(lines)


def gen_index(ctx):
    lines = ["## Index", ""]
    entries = {}  # term -> slug
    for level, text, sslug, pid in ctx["headings"]:
        if 2 <= level <= 3 and text.strip().lower() not in ("index", "table of contents"):
            entries.setdefault(text.strip(), sslug)
    for n in ctx.get("command_names", []):
        entries.setdefault(n.upper() + " (command)", "cmd-" + slug(n))
    for n in ctx.get("function_names", []):
        entries.setdefault(n.upper() + " (function)", "function-reference")
    if not entries:
        return "\n".join(lines + ["_(no index terms)_"])
    by_letter = {}
    for term, sslug in entries.items():
        letter = term[0].upper()
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append((term, sslug))
    for letter in sorted(by_letter):
        lines.append("")
        lines.append("**%s**" % letter)
        lines.append("")
        for term, sslug in sorted(by_letter[letter], key=lambda x: x[0].lower()):
            lines.append("- [%s](#%s)" % (term, sslug))
    return "\n".join(lines)


def gen_colophon(ctx):
    acc = ctx["accepted"]
    mp = ctx["machine"]
    lines = [
        "## Colophon — build provenance",
        "",
        "This manual assembled itself. The record below is emitted by the assembler",
        "so the self-documentation claim is auditable end to end.",
        "",
        "| | |",
        "| --- | --- |",
        "| Assembler | `%s` |" % ASSEMBLER_VERSION,
        "| Manifest | `tools/manualgen/manual_assembly_manifest.yaml` (%s) |"
        % ctx["manifest"]["schema"],
        "| Parts assembled | %d (of %d declared) |"
        % (ctx["stats"]["parts_emitted"], ctx["stats"]["parts_total"]),
        "| Greenfield parts generated | %d |" % ctx["stats"]["greenfield_emitted"],
        "| Repository HEAD (context only) | `%s` |" % ctx["commit"],
        "| Python (build) | %s (target 3.12) |"
        % ".".join(str(x) for x in sys.version_info[:3]),
        "| Build timestamp (UTC) | %s |" % ctx["build_utc"],
        "| Machine | %s — %s |"
        % (mp.get("machine_type", "n/a"), mp.get("historical_run_binding", "n/a")),
        "| Accepted reader baseline | `%s` |" % ((acc.get("artifact_sha256") or "")[:12] or "n/a"),
    ]
    return "\n".join(lines)


GENERATORS = {
    "assembler:frontmatter:fm-title": gen_frontmatter_title,
    "assembler:frontmatter:fm-provenance": gen_frontmatter_provenance,
    "assembler:toc": gen_toc,
    "assembler:function-reference": gen_function_reference,
    "assembler:message-catalog": gen_message_catalog,
    "assembler:diagrams": gen_diagrams,
    "assembler:glossary": gen_glossary,
    "assembler:index": gen_index,
    "assembler:colophon": gen_colophon,
}


# --------------------------------------------------------------------------- #
# part rendering
# --------------------------------------------------------------------------- #
def resolve_existing(part):
    """Map a part's declared output to a concrete published file, if any."""
    out = part.get("output")
    if not out or "*" in out:
        return None
    p = os.path.join(PUB_ROOT, out)
    return p if os.path.exists(p) else None


def bind_command_reference(part, ctx):
    cmd_dir = os.path.join(PUB_ROOT, "command_reference_v1", "commands")
    files = sorted(
        [f for f in os.listdir(cmd_dir) if f.endswith(".md")]
    ) if os.path.isdir(cmd_dir) else []
    names = [os.path.splitext(f)[0] for f in files]
    ctx["command_names"] = names
    body = [
        "## Command Reference",
        "",
        anchor_bind(part["id"], "command_reference_v1/commands", len(files)),
        "",
        "%d command pages bound from the reference set." % len(files),
        "",
    ]
    for f in files:
        name = os.path.splitext(f)[0]
        page = rd(os.path.join(cmd_dir, f))
        # strip the page's own leading H1, re-title as H3, demote the rest
        page = re.sub(r"\A\s*#\s+.*\n", "", page)
        body.append('<a id="cmd-%s"></a>' % slug(name))
        body.append("### %s" % name.upper())
        body.append("")
        body.append(demote(page, 3).strip())
        body.append("")
    return "\n".join(body)


def render_part(part, ctx):
    pid = part["id"]
    mode = part["region_mode"]
    gen = (part.get("binding") or {}).get("generator")
    title = part.get("title", pid)
    src = src_label(part.get("source_of_record", "-"))

    # authored: include the existing hand-authored file verbatim, no anchor
    if mode == "authored":
        f = resolve_existing(part)
        if f:
            body = demote(rd(f).strip(), 1)
        elif part.get("status") == "greenfield":
            body = "## %s\n\n_To be authored._" % title
        else:
            body = "## %s\n\n_authored part not found_" % title
        # bracketed for drift tooling, but marked authored: the assembler never
        # rewrites the inside of this region (review-only).
        return "%s\n%s\n%s" % (anchor_begin(pid, "authored", src), body, anchor_end(pid))

    # bind: command reference (set) or diagrams (generated listing)
    if mode == "bind":
        if pid == "spine-command-reference":
            body = bind_command_reference(part, ctx)
            return "%s\n%s\n%s" % (anchor_begin(pid, gen, src), body, anchor_end(pid))
        if pid == "diagrams-from-matrix":
            body = gen_diagrams(ctx)
            return "%s\n%s\n%s" % (anchor_begin(pid, gen, src), body, anchor_end(pid))

    # generator-backed regions (whole-file / candidate greenfield / append greenfield)
    key = gen
    if gen == "assembler:frontmatter":
        key = "assembler:frontmatter:" + pid
    if key in GENERATORS:
        body = GENERATORS[key](ctx)
        head = anchor_append(pid) if mode == "append" else anchor_begin(pid, gen, src)
        return "%s\n%s\n%s" % (head, body, anchor_end(pid))

    # candidate / append backed by an existing reviewed file (manualgen output)
    f = resolve_existing(part)
    if f:
        head = anchor_append(pid) if mode == "append" else anchor_begin(pid, gen, src)
        return "%s\n%s\n%s" % (head, demote(rd(f).strip(), 1), anchor_end(pid))

    # last resort: a labelled placeholder region (keeps the manual well-formed)
    head = anchor_begin(pid, gen, src)
    return "%s\n## %s\n\n_part pending generator (%s)_\n%s" % (head, title, gen, anchor_end(pid))


def collect_headings(pid, md, headings):
    for line in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append((level, text, slug(text), pid))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(out_dir=None):
    if sys.version_info[:2] != (3, 12):
        raise SystemExit(
            "manual assembler requires Python 3.12; observed %d.%d"
            % sys.version_info[:2]
        )
    out_dir = out_dir or OUT_DIR
    out_md = os.path.join(out_dir, "developer_manual_assembled_v1.md")
    out_report = os.path.join(out_dir, "assembly_report_v1.json")

    manifest = yaml.safe_load(rd(MANIFEST))
    parts = sorted(manifest["parts"], key=lambda p: p["order"])
    by_id = {p["id"]: p for p in parts}

    ctx = {
        "manifest": manifest,
        "accepted": load_json(manifest["provenance"]["accepted_artifact"]),
        "machine": load_json(manifest["provenance"]["machine_profile"]),
        "commit": git_commit(),
        "build_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "headings": [],
        "command_names": [],
        "function_names": [],
        "stats": {
            "parts_total": len(parts),
            "parts_emitted": len(parts),
            "greenfield_emitted": sum(
                1
                for p in parts
                if p.get("status") == "greenfield" and p["region_mode"] != "authored"
            ),
        },
    }

    rendered = {}
    headings = []

    # pass 1 -- everything except heading-dependent parts
    for p in parts:
        if p["id"] in DEFERRED:
            continue
        md = render_part(p, ctx)
        rendered[p["id"]] = md
        collect_headings(p["id"], md, headings)

    ctx["headings"] = headings

    # pass 2 -- TOC + index (need the assembled heading tree)
    for pid in DEFERRED:
        p = by_id[pid]
        md = render_part(p, ctx)
        rendered[pid] = md

    # emit in manifest order
    doc = "\n\n".join(rendered[p["id"]] for p in parts).rstrip() + "\n"

    os.makedirs(out_dir, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(doc)

    # report
    greenfield_emitted = ctx["stats"]["greenfield_emitted"]

    part_report = []
    for p in parts:
        md = rendered[p["id"]]
        part_report.append(
            {
                "id": p["id"],
                "kind": p["kind"],
                "class": p["class"],
                "region_mode": p["region_mode"],
                "generator": (p.get("binding") or {}).get("generator"),
                "status": p.get("status"),
                "lines": md.count("\n") + 1,
                "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()[:16],
            }
        )

    begin_n = doc.count("MAN:BEGIN") + doc.count("MAN:APPEND")
    end_n = doc.count("MAN:END")
    bind_n = doc.count("MAN:BIND")
    report = {
        "schema": "dottalk.manual.assembly_report.v1",
        "assembler": ASSEMBLER_VERSION,
        "manifest": "tools/manualgen/manual_assembly_manifest.yaml",
        "build_utc": ctx["build_utc"],
        "commit": ctx["commit"],
        "python": ".".join(str(x) for x in sys.version_info[:3]),
        "output_md": path_label(out_md),
        "output_md_sha256": sha256_file(out_md),
        "total_lines": doc.count("\n") + 1,
        "anchor_balance": {
            "open": begin_n,
            "close": end_n,
            "bind": bind_n,
            "balanced": begin_n == end_n,
        },
        "counts": {
            "parts": len(parts),
            "greenfield_generated": greenfield_emitted,
            "command_pages_bound": len(ctx.get("command_names", [])),
            "functions_harvested": len(ctx.get("function_names", [])),
            "diagrams_bound": ctx.get("diagram_count", 0),
            "headings": len(headings),
        },
        "parts": part_report,
    }
    with open(out_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("assembled:", path_label(out_md))
    print("report   :", path_label(out_report))
    print("lines    :", report["total_lines"])
    print("anchors  :", report["anchor_balance"])
    print("counts   :", json.dumps(report["counts"]))
    if begin_n != end_n:
        print("WARNING: unbalanced MAN anchors", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Assemble the developer manual from the manifest.")
    ap.add_argument("--out-dir", default=None, help="output directory (default: generated/assembled)")
    args = ap.parse_args()
    sys.exit(main(args.out_dir))
