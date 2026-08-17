#!/usr/bin/env python3
"""ws_proxy -- carry a WebSocket upgrade through the reports gateway.

WHY THIS EXISTS (measured 2026-08-15, fixed 2026-08-16, AIF-118)
    serve_dynamic_reports proxies the website with urllib, which speaks HTTP and
    only HTTP. A WebSocket handshake is an HTTP GET carrying `Upgrade:
    websocket`, and the server answers `101 Switching Protocols` -- after which
    the socket is no longer HTTP at all. urllib cannot represent that, so the
    upgrade was dropped and the request fell through to an ordinary GET.

    The cost was not an error. It was SILENCE. `next dev` serves its HMR client
    over that socket; with the socket dead, React never hydrates behind :3000.
    Measured: 3 of 490 elements carried a React fiber via the gateway, against
    445 of 493 on :3002 direct. Every client component was inert -- menus did
    not open, useEffect never fired, the theme control did nothing. The HTML
    arrived byte-identical, every chunk loaded, the console was clean and the
    page LOOKED perfect. The only tell was that "[HMR] connected" appeared on
    :3002 and never on :3000.

    That cost five rounds of "fixing" a theme button that had never once been
    able to run a click handler. This module is the real fix.

WHAT IT DOES
    Detects the upgrade on the way in, opens a raw TCP socket to upstream,
    replays the client's request line and headers verbatim, and then pumps bytes
    in both directions until either side closes. It does NOT parse WebSocket
    frames -- there is no reason to. The gateway is a pipe here, and a pipe that
    understands the payload is a pipe that can corrupt it.

WHAT IT DELIBERATELY DOES NOT DO
    No frame inspection, no message logging, no reconnection, no buffering
    beyond one relay chunk. If upstream is down the handshake fails and the
    caller falls back to the ordinary HTTP path, which is the pre-existing
    behaviour and already reports it.

Exit criteria this module was held to: the upgrade must be OBSERVED to cross
(a 101 from upstream reaching the client), not merely "not error".
"""

from __future__ import annotations

import selectors
import socket
import urllib.parse

# A relay chunk. HMR payloads are small; this only bounds one read.
RELAY_CHUNK = 65536

# How long to wait for upstream's 101. The handshake is local (127.0.0.1), so
# this is generous. It is NOT the lifetime of the socket -- once the relay
# starts, the sockets block indefinitely and are governed by selectors.
HANDSHAKE_TIMEOUT = 10.0


def is_websocket_upgrade(headers) -> bool:
    """True when this request is a WebSocket handshake.

    Both headers are required by RFC 6455 and both are checked. `Connection`
    may be a comma-separated list ("keep-alive, Upgrade"), so it is tokenised
    rather than compared whole -- comparing whole is a silent miss, which is
    the defect class this module exists to close.
    """
    upgrade = (headers.get("Upgrade") or "").strip().lower()
    if upgrade != "websocket":
        return False
    connection = (headers.get("Connection") or "").lower()
    return any(tok.strip() == "upgrade" for tok in connection.split(","))


def _rebuild_request(handler) -> bytes:
    """Reconstruct the client's request line and headers, byte-for-byte.

    Sec-WebSocket-Key and Sec-WebSocket-Accept are a challenge/response pair.
    Rewriting or normalising ANY header here risks breaking that handshake, so
    headers are replayed exactly as received. Only Host is rewritten, because
    upstream is a different authority and some dev servers check it.
    """
    parts = urllib.parse.urlsplit(handler.path)
    target = parts.path + (("?" + parts.query) if parts.query else "")
    lines = [f"GET {target} HTTP/1.1"]
    for key, value in handler.headers.items():
        if key.lower() == "host":
            continue
        lines.append(f"{key}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")


def _relay(a: socket.socket, b: socket.socket) -> None:
    """Pump bytes between two sockets until either closes.

    selectors rather than two threads: one connection is one thread already
    (ThreadingHTTPServer), and spawning two more per socket to move bytes is
    how a dev gateway ends up with hundreds of threads after an afternoon of
    page reloads.
    """
    sel = selectors.DefaultSelector()
    a.setblocking(False)
    b.setblocking(False)
    sel.register(a, selectors.EVENT_READ, b)
    sel.register(b, selectors.EVENT_READ, a)
    try:
        while True:
            for key, _ in sel.select(timeout=None):
                src: socket.socket = key.fileobj  # type: ignore[assignment]
                dst: socket.socket = key.data
                try:
                    chunk = src.recv(RELAY_CHUNK)
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError:
                    return
                if not chunk:
                    return
                try:
                    dst.sendall(chunk)
                except OSError:
                    return
    finally:
        sel.close()


def try_proxy_upgrade(handler, upstream: str) -> bool:
    """Carry a WebSocket upgrade to `upstream`. Returns True if it was handled.

    Returns False when this is not an upgrade, so the caller falls straight
    through to its ordinary HTTP path. Returns True once the socket has been
    taken over -- after which the caller MUST NOT write to it, and must set
    close_connection so the handler loop does not try to read another request
    off a socket that is no longer speaking HTTP.
    """
    if not is_websocket_upgrade(handler.headers):
        return False

    parts = urllib.parse.urlsplit(upstream)
    host = parts.hostname or "127.0.0.1"
    port = parts.port or (443 if parts.scheme == "https" else 80)

    try:
        server = socket.create_connection((host, port), timeout=HANDSHAKE_TIMEOUT)
    except OSError:
        # Upstream is down. Say so in the protocol the CLIENT is speaking: it
        # asked for an upgrade, so a 502 is a real answer. Silence here would
        # reproduce the exact defect this module was written to remove.
        try:
            handler.send_error(502, "websocket upstream unreachable")
        except OSError:
            pass
        return True

    try:
        server.sendall(_rebuild_request(handler))
        # Read only the handshake response, then stop parsing forever. The
        # header terminator may arrive split across reads, so accumulate.
        buf = b""
        while b"\r\n\r\n" not in buf:
            server.settimeout(HANDSHAKE_TIMEOUT)
            piece = server.recv(RELAY_CHUNK)
            if not piece:
                raise OSError("upstream closed during handshake")
            buf += piece

        client = handler.connection
        handler.close_connection = True
        client.sendall(buf)

        # A non-101 is upstream declining the upgrade. Its response has already
        # been forwarded verbatim, so the client sees the real reason rather
        # than a gateway invention. Nothing left to relay.
        status_ok = buf.split(b"\r\n", 1)[0].split(b" ", 2)[1:2] == [b"101"]
        if not status_ok:
            return True

        server.settimeout(None)
        _relay(client, server)
        return True
    except OSError:
        handler.close_connection = True
        return True
    finally:
        try:
            server.close()
        except OSError:
            pass
