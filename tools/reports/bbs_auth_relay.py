#!/usr/bin/env python3
"""bbs_auth_relay.py -- validate (member, token) by relaying AUTH to the loopback bbsd.

AIF-097 Part B, M0 (the dogfood). Instead of the gateway hashing or storing credentials, it
opens a loopback socket to dottalk_bbsd and speaks the real AUTH handshake, so bbsd (Argon2id)
stays the single source of auth truth. This module does NO hashing and stores NO credential.

Protocol (verified against src/bbs/bbs_server.cpp `handle_conn`, 2026-08-08):
  client -> "AUTH <member> <token>\n"          first line; the verb is case-insensitive
  server -> "OK <acting_member_key>\n" ".\n"    on success
         -> "ERR auth failed\n" ".\n"           on failure (no leak of which half was wrong)
  client -> "QUIT\n"                            to close cleanly

The socket I/O sits behind a `transport` callable so the decision LOGIC is unit-tested without a
live daemon. bbsd binds 127.0.0.1:8765 by default (loopback only).
"""

import argparse
import socket
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_FORBIDDEN = set(" \t\r\n\x00")   # member.key + token are whitespace-free tokens in the line protocol


class AuthResult:
    def __init__(self, ok, member=None, reason=""):
        self.ok = ok
        self.member = member
        self.reason = reason

    def __repr__(self):
        return "AuthResult(ok=%r, member=%r, reason=%r)" % (self.ok, self.member, self.reason)


def _valid_field(s):
    return bool(s) and not any(c in _FORBIDDEN for c in s)


def build_auth_line(member, token):
    """The first protocol line. Reject whitespace/control chars so a crafted member/token cannot
    corrupt the line protocol or inject a second command (a real risk on a space-delimited wire)."""
    if not _valid_field(member) or not _valid_field(token):
        raise ValueError("member and token must be non-empty with no whitespace or control chars")
    return "AUTH %s %s\n" % (member, token)


def parse_response(first_line):
    """Map bbsd's first response line to an AuthResult. No-leak: any non-OK is one generic failure,
    matching the server, which never says whether the member or the token was wrong."""
    line = (first_line or "").strip()
    if line.startswith("OK"):
        parts = line.split(None, 1)
        return AuthResult(True, member=(parts[1].strip() if len(parts) > 1 else None))
    return AuthResult(False, reason="authentication failed")


def authenticate(member, token, transport):
    """Validate a credential. `transport(auth_line) -> first_response_line`. Malformed input never
    reaches the wire; an unreachable daemon is a failure, not an exception the caller must handle."""
    try:
        auth_line = build_auth_line(member, token)
    except ValueError as exc:
        return AuthResult(False, reason=str(exc))
    try:
        resp = transport(auth_line)
    except OSError as exc:
        return AuthResult(False, reason="bbsd unreachable: %s" % exc)
    return parse_response(resp)


def _recv_line(sk, cap=4096):
    buf = b""
    while b"\n" not in buf and len(buf) < cap:
        chunk = sk.recv(256)
        if not chunk:
            break
        buf += chunk
    return buf.split(b"\n", 1)[0].decode("utf-8", "replace")


def socket_transport(host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=3.0):
    """Real transport: one connection -- send AUTH, read the first line, QUIT, close."""
    def _t(auth_line):
        with socket.create_connection((host, port), timeout=timeout) as sk:
            sk.settimeout(timeout)
            sk.sendall(auth_line.encode("utf-8"))
            first = _recv_line(sk)
            try:
                sk.sendall(b"QUIT\n")
            except OSError:
                pass
            return first
    return _t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--member", required=True)
    ap.add_argument("--token", required=True, help="diagnostic only; a real caller passes this from a form, not argv")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    a = ap.parse_args(argv)
    r = authenticate(a.member, a.token, socket_transport(a.host, a.port))
    print(("OK " + (r.member or "")) if r.ok else ("FAIL " + r.reason), file=sys.stderr)
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
