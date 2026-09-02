#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: fullstack_docs
# layer: tool
# owns: the derived structural map of the x64base-site repository -- every page
#       with its maintenance class, its tracking state, and the route that serves it
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""build_website_tree.py -- derive the website's structure map.

WHY THIS IS GENERATED AND NOT WRITTEN
-------------------------------------
A hand-drawn tree of ~150 pages is stale the first time someone adds one, and
this lane has spent enough time on hand-kept lists beside the thing they
describe: the manifest's own `totals:` block, `collect_set_subcommands()`, the
64-name literal in `cmdhelp.cpp`, and the accepted manual's page counts. Each was
correct when written.

So this JOINS three authorities that already exist and never asserts anything of
its own:

    filesystem      content/**/*.mdx -- what pages exist
    manifest        tools/fullstack_docs/website_content_manifest.yaml -- the class
    git             is the page actually tracked?

WHAT THE JOIN CATCHES FOR FREE, and this is the real reason it reads git:

  - a page on disk that NO class declares (the manifest gate catches this too)
  - a page DECLARED by the manifest that git does not have -- which the manifest
    gate does NOT catch, because it validates against the filesystem. Two Lab
    pages were in exactly that state on 2026-09-02, hours after the identical
    defect was found and gated for the accepted manual. See
    GATE_CORRECTIONS_REQUIRED_V1.md, G3.

    exit 0   emitted (or --check found no drift)
    exit 2   --check found drift, or an untracked declared page exists
