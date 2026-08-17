#!/usr/bin/env python3
"""Maintenance UI for the AI-Portal tracking system (AIF-086).

A small local web console over tools/dbf/crud.py for the tracking tables
(SYSLANE / SYSRUN / SYSRUNLANE / SYSPROOF / SYSTASK) and, read-only, every other
SYS* table. It is a maintenance surface, not a public report:

  READ  is the pure DBF path (crud.read_rows) -- no engine, works anywhere.
  WRITE reuses crud's CRUD with posture-A semantics:
        - soft-close by default, --purge (tombstone) behind an explicit confirm,
        - bbs tables write-guarded, append-only refused, crosswalk rules enforced,
        - two modes: EXECUTE (through pydottalk) or EMIT (return the DotScript /
          fsram dry run so you can feed it via datarun yourself).

Loopback only. Single-writer (pydottalk takes no lock). Run:

    python tools/dbf/maint_server.py            # http://127.0.0.1:8770
    python tools/dbf/maint_server.py --port 8771

The EMIT mode needs no engine and works in any environment; EXECUTE needs a
pydottalk built with xbase (see the capability review).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hmac
import ipaddress
import json
import secrets
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_registry as reg   # noqa: E402
import crud                     # noqa: E402


REPO = Path(__file__).resolve().parents[2]
PAGE_PATH = Path(__file__).resolve().with_name("maint_console.html")
WRITE_LOCK = threading.Lock()


def is_loopback_host(value: str | None) -> bool:
    """Return True only for an explicit loopback hostname or address."""
    host = (value or "").strip().strip("[]").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def require_local_json(headers, expected_token: str = "") -> None:
    """Enforce the browser boundary for maintenance POST requests."""
    if headers.get_content_type() != "application/json":
        raise crud.CrudError("maintenance POST requires Content-Type: application/json")
    host = urllib.parse.urlsplit("//" + (headers.get("Host") or "")).hostname
    if not is_loopback_host(host):
        raise crud.CrudError("maintenance POST requires a loopback Host header")
    origin = headers.get("Origin")
    if origin and not is_loopback_host(urllib.parse.urlsplit(origin).hostname):
        raise crud.CrudError("maintenance POST rejected non-loopback Origin")
    supplied = headers.get("X-DotTalk-Maint-Token") or ""
    if expected_token and not hmac.compare_digest(supplied, expected_token):
        raise crud.CrudError("maintenance POST rejected invalid session token")


def _iso_mtime(path: Path) -> str:
    if not path.is_file():
        return ""
    return dt.datetime.fromtimestamp(
        path.stat().st_mtime, tz=dt.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def _registry_health(repo_root: Path | None = None) -> dict:
    """Compare live per-record fragments with reviewed flat snapshot inputs.

    The fragments are development truth.  The flat files are deliberately kept as
    the reviewed production-snapshot inputs, so a difference is reported as snapshot
    lag rather than silently repaired from this maintenance surface.
    """
    root = Path(repo_root or REPO).resolve()
    registry_tools = root / "tools" / "registries"
    if not (registry_tools / "registry_fragments.py").is_file():
        registry_tools = REPO / "tools" / "registries"
    if str(registry_tools) not in sys.path:
        sys.path.insert(0, str(registry_tools))
    try:
        import registry_fragments as fragments  # noqa: E402
    except BaseException as exc:  # PyYAML absence raises SystemExit in that module.
        return {
            "ok": False,
            "error": f"registry health unavailable: {type(exc).__name__}: {exc}",
            "items": [],
            "pending_total": 0,
        }

    labels = {
        "ai_runs.yaml": "Runs",
        "proofs.yaml": "Proofs",
        "lessons.yaml": "Lessons",
    }
    items = []
    pending_total = 0
    for name, spec in fragments.SPECS.items():
        flat_path = root / "labtalk" / "registries" / name
        try:
            flat = fragments.load(flat_path) if flat_path.is_file() else {}
            flat_rows = flat.get(spec["key"]) or []
            _, live_rows = fragments.read_fragments(root, spec)
            if live_rows is None:
                live_rows = []
            flat_ids = {
                str(row.get(spec["idf"]))
                for row in flat_rows
                if isinstance(row, dict) and row.get(spec["idf"])
            }
            live_ids = {
                str(row.get(spec["idf"]))
                for row in live_rows
                if isinstance(row, dict) and row.get(spec["idf"])
            }
            new_ids = sorted(live_ids - flat_ids)
            flat_only = sorted(flat_ids - live_ids)
            flat_by_id = {
                str(row.get(spec["idf"])): row
                for row in flat_rows
                if isinstance(row, dict) and row.get(spec["idf"])
            }
            live_by_id = {
                str(row.get(spec["idf"])): row
                for row in live_rows
                if isinstance(row, dict) and row.get(spec["idf"])
            }
            changed = sorted(
                identity for identity in live_ids & flat_ids
                if live_by_id[identity] != flat_by_id[identity]
            )
            pending = sorted(set(new_ids + changed))
            pending_total += len(pending)
            item = {
                "name": name,
                "label": labels.get(name, name),
                "fragment_dir": spec["dir"],
                "live_count": len(live_ids),
                "snapshot_count": len(flat_ids),
                "pending_count": len(pending),
                "flat_only_count": len(flat_only),
                "pending_ids": pending,
                "new_ids": new_ids,
                "changed_ids": changed,
                "flat_only_ids": flat_only,
                "snapshot_modified_at": _iso_mtime(flat_path),
            }
            if name == "ai_runs.yaml":
                composed = fragments.compose_registry(root, name)
                item["live_lane_count"] = len(composed.get("current_by_lane") or {})
                item["snapshot_lane_count"] = len(flat.get("current_by_lane") or {})
                item["index_drift"] = bool(
                    composed.get("current_by_lane") != flat.get("current_by_lane")
                    or composed.get("current_by_project") != flat.get("current_by_project")
                )
            else:
                item["index_drift"] = False
            item["status"] = (
                "current"
                if not pending and not flat_only and not item["index_drift"]
                else "snapshot_lag"
            )
            items.append(item)
        except Exception as exc:  # One broken registry should not hide DBF maintenance.
            items.append({
                "name": name,
                "label": labels.get(name, name),
                "fragment_dir": spec["dir"],
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "live_count": 0,
                "snapshot_count": 0,
                "pending_count": 0,
                "flat_only_count": 0,
                "pending_ids": [],
                "new_ids": [],
                "changed_ids": [],
                "flat_only_ids": [],
                "index_drift": False,
            })
    return {
        "ok": all(item.get("status") != "error" for item in items),
        "items": items,
        "pending_total": pending_total,
        "live_source": "registry fragments",
        "snapshot_source": "reviewed flat registries",
    }


def _table_summary(spec: reg.TableSpec) -> dict:
    path = crud.META / spec.subdir / f"{spec.name}.dbf"
    base = {
        "name": spec.name,
        "subdir": spec.subdir,
        "writable": spec.writable,
        "close": spec.close.kind,
        "append_only": spec.append_only,
        "pk": spec.pk,
        "key": spec.key,
        "ckey": list(spec.ckey),
        "field_count": len(spec.fields),
        "exists": path.is_file(),
        "modified_at": _iso_mtime(path),
    }
    if not path.is_file():
        return {**base, "count": 0, "live": 0, "error": "DBF not found"}
    try:
        rows = crud.read_rows(
            spec.name,
            include_deleted=True,
            include_metadata=True,
        )
        live = sum(
            not row.get("_deleted", False) and crud.is_live(spec, row)
            for row in rows
        )
        return {**base, "count": len(rows), "live": live, "error": ""}
    except Exception as exc:  # Keep the rest of the catalog visible.
        return {
            **base,
            "count": 0,
            "live": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


# ---- JSON API helpers ---------------------------------------------------------
def _tables_payload(repo_root: Path | None = None, write_enabled: bool = True) -> dict:
    out = [_table_summary(reg.TABLES[name]) for name in sorted(reg.TABLES)]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "posture": {
            "execute_enabled": bool(write_enabled),
            "default_mode": "dts",
            "direct_write_locking": "single-writer; pydottalk exposes no lock",
        },
        "catalogs": {
            catalog: len([item for item in out if item["subdir"] == catalog])
            for catalog in sorted({item["subdir"] for item in out})
        },
        "registry_health": _registry_health(repo_root),
        "tables": out,
    }


def _table_payload(name: str, include_deleted: bool) -> dict:
    spec = reg.get(name)
    rows = crud.read_rows(
        name,
        include_deleted=include_deleted,
        include_metadata=True,
    )
    live = [
        not row.get("_deleted", False) and crud.is_live(spec, row)
        for row in rows
    ]
    return {
        "name": spec.name, "subdir": spec.subdir, "writable": spec.writable,
        "append_only": spec.append_only, "close": spec.close.kind,
        "pk": spec.pk, "key": spec.key, "ckey": list(spec.ckey),
        "columns": list(spec.field_names()),
        "fields": [
            {"name": field_name, "type": field_type, "width": field_width}
            for field_name, field_type, field_width in spec.fields
        ],
        "rows": [{"_live": lv, **r} for r, lv in zip(rows, live)],
        "count": len(rows), "live": sum(live),
        "modified_at": _iso_mtime(
            crud.META / spec.subdir / f"{spec.name}.dbf"
        ),
    }


def _assert_expected_rowver(
    spec: reg.TableSpec,
    key,
    where: dict,
    expected,
) -> None:
    """Refuse a stale direct edit before opening the lockless writer.

    This check prevents two browser operations in this maintenance process from
    silently overwriting one another.  It is not a substitute for an engine-level
    cross-process lock, which pydottalk does not expose.
    """
    rowver = spec.close.rowver
    if not rowver:
        return
    if expected is None or str(expected).strip() == "":
        raise crud.CrudError(f"{spec.name}: expected {rowver} is required for direct mutation")
    selector = crud._key_selector(
        spec,
        key,
        {field.upper(): value for field, value in where.items()},
    )
    matches = [
        row for row in crud.read_rows(spec.name)
        if all(str(row.get(field, "")) == str(value) for field, value in selector.items())
    ]
    if not matches:
        raise crud.CrudError(f"{spec.name}: no live row matching {selector}")
    observed = str(matches[-1].get(rowver, "")).strip()
    if observed != str(expected).strip():
        raise crud.CrudError(
            f"{spec.name}: stale row version; expected {expected}, observed {observed}. Reload first."
        )


def _do_op(body: dict, write_enabled: bool = True) -> dict:
    """Dispatch a write. mode: 'execute' | 'dts' | 'ram'.
    write_enabled=False (the shared gateway default) refuses Execute -- read + emit only."""
    cmd = body.get("op")
    table = body.get("table", "")
    spec = reg.get(table)
    values = body.get("set", {}) or {}
    key = body.get("key")
    where = body.get("where", {}) or {}
    purge = bool(body.get("purge"))
    mode = body.get("mode", "dts")

    if cmd not in ("create", "update", "delete"):
        raise crud.CrudError(f"unknown op: {cmd}")
    if mode not in ("dts", "ram", "execute"):
        raise crud.CrudError(f"unknown mode: {mode}")

    if purge and body.get("confirm") != f"PURGE {spec.name}":
        raise crud.CrudError(
            f"purge confirmation mismatch: enter PURGE {spec.name} exactly"
        )

    if mode in ("dts", "ram"):
        fn = crud.emit_ram if mode == "ram" else crud.emit_dts
        lines = fn(cmd, spec, values, key, where, purge, bool(body.get("indexed")))
        return {"ok": True, "mode": mode, "dotscript": "\n".join(lines)}

    if not write_enabled:
        raise crud.CrudError("Execute is disabled on this surface (read + emit only). "
                             "Use Emit DotScript / Emit fsram here, or run the standalone "
                             "maint_server.py for live writes.")
    if not body.get("ack_execute"):
        raise crud.CrudError(
            "Execute requires explicit acknowledgement of the single-writer, no-lock posture."
        )
    if cmd in ("update", "delete"):
        _assert_expected_rowver(spec, key, where, body.get("expected_rowver"))
    # EXECUTE via pydottalk. Refuse a write that cannot land BEFORE opening the engine
    # (bbs guard / append-only update), so we never spin up the lock-less writer for it.
    crud._require_writable(spec)
    if cmd == "update" and spec.append_only:
        raise crud.CrudError(f"{spec.name} is append-only: update-in-place is refused; "
                             f"create a superseding row instead.")
    area = crud._open_real_area(spec)
    try:
        if cmd == "create":
            res = crud.op_create(area, spec, values)
        elif cmd == "update":
            res = crud.op_update(area, spec, key, where, values)
        else:  # delete
            res = crud.op_purge(area, spec, key, where) if purge \
                else crud.op_soft_close(area, spec, key, where)
        return {"ok": True, "mode": "execute", "result": res}
    finally:
        area.close()


# ---- HTTP handler -------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, obj=None, html=None):
        self.send_response(code)
        if html is not None:
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = html.encode("utf-8")
        else:
            self.send_header("Content-Type", "application/json")
            body = json.dumps(obj).encode("utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                return self._send(
                    200,
                    html=render_page(
                        "/api", True, getattr(self.server, "write_token", "")
                    ),
                )
            if u.path == "/api/tables":
                return self._send(200, _tables_payload(REPO, write_enabled=True))
            if u.path.startswith("/api/table/"):
                name = u.path.rsplit("/", 1)[-1]
                inc = parse_qs(u.query).get("deleted", ["0"])[0] == "1"
                return self._send(200, _table_payload(name, inc))
            return self._send(404, {"error": "not found"})
        except (crud.CrudError, KeyError) as exc:
            return self._send(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return self._send(500, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        try:
            require_local_json(self.headers, getattr(self.server, "write_token", ""))
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if self.path != "/api/op":
                return self._send(404, {"error": "not found"})
            with WRITE_LOCK:
                return self._send(200, _do_op(body))
        except (crud.CrudError, KeyError) as exc:
            return self._send(400, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})


# NOTE (2026-08-17, AIF-118): the module-level `PAGE` template that used to sit
# here was REMOVED. It was an 8,698-character copy of the console HTML, left
# behind when the page was extracted to maint_console.html and loaded through
# PAGE_PATH. Nothing referenced it -- `render_page()` below reads the file --
# so it was a second, silent source of truth: edit the real page and this copy
# stays behind, looking authoritative to anyone who opens the module. It had
# already missed the light theme added the same morning.
#
# If a no-file fallback is wanted, make it an explicit failure instead of a
# stale duplicate: let PAGE_PATH.read_text() raise, or catch and serve a short
# diagnostic that names the missing path. A fallback that silently serves
# different bytes than the file is the defect, not the safety net.


def render_page(
    api_base: str = "/api",
    write_enabled: bool = True,
    write_token: str = "",
) -> str:
    """The console HTML with its API base path and write flag injected. Lets the same
    page serve standalone (/api, write) or mounted on the gateway (/AI/console/api, emit)."""
    template = PAGE_PATH.read_text(encoding="utf-8")
    return (template.replace("__API_BASE__", api_base)
                .replace("__WRITE__", "true" if write_enabled else "false")
                .replace("__WRITE_TOKEN__", json.dumps(write_token)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tracking maintenance UI")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    if not is_loopback_host(a.host):
        ap.error("write-enabled maintenance server must bind to loopback")
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.write_token = secrets.token_urlsafe(32)
    print(f"tracking maintenance UI: http://{a.host}:{a.port}  (loopback only, Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
