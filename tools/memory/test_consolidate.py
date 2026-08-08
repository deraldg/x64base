#!/usr/bin/env python3
"""Tests for the Frontal_Mem triage value function (consolidate.py).

The load-bearing test is test_reproduces_hand_triage: the tool must reproduce, on this
session's working-set, the same PROMOTE/DISCARD decisions the agent made BY HAND in
SESSION_CLOSEOUT_PORTAL_MEMORY_SYNAPSE_2026-08-08.md. That closes the dogfood loop -- the
automated gate agrees with the hand-run gate, or one of them is wrong.
"""

import json
import unittest
from pathlib import Path

import consolidate as C

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "session_2026-08-08.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestValueFunction(unittest.TestCase):
    def test_signals_normalize_to_unit_range(self):
        norm = C.normalize_signals({"acted_on": True, "cost_to_learn_min": 120,
                                    "references": 9, "contradicts": "x", "novelty": 2.0})
        for k, v in norm.items():
            self.assertGreaterEqual(v, 0.0, k)
            self.assertLessEqual(v, 1.0, k)
        self.assertEqual(norm["cost_to_learn"], 1.0)   # saturates at an hour
        self.assertEqual(norm["referenced"], 1.0)      # saturates at 3
        self.assertEqual(norm["contradiction"], 1.0)

    def test_monotonic_in_each_signal(self):
        base = {"acted_on": False, "cost_to_learn_min": 0, "references": 0,
                "contradicts": None, "novelty": 0.0}
        s0, _ = C.score_candidate(base)
        for field, bigger in [("acted_on", True), ("cost_to_learn_min", 60),
                              ("references", 3), ("contradicts", "y"), ("novelty", 1.0)]:
            up = dict(base); up[field] = bigger
            s1, _ = C.score_candidate(up)
            self.assertGreater(s1, s0, "raising %s must raise score" % field)

    def test_thresholds_bucket(self):
        self.assertEqual(C.decide(0.9), "PROMOTE")
        self.assertEqual(C.decide(0.45), "HOLD")
        self.assertEqual(C.decide(0.1), "DISCARD")


class TestProposal(unittest.TestCase):
    def test_reproduces_hand_triage(self):
        proposal = C.build_proposal(load_fixture(), bias_name="balanced")
        decisions = {c["id"]: c["decision"] for c in proposal["candidates"]}
        expected = {
            "editions_ground_truth": "PROMOTE",
            "synapse_doctrine": "PROMOTE",
            "ai_glossary": "PROMOTE",
            "frontal_mem_pointer": "PROMOTE",
            "frontal_memory_finding": "PROMOTE",
            "session_scaffolding": "DISCARD",
            "narrow_synapse_def": "DISCARD",
        }
        self.assertEqual(decisions, expected)
        self.assertEqual(proposal["counts"], {"PROMOTE": 5, "HOLD": 0, "DISCARD": 2})

    def test_superseded_is_discarded_regardless(self):
        ws = {"session": {}, "candidates": [{
            "id": "x", "class": "semantic", "summary": "high score but superseded",
            "superseded_by": "y",
            "signals": {"acted_on": True, "cost_to_learn_min": 60, "references": 3,
                        "contradicts": "z", "novelty": 1.0}}]}
        prop = C.build_proposal(ws)
        self.assertEqual(prop["candidates"][0]["decision"], "DISCARD")
        self.assertIn("superseded", prop["candidates"][0]["reason"])

    def test_contradiction_flags_reconsolidation(self):
        prop = C.build_proposal(load_fixture())
        syn = next(c for c in prop["candidates"] if c["id"] == "synapse_doctrine")
        self.assertTrue(syn["needs_reconsolidation"])

    def test_cost_asymmetry_bias_shifts_promotions(self):
        balanced = C.build_proposal(load_fixture(), bias_name="balanced")
        strict = C.build_proposal(load_fixture(), bias_name="small_trusted_store")
        # raising the bar (over-promotion is the graver sin) promotes fewer, never more
        self.assertLessEqual(strict["counts"]["PROMOTE"], balanced["counts"]["PROMOTE"])

    def test_dedupe_collapses_duplicates(self):
        ws = load_fixture()
        dupe = dict(ws["candidates"][0]); dupe["id"] = "editions_dupe"
        ws["candidates"].append(dupe)
        prop = C.build_proposal(ws)
        self.assertGreaterEqual(prop["duplicates_collapsed"], 1)


class TestConfirm(unittest.TestCase):
    def test_only_owner_approved_promotes_reach_manifest(self):
        proposal = C.build_proposal(load_fixture())
        decisions = {"editions_ground_truth": "approve", "synapse_doctrine": "reject",
                     "session_scaffolding": "approve"}  # approving a DISCARD must not write it
        manifest = C.confirm(proposal, decisions)
        ids = {i["id"] for i in manifest["to_write"]}
        self.assertEqual(ids, {"editions_ground_truth"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
