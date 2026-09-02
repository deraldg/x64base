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
    git             TRACKED, IGNORED, or UNTRACKED (see `git_state`)

WHAT THE JOIN CATCHES FOR FREE, and this is the real reason it reads git:

  - a page on disk that NO class declares (the manifest gate catches this too)
  - a page DECLARED by the manifest that git neither tracks NOR ignores -- which
    the manifest gate does NOT catch, because it validates against the
    filesystem. Two Lab pages were in exactly that state on 2026-09-02, hours
    after the identical defect was found and gated for the accepted manual. See
    GATE_CORRECTIONS_REQUIRED_V1.md, G3. Both are now tracked.

THE IGNORED CASE IS NOT A FINDING, and the first version of this tool got that
wrong. `content/portal/*` is gitignored deliberately -- local-only working
references -- and reporting it as "declared but untracked" reported a DECISION as
a FAULT. Two conditions, one answer, which is the exact defect this lane spent
the day cataloguing. The three-way split in `git_state` is the correction.

    exit 0   emitted (or --check found no drift)
    exit 2   --check found drift, or a declared page is neither tracked nor
             ignored
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


def git_state(site: Path, rel: str) -> str:
    """TRACKED | IGNORED | UNTRACKED.

    THE THREE-WAY SPLIT IS THE POINT, and an earlier version of this tool did not
    make it. It asked only "is this tracked?" and reported everything else as
    "DECLARED BUT UNTRACKED", which flagged `content/portal/*` as a defect when
    those pages are DELIBERATELY gitignored. A decision was reported as a fault.

    That is the same shape this lane spent 2026-09-02 cataloguing: one answer for
    two conditions that need different responses (GATE_CORRECTIONS_REQUIRED_V1,
    G1). The prepush gate already states the distinction in its own message --
    "an IGNORED path can never be staged at all" -- so the tool that reads git
    should honour it.

        TRACKED    in the index; a second machine has it, and a diff exists
        IGNORED    excluded ON PURPOSE by .gitignore; not a finding
        UNTRACKED  neither. Exists on ONE disk. This is the defect.
    """
    if subprocess.run(
        ["git", "--no-optional-locks", "ls-files", "--error-unmatch", rel],
        cwd=site, capture_output=True, timeout=30, check=False,
    ).returncode == 0:
        return "TRACKED"
    if subprocess.run(
        ["git", "--no-optional-locks", "check-ignore", "-q", rel],
        cwd=site, capture_output=True, timeout=30, check=False,
    ).returncode == 0:
        return "IGNORED"
    return "UNTRACKED"


