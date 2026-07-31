#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import importlib
import json
import shutil
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List


PROBE_ROWS = [
    {
        "PROBEID": "P001",
        "TITLE": "DotTalk CREATE X64 memo import probe",
        "NOTES": "First memo row loaded through DotTalk++ IMPORT after CREATE X64.",
    },
    {
        "PROBEID": "P002",
        "TITLE": "Second memo row with comma",
        "NOTES": "Memo text includes a comma, quotes, and UTF-8-ish source characters for CSV parser proof.",
    },
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return str(value)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv_dict(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def assert_probe_path(repo: Path, probe_path: Path) -> None:
    try:
        rel = probe_path.resolve().relative_to(repo.resolve()).as_posix().lower()
    except Exception:
        raise SystemExit(f"Probe path must be inside repo: {probe_path}")
    allowed = "dottalkpp/data/metadata/datadict_create_probe"
    if rel != allowed and not rel.startswith(allowed + "/"):
        raise SystemExit(f"Refusing write/read outside DD-046 probe path: {rel}")


def harden_pydottalk_path(repo: Path) -> Dict[str, Any]:
    build_python = repo / "build" / "python"
    added = 0
    if build_python.exists():
        bp = str(build_python.resolve())
        if bp not in sys.path:
            sys.path.insert(0, bp)
            added = 1
    return {
        "build_python_path": str(build_python),
        "build_python_exists": int(build_python.exists()),
        "added_to_sys_path": added,
    }


def emit_dottalk_commands(path: Path, probe_slot: str, import_csv: Path) -> None:
    text = "\n".join([
        "* DD-046 v1.1 DotTalk++ X64 CREATE / IMPORT / Memo / Index probe",
        "setpath dbf " + probe_slot,
        "create x64 ddprobe (probeid C(20), title C(80), notes M)",
        "import " + str(import_csv),
        "count",
        "goto 1",
        "tup",
        "goto 2",
        "tup",
        "* Optional/manual index probe:",
        "index on probeid tag probeid",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def emit_pydottalk_probe(path: Path) -> None:
    lines = [
        "#!/usr/bin/env python3",
        "from __future__ import annotations",
        "import argparse",
        "import sys",
        "from pathlib import Path",
        "",
        "def harden(repo: Path):",
        "    bp = repo / 'build' / 'python'",
        "    if bp.exists() and str(bp) not in sys.path:",
        "        sys.path.insert(0, str(bp))",
        "",
        "def main() -> int:",
        "    ap = argparse.ArgumentParser(description='DD-046 v1.1 pydottalk readback probe')",
        "    ap.add_argument('--repo-root', default=r'D:\\code\\ccode')",
        "    ap.add_argument('--try-memo-mutation', action='store_true')",
        "    args = ap.parse_args()",
        "    repo = Path(args.repo_root)",
        "    harden(repo)",
        "    import pydottalk",
        "    dbf = repo / 'dottalkpp' / 'data' / 'metadata' / 'datadict_create_probe' / 'DDPROBE.dbf'",
        "    print('DD-046 v1.1 pydottalk probe')",
        "    print('pydottalk:', getattr(pydottalk, '__version__', '<no version>'))",
        "    print('dbf:', dbf)",
        "    print('exists:', dbf.exists())",
        "    a = pydottalk.Dbf()",
        "    a.open(str(dbf))",
        "    print('isOpen:', a.isOpen())",
        "    print('recCount:', a.recCount())",
        "    print('fieldCount:', a.fieldCount())",
        "    print('memoPath:', str(getattr(a, 'memoPath', lambda: '')()))",
        "    print('memoKind:', str(getattr(a, 'memoKind', lambda: '')()))",
        "    print('fields:', list(a.fields()))",
        "    a.top()",
        "    print('first:', a.readCurrent())",
        "    a.close()",
        "    return 0",
        "",
        "if __name__ == '__main__':",
        "    raise SystemExit(main())",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def read_dbf_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read(8192)
    if len(data) < 32:
        raise ValueError(f"Too small for DBF header: {path}")
    version = data[0]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    field_count = (header_len - 33) // 32
    fields = []
    off = 32
    for _ in range(field_count):
        desc = data[off:off+32]
        raw_name = desc[0:11].split(b"\x00", 1)[0]
        fields.append({
            "name": raw_name.decode("ascii", errors="ignore"),
            "type": chr(desc[11]),
            "width": desc[16],
            "decimals": desc[17],
        })
        off += 32
    return {
        "version": version,
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "field_count": field_count,
        "fields": fields,
    }


def inspect_probe_files(repo: Path, probe_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not probe_dir.exists():
        return rows
    for p in sorted(probe_dir.iterdir(), key=lambda q: q.name.lower()):
        if not p.is_file():
            continue
        rows.append({
            "file": p.name,
            "path": safe_rel(repo, p),
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    return rows


def same_stem_sidecars(files: List[Dict[str, Any]], stem: str = "ddprobe") -> List[Dict[str, Any]]:
    out = []
    for row in files:
        name = str(row.get("file", ""))
        p = Path(name)
        if p.stem.lower() == stem.lower() and p.suffix.lower() != ".dbf":
            out.append(row)
    return out


def try_pydottalk_readback(repo: Path, probe_dir: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "attempted": 1,
        "import_ok": 0,
        "open_ok": 0,
        "rec_count": "",
        "field_count": "",
        "memo_path": "",
        "memo_kind": "",
        "first_record": "",
        "second_record": "",
        "memo_content_hint": 0,
        "error": "",
    }
    try:
        harden_pydottalk_path(repo)
        mod = importlib.import_module("pydottalk")
        out["import_ok"] = 1
        dbf_path = probe_dir / "DDPROBE.dbf"
        if not dbf_path.exists():
            dbf_path = probe_dir / "ddprobe.dbf"
        a = mod.Dbf()
        a.open(str(dbf_path))
        out["open_ok"] = int(a.isOpen())
        out["rec_count"] = int(a.recCount())
        out["field_count"] = int(a.fieldCount())
        try:
            out["memo_path"] = str(a.memoPath())
        except Exception:
            out["memo_path"] = ""
        try:
            out["memo_kind"] = str(a.memoKind())
        except Exception:
            out["memo_kind"] = ""
        a.top()
        first = repr(a.readCurrent())
        out["first_record"] = first
        try:
            a.gotoRec(2)
            second = repr(a.readCurrent())
        except Exception:
            second = ""
        out["second_record"] = second
        if "First memo row loaded" in first or "Memo text includes" in second:
            out["memo_content_hint"] = 1
        a.close()
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-046 v1.1 DotTalk++ X64 CREATE / IMPORT / Memo / Index probe evidence tool")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD046-v1_1-dottalk-x64-create-import-memo-index-probe-v0")
    ap.add_argument("--probe-slot", default="metadata\\datadict_create_probe")
    ap.add_argument("--probe-dir", default="dottalkpp/data/metadata/datadict_create_probe")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--prepare-probe-files", action="store_true")
    ap.add_argument("--replace-probe-dir", action="store_true")
    ap.add_argument("--inspect-after-runtime", action="store_true")
    ap.add_argument("--pydottalk-readback", action="store_true")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    probe_dir = (repo / args.probe_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert_probe_path(repo, probe_dir)

    csv_out = out / "dd046_ddprobe_import.csv"
    dts_out = out / "dd046_dottalk_x64_create_import_probe.dts"
    pydt_out = out / "dd046_pydottalk_probe.py"

    write_csv_dict(csv_out, PROBE_ROWS, ["PROBEID", "TITLE", "NOTES"])
    emit_dottalk_commands(dts_out, args.probe_slot, csv_out)
    emit_pydottalk_probe(pydt_out)

    prepared_files: List[Dict[str, Any]] = []
    if args.prepare_probe_files:
        if probe_dir.exists() and args.replace_probe_dir:
            shutil.rmtree(probe_dir)
        probe_dir.mkdir(parents=True, exist_ok=True)
        import_csv = probe_dir / "ddprobe_import.csv"
        write_csv_dict(import_csv, PROBE_ROWS, ["PROBEID", "TITLE", "NOTES"])
        emit_dottalk_commands(probe_dir / "dd046_dottalk_x64_create_import_probe.dts", args.probe_slot, import_csv)
        emit_pydottalk_probe(probe_dir / "dd046_pydottalk_probe.py")
        prepared_files = inspect_probe_files(repo, probe_dir)

    inspection: Dict[str, Any] = {}
    inspection_failures = 0
    if args.inspect_after_runtime:
        dbf = probe_dir / "DDPROBE.dbf"
        if not dbf.exists():
            dbf = probe_dir / "ddprobe.dbf"
        if not dbf.exists():
            inspection = {"status": "MISSING_DDPROBE_DBF", "dbf_exists": 0}
            inspection_failures += 1
        else:
            try:
                hdr = read_dbf_header(dbf)
                files = inspect_probe_files(repo, probe_dir)
                sidecars = same_stem_sidecars(files, "ddprobe")
                inspection = {
                    "status": "PASS" if hdr["records"] >= 2 and hdr["field_count"] == 3 and sidecars else "REVIEW",
                    "dbf_exists": 1,
                    "dbf_path": safe_rel(repo, dbf),
                    "records": hdr["records"],
                    "field_count": hdr["field_count"],
                    "fields": hdr["fields"],
                    "same_stem_sidecars": sidecars,
                    "files": files,
                }
                if inspection["status"] != "PASS":
                    inspection_failures += 1
            except Exception as exc:
                inspection = {"status": "READ_ERROR", "error": f"{type(exc).__name__}: {exc}"}
                inspection_failures += 1

    pydt = {"attempted": 0}
    pydt_failures = 0
    if args.pydottalk_readback:
        pydt = try_pydottalk_readback(repo, probe_dir)
        if not (pydt.get("import_ok") == 1 and pydt.get("open_ok") == 1 and int(pydt.get("rec_count") or 0) >= 2):
            pydt_failures += 1

    boundary_rows = [
        {"boundary": "evidence_tool_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "probe_directory_only_when_preparing", "observed": int(args.prepare_probe_files), "required": "0 or 1 depending on flag", "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "datadict_sandbox_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "meta_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv_dict(out / "dd046_prepared_probe_file_ledger.csv", prepared_files, ["file", "path", "bytes", "sha256"])
    write_csv_dict(out / "dd046_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_json(out / "dd046_runtime_inspection.json", inspection)
    write_json(out / "dd046_pydottalk_readback.json", pydt)

    failures = inspection_failures + pydt_failures
    if args.inspect_after_runtime or args.pydottalk_readback:
        status = "DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_GREEN" if failures == 0 else "DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_REVIEW"
    elif args.prepare_probe_files:
        status = "DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_READY"
    else:
        status = "DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_PLAN_READY"

    manifest = {
        "contract": "dd046_v1_1_probe_evidence_tool_hardening_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "probe_slot": args.probe_slot,
        "probe_dir": str(probe_dir),
        "profiles": args.profile,
        "prepare_probe_files": int(args.prepare_probe_files),
        "replace_probe_dir": int(args.replace_probe_dir),
        "inspect_after_runtime": int(args.inspect_after_runtime),
        "pydottalk_readback": int(args.pydottalk_readback),
        "failures": failures,
        "active_catalog_mutation": 0,
        "datadict_sandbox_mutation": 0,
        "help_meta_cmdhelpchk_mutations": 0,
        "lmdb_build": 0,
        "source_edits": 0,
        "next_recommended_package": "DD-049 shared helper cleanup or DD-050 canonical catalog rebuild plan after evidence closure",
    }
    write_json(out / "dd046_dottalk_x64_create_import_probe_manifest.json", manifest)

    report = "\n".join([
        "# DD-046 v1.1 DotTalk++ X64 CREATE / IMPORT / Memo / Index Probe Evidence",
        "",
        f"Run id: `{args.run_id}`",
        f"Status: **{status}**",
        f"Created UTC: `{manifest['created_utc']}`",
        "",
        "## v1.1 hardening",
        "",
        "- Converts pydottalk enum/path values to JSON-safe strings.",
        "- Detects same-stem memo sidecars case-insensitively.",
        "- Captures first and second pydottalk records as repr text.",
        "",
        "## Boundary",
        "",
        "DD-046 v1.1 is evidence-tool hardening only. It does not mutate the active catalog, sandbox catalog, HELP/META/CMDHELPCHK, LMDB, or source.",
        "",
    ])
    (out / "DD046_DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-046 v1.1 probe manifest: {out / 'dd046_dottalk_x64_create_import_probe_manifest.json'}")
    print(f"status: {status}; failures: {failures}; active_catalog_mutation: 0")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
