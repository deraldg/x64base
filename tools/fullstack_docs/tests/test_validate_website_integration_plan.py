import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.fullstack_docs.validate_website_integration_plan import (
    _status_paths,
    validate_plan,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class WebsiteIntegrationPlanTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> dict:
        operations = []
        for sequence in range(1, 12):
            action = "CREATE" if sequence >= 10 else ("REPLACE" if sequence == 1 else "UPDATE")
            path = f"content/target-{sequence}.mdx"
            before = "ABSENT"
            if action != "CREATE":
                data = f"before-{sequence}".encode()
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                before = digest(data)
            operations.append(
                {
                    "sequence": sequence,
                    "action": action,
                    "route": f"/route-{sequence}",
                    "site_path": path,
                    "before_sha256": before,
                    "proof_label": "manual-reviewed",
                    "content_contract": ["bounded change"],
                }
            )
        return {
            "schema": "dottalk.website.integration_plan.v1",
            "status": "PLAN_READY_MUTATION_NOT_AUTHORIZED",
            "website": {
                "branch": "codex/lean-sites-publish",
                "baseline_commit": "abc123",
                "build_command": "npm run build",
            },
            "authorization": {
                "website_mutation_authorized": False,
                "website_build_authorized": False,
                "website_commit_authorized": False,
                "website_push_authorized": False,
                "website_deployment_authorized": False,
            },
            "operations": operations,
            "holds": [
                "No website commit in Gate 7.",
                "No metacollect work.",
                "No dependency change.",
            ],
        }

    def run_validation(self, plan: dict, root: Path) -> list[str]:
        return validate_plan(
            plan,
            root,
            observed_branch="codex/lean-sites-publish",
            observed_head="abc123",
            observed_status="",
        )

    def test_valid_plan_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual([], self.run_validation(self.make_fixture(root), root))

    def test_hash_drift_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = self.make_fixture(root)
            (root / plan["operations"][0]["site_path"]).write_text("drift", encoding="utf-8")
            self.assertTrue(any("before hash drift" in item for item in self.run_validation(plan, root)))

    def test_enabled_authority_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = self.make_fixture(root)
            plan["authorization"]["website_mutation_authorized"] = True
            self.assertTrue(any("authorization flags" in item for item in self.run_validation(plan, root)))

    def test_duplicate_route_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = self.make_fixture(root)
            plan["operations"][1]["route"] = plan["operations"][0]["route"]
            self.assertTrue(any("duplicate route" in item for item in self.run_validation(plan, root)))

    def test_status_path_parser_handles_modified_and_untracked(self):
        status = " M content/existing.mdx\n?? content/new.mdx\n"
        self.assertEqual(
            {"content/existing.mdx", "content/new.mdx"},
            _status_paths(status),
        )

    def test_status_path_parser_handles_trimmed_first_row(self):
        self.assertEqual(
            {"app/downloads/page.tsx"},
            _status_paths("M app/downloads/page.tsx"),
        )


if __name__ == "__main__":
    unittest.main()
