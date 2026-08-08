#!/usr/bin/env python3
"""Full-pipeline tests for the Lane 1 write adapter (promote.py).

Exercises the whole engine-free chain end to end:
  working-set -> consolidate.propose -> consolidate.confirm -> promote.render -> BBS POST records.
Asserts the attribution and safety invariants the store depends on (AIF-075): posts go through
the attributed shell path (never author 0), bodies are comment-free and single-line, the subject
never collides with the ` BODY ` split marker, and only owner-confirmed items are written.
"""

import json
import unittest
from pathlib import Path

import consolidate as C
import promote as P

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "session_2026-08-08.json"


def pipeline():
    ws = json.loads(FIXTURE.read_text(encoding="utf-8"))
    proposal = C.build_proposal(ws)
    decisions = {c["id"]: "approve" for c in proposal["candidates"] if c["decision"] == "PROMOTE"}
    manifest = C.confirm(proposal, decisions)
    return P.render(manifest, board="board.afb.chat")


class TestRender(unittest.TestCase):
    def test_renders_one_post_per_confirmed_promote(self):
        rendered = pipeline()
        self.assertEqual(rendered["count"], 5)                 # the five PROMOTEs
        self.assertEqual(len(rendered["posts"]), 5)

    def test_every_post_attributed_never_author_zero(self):
        for p in pipeline()["posts"]:
            self.assertTrue(p["command"].startswith("BBS POST "))  # attributed shell path
            self.assertNotIn("author_id=0", p["command"])
            self.assertIn("current_member", p["author"])

    def test_bodies_are_comment_free_and_single_line(self):
        for p in pipeline()["posts"]:
            self.assertNotIn("&&", p["body"])                  # DotTalk++ comment marker banned
            self.assertNotIn("\n", p["body"])
            self.assertTrue(p["body"])

    def test_subject_carries_source_lane_marker_and_no_body_collision(self):
        for p in pipeline()["posts"]:
            self.assertTrue(p["subject"].startswith("[consolidated:"))
            self.assertNotIn(" BODY ", p["subject"])           # would confuse split_subject_body

    def test_body_carries_provenance(self):
        for p in pipeline()["posts"]:
            self.assertIn("provenance:", p["body"])

    def test_only_confirmed_items_render(self):
        # approve a DISCARD in confirm: it must not reach the manifest, so it must not render
        ws = json.loads(FIXTURE.read_text(encoding="utf-8"))
        proposal = C.build_proposal(ws)
        manifest = C.confirm(proposal, {"session_scaffolding": "approve"})
        rendered = P.render(manifest)
        self.assertEqual(rendered["count"], 0)

    def test_ampersand_marker_is_neutralized(self):
        manifest = {"session": {}, "to_write": [{
            "id": "x", "summary": "uses && the comment marker inline", "score": 0.9,
            "owner_confirmed": True, "provenance": {"source_lane": "session"}}]}
        rendered = P.render(manifest)
        self.assertNotIn("&&", rendered["posts"][0]["command"])

    def test_script_comments_only_on_own_lines(self):
        script = P.to_script(pipeline())
        for line in script.splitlines():
            if line.startswith("BBS POST"):
                self.assertNotIn("&&", line)                   # no comment on a POST line


if __name__ == "__main__":
    unittest.main(verbosity=2)
