#!/usr/bin/env python3
"""Tests for bbs_auth_relay -- the AIF-097 Part B auth-relay logic.

The socket is mocked via a fake transport, so these test the DECISION logic against the exact
bbsd responses (verified from src/bbs/bbs_server.cpp) without a live daemon. The load-bearing
tests are the no-leak check and the injection rejection.
"""

import unittest

import bbs_auth_relay as R


def transport_returning(line):
    def _t(_auth_line):
        return line
    return _t


class TestParse(unittest.TestCase):
    def test_ok_extracts_member(self):
        r = R.parse_response("OK member.derald")
        self.assertTrue(r.ok)
        self.assertEqual(r.member, "member.derald")

    def test_err_is_generic_failure(self):
        r = R.parse_response("ERR auth failed")
        self.assertFalse(r.ok)
        self.assertIsNone(r.member)

    def test_empty_is_failure(self):
        self.assertFalse(R.parse_response("").ok)
        self.assertFalse(R.parse_response(None).ok)


class TestAuthenticate(unittest.TestCase):
    def test_success(self):
        r = R.authenticate("member.derald", "goodtoken", transport_returning("OK member.derald"))
        self.assertTrue(r.ok)
        self.assertEqual(r.member, "member.derald")

    def test_no_leak_bad_member_and_bad_token_are_indistinguishable(self):
        # bbsd returns the SAME "ERR auth failed" whether the member or the token was wrong.
        bad_member = R.authenticate("nope", "goodtoken", transport_returning("ERR auth failed"))
        bad_token = R.authenticate("member.derald", "wrong", transport_returning("ERR auth failed"))
        self.assertFalse(bad_member.ok)
        self.assertFalse(bad_token.ok)
        self.assertEqual(bad_member.reason, bad_token.reason)   # no distinction leaked

    def test_daemon_unreachable_is_failure_not_exception(self):
        def boom(_):
            raise OSError("connection refused")
        r = R.authenticate("member.derald", "t", boom)
        self.assertFalse(r.ok)
        self.assertIn("unreachable", r.reason)

    def test_malformed_input_never_hits_the_wire(self):
        calls = []
        def spy(line):
            calls.append(line); return "OK x"
        # a token containing a space/newline could inject a second command on the wire
        r = R.authenticate("member.derald", "tok en", spy)
        self.assertFalse(r.ok)
        r2 = R.authenticate("member.derald", "tok\nSHUTDOWN", spy)
        self.assertFalse(r2.ok)
        self.assertEqual(calls, [])   # transport never called for malformed input


class TestBuildLine(unittest.TestCase):
    def test_well_formed(self):
        self.assertEqual(R.build_auth_line("member.derald", "abc"), "AUTH member.derald abc\n")

    def test_rejects_whitespace_and_control(self):
        for bad in ["a b", "a\tb", "a\nb", "", "a\x00b"]:
            with self.assertRaises(ValueError):
                R.build_auth_line("member.derald", bad)
            with self.assertRaises(ValueError):
                R.build_auth_line(bad, "token")


if __name__ == "__main__":
    unittest.main(verbosity=2)