def page_path(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        return value["path"]
    return ""


def load_classes(manifest: Path) -> tuple[dict, dict, dict]:
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    cls, gen, con = {}, {}, {}
    for name, spec in (data.get("classes") or {}).items():
        for value in (spec or {}).get("pages", []):
            p = page_path(value)
            if not p:
                continue
            cls[p] = name
            if isinstance(value, dict) and value.get("generator"):
                gen[p] = value["generator"]
            if isinstance(value, dict) and value.get("contract"):
                c = value["contract"]
                con[p] = [c] if isinstance(c, str) else list(c)
    return cls, gen, con


def last_touched(repo: Path, pathspec: str = ".") -> dict[str, str]:
    """repo-relative path -> YYYY-MM-DD of the NEWEST commit touching it.

    ONE git pass, not one per file. At ~150 pages against two repositories a
    per-file `git log` is ~300 subprocesses; this is two. Read-only and
    lock-free, so it is allowed from a mounted sandbox (CLAUDE.md, Sandbox
    agents: `log` is on the exhaustive allow-list).

    `git log` emits newest-first, so the FIRST date seen for a path is its
    newest. Later (older) sightings are discarded.
    """
    try:
        out = subprocess.run(
            ["git", "--no-optional-locks", "log", "--format=%x00%ad",
             "--date=short", "--name-only", "--", pathspec],
            cwd=repo, capture_output=True, text=True, timeout=300, check=False,
        ).stdout
    except (FileNotFoundError, NotADirectoryError, subprocess.TimeoutExpired):
        # A bad --engine-root must not end the run in a traceback. Returning {}
        # leaves every binding UNDATED, which is a REPORTED state that names the
        # problem, rather than a stack trace that names a Python line. Caught by
        # test_missing_repo_returns_empty_not_an_exception, which failed against
        # the first version of this function.
        print(f"website-tree: cannot read git history at {repo} -- "
              "bindings will report UNDATED", file=sys.stderr)
        return {}
    dates: dict[str, str] = {}
    current = None
    for line in out.splitlines():
        if line.startswith("\x00"):
            current = line[1:].strip()
        elif line.strip() and current:
            dates.setdefault(line.strip(), current)
    return dates


# FOUR STATES, DELIBERATELY, and the whole point of this check.
#
# The 2026-09-02 lane spent a day on gates that answered two different
# conditions with one word. This comparison could easily do the same: collapse
# "the page might be stale" into "the page is wrong", or collapse "nothing was
# declared" into "nothing is wrong". Both would be false, and the second is how
# `content/docs/engine/workspaces.mdx` sat six days behind its own engine
# contract while every freshness gate passed it.
#
#   CURRENT      page last touched AT OR AFTER its contract. Says nothing about
#                whether the page is CORRECT -- only that nobody changed the
#                contract behind its back.
#   UNVERIFIED   the contract moved AFTER the page. NOT a claim that the page is
#                wrong. It is a claim that no human has looked since the
#                authority changed, which is the only thing a date can prove.
#   NO-CONTRACT  the manifest declares no contract for this page. NOT a finding.
#                Most pages make no capability claim and need no binding.
#   MISSING      a contract IS declared and the file is not there. A real defect,
#                and the one state here that is unambiguously broken.
CURRENCY_NOTE = {
    "CURRENT": "page is at or ahead of its contract",
    "UNVERIFIED": "CONTRACT MOVED AFTER THE PAGE -- needs a human read, not a rewrite",
    "NO-CONTRACT": "no capability binding declared; not a finding",
    "MISSING": "declared contract file does not exist -- fix the binding",
    "UNDATED": "binding declared but no commit date resolved -- fix the binding path",
}


def currency(page_date, contract_dates: list, engine: Path, contracts: list) -> tuple[str, str]:
    """Return (state, detail). Never asserts a page is WRONG -- only unverified."""
    if not contracts:
        return "NO-CONTRACT", ""
    absent = [c for c in contracts if not (engine / c).exists()]
    if absent:
        return "MISSING", ", ".join(absent)
    known = [d for d in contract_dates if d]
    if not known or not page_date:
        # UNDATED IS ITS OWN STATE, and collapsing it into NO-CONTRACT was a real
        # bug in the first version of this function -- caught 2026-09-02 by
        # running the tool, not by reading it. `last_touched` was scoped to
        # `src`, so a contract declared under `include/` produced no date, and
        # this branch reported "no binding declared" for a page that HAD one.
        # A binding that cannot be dated is not a binding that does not exist:
        # the first needs fixing, the second is normal. Exactly the defect the
        # currency check was written to find, in the currency check.
        return "UNDATED", "contract declared but no commit date resolved"
    newest = max(known)
    if newest > page_date:
        return "UNVERIFIED", f"page {page_date} < contract {newest}"
    return "CURRENT", f"page {page_date} >= contract {newest}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", type=Path, help="write the tree here")
    ap.add_argument("--check", type=Path, help="compare against an existing tree; exit 2 on drift")
    ap.add_argument("--engine-root", type=Path,
                    help="D:\\code\\ccode -- enables the capability-currency column. "
                         "Optional: without it the tool behaves exactly as before.")
    a = ap.parse_args(argv)

    site = a.site_root.resolve()
    content = site / "content"
    classes, generators, contracts = load_classes(a.manifest)

    engine = a.engine_root.resolve() if a.engine_root else None
    page_dates = last_touched(site, "content") if engine else {}
    # WHOLE REPO, not "src". Contracts live under include/ too -- scoping this
    # to src/ silently undated every header binding (found 2026-09-02).
    eng_dates = last_touched(engine) if engine else {}

    pages = sorted(p.relative_to(content).as_posix()[:-4] for p in content.rglob("*.mdx"))
    by_bucket: dict[str, list[str]] = collections.defaultdict(list)
    for p in pages:
        by_bucket[p.split("/")[0]].append(p)

    untracked_declared, unclassified, ignored_declared = [], [], []
    unverified: list[tuple] = []
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
            state = git_state(site, rel)
            if cls is None:
                unclassified.append(p)
            if cls is not None and state == "UNTRACKED":
                untracked_declared.append(p)
            if cls is not None and state == "IGNORED":
                ignored_declared.append(p)
            flag = {"TRACKED": "", "IGNORED": "   [gitignored on purpose]",
                    "UNTRACKED": "   << UNTRACKED"}[state]
            gen = f"  <- {generators[p]}" if p in generators else ""
            cur = ""
            if engine:
                cs = contracts.get(p, [])
                st, detail = currency(
                    page_dates.get(rel), [eng_dates.get(c) for c in cs], engine, cs)
                if st != "NO-CONTRACT":
                    cur = f"   [{st}]"
                if st in ("UNVERIFIED", "MISSING", "UNDATED"):
                    unverified.append((p, st, detail, cs))
            leaf = p.split("/", 1)[1] if "/" in p else p
            W(f"|  |- {leaf:<52} {cls or 'UNCLASSIFIED':<20}{flag}{gen}{cur}")
    W("```")
    W("")

    if engine:
        W("## Capability currency -- does the page still match the engine?")
        W("")
        W("A FRESHNESS AUDIT CANNOT CATCH THIS, and that is why the column exists.")
        W("On 2026-09-02 `content/docs/engine/workspaces.mdx` still told readers")
        W('"One workspace is live at a time" while the engine had been additive since')
        W("R128 (2026-08-26). The page was not stale by date -- it was last touched")
        W("2026-08-26, and the CONTRACT it describes was last touched 2026-08-30, six")
        W("days NEWER. Every freshness gate passed it. Nothing asked whether the")
        W("authority had moved underneath.")
        W("")
        W("This compares two commit dates across two repositories. It proves exactly")
        W("one thing -- whether a human has read the page since its authority")
        W("changed -- and deliberately does NOT claim the page is wrong.")
        W("")
        W("| State | Meaning |")
        W("| --- | --- |")
        for name, note in CURRENCY_NOTE.items():
            W(f"| `{name}` | {note} |")
        W("")
        if unverified:
            W("### Pages whose contract moved after them")
            W("")
            W("| Page | State | Evidence | Contract |")
            W("| --- | --- | --- | --- |")
            for p, st, detail, cs in unverified:
                W(f"| `{p}` | **{st}** | {detail} | {', '.join(f'`{c}`' for c in cs)} |")
        else:
            W("No page with a declared contract is behind it.")
        W("")
        W("BINDINGS ARE DECLARED, NOT GUESSED. A page earns a contract by carrying")
        W("`contract:` in `website_content_manifest.yaml`. Convention-matching a page")
        W("name to `cmd_<name>.cpp` was rejected: it would silently bind the wrong")
        W("file and report a confident comparison against it, which is worse than")
        W("reporting nothing. An undeclared page is `NO-CONTRACT` and is not a")
        W("finding -- most pages make no capability claim.")
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

    if ignored_declared:
        W("## Declared and GITIGNORED -- deliberate, not a finding")
        W("")
        W("These pages are classified by the manifest and excluded from git ON")
        W("PURPOSE. They exist for the local build only. Listed so the next reader")
        W("does not 'fix' a decision, which an earlier version of this tool invited")
        W("by reporting them as untracked.")
        W("")
        for p in ignored_declared:
            W(f"- `content/{p}.mdx`")
        W("")

    if unclassified or untracked_declared:
        W("## FINDINGS")
        W("")
        for p in unclassified:
            W(f"- UNCLASSIFIED, no manifest class declares it: `content/{p}.mdx`")
        for p in untracked_declared:
            W(f"- DECLARED, NOT IGNORED, AND NOT TRACKED. Exists on one disk only: "
              f"`content/{p}.mdx`")
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
          f"gitignored-by-design {len(ignored_declared)}   "
          f"UNTRACKED {len(untracked_declared)}")
    return 2 if (unclassified or untracked_declared) else 0


if __name__ == "__main__":
    raise SystemExit(main())
