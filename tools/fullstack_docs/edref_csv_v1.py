#!/usr/bin/env python3
"""edref_csv_v1 -- move the EDREF catalog between edref.hpp and CSV.

WHY
    include/edref.hpp is 1100+ lines of raw string literals at 29 entries. At
    textbook size it stops being reviewable: a one-word fix to a summary
    rebuilds the CLI, and a diff of the file is unreadable. The project already
    solved this shape once -- SYSFUNC lives in
    dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv and is seeded into a
    DBF.

THE DIRECTION MATTERS, AND THIS TOOL DOES NOT PICK IT YET
    Two designs were on the table:

      A. CSV is source; a generator emits edref.hpp; help stays COMPILED IN.
      B. CSV seeds a DBF; the engine reads the catalog at RUNTIME.

    B is the more interesting one -- the teaching material for a database
    engine, stored in that engine, queryable with the commands it teaches. But
    it makes HELP depend on data files being present, and the lean edition
    already ships without the Bible SQLite. Help that can be absent is a
    different product decision than help that cannot.

    So this tool deliberately does only the reversible half: export and import,
    with a proven round trip. Neither the build nor the runtime changes. When
    the direction is chosen, the pipeline is already here and verified, and the
    choice is a small change rather than a migration.

USAGE
    edref_csv_v1.py export --out <file.csv>
    edref_csv_v1.py verify            # export, re-import, compare -- no writes

Exit codes:
  0 ok
  1 round trip lost or altered data
  2 usage or environment error
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edrefcheck_v1 import parse_catalog, repo_root  # noqa: E402

COLUMNS = [
    "topic",
    "syntax",
    "kind",
    "level",
    "sequence",
    "prereq",
    "script_ref",
    "lab_ref",
    "supported",
    "summary",
]


def export_rows(root: Path) -> list[dict]:
    state, entries = parse_catalog(root / "include" / "edref.hpp")
    if state != "populated":
        raise SystemExit(f"edref_csv: catalog state = {state}; nothing to export")
    rows = []
    for e in entries:
        rows.append(
            {
                "topic": e["topic"],
                "syntax": e["syntax"],
                "kind": e["kind"],
                "level": e["level"],
                "sequence": e["sequence"],
                "prereq": e["prereq"],
                "script_ref": e["script_ref"],
                "lab_ref": e["lab_ref"],
                "supported": "true" if e["supported"] else "false",
                # Summaries are multi-line prose. csv handles embedded newlines
                # correctly when quoted; this is why the file must be read with
                # a real CSV parser and never with split(",").
                "summary": e["summary"],
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    # newline="" is required by the csv module; without it Windows doubles the
    # line endings inside quoted multi-line fields and the round trip fails in
    # a way that looks like data corruption.
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verify(root: Path) -> int:
    import io

    original = export_rows(root)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in original:
        w.writerow(r)
    buf.seek(0)
    reread = list(csv.DictReader(buf))

    problems: list[str] = []
    if len(original) != len(reread):
        problems.append(f"count changed: {len(original)} -> {len(reread)}")
    for a, b in zip(original, reread):
        for col in COLUMNS:
            if str(a[col]) != str(b[col]):
                problems.append(
                    f"{a['topic']}.{col}: {len(str(a[col]))} chars -> "
                    f"{len(str(b[col]))} chars"
                )
    print(f"edref_csv: {len(original)} entries exported")
    print(f"edref_csv: summary bytes total = {sum(len(r['summary']) for r in original)}")
    if problems:
        for p in problems:
            print(f"edref_csv: LOSS: {p}", file=sys.stderr)
        print(f"edref_csv: FAIL -- {len(problems)} field(s) altered", file=sys.stderr)
        return 1
    print("edref_csv: round trip clean -- every field byte-identical")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["export", "verify"])
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else repo_root(Path(__file__).resolve().parent)

    if args.mode == "verify":
        return verify(root)

    if not args.out:
        print("edref_csv: --out is required for export", file=sys.stderr)
        return 2
    rows = export_rows(root)
    write_csv(rows, Path(args.out))
    print(f"edref_csv: wrote {len(rows)} entries to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
