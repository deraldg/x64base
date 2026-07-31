from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "build_current_work_feed.py"
SPEC = importlib.util.spec_from_file_location("build_current_work_feed", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixtures() -> tuple[dict, dict]:
    projects = {
        "projects": [
            {"id": "project.one", "name": "One", "kind": "runtime", "status": "active"}
        ]
    }
    tasks = {
        "schema": "labtalk.ai_portal.tasks.v1",
        "as_of_date": "2026-07-23",
        "authority": {
            "system_of_record": "portal",
            "pseudo_chat_role": "return lane",
            "publication_rule": "reports only",
        },
        "current_documentation_flush": {
            "run_id": "RUN-1",
            "ticket": "AIF-1",
            "state": "review",
            "publication_state": "local",
            "maintenance_class": "maintained_current",
            "source_contracts": 1,
            "help_topics": 2,
            "help_lines": 3,
            "command_reference_pages": 4,
            "command_lineage_rows": 5,
            "manual_parts": 6,
            "manual_lines": 7,
            "manual_pdf_pages": 8,
            "website_static_pages": 9,
            "next_gate": "review",
        },
        "tasks": [
            {
                "id": "task.one",
                "title": "Task One",
                "ticket": "AIF-1",
                "kind": "docs",
                "project_ids": ["project.one"],
                "channel": "ai_portal",
                "status": "active",
                "owner": "Derald",
                "updated_on": "2026-07-23",
                "truth_state": "grounded",
                "proof_state": "pass",
                "next_gate": "review",
                "summary": "summary",
                "website_paths": ["/docs/one"],
            }
        ],
    }
    return projects, tasks


class CurrentWorkFeedTests(unittest.TestCase):
    def test_public_projection_omits_local_roots(self) -> None:
        projects, tasks = fixtures()
        projects["projects"][0]["root"] = "D:/private"
        MODULE.validate(projects, tasks)
        feed = MODULE.public_projection(projects, tasks)
        encoded = json.dumps(feed)
        self.assertNotIn("D:/private", encoded)
        self.assertEqual(feed["summary"]["tasks"], 1)
        self.assertEqual(feed["summary"]["task_statuses"], {"active": 1})

    def test_unknown_project_fails_closed(self) -> None:
        projects, tasks = fixtures()
        tasks["tasks"][0]["project_ids"] = ["project.missing"]
        with self.assertRaisesRegex(ValueError, "unknown projects"):
            MODULE.validate(projects, tasks)

    def test_render_contains_status_next_gate_and_public_link(self) -> None:
        projects, tasks = fixtures()
        MODULE.validate(projects, tasks)
        text = MODULE.render_mdx(MODULE.public_projection(projects, tasks))
        self.assertIn("Current Tasks & Projects", text)
        self.assertIn("`active`", text)
        self.assertIn("review", text)
        self.assertIn("[open](/docs/one)", text)


if __name__ == "__main__":
    unittest.main()
