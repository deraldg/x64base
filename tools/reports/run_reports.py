#!/usr/bin/env python3
"""Launch the local AI-operations report stack and open the live view.

One command brings up both servers and opens the browser:
  1. the website dev server (Next.js) on an upstream port (preferred 3002)
  2. the dynamic reports gateway (serve_dynamic_reports.py) on a public port
     (preferred 3000), which re-runs the report builder on every request and
     proxies everything else to the website.

Port handling (why this is not hard-coded):
  * Next.js AUTO-BUMPS if its requested port is taken (3000 -> 3001 -> ...), so
    this launcher picks a guaranteed-free port itself and forces Next onto it,
    then points the gateway's upstream at that exact port -- they always match.
  * The gateway is a plain Python http.server and does NOT auto-bump; if its
    port is taken it would error, so the launcher picks a free one for it too.
  * If a server is already listening on the preferred port, it is reused.
  * Even with no website up, /reports/ still works -- the gateway regenerates
    reports locally; the upstream only serves the rest of the site.

The actual live URL is printed at the end (open :GATEWAY, not :SITE). Each server
runs in its own console window; close it (or Ctrl+C in it) to stop that server.

Usage:
  python tools/reports/run_reports.py
  python tools/reports/run_reports.py --site D:/dev/x64base-site
  python tools/reports/run_reports.py --no-open
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
GATEWAY = REPO / "tools" / "reports" / "serve_dynamic_reports.py"


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """True if something is already listening on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def _free_port(host: str, preferred: int, span: int = 30) -> int:
    """The preferred port if bindable, else the next free port above it."""
    for port in range(preferred, preferred + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    return preferred


def _wait_for_port(host: str, port: int, label: str, tries: int = 90) -> bool:
    for _ in range(tries):
        if _port_open(host, port):
            return True
        time.sleep(1)
    print(f"[run_reports] timed out waiting for {label} on {host}:{port}", file=sys.stderr)
    return False


def _spawn(command: str, cwd: Path) -> subprocess.Popen:
    """Start a long-running server in its own window so it outlives this launcher."""
    kwargs = {"cwd": str(cwd), "shell": True}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Launch the local report stack.")
    parser.add_argument(
        "--site",
        default=os.environ.get("X64BASE_SITE", "D:/dev/x64base-site"),
        help="website source dir (Next.js) [default: D:/dev/x64base-site]",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--site-port", type=int, default=3002, help="preferred website upstream port")
    parser.add_argument("--gateway-port", type=int, default=3000, help="preferred reports gateway port")
    parser.add_argument("--report", default="AI_PORTAL_REPORT.html", help="report to open")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    args = parser.parse_args(argv)

    if not GATEWAY.is_file():
        print(f"[run_reports] gateway not found: {GATEWAY}", file=sys.stderr)
        return 2

    site = Path(args.site)

    # 1. website (upstream) -----------------------------------------------------
    if _port_open(args.host, args.site_port):
        upstream_port = args.site_port
        print(f"[run_reports] website already up on {args.host}:{upstream_port} -- reusing it")
    elif site.is_dir():
        upstream_port = _free_port(args.host, args.site_port)
        print(f"[run_reports] starting website: npx next dev -p {upstream_port}  (in {site})")
        # a free port is forced, so Next lands on it exactly (no surprise bump)
        _spawn(f"npx next dev -p {upstream_port}", site)
        _wait_for_port(args.host, upstream_port, "website")
    else:
        upstream_port = args.site_port
        print(
            f"[run_reports] site dir not found ({site}); skipping website. "
            "Reports still work; non-report pages will 502 until a site is up."
        )

    # 2. gateway (public) -------------------------------------------------------
    if _port_open(args.host, args.gateway_port):
        gateway_port = args.gateway_port
        print(f"[run_reports] gateway already up on {args.host}:{gateway_port} -- reusing it")
    else:
        gateway_port = _free_port(args.host, args.gateway_port)
        print(
            f"[run_reports] starting gateway on {args.host}:{gateway_port} "
            f"(upstream http://{args.host}:{upstream_port})"
        )
        gw_cmd = (
            f'"{sys.executable}" "{GATEWAY}" '
            f"--bind {args.host} --port {gateway_port} "
            f"--upstream http://{args.host}:{upstream_port}"
        )
        _spawn(gw_cmd, REPO)
        _wait_for_port(args.host, gateway_port, "gateway")

    url = f"http://localhost:{gateway_port}/reports/{args.report}"
    print("")
    print(f"[run_reports] LIVE report:  {url}")
    print(f"[run_reports] website:      http://localhost:{upstream_port}/  (its /reports/ is STALE static)")
    print("[run_reports] You are on the live view when you see the green")
    print("[run_reports] 'LIVE LOCAL VIEW ... generated for this request' banner + a current timestamp.")
    if not args.no_open:
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
