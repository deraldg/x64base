from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/validate_website_feed_packet.py"
SPEC = importlib.util.spec_from_file_location("validate_website_feed_packet", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class WebsiteFeedValidatorTests(unittest.TestCase):
    def test_current_route_contract_has_no_findings(self) -> None:
        commit = "a" * 40
        rows = []
        actions = ["CREATE"] * 2 + ["UPDATE"] * 8 + ["REPLACE"]
        labels = ["manual-reviewed", "generated-reviewed", "help-catalog-evidenced"]
        for index, action in enumerate(actions):
            rows.append(
                {
                    "action": action,
                    "site_path": f"content/path-{index}.mdx",
                    "route": f"/route-{index}",
                    "proof_label": labels[index % len(labels)],
                    "gate7_mutation_authorized": "0",
                    "public_source_url": f"https://github.com/deraldg/x64base/blob/{commit}/source-{index}",
                }
            )
        self.assertEqual([], MOD.validate_route_rows(rows, commit))

    def test_absolute_local_site_path_fails(self) -> None:
        row = {
            "action": "REPLACE",
            "site_path": "D:\\dev\\file.mdx",
            "route": "/route",
            "proof_label": "manual-reviewed",
            "gate7_mutation_authorized": "0",
            "public_source_url": "https://github.com/deraldg/x64base/blob/x/source",
        }
        findings = MOD.validate_route_rows([row], "x")
        self.assertTrue(any("SITE_PATH_NOT_REPOSITORY_RELATIVE" in item for item in findings))

    def test_gate7_authority_must_be_zero(self) -> None:
        row = {
            "action": "REPLACE",
            "site_path": "file.mdx",
            "route": "/route",
            "proof_label": "manual-reviewed",
            "gate7_mutation_authorized": "1",
            "public_source_url": "https://github.com/deraldg/x64base/blob/x/source",
        }
        findings = MOD.validate_route_rows([row], "x")
        self.assertTrue(any("GATE7_AUTHORITY_NOT_ZERO" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
