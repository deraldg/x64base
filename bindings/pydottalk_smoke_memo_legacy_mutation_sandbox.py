import os
import shutil
import sys
from pathlib import Path

import pydottalk
from pydottalk_nonmemo_common import repo_default_sandbox


LEGACY_MEMO_CASES = [
    {
        "name": "FOX26",
        "dbf": "MEMO_FOX26.dbf",
        "sidecar": "MEMO_FOX26.fpt",
        "scratch_stem": "PYDT_MEMO_MUT_FOX26",
        "original": "fox26 memo",
        "updated": "fox26 memo updated by pydottalk",
        "appended": "fox26 memo appended by pydottalk",
    },
    {
        "name": "MSDOS",
        "dbf": "MEMO_MSDOS.dbf",
        "sidecar": "MEMO_MSDOS.dbt",
        "scratch_stem": "PYDT_MEMO_MUT_MSDOS",
        "original": "msdos memo",
        "updated": "msdos memo updated by pydottalk",
        "appended": "msdos memo appended by pydottalk",
    },
    {
        "name": "VFP",
        "dbf": "MEMO_VFP.dbf",
        "sidecar": "MEMO_VFP.fpt",
        "scratch_stem": "PYDT_MEMO_MUT_VFP",
        "original": "vfp memo o",
        "updated": "vfp memo updated by pydottalk",
        "appended": "vfp memo appended by pydottalk",
    },
]


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


def open_area(path: Path):
    area = pydottalk.xbase.DbArea()
    area.open(str(path))
    return area


def copy_pair(sandbox: Path, case: dict):
    src_dbf = sandbox / case["dbf"]
    src_sidecar = sandbox / case["sidecar"]

    if not src_dbf.exists():
        raise FileNotFoundError(f"source DBF not found: {src_dbf}")

    if not src_sidecar.exists():
        raise FileNotFoundError(f"source memo sidecar not found: {src_sidecar}")

    ext = src_sidecar.suffix
    scratch_dbf = sandbox / f"{case['scratch_stem']}.dbf"
    scratch_sidecar = sandbox / f"{case['scratch_stem']}{ext}"

    for p in (scratch_dbf, scratch_sidecar):
        if p.exists():
            p.unlink()

    shutil.copy2(src_dbf, scratch_dbf)
    shutil.copy2(src_sidecar, scratch_sidecar)

    return src_dbf, src_sidecar, scratch_dbf, scratch_sidecar


def get_indexes(area):
    fields = area.fields()

    print("fields:")
    for i, field in enumerate(fields, start=1):
        print(f"  [{i}] {fname(field)} {ftype(field)} {flen(field)} {fdec(field)}")

    id_i = find_field(fields, "ID")
    title_i = find_field(fields, "TITLE")
    notes_i = find_field(fields, "NOTES")

    if ftype(fields[notes_i - 1]) != "M":
        raise RuntimeError(f"NOTES is not M type: {ftype(fields[notes_i - 1])}")

    return id_i, title_i, notes_i


def read_notes(area, notes_i, recno):
    area.goto_rec(recno)
    area.read_current()
    value = area.get(notes_i)
    return "" if value is None else str(value)


def verify_notes(path: Path, recno: int, expected: str, deleted_expected=None):
    area = open_area(path)
    try:
        _, _, notes_i = get_indexes(area)
        area.goto_rec(recno)
        area.read_current()

        text = "" if area.get(notes_i) is None else str(area.get(notes_i))
        deleted = area.is_deleted()

        print(f"verify recno {recno} deleted={deleted} NOTES={text!r}")

        if text != expected:
            raise RuntimeError(
                f"memo mismatch at recno {recno}: expected {expected!r}, got {text!r}"
            )

        if deleted_expected is not None and deleted != deleted_expected:
            raise RuntimeError(
                f"delete flag mismatch at recno {recno}: "
                f"expected {deleted_expected}, got {deleted}"
            )

    finally:
        area.close()


