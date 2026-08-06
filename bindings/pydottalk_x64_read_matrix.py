#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from pydottalk_nonmemo_common import open_area, repo_default_x64_dir, safe_close, row_dict, field_name, field_type, field_len, fields

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--x64-dir", default=str(repo_default_x64_dir()))
    ap.add_argument("--limit", type=int, default=20)
    ns = ap.parse_args()
    x64_dir = Path(ns.x64_dir)
    candidates = sorted(x64_dir.glob("*.dbf"))[:ns.limit]
    print("PYDOTTALK X64 READ MATRIX")
    print(f"x64_dir: {x64_dir}")
    print(f"candidate_count: {len(candidates)}")
    opened = 0
    failures = 0
    for path in candidates:
        print("")
        print(f"TABLE {path.name}")
        try:
            area = open_area(path)
            try:
                opened += 1
                print(f"  logical_name: {area.logical_name()}")
                print(f"  records: {area.rec_count()}")
                print(f"  rec_length: {area.rec_length()}")
                print(f"  field_count: {area.field_count()}")
                print("  fields:")
                for fd in fields(area):
                    print(f"    {field_name(fd)} {field_type(fd)} {field_len(fd)}")
                if int(area.rec_count()) > 0:
                    area.top()
                    print(f"  first_row: {row_dict(area)}")
                else:
                    print("  first_row: <empty table>")
            finally:
                safe_close(area)
        except Exception as exc:
            failures += 1
            print(f"  ERROR: {type(exc).__name__}: {exc}")
    print(f"opened: {opened}")
    print(f"failures: {failures}")
    if opened == 0:
        raise RuntimeError("no x64 tables opened")
    print("OK: x64 read matrix completed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
