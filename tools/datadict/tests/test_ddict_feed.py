from __future__ import annotations
import copy
import csv
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.datadict.catalog import ddict_feed as feed
from tools.fullstack_docs.build_ddict_website_candidate import build as website_build
from tools.manualgen.manualgen_lib.harvest import inventory_harvest


class NativeFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = ROOT / "build/src/Release/ddict_export.exe"
        test = ROOT / "build/src/tests/Release/dottalkpp_ddict_catalog_view_test.exe"
        result = subprocess.run([str(test)], capture_output=True, text=True, check=True)
        cls.fixture = Path(re.search(r"^FIXTURES (.+)$", result.stdout, re.M).group(1).strip())
        if not cls.fixture.resolve().is_relative_to(ROOT / "build/ddict-dogfood"):
            raise ValueError("Unexpected native fixture location")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ddict-feed-test-", dir=ROOT / "build")
        self.base = Path(self.temp.name).resolve()
        if not self.base.is_relative_to(ROOT / "build"):
            raise ValueError("Test path escapes build")
        self.catalog = self.base / "catalog"
        shutil.copytree(self.fixture / "command_home/data/datadict", self.catalog)
        shutil.copyfile(self.fixture / "command_memo_saved.dtx", self.catalog / "DATA_DICTIONARY_OBJECT_ATTRIBUTES.dtx")
        self.out = self.base / "feed"

    def tearDown(self):
        self.temp.cleanup()

    def make_feed(self):
        return feed.build(ROOT, self.exe, self.catalog, self.out)

    def test_native_long_names_memo_and_read_only(self):
        before = feed.snapshot(self.catalog)
        result = self.make_feed()
        self.assertEqual(result["status"], "READY")
        self.assertEqual(before, feed.snapshot(self.catalog))
        data = json.loads((self.out / "DDICT_NATIVE.json").read_text())
        self.assertEqual(2, len(data["tables"]["DDOBJECT"]))
        attr = data["tables"]["DDATTR"][0]
        self.assertEqual("RESOLVED", attr["_DD_MEMO_STATE:CATALOG_ATTRIBUTE_DETAIL"])
        self.assertIn("Native x64base dogfood memo", attr["CATALOG_ATTRIBUTE_DETAIL"])
        self.assertIn("A_VERY_LONG_COMMAND_SURFACE_NAME", (self.out / "dictionary.md").read_text())
        self.assertEqual(5, result["identity_count"])

    def test_missing_memo_stays_explicit(self):
        memo = self.catalog / "DATA_DICTIONARY_OBJECT_ATTRIBUTES.dtx"
        memo.unlink()
        result = self.make_feed()
        self.assertEqual("REVIEW", result["status"])
        self.assertFalse(memo.exists())
        self.assertIn("UNAVAILABLE", (self.out / "DDICT_NATIVE.json").read_text())

    def test_every_diagnostic_gets_a_blocking_disposition(self):
        diagnostics = [
            "DATA_DICTIONARY_RUNS: RUN_DETAIL_TEXT: MemoStore: memo object not found or unreadable (cells=2)",
            "DATA_DICTIONARY_OBJECT_ATTRIBUTES: CATALOG_ATTRIBUTE_DETAIL: invalid space-filled x64 memo link (cells=126)",
            "DATA_DICTIONARY_RELATION_EDGES: unresolved target x64:OBJ_123",
        ]
        rows = feed.diagnostic_disposition(diagnostics)
        self.assertEqual(3, len(rows))
        self.assertEqual({"MEMO_PAYLOAD_UNAVAILABLE", "MEMO_LINK_INVALID", "RELATION_ENDPOINT_UNRESOLVED"}, {r["category"] for r in rows})
        self.assertTrue(all(r["severity"] == "BLOCKS_READY" and not r["auto_fix"] for r in rows))
        self.assertEqual(128, sum(r["affected_cells"] for r in rows))

    def test_unknown_diagnostic_fails_build(self):
        rows = feed.diagnostic_disposition(["DDOBJECT: unexpected reader condition"])
        self.assertEqual("UNCLASSIFIED", rows[0]["category"])

    def test_catalog_member_change_fails(self):
        self.make_feed()
        (self.catalog / "new-file.txt").write_text("changed membership")
        with self.assertRaisesRegex(ValueError, "Stale catalog"):
            feed.validate_bundle(self.out, ROOT)

    def test_changed_bytes_same_size_fail(self):
        self.make_feed()
        path = self.catalog / "DDOBJECT.dbf"
        raw = bytearray(path.read_bytes()); raw[-2] ^= 1; path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "Stale catalog"):
            feed.validate_bundle(self.out, ROOT)

    def test_tampered_artifact_fails(self):
        self.make_feed()
        (self.out / "dictionary.md").write_text("forged output")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            feed.validate_bundle(self.out, ROOT)

    def test_duplicate_identity_fails(self):
        self.make_feed()
        data = json.loads((self.out / "DDICT_NATIVE.json").read_text())
        data["tables"]["DDOBJECT"].append(copy.deepcopy(data["tables"]["DDOBJECT"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate dictionary identity"):
            feed.validate_native(data)

    def test_reference_collision_is_review_not_collapse(self):
        self.make_feed()
        data = json.loads((self.out / "DDICT_NATIVE.json").read_text())
        for row in data["tables"]["DDOBJECT"]:
            row.update(OBJTYPE="COMMAND", NAME="set  order")
        mapping = feed.crosswalk(data)
        matches = [m for m in mapping if m["reference_key"] == "CMD:SET ORDER"]
        self.assertEqual(2, len(matches))
        self.assertTrue(all(m["mapping_state"] == "AMBIGUOUS_REFERENCE_REVIEW" for m in matches))
        self.assertEqual("REVIEW", feed.feed_status(data, mapping))

    def test_argument_kind_prevents_collision(self):
        a = feed.reference_key("ARGUMENT", "path", "set", "command", "keyword")
        b = feed.reference_key("ARGUMENT", "path", "set", "command", "placeholder")
        self.assertEqual("ARG:COMMAND:SET:KEYWORD:PATH", a)
        self.assertNotEqual(a, b)
        self.assertEqual("", feed.reference_key("COMMAND_SURFACE", "SET"))

    def test_output_cannot_overwrite_or_touch_live_data(self):
        self.make_feed()
        with self.assertRaisesRegex(ValueError, "overwrite refused"):
            self.make_feed()
        with self.assertRaisesRegex(ValueError, "live data"):
            feed.build(ROOT, self.exe, self.catalog, ROOT / "dottalkpp/data/forbidden-feed")

    def test_manualgen_companion_and_website_candidate(self):
        self.make_feed()
        paths = SimpleNamespace(repo_root=ROOT, harvest_workspace=str(self.out), manualgen_root=ROOT / "docs/manuals/developer/manualgen")
        self.assertEqual("READY", inventory_harvest(paths)["dictionary"]["status"])
        pointer = self.base / "pointer.json"
        pointer.write_text(json.dumps({"workspace": self.out.relative_to(ROOT).as_posix(), "manifest_sha256": feed.sha(self.out / "DDICT_MANIFEST.json")}))
        packet = website_build(ROOT, pointer, self.base / "site-candidate")
        self.assertFalse(packet["publishable"])
        self.assertEqual("CANDIDATE", packet["acceptance"])
        self.assertEqual("READY", feed.validate_bundle(self.base / "site-candidate", ROOT)["status"])
        (self.out / "dictionary.md").write_text("stale")
        self.assertEqual("FAIL", inventory_harvest(paths)["dictionary"]["status"])

    def test_manual_recipe_is_actually_rendered(self):
        spec = importlib.util.spec_from_file_location("ddict_assembler_test", ROOT / "tools/manualgen/assemble_manual.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        import yaml
        manifest = yaml.safe_load((ROOT / "tools/manualgen/manual_assembly_manifest.yaml").read_text(encoding="utf-8"))
        part = next(p for p in manifest["parts"] if p["id"] == "art-ddict-recipes")
        rendered = mod.render_part(part, {"output_dir": self.base})
        self.assertIn("Data dictionary and metadata recipe book", rendered)
        self.assertIn("DDICT_MANIFEST", rendered)
        for target in re.findall(r"\]\(([^)]+)\)", rendered):
            if not re.match(r"^[A-Za-z]+:", target):
                self.assertTrue((self.base / target.split('#')[0]).exists(), target)

    def test_portal_opens_only_current_validated_feed(self):
        self.make_feed()
        pointer = self.base / "portal-pointer.json"
        pointer.write_text(json.dumps({"workspace": self.out.relative_to(ROOT).as_posix(), "manifest_sha256": feed.sha(self.out / "DDICT_MANIFEST.json")}))
        spec = importlib.util.spec_from_file_location("ddict_portal_test", ROOT / "labtalk/portal/labtalk_portal.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        item = mod.PortalItem("portal.docs", "Docs", "doc.ddict.feed", "Dictionary", "ddict_feed", {"path": str(pointer)})
        self.assertEqual(self.out / "dictionary.html", mod.first_openable_path(item))
        (self.catalog / "change.txt").write_text("new member")
        self.assertIsNone(mod.first_openable_path(item))
        self.assertIn("stale", mod.ddict_feed_status(item)[1].lower())

    def test_portal_clone_mode_is_snapshot_only(self):
        self.make_feed()
        pointer = self.base / "portal-pointer-clone.json"
        pointer.write_text(json.dumps({"workspace": self.out.relative_to(ROOT).as_posix(), "manifest_sha256": feed.sha(self.out / "DDICT_MANIFEST.json")}))
        shutil.rmtree(self.catalog)
        spec = importlib.util.spec_from_file_location("ddict_portal_clone_test", ROOT / "labtalk/portal/labtalk_portal.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        item = mod.PortalItem("portal.docs", "Docs", "doc.ddict.feed", "Dictionary", "ddict_feed", {"path": str(pointer)})
        self.assertEqual(self.out / "dictionary.html", mod.first_openable_path(item))
        self.assertIn("SNAPSHOT_ONLY", mod.ddict_feed_status(item)[1])

    def test_fullstack_preflight_never_accepts_snapshot_only(self):
        from tools.fullstack_docs.docpush_preflight import check_ddict_feed
        self.make_feed()
        pointer = self.base / "preflight-no-source.json"
        pointer.write_text(json.dumps({"workspace": self.out.relative_to(ROOT).as_posix(), "manifest_sha256": feed.sha(self.out / "DDICT_MANIFEST.json")}))
        shutil.rmtree(self.catalog)
        self.assertEqual("FAIL", check_ddict_feed(ROOT, pointer)["status"])

    def test_fullstack_preflight_rejects_stale_pointer(self):
        from tools.fullstack_docs.docpush_preflight import check_ddict_feed
        self.make_feed()
        pointer = self.base / "preflight-pointer.json"
        selected = {"workspace": self.out.relative_to(ROOT).as_posix(), "manifest_sha256": feed.sha(self.out / "DDICT_MANIFEST.json")}
        pointer.write_text(json.dumps(selected))
        self.assertEqual("READY", check_ddict_feed(ROOT, pointer)["status"])
        selected["manifest_sha256"] = "0" * 64
        pointer.write_text(json.dumps(selected))
        self.assertEqual("FAIL", check_ddict_feed(ROOT, pointer)["status"])

    def test_syscmd_export_honors_both_registry_and_contract_roots(self):
        workspace = self.base / "source-scope"
        for folder, name in (("selected", "SCOPE_ALLOWED"), ("excluded", "SCOPE_EXCLUDED")):
            directory = workspace / "src" / folder
            directory.mkdir(parents=True)
            (directory / "command.cpp").write_text(
                f'// @dottalk.usage v1\n// command: {name}\n// status: supported\n// noargs: usage\n// usage:\n//   {name}\n// @dottalk.end\nregistry().add("{name}", &cmd_{name});\n')
        def emit(roots, suffix):
            output = self.base / (suffix + ".csv")
            # Relative fixture workspace avoids the collector's existing
            # absolute /build/ exclusion (the fixture itself lives in build).
            args = [str(ROOT / "build/Release/metacollect.exe"), ".", "--no-source", "--syscmd-import-out", str(output)]
            for source in roots:
                args += ["--source-root", source]
            subprocess.run(args, cwd=workspace, capture_output=True, check=True)
            with output.open(newline="", encoding="utf-8") as stream:
                return {r["CAN_NAME"] for r in csv.DictReader(stream)}
        self.assertEqual({"SCOPE_ALLOWED"}, emit(["src/selected"], "one-root"))
        self.assertEqual({"SCOPE_ALLOWED", "SCOPE_EXCLUDED"}, emit(["src/selected", "src/excluded"], "two-roots"))


if __name__ == "__main__":
    unittest.main()