"""
from __future__ import annotations

import argparse
import collections
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("build_website_tree: PyYAML required -- use .venv312, not the vcpkg python")
    raise SystemExit(2)

CLASS_NOTE = {
    "generated": "regenerated every push; NEVER hand-edit a generated region",
    "derived": "regenerate or review when its source evidence changes",
    "maintained": "hand-authored; review when the tracked subject changes",
    "maintained_current": "permanent route, replaceable present-state region",
    "reported": "append-only measurement with pinned provenance",
    "static": "website-owned copy; human review only",
}


def tracked(site: Path, rel: str) -> bool:
    return subprocess.run(
        ["git", "--no-optional-locks", "ls-files", "--error-unmatch", rel],
        cwd=site, capture_output=True, timeout=30, check=False,
    ).returncode == 0


def page_path(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        return value["path"]
    return ""


def load_classes(manifest: Path) -> tuple[dict, dict]:
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    cls, gen = {}, {}
    for name, spec in (data.get("classes") or {}).items():
        for value in (spec or {}).get("pages", []):
            p = page_path(value)
            if not p:
                continue
            cls[p] = name
            if isinstance(value, dict) and value.get("generator"):
                gen[p] = value["generator"]
    return cls, gen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", type=Path, help="write the tree here")
    ap.add_argument("--check", type=Path, help="compare against an existing tree; exit 2 on drift")
    a = ap.parse_args(argv)

    site = a.site_root.resolve()
    content = site / "content"
    classes, generators = load_classes(a.manifest)

    pages = sorted(p.relative_to(content).as_posix()[:-4] for p in content.rglob("*.mdx"))
    by_bucket: dict[str, list[str]] = collections.defaultdict(list)
    for p in pages:
        by_bucket[p.split("/")[0]].append(p)

    untracked_declared, unclassified = [], []
    out: list[str] = []
    W = out.append

    W("# x64base-site -- structure map (DERIVED, do not hand-edit)")
    W("")
    W("    generator  tools/fullstack_docs/build_website_tree.py")
    W("    joins      filesystem + website_content_manifest.yaml + git tracking")
    W("    regenerate whenever a page is added, removed, or reclassified")
    W("")
    W("Every page below carries its MAINTENANCE CLASS, which decides how it may be")
    W("edited, and its TRACKING state. A page that is declared but untracked is a")
    W("defect, not a style: it resolves on one machine and nowhere else.")
    W("")
    W("## Maintenance classes")
    W("")
    W("| Class | Rule |")
    W("| --- | --- |")
    for name, note in CLASS_NOTE.items():
        W(f"| `{name}` | {note} |")
    W("")

    W("## Content tree")
    W("")
    W("```text")
    W("content/")
    for bucket in sorted(by_bucket):
        W(f"|- {bucket}/                    {len(by_bucket[bucket])} page(s)")
        for p in by_bucket[bucket]:
            cls = classes.get(p)
            rel = f"content/{p}.mdx"
            is_tracked = tracked(site, rel)
            if cls is None:
                unclassified.append(p)
            if cls is not None and not is_tracked:
                untracked_declared.append(p)
            flag = "" if is_tracked else "   << UNTRACKED"
            gen = f"  <- {generators[p]}" if p in generators else ""
            leaf = p.split("/", 1)[1] if "/" in p else p
            W(f"|  |- {leaf:<52} {cls or 'UNCLASSIFIED':<20}{flag}{gen}")
    W("```")
    W("")

    W("## Structures that are not pages")
    W("")
    W("```text")
    W("app/                    Next.js routes. Buckets use catch-all [...slug];")
    W("                        /lab is [[...slug]] so the index emits as an EMPTY")
    W("                        optional slug -- both /lab and each child must build.")
    W("components/             React components (client components need hydration;")
    W("                        see start-ai.ps1 on :3000 vs :3002).")
    W("config/")
    W("|- nav.ts               top navigation")
    W("|- sidebars.ts          docs sidebar registration")
    W("|- analytics.ts, retro.ts")
    W("public/")
    W("|- artifacts/           THE AUTHORITIES the site binds to:")
    W("|  |- documentation-progress-v1.json   11 of 13 freshness contracts read this")
    W("|  |- current-work-v1.json             generated task feed")
    W("|  '- site-release.json                release stamp")
    W("|- downloads/current/   DEVELOPER_MANUAL_LATEST.json + staged manual")
    W("|- diagrams/            generated images; sources live in diagrams/")
    W("|- AI/, eco/            raw artifacts served as-is; NEVER hand-edit")
    W("'- images/              evidence screenshots, brand, story figures")
    W("scripts/                THE GATES. All run by `npm run build`:")
    W("|- check-diagrams.mjs           diagrams generated and current")
    W("|- check-public-content.mjs     public content policy")
    W("|- check-site-freshness.mjs     13 contracts; --self-test proves they bite")
    W("|- site-freshness-contracts.json  the contract definitions")
    W("|- check-opacity-scale.mjs      Tailwind opacity on-scale")
    W("|- clean-build-output.mjs       clears .next/out/dist")
    W("|- strip-local-only-output.mjs  removes lab/reports/retro/portal from out/")
    W("'- publish-github-pages.mjs     the ONLY publication route")
    W("diagrams/               .mmd / .drawio SOURCES, kept with their images")
    W("apache/                 alternate static host config")
    W("```")
    W("")

    W("## Publication boundary -- EXPOSURE IS NOT THE SAME AS SUBJECT")
    W("")
    W("`strip-local-only-output.mjs` removes these from the published build, and the")
    W("publisher ABORTS if any survives:")
    W("")
    W("    lab  reports  retro  portal")
    W("")
    W("They exist in the working tree and on the local preview; they must never reach")
    W("x64base.com. `/memory` and `/portal` are additionally excluded from the search")
    W("index via `data-pagefind-ignore`.")
    W("")
    W("**TWO SURFACES CAN SHARE A SUBJECT AND HAVE OPPOSITE EXPOSURE.** This pair is")
    W("the one that catches people, and it caught the steward on 2026-09-02:")
    W("")
    W("    /portal/overview, /portal/schemas          LOCAL ONLY. Stripped from the")
    W("                                               build, unlisted, noindex, absent")
    W("                                               from search. Working references.")
    W("    /docs/labtalk/ai-portal                    PUBLIC. Describes the same")
    W("    /docs/labtalk/ai-portal-schemas            subject for readers.")
    W("")
    W("Same words in the route, opposite audiences. Read the maintenance class and")
    W("the strip list before describing a page's reach -- a page being about the AI")
    W("Portal says nothing about whether anyone outside can see it.")
    W("")
    W("**AND THE SUBJECT ITSELF IS NARROWER THAN THE NAME SUGGESTS.** Owner, 2026-09-02:")
    W("the AI Portal is not promised in any product and is separate; there is no")
    W("student portal; the only portal offered is for LabTalk, as custom end-user")
    W("development work, and it is neither the house AI Portal nor the BBS. The public")
    W("page already states this -- \"It is not a student portal for accessing an AI")
    W("service\" -- and that sentence is load-bearing. Do not soften it.")
    W("")

    W("## Counts")
    W("")
    counts = collections.Counter(classes.get(p, "UNCLASSIFIED") for p in pages)
    W("| Class | Pages |")
    W("| --- | ---: |")
    for name, n in sorted(counts.items()):
        W(f"| `{name}` | {n} |")
    W(f"| **total** | **{len(pages)}** |")
    W("")

    if unclassified or untracked_declared:
        W("## FINDINGS")
        W("")
        for p in unclassified:
            W(f"- UNCLASSIFIED, no manifest class declares it: `content/{p}.mdx`")
        for p in untracked_declared:
            W(f"- DECLARED BUT UNTRACKED, resolves on one machine only: `content/{p}.mdx`")
        W("")

    body = "\n".join(out) + "\n"

    if a.check:
        current = a.check.read_text(encoding="utf-8") if a.check.is_file() else ""
        if current != body:
            print(f"website-tree: DRIFT -- {a.check} does not match the derived tree")
            return 2
        print("website-tree: PASS -- the committed tree matches the derived one")
    if a.out:
        a.out.write_text(body, encoding="ascii", newline="\n")
        print(f"website-tree: wrote {a.out}")
    if not a.out and not a.check:
        print(body)

    print(f"  pages {len(pages)}   unclassified {len(unclassified)}   "
          f"declared-but-untracked {len(untracked_declared)}")
    return 2 if (unclassified or untracked_declared) else 0


if __name__ == "__main__":
    raise SystemExit(main())
