import os
import sys
from pathlib import Path

import pydottalk
from pydottalk_helpers import Table
from pydottalk_nonmemo_common import repo_default_sandbox


def field_type(field):
    return str(getattr(field, "type", "")).upper()


def field_name(field):
    return str(getattr(field, "name", ""))


def field_len(field):
    return getattr(field, "len", getattr(field, "length", ""))


def field_dec(field):
    return getattr(field, "dec", getattr(field, "decimals", ""))


def preview(value, limit=120):
    text = "" if value is None else str(value)
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def inspect_table(path: Path, max_rows: int = 5) -> bool:
    print()
    print("=" * 72)
    print("table:", path)

    with Table(path) as t:
        area = t.area

        print("logical_name:", area.logical_name())
        print("records     :", area.rec_count())
        print("rec_length  :", area.rec_length())
        print("memo_kind   :", area.memo_kind())
        print("memo_path   :", area.memo_path())

        fields = area.fields()
        print("fields:")
        for i, f in enumerate(fields, start=1):
            print(
                f"  [{i}] {field_name(f)} "
                f"{field_type(f)} {field_len(f)} {field_dec(f)}"
            )

        memo_indexes = [
            i
            for i, f in enumerate(fields, start=1)
            if field_type(f) == "M"
        ]

        if not memo_indexes:
            print("memo fields : none")
            return False

        print("memo fields :", ", ".join(field_name(fields[i - 1]) for i in memo_indexes))

        rows_to_read = min(area.rec_count(), max_rows)
        print(f"reading first {rows_to_read} row(s):")

        for recno in range(1, rows_to_read + 1):
            area.goto_rec(recno)
            area.read_current()

            print()
            print(f"recno {area.recno()} deleted={area.is_deleted()}")

            for i in memo_indexes:
                f = fields[i - 1]
                value = area.get(i)
                text = "" if value is None else str(value)

                print(
                    f"  {field_name(f)}: "
                    f"len={len(text)} "
                    f"repr={preview(repr(value), 160)}"
                )

        return True


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)

    sandbox_dir = repo_default_sandbox()

    explicit = os.environ.get("PYDOTTALK_MEMO_DBF", "").strip()
    if explicit:
        candidates = [Path(explicit)]
    else:
        candidates = sorted(sandbox_dir.glob("MEMO_*.dbf"))
        candidates += sorted(sandbox_dir.glob("MEMO_*.DBF"))

    # De-duplicate case-insensitively.
    seen = set()
    unique_candidates = []
    for p in candidates:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique_candidates.append(p)

    print("sandbox:", sandbox_dir)
    print("candidate count:", len(unique_candidates))
    for p in unique_candidates:
        print(" -", p)

    if not unique_candidates:
        raise FileNotFoundError(
            f"no MEMO_*.dbf candidates found under sandbox: {sandbox_dir}"
        )

    memo_tables_seen = 0
    failures = 0

    for path in unique_candidates:
        try:
            if inspect_table(path):
                memo_tables_seen += 1
        except Exception as exc:
            failures += 1
            print()
            print("=" * 72)
            print("FAILED:", path)
            print(type(exc).__name__ + ":", exc)

    print()
    print("=" * 72)
    print("memo tables with M fields:", memo_tables_seen)
    print("failures:", failures)

    if memo_tables_seen == 0:
        raise RuntimeError("no readable memo-field tables were found")

    if failures:
        raise RuntimeError(f"{failures} memo candidate(s) failed")

    print()
    print("OK: sandbox memo read smoke completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
