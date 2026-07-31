from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools/selfdoc/validate_documentation_lineages.py"
SPEC = importlib.util.spec_from_file_location("documentation_lineage_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class DocumentationLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = json.loads((REPO_ROOT / "selfdoc/source_contract_probe_lineage_v1.json").read_text(encoding="utf-8"))
        cls.messaging = json.loads((REPO_ROOT / "selfdoc/messaging_exporter_lineage_v1.json").read_text(encoding="utf-8"))

    def codes(self, source: dict, messaging: dict) -> list[str]:
        return [row["code"] for row in VALIDATOR.validate_lineages(REPO_ROOT, source, messaging)]

    def test_current_lineages_pass(self) -> None:
        self.assertEqual([], VALIDATOR.validate_lineages(REPO_ROOT, self.source, self.messaging))

    def test_source_role_path_must_exist(self) -> None:
        source = copy.deepcopy(self.source)
        source["current_role_split"]["snapshot"] = "missing/snapshot.py"
        self.assertIn("ROLE_PATH", self.codes(source, self.messaging))

    def test_message_hash_drift_fails(self) -> None:
        messaging = copy.deepcopy(self.messaging)
        messaging["canonical_exporter"]["sha256"] = "0" * 64
        self.assertIn("PATH_HASH", self.codes(self.source, messaging))

    def test_historical_exporter_cannot_be_default(self) -> None:
        messaging = copy.deepcopy(self.messaging)
        messaging["historical_exporter"]["execution_default_allowed"] = True
        self.assertIn("HISTORICAL_GATE", self.codes(self.source, messaging))


if __name__ == "__main__":
    unittest.main()
