from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "selfdoc" / "validate_metadata_system_registry.py"
SPEC = importlib.util.spec_from_file_location("metadata_registry_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class MetadataSystemRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        registry_path = REPO_ROOT / "selfdoc" / "metadata_system_registry_v1.json"
        cls.registry = json.loads(registry_path.read_text(encoding="utf-8"))

    def codes(self, registry: dict) -> list[str]:
        return [row["code"] for row in VALIDATOR.validate_registry(registry, REPO_ROOT)]

    def test_current_registry_has_no_structural_findings(self) -> None:
        findings = VALIDATOR.validate_registry(self.registry, REPO_ROOT)
        structural = [row for row in findings if row["code"] != "ENTRYPOINT_HASH"]
        self.assertEqual([], structural)

    def test_guarded_harvest_system_passes_scoped_freshness(self) -> None:
        self.assertEqual(
            [],
            VALIDATOR.validate_registry(self.registry, REPO_ROOT, {"META-025"}),
        )

    def test_unknown_scoped_system_fails(self) -> None:
        self.assertIn(
            "SYSTEM_SELECTION",
            self.codes_for_scope(self.registry, {"META-999"}),
        )

    def codes_for_scope(self, registry: dict, system_ids: set[str]) -> list[str]:
        return [
            row["code"]
            for row in VALIDATOR.validate_registry(registry, REPO_ROOT, system_ids)
        ]

    def test_duplicate_id_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["systems"][1]["system_id"] = data["systems"][0]["system_id"]
        self.assertIn("SYSTEM_ID_DUPLICATE", self.codes(data))

    def test_missing_entrypoint_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["systems"][0]["canonical_entrypoints"][0] = "missing/collector.py"
        self.assertIn("ENTRYPOINT_MISSING", self.codes(data))

    def test_protected_mutator_cannot_be_default(self) -> None:
        data = copy.deepcopy(self.registry)
        row = next(system for system in data["systems"] if system["mutation_class"] == "PROTECTED_HELP_MUTATOR")
        row["execution_default_allowed"] = True
        self.assertIn("DEFAULT_EXECUTION", self.codes(data))

    def test_primary_hash_drift_fails(self) -> None:
        data = copy.deepcopy(self.registry)
        data["systems"][0]["source_sha256"] = "0" * 64
        self.assertIn("ENTRYPOINT_HASH", self.codes(data))

    def test_malformed_hash_fails_even_outside_freshness_scope(self) -> None:
        data = copy.deepcopy(self.registry)
        data["systems"][0]["source_sha256"] = "not-a-hash"
        self.assertIn("SOURCE_SHA256", self.codes_for_scope(data, {"META-025"}))


if __name__ == "__main__":
    unittest.main()
