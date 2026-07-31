from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "selfdoc" / "validate_source_contract_vocabulary.py"
SPEC = importlib.util.spec_from_file_location("source_contract_vocabulary_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SourceContractVocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = REPO_ROOT / "selfdoc" / "source_contract_vocabulary_v1.json"
        cls.registry = json.loads(path.read_text(encoding="utf-8"))

    def codes(self, data: dict) -> list[str]:
        return [row["code"] for row in VALIDATOR.validate_registry(data, REPO_ROOT)]

    def test_current_registry_passes(self) -> None:
        self.assertEqual([], VALIDATOR.validate_registry(self.registry, REPO_ROOT))

    def test_removed_field_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["extension_fields"].pop()
        self.assertIn("VOCABULARY_DRIFT", self.codes(data))

    def test_bad_alias_target_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["alias_map"]["writes_file"] = "unknown_field"
        self.assertIn("ALIAS_TARGET", self.codes(data))

    def test_mutation_gate_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["mutation_authorized"] = True
        self.assertIn("SAFETY_GATE", self.codes(data))


if __name__ == "__main__":
    unittest.main()
