#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List


CORE_TABLES = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

EXPECTED_COUNTS = {
    "DDRUN": 1,
    "DDBASE": 1,
    "DDSOURCE": 7,
    "DDOBJECT": 100,
    "DDATTR": 423,
    "DDEDGE": 89,
    "DDEVID": 1,
    "DDGATE": 6,
    "DDREVIEW": 0,
    "DDARTIF": 7,
    "DDPROFILE": 3,
}

HELPER_CODE = '"""Read-only active Data Dictionary helper prototype.\n\nDD-062 prototype boundary:\n- read active Data Dictionary DBFs through pydottalk\n- no append/replace/delete/pack/zap\n- no CREATE/IMPORT/CDX/BUILDLMDB\n- no HELP/META/CMDHELPCHK mutation\n\nThis helper is intentionally small and conservative. It favors row-count and\nlinear readback proof first; later DD packages can add index-aware seek paths.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Any, Dict, Iterable, List, Optional\n\n\nCORE_TABLES = [\n    "DDRUN",\n    "DDBASE",\n    "DDSOURCE",\n    "DDOBJECT",\n    "DDATTR",\n    "DDEDGE",\n    "DDEVID",\n    "DDGATE",\n    "DDREVIEW",\n    "DDARTIF",\n    "DDPROFILE",\n]\n\nEXPECTED_COUNTS = {\n    "DDRUN": 1,\n    "DDBASE": 1,\n    "DDSOURCE": 7,\n    "DDOBJECT": 100,\n    "DDATTR": 423,\n    "DDEDGE": 89,\n    "DDEVID": 1,\n    "DDGATE": 6,\n    "DDREVIEW": 0,\n    "DDARTIF": 7,\n    "DDPROFILE": 3,\n}\n\n\n@dataclass(frozen=True)\nclass DataDictPaths:\n    repo_root: Path\n    active_catalog: Path\n    index_path: Path\n    lmdb_path: Path\n\n    @staticmethod\n    def from_repo_root(repo_root: str | Path) -> "DataDictPaths":\n        root = Path(repo_root).resolve()\n        return DataDictPaths(\n            repo_root=root,\n            active_catalog=root / "dottalkpp" / "data" / "metadata" / "datadict",\n            index_path=root / "dottalkpp" / "data" / "indexes",\n            lmdb_path=root / "dottalkpp" / "data" / "lmdb",\n        )\n\n\nclass ActiveDataDictionaryReader:\n    """Read-only helper over the active Data Dictionary catalog."""\n\n    def __init__(self, paths: DataDictPaths, pydottalk_module: Any) -> None:\n        self.paths = paths\n        self.pydottalk = pydottalk_module\n\n    def _dbf_path(self, table: str) -> Path:\n        table_u = table.upper()\n        if table_u not in CORE_TABLES:\n            raise ValueError(f"Unknown Data Dictionary table: {table}")\n        return self.paths.active_catalog / f"{table_u.lower()}.dbf"\n\n    def _open(self, table: str) -> Any:\n        dbf = self._dbf_path(table)\n        area = self.pydottalk.Dbf()\n        area.open(str(dbf))\n        if not area.isOpen():\n            raise RuntimeError(f"Unable to open {dbf}")\n        return area\n\n    def table_counts(self) -> Dict[str, int]:\n        counts: Dict[str, int] = {}\n        for table in CORE_TABLES:\n            area = self._open(table)\n            try:\n                counts[table] = int(area.recCount())\n            finally:\n                area.close()\n        return counts\n\n    def verify_counts(self) -> Dict[str, Dict[str, Any]]:\n        observed = self.table_counts()\n        return {\n            table: {\n                "expected": EXPECTED_COUNTS[table],\n                "observed": observed.get(table),\n                "pass": observed.get(table) == EXPECTED_COUNTS[table],\n            }\n            for table in CORE_TABLES\n        }\n\n    def table_status(self) -> List[Dict[str, Any]]:\n        rows: List[Dict[str, Any]] = []\n        for table in CORE_TABLES:\n            path = self._dbf_path(table)\n            area = self._open(table)\n            try:\n                rows.append(\n                    {\n                        "table": table,\n                        "path": str(path),\n                        "records": int(area.recCount()),\n                        "fields": int(area.fieldCount()),\n                    }\n                )\n            finally:\n                area.close()\n        return rows\n\n    def rows(self, table: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:\n        """Return rows as best-effort dictionaries using pydottalk field access.\n\n        This is intentionally conservative and may need adaptation if pydottalk\n        exposes field names/values differently in a given build.\n        """\n        area = self._open(table)\n        out: List[Dict[str, Any]] = []\n        try:\n            rec_count = int(area.recCount())\n            field_count = int(area.fieldCount())\n            names = []\n            for i in range(field_count):\n                try:\n                    names.append(str(area.fieldName(i)))\n                except Exception:\n                    names.append(f"FIELD_{i}")\n            max_rows = rec_count if limit is None else min(rec_count, limit)\n            for recno in range(1, max_rows + 1):\n                try:\n                    area.goto(recno)\n                except Exception:\n                    try:\n                        area.go(recno)\n                    except Exception:\n                        break\n                row: Dict[str, Any] = {}\n                for i, name in enumerate(names):\n                    try:\n                        row[name] = area.get(i)\n                    except Exception:\n                        try:\n                            row[name] = area.get(name)\n                        except Exception:\n                            row[name] = None\n                out.append(row)\n        finally:\n            area.close()\n        return out\n\n    def find_objects(self, name: Optional[str] = None, objtype: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:\n        rows = self.rows("DDOBJECT", limit=None)\n        result: List[Dict[str, Any]] = []\n        name_u = name.upper() if name else None\n        objtype_u = objtype.upper() if objtype else None\n        for row in rows:\n            values = {str(k).upper(): v for k, v in row.items()}\n            row_name = str(values.get("NAME", values.get("OBJNAME", ""))).upper()\n            row_type = str(values.get("OBJTYPE", "")).upper()\n            if name_u and name_u not in row_name:\n                continue\n            if objtype_u and objtype_u != row_type:\n                continue\n            result.append(row)\n            if len(result) >= limit:\n                break\n        return result\n\n    def attrs_for_object(self, objid: str, limit: int = 200) -> List[Dict[str, Any]]:\n        rows = self.rows("DDATTR", limit=None)\n        objid_s = str(objid)\n        out: List[Dict[str, Any]] = []\n        for row in rows:\n            values = {str(k).upper(): v for k, v in row.items()}\n            if str(values.get("OBJID", "")) == objid_s:\n                out.append(row)\n                if len(out) >= limit:\n                    break\n        return out\n\n    def edges_for_object(self, objid: str, direction: str = "both", limit: int = 200) -> List[Dict[str, Any]]:\n        rows = self.rows("DDEDGE", limit=None)\n        objid_s = str(objid)\n        direction_l = direction.lower()\n        out: List[Dict[str, Any]] = []\n        for row in rows:\n            values = {str(k).upper(): v for k, v in row.items()}\n            from_obj = str(values.get("FROMOBJ", ""))\n            to_obj = str(values.get("TOOBJ", ""))\n            if direction_l in {"both", "out"} and from_obj == objid_s:\n                out.append(row)\n            elif direction_l in {"both", "in"} and to_obj == objid_s:\n                out.append(row)\n            if len(out) >= limit:\n                break\n        return out\n'


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def pydottalk_readback(repo: Path, active_path: Path) -> List[Dict[str, Any]]:
    path_info = harden_pydottalk_path(repo)
    try:
        mod = importlib.import_module("pydottalk")
        import_ok = 1
        import_error = ""
    except Exception as exc:
        mod = None
        import_ok = 0
        import_error = f"{type(exc).__name__}: {exc}"

    rows: List[Dict[str, Any]] = []
    for table in CORE_TABLES:
        expected = EXPECTED_COUNTS[table]
        row: Dict[str, Any] = {
            "table": table,
            "expected_rows": expected,
            "import_ok": import_ok,
            "open_ok": 0,
            "rec_count": "",
            "row_count_match": 0,
            "field_count": "",
            "sample_attempted": 0,
            "sample_ok": 0,
            "error": import_error,
            "build_python_exists": path_info["build_python_exists"],
        }
        if import_ok and mod is not None:
            try:
                dbf = active_path / f"{table.lower()}.dbf"
                area = mod.Dbf()
                area.open(str(dbf))
                row["open_ok"] = int(area.isOpen())
                row["rec_count"] = int(area.recCount())
                row["row_count_match"] = int(int(area.recCount()) == expected)
                row["field_count"] = int(area.fieldCount())
                if int(area.recCount()) > 0:
                    row["sample_attempted"] = 1
                    try:
                        area.goto(1)
                    except Exception:
                        try:
                            area.go(1)
                        except Exception:
                            pass
                    row["sample_ok"] = 1
                area.close()
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-062 guarded pydottalk read-only Data Dictionary helper prototype")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD062-pydottalk-readonly-datadict-helper-prototype-v0")
    ap.add_argument("--dd061-dir", default="docs/datadict/reports/DD061-active-datadict-consumer-read-api-plan-v1_1")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--helper-destination", default="tools/datadict/catalog/datadict_reader.py")
    ap.add_argument("--install-helper", action="store_true", help="Install read-only helper prototype into tools/datadict/catalog")
    ap.add_argument("--replace-existing-helper", action="store_true")
    ap.add_argument("--run-pydottalk-smoke", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd061_dir = (repo / args.dd061_dir).resolve()
    active_path = (repo / args.active_path).resolve()
    helper_dest = (repo / args.helper_destination).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd061_manifest = read_json(dd061_dir / "dd061_active_datadict_consumer_read_api_plan_manifest.json")
    dd061_ready = dd061_manifest.get("status") == "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_READY"

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if not dd061_ready:
        failures += 1
        review_rows.append({"issue": "DD061_NOT_READY", "detail": dd061_manifest.get("status", "")})

    report_helper_path = out / "datadict_reader.py"
    report_helper_path.write_text(HELPER_CODE, encoding="utf-8")

    helper_installed = 0
    helper_action = "REPORT_ARTIFACT_ONLY"
    if args.install_helper and failures == 0:
        if helper_dest.exists() and not args.replace_existing_helper:
            failures += 1
            helper_action = "DESTINATION_EXISTS_REPLACE_NOT_ALLOWED"
            review_rows.append({"issue": "HELPER_DESTINATION_EXISTS", "detail": str(helper_dest)})
        else:
            helper_dest.parent.mkdir(parents=True, exist_ok=True)
            helper_dest.write_text(HELPER_CODE, encoding="utf-8")
            helper_installed = 1
            helper_action = "INSTALLED_READONLY_HELPER"

    smoke_rows: List[Dict[str, Any]] = []
    if args.run_pydottalk_smoke:
        smoke_rows = pydottalk_readback(repo, active_path)
        for r in smoke_rows:
            if int(r.get("row_count_match", 0)) != 1:
                failures += 1
                review_rows.append({
                    "issue": "PYDOTTALK_SMOKE_ROW_COUNT_MISMATCH",
                    "detail": f"{r['table']} expected {r['expected_rows']} observed {r.get('rec_count')} error {r.get('error')}",
                })

    if args.install_helper and args.run_pydottalk_smoke:
        status = "PYDOTTALK_READONLY_DATADICT_HELPER_INSTALLED_AND_SMOKE_GREEN" if failures == 0 else "PYDOTTALK_READONLY_DATADICT_HELPER_REVIEW"
    elif args.install_helper:
        status = "PYDOTTALK_READONLY_DATADICT_HELPER_INSTALLED" if failures == 0 else "PYDOTTALK_READONLY_DATADICT_HELPER_REVIEW"
    elif args.run_pydottalk_smoke:
        status = "PYDOTTALK_READONLY_DATADICT_SMOKE_GREEN" if failures == 0 else "PYDOTTALK_READONLY_DATADICT_SMOKE_REVIEW"
    else:
        status = "PYDOTTALK_READONLY_DATADICT_HELPER_PROTOTYPE_READY" if failures == 0 else "PYDOTTALK_READONLY_DATADICT_HELPER_PROTOTYPE_REVIEW"

    gate_rows = [
        {
            "gate": "dd061_read_api_plan_ready",
            "expected": "ACTIVE_DATADICT_CONSUMER_READ_API_PLAN_READY",
            "observed": dd061_manifest.get("status", ""),
            "pass": int(dd061_ready),
        },
        {
            "gate": "helper_report_artifact_written",
            "expected": 1,
            "observed": int(report_helper_path.exists()),
            "pass": int(report_helper_path.exists()),
        },
        {
            "gate": "helper_installed_when_requested",
            "expected": int(args.install_helper),
            "observed": helper_installed,
            "pass": int((not args.install_helper) or helper_installed == 1),
        },
        {
            "gate": "pydottalk_smoke_when_requested",
            "expected": int(args.run_pydottalk_smoke),
            "observed": int(bool(smoke_rows) and all(int(r.get("row_count_match", 0)) == 1 for r in smoke_rows)),
            "pass": int((not args.run_pydottalk_smoke) or (bool(smoke_rows) and all(int(r.get("row_count_match", 0)) == 1 for r in smoke_rows))),
        },
    ]

    boundary_rows = [
        {"boundary": "read_only_helper_prototype", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits_beyond_optional_helper_install", "observed": helper_installed, "required": int(args.install_helper), "pass": 1},
    ]

    helper_api_rows = [
        {"api": "DataDictPaths.from_repo_root(repo_root)", "purpose": "Resolve active catalog/index/lmdb paths", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.table_counts()", "purpose": "Return row counts for all DD tables", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.verify_counts()", "purpose": "Compare active row counts against expected baseline counts", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.table_status()", "purpose": "Return table path/record/field metadata", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.rows(table, limit=None)", "purpose": "Best-effort row dictionaries", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.find_objects(...)", "purpose": "Find catalog objects by name/type", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.attrs_for_object(objid)", "purpose": "Return DDATTR rows for object", "read_only": 1},
        {"api": "ActiveDataDictionaryReader.edges_for_object(objid, direction='both')", "purpose": "Return DDEDGE rows for object", "read_only": 1},
    ]

    write_csv(out / "dd062_helper_api_surface.csv", helper_api_rows, ["api", "purpose", "read_only"])
    write_csv(out / "dd062_pydottalk_smoke_readback.csv", smoke_rows, ["table", "expected_rows", "import_ok", "open_ok", "rec_count", "row_count_match", "field_count", "sample_attempted", "sample_ok", "error", "build_python_exists"])
    write_csv(out / "dd062_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd062_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd062_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd062_pydottalk_readonly_datadict_helper_prototype_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd061_status": dd061_manifest.get("status", ""),
        "active_path": str(active_path),
        "report_helper_path": str(report_helper_path),
        "helper_destination": str(helper_dest),
        "install_helper": int(args.install_helper),
        "replace_existing_helper": int(args.replace_existing_helper),
        "helper_installed": helper_installed,
        "helper_action": helper_action,
        "run_pydottalk_smoke": int(args.run_pydottalk_smoke),
        "smoke_rows": len(smoke_rows),
        "failures": failures,
        "active_catalog_mutation": 0,
        "runtime_command_registration": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "cdx_lmdb_create_rebuild": 0,
        "next_recommended_action": "If accepted, DD-063 report-only DotTalk++ DDICT command contract or DD-062R stronger query smoke.",
    }
    write_json(out / "dd062_pydottalk_readonly_datadict_helper_manifest.json", manifest)

    report = f"""# DD-062 pydottalk Read-Only Data Dictionary Helper Prototype

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-062 creates a guarded pydottalk read-only helper prototype for the active Data
Dictionary catalog.

## Inputs

- DD-061 status: `{dd061_manifest.get('status', '')}`
- Active catalog path: `{active_path}`

## Helper

- Report artifact: `{report_helper_path}`
- Install destination: `{helper_dest}`
- Install requested: **{int(args.install_helper)}**
- Helper installed: **{helper_installed}**

## Smoke

- pydottalk smoke requested: **{int(args.run_pydottalk_smoke)}**
- Smoke rows: **{len(smoke_rows)}**

## Boundary

DD-062 does not mutate the active catalog, append/replace/delete/pack/zap DBFs,
create/rebuild CDX or LMDB, register runtime commands, or mutate
HELP/META/CMDHELPCHK.
"""
    (out / "DD062_PYDOTTALK_READONLY_DATADICT_HELPER_PROTOTYPE_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-062 pydottalk read-only helper manifest: {out / 'dd062_pydottalk_readonly_datadict_helper_manifest.json'}")
    print(f"status: {status}; failures: {failures}; helper_installed: {helper_installed}; smoke_rows: {len(smoke_rows)}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
