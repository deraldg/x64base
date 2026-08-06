import hashlib
import os
import shutil
import sys
from pathlib import Path

import pydottalk
from pydottalk_nonmemo_common import repo_default_sandbox


CASES = [
    {
        "name": "FOX26",
        "dbf": "MEMO_FOX26.dbf",
        "sidecar": "MEMO_FOX26.fpt",
        "scratch": "PYDT_MEMO_DIAG_FOX26",
        "short": "fox26NEW",
        "long": "fox26 memo long update through pydottalk",
    },
    {
        "name": "MSDOS",
        "dbf": "MEMO_MSDOS.dbf",
        "sidecar": "MEMO_MSDOS.dbt",
        "scratch": "PYDT_MEMO_DIAG_MSDOS",
        "short": "msdosNEW",
        "long": "msdos memo long update through pydottalk",
    },
    {
        "name": "VFP",
        "dbf": "MEMO_VFP.dbf",
        "sidecar": "MEMO_VFP.fpt",
        "scratch": "PYDT_MEMO_DIAG_VFP",
        "short": "vfpNEW",
        "long": "vfp memo long update through pydottalk",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_file(path: Path):
    if not path.exists():
        return {"exists": False, "size": None, "sha256": None}
    return {
        "exists": True,
        "size": path.stat().st_size,
        "sha256": sha256(path),
    }


def fget(field, key, default=""):
    if isinstance(field, dict):
        return field.get(key, default)
    return getattr(field, key, default)


def fname(field):
    return str(fget(field, "name", ""))


def ftype(field):
    return str(fget(field, "type", "")).upper()


def find_field(fields, name):
    want = name.upper()
    for i, field in enumerate(fields, start=1):
        if fname(field).upper() == want:
            return i
    raise KeyError(f"field not found: {name}")


def open_area(path: Path):
    area = pydottalk.xbase.DbArea()
    area.open(str(path))
    return area


def read_notes(path: Path, recno: int = 1):
    area = open_area(path)
    try:
        fields = area.fields()
        notes_i = find_field(fields, "NOTES")
        area.goto_rec(recno)
        area.read_current()
        v = area.get(notes_i)
        return "" if v is None else str(v)
    finally:
        area.close()


def write_notes(path: Path, text: str, recno: int = 1):
    area = open_area(path)
    try:
        fields = area.fields()
        notes_i = find_field(fields, "NOTES")

        print("  fields:")
        for i, f in enumerate(fields, start=1):
            print(f"    [{i}] {fname(f)} {ftype(f)}")

        area.goto_rec(recno)
        area.read_current()
        before = "" if area.get(notes_i) is None else str(area.get(notes_i))

        area.set(notes_i, text)
        area.write_current()

        after_same_open = "" if area.get(notes_i) is None else str(area.get(notes_i))

        return before, after_same_open
    finally:
        area.close()


def copy_pair(sandbox: Path, case: dict):
    src_dbf = sandbox / case["dbf"]
    src_sidecar = sandbox / case["sidecar"]

    if not src_dbf.exists():
        raise FileNotFoundError(src_dbf)
    if not src_sidecar.exists():
        raise FileNotFoundError(src_sidecar)

    scratch_dbf = sandbox / f"{case['scratch']}.dbf"
    scratch_sidecar = sandbox / f"{case['scratch']}{src_sidecar.suffix}"

    for p in (scratch_dbf, scratch_sidecar):
        if p.exists():
            p.unlink()

    shutil.copy2(src_dbf, scratch_dbf)
    shutil.copy2(src_sidecar, scratch_sidecar)

    return scratch_dbf, scratch_sidecar


def run_case(sandbox: Path, case: dict):
    print()
    print("=" * 72)
    print("case:", case["name"])

    scratch_dbf, scratch_sidecar = copy_pair(sandbox, case)

    print("scratch DBF    :", scratch_dbf)
    print("scratch sidecar:", scratch_sidecar)

    initial_dbf = stat_file(scratch_dbf)
    initial_sidecar = stat_file(scratch_sidecar)

    print("initial DBF    :", initial_dbf)
    print("initial sidecar:", initial_sidecar)
    print("initial NOTES  :", repr(read_notes(scratch_dbf)))

    print()
    print("SHORT UPDATE:", repr(case["short"]))
    before, after_same_open = write_notes(scratch_dbf, case["short"])
    print("  before same open:", repr(before))
    print("  after same open :", repr(after_same_open))
    print("  after reopen    :", repr(read_notes(scratch_dbf)))
    print("  DBF after short :", stat_file(scratch_dbf))
    print("  sidecar after short:", stat_file(scratch_sidecar))

    print()
    print("LONG UPDATE:", repr(case["long"]))
    before, after_same_open = write_notes(scratch_dbf, case["long"])
    print("  before same open:", repr(before))
    print("  after same open :", repr(after_same_open))
    print("  after reopen    :", repr(read_notes(scratch_dbf)))
    print("  DBF after long  :", stat_file(scratch_dbf))
    print("  sidecar after long:", stat_file(scratch_sidecar))

    print()
    print("delta summary:")
    print("  DBF changed from initial    :", stat_file(scratch_dbf)["sha256"] != initial_dbf["sha256"])
    print("  sidecar changed from initial:", stat_file(scratch_sidecar)["sha256"] != initial_sidecar["sha256"])


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)
    print("scope: legacy memo write diagnostics only; x64 memos skipped")

    sandbox = repo_default_sandbox()

    print("sandbox:", sandbox)

    for case in CASES:
        run_case(sandbox, case)

    print()
    print("OK: legacy memo write diagnostic completed.")
    print("NOTE: This is diagnostic; mismatches are expected until memo write path is fixed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
