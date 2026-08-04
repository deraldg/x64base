#!/usr/bin/env python3
"""Serve local AI operational reports dynamically and proxy the website.

Every report request runs the existing read-only report builder into a fresh
temporary directory. The response therefore reflects the current DBF tables,
registries, and AIF queue without mutating ``docs/reports`` or relying on a
manual regeneration step.

Non-report requests are proxied to the local website development server. This
keeps the normal ``http://localhost:3000`` entry point while the reports remain
local-only and absent from public builds.

Usage:
    python tools/reports/serve_dynamic_reports.py
    python tools/reports/serve_dynamic_reports.py --upstream http://127.0.0.1:3002
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.server
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPORT_ALIASES = {
    "": "index.html",
    "index": "index.html",
    "index.html": "index.html",
    "AI_PORTAL_REPORT": "AI_PORTAL_REPORT.html",
    "AI_PORTAL_REPORT.html": "AI_PORTAL_REPORT.html",
    "BBS_BOARDS_REPORT": "BBS_BOARDS_REPORT.html",
    "BBS_BOARDS_REPORT.html": "BBS_BOARDS_REPORT.html",
    "BBS_ACCESS_REPORT": "BBS_ACCESS_REPORT.html",
    "BBS_ACCESS_REPORT.html": "BBS_ACCESS_REPORT.html",
    "AIF_RULINGS_REPORT": "AIF_RULINGS_REPORT.html",
    "AIF_RULINGS_REPORT.html": "AIF_RULINGS_REPORT.html",
}

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def decorate_live_html(body: bytes, observed: str) -> bytes:
    """Make request-time status visible without altering static export files."""
    text = body.decode("utf-8", "replace")
    marker = '<body><div class="wrap">'
    banner = (
        marker
        + '<div class="band" style="background:#dcfce7;color:#14532d;'
        'border:1px solid #86efac">LIVE LOCAL VIEW -- generated for this request '
        f'from current canonical state at <code>{observed}</code>. Reload to re-read.'
        '</div>'
    )
    if marker in text:
        text = text.replace(marker, banner, 1)
    return text.encode("utf-8")


def report_name_for_path(raw_path: str) -> str | None:
    path = urllib.parse.urlsplit(raw_path).path
    if path in {"/reports", "/reports/"}:
        return "index.html"
    if not path.startswith("/reports/"):
        return None
    relative = urllib.parse.unquote(path[len("/reports/") :]).strip("/")
    return REPORT_ALIASES.get(relative)


class DynamicReportServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, *, repo_root: Path, upstream: str):
        super().__init__(address, handler)
        self.repo_root = repo_root
        self.upstream = upstream.rstrip("/")
        self.render_lock = threading.Lock()

    def render_report(self, name: str) -> tuple[bytes, str]:
        builder = self.repo_root / "tools" / "reports" / "build_reports.py"
        with self.render_lock, tempfile.TemporaryDirectory(
            prefix="dottalk-live-reports-"
        ) as temporary:
            out = Path(temporary)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(builder),
                    "--root",
                    str(self.repo_root),
                    "--out",
                    str(out),
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout).strip()
                raise RuntimeError(detail or f"report builder exited {completed.returncode}")
            target = out / name
            if not target.is_file():
                raise RuntimeError(f"report builder did not emit {name}")
            observed = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return decorate_live_html(target.read_bytes(), observed), observed


class Handler(http.server.BaseHTTPRequestHandler):
    server: DynamicReportServer

    def do_GET(self):
        self._dispatch(include_body=True)

    def do_HEAD(self):
        self._dispatch(include_body=False)

    def _dispatch(self, *, include_body: bool):
        name = report_name_for_path(self.path)
        if name is not None:
            self._serve_report(name, include_body=include_body)
            return
        if urllib.parse.urlsplit(self.path).path.startswith("/reports/"):
            self.send_error(404, "Unknown local report")
            return
        self._proxy(include_body=include_body)

    def _serve_report(self, name: str, *, include_body: bool):
        try:
            body, observed = self.server.render_report(name)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            message = (
                "Dynamic report generation failed.\n\n"
                f"{type(exc).__name__}: {exc}\n"
            ).encode("utf-8", "replace")
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            if include_body:
                self.wfile.write(message)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-DotTalk-Report-Mode", "dynamic")
        self.send_header("X-DotTalk-Report-Observed-At", observed)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _proxy(self, *, include_body: bool):
        target = self.server.upstream + self.path
        request = urllib.request.Request(target, method="GET" if include_body else "HEAD")
        for key in ("Accept", "Accept-Language", "User-Agent"):
            value = self.headers.get(key)
            if value:
                request.add_header(key, value)
        try:
            response = urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        except urllib.error.URLError as exc:
            message = (
                "The local website server is unavailable, but /reports/ remains "
                f"available.\n\nUpstream: {self.server.upstream}\n{exc}\n"
            ).encode("utf-8", "replace")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            if include_body:
                self.wfile.write(message)
            return

        body = response.read() if include_body else b""
        self.send_response(response.status)
        for key, value in response.headers.items():
            lower = key.lower()
            if lower in HOP_BY_HOP_HEADERS or lower == "content-length":
                continue
            self.send_header(key, value)
        if include_body:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def log_message(self, fmt: str, *args):
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f"{timestamp} {self.client_address[0]} {fmt % args}\n")
        sys.stdout.flush()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="DotTalk++ repository root",
    )
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--upstream", default="http://127.0.0.1:3002")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    builder = root / "tools" / "reports" / "build_reports.py"
    if not builder.is_file():
        print(f"missing report builder: {builder}", file=sys.stderr)
        return 2
    server = DynamicReportServer(
        (args.bind, args.port),
        Handler,
        repo_root=root,
        upstream=args.upstream,
    )
    print(
        f"Dynamic local reports: http://{args.bind}:{args.port}/reports/\n"
        f"Website upstream:      {args.upstream}\n"
        "Report responses are rebuilt from current local state and are never cached."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
