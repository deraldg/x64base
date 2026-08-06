#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: tools
# layer: helper
# owns:
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: supported
#
# Producer-side generator for the GPTbase hosted-advisor knowledge bundle. Makes the
# bundle a DERIVED, PUBLIC-SAFE consumer instead of a hand-curated snapshot that goes
# stale. Manifest: docs/ai-friendly/GPTBASE_BUNDLE_MANIFEST_V1.md. Read-only over
# sources; writes only the --out bundle dir. The bundle is PUBLIC (cloud GPT, not
# egress-isolated): default-deny; a sensitivity finding fails the build closed.
# Sources are grouped into a few coherent section files to stay under the Custom
# GPT knowledge-file cap and to avoid same-stem collisions.
"""Assemble the GPTbase bundle from already-public site content + public-safe seeds."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# (bundle_file, title, intent-phrase-for-the-pointer, [site globs], [repo files])
SECTIONS = [
    ("01_orientation.md", "Orientation: products and getting started",
     "get oriented -- what the products are, install, quickstart",
     ["products/*.mdx", "docs/getting-started/*.mdx"], []),
    ("02_engine.md", "Engine: DBF x32/x64, memo, indexes, VDISK, crosswalk",
     "understand the engine -- DBF x32 vs x64, memo, CDX/CNX/LMDB indexes, VDISK, "
     "capability map",
     ["docs/engine/*dbf*.mdx", "docs/engine/*format*.mdx", "docs/engine/*memo*.mdx",
      "docs/engine/*index*.mdx", "docs/engine/*vdisk*.mdx",
      "docs/engine/feature-crosswalk.mdx"], []),
    ("03_command_reference.md", "Command surface: catalog, DotScript, mutators",
     "look up a command, DotScript, or data-mutation safety",
     ["docs/dottalk/command-catalog.mdx", "docs/dottalk/*dotscript*.mdx",
      "docs/dottalk/*data-mutator*.mdx"], []),
    ("04_workbench.md", "DotTalk++ Workbench (GUI/TUI family)",
     "the GUI/TUI Workbench family (ArcticTalk and relatives)",
     ["docs/talk-family/*.mdx"], []),
    ("05_process_and_roles.md", "SDLC, AI roles taxonomy, doc-flush intent",
     "the SDLC, the three AI roles (agent / Ollama / GPTbase), how docs are produced",
     ["docs/dottalk/sdlc*.mdx", "docs/labtalk/sdlc*.mdx"],
     ["docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md",
      "docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_NORTH_STAR_V1.md"]),
    ("06_history.md", "Historical lineage and preservation",
     "project history and source lineage",
     ["docs/dev/historical-*.mdx"], []),
]
SITE_EXCLUDE = ("identity-security", "identity_security")

_SCRUB = re.compile(r"(?:[A-Za-z]:\\[^\s`)\"']+|/mnt/[^\s`)\"']+|/home/[^\s`)\"']+)")
_LEAK = re.compile(r"[A-Za-z]:\\|/mnt/|/home/|C:\\Users|BEGIN [A-Z ]*PRIVATE KEY|"
                   r"password\s*[:=]|api[_-]?key\s*[:=]|token\s*[:=]\s*\S", re.IGNORECASE)


def _as_of_date(repo_root: Path) -> str:
    text = (repo_root / "labtalk/registries/ai_portal_tasks.yaml").read_text(
        encoding="utf-8", errors="replace")
    m = re.search(r'^as_of_date:\s*"?([0-9-]+)"?', text, re.MULTILINE)
    return m.group(1) if m else "unknown"


def _scrub(text: str) -> str:
    return _SCRUB.sub("[local path]", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--site-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    content = args.site_root.resolve() / "content"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    as_of = _as_of_date(repo)

    findings: list[str] = []
    manifest = {"schema": "x64base.gptbase_bundle.v1", "as_of_date": as_of,
                "sensitivity": "public", "sections": []}
    total = 0

    pointer_rows: list[tuple[str, str]] = []
    for fname, title, intent, globs, repo_files in SECTIONS:
        pointer_rows.append((intent, fname))
        sources: list[tuple[str, Path]] = []
        seen: set[Path] = set()
        for g in globs:
            for p in sorted(content.glob(g)):
                if p in seen or any(x in p.name.lower() for x in SITE_EXCLUDE):
                    continue
                seen.add(p)
                sources.append(("site:" + str(p.relative_to(content)), p))
        for rel in repo_files:
            p = repo / rel
            if p.exists():
                sources.append(("repo:" + rel, p))

        parts = [f"# {title}\n",
                 f"<!-- GPTbase bundle section. as_of {as_of}. PUBLIC orientation, "
                 f"derived; verify against source. -->\n"]
        src_records = []
        for origin, src in sources:
            body = _scrub(src.read_text(encoding="utf-8", errors="replace"))
            leak = _LEAK.search(body)
            if leak:
                findings.append(f"{origin}: residual token {leak.group(0)!r}")
            parts.append(f"\n\n---\n\n<!-- source: {origin} -->\n\n{body}")
            src_records.append(origin)
        blob = "".join(parts)
        (out / fname).write_text(blob, encoding="utf-8")
        sha = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        manifest["sections"].append({"bundle_file": fname, "title": title,
                                     "sources": src_records, "sha256": sha,
                                     "bytes": len(blob)})
        total += len(blob)
        print(f"  {fname:<26} {len(blob):>7} bytes  <- {len(src_records)} source(s)")

    # Pointer / start-here index: route the GPT by intent, not a linear scan.
    # Mirrors the portal recall-graph pattern (reach by trigger, not read).
    idx = [f"# Start here -- x64base knowledge bundle (pointer)\n",
           f"<!-- as_of {as_of}. PUBLIC orientation, derived; verify against "
           f"current source before acting. -->\n",
           "\nThis bundle is public orientation about x64base, derived from the "
           "project's source of truth. It is orientation, not authority.\n",
           "\nRoute your question:\n\n| If you want to | Read |\n| --- | --- |\n"]
    for intent, fname in pointer_rows:
        idx.append(f"| {intent} | `{fname}` |\n")
    idx.append("\nIf a question is about local or sensitive data, this is the wrong "
               "tool -- that is the local Ollama's job, behind the egress block. "
               "GPTbase is public orientation only.\n")
    pointer_blob = "".join(idx)
    (out / "00_start_here.md").write_text(pointer_blob, encoding="utf-8")
    manifest["sections"].insert(0, {
        "bundle_file": "00_start_here.md", "title": "Pointer / start-here index",
        "sources": ["generated:pointer"],
        "sha256": hashlib.sha256(pointer_blob.encode("utf-8")).hexdigest(),
        "bytes": len(pointer_blob)})

    (out / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"bundle: {len(SECTIONS)} files, {total} bytes, as_of={as_of} -> {out}")
    if findings:
        print("SENSITIVITY FINDINGS (build fails closed):", file=sys.stderr)
        for f in findings:
            print("  - " + f, file=sys.stderr)
        return 2
    print("sensitivity: clean (default-deny scan passed)")
    print("NOTE: authoritative gate is x64base-site check-public-content.mjs; "
          "run it on the bundle before upload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
