#!/usr/bin/env python3
"""check-site-artifacts -- the public site must not outlive the facts it quotes.

WHY THIS EXISTS. x64base.com carries generated authority artifacts derived from
THIS tree -- spec counts, marker counts, the primary-key flag, the SQL command
list, the conformance map's coverage -- and freshness contracts on the site hold
its pages to those artifacts. That half is mechanical and blocks the site build.

THE OTHER HALF WAS VOLUNTARY, and this file is that half. The site's checker
resolves every authority against the SITE root, so it can prove a page agrees
with the file beside it and NOTHING about this tree. That is exactly how a false
AUTOINCREMENT claim survived two days in 2026-09: the page and its authority
agreed with each other, and both were wrong about the engine. On 2026-09-09 a
second sweep found five pages calling a SHIPPED feature "still planned". Neither
was catchable from the site side. Both were changes made HERE.

WHAT IT CHECKS. For every generator in the site tree it runs the generator
against this tree and compares the result with the artifact the site has
published, and it separates two different failures rather than lumping them:

  FACTS DIFFER          the site is now saying something this tree contradicts.
                        HARD. Re-derive, fix the sentences the site's own
                        freshness contract will name, and commit both.
  ONLY PROVENANCE STALE every fact IT COMPARES still holds; the artifact's
                        engine commit stamp is behind. ADVISORY.

SAY WHAT IS ACTUALLY CHECKED. That second line read "the site is TRUE, merely
older than this tree" until 2026-09-10, and the advisory printed the same claim.
It was never in scope. This file compares GENERATED JSON against generators; the
site's PROSE is checked by the site tree's own TIER 2 sweep and by nobody here.
On 2026-09-10 four sentences on two pages were found describing two retired
predicate surfaces -- `SQL`'s, gone since 2026-09-04, and `SQLSEL`'s, gone that
morning -- while every artifact number stayed correct, because neither
retirement changed anything either artifact counts. Six days of green, and the
green was truthful about its own scope and lying about the sentence it printed.
An instrument that overstates its reach is worse than one that is missing: the
missing one sends somebody looking.

AND THE POINTER THIS FILE HANDS OUT IS NARROWER THAN IT SOUNDS, which is the
same fault one turn later. The site's prose sweep detects pages UNDERSTATING a
shipped capability -- that is what its authority is, a list of what ships, and
what its 2026-09-05 incident was. A page asserting a RETIRED surface is the
opposite polarity and has no entry to match, so both tiers of that check were
green through these six days as well. The advisory says so rather than implying
coverage that does not exist. Giving the capability authority a retired-entry
polarity would close it; that is a site-tree change and its own decision.

THAT SPLIT IS THE WHOLE DESIGN. Comparing whole artifacts would flag drift on
EVERY engine commit, because the artifact records the commit it was derived at
and any commit changes it. A gate that fires on every push is a gate somebody
turns off, and then the real drift ships behind it. Measured, not assumed: both
artifacts reproduce FACT-IDENTICAL from a tree at a different commit.

IT ASKS THE GENERATORS WHERE THEIR ARTIFACTS LIVE (`--artifact-path`) and finds
them by glob, so this file keeps NO list of generator/artifact pairs. A second
hand-kept list of the same fact is how two lists drift, and this repo has paid
for that shape repeatedly -- two teardown lists over one member, a registry
array whose size is typed separately from its contents, a nav table missing two
commands that were registered all along.

CONFIGURATION, and the reason it is not guessed. The site tree is a DIFFERENT
repository on a different clone, and its path is machine-specific:

    X64BASE_SITE_TREE=<path>   environment, or
    tmp/site_tree.txt          one line, first non-comment

The file lives in tmp/ because tmp/ is ALREADY ignored and this tree's
.gitignore is off-limits to edit. That is not a workaround: a config file
holding a machine-specific absolute path must never become committable by
accident, and putting it somewhere already ignored is stronger than adding a
rule somebody could later reorder.

NOT CONFIGURED is reported LOUDLY and does not block -- a clone with no site
checkout is a normal state, not a defect, and a gate that hard-fails where it
cannot run wedges the people it exists to protect. But it never passes SILENTLY:
a silent skip and a real pass look identical, which is the failure this tree
keeps finding in its own instruments.

CONFIGURED BUT UNUSABLE IS A DEFECT, NOT AN ABSENCE, and blocks: a path that
does not exist, a site tree with no generators, a node that will not run. That
distinction -- missing counted separately from wrong -- is the same one
PKDURABLE's validator makes about markers, for the same reason.

WHAT IT CANNOT DO. It cannot prove the site was REPUBLISHED. It compares this
tree against the artifact in the site WORKING TREE; whether that was built and
pushed to x64base.com is a separate act with its own evidence (the release
number in /artifacts/site-release.json). A green here means the site tree is
ready to publish truthfully, not that the live site is truthful.

Exit codes: 0 clean or not configured, 1 advisory, 2 hard-blocked, 4 usage error.
"""

