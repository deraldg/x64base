# pydottalk_helpers.py
# Small pure-Python helper layer over pydottalk 0.3.0.
#
# This file intentionally does not change the C++ binding.
# It makes the current low-level DbArea API easier to smoke-test and use:
#   - context manager
#   - field name lookup
#   - current row as dict
#   - simple record iteration
#
# Current binding facts used here:
#   - pydottalk.xbase.DbArea exists
#   - fields() returns dict-like field definitions in current builds
#   - get/set use 1-based field indexes
#   - read_current()/readCurrent() positions the internal buffer and may return None

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

import pydottalk


_MISSING = object()


def _call_any(obj: Any, names: Sequence[str], *args: Any, default: Any = _MISSING) -> Any:
    """Call the first existing method/property from names."""
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            return value(*args) if callable(value) else value
    if default is not _MISSING:
        return default
    raise AttributeError(f"None of these exist on {type(obj).__name__}: {list(names)}")


def field_part(field_def: Any, key: str, default: Any = None) -> Any:
    """Read a field definition property from either dict-style or attr-style objects."""
    if isinstance(field_def, Mapping):
        return field_def.get(key, default)
    if hasattr(field_def, key):
        return getattr(field_def, key)
    if hasattr(field_def, "get"):
        try:
            return field_def.get(key, default)
        except Exception:
            return default
    return default


def normalize_field_def(field_def: Any) -> Dict[str, Any]:
    """Return a plain dict with name/type/length/decimals."""
    return {
        "name": field_part(field_def, "name", ""),
        "type": field_part(field_def, "type", ""),
        "length": field_part(field_def, "length", 0),
        "decimals": field_part(field_def, "decimals", 0),
    }


class Table:
    """Convenience wrapper for pydottalk.xbase.DbArea.

    This wrapper is intentionally thin. It does not pretend to expose indexes,
    relations, DotTalk commands, or SQL. It gives Python a comfortable read path
    over the currently-proven DbArea binding.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.area = pydottalk.xbase.DbArea()
        self._opened = False

    def __enter__(self) -> "Table":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def open(self) -> None:
        self.area.open(str(self.path))
        self._opened = True

    def close(self) -> None:
        if self._opened:
            _call_any(self.area, ["close"], default=None)
            self._opened = False

    def is_open(self) -> bool:
        return bool(_call_any(self.area, ["is_open", "isOpen"], default=False))

    def filename(self) -> str:
        return str(_call_any(self.area, ["filename"], default=self.path))

    def logical_name(self) -> str:
        return str(_call_any(self.area, ["logical_name", "logicalName", "name"], default=self.path.stem.upper()))

    def dbf_basename(self) -> str:
        return str(_call_any(self.area, ["dbf_basename", "dbfBasename"], default=self.path.stem))

    def rec_count(self) -> int:
        return int(_call_any(self.area, ["rec_count", "recCount"]))

    def recno(self) -> int:
        return int(_call_any(self.area, ["recno"], default=0))

    def rec_length(self) -> int:
        return int(_call_any(self.area, ["rec_length", "recLength", "recordLength", "cpr"], default=0))

    def fields(self) -> List[Dict[str, Any]]:
        raw = _call_any(self.area, ["fields"], default=[])
        return [normalize_field_def(f) for f in raw]

    def field_names(self) -> List[str]:
        return [str(f["name"]) for f in self.fields()]

    def field_index(self, name: str) -> int:
        want = name.upper()
        matches: List[Tuple[int, str]] = []
        for idx1, fname in enumerate(self.field_names(), start=1):
            if fname.upper() == want:
                return idx1
            if fname.upper().startswith(want):
                matches.append((idx1, fname))
        if len(matches) == 1:
            return matches[0][0]
        if len(matches) > 1:
            raise KeyError(f"Ambiguous field prefix {name!r}: {[m[1] for m in matches]}")
        raise KeyError(f"Field not found: {name}")

    def top(self) -> None:
        _call_any(self.area, ["top"])

    def bottom(self) -> None:
        _call_any(self.area, ["bottom"])

    def goto(self, recno: int) -> None:
        _call_any(self.area, ["goto_rec", "gotoRec"], recno)

    def skip(self, delta: int = 1) -> None:
        _call_any(self.area, ["skip"], delta)

    def eof(self) -> bool:
        return bool(_call_any(self.area, ["eof"], default=False))

    def bof(self) -> bool:
        return bool(_call_any(self.area, ["bof"], default=False))

    def read_current(self) -> None:
        _call_any(self.area, ["read_current", "readCurrent"], default=None)

    def get(self, field: int | str) -> Any:
        idx1 = field if isinstance(field, int) else self.field_index(field)
        return _call_any(self.area, ["get"], idx1)

    def set(self, field: int | str, value: Any) -> None:
        idx1 = field if isinstance(field, int) else self.field_index(field)
        _call_any(self.area, ["set"], idx1, value)

    def write_current(self) -> None:
        _call_any(self.area, ["write_current", "writeCurrent"])

    def row_dict(self, names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        self.read_current()
        wanted = list(names) if names is not None else self.field_names()
        return {name: self.get(name) for name in wanted}

    def rows(self, limit: Optional[int] = None, names: Optional[Sequence[str]] = None) -> Iterator[Dict[str, Any]]:
        self.top()
        count = 0
        while not self.eof():
            yield self.row_dict(names=names)
            count += 1
            if limit is not None and count >= limit:
                break
            self.skip(1)

    def describe(self) -> Dict[str, Any]:
        return {
            "filename": self.filename(),
            "logical_name": self.logical_name(),
            "dbf_basename": self.dbf_basename(),
            "rec_count": self.rec_count(),
            "recno": self.recno(),
            "rec_length": self.rec_length(),
            "field_count": len(self.fields()),
            "fields": self.fields(),
        }


def open_table(path: str | Path) -> Table:
    t = Table(path)
    t.open()
    return t
