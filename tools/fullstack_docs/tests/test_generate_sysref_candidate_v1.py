from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/generate_sysref_candidate_v1.py"
SPEC = importlib.util.spec_from_file_location("generate_sysref_candidate_v1", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.metadata = root / "inputs"
        self.schema = root / "dottalkpp/data/schemas/metadata/sysref_catalog.dtschema"
        self.schema.parent.mkdir(parents=True)
        self.schema.write_text("SCHEMA_ID: SYSREF_CATALOG_V1\n", encoding="utf-8")
        self.syscmd = self.metadata / "syscmd.csv"
        self.sysargs = self.metadata / "sysargs.csv"
        self.srcusage = self.metadata / "srcusage.csv"
        self.refvoice = self.metadata / "refvoice.csv"
        self.syssubcmd = self.metadata / "syssubcmd.csv"
        self.manifest = root / "manifest.json"
        self.harvest_run = "HARVEST-TEST-001"
        self.write_sources()
        self.write_manifest()

    def write_sources(self, voice_rows: list[dict[str, str]] | None = None) -> None:
        write_csv(
            self.syscmd,
            ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"],
            [
                {"CMD_ID": "CMD_BAR", "CAN_NAME": "BAR", "TYPE": "command", "VIS": "public", "HANDLER": "cmd_BAR", "ACTIVE": "T"},
                {"CMD_ID": "CMD_FOO", "CAN_NAME": "FOO", "TYPE": "command", "VIS": "public", "HANDLER": "cmd_FOO", "ACTIVE": "T"},
            ],
        )
        write_csv(
            self.sysargs,
            ["OWNER_NAM", "ARG_KIND", "ARG_NAME", "ACTIVE", "SRC_AUTH", "SRC_FILE"],
            [{"OWNER_NAM": "FOO", "ARG_KIND": "placeholder", "ARG_NAME": "VALUE", "ACTIVE": "T", "SRC_AUTH": "usage_contract_v1", "SRC_FILE": "src/cli/cmd_foo.cpp"}],
        )
        write_csv(
            self.srcusage,
            ["COMMAND", "STATUS", "SUMMARY", "USAGE", "EXAMPLES", "NOTES", "RELATED", "SRC_FILE"],
            [
                {"COMMAND": "BAR", "STATUS": "experimental", "SUMMARY": "Bar remains implemented but unsupported.", "USAGE": "BAR <value>", "EXAMPLES": "", "NOTES": "", "RELATED": "FOO", "SRC_FILE": "src/cli/cmd_bar.cpp"},
                {"COMMAND": "FOO", "STATUS": "supported", "SUMMARY": "Foo summary.", "USAGE": "FOO <value>\nFOO STATUS", "EXAMPLES": "FOO 1", "NOTES": "A note.", "RELATED": "BAR", "SRC_FILE": "src/cli/cmd_foo.cpp"},
            ],
        )
        fields = [
            "OVR_ID", "NAMESPACE", "ENT_KIND", "CAN_NAME", "LOCALE_ID", "VOICE",
            "KIND", "ORDINAL", "TEXT", "RATIONALE", "OWNER", "RULING_ID",
            "REVIEW_ST", "SRC_HASH", "ACTIVE", "VER_AT",
        ]
        write_csv(self.refvoice, fields, voice_rows or [])
        write_csv(
            self.syssubcmd,
            [
                "QUAL_NAME", "IMPL_STAT", "VIS_TIER", "SRC_AUTH", "SRC_FILE",
                "HANDLER", "ACTIVE", "NOTES",
            ],
            [],
        )

    def write_manifest(self, overrides: dict[str, dict[str, str]] | None = None) -> None:
        overrides = overrides or {}
        paths = {
            "SYSCMD": self.syscmd,
            "SYSARGS": self.sysargs,
            "SRCUSAGE": self.srcusage,
            "REFVOICE": self.refvoice,
            "SYSSUBCMD": self.syssubcmd,
        }
        inputs = []
        for role, path in paths.items():
            item = {
                "role": role,
                "path": path.relative_to(self.root).as_posix(),
                "sha256": MOD.sha256_file(path),
                "producer_run_id": "CANONICAL" if role == "REFVOICE" else self.harvest_run,
            }
            item.update(overrides.get(role, {}))
            inputs.append(item)
        payload = {
            "schema": MOD.MANIFEST_SCHEMA,
            "harvest_run_id": self.harvest_run,
            "repo_sha": "1" * 40,
            "created_utc": "2026-10-13T12:00:00Z",
            "created_by": "member.ai.codex",
            "collector": {"id": "fixture-collector-v1", "sha256": "A" * 64},
            "inputs": inputs,
        }
        self.manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def args(self, out: Path) -> list[str]:
        return [
            "--root", str(self.root),
            "--run-id", "DOTREF-M3B-TEST-001",
            "--harvest-manifest", str(self.manifest),
            "--voice-catalog", str(self.refvoice),
            "--namespace", "DOT",
            "--out", str(out),
            "--report-only",
        ]


class SysRefCandidateTests(unittest.TestCase):
    def test_report_only_candidate_is_deterministic_and_support_is_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            out_a = fixture.root / "out-a"
            out_b = fixture.root / "out-b"
            self.assertEqual(0, MOD.main(fixture.args(out_a)))
            self.assertEqual(0, MOD.main(fixture.args(out_b)))

            files_a = sorted(path.relative_to(out_a) for path in out_a.rglob("*") if path.is_file())
            files_b = sorted(path.relative_to(out_b) for path in out_b.rglob("*") if path.is_file())
            self.assertEqual(files_a, files_b)
            for rel in files_a:
                self.assertEqual((out_a / rel).read_bytes(), (out_b / rel).read_bytes(), rel)
                self.assertNotIn((out_a / rel).suffix.lower(), MOD.FORBIDDEN_SUFFIXES)

            with (out_a / "candidate/sysref_candidate.csv").open(encoding="utf-8", newline="") as handle:
                rows = {row["CAN_NAME"]: row for row in csv.DictReader(handle)}
            self.assertEqual("T", rows["BAR"]["IMPLEMENT"])
            self.assertEqual("F", rows["BAR"]["SUPPORTED"])
            self.assertEqual("T", rows["FOO"]["IMPLEMENT"])
            self.assertEqual("T", rows["FOO"]["SUPPORTED"])

    def test_hash_mismatch_fails_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.write_manifest({"SYSCMD": {"sha256": "0" * 64}})
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            self.assertFalse(out.exists())

    def test_mixed_harvest_run_fails_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.write_manifest({"SYSARGS": {"producer_run_id": "OTHER-RUN"}})
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            self.assertFalse(out.exists())

    def test_stale_approved_override_blocks_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.write_sources([{
                "OVR_ID": "OVR_FOO_SUMMARY",
                "NAMESPACE": "DOT",
                "ENT_KIND": "COMMAND",
                "CAN_NAME": "FOO",
                "LOCALE_ID": "en-US",
                "VOICE": "NATIVE",
                "KIND": "SUMMARY",
                "ORDINAL": "1",
                "TEXT": "Reviewed Foo summary.",
                "RATIONALE": "Native wording.",
                "OWNER": "member.derald",
                "RULING_ID": "R-TEST",
                "REVIEW_ST": "APPROVED",
                "SRC_HASH": "0" * 64,
                "ACTIVE": "T",
                "VER_AT": "2026-10-13T12:00:00Z",
            }])
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            report = json.loads((out / "reports/authority_join_report.json").read_text(encoding="utf-8"))
            self.assertEqual("BLOCKED", report["status"])
            self.assertIn("REFVOICE_SOURCE_STALE", {item["code"] for item in report["diagnostics"]})

    def test_current_approved_override_is_applied_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.write_sources([{
                "OVR_ID": "OVR_FOO_SUMMARY",
                "NAMESPACE": "DOT",
                "ENT_KIND": "COMMAND",
                "CAN_NAME": "FOO",
                "LOCALE_ID": "en-US",
                "VOICE": "NATIVE",
                "KIND": "SUMMARY",
                "ORDINAL": "1",
                "TEXT": "Reviewed Foo summary.",
                "RATIONALE": "Native wording.",
                "OWNER": "member.derald",
                "RULING_ID": "R-TEST",
                "REVIEW_ST": "APPROVED",
                "SRC_HASH": MOD.sha256_bytes(b"Foo summary."),
                "ACTIVE": "T",
                "VER_AT": "2026-10-13T12:00:00Z",
            }])
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "candidate/sysrefline_candidate.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            row = next(item for item in rows if item["KIND"] == "SUMMARY" and item["OVERRIDE"] == "T")
            self.assertEqual("Reviewed Foo summary.", row["TEXT"])
            self.assertEqual("REFVOICE", row["SRC_AUTH"])
            self.assertEqual("APPROVED_OVERRIDE", row["REVIEW_ST"])

    def test_missing_usage_contract_is_explicit_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            write_csv(
                fixture.srcusage,
                ["COMMAND", "STATUS", "SUMMARY", "USAGE", "EXAMPLES", "NOTES", "RELATED", "SRC_FILE"],
                [{"COMMAND": "FOO", "STATUS": "supported", "SUMMARY": "Foo summary.", "USAGE": "FOO", "EXAMPLES": "", "NOTES": "", "RELATED": "", "SRC_FILE": "src/cli/cmd_foo.cpp"}],
            )
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            with (out / "reports/dispositions.csv").open(encoding="utf-8", newline="") as handle:
                dispositions = list(csv.DictReader(handle))
            self.assertTrue(any(row["CAN_NAME"] == "BAR" and row["CLASSIFICATION"] == "IMPLEMENTED_MISSING_USAGE" for row in dispositions))

    def test_auxiliary_contract_does_not_conflict_with_command_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            with fixture.srcusage.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows.append({
                "COMMAND": "FOO",
                "STATUS": "implementation-helper",
                "SUMMARY": "Helper implementation for FOO.",
                "USAGE": "This file does not export a command.",
                "EXAMPLES": "",
                "NOTES": "",
                "RELATED": "",
                "SRC_FILE": "src/cli/cmd_foo_helper.cpp",
            })
            write_csv(fixture.srcusage, list(rows[0]), rows)
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "reports/dispositions.csv").open(encoding="utf-8", newline="") as handle:
                dispositions = list(csv.DictReader(handle))
            self.assertTrue(any(
                row["CAN_NAME"] == "FOO"
                and row["CLASSIFICATION"] == "AUXILIARY_USAGE_IGNORED"
                and row["BLOCKING"] == "F"
                for row in dispositions
            ))

    def test_two_command_surface_contracts_still_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            with fixture.srcusage.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            duplicate = dict(rows[-1])
            duplicate["SRC_FILE"] = "src/cli/cmd_foo_second.cpp"
            rows.append(duplicate)
            write_csv(fixture.srcusage, list(rows[0]), rows)
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            report = json.loads((out / "reports/authority_join_report.json").read_text(encoding="utf-8"))
            self.assertIn("SRCUSAGE_DUPLICATE_COMMAND", {item["code"] for item in report["diagnostics"]})

    def test_unregistered_experimental_contract_is_disposition_not_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            with fixture.srcusage.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows.append({
                "COMMAND": "PLANNED",
                "STATUS": "experimental",
                "SUMMARY": "Planned surface.",
                "USAGE": "PLANNED",
                "EXAMPLES": "",
                "NOTES": "Not registered.",
                "RELATED": "",
                "SRC_FILE": "src/cli/cmd_planned.cpp",
            })
            write_csv(fixture.srcusage, list(rows[0]), rows)
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "reports/dispositions.csv").open(encoding="utf-8", newline="") as handle:
                dispositions = list(csv.DictReader(handle))
            self.assertTrue(any(
                row["CAN_NAME"] == "PLANNED"
                and row["CLASSIFICATION"] == "DECLARED_WITHOUT_RUNTIME_IDENTITY"
                and row["BLOCKING"] == "F"
                for row in dispositions
            ))

    def test_compact_command_uses_unique_syssubcmd_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            write_csv(
                fixture.syscmd,
                ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"],
                [{"CMD_ID": "CMD_SETCASE", "CAN_NAME": "SETCASE", "TYPE": "command", "VIS": "public", "HANDLER": "cmd_SETCASE", "ACTIVE": "T"}],
            )
            write_csv(
                fixture.srcusage,
                ["COMMAND", "STATUS", "SUMMARY", "USAGE", "EXAMPLES", "NOTES", "RELATED", "SRC_FILE"],
                [],
            )
            write_csv(
                fixture.sysargs,
                ["OWNER_NAM", "ARG_KIND", "ARG_NAME", "ACTIVE", "SRC_AUTH", "SRC_FILE"],
                [],
            )
            write_csv(
                fixture.syssubcmd,
                ["QUAL_NAME", "IMPL_STAT", "VIS_TIER", "SRC_AUTH", "SRC_FILE", "HANDLER", "ACTIVE", "NOTES"],
                [{
                    "QUAL_NAME": "SET CASE", "IMPL_STAT": "implemented", "VIS_TIER": "public",
                    "SRC_AUTH": "subusage_contract", "SRC_FILE": "cmd_set.cpp", "HANDLER": "cmd_SETCASE",
                    "ACTIVE": "T", "NOTES": "summary=Set case behavior. ; syntax=SET CASE ON|OFF",
                }],
            )
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "candidate/sysrefline_candidate.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row["TEXT"] == "SET CASE ON|OFF" and row["SRC_AUTH"] == "SYSSUBCMD" for row in rows))

    def test_syntax_command_uses_unique_sysargs_owner_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            write_csv(
                fixture.syscmd,
                ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"],
                [
                    {"CMD_ID": "CMD_ELSE", "CAN_NAME": "ELSE", "TYPE": "syntax-command", "VIS": "public", "HANDLER": "cmd_ELSE", "ACTIVE": "T"},
                    {"CMD_ID": "CMD_IF", "CAN_NAME": "IF", "TYPE": "syntax-command", "VIS": "public", "HANDLER": "cmd_IF", "ACTIVE": "T"},
                ],
            )
            write_csv(
                fixture.sysargs,
                ["OWNER_NAM", "ARG_KIND", "ARG_NAME", "ACTIVE", "SRC_AUTH", "SRC_FILE"],
                [{"OWNER_NAM": "IF", "ARG_KIND": "keyword", "ARG_NAME": "ELSE", "ACTIVE": "T", "SRC_AUTH": "usage_contract_v1", "SRC_FILE": "src/cli/cmd_if.cpp"}],
            )
            write_csv(
                fixture.srcusage,
                ["COMMAND", "STATUS", "SUMMARY", "USAGE", "EXAMPLES", "NOTES", "RELATED", "SRC_FILE"],
                [{"COMMAND": "IF", "STATUS": "supported", "SUMMARY": "Conditional script flow.", "USAGE": "IF <expr>\nELSE\nENDIF", "EXAMPLES": "", "NOTES": "", "RELATED": "", "SRC_FILE": "src/cli/cmd_if.cpp"}],
            )
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "reports/dispositions.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row["CAN_NAME"] == "ELSE" and "SYNTAX_COMMAND_OF_IF" in row["DETAIL"] for row in rows))

    def test_routed_alias_requires_handler_and_sysargs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            write_csv(
                fixture.syscmd,
                ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"],
                [
                    {"CMD_ID": "CMD_BUILD", "CAN_NAME": "BUILD", "TYPE": "command", "VIS": "public", "HANDLER": "cmd_BUILDVECTORS", "ACTIVE": "T"},
                    {"CMD_ID": "CMD_BUILDVECTORS", "CAN_NAME": "BUILDVECTORS", "TYPE": "command", "VIS": "public", "HANDLER": "cmd_BUILDVECTORS", "ACTIVE": "T"},
                ],
            )
            write_csv(
                fixture.sysargs,
                ["OWNER_NAM", "ARG_KIND", "ARG_NAME", "ACTIVE", "SRC_AUTH", "SRC_FILE"],
                [{"OWNER_NAM": "BUILDVECTORS", "ARG_KIND": "keyword", "ARG_NAME": "BUILD", "ACTIVE": "T", "SRC_AUTH": "usage_contract_v1", "SRC_FILE": "src/cli/cmd_buildvectors.cpp"}],
            )
            write_csv(
                fixture.srcusage,
                ["COMMAND", "STATUS", "SUMMARY", "USAGE", "EXAMPLES", "NOTES", "RELATED", "SRC_FILE"],
                [{"COMMAND": "BUILDVECTORS", "STATUS": "supported", "SUMMARY": "Report build vectors.", "USAGE": "BUILDVECTORS\nBUILD VECTORS", "EXAMPLES": "", "NOTES": "", "RELATED": "", "SRC_FILE": "src/cli/cmd_buildvectors.cpp"}],
            )
            fixture.write_manifest()
            out = fixture.root / "out"
            self.assertEqual(0, MOD.main(fixture.args(out)))
            with (out / "reports/dispositions.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row["CAN_NAME"] == "BUILD" and "ROUTED_ALIAS_OF_BUILDVECTORS" in row["DETAIL"] for row in rows))

    def test_existing_output_directory_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            out = fixture.root / "out"
            out.mkdir()
            self.assertEqual(2, MOD.main(fixture.args(out)))

    def test_manifest_cannot_bind_an_input_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fixture = Fixture(base / "repo")
            outside = base / "outside.csv"
            outside.write_bytes(fixture.syscmd.read_bytes())
            fixture.write_manifest({
                "SYSCMD": {
                    "path": "../outside.csv",
                    "sha256": MOD.sha256_file(outside),
                }
            })
            out = fixture.root / "out"
            self.assertEqual(2, MOD.main(fixture.args(out)))
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
