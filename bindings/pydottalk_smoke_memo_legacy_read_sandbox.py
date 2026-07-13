import os
import sys
from pathlib import Path

import pydottalk
from pydottalk_nonmemo_common import repo_default_sandbox


EXPECTED = {
    "MEMO_FOX26.dbf": "fox26 memo",
    "MEMO_MSDOS.dbf": "msdos memo",
    "MEMO_VFP.dbf": "vfp memo o",
}


def fget(field, key, default=""):
    if isinstance(field, dict):
        return field.get(key, default)
    return getattr(field, key, default)


def fname(field):
    return str(fget(field, "name", ""))


def ftype(field):
    return str(fget(field, "type", "")).upper()


def flen(field):
    return fget(field, "length", fget(field, "len", ""))


def fdec(field):
    return fget(field, "decimals", fget(field, "dec", ""))


def find_field(fields, name):
    want = name.upper()
    for i, field in enumerate(fields, start=1):
        if fname(field).upper() == want:
            return i
    raise KeyError(f"field not found: {name}")


def check_table(path: Path, expected: str) -> None:
    print()
    print("=" * 72)
    print("table:", path)

    area = pydottalk.xbase.DbArea()
    area.open(str(path))

    try:
        print("logical_name:", area.logical_name())
        print("records     :", area.rec_count())
        print("rec_length  :", area.rec_length())
        print("memo_kind   :", area.memo_kind())
        print("memo_path   :", area.memo_path())

        fields = area.fields()
        print("fields:")
        for i, field in enumerate(fields, start=1):
            print(f"  [{i}] {fname(field)} {ftype(field)} {flen(field)} {fdec(field)}")

        notes_i = find_field(fields, "NOTES")
        if ftype(fields[notes_i - 1]) != "M":
            raise RuntimeError(f"NOTES is not M type: {ftype(fields[notes_i - 1])}")

        area.goto_rec(1)
        area.read_current()

        value = area.get(notes_i)
        text = "" if value is None else str(value)

        print("NOTES repr:", repr(value))
        print("NOTES text:", text)

        if text != expected:
            raise RuntimeError(f"expected {expected!r}, got {text!r}")

        print("OK:", path.name)

    finally:
        area.close()


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)

    sandbox = repo_default_sandbox()

    failures = 0

    for filename, expected in EXPECTED.items():
        path = sandbox / filename
        if not path.exists():
            print("MISSING:", path)
            failures += 1
            continue

        try:
            check_table(path, expected)
        except Exception as exc:
            print("FAILED:", path)
            print(type(exc).__name__ + ":", exc)
            failures += 1

    print()
    print("=" * 72)
    print("failures:", failures)

    if failures:
        raise RuntimeError(f"{failures} legacy memo read failure(s)")

    print("OK: legacy memo read smoke completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
