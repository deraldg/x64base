#!/usr/bin/env python3
"""
help_guard_v1.py -- Gate 3 flush guard for the HELP tier.

Read-only, deterministic, baseline-ratcheting. Same evidence contract as
stack_audit_v1.py; see FLUSH_GUARD_STAGE_MODEL_V1.md for the protocol.

Checks:

  A. HELP_COUNTS   Row counts for the canonical HELP tables vs a recorded
                   baseline. A DECREASE is a regression (content was lost);
                   an increase is reported but never blocks.
  B. SHADOW_SET    Detects divergent duplicate copies of the HELP table set in
                   other directories. This is the failure that motivated the
                   check: dottalkpp/data/dbf/help/ holds a 2026-05-14 snapshot
                   whose counts differ materially from the live 2026-07-22 set
                   (COMMANDS 402 vs 459, HELP_LINE 8073 vs 29197). A tool given
                   the wrong root consumes the stale set and reports success.
  C. LOCALE_SET    Presence/among-set consistency of the *_LOCALE companions.
  D. CMDHELPCHK    NOT assertable from files alone -- it requires a runtime pass.
                   The guard reports it as REQUIRED EXTERNAL EVIDENCE and, if
                   --cmdhelpchk <transcript> is supplied, checks the transcript
                   for a clean verdict rather than pretending it ran.

Canonical root: dottalkpp/data/help  (newest set; matches the Gate 3 reference
counts recorded in DOCFLUSH-20260722-001: 459 legacy commands, 2,566 arguments,
29,197 lines).

Exit codes:  0 PASS  .  3 WARN  .  1 FAIL (count regression, or divergent shadow
             set when --strict-shadow is given).

Usage:
  python tools/fullstack_docs/help_guard_v1.py
  python tools/fullstack_docs/help_guard_v1.py --out-dir <run>/gate3_<date>
  python tools/fullstack_docs/help_guard_v1.py --write-baseline
  python tools/fullstack_docs/help_guard_v1.py --cmdhelpchk <transcript.txt>

Owner: member.derald  .  steward: member.ai.claude.cowork  .  lane: full_stack_documentation
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

CANONICAL_HELP = "dottalkpp/data/help"

# Tables that constitute the HELP tier. Names are matched case-insensitively.
CORE_TABLES = ["COMMANDS", "CMD_ARGS", "HELP_TOPIC", "HELP_SECTION",
               "HELP_LINE", "HELP_ARTIFACTS"]
LOCALE_TABLES = ["HELP_TOPIC_LOCALE", "HELP_SECTION_LOCALE",
                 "HELP_LINE_LOCALE", "HELP_ARTIFACT_LOCALE"]

# Directories to sweep for divergent duplicate sets.
SHADOW_ROOTS = ["dottalkpp/data/dbf/help", "dottalkpp/data/help/FULL"]

# Gate 3 reference from DOCFLUSH-20260722-001 (documentation, not a threshold).
GATE3_REFERENCE = {"COMMANDS": 459, "CMD_ARGS": 2566, "HELP_LINE": 29197}


def dbf_rowcount(path: Path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(8)
        if len(head) < 8:
            return None
        return struct.unpack("<I", head[4:8])[0]
    except Exception:
        return None


def find_table(root: Path, name: str):
    """Case-insensitive lookup of <name>.dbf directly under root."""
    if not root.is_dir():
        return None
    target = f"{name.lower()}.dbf"
    for entry in sorted(os.listdir(root)):
        if entry.lower() == target:
            return root / entry
    return None


def read_set(root: Path, names):
    out = {}
    for n in names:
        p = find_table(root, n)
        out[n] = {"path": str(p.relative_to(root.parents[len(root.parents) - 1]))
                  if p else None,
                  "rows": dbf_rowcount(p) if p else None,
                  # AWARE UTC. These mtimes are only REPORTED here, never
                  # compared against another timestamp -- so this was not the
                  # false-finding bug that hit manual_guard_v1.py parse_iso().
                  # Made explicit anyway: a naive local string in an evidence
                  # bundle invites exactly that comparison later.
                  "mtime": (datetime.datetime
                            .fromtimestamp(p.stat().st_mtime, datetime.timezone.utc)
                            .strftime("%Y-%m-%dT%H:%M:%SZ") if p else None)}
    return out


def check_counts(live, baseline):
    findings, detail = [], {}
    for name in CORE_TABLES:
        rows = live.get(name, {}).get("rows")
        detail[name] = rows
        if rows is None:
            findings.append({"check": "HELP_COUNTS", "code": "MISSING_TABLE",
                             "severity": "FAIL",
                             "message": f"{name}.dbf not found under {CANONICAL_HELP}"})
            continue
        if rows == 0:
            findings.append({"check": "HELP_COUNTS", "code": "EMPTY_TABLE",
                             "severity": "WARN",
                             "message": f"{name} has zero rows"})
        if baseline:
            prev = baseline.get("counts", {}).get(name)
            if isinstance(prev, int):
                if rows < prev:
                    findings.append({"check": "HELP_COUNTS", "code": "COUNT_REGRESSION",
                                     "severity": "FAIL",
                                     "message": f"{name}: {prev} -> {rows} rows "
                                                f"({prev - rows} LOST since baseline)"})
                elif rows > prev:
                    findings.append({"check": "HELP_COUNTS", "code": "COUNT_INCREASE",
                                     "severity": "WARN",
                                     "message": f"{name}: {prev} -> {rows} rows (+{rows - prev}; "
                                                f"expected after a rebuild -- ratchet the baseline "
                                                f"deliberately if correct)"})
    # documentation-only cross-reference against the recorded Gate 3 numbers
    ref = {}
    for k, v in GATE3_REFERENCE.items():
        got = live.get(k, {}).get("rows")
        ref[k] = {"gate3_reference": v, "now": got, "matches": got == v}
    detail["_gate3_reference"] = ref
    return findings, detail


def check_shadow(root: Path, live):
    """B. A second, divergent copy of the HELP set is a silent-failure hazard."""
    findings, detail = [], {}
    live_counts = {k: v["rows"] for k, v in live.items() if v["rows"] is not None}
    for rel in SHADOW_ROOTS:
        sroot = root / rel
        if not sroot.is_dir():
            continue
        found = read_set(sroot, CORE_TABLES)
        present = {k: v["rows"] for k, v in found.items() if v["rows"] is not None}
        if not present:
            continue
        diverging = {k: (live_counts.get(k), v) for k, v in present.items()
                     if live_counts.get(k) is not None and live_counts.get(k) != v}
        newest = max((v["mtime"] for v in found.values() if v["mtime"]), default=None)
        detail[rel] = {"tables_present": len(present), "counts": present,
                       "newest_mtime": newest, "diverging_tables": len(diverging)}
        if diverging:
            sample = ", ".join(f"{k} live={a} shadow={b}" for k, (a, b) in
                               sorted(diverging.items())[:3])
            findings.append({"check": "SHADOW_SET", "code": "DIVERGENT_COPY",
                             "severity": "WARN",
                             "message": f"{rel}: {len(present)} HELP table(s), "
                                        f"{len(diverging)} diverge from the canonical set "
                                        f"(newest {newest}). Any tool pointed here consumes "
                                        f"stale HELP and reports success. {sample}"})
        else:
            findings.append({"check": "SHADOW_SET", "code": "DUPLICATE_COPY",
                             "severity": "WARN",
                             "message": f"{rel}: duplicate HELP set present and currently "
                                        f"in agreement -- still a divergence hazard"})
    return findings, detail


def dbf_rows(path: Path):
    """Read an x64 DBF into dicts. Returns [] on any problem.

    TWO TRAPS, both hit while building this check (AIF-066):

    1. The x64 0x64 variant prepends extended descriptors whose name bytes are
       not printable. Counting them as fields shifts every offset. Filter on
       "name starts with a letter".
    2. x64's unique-name fallback produces names like LOCALIZE~1 when two
       logical names truncate to the same 10-char physical name (here
       LOCALIZED_TITLE and LOCALIZED_HASH both -> LOCALIZED_). A tidy
       [A-Z0-9_]+ filter DROPS that column and silently shifts everything after
       it by its width -- which is how a first pass "proved" SOURCE_HASH was
       sha256(SOURCE_TITLE) when it is not. Widths must reconcile:
       sum(field widths) + 1 deleted-flag byte == record length.
    """
    try:
        raw = path.read_bytes()
        recs = struct.unpack("<I", raw[4:8])[0]
        hl = struct.unpack("<H", raw[8:10])[0]
        rl = struct.unpack("<H", raw[10:12])[0]
        off, fields = 32, []
        while off < hl - 1 and raw[off] != 0x0D:
            nm = raw[off:off + 11].split(b"\0")[0].decode("latin-1")
            w = raw[off + 16]
            if nm and nm[0].isalpha():
                fields.append((nm, w))
            off += 32
        if sum(w for _, w in fields) + 1 != rl:
            return []                      # refuse to guess at a layout we cannot verify
        out = []
        for i in range(recs):
            rec = raw[hl + i * rl: hl + (i + 1) * rl]
            if len(rec) < rl or rec[0:1] == b"*":
                continue
            o, d = 1, {}
            for nm, w in fields:
                d[nm] = rec[o:o + w].decode("latin-1").strip()
                o += w
            out.append(d)
        return out
    except Exception:
        return []


def check_locale(root: Path):
    """C. LOCALE_SET -- presence, and now integrity, of the locale companions.

    LOCALE_DRIFT added 2026-07-27 (AIF-066). HELP_TOPIC_LOCALE carries
    SOURCE_HASH and LOCALIZED_HASH columns whose only purpose is detecting that
    the underlying HELP source moved since the locale row was generated.
    Measured that day: HelpTopicLocaleView in src/cli/cmdhelp.cpp reads SIX of
    the table's fourteen columns and SOURCE_HASH is not among them -- the string
    appears nowhere under src/ or include/. Written on every row, compared by
    nothing.

    That gap is invisible at the prompt by construction: under the
    @dottalk.locale-preview-contract, a DRAFT_PLACEHOLDER row falls back to
    source text -- correctly -- and a STALE row falls back to source text too,
    because nothing checks. Identical output, so drift has no symptom.

    Running these checks for the first time found the fixture 2/5 orphaned:
    DOT|SET LANGUAGE and DOT|SET LOCALE no longer exist in HELP_TOPIC after the
    2026-07-22 rebuild. Those are the two topics documenting the locale feature
    itself.

    WHAT IS AND IS NOT VERIFIABLE HERE:
      LOCALIZED_HASH  IS recomputable -- confirmed sha256(LOCALIZED_TITLE)[:16]
                      on 25/25 rows -- so it is checked outright.
      SOURCE_HASH     is NOT recomputable from here. It holds one value per
                      topic, stable across that topic's locale rows, so it
                      hashes topic SOURCE CONTENT rather than the title. The
                      generator (RUN_ID PHASE23J-*) is not in the tree, so the
                      exact input is unknown. Cohesion is checked; correctness
                      is not, and must not be claimed.
    """
    findings, detail = [], {}
    hroot = root / CANONICAL_HELP
    found = read_set(hroot, LOCALE_TABLES)
    for n, v in found.items():
        detail[n] = v["rows"]
    missing = [n for n, v in found.items() if v["rows"] is None]
    if missing:
        findings.append({"check": "LOCALE_SET", "code": "MISSING_LOCALE_TABLE",
                         "severity": "WARN",
                         "message": f"locale companion(s) absent: {', '.join(missing)}"})

    tl_path = find_table(hroot, "HELP_TOPIC_LOCALE")
    ht_path = find_table(hroot, "HELP_TOPIC")
    if not tl_path or not ht_path:
        return findings, detail

    tl, ht = dbf_rows(tl_path), dbf_rows(ht_path)
    if not tl or not ht:
        findings.append({"check": "LOCALE_DRIFT", "code": "UNREADABLE",
                         "severity": "WARN",
                         "message": "HELP_TOPIC_LOCALE or HELP_TOPIC could not be "
                                    "parsed with a width-reconciled layout -- "
                                    "drift NOT checked, do not read this as clean"})
        return findings, detail

    live = {r.get("TOPICKEY", ""): r for r in ht}
    orphans, drifted, badhash = [], [], 0
    src_by_topic = {}
    for r in tl:
        key = r.get("TOPICKEY", "")
        src_by_topic.setdefault(key, set()).add(r.get("SOURCE_HAS", ""))
        loc_title = r.get("LOCALIZED_", "")
        if hashlib.sha256(loc_title.encode()).hexdigest()[:16] != r.get("LOCALIZE~1", ""):
            badhash += 1
        if r.get("LOCALE_ID") != "en-US":
            continue
        if key not in live:
            orphans.append(key)
        else:
            cur = live[key].get("TITLE") or live[key].get("TOPIC") or ""
            if r.get("SOURCE_TIT", "") != cur:
                drifted.append(f"{key} (stored '{r.get('SOURCE_TIT')}' vs live '{cur}')")

    incoherent = [k for k, v in src_by_topic.items() if len(v) > 1]
    detail["locale_drift"] = {"topics_checked": len(src_by_topic),
                              "orphaned": len(orphans), "title_drift": len(drifted),
                              "localized_hash_mismatch": badhash,
                              "source_hash_incoherent": len(incoherent)}

    if orphans:
        findings.append({"check": "LOCALE_DRIFT", "code": "ORPHANED_TOPIC",
                         "severity": "WARN",
                         "message": f"{len(orphans)} locale topic(s) no longer exist in "
                                    f"HELP_TOPIC -- preview falls back silently, which is "
                                    f"indistinguishable from a draft row: {', '.join(orphans)}"})
    if drifted:
        findings.append({"check": "LOCALE_DRIFT", "code": "TITLE_DRIFT",
                         "severity": "WARN",
                         "message": f"{len(drifted)} locale row(s) hold a SOURCE_TITLE that no "
                                    f"longer matches HELP_TOPIC: {'; '.join(drifted)}"})
    if badhash:
        findings.append({"check": "LOCALE_DRIFT", "code": "LOCALIZED_HASH_MISMATCH",
                         "severity": "FAIL",
                         "message": f"{badhash} row(s) where LOCALIZED_HASH != "
                                    f"sha256(LOCALIZED_TITLE)[:16] -- the one hash that IS "
                                    f"recomputable does not reproduce"})
    if incoherent:
        findings.append({"check": "LOCALE_DRIFT", "code": "SOURCE_HASH_INCOHERENT",
                         "severity": "WARN",
                         "message": f"{len(incoherent)} topic(s) whose locale rows disagree on "
                                    f"SOURCE_HASH; one source, one hash: {', '.join(incoherent)}"})
    return findings, detail


def check_cmdhelpchk(transcript: str | None):
    """D. Requires a runtime pass. Never inferred."""
    if not transcript:
        return ([{"check": "CMDHELPCHK", "code": "EXTERNAL_EVIDENCE_REQUIRED",
                  "severity": "WARN",
                  "message": "CMDHELPCHK cannot be asserted from files. Run it and supply "
                             "--cmdhelpchk <transcript>; Gate 3 is not complete without it."}],
                {"supplied": False})
    p = Path(transcript)
    if not p.is_file():
        return ([{"check": "CMDHELPCHK", "code": "TRANSCRIPT_MISSING", "severity": "FAIL",
                  "message": f"transcript not found: {transcript}"}], {"supplied": False})
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    bad = [w for w in ("error", "fail", "mismatch", "missing") if w in low]
    detail = {"supplied": True, "path": str(p), "bytes": len(text),
              "flagged_terms": bad}
    if bad:
        return ([{"check": "CMDHELPCHK", "code": "TRANSCRIPT_NOT_CLEAN", "severity": "WARN",
                  "message": f"transcript contains {', '.join(bad)} -- review before promoting"}],
                detail)
    return ([], detail)


def run(root: Path, baseline, transcript):
    hroot = root / CANONICAL_HELP
    live = read_set(hroot, CORE_TABLES)
    findings, detail = [], {}
    f, d = check_counts(live, baseline);       findings += f; detail["counts"] = d
    f, d = check_shadow(root, live);           findings += f; detail["shadow"] = d
    f, d = check_locale(root);                 findings += f; detail["locale"] = d
    f, d = check_cmdhelpchk(transcript);       findings += f; detail["cmdhelpchk"] = d
    detail["canonical_root"] = CANONICAL_HELP
    detail["canonical_mtimes"] = {k: v["mtime"] for k, v in live.items()}
    counts = {"FAIL": sum(1 for x in findings if x["severity"] == "FAIL"),
              "WARN": sum(1 for x in findings if x["severity"] == "WARN")}
    by_check = {}
    for x in findings:
        by_check[x["check"]] = by_check.get(x["check"], 0) + 1
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "root": str(root), "gate": 3, "tier": "HELP",
            "counts": counts, "by_check": by_check,
            "detail": detail, "findings": findings,
            "_live_counts": {k: v["rows"] for k, v in live.items()}}


def render_markdown(s):
    L = [f"# Gate 3 flush guard -- HELP tier\n",
         f"Generated: {s['generated_at']}  ",
         f"Root: `{s['root']}`  ",
         f"Canonical HELP: `{s['detail']['canonical_root']}`\n",
         f"**FAIL: {s['counts']['FAIL']}  .  WARN: {s['counts']['WARN']}**\n",
         "## Table counts\n", "| table | rows |", "|---|---:|"]
    for k, v in s["_live_counts"].items():
        L.append(f"| {k} | {v if v is not None else 'MISSING'} |")
    L.append("\n## Detail\n```json")
    L.append(json.dumps(s["detail"], indent=2, sort_keys=True))
    L.append("```\n## Findings\n")
    if not s["findings"]:
        L.append("(none)\n")
    else:
        L.append("| severity | check | code | message |")
        L.append("|---|---|---|---|")
        for f in s["findings"]:
            L.append(f"| {f['severity']} | {f['check']} | {f['code']} | "
                     f"{f['message'].replace('|', chr(92) + '|')} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--baseline", default="docs/maintenance/lanes/full_stack_documentation/"
                                          "help_guard_baseline_v1.json")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--cmdhelpchk", default=None,
                    help="path to a CMDHELPCHK transcript (required for a complete Gate 3)")
    ap.add_argument("--strict-shadow", action="store_true",
                    help="treat a divergent shadow HELP set as FAIL")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    bpath = root / args.baseline

    baseline = None
    if bpath.is_file():
        try:
            baseline = json.loads(bpath.read_text(encoding="utf-8"))
        except Exception:
            baseline = None

    s = run(root, baseline, args.cmdhelpchk)

    if args.write_baseline:
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps(
            {"counts": s["_live_counts"], "recorded_at": s["generated_at"]},
            indent=2, sort_keys=True), encoding="utf-8")
        print(f"help-guard: baseline written -> {bpath}")
        for k, v in s["_live_counts"].items():
            print(f"   {k:16} {v}")
        return 0

    if args.json:
        print(json.dumps(s, indent=2, sort_keys=True))
    else:
        print("=== Gate 3 flush guard -- HELP ===")
        print(f"  canonical root : {s['detail']['canonical_root']}")
        print(f"  FAIL / WARN    : {s['counts']['FAIL']} / {s['counts']['WARN']}")
        for k, v in s["_live_counts"].items():
            print(f"     {k:16} {v if v is not None else 'MISSING'}")
        print(f"  baseline       : {'recorded' if baseline else 'NONE (--write-baseline)'}")
        print()
        for f in s["findings"]:
            print(f"  [{f['severity']}] {f['check']}/{f['code']}: {f['message']}")

    if args.out_dir:
        od = Path(args.out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "help_guard_summary.json").write_text(
            json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
        (od / "help_guard_report.md").write_text(render_markdown(s), encoding="utf-8")
        print(f"\nhelp-guard: evidence -> {od}")

    if s["counts"]["FAIL"]:
        return 1
    if args.strict_shadow and any(f["code"] == "DIVERGENT_COPY" for f in s["findings"]):
        print("\nhelp-guard: FAIL -- divergent shadow HELP set (--strict-shadow).", file=sys.stderr)
        return 1
    return 3 if s["counts"]["WARN"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
