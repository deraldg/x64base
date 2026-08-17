"""Regression: the reports gateway must carry a WebSocket upgrade to upstream.

WHY THESE ASSERTIONS AND NOT "IT DID NOT ERROR"
    The defect this guards against produced no error at any layer. The gateway
    proxied the handshake GET as an ordinary GET, upstream answered, the client
    got valid HTTP, and `next dev`'s HMR socket simply never connected -- so
    React never hydrated behind :3000 and every client component sat inert while
    the page looked perfect. Measured 2026-08-15: 3 of 490 elements carried a
    React fiber through the gateway against 445 of 493 direct.

    So a test that asserts "no exception" would have passed against the broken
    gateway. Each arm below asserts an OBSERVED protocol outcome instead: a 101
    reaching the client, the challenge/response surviving byte-for-byte, and
    real payload crossing in both directions.

PROVEN TO FAIL (2026-08-16, AIF-118). Four mutations of ws_proxy.py, each
reverted after:
    never detect the upgrade      -> arm A fails, "NO 101"
    compare Connection whole      -> arm C fails (real clients send
                                     "keep-alive, Upgrade")
    drop Sec-WebSocket-Key        -> arm A fails, challenge corrupted
    relay one direction only      -> arm B times out
A fifth check is structural: the mutation helper asserts its anchor exists,
because an earlier attempt in this lane silently substituted nothing and the
resulting PASS meant only that no mutation had been applied.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import importlib.util
import os
import socket
import threading
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "ws_proxy.py"
SPEC = importlib.util.spec_from_file_location("ws_proxy", MODULE_PATH)
ws_proxy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ws_proxy)

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _accept_loop(sock):
    while True:
        try:
            conn, _ = sock.accept()
        except OSError:
            return
        threading.Thread(target=_echo_ws, args=(conn,), daemon=True).start()


def _echo_ws(conn):
    """Minimal RFC 6455 upstream: real handshake, then echo raw bytes."""
    buf = b""
    try:
        while b"\r\n\r\n" not in buf:
            piece = conn.recv(4096)
            if not piece:
                return
            buf += piece
        key = b""
        for line in buf.split(b"\r\n"):
            if line.lower().startswith(b"sec-websocket-key:"):
                key = line.split(b":", 1)[1].strip()
        accept = base64.b64encode(hashlib.sha1(key + GUID).digest())
        conn.sendall(
            b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
            b"Connection: Upgrade\r\nSec-WebSocket-Accept: " + accept + b"\r\n\r\n"
        )
        while True:
            data = conn.recv(4096)
            if not data:
                return
            conn.sendall(b"ECHO:" + data)
    except OSError:
        return
    finally:
        try:
            conn.close()
        except OSError:
            pass


class WebSocketUpgradeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = socket.socket()
        cls.up.bind(("127.0.0.1", 0))
        cls.up.listen(8)
        cls.uport = cls.up.getsockname()[1]
        threading.Thread(target=_accept_loop, args=(cls.up,), daemon=True).start()

        upstream = f"http://127.0.0.1:{cls.uport}"

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_GET(self):
                # The same two lines the real gateway uses.
                if ws_proxy.try_proxy_upgrade(self, upstream):
                    return
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"hi")

        cls.gw = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.gport = cls.gw.server_address[1]
        threading.Thread(target=cls.gw.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.gw.shutdown()
        cls.gw.server_close()
        cls.up.close()

    def _handshake(self, connection_header="Upgrade"):
        sock = socket.create_connection(("127.0.0.1", self.gport), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall(
            (
                "GET /_next/webpack-hmr HTTP/1.1\r\n"
                "Host: gateway\r\n"
                "Upgrade: websocket\r\n"
                f"Connection: {connection_header}\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            piece = sock.recv(4096)
            if not piece:
                break
            buf += piece
        return sock, buf, key

    def test_a_upgrade_reaches_the_client(self):
        sock, resp, key = self._handshake()
        self.addCleanup(sock.close)
        self.assertIn(b"101", resp.split(b"\r\n")[0],
                      "no 101 Switching Protocols -- the upgrade did not cross")
        expected = base64.b64encode(
            hashlib.sha1(key.encode() + GUID).digest()).decode()
        got = [
            line.split(b":", 1)[1].strip().decode()
            for line in resp.split(b"\r\n")
            if line.lower().startswith(b"sec-websocket-accept:")
        ]
        self.assertEqual(got, [expected],
                         "the handshake challenge was altered in transit")

    def test_b_payload_relays_both_directions(self):
        sock, resp, _ = self._handshake()
        self.addCleanup(sock.close)
        self.assertIn(b"101", resp.split(b"\r\n")[0])
        sock.sendall(b"hello-hmr")
        self.assertEqual(sock.recv(4096), b"ECHO:hello-hmr")
        sock.sendall(b"second")
        self.assertEqual(sock.recv(4096), b"ECHO:second")

    def test_c_connection_header_may_be_a_list(self):
        # Real browsers and proxies send "keep-alive, Upgrade". Comparing the
        # header whole is a silent miss -- it looks like "not a websocket".
        sock, resp, _ = self._handshake("keep-alive, Upgrade")
        self.addCleanup(sock.close)
        self.assertIn(b"101", resp.split(b"\r\n")[0])

    def test_d_plain_get_is_unaffected(self):
        sock = socket.create_connection(("127.0.0.1", self.gport), timeout=10)
        self.addCleanup(sock.close)
        sock.sendall(b"GET /ordinary HTTP/1.1\r\nHost: g\r\nConnection: close\r\n\r\n")
        buf = b""
        while True:
            piece = sock.recv(4096)
            if not piece:
                break
            buf += piece
        self.assertIn(b"200", buf.split(b"\r\n")[0])
        self.assertTrue(buf.endswith(b"hi"))

    def test_e_non_upgrade_headers_are_not_claimed(self):
        # The detector must not claim a request it cannot serve.
        class H:
            pass

        for headers in ({}, {"Upgrade": "h2c", "Connection": "Upgrade"},
                        {"Upgrade": "websocket"}, {"Connection": "Upgrade"}):
            with self.subTest(headers=headers):
                self.assertFalse(ws_proxy.is_websocket_upgrade(headers))

    def test_f_unreachable_upstream_answers_rather_than_hangs(self):
        # A dead upstream must produce a real status, not silence.
        dead = socket.socket()
        dead.bind(("127.0.0.1", 0))
        port = dead.getsockname()[1]
        dead.close()

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_GET(self):
                if ws_proxy.try_proxy_upgrade(self, f"http://127.0.0.1:{port}"):
                    return
                self.send_error(500)

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)

        sock = socket.create_connection(("127.0.0.1", srv.server_address[1]), timeout=10)
        self.addCleanup(sock.close)
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall(
            ("GET /_next/webpack-hmr HTTP/1.1\r\nHost: g\r\nUpgrade: websocket\r\n"
             f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n\r\n").encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            piece = sock.recv(4096)
            if not piece:
                break
            buf += piece
        self.assertIn(b"502", buf.split(b"\r\n")[0],
                      "a dead upstream must answer 502, not fall silent")


if __name__ == "__main__":
    unittest.main()
