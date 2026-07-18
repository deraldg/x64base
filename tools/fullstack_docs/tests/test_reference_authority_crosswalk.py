from __future__ import annotations
import importlib.util, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/build_reference_authority_crosswalk.py"
DEVELOPMENT_CROSSWALK_INPUTS = (
    ROOT / "selfdoc/reference_identity_authority_v1.json",
    ROOT / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/reference_inventory/fullstack_reference_identity_inventory_v1.csv",
    ROOT / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/metacollect_phase/candidate_v1/SYSFUNC_IMPORT_candidate_v1.csv",
    ROOT / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/metacollect_phase/candidate_v1/SYSARGS_IMPORT_candidate_v1.csv",
)
SPEC = importlib.util.spec_from_file_location("crosswalk", PATH); assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class CrosswalkTests(unittest.TestCase):
    @unittest.skipUnless(
        all(path.exists() for path in DEVELOPMENT_CROSSWALK_INPUTS),
        "development authority and metacollect evidence are intentionally absent from the public projection",
    )
    def test_current_build_counts_and_unique_ids(self):
        rows, excluded, manifest = MOD.build(ROOT)
        self.assertEqual(593, len(rows)); self.assertEqual(24, len(excluded))
        self.assertEqual({"ARGUMENT": 221, "COMMAND": 307, "FUNCTION": 65}, manifest["entity_counts"])
        self.assertEqual([], manifest["duplicate_logical_ids"])
    def test_educational_topic_is_excluded(self):
        row = {"identity":"INTRO","classification":"EDUCATIONAL_TOPIC"}
        self.assertIsNone(MOD.command_row(row, "H", "C"))
    def test_argument_key_includes_kind(self):
        base={"OWNER_KND":"command","OWNER_NAM":"SET","ARG_KIND":"placeholder","ARG_NAME":"VALUE","ARG_ID":"ARG_SET_VALUE","SRC_AUTH":"usage_contract_v1","SRC_FILE":"x","REQUIRED":"true","REPEAT":"false","VAL_SHAPE":"value"}
        first=MOD.argument_row(base,"H","C"); base["ARG_KIND"]="keyword"; second=MOD.argument_row(base,"H","C")
        self.assertNotEqual(first["logical_id"],second["logical_id"]); self.assertEqual(first["legacy_id"],second["legacy_id"])
    def test_command_key_preserves_canonical_space(self):
        row={"identity":"SET ORDER","classification":"ALIGNED_COMMAND","in_static_registry":"True","in_usage_contract":"True","in_dotref":"True","in_foxref":"False","in_edref":"False","dotref_evidence":"d","foxref_evidence":"","edref_evidence":"","registry_evidence":"r","usage_evidence":"u"}
        self.assertEqual("CMD:SET ORDER",MOD.command_row(row,"H","C")["logical_id"])

if __name__ == "__main__": unittest.main()
