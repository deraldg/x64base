"""Every recall trigger must resolve to a real, non-thin working set.

WHY THIS EXISTS (AIF-118, 2026-08-16)
    AIF-115 measured that the Tier 1 seed's "Going deeper" table and this
    resolver had diverged in BOTH directions, and made demotion of the table
    conditional on a precondition stated in prose:

        "if the resolver is thin then demoting its fallback makes Tier 1 worse
         -- VERIFY BEFORE DEMOTING."

    A precondition nobody can run is a wish. This is that precondition as a
    query. The seed's 8192 B ceiling is the forcing function for demotion, and
    demotion is only safe while every trigger still answers -- so this test is
    what stands between "the table moved" and "the guidance vanished".

    It is deliberately CHEAP and STRUCTURAL. It does not grade whether prose
    teaches well; that is a human judgement and this will not pretend otherwise.
    It asserts only what is mechanically knowable and what actually went wrong
    before: a trigger with no nodes, a node pointing at a file that is not there,
    and a section that resolves to almost nothing.

THE THIN-SECTION ARM IS NOT HYPOTHETICAL. On 2026-08-16 `section_size` counted a
`#` comment inside a fenced code block as the next heading and reported **64 B
for a 3516 B section**. Nothing complained, because a small working set is the
output this tool exists to produce. That is why "thin" is a FAILURE here rather
than a nice-to-have: the failure mode of retrieval is silence, not error.

PROVEN TO FAIL (three mutations of the graph, each reverted after):
    point a node at a missing file   -> "missing path docs/NOPE_DELETED.md"
    delete a trigger's fires_at edge -> "NO NODES"
    anchor a node mid-code-fence     -> "thin total 441 B"
"""

from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
GRAPH = REPO_ROOT / "labtalk" / "registries" / "portal_recall_graph.yaml"
RECALL = REPO_ROOT / "labtalk" / "ai_portal" / "recall.py"

SPEC = importlib.util.spec_from_file_location("recall", RECALL)
recall = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recall)

# A single node under this is almost certainly a truncation, not brevity.
MIN_NODE_BYTES = 300
# A whole trigger under this cannot restore competence for anything.
MIN_TRIGGER_BYTES = 500


def load():
    graph = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    fires = {}
    for edge in graph["edges"]:
        if edge.get("type") == "fires_at":
            fires.setdefault(edge["from"], []).append(edge["to"])
    return graph, nodes, fires


class RecallCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph, cls.nodes, cls.fires = load()

    def test_every_trigger_fires_at_something(self):
        for trig in self.graph["triggers"]:
            with self.subTest(trigger=trig["id"]):
                self.assertTrue(
                    self.fires.get(trig["id"]),
                    f"{trig['id']} resolves to NOTHING -- an agent asking for this "
                    "guidance gets an empty answer, and any seed row it backs "
                    "cannot be demoted",
                )

    def test_every_referenced_node_exists_on_disk(self):
        for trig_id, node_ids in self.fires.items():
            for node_id in node_ids:
                with self.subTest(trigger=trig_id, node=node_id):
                    node = self.nodes.get(node_id)
                    self.assertIsNotNone(node, f"dangling node id {node_id}")
                    path = REPO_ROOT / str(node.get("path", ""))
                    self.assertTrue(
                        path.is_file(),
                        f"{trig_id} -> {node_id} points at {node.get('path')}, "
                        "which is not on disk",
                    )

    def test_every_referenced_node_is_TRACKED_not_merely_present(self):
        """On disk is not the same as in the repository.

        ADDED 2026-08-16 after this suite passed in the working tree and FAILED
        against a fresh checkout of the same commit. Three nodes pointed at
        `docs/manuals/developer/dev/dev-0*.md`, which exist on the maintainer's
        disk and are in no commit -- 21 of the 22 files in that directory are
        untracked and none are gitignored. Every clone would have resolved
        `read_write_dbf` to nothing while this test reported green.

        That is the lane's own defect shape inside the gate written to detect
        it: a check whose subject was the author's filesystem rather than the
        artifact that ships. Same family as launch-common.ps1 (ten tracked
        scripts dot-sourcing an untracked file) and the SYSFUNC metadata tables.
        """
        try:
            tracked = set(
                subprocess.run(
                    ["git", "--no-optional-locks", "ls-files"],
                    cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
                    check=True,
                ).stdout.splitlines()
            )
        except (OSError, subprocess.SubprocessError):
            self.skipTest("git unavailable; cannot distinguish tracked from present")

        for trig_id, node_ids in self.fires.items():
            for node_id in node_ids:
                node = self.nodes.get(node_id)
                if not node:
                    continue
                rel = str(node.get("path", "")).replace("\\", "/")
                with self.subTest(trigger=trig_id, node=node_id):
                    self.assertIn(
                        rel, tracked,
                        f"{trig_id} -> {node_id} points at {rel}, which is NOT "
                        "tracked. It resolves on this machine and to nothing in "
                        "a clone, so Tier 1 retrieval would silently return an "
                        "empty working set for everyone else.",
                    )

    def test_no_node_resolves_to_a_truncated_section(self):
        for trig_id, node_ids in self.fires.items():
            for node_id in node_ids:
                node = self.nodes.get(node_id)
                if not node:
                    continue
                path = REPO_ROOT / str(node.get("path", ""))
                if not path.is_file():
                    continue
                with self.subTest(node=node_id):
                    size = recall.section_size(REPO_ROOT, node)
                    self.assertGreaterEqual(
                        size, MIN_NODE_BYTES,
                        f"{node_id} resolves to {size} B. Either the anchor is "
                        "wrong or section_size is truncating again (it once "
                        "reported 64 B for a 3516 B section).",
                    )

    def test_no_trigger_is_thin_overall(self):
        for trig in self.graph["triggers"]:
            node_ids = self.fires.get(trig["id"], [])
            total = sum(
                recall.section_size(REPO_ROOT, self.nodes[n])
                for n in node_ids
                if n in self.nodes
                and (REPO_ROOT / str(self.nodes[n].get("path", ""))).is_file()
            )
            with self.subTest(trigger=trig["id"]):
                self.assertGreaterEqual(
                    total, MIN_TRIGGER_BYTES,
                    f"{trig['id']} resolves to {total} B in total -- too little "
                    "to restore competence, so its seed row must NOT be demoted",
                )

    def test_the_graph_still_validates(self):
        # Cheap belt-and-braces: recall's own integrity check, so a coverage
        # pass cannot be read as an all-clear while edges dangle.
        graph, nodes, fires = load()
        node_ids = set(nodes)
        trigger_ids = {t["id"] for t in graph["triggers"]}
        for edge in graph["edges"]:
            with self.subTest(edge=f"{edge['from']}->{edge['to']}"):
                self.assertIn(edge["from"], node_ids | trigger_ids)
                self.assertIn(edge["to"], node_ids | trigger_ids)


if __name__ == "__main__":
    unittest.main()
