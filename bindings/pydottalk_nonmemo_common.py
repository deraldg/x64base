# Shared helpers for non-memo pydottalk proof scripts.
from __future__ import annotations
import os, shutil, sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]

def add_pydottalk_bin_from_env() -> None:
    bin_dir = os.environ.get("PYDOTTALK_BIN", "").strip()
    if bin_dir and bin_dir not in sys.path:
        sys.path.insert(0, bin_dir)

def repo_default_sandbox() -> Path:
    return Path(
        os.environ.get(
            "DOTTALK_SANDBOX_DBF_DIR",
            str(REPO_ROOT / "dottalkpp" / "data" / "dbf" / "sandbox"),
        )
    )

def repo_default_x64_dir() -> Path:
    return Path(
        os.environ.get(
            "DOTTALK_X64_DBF_DIR",
            str(REPO_ROOT / "dottalkpp" / "data" / "dbf" / "x64"),
        )
    )

def require_file(path: Path) -> Path:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    return path

def copy_dbf_scratch(src: Path, dst_name: str) -> Path:
    require_file(src)
    dst = src.with_name(dst_name)
    if dst.exists():
        dst.unlink()
    shutil.copy2(src, dst)
    return dst

def import_pydottalk():
    add_pydottalk_bin_from_env()
    import pydottalk  # type: ignore
    return pydottalk

def open_area(path: Path):
    pydottalk = import_pydottalk()
    area = pydottalk.xbase.DbArea()
    ok = area.open(str(path))
    if ok is False:
        raise RuntimeError(f"DbArea.open returned False for {path}")
    if hasattr(area, "is_open") and not area.is_open():
        raise RuntimeError(f"DbArea did not report open for {path}")
    return area

def safe_close(area: Any) -> None:
    try:
        area.close()
    except Exception:
        pass

def field_name(fd: Any) -> str:
    if isinstance(fd, dict):
        return str(fd.get("name") or fd.get("Name") or "")
    return str(getattr(fd, "name", "") or "")

def field_type(fd: Any) -> str:
    if isinstance(fd, dict):
        return str(fd.get("type") or fd.get("Type") or "")
    return str(getattr(fd, "type", "") or "")

def field_len(fd: Any) -> int:
    if isinstance(fd, dict):
        val = fd.get("len", fd.get("length", fd.get("Len", fd.get("Length", 0))))
    else:
        val = getattr(fd, "len", getattr(fd, "length", 0))
    try:
        return int(val)
    except Exception:
        return 0

def fields(area: Any) -> List[Any]:
    return list(area.fields())

def field_index_1based(area: Any, name: str) -> int:
    want = name.upper()
    for i, fd in enumerate(fields(area), start=1):
        if field_name(fd).upper() == want:
            return i
    raise KeyError(name)

def row_dict(area: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for i, fd in enumerate(fields(area), start=1):
        nm = field_name(fd) or f"FIELD_{i}"
        try:
            out[nm] = str(area.get(i))
        except Exception as exc:
            out[nm] = f"<ERROR {type(exc).__name__}: {exc}>"
    return out

def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)

def set_field_by_name(area: Any, name: str, value: Any) -> None:
    area.set(field_index_1based(area, name), value)

def get_field_by_name(area: Any, name: str) -> str:
    return str(area.get(field_index_1based(area, name)))
