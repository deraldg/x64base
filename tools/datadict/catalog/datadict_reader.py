"""Read-only active Data Dictionary helper prototype.

DD-062 prototype boundary:
- read active Data Dictionary DBFs through pydottalk
- no append/replace/delete/pack/zap
- no CREATE/IMPORT/CDX/BUILDLMDB
- no HELP/META/CMDHELPCHK mutation

This helper is intentionally small and conservative. It favors row-count and
linear readback proof first; later DD packages can add index-aware seek paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


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


@dataclass(frozen=True)
class DataDictPaths:
    repo_root: Path
    active_catalog: Path
    index_path: Path
    lmdb_path: Path

    @staticmethod
    def from_repo_root(repo_root: str | Path) -> "DataDictPaths":
        root = Path(repo_root).resolve()
        return DataDictPaths(
            repo_root=root,
            active_catalog=root / "dottalkpp" / "data" / "metadata" / "datadict",
            index_path=root / "dottalkpp" / "data" / "indexes",
            lmdb_path=root / "dottalkpp" / "data" / "lmdb",
        )


class ActiveDataDictionaryReader:
    """Read-only helper over the active Data Dictionary catalog."""

    def __init__(self, paths: DataDictPaths, pydottalk_module: Any) -> None:
        self.paths = paths
        self.pydottalk = pydottalk_module

    def _dbf_path(self, table: str) -> Path:
        table_u = table.upper()
        if table_u not in CORE_TABLES:
            raise ValueError(f"Unknown Data Dictionary table: {table}")
        return self.paths.active_catalog / f"{table_u.lower()}.dbf"

    def _open(self, table: str) -> Any:
        dbf = self._dbf_path(table)
        area = self.pydottalk.Dbf()
        area.open(str(dbf))
        if not area.isOpen():
            raise RuntimeError(f"Unable to open {dbf}")
        return area

    def table_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for table in CORE_TABLES:
            area = self._open(table)
            try:
                counts[table] = int(area.recCount())
            finally:
                area.close()
        return counts

    def verify_counts(self) -> Dict[str, Dict[str, Any]]:
        observed = self.table_counts()
        return {
            table: {
                "expected": EXPECTED_COUNTS[table],
                "observed": observed.get(table),
                "pass": observed.get(table) == EXPECTED_COUNTS[table],
            }
            for table in CORE_TABLES
        }

    def table_status(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for table in CORE_TABLES:
            path = self._dbf_path(table)
            area = self._open(table)
            try:
                rows.append(
                    {
                        "table": table,
                        "path": str(path),
                        "records": int(area.recCount()),
                        "fields": int(area.fieldCount()),
                    }
                )
            finally:
                area.close()
        return rows

    def rows(self, table: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return rows as best-effort dictionaries using pydottalk field access.

        This is intentionally conservative and may need adaptation if pydottalk
        exposes field names/values differently in a given build.
        """
        area = self._open(table)
        out: List[Dict[str, Any]] = []
        try:
            rec_count = int(area.recCount())
            field_count = int(area.fieldCount())
            names = []
            for i in range(field_count):
                try:
                    names.append(str(area.fieldName(i)))
                except Exception:
                    names.append(f"FIELD_{i}")
            max_rows = rec_count if limit is None else min(rec_count, limit)
            for recno in range(1, max_rows + 1):
                try:
                    area.goto(recno)
                except Exception:
                    try:
                        area.go(recno)
                    except Exception:
                        break
                row: Dict[str, Any] = {}
                for i, name in enumerate(names):
                    try:
                        row[name] = area.get(i)
                    except Exception:
                        try:
                            row[name] = area.get(name)
                        except Exception:
                            row[name] = None
                out.append(row)
        finally:
            area.close()
        return out

    def find_objects(self, name: Optional[str] = None, objtype: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.rows("DDOBJECT", limit=None)
        result: List[Dict[str, Any]] = []
        name_u = name.upper() if name else None
        objtype_u = objtype.upper() if objtype else None
        for row in rows:
            values = {str(k).upper(): v for k, v in row.items()}
            row_name = str(values.get("NAME", values.get("OBJNAME", ""))).upper()
            row_type = str(values.get("OBJTYPE", "")).upper()
            if name_u and name_u not in row_name:
                continue
            if objtype_u and objtype_u != row_type:
                continue
            result.append(row)
            if len(result) >= limit:
                break
        return result

    def attrs_for_object(self, objid: str, limit: int = 200) -> List[Dict[str, Any]]:
        rows = self.rows("DDATTR", limit=None)
        objid_s = str(objid)
        out: List[Dict[str, Any]] = []
        for row in rows:
            values = {str(k).upper(): v for k, v in row.items()}
            if str(values.get("OBJID", "")) == objid_s:
                out.append(row)
                if len(out) >= limit:
                    break
        return out

    def edges_for_object(self, objid: str, direction: str = "both", limit: int = 200) -> List[Dict[str, Any]]:
        rows = self.rows("DDEDGE", limit=None)
        objid_s = str(objid)
        direction_l = direction.lower()
        out: List[Dict[str, Any]] = []
        for row in rows:
            values = {str(k).upper(): v for k, v in row.items()}
            from_obj = str(values.get("FROMOBJ", ""))
            to_obj = str(values.get("TOOBJ", ""))
            if direction_l in {"both", "out"} and from_obj == objid_s:
                out.append(row)
            elif direction_l in {"both", "in"} and to_obj == objid_s:
                out.append(row)
            if len(out) >= limit:
                break
        return out
