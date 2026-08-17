#!/usr/bin/env python3
"""DBF CRUD over pydottalk -- posture A (pydottalk-direct, scoped safe).

AIF-086. A small, self-contained "mini shell" (ArcticTalk-style REPL) plus one-shot
subcommands for create / read / update / delete across the SYS* catalogs, driven
entirely by schema_registry.py. It writes ONLY within the confirmed pydottalk
surface (append_blank / set_field / write_current / delete_current); it takes NO
lock, so it is a SINGLE-WRITER tool. See
PYDOTTALK_CAPABILITY_REVIEW_AND_CRUD_READINESS_V1.md.

Guard rails (posture A):
  - READS work on every table (reads are safe).
  - WRITES are refused on the bbs catalog (dottalk_bbsd may hold the store and there
    is no lock to coordinate with it). Portal + identity are writable single-writer.
  - DELETE defaults to a policy-driven SOFT-CLOSE (reversible: rewrite the status /
    clear VTHRU). --purge maps to delete_current (the classic xBase deleted
    tombstone): IRREVERSIBLE through pydottalk (no RECALL bound) and NOT
    space-reclaiming (no PACK bound). It prints a loud warning and needs --yes.

The write path talks to an `Area` (the small protocol below). The real adapter wires
pydottalk's DbArea; tests inject an in-memory FakeArea, so the CRUD LOGIC is fully
exercised without the win_amd64 .pyd (which the steward sandbox cannot load).

One-shot:
  python tools/dbf/crud.py list
  python tools/dbf/crud.py read   SYSLANE [--where STATUS=1] [--include-deleted] [--limit N]
  python tools/dbf/crud.py create SYSLANE --set LKEY=AIF-099 --set TITLE="New lane"
  python tools/dbf/crud.py update SYSLANE --key AIF-099 --set STATUS=1
  python tools/dbf/crud.py delete SYSLANE --key AIF-099            # soft-close
  python tools/dbf/crud.py delete SYSLANE --key AIF-099 --purge --yes
Mini shell:
  python tools/dbf/crud.py shell
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_registry as reg  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
META = REPO / "dottalkpp" / "data" / "metadata"


# ---- the small write/read protocol the CRUD needs from an area ----------------
# pydottalk's DbArea satisfies this; FakeArea (tests) reimplements it in memory.
class Area:  # documentation-only protocol
    def rec_count(self) -> int: ...
    def top(self) -> None: ...
    def skip(self, delta: int) -> None: ...
    def goto_rec(self, recno: int) -> None: ...
    def recno(self) -> int: ...
    def eof(self) -> bool: ...
    def is_deleted(self) -> bool: ...
    def get_field(self, name: str) -> str: ...
    def set_field(self, name: str, value: str) -> None: ...
    def append_blank(self) -> None: ...
    def write_current(self) -> None: ...
    def delete_current(self) -> None: ...
    def close(self) -> None: ...


class CrudError(RuntimeError):
    pass


def now_epoch() -> int:
    return int(time.time())


# ---- validation ---------------------------------------------------------------
def _validate_assignments(spec: reg.TableSpec, values: dict) -> dict:
    """Reject unknown fields; light type/width checks (no engine RULE is bound)."""
    fmap = spec.field_map()
    out: dict = {}
    for name, raw in values.items():
        up = name.upper()
        if up not in fmap:
            raise CrudError(f"{spec.name}: unknown field {name!r} "
                            f"(fields: {', '.join(spec.field_names())})")
        typ, length = fmap[up]
        val = str(raw)
        if typ == "N":
            probe = val.strip().lstrip("-")
            if probe and not probe.replace(".", "", 1).isdigit():
                raise CrudError(f"{spec.name}.{up} is numeric N({length}); got {val!r}")
        elif typ == "L":
            if val.upper() not in ("T", "F", "1", "0", "Y", "N", "", " "):
                raise CrudError(f"{spec.name}.{up} is logical L; got {val!r}")
            val = "T" if val.upper() in ("T", "1", "Y") else "F"
        elif typ == "C":
            if len(val) > length:
                raise CrudError(f"{spec.name}.{up} exceeds C({length}): {len(val)} chars")
        out[up] = val
    return out


def _require_writable(spec: reg.TableSpec) -> None:
    if not spec.writable:
        raise CrudError(
            f"{spec.name} is in the '{spec.subdir}' catalog, which is written by "
            f"dottalk_bbsd. pydottalk exposes no lock, so posture A refuses writes "
            f"here. Use the engine CLI/DotScript (which locks), or stop the daemon "
            f"first (Stop-ScheduledTask 'DotTalkBBSD').")


# ---- row scanning -------------------------------------------------------------
def _iter_rows(area, spec: reg.TableSpec, include_deleted: bool):
    n = int(area.rec_count())
    if n <= 0:
        return
    area.top()
    for _ in range(n):
        if include_deleted or not area.is_deleted():
            yield {fn: area.get_field(fn) for fn in spec.field_names()}, area.recno()
        area.skip(1)


def _find_recno(area, spec: reg.TableSpec, key_values: dict) -> Optional[int]:
    """Locate the recno of the (newest, for append-only) row matching key_values."""
    match = None
    n = int(area.rec_count())
    if n <= 0:
        return None
    area.top()
    for _ in range(n):
        if not area.is_deleted():
            if all(area.get_field(k) == str(v) for k, v in key_values.items()):
                match = area.recno()  # keep last => newest for append-only tables
        area.skip(1)
    return match


def _next_id(area, spec: reg.TableSpec) -> int:
    if not spec.pk:
        return 0
    hi = 0
    for row, _rec in _iter_rows(area, spec, include_deleted=True):
        try:
            hi = max(hi, int(row.get(spec.pk, "0") or "0"))
        except ValueError:
            pass
    return hi + 1


def _key_selector(spec: reg.TableSpec, key: Optional[str], where: dict) -> dict:
    if spec.ckey:
        missing = [k for k in spec.ckey if k not in {w.upper() for w in where}]
        if missing:
            raise CrudError(f"{spec.name} is a crosswalk; supply --where for its key "
                            f"fields {spec.ckey}")
        return {k: where[k] for k in spec.ckey}
    if spec.key and key is not None:
        return {spec.key: key}
    if spec.pk and key is not None:
        return {spec.pk: key}
    raise CrudError(f"{spec.name}: need --key (natural key {spec.key or spec.pk}) "
                    f"to locate a row")


# ---- operations ---------------------------------------------------------------
def op_create(area, spec: reg.TableSpec, values: dict) -> dict:
    _require_writable(spec)
    if spec.append_only:
        pass  # create appends by nature; that is fine even for append-only tables
    vals = _validate_assignments(spec, values)
    assigned = dict(vals)
    # Compute the next id BEFORE append_blank: scanning moves the cursor off the
    # freshly appended row.
    if spec.pk and spec.pk not in assigned:
        assigned[spec.pk] = str(_next_id(area, spec))
    if spec.close.rowver and spec.close.rowver not in assigned:
        assigned[spec.close.rowver] = "1"
    area.append_blank()
    for fn, v in assigned.items():
        area.set_field(fn, v)
    area.write_current()
    return assigned


def op_read(area, spec: reg.TableSpec, where: dict, include_deleted: bool,
            limit: Optional[int]) -> list:
    rows = []
    wl = {k.upper(): str(v) for k, v in where.items()}
    for row, _rec in _iter_rows(area, spec, include_deleted):
        if all(row.get(k, "") == v for k, v in wl.items()):
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def op_update(area, spec: reg.TableSpec, key: Optional[str], where: dict,
              values: dict) -> dict:
    _require_writable(spec)
    if spec.append_only:
        raise CrudError(f"{spec.name} is append-only: update-in-place is refused. "
                        f"Append a new row (create) that supersedes the old one.")
    vals = _validate_assignments(spec, values)
    sel = _key_selector(spec, key, {k.upper(): v for k, v in where.items()})
    rec = _find_recno(area, spec, sel)
    if rec is None:
        raise CrudError(f"{spec.name}: no live row matching {sel}")
    area.goto_rec(rec)
    for fn, v in vals.items():
        area.set_field(fn, v)
    if spec.close.rowver:
        _bump_rowver(area, spec)
    area.write_current()
    return {"recno": rec, **vals}


def op_soft_close(area, spec: reg.TableSpec, key: Optional[str], where: dict) -> dict:
    _require_writable(spec)
    p = spec.close
    sel = _key_selector(spec, key, {k.upper(): v for k, v in where.items()})
    if p.kind == "crosswalk":
        raise CrudError(f"{spec.name} is a crosswalk link: there is no soft-close. "
                        f"Remove the link with --purge (deleted tombstone).")
    if p.kind == "append_term":
        return _append_terminal(area, spec, sel)
    rec = _find_recno(area, spec, sel)
    if rec is None:
        raise CrudError(f"{spec.name}: no live row matching {sel}")
    area.goto_rec(rec)
    changed = {}
    if p.kind == "bitemporal":
        area.set_field(p.field, str(now_epoch()))
        changed[p.field] = area.get_field(p.field)
    elif p.kind == "status":
        area.set_field(p.field, str(p.terminal))
        changed[p.field] = str(p.terminal)
        if p.epoch:
            area.set_field(p.epoch, str(now_epoch()))
            changed[p.epoch] = area.get_field(p.epoch)
    elif p.kind == "status_str":
        area.set_field(p.field, str(p.terminal))
        changed[p.field] = str(p.terminal)
    else:
        raise CrudError(f"{spec.name}: unhandled close policy {p.kind}")
    if p.rowver:
        _bump_rowver(area, spec)
    area.write_current()
    return {"recno": rec, "soft_closed": changed}


def op_purge(area, spec: reg.TableSpec, key: Optional[str], where: dict) -> dict:
    _require_writable(spec)
    sel = _key_selector(spec, key, {k.upper(): v for k, v in where.items()})
    rec = _find_recno(area, spec, sel)
    if rec is None:
        raise CrudError(f"{spec.name}: no live row matching {sel}")
    area.goto_rec(rec)
    area.delete_current()
    return {"recno": rec, "tombstoned": sel,
            "note": "DBF deleted flag set; irreversible via pydottalk (no RECALL), "
                    "space not reclaimed (engine PACK required)"}


def _bump_rowver(area, spec: reg.TableSpec) -> None:
    cur = area.get_field(spec.close.rowver).strip() or "0"
    try:
        nxt = int(cur) + 1
    except ValueError:
        nxt = 1
    area.set_field(spec.close.rowver, str(nxt))


def _append_terminal(area, spec: reg.TableSpec, sel: dict) -> dict:
    """Append-only close: copy the newest matching row, stamp terminal + epoch."""
    rec = _find_recno(area, spec, sel)
    if rec is None:
        raise CrudError(f"{spec.name}: no row matching {sel} to close")
    area.goto_rec(rec)
    snapshot = {fn: area.get_field(fn) for fn in spec.field_names()}
    p = spec.close
    snapshot[p.field] = str(p.terminal)
    if p.epoch:
        snapshot[p.epoch] = str(now_epoch())
    if spec.pk:
        snapshot[spec.pk] = str(_next_id(area, spec))
    if p.rowver:
        try:
            snapshot[p.rowver] = str(int(snapshot.get(p.rowver, "0") or "0") + 1)
        except ValueError:
            snapshot[p.rowver] = "1"
    area.append_blank()
    for fn, v in snapshot.items():
        area.set_field(fn, v)
    area.write_current()
    return {"append_only_close": True, "new_row": snapshot}


# ---- engine REPL / DotScript emit (posture B: lock-safe, no pydottalk) --------
# The write path pydottalk cannot safely take (no LOCK/RECALL/PACK) is exactly what
# the engine REPL does natively. So instead of writing through the binding, emit the
# DotScript the maintainer feeds via `datarun.ps1 -CommandLines ...` (the same route
# that loaded SYSTASK). Grammar verified against cmd_create/cmd_replace/cmd_delete and
# the regression scripts.
#
# PATH SLOTS: the engine resolves DBF, INDEXES and LMDB as THREE separate slots. A
# scan-based (LOCATE) edit needs only SET PATH DBF. But once a table carries a CDX/
# LMDB index, a REPLACE on an indexed field must maintain or REINDEX it -- which needs
# the INDEXES and LMDB slots pointed too, or the container is not found. So --indexed
# emits all three slots + a trailing REINDEX; the default (no index built yet) does not.
def _dts_quote(spec: reg.TableSpec, field: str, value: str) -> str:
    typ = spec.field_map()[field][0]
    if typ == "C":
        return "'" + str(value).replace("'", "''") + "'"
    if typ == "L":
        return ".T." if str(value).upper() in ("T", "1", "Y") else ".F."
    return str(value)  # N: bare


def _dts_paths(spec: reg.TableSpec, indexed: bool) -> list:
    lines = [f"SET PATH DBF metadata/{spec.subdir}"]
    if indexed:
        lines += [f"SET PATH INDEXES metadata/{spec.subdir}",
                  f"SET PATH LMDB metadata/{spec.subdir}"]
    return lines


def _dts_locate(spec: reg.TableSpec, sel: dict) -> str:
    conds = " .AND. ".join(f"{k} = {_dts_quote(spec, k, v)}" for k, v in sel.items())
    return f"LOCATE FOR {conds}"


def _dts_reindex(spec: reg.TableSpec, indexed: bool) -> list:
    return ["REINDEX CDX QUIET"] if indexed else []  # maintain the index after the write


def _dts_create_clause(spec: reg.TableSpec) -> str:
    parts = []
    for (n, t, l) in spec.fields:
        parts.append(f"{n} N({l},0)" if t == "N" else (f"{n} C({l})" if t == "C" else f"{n} L"))
    return f"CREATE X64 {spec.name} (" + ", ".join(parts) + ")"


def _seed_csv_rel(spec: reg.TableSpec) -> Optional[str]:
    p = REPO / "dottalkpp" / "data" / "metadata" / spec.subdir / "seed" / f"{spec.name}.csv"
    return f"metadata/{spec.subdir}/seed/{spec.name}.csv" if p.is_file() else None


def _op_lines(cmd: str, spec: reg.TableSpec, values: dict, key, where: dict,
              purge: bool, indexed: bool) -> list:
    """Just the mutation verbs (no SET PATH, no USE) -- shared by disk + RAM emit."""
    lines = []
    if cmd == "create":
        _require_writable(spec)
        vals = _validate_assignments(spec, values)
        assigned = dict(vals)
        if spec.pk and spec.pk not in assigned:
            hi = max([int(r.get(spec.pk, "0") or "0")
                      for r in read_rows(spec.name, include_deleted=True)] + [0])
            assigned[spec.pk] = str(hi + 1)
        if spec.close.rowver and spec.close.rowver not in assigned:
            assigned[spec.close.rowver] = "1"
        lines.append("APPEND")  # bare APPEND adds one blank row; 'APPEND BLANK' is rejected
        lines += [f"REPLACE {f} WITH {_dts_quote(spec, f, v)}" for f, v in assigned.items()]
    elif cmd == "update":
        _require_writable(spec)
        if spec.append_only:
            raise CrudError(f"{spec.name} is append-only: emit a create, not an update.")
        vals = _validate_assignments(spec, values)
        sel = _key_selector(spec, key, {k.upper(): v for k, v in where.items()})
        lines.append(_dts_locate(spec, sel))
        lines += [f"REPLACE {f} WITH {_dts_quote(spec, f, v)}" for f, v in vals.items()]
        if spec.close.rowver:
            lines.append(f"REPLACE {spec.close.rowver} WITH {spec.close.rowver} + 1")
        lines += _dts_reindex(spec, indexed)
    elif cmd == "delete":
        _require_writable(spec)
        sel = _key_selector(spec, key, {k.upper(): v for k, v in where.items()})
        lines.append(_dts_locate(spec, sel))
        if purge:
            lines.append("DELETE")
            lines.append("PACK")  # physical reclaim (irreversible; rebuild indexes after)
        else:
            p = spec.close
            if p.kind == "crosswalk":
                raise CrudError(f"{spec.name} is a crosswalk: no soft-close. Use --purge.")
            if p.kind == "bitemporal":
                lines.append(f"REPLACE {p.field} WITH {now_epoch()}")
            elif p.kind in ("status", "status_str"):
                lines.append(f"REPLACE {p.field} WITH {_dts_quote(spec, p.field, p.terminal)}")
                if p.epoch:
                    lines.append(f"REPLACE {p.epoch} WITH {now_epoch()}")
            elif p.kind == "append_term":
                raise CrudError(f"{spec.name} is append-only: emit a create of the "
                                f"terminal row (STATUS={p.terminal}) instead.")
            if p.rowver:
                lines.append(f"REPLACE {p.rowver} WITH {p.rowver} + 1")
        lines += _dts_reindex(spec, indexed)
    else:
        raise CrudError(f"emit: unsupported command {cmd}")
    return lines


def emit_dts(cmd: str, spec: reg.TableSpec, values: dict, key, where: dict,
             purge: bool, indexed: bool) -> list:
    """Disk-persistent DotScript: SET PATH + USE + the mutation."""
    return _dts_paths(spec, indexed) + [f"USE {spec.name}"] + \
        _op_lines(cmd, spec, values, key, where, purge, indexed)


def emit_ram(cmd: str, spec: reg.TableSpec, values: dict, key, where: dict,
             purge: bool, indexed: bool) -> list:
    """Self-contained RAM dry run: build the table + index in the fsram VFS, run the
    op, LIST to self-assert, drop the RAM disk. Touches NO disk file. DO mem sets the
    DBF/INDEXES/LMDB slots itself, so no SET PATH is emitted."""
    head = ["DO mem", "VDISK UNMOUNT", "DO mem", _dts_create_clause(spec)]
    seed = _seed_csv_rel(spec)
    if seed:
        head.append(f"IMPORT {seed}")
    if indexed and (spec.key or spec.pk):
        tag = spec.key or spec.pk
        head += ["CDX CREATE", f"CDX ADDTAG {tag}", "REINDEX CDX", f"SET ORDER TAG {tag}"]
    op = _op_lines(cmd, spec, values, key, where, purge, indexed)
    # DISPLAY the affected record (cursor sits on it after APPEND or LOCATE), then
    # TOP + LIST for context. LIST alone lists from the current record, so reset first.
    tail = ["DISPLAY", "TOP", "LIST 20", "VDISK STATUS", "VDISK UNMOUNT", "DO x64"]
    return head + op + tail


# ---- dependency-free read path (no engine, no .pyd) ---------------------------
# The interactive/write path uses pydottalk. But REPORTS derive from these tables
# and must stay runnable with no engine (the report generator already parses DBF by
# hand and runs in the sandbox). So read has a pure-Python path too: parse the DBF
# directly, respect the deleted tombstone, and classify live vs closed via the
# registry policy. This is what build_reports.py wires in as its DBF derive-source.
def _read_dbf_pure(
    path: Path,
    include_deleted: bool = False,
    include_metadata: bool = False,
) -> tuple:
    import struct
    b = Path(path).read_bytes()
    _nrec, hlen, rlen = struct.unpack_from("<IHH", b, 4)
    fields, off = [], 96
    while off < len(b) and b[off] != 0x0D:
        raw = b[off:off + 32]
        if len(raw) < 32:
            break
        name = raw[0:11].split(b"\x00")[0].decode("ascii", "replace").strip()
        if not name:
            break
        disp = struct.unpack_from("<I", raw, 12)[0]
        flen = struct.unpack_from("<I", raw, 16)[0]
        fields.append((name, disp, flen))
        off += 32
    nrec = struct.unpack_from("<I", b, 4)[0]
    rows = []
    for i in range(nrec):
        base = hlen + i * rlen
        rec = b[base:base + rlen]
        if len(rec) < rlen:
            continue
        deleted = rec[0:1] == b"*"
        if not include_deleted and deleted:
            continue  # deleted tombstone
        row = {n: rec[d:d + ln].decode("cp437", "replace").strip() for (n, d, ln) in fields}
        if include_metadata:
            row["_deleted"] = deleted
            row["_recno"] = i + 1
        rows.append(row)
    return [f[0] for f in fields], rows


def is_live(spec: reg.TableSpec, row: dict) -> bool:
    """Classify a row as live vs closed per its close policy (soft-close aware)."""
    p = spec.close
    if p.kind == "bitemporal":
        return (row.get(p.field, "") or "").strip() in ("", "0")
    if p.kind in ("status", "status_str"):
        return str(row.get(p.field, "")).strip() != str(p.terminal)
    return True  # crosswalk / append_term: a link/ledger row is always "present"


def read_rows(
    table: str,
    root: Path = REPO,
    include_deleted: bool = False,
    include_metadata: bool = False,
) -> list:
    """All non-deleted rows of a table via the pure DBF path (no engine)."""
    spec = reg.get(table)
    path = Path(root) / "dottalkpp" / "data" / "metadata" / spec.subdir / f"{spec.name}.dbf"
    if not path.is_file():
        raise CrudError(f"{spec.name}: no DBF at {path} (seed/load it first)")
    _names, rows = _read_dbf_pure(path, include_deleted, include_metadata)
    return rows


def read_live(table: str, root: Path = REPO) -> list:
    """Non-deleted rows that are also live per the close policy."""
    spec = reg.get(table)
    return [r for r in read_rows(table, root) if is_live(spec, r)]


# ---- real pydottalk adapter (maintainer box; not importable in the sandbox) ----
def _open_real_area(spec: reg.TableSpec):
    sys.path.insert(0, str(REPO / "bindings"))
    build_py = Path(os.environ.get("PYDOTTALK_BIN", REPO / "build-labtalk" / "python"))
    if str(build_py) not in sys.path:
        sys.path.insert(0, str(build_py))
    try:
        import pydottalk  # type: ignore
    except ImportError as exc:
        raise CrudError(f"pydottalk not importable ({exc}). Set PYDOTTALK_BIN to the "
                        f"dir holding the built .pyd (PowerShell: "
                        f"$env:PYDOTTALK_BIN='D:\\code\\ccode\\build-labtalk\\python').")
    if not getattr(pydottalk, "HAVE_XBASE", False) or not hasattr(pydottalk, "xbase"):
        found = sorted(str(p.parent) for p in REPO.glob("**/pydottalk*.pyd")
                       if "build" in str(p).lower())[:8]
        loaded = getattr(pydottalk, "__file__", "?")
        hint = ("\n  pydottalk builds found in-tree:\n    " + "\n    ".join(found)
                if found else "\n  (no other pydottalk*.pyd found in-tree)")
        raise CrudError(
            "pydottalk was built WITHOUT the xbase core -- it has no .xbase submodule, "
            "so there is no DbArea to write through. The write path needs it (reads do "
            "not -- 'read' works regardless).\n"
            f"  loaded from: {loaded}{hint}\n"
            "  Point PYDOTTALK_BIN at a build whose pydottalk has xbase, or rebuild with "
            "the xbase target visible to CMake (configure the full tree, not the binding "
            "alone). Verify: python -c \"import pydottalk; print(pydottalk.HAVE_XBASE)\" -> "
            "True. This is the binding-timeliness gap the capability review flagged.")
    from pydottalk_nonmemo_common import open_area, get_field_by_name, set_field_by_name

    path = META / spec.subdir / f"{spec.name}.dbf"
    raw = open_area(path)

    class _Adapter:
        def rec_count(self):
            return int(raw.rec_count())

        def top(self):
            raw.top()

        def skip(self, d):
            raw.skip(d)

        def goto_rec(self, r):
            raw.goto_rec(r)

        def recno(self):
            return int(raw.recno())

        def eof(self):
            return bool(raw.eof())

        def is_deleted(self):
            return bool(raw.is_deleted())

        def get_field(self, name):
            return str(get_field_by_name(raw, name)).rstrip()

        def set_field(self, name, value):
            set_field_by_name(raw, name, value)

        def append_blank(self):
            raw.append_blank()

        def write_current(self):
            raw.write_current()

        def delete_current(self):
            raw.delete_current()

        def close(self):
            try:
                raw.close()
            except Exception:
                pass

    return _Adapter()


# ---- rendering ----------------------------------------------------------------
def _print_rows(rows: list, spec: reg.TableSpec) -> None:
    if not rows:
        print("(no rows)")
        return
    cols = list(spec.field_names())
    widths = {c: min(28, max(len(c), *(len(r.get(c, "")) for r in rows))) for c in cols}
    line = "  ".join(c.ljust(widths[c]) for c in cols)
    print(line)
    print("  ".join("-" * widths[c] for c in cols))
    for r in rows:
        print("  ".join((r.get(c, "")[:widths[c]]).ljust(widths[c]) for c in cols))
    print(f"({len(rows)} row(s))")


def _parse_sets(pairs: list) -> dict:
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise CrudError(f"--set expects FIELD=VALUE, got {p!r}")
        k, v = p.split("=", 1)
        out[k.strip()] = v
    return out


# ---- command aliases / shortcuts (mini-shell affordance) ----------------------
_CANON = ("list", "read", "create", "update", "delete", "help", "quit")
ALIASES = {
    "l": "list", "ls": "list", "tables": "list",
    "r": "read", "sel": "read", "select": "read", "get": "read",
    "c": "create", "new": "create", "add": "create", "ins": "create", "insert": "create",
    "u": "update", "upd": "update", "set": "update", "mod": "update",
    "d": "delete", "del": "delete", "rm": "delete", "close": "delete",
    "h": "help", "?": "help", "man": "help",
    "q": "quit", "exit": "quit", "bye": "quit",
}


def resolve_cmd(word: str) -> str:
    """Map an alias, or an unambiguous prefix, to a canonical command."""
    w = word.lower()
    if w in _CANON:
        return w
    if w in ALIASES:
        return ALIASES[w]
    hits = [c for c in _CANON if c.startswith(w)]
    if len(hits) == 1:
        return hits[0]
    return w  # unresolved / ambiguous -> caller reports it


# ---- dispatch (shared by one-shot CLI and the mini shell) ---------------------
def dispatch(cmd: str, rest: list, area_factory=_open_real_area) -> int:
    cmd = resolve_cmd(cmd)
    if cmd in ("list", "tables"):
        for name in sorted(reg.TABLES):
            s = reg.TABLES[name]
            flag = "rw" if s.writable else "RO"
            print(f"  {name:12s} {s.subdir:9s} [{flag}] close={s.close.kind}"
                  f"{' append-only' if s.append_only else ''}")
        print(f"\nwritable: {', '.join(reg.writable_tables())}")
        print(f"read-only (write-guarded): {', '.join(reg.readonly_tables())}")
        return 0

    ap = argparse.ArgumentParser(prog=cmd, add_help=False)
    ap.add_argument("table")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--where", action="append", default=[])
    ap.add_argument("--key", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-deleted", action="store_true")
    ap.add_argument("--purge", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--emit", action="store_true",
                    help="print the engine DotScript for this op instead of writing via "
                         "pydottalk (feed it with datarun.ps1 -CommandLines). Lock-safe, "
                         "no binding needed.")
    ap.add_argument("--indexed", action="store_true",
                    help="the table carries a CDX/LMDB index: emit the INDEXES+LMDB path "
                         "slots and a trailing REINDEX so the write maintains the index.")
    ap.add_argument("--ram", action="store_true",
                    help="with --emit: a self-contained fsram (RAM VFS) dry run -- build "
                         "the table+index in RAM, run the op, LIST to self-assert, drop "
                         "the RAM disk. Zero disk footprint; proves the op on a real engine.")
    a = ap.parse_args(rest)
    spec = reg.get(a.table)
    where = _parse_sets(a.where)

    if a.emit and cmd in ("create", "update", "delete"):
        fn = emit_ram if a.ram else emit_dts
        lines = fn(cmd, spec, _parse_sets(a.set), a.key, where, a.purge, a.indexed)
        print("\n".join(lines))
        return 0

    # READ is engine-free: use the pure DBF path (no pydottalk needed), so it works
    # even when the binding lacks xbase. Only writes open a real area.
    if cmd == "read":
        wl = {k.upper(): str(v) for k, v in where.items()}
        rows = []
        for row in read_rows(spec.name, include_deleted=a.include_deleted):
            if all(row.get(k, "") == v for k, v in wl.items()):
                rows.append(row)
                if a.limit and len(rows) >= a.limit:
                    break
        _print_rows(rows, spec)
        return 0

    area = area_factory(spec)
    try:
        if cmd == "create":
            res = op_create(area, spec, _parse_sets(a.set))
            print(f"created {spec.name}: {res}")
        elif cmd == "update":
            res = op_update(area, spec, a.key, where, _parse_sets(a.set))
            print(f"updated {spec.name}: {res}")
        elif cmd == "delete":
            if a.purge:
                if not a.yes:
                    print("REFUSED: --purge sets the xBase deleted tombstone. It is "
                          "IRREVERSIBLE via pydottalk (no RECALL) and does not reclaim "
                          "space (engine PACK needed). Re-run with --yes to confirm.",
                          file=sys.stderr)
                    return 3
                res = op_purge(area, spec, a.key, where)
                print(f"PURGED {spec.name}: {res}")
            else:
                res = op_soft_close(area, spec, a.key, where)
                print(f"soft-closed {spec.name}: {res}")
        else:
            print(f"unknown command: {cmd}", file=sys.stderr)
            return 2
        return 0
    finally:
        area.close()


def shell(area_factory=_open_real_area) -> int:
    print("dbf-crud mini shell (posture A). Commands: list | read | create | update "
          "| delete | help | quit")
    print("example: read SYSLANE --where STATUS=1 --limit 5")
    while True:
        try:
            raw = input("dbf> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        parts = shlex.split(raw)
        cmd, rest = resolve_cmd(parts[0]), parts[1:]
        if cmd == "quit":
            return 0
        if cmd == "help":
            print("  list | read T [--where F=V] | create T --set F=V | "
                  "update T --key K --set F=V | delete T --key K [--purge --yes]")
            continue
        try:
            dispatch(cmd, rest, area_factory)
        except (CrudError, KeyError) as exc:
            print(f"error: {exc}", file=sys.stderr)
        except SystemExit:
            pass  # argparse on a bad line should not kill the shell


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = resolve_cmd(argv[0]), argv[1:]
    if argv[0].lower() in ("shell", "repl"):
        return shell()
    try:
        return dispatch(cmd, rest)
    except (CrudError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
