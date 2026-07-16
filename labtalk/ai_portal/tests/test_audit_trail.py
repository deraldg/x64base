from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal.audit_trail import audit_closeouts  # noqa: E402


REQUIRED_FIELDS = [
    "ai_report_audit.schema",
    "ai_report_audit.report_id",
    "ai_report_audit.recorded_at_utc",
    "ai_report_audit.agent.provider",
    "ai_report_audit.agent.product",
    "ai_report_audit.agent.model",
    "ai_report_audit.agent.access_mode",
    "ai_report_audit.session.id",
    "ai_report_audit.session.chat_reference",
    "ai_report_audit.project.id",
    "ai_report_audit.project.root",
    "ai_report_audit.git.branch",
    "ai_report_audit.git.baseline_commit",
    "ai_report_audit.authorization.requested_by",
    "ai_report_audit.authorization.scope",
    "ai_report_audit.report.path",
    "ai_report_audit.report.kind",
]


class AuditTrailTests(unittest.TestCase):
    def make_repo(self, grandfathered: list[str] | None = None) -> tuple[Path, Path, tempfile.TemporaryDirectory[str]]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "docs" / "maintenance").mkdir(parents=True)
        (root / "labtalk" / "registries").mkdir(parents=True)
        (root / "labtalk" / "registries" / "projects.yaml").write_text(
            "projects:\n  - id: project.test\n    root: .\n",
            encoding="utf-8",
        )
        grandfather_lines = "\n".join(f"    - {entry}" for entry in (grandfathered or []))
        policy = root / "labtalk" / "registries" / "ai_report_audit.yaml"
        policy.write_text(
            textwrap.dedent(
                f"""
                report_audit:
                  schema: ai-report-audit-v1
                  status: active_mandatory
                  closeout_glob: docs/maintenance/SESSION_CLOSEOUT_*.md
                  template: docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md
                  project_registry: labtalk/registries/projects.yaml
                  required_fields:
                """
            ).lstrip()
            + "\n".join(f"    - {field}" for field in REQUIRED_FIELDS)
            + "\n  allowed_access_modes: [local_write, hosted_proposal]\n"
            + "  grandfathered_closeouts:\n"
            + (grandfather_lines or "    []")
            + "\n",
            encoding="utf-8",
        )
        return root, policy, temp

    def valid_closeout(self, path: str, report_id: str = "AIPR-TEST-001") -> str:
        return textwrap.dedent(
            f"""\
            ---
            ai_report_audit:
              schema: ai-report-audit-v1
              report_id: {report_id}
              recorded_at_utc: 2026-07-16T00:00:00Z
              agent:
                provider: OpenAI
                product: Codex
                model: not_exposed
                access_mode: local_write
              session:
                id: task-123
                chat_reference: codex-task:task-123
              project:
                id: project.test
                root: .
              git:
                branch: test
                baseline_commit: 0123456789abcdef
              authorization:
                requested_by: maintainer
                scope: test the audit contract
              report:
                path: {path}
                kind: session_closeout
            ---
            # Session Closeout
            """
        )

    def test_valid_envelope_passes(self) -> None:
        root, policy, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        report = "docs/maintenance/SESSION_CLOSEOUT_VALID_2026-07-16.md"
        (root / report).write_text(self.valid_closeout(report), encoding="utf-8")

        audit = audit_closeouts(root, policy)

        self.assertEqual(audit["finding_count"], 0)
        self.assertEqual(audit["valid_count"], 1)

    def test_missing_agent_identity_is_reported(self) -> None:
        root, policy, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        report = "docs/maintenance/SESSION_CLOSEOUT_MISSING_2026-07-16.md"
        text = self.valid_closeout(report).replace("    provider: OpenAI\n", "")
        (root / report).write_text(text, encoding="utf-8")

        audit = audit_closeouts(root, policy)

        fields = {finding["field"] for finding in audit["findings"]}
        self.assertIn("ai_report_audit.agent.provider", fields)

    def test_unknown_project_and_wrong_report_path_are_reported(self) -> None:
        root, policy, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        report = "docs/maintenance/SESSION_CLOSEOUT_WRONG_2026-07-16.md"
        text = self.valid_closeout("docs/maintenance/OTHER.md").replace(
            "id: project.test", "id: project.unknown"
        )
        (root / report).write_text(text, encoding="utf-8")

        audit = audit_closeouts(root, policy)

        fields = {finding["field"] for finding in audit["findings"]}
        self.assertIn("ai_report_audit.project.id", fields)
        self.assertIn("ai_report_audit.report.path", fields)

    def test_grandfathered_closeout_does_not_need_front_matter(self) -> None:
        report = "docs/maintenance/SESSION_CLOSEOUT_LEGACY_2026-07-15.md"
        root, policy, temp = self.make_repo([report])
        self.addCleanup(temp.cleanup)
        (root / report).write_text("# Legacy closeout\n", encoding="utf-8")

        audit = audit_closeouts(root, policy)

        self.assertEqual(audit["finding_count"], 0)
        self.assertEqual(audit["grandfathered_count"], 1)

    def test_duplicate_report_id_is_reported(self) -> None:
        root, policy, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        first = "docs/maintenance/SESSION_CLOSEOUT_FIRST_2026-07-16.md"
        second = "docs/maintenance/SESSION_CLOSEOUT_SECOND_2026-07-16.md"
        (root / first).write_text(self.valid_closeout(first, "AIPR-DUP"), encoding="utf-8")
        (root / second).write_text(self.valid_closeout(second, "AIPR-DUP"), encoding="utf-8")

        audit = audit_closeouts(root, policy)

        self.assertTrue(any("duplicate report id" in finding["issue"] for finding in audit["findings"]))
        self.assertEqual(audit["valid_count"], 1)

    def test_wrong_report_kind_is_reported(self) -> None:
        root, policy, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        report = "docs/maintenance/SESSION_CLOSEOUT_KIND_2026-07-16.md"
        text = self.valid_closeout(report).replace(
            "kind: session_closeout", "kind: portal_truth_audit"
        )
        (root / report).write_text(text, encoding="utf-8")

        audit = audit_closeouts(root, policy)

        fields = {finding["field"] for finding in audit["findings"]}
        self.assertIn("ai_report_audit.report.kind", fields)


if __name__ == "__main__":
    unittest.main()
