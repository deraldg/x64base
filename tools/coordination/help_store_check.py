#!/usr/bin/env python3
"""Does every HELP_LINE row know which topic it belongs to? Ask the tables, not the engine.

WHY THIS EXISTS. On 2026-08-24 the HELP store held 2,757 line rows -- 9.4% of
it -- that no operator could reach, because their TOPICKEY was blank. The whole
SHARED_MSG bucket, every row of it. The condition had been reproducible across
five rebuilds since at least 2026-08-05 and nothing failed: CMDHELPCHK reported
"OK no structural issues found", and the only surface that named the problem
printed it as `SHARED_MSG [lines=2637, topics=0]` -- a zero in a column, next to
seven buckets with positive counts. See AIF-126.

Three properties this checker has that the existing gates did not:

  IT READS THE TABLES DIRECTLY. No engine, no build, no rebuilt store. A DBF
  header/record walk in the standard library. It runs in a sandbox that cannot
  compile, which is exactly where a lot of this lane's verification happens.

  IT COMPARES TWO TABLES. Every gate that passed over this defect looked at one
  table at a time. The defect lives in the JOIN: headers in HELP_TOPIC, lines in
  HELP_LINE, and a blank key between them. Nothing that reads one table can see
  it.

  IT DIFFS TOPIC SETS, NOT TOPIC COUNTS. A count floor scores a repair as a
  regression -- it did exactly that on 2026-08-24, when five bogus command rows
  were correctly withdrawn and the topic total fell below the Gate 4 floor. A
  set diff names every departure and lets a human disposition it. Floors are for
  quantities that only grow; membership is not one of them.

  $py12 tools\\coordination\\help_store_check.py
  $py12 tools\\coordination\\help_store_check.py --store <dir>
  $py12 tools\\coordination\\help_store_check.py --against <dir>   -- topic-set diff
  $py12 tools\\coordination\\help_store_check.py --json

Exit codes: 0 clean, 1 defect found, 2 could not read the store.
"""
import argparse
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "dottalkpp" / "data" / "help"


# --- DBF reader ------------------------------------------------------------
# Deliberately minimal and dependency-free. Reads the 32-byte header, the field
# descriptor array, then fixed-length records. Byte 0 of a record is the
# deletion flag. Bytes 1-3 of the header are the generation date, which is a
# free freshness stamp: a store that did not rebuild carries the old date.

def read_dbf(path, want=None):
    with open(path, "rb") as f:
        head = f.read(32)
        if len(head) < 32:
            raise ValueError("short header: %s" % path)
        year, month, day = head[1], head[2], head[3]
        nrec = struct.unpack("<I", head[4:8])[0]
        hdrlen = struct.unpack("<H", head[8:10])[0]
        reclen = struct.unpack("<H", head[10:12])[0]
        fields = []
        while True:
            fd = f.read(32)
            if not fd or fd[0:1] == b"\r":
                break
            name = fd[0:11].split(b"\x00")[0].decode("latin1")
            fields.append((name, fd[16]))
        offsets, pos = {}, 1
        for name, flen in fields:
            offsets[name] = (pos, flen)
            pos += flen
        cols = want or [n for n, _ in fields]
        rows = []
        f.seek(hdrlen)
        for _ in range(nrec):
            rec = f.read(reclen)
            if len(rec) < reclen:
                break
            if rec[0:1] == b"*":
                continue
            row = {}
            for c in cols:
                if c not in offsets:
                    row[c] = ""
                    continue
                o, l = offsets[c]
                row[c] = rec[o:o + l].decode("latin1").strip()
            rows.append(row)
    gen = "%04d-%02d-%02d" % (1900 + year if year >= 100 else 2000 + year, month, day)
    return {"gen": gen, "declared": nrec, "rows": rows,
            "fields": [n for n, _ in fields]}


def as_int(s):
    s = s.strip()
    return int(s) if s.lstrip("-").isdigit() else 0


# --- the checks ------------------------------------------------------------

