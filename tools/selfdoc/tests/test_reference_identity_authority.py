from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "selfdoc" / "validate_reference_identity_authority.py"
SPEC = importlib.util.spec_from_file_location("reference_identity_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ReferenceIdentityAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((REPO_ROOT / "selfdoc" / "reference_identity_authority_v1.json").read_text(encoding="utf-8"))

    def codes(self, data: dict) -> list[str]:
        return [row["code"] for row in VALIDATOR.validate_map(data, REPO_ROOT)]

    def test_current_map_and_evidence_pass(self) -> None:
        result = VALIDATOR.audit(REPO_ROOT / "selfdoc" / "reference_identity_authority_v1.json", REPO_ROOT)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(331, result["metrics"]["reference_identities"])
        self.assertEqual(65, result["metrics"]["function_candidates"])
        self.assertEqual(221, result["metrics"]["argument_candidates"])

    def test_duplicate_entity_fails(self) -> None:
        data = copy.deepcopy(self.data)
        data["entity_types"].append(copy.deepcopy(data["entity_types"][0]))
        self.assertIn("ENTITY_DUPLICATE", self.codes(data))

    def test_unknown_authority_fails(self) -> None:
        data = copy.deepcopy(self.data)
        data["field_rules"][0]["authority_order"] = ["AUTH-MISSING"]
        self.assertIn("FIELD_AUTHORITY", self.codes(data))

    def test_unknown_metadata_system_fails(self) -> None:
        data = copy.deepcopy(self.data)
        data["authority_sources"][0]["system_ids"] = ["META-999"]
        self.assertIn("SYSTEM_REFERENCE", self.codes(data))

    def test_mutation_gate_fails_closed(self) -> None:
        data = copy.deepcopy(self.data)
        data["mutation_authorized"] = True
        self.assertIn("MUTATION_GATE", self.codes(data))


if __name__ == "__main__":
    unittest.main()