import glob
import json
import os
import subprocess
import sys

LOCAL_CONFIG = os.path.join("tmp", "site_tree.txt")
GENERATOR_GLOB = os.path.join("scripts", "derive-*-authority.mjs")
# Provenance, not fact. Stripped before comparing; see the docstring.
PROVENANCE_KEYS = ("engine", "derived_on")


def repo_root():
    out = subprocess.run(["git", "--no-optional-locks", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def configured_site_tree(root):
    """Return (path, source) or (None, None). Never guesses a location."""
    env = os.environ.get("X64BASE_SITE_TREE", "").strip()
    if env:
        return env, "X64BASE_SITE_TREE"
    local = os.path.join(root, LOCAL_CONFIG)
    if os.path.exists(local):
        with open(local, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line, LOCAL_CONFIG
    return None, None


def facts_of(doc):
    return {k: v for k, v in doc.items() if k not in PROVENANCE_KEYS}


def differing_keys(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def run_node(site, argv):
    """Run node in the SITE tree. Returns (returncode, stdout, stderr)."""
    try:
        out = subprocess.run(["node"] + argv, cwd=site,
                             capture_output=True, text=True)
    except OSError as exc:
        return None, "", str(exc)
    return out.returncode, out.stdout, out.stderr


def main(argv):
    root = repo_root()
    if root is None:
        print("check-site-artifacts: not a git worktree -- skipped")
        return 0

    site, source = configured_site_tree(root)
    if not site:
        print("check-site-artifacts: NOT CONFIGURED -- the published site "
              "artifacts were NOT checked against this tree.")
        print(f"  To enable: set X64BASE_SITE_TREE, or put the site tree's path "
              f"on one line in {LOCAL_CONFIG} (gitignored).")
        print("  This is reported every run on purpose. A silent skip and a real "
              "pass look the same, and that is a defect this tree keeps finding.")
        return 0

    if not os.path.isdir(site):
        print(f"check-site-artifacts: BLOCKED -- {source} names {site!r}, "
              f"which is not a directory.", file=sys.stderr)
        print("  A configured path that does not resolve is a defect, not an "
              "absence. Fix the path or remove the configuration.", file=sys.stderr)
        return 2

    generators = sorted(
        os.path.relpath(p, site).replace("\\", "/")
        for p in glob.glob(os.path.join(site, GENERATOR_GLOB))
    )
    if not generators:
        print(f"check-site-artifacts: BLOCKED -- no {GENERATOR_GLOB} found under "
              f"{site}.", file=sys.stderr)
        print("  The path is configured as a site tree but carries no authority "
              "generators. Either it is the wrong directory, or the generators "
              "were removed and this check should be too.", file=sys.stderr)
        return 2

    hard = False
    advisory = False
    for gen in generators:
        rc, where, err = run_node(site, [gen, "--artifact-path"])
        if rc != 0:
            print(f"check-site-artifacts: BLOCKED -- {gen} could not report its "
                  f"artifact path.", file=sys.stderr)
            print(f"    {(err or '').strip()[:400]}", file=sys.stderr)
            return 2
        rel = where.strip()
        published_path = os.path.join(site, *rel.split("/"))

        rc, fresh_text, err = run_node(site, [gen, "--engine", root, "--print"])
        if rc != 0:
            print(f"check-site-artifacts: BLOCKED -- {gen} failed against this "
                  f"tree.", file=sys.stderr)
            print(f"    {(err or '').strip()[:400]}", file=sys.stderr)
            return 2

        try:
            fresh = json.loads(fresh_text)
        except ValueError as exc:
            print(f"check-site-artifacts: BLOCKED -- {gen} did not emit JSON: "
                  f"{exc}", file=sys.stderr)
            return 2

        if not os.path.exists(published_path):
            print(f"check-site-artifacts: BLOCKED -- {gen} derives {rel}, which "
                  f"the site tree does not have.", file=sys.stderr)
            print("  Run the generator in the site tree and commit the artifact "
                  "there.", file=sys.stderr)
            hard = True
            continue

        with open(published_path, "r", encoding="utf-8") as fh:
            try:
                published = json.load(fh)
            except ValueError as exc:
                print(f"check-site-artifacts: BLOCKED -- {rel} is not valid "
                      f"JSON: {exc}", file=sys.stderr)
                hard = True
                continue

        diff = differing_keys(facts_of(published), facts_of(fresh))
        if diff:
            print(f"check-site-artifacts: {rel} -- FACTS DIFFER from this tree",
                  file=sys.stderr)
            for key in diff:
                print(f"    {key}:", file=sys.stderr)
                print(f"      site   {json.dumps(published.get(key))[:300]}",
                      file=sys.stderr)
                print(f"      engine {json.dumps(fresh.get(key))[:300]}",
                      file=sys.stderr)
            hard = True
            continue

        site_commit = (published.get("engine") or {}).get("commit")
        engine_commit = (fresh.get("engine") or {}).get("commit")
        if site_commit != engine_commit:
            print(f"check-site-artifacts: {rel} -- facts hold; provenance stale "
                  f"({(site_commit or '?')[:9]} -> {(engine_commit or '?')[:9]})")
            advisory = True
        else:
            print(f"check-site-artifacts: {rel} -- current")

    if hard:
        print("\n  BLOCKED -- a published site artifact disagrees with this "
              "tree. The site's own freshness contracts CANNOT see this: they "
              "resolve against the site root. Re-derive in the site tree, then "
              "run its `npm run check:freshness`, which will name every sentence "
              "that has to change.", file=sys.stderr)
        return 2
    if advisory:
        print("\n  ADVISORY -- every fact IN THE ARTIFACTS still holds. They "
              "were derived at an older commit of this tree; re-derive when "
              "convenient so the stamp the pages print matches. NOT blocking.")
        print("  THIS SAYS NOTHING ABOUT THE SITE'S PROSE. This check reads the "
              "generated JSON authorities and compares numbers. A page can "
              "contradict this tree without any artifact number moving, and "
              "this line used to claim otherwise -- it read 'nothing on the "
              "site is false' for six days while four sentences across two "
              "pages described a scanner retired 2026-09-04 and a SQLSEL "
              "predicate form retired 2026-09-10. Neither retirement changed a "
              "counted fact.")
        print("  AND NOTHING ELSE CAUGHT THEM EITHER, so do not read the line "
              "above as a handoff. The site tree's `npm run check:freshness` "
              "is the prose instrument and BOTH ITS TIERS WERE GREEN "
              "throughout: tier 1 compares exact values and no number was "
              "stale; tier 2 sweeps pages for a SHIPPED capability described "
              "as planned or missing, and its authority is a list of what "
              "ships, so a page asserting a REMOVED surface has no entry to "
              "match. That is one polarity, and a retirement is the other. "
              "Run it anyway -- it catches what it was built for -- but the "
              "sweep that found these four sentences was a person asking.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
