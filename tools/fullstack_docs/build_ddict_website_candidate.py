"""Produce a hash-bound internal website candidate from the current DDICT feed.

Writes only a new development output directory. Never touches the website
checkout, accepted artifacts or publication pointers.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datadict.catalog.ddict_feed import contained, sha, validate_bundle
from tools.manualgen.assemble_manual import rebase_source_links


def build(repo: Path, pointer: Path, output: Path) -> dict:
    repo, output = repo.resolve(), output.resolve()
    if not output.is_relative_to(repo) or output.is_relative_to(repo / "dottalkpp/data") or output.exists():
        raise ValueError("Output must be a new non-live directory inside development")
    selected = json.loads(pointer.read_text(encoding="utf-8"))
    source = contained(repo, selected["workspace"])
    result = validate_bundle(source, repo)
    if result["manifest_sha256"] != selected["manifest_sha256"]:
        raise ValueError("Current dictionary pointer does not match its manifest")
    output.mkdir(parents=True)
    for name in ("dictionary.md", "dictionary.html", "DDICT_MANIFEST.json", "DDICT_NATIVE.json", "DDICT_CROSSWALK.json", "DDICT_DIAGNOSTIC_DISPOSITION.json"):
        shutil.copyfile(source / name, output / name)
    recipe = repo / "docs/datadict/DDICT_METADATA_RECIPE_BOOK_V1.md"
    (output / "dictionary-recipes.md").write_text(rebase_source_links(recipe.read_text(encoding="utf-8"), recipe, output), encoding="utf-8")
    packet = {"schema": "dottalk.website.ddict_candidate.v1", "acceptance": "CANDIDATE",
              "sensitivity": "internal", "status": result["status"], "publishable": False,
              "input_manifest_sha256": result["manifest_sha256"],
              "recipe_source_sha256": sha(recipe),
              "artifacts": {p.name: sha(p) for p in sorted(output.iterdir())},
              "proposed_routes": ["/docs/dottalk/data-dictionary", "/docs/dottalk/data-dictionary-recipes"],
              "publication_requirements": ["Resolve catalog diagnostics and ambiguous identities", "Review internal evidence and source paths for public release", "Accept selected manual parts", "Recheck website baseline and deploy separately"]}
    (output / "website-ddict-candidate.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    return packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--pointer", type=Path, default=ROOT / "labtalk/registries/current_ddict_feed.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.repo_root, args.pointer, args.out)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, str(exc) + "\n")