def inspect(store):
    store = pathlib.Path(store)
    line_p = store / "HELP_LINE.dbf"
    topic_p = store / "HELP_TOPIC.dbf"
    for p in (line_p, topic_p):
        if not p.exists():
            raise IOError("not a help store, missing %s" % p.name)

    lines = read_dbf(line_p, ["TOPICKEY", "SOURCE", "CATALOG"])
    topics = read_dbf(topic_p, ["TOPICKEY", "SECTIONS", "LINES", "STATUS", "CONFID"])

    keyed, blank, by_source = set(), [], {}
    for r in lines["rows"]:
        k = r["TOPICKEY"]
        if k:
            keyed.add(k)
        else:
            blank.append(r)
            by_source[r["SOURCE"]] = by_source.get(r["SOURCE"], 0) + 1

    header_keys = set(r["TOPICKEY"] for r in topics["rows"] if r["TOPICKEY"])
    orphan_headers = sorted(header_keys - keyed)
    orphan_lines = sorted(keyed - header_keys)
    claimed = sum(as_int(r["LINES"]) for r in topics["rows"]
                  if r["TOPICKEY"] in set(orphan_headers))

    both = [r["TOPICKEY"] for r in topics["rows"]
            if r["STATUS"] == "pending" and r["CONFID"] == "AUTHORITATIVE"]

    return {
        "store": str(store),
        "line_gen": lines["gen"], "topic_gen": topics["gen"],
        "line_rows": len(lines["rows"]), "topic_rows": len(topics["rows"]),
        "topics_reachable": len(keyed),
        "blank_key_rows": len(blank),
        "blank_key_by_source": by_source,
        "orphan_headers": orphan_headers,
        "orphan_header_claimed_lines": claimed,
        "orphan_lines": orphan_lines,
        "pending_and_authoritative": len(both),
        "topic_set": sorted(keyed),
    }


def report(d, against=None):
    bad = []
    print("HELP store check -- %s" % d["store"])
    print("  generation   : HELP_LINE %s   HELP_TOPIC %s"
          % (d["line_gen"], d["topic_gen"]))
    if d["line_gen"] != d["topic_gen"]:
        bad.append("the two tables were generated on different dates")
    print("  rows         : HELP_LINE %d   HELP_TOPIC %d"
          % (d["line_rows"], d["topic_rows"]))
    print("  reachable    : %d topics" % d["topics_reachable"])
    print()

    if d["blank_key_rows"]:
        pct = 100.0 * d["blank_key_rows"] / max(1, d["line_rows"])
        print("  DEFECT  %d HELP_LINE rows have a BLANK TOPICKEY (%.1f%% of the store)"
              % (d["blank_key_rows"], pct))
        for src, n in sorted(d["blank_key_by_source"].items(), key=lambda kv: -kv[1]):
            print("            %-16s %d" % (src or "(no SOURCE)", n))
        print("          No operator can reach these rows through any command.")
        bad.append("blank TOPICKEY on %d line rows" % d["blank_key_rows"])
    else:
        print("  ok      every HELP_LINE row names a topic")

    if d["orphan_headers"]:
        print()
        print("  DEFECT  %d HELP_TOPIC headers have no lines, and claim %d between them"
              % (len(d["orphan_headers"]), d["orphan_header_claimed_lines"]))
        for k in d["orphan_headers"][:12]:
            print("            %s" % k)
        if len(d["orphan_headers"]) > 12:
            print("            ... and %d more" % (len(d["orphan_headers"]) - 12))
        bad.append("%d headers with no reachable lines" % len(d["orphan_headers"]))

    if d["orphan_lines"]:
        print()
        print("  DEFECT  %d topic keys appear in HELP_LINE with no HELP_TOPIC header"
              % len(d["orphan_lines"]))
        for k in d["orphan_lines"][:12]:
            print("            %s" % k)
        bad.append("%d line keys with no header" % len(d["orphan_lines"]))

    if d["pending_and_authoritative"]:
        print()
        print("  WARN    %d rows are STATUS=pending and CONFID=AUTHORITATIVE at once"
              % d["pending_and_authoritative"])
        print("          The store says the same content is settled and unwritten.")

    if against:
        print()
        print("  topic-set diff against %s" % against["store"])
        a, b = set(against["topic_set"]), set(d["topic_set"])
        gone, new = sorted(a - b), sorted(b - a)
        if not gone and not new:
            print("            identical (%d topics)" % len(b))
        for k in gone:
            print("            LOST   %s" % k)
        for k in new:
            print("            GAINED %s" % k)
        print("            net %+d  (%d -> %d)" % (len(b) - len(a), len(a), len(b)))
        print()
        print("          A departure is not a failure. Name each one and")
        print("          disposition it. Do NOT gate on the count.")

    print()
    if bad:
        print("RESULT: %d defect class(es) -- %s" % (len(bad), "; ".join(bad)))
    else:
        print("RESULT: clean")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--against", default=None,
                    help="a second store directory to diff topic SETS against")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        d = inspect(a.store)
        other = inspect(a.against) if a.against else None
    except (IOError, ValueError) as e:
        sys.stderr.write("help_store_check: %s\n" % e)
        return 2
    if a.json:
        out = {"store": d, "against": other}
        for side in (out["store"], out["against"]):
            if side:
                side.pop("topic_set", None)
        print(json.dumps(out, indent=2, sort_keys=True))
        return 1 if (d["blank_key_rows"] or d["orphan_headers"] or d["orphan_lines"]) else 0
    return report(d, other)


if __name__ == "__main__":
    sys.exit(main())