def run_case(sandbox: Path, case: dict):
    print()
    print("=" * 72)
    print("case:", case["name"])

    src_dbf, src_sidecar, scratch_dbf, scratch_sidecar = copy_pair(sandbox, case)

    print("source DBF     :", src_dbf)
    print("source sidecar :", src_sidecar)
    print("scratch DBF    :", scratch_dbf)
    print("scratch sidecar:", scratch_sidecar)
    print("NOTE           : mutation smoke uses copied DBF+memo sidecar only")

    # Phase 1: open copied pair and verify original memo payload.
    area = open_area(scratch_dbf)
    try:
        print("logical_name:", area.logical_name())
        print("records     :", area.rec_count())
        print("rec_length  :", area.rec_length())
        print("memo_kind   :", area.memo_kind())
        print("memo_path   :", area.memo_path())

        id_i, title_i, notes_i = get_indexes(area)

        before_count = area.rec_count()
        if before_count < 1:
            raise RuntimeError("memo fixture unexpectedly has no records")

        original = read_notes(area, notes_i, 1)
        print("original recno 1 NOTES:", repr(original))

        if original != case["original"]:
            raise RuntimeError(
                f"original payload mismatch: expected {case['original']!r}, got {original!r}"
            )

        # Phase 2: update existing memo.
        area.goto_rec(1)
        area.read_current()
        area.set(notes_i, case["updated"])
        area.write_current()
        print("updated recno 1 NOTES")

    finally:
        area.close()

    # Reopen verify update.
    verify_notes(scratch_dbf, 1, case["updated"], deleted_expected=False)

    # Phase 3: append a new memo record.
    area = open_area(scratch_dbf)
    try:
        id_i, title_i, notes_i = get_indexes(area)

        before_append_count = area.rec_count()

        area.append_blank()
        appended_recno = area.recno()

        area.set(id_i, "99")
        area.set(title_i, "PYDT_APPEND")
        area.set(notes_i, case["appended"])
        area.write_current()

        after_append_count = area.rec_count()

        print("before append rec_count:", before_append_count)
        print("after append rec_count :", after_append_count)
        print("appended recno         :", appended_recno)

        if after_append_count != before_append_count + 1:
            raise RuntimeError(
                f"append count mismatch: {before_append_count} -> {after_append_count}"
            )

    finally:
        area.close()

    # Reopen verify append.
    verify_notes(scratch_dbf, appended_recno, case["appended"], deleted_expected=False)

    # Phase 4: delete appended memo record.
    area = open_area(scratch_dbf)
    try:
        _, _, notes_i = get_indexes(area)

        count_before_delete = area.rec_count()
        area.goto_rec(appended_recno)
        area.read_current()

        text_before_delete = "" if area.get(notes_i) is None else str(area.get(notes_i))
        print("before delete appended NOTES:", repr(text_before_delete))
        print("before delete is_deleted    :", area.is_deleted())

        if text_before_delete != case["appended"]:
            raise RuntimeError(
                f"wrong record targeted for delete: expected appended memo "
                f"{case['appended']!r}, got {text_before_delete!r}"
            )

        area.delete_current()

        print("after delete is_deleted     :", area.is_deleted())
        print("after delete rec_count      :", area.rec_count())

        if not area.is_deleted():
            raise RuntimeError("delete_current() did not mark appended record deleted")

        if area.rec_count() != count_before_delete:
            raise RuntimeError(
                f"delete changed record count unexpectedly: "
                f"{count_before_delete} -> {area.rec_count()}"
            )

    finally:
        area.close()

    # Reopen verify delete flag and memo payload still readable at physical recno.
    verify_notes(
        scratch_dbf,
        appended_recno,
        case["appended"],
        deleted_expected=True,
    )

    print("OK:", case["name"], "legacy memo mutation smoke completed")


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)
    print("scope: legacy 32-bit/sidecar memos only; x64 memos intentionally skipped")

    sandbox = repo_default_sandbox()

    print("sandbox:", sandbox)

    failures = 0

    for case in LEGACY_MEMO_CASES:
        try:
            run_case(sandbox, case)
        except Exception as exc:
            failures += 1
            print()
            print("FAILED:", case["name"])
            print(type(exc).__name__ + ":", exc)

    print()
    print("=" * 72)
    print("failures:", failures)

    if failures:
        raise RuntimeError(f"{failures} legacy memo mutation failure(s)")

    print()
    print("OK: legacy memo mutation smoke completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
