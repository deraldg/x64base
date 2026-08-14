#!/usr/bin/env python3
"""
ecoschema_map.py -- generate the drill-down ecoschema map from the registries
and from the source tree, and JOIN them so the bridge between the two poles is
literal rather than decorative.

The map is GENERATED, never hand-edited, for the reason Tier 0 states about
itself: a hand-maintained picture of perishable state drifts.

v2 (2026-08-12) removed the two hand-written literals that could drift:
  - engine subsystems are now SCANNED from src/*/ with real file counts
  - proof coverage is JOINED from labtalk/registries/proofs.yaml
Lifecycle names remain literal on purpose: they are doctrine, each carrying a
charter path that is checked for existence at run time and flagged if absent.

Sources of truth, read at run time:
    labtalk/registries/projects.yaml   projects, kinds, statuses, lanes
    labtalk/registries/proofs.yaml     proof records, states, declared vocabulary
    coordination/aif/AIF-*.claim       the atomic lane ledger
    src/*/                             the engine's actual decomposition
    labtalk/proofs/runs/               captured transcripts (counted, not parsed)

Output:
    docs/maintenance/ECOSCHEMA_MAP_V1.html   self-contained, no network deps

Usage:
    python tools/fullstack_docs/ecoschema_map.py [--out PATH]

Owner: member.derald - steward: member.ai.claude.cowork
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

try:
    import yaml
except ImportError:
    print("ecoschema-map: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(4)


# Prose rule for this map (owner direction 2026-08-13): write to a READER who
# has just arrived, not to the maintainer. A stranger -- a student, an outside
# developer, an AI agent onboarding cold -- should be able to learn what these
# four surfaces ARE and why the distinction between them is worth drawing.
# No in-jokes, no "us", no assumed context.
POLES = {
    "x64base": {
        "label": "x64base",
        "tag": "declared // what the system says it is",
        "blurb": "The plan of the system, written down: its lifecycles, its "
                 "promotion ladder, the projects it has opened and the lanes "
                 "someone has claimed. Every software project has a description "
                 "of itself like this. It is drawn top-down, so it necessarily "
                 "mixes what is finished with what is only intended -- and that "
                 "mixture is not dishonesty, it is what a plan is.",
        "reads": "Read this side to learn what the system is ORGANISED to be.",
    },
    "dottalkpp": {
        "label": "DotTalk++",
        "tag": "built // what the code actually contains",
        "blurb": "The same system counted from the other end: directories that "
                 "exist on disk, with their source files tallied. Nothing here "
                 "is claimed -- it is measured at the moment this page is "
                 "generated. If a subsystem appears here, code for it exists. "
                 "That is a different and smaller statement than saying it works.",
        "reads": "Read this side to learn what has actually been BUILT.",
    },
    "labtalk": {
        "label": "LabTalk",
        "tag": "recorded // what has been taught and evidenced",
        "blurb": "Where the work becomes knowledge someone else can use: "
                 "lessons, proof documents, the registries that index them, and "
                 "the portal that onboards a newcomer. A system can be built and "
                 "still be unlearnable. This is the surface that decides which.",
        "reads": "Read this side to learn what the project KNOWS about itself.",
    },
    "site": {
        "label": "x64base.com",
        "tag": "published // what an outsider is told",
        "blurb": "The public face of the other three. It is the only surface most "
                 "people will ever see, so it is the one where a claim that "
                 "outruns its evidence does the most damage. Everything published "
                 "here should be traceable back to one of the other piers.",
        # This panel is deliberately the odd one out, and says why in plain terms.
        "reads": "This pier is DECLARED, not measured: the website lives in a "
                 "separate repository that this page's generator cannot read. "
                 "Everything else here is counted; this one is asserted, and "
                 "saying so is the point.",
    },
}

LIFECYCLES = [
    ("DotTalk++ SDLC", "engine, runtime and system correctness",
     "docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md",
     ["requirements/boundary", "design", "implementation", "verification",
      "documentation/metadata", "release and promotion"]),
    ("LabTalk SDLC", "laboratory campus truth and learning material",
     "labtalk/LABTALK_SDLC_FRAMEWORK_v0.md",
     ["labs", "cases", "lessons", "proofs", "student readiness"]),
    ("maintenance SDLC", "the maintenance surfaces and their gates",
     "docs/maintenance/MAINTENANCE_CHARTER_v1.md",
     ["MAINT", "BBOX", "DDICT", "MANUAL", "drift gates"]),
    ("AI Systems Integration SDLC", "relationships, vocabulary, end-to-end gates",
     "docs/maintenance/AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md",
     ["portal", "curation", "onboarding", "memory", "reports", "coordination",
      "pseudo-chat", "AI-BBS", "authorization", "evidence", "projections"]),
    ("PDLC", "programming development life cycle, program scale",
     "docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md",
     ["analyze", "design", "code", "test/debug", "document", "maintain"]),
]

PROMOTION_LEVELS = [
    ("source_defined", "code or contract exists"),
    ("runtime_observed", "runtime proof exists"),
    ("help_documented", "HELP exposes it accurately"),
    ("validated", "a validator checked it"),
    ("professional_ready", "safe for normal runtime use"),
    ("lab_ready", "safe for LabTalk to package"),
]

STATUS_CLASS = {
    "active_beta": "s-beta", "active_development": "s-active",
    "active_curated_staging": "s-active", "active_seed": "s-seed",
    "seed": "s-seed", "design_intended": "s-plan", "prototype": "s-proto",
    "local_prototype": "s-proto", "reserved_local_only": "s-plan",
    "downstream_publication_truth": "s-pub",
    "charter_with_autonomous_poc": "s-plan",
    "runtime_observed": "s-beta", "source_defined": "s-seed",
    "validated": "s-active", "no proof registered": "s-plan",
}


# --- machine-path scrub --------------------------------------------------------
# The map is published to x64base.com, and the site's own guard
# (scripts/check-public-content.mjs) refuses any asset carrying a local machine
# path. Registry notes legitimately name the roots -- projects.yaml describes
# D:/code/ccode and C:/x64base by design -- so the scrub happens here, at the
# publication boundary, rather than by censoring the registry.
#
# Caught by that guard on 2026-08-13, on the first attempt to publish this map.
# The named map below is for readability; the catch-all is what makes it safe,
# because the next note to name a new path would otherwise leak silently.
PATH_NAMES = [
    (r"[Dd]:[\\/]code[\\/]ccode", "the development root"),
    (r"[Cc]:[\\/]x64base", "the staging root"),
    (r"[Dd]:[\\/]dev[\\/]x64base-site", "the website root"),
    (r"[Dd]:[\\/]dev", "the website tree"),
]
ANY_LOCAL_PATH = re.compile(r"[A-Za-z]:[\\/][^\s\"',;)\]]*")


def scrub(text: str) -> str:
    """Remove machine-absolute paths from anything destined for a public asset."""
    if not text:
        return text
    for pat, rep in PATH_NAMES:
        text = re.sub(pat, rep, text)
    return ANY_LOCAL_PATH.sub("<local path>", text)


def scrub_tree(obj):
    if isinstance(obj, str):
        return scrub(obj)
    if isinstance(obj, dict):
        return {k: scrub_tree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub_tree(v) for v in obj]
    return obj


# --- work state, from the intake queue ----------------------------------------
# The claim ledger says a lane EXISTS. The intake queue says what STATE it is in,
# and the map ignored that column entirely -- so a reader could see 43 claimed
# lanes and not know which were proven, promoted, or merely proposed.
#
# Measured 2026-08-14 before writing the normaliser: 108 intake rows carry 86
# DISTINCT status strings. That is free text, not a vocabulary, and it repeats the
# underscore/hyphen split already found in proofs.yaml ("source_defined" x3 vs
# "source-defined" x3; "runtime-observed" x6 vs "closed_runtime_observed" x4).
# So: bucket by keyword, keep the raw string on the node, and report whatever
# refuses to bucket rather than dropping it.
INTAKE_QUEUE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"

# Order matters: first keyword hit wins, so terminal states are tested before
# in-flight ones. Keys were extended 2026-08-14 from the 22 rows that refused to
# bucket on the first pass -- measured, not guessed. Deliberately NOT tuned to
# zero: a residual "unclassified" is the honest signal that this column is free
# text, and driving it to zero by inventing keys would hide that.
WORK_STATE = [
    ("rejected",    ("reject", "withdrawn", "superseded")),
    ("closed",      ("closed", "retired", "complete")),
    ("promoted",    ("promoted", "published", "merged", "deployed")),
    ("proven",      ("runtime-proven", "runtime_proven", "runtime-observed",
                     "runtime_observed", "validated", "green", "proven",
                     "measured", "fixed")),
    ("source-defined", ("source-defined", "source_defined", "implemented", "built")),
    ("anchored",    ("anchored", "codified", "documented", "pin ")),
    ("active",      ("active", "in flight", "in progress", "wiring pending")),
    ("in-review",   ("review-needed", "review needed", "review_needed", "routed",
                     "draft", "scoping")),
    ("planned",     ("planned", "proposed", "not started", "not-started",
                     "pick-up-ready", "design", "intake", "charter", "staged",
                     "seed")),
]


def work_state(raw: str) -> str:
    low = (raw or "").lower()
    for name, keys in WORK_STATE:
        if any(k in low for k in keys):
            return name
    return "unclassified"


def load_intake(root: str) -> dict:
    """AIF-NNN -> {raw status, bucket}. Absent file is not fatal."""
    out = {}
    path = os.path.join(root, INTAKE_QUEUE)
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\|\s*(AIF-\d{3})\s*\|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        raw = cells[6] if len(cells) > 6 else ""
        raw = re.sub(r"\*\*|`", "", raw)[:90]
        out[m.group(1)] = {"raw": raw, "state": work_state(raw)}
    return out


def repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(here, ".git")) and \
           os.path.isfile(os.path.join(here, "AI_README.md")):
            return here
        here = os.path.dirname(here)
    return os.getcwd()


def scan_subsystems(root: str) -> list[dict]:
    """The built pole, SCANNED. No declared list to go stale."""
    subs = []
    for d in sorted(glob.glob(os.path.join(root, "src", "*", ""))):
        name = os.path.basename(d.rstrip(os.sep))
        srcs = [f for f in glob.glob(os.path.join(d, "**", "*"), recursive=True)
                if f.rsplit(".", 1)[-1] in ("cpp", "c", "cc", "cxx")]
        hdrs = [f for f in glob.glob(os.path.join(d, "**", "*"), recursive=True)
                if f.rsplit(".", 1)[-1] in ("hpp", "h", "hh", "inl", "ipp")]
        subs.append({"name": name, "src": len(srcs), "hdr": len(hdrs)})
    return [s for s in subs if s["src"] or s["hdr"]]


def load(root: str) -> dict:
    projects = yaml.safe_load(
        open(os.path.join(root, "labtalk/registries/projects.yaml"), encoding="utf-8")
    )["projects"]

    pf = yaml.safe_load(
        open(os.path.join(root, "labtalk/registries/proofs.yaml"), encoding="utf-8"))
    proofs = pf.get("proofs", [])
    declared = {s["id"] for s in pf.get("proof_states", [])}

    claims = []
    for f in sorted(glob.glob(os.path.join(root, "coordination/aif/AIF-*.claim"))):
        txt = open(f, encoding="utf-8", errors="replace").read()

        def field(k: str) -> str:
            m = re.search(rf"^{k}:\s*(.+)$", txt, re.M)
            return m.group(1).strip() if m else ""

        claims.append({"aif": os.path.basename(f)[:-6], "lane": field("lane"),
                       "member": field("member")})

    # LabTalk surfaces, SCANNED the same way src/ is -- counted, not declared.
    # Owner direction 2026-08-13: the span rests on four piers, and a pier with
    # no data is decoration. These are real directories with real file counts.
    labtalk_areas = []
    for name, rel in (("lessons", "labtalk/lessons"),
                      ("proofs", "labtalk/proofs"),
                      ("registries", "labtalk/registries"),
                      ("ai_portal", "labtalk/ai_portal"),
                      ("portal", "labtalk/portal")):
        n = len([p for p in glob.glob(os.path.join(root, rel, "**", "*"),
                                      recursive=True) if os.path.isfile(p)])
        if n:
            labtalk_areas.append({"name": name, "rel": rel, "files": n})

    intake = load_intake(root)

    return {"projects": projects, "claims": claims, "proofs": proofs,
            "intake": intake,
            "declared_states": declared,
            "subsystems": scan_subsystems(root),
            "labtalk": labtalk_areas,
            "transcripts": len(glob.glob(os.path.join(root, "labtalk/proofs/runs/*"))),
            "dts": len(glob.glob(os.path.join(root, "dottalkpp/data/scripts/**/*.dts"),
                                 recursive=True))}


def join_proofs(data: dict) -> dict:
    """Map proof records onto scanned subsystems. Report what will not map."""
    names = {s["name"] for s in data["subsystems"]}
    by_sub, unmapped = defaultdict(list), []
    for p in data["proofs"]:
        src = (p.get("source") or "").replace("\\", "/")
        hit = None
        m = re.search(r"/(?:src|include)/([A-Za-z0-9_]+)/", src)
        if m and m.group(1) in names:
            hit = m.group(1)
        if not hit:
            for seg in p["id"].split(".")[1:3]:
                if seg in names:
                    hit = seg
                    break
        (by_sub[hit].append(p) if hit else unmapped.append(p))

    undeclared = [(p["id"], p.get("state"))
                  for p in data["proofs"]
                  if p.get("state") not in data["declared_states"]]

    where = Counter()
    for p in data["proofs"]:
        s = (p.get("source") or "").replace("\\", "/")
        if not s.strip():
            where["no source recorded"] += 1
        elif re.search(r"/(src|include)/", s):
            where["engine source"] += 1
        elif "labtalk/proofs/runs" in s:
            where["run transcript"] += 1
        else:
            where["a document"] += 1

    return {"by_sub": by_sub, "unmapped": unmapped,
            "undeclared": undeclared, "where": where}


def build(data: dict, jn: dict) -> dict:
    nodes, kids = {}, {"root": []}

    def add(nid, parent, label, kind, status="", meta=None, note=""):
        nodes[nid] = {"id": nid, "label": label, "kind": kind, "status": status,
                      "meta": meta or {}, "note": note}
        kids.setdefault(parent, []).append(nid)

    for key, p in POLES.items():
        add(f"pole:{key}", "root", p["label"], "pole", "",
            {"tag": p["tag"], "reads": p["reads"]}, p["blurb"])
    # The "reads" line here used to say this was "the panel that can embarrass
    # us". Removed on the owner's rule (2026-08-13): keep a remark like that only
    # if the measurement genuinely warrants it, otherwise it is unprofessional.
    # It does not warrant it. What this panel shows is an INDEXING gap, not a
    # quality one -- most proof artifacts on disk were never registered. Calling
    # that embarrassing both misstates the finding and performs modesty at the
    # reader, who came here to learn something.
    add("pole:bridge", "root", "The bridge", "pole", "",
        {"tag": "measured // how the other four compare",
         "reads": "Read this side to learn how far a claim and its evidence have "
                  "drifted apart -- and which of the two is usually at fault."},
        "A plan and a codebase always disagree somewhat. This panel measures the "
        "distance between them instead of assuming it. It asks one question of "
        "each pier: how much of what is here carries evidence that someone "
        "registered? Where the answer is low, read it first as a statement about "
        "the RECORD KEEPING, and only then about the work -- the two are easy to "
        "confuse and the difference matters.")

    # --- x64base pole -------------------------------------------------------
    add("grp:lifecycles", "pole:x64base", "Lifecycles", "group", "",
        {"count": len(LIFECYCLES)},
        "Five named lifecycles. A bare 'the SDLC' is not sufficient when more than "
        "one could apply.")
    for name, blurb, doc, phases in LIFECYCLES:
        nid = "lc:" + re.sub(r"\W+", "_", name.lower())
        add(nid, "grp:lifecycles", name, "lifecycle",
            "" if os.path.exists(doc) else "charter not found",
            {"doc": doc}, blurb)
        for ph in phases:
            add(f"{nid}:ph:{ph}", nid, ph, "phase", "", {}, "")

    add("grp:promotion", "pole:x64base", "Promotion ladder", "group", "",
        {"count": len(PROMOTION_LEVELS)},
        "The ladder a claim climbs. Never claim a later stage because an earlier "
        "one succeeded.")
    for lvl, mean in PROMOTION_LEVELS:
        n = sum(1 for p in data["proofs"] if p.get("state") == lvl)
        add(f"pl:{lvl}", "grp:promotion", lvl, "level", "",
            {"count": n}, f"{mean} -- {n} registered proof(s) at this rung")

    add("grp:projects", "pole:x64base", "Projects", "group", "",
        {"count": len(data["projects"])},
        "Work is nested three deep: a PROJECT contains LANES, and a lane contains "
        "MILESTONES. The nesting matters because it is what lets a large system be "
        "discussed at the size you happen to need -- a project for direction, a "
        "lane for a piece of work someone owns, a milestone for a thing that can "
        "actually be finished.")
    lane_ix = defaultdict(list)
    for c in data["claims"]:
        lane_ix[c["lane"].lower()].append(c)
    for p in data["projects"]:
        pid = "pr:" + p["id"]
        lanes = p.get("lanes") or []
        add(pid, "grp:projects", p["id"], "project", p.get("status", ""),
            {"kind": p.get("kind", ""), "count": len(lanes)},
            (p.get("notes") or "")[:380])
        for ln in lanes:
            hits = lane_ix.get(ln.lower(), [])
            add(f"{pid}:ln:{ln}", pid, ln, "lane", "",
                {"aif": ", ".join(h["aif"] for h in hits)}, "")

    add("grp:claims", "pole:x64base", "Claimed AIF lanes", "group", "",
        {"count": len(data["claims"])},
        "A lane number is CLAIMED before work starts, so that two people -- or two "
        "AI agents -- cannot pick the same one at the same time. The claim is made "
        "by creating a file that only succeeds if it does not already exist, which "
        "is a small idea with a large consequence: the answer to 'is this number "
        "free?' can never be a stale guess.")
    intake = data.get("intake", {})
    for c in data["claims"]:
        ix = intake.get(c["aif"], {})
        add(f"cl:{c['aif']}", "grp:claims", c["aif"], "claim",
            ix.get("state", "no intake row"),
            {"member": c["member"], "raw": ix.get("raw", "")}, c["lane"])

    # Work state -- the column the map used to ignore.
    buckets = defaultdict(list)
    for aif, ix in sorted(intake.items()):
        buckets[ix["state"]].append((aif, ix["raw"]))
    order = [n for n, _ in WORK_STATE] + ["unclassified"]
    add("grp:workstate", "pole:x64base", "Work state", "group", "",
        {"count": len(intake)},
        f"{len(intake)} intake rows bucketed by the Status column. The claim ledger "
        f"says a lane exists; this says what state it is in.")
    for name in order:
        rows = buckets.get(name, [])
        if not rows:
            continue
        add(f"ws:{name}", "grp:workstate", name, "state", name,
            {"count": len(rows)}, f"{len(rows)} lane(s)")
        for aif, raw in rows:
            add(f"ws:{name}:{aif}", f"ws:{name}", aif, "lane", "", {}, raw)

    # --- dottalkpp pole: SCANNED -------------------------------------------
    subs = data["subsystems"]
    add("grp:engine", "pole:dottalkpp", "Engine subsystems", "group", "",
        {"count": len(subs)},
        f"Scanned from src/*/ at run time -- {len(subs)} directories carrying source.")
    for s in sorted(subs, key=lambda x: -(x["src"] + x["hdr"])):
        pr = jn["by_sub"].get(s["name"], [])
        best = "no proof registered"
        for lvl, _ in reversed(PROMOTION_LEVELS):
            if any(p.get("state") == lvl for p in pr):
                best = lvl
                break
        nid = "sub:" + s["name"]
        add(nid, "grp:engine", s["name"], "subsystem", best,
            {"count": len(pr), "files": f"{s['src']} src / {s['hdr']} hdr"},
            f"{s['src']} source file(s), {s['hdr']} header(s). "
            f"{len(pr)} registered proof(s).")
        for p in pr:
            add(f"{nid}:pf:{p['id']}", nid, p["id"], "proof",
                p.get("state", ""), {}, (p.get("label") or "")[:200])

    # --- labtalk pole: SCANNED ----------------------------------------------
    areas = data.get("labtalk", [])
    lt_total = sum(a["files"] for a in areas)
    add("grp:labtalk", "pole:labtalk", "Campus surfaces", "group", "",
        {"count": len(areas)},
        f"Scanned from labtalk/ at run time -- {len(areas)} surface(s), "
        f"{lt_total} file(s).")
    for a in sorted(areas, key=lambda x: -x["files"]):
        add("lt:" + a["name"], "grp:labtalk", a["name"], "subsystem", "",
            {"count": a["files"], "files": f"{a['files']} files"},
            f"{a['files']} file(s) under {a['rel']}.")

    # --- site pole: DECLARED, and labelled as such --------------------------
    add("grp:site", "pole:site", "Published surfaces", "group", "",
        {"count": 0},
        "NOT SCANNED. The site lives in a separate repository (x64base-site) "
        "that this generator cannot read, so nothing here is measured. Listing "
        "declared names would be the one hand-written literal on a map whose v2 "
        "note says it removed hand-written literals BECAUSE THEY DRIFT. The "
        "honest fix is an export from the site tree into this one -- "
        "tools/reports/regen_site_regression.ps1 already writes cross-tree, so "
        "the precedent exists. Until then this pier reports its own absence.")

    # --- the bridge ---------------------------------------------------------
    covered = [s for s in subs if jn["by_sub"].get(s["name"])]

    # Per-pier coverage. The span rests on four piers, so it reports on four
    # (owner direction 2026-08-13). Two are measured, one is measured and
    # trivially complete, and one cannot be -- and saying which is which IS the
    # measurement. A span that reported only the piers it could reach would be
    # the same overclaim-by-omission this panel exists to catch.
    add("br:piers", "pole:bridge",
        "Proof coverage, per pier", "measure", "", {"count": 4},
        "How much registered proof each pier carries. Read the gaps as facts "
        "about the REGISTRY first and the work second.")
    add("br:pier:x64base", "br:piers",
        f"x64base -- {len(data['projects'])} projects, {len(data['claims'])} claims declared",
        "measure", "", {"count": len(data["projects"])},
        "Declared intent. Coverage here means a lane exists and is claimed, not "
        "that anything is built.")
    add("br:pier:dottalkpp", "br:piers",
        f"DotTalk++ -- {len(covered)} of {len(subs)} subsystems carry a registered proof",
        "measure", "", {"count": len(covered)},
        "The number that reads worst and means least without its companion "
        "below: the engine is not unproven, the index is aimed elsewhere.")
    add("br:pier:labtalk", "br:piers",
        f"LabTalk -- {lt_total} files across {len(areas)} surfaces",
        "measure", "", {"count": lt_total},
        "The campus holds the proof DOCUMENTS the registry indexes, so it is "
        "both a pier and the filing cabinet the bridge reads from.")
    add("br:pier:site", "br:piers",
        "x64base.com -- 0 proof records, and 0 is not a finding",
        "defect", "", {"count": 0},
        "The site carries no registered proof at all. That is not evidence the "
        "site is unproven; it is evidence that NOTHING IN THIS REGISTRY POINTS "
        "AT IT, because the generator cannot see that repository. The zero is "
        "the absence of a measurement, not a measurement of absence -- and it "
        "is shown rather than omitted so the distinction stays visible.")
    add("br:coverage", "pole:bridge",
        f"{len(covered)} of {len(subs)} subsystems carry a registered proof",
        "measure", "", {"count": len(covered)},
        "How much of the built code has evidence filed against it in the proof "
        "registry. Read the remainder carefully: a subsystem showing 'no proof "
        "registered' means NOBODY FILED A RECORD, which is not the same as "
        "nobody testing it. The two readings differ enormously and only one of "
        "them is supported by this number. The measure directly below shows why.")
    add("br:elsewhere", "pole:bridge",
        f"{data['transcripts']} transcripts and {data['dts']} .dts scripts exist",
        "measure", "", {},
        "Test scripts and recorded runs sitting on disk that the registry does "
        "not point at. Compare this count with the one above and the real "
        "situation appears: the testing largely happened, and the FILING did "
        "not keep up with it. That is an ordinary condition in a fast-moving "
        "project, and it is worth publishing rather than hiding, because a "
        "coverage number read without it says something untrue.")
    for k, v in jn["where"].most_common():
        add(f"br:w:{k}", "pole:bridge", f"{v} proof records point at {k}", "measure",
            "", {"count": v}, "")
    ix = data.get("intake", {})
    unc = [a for a, v in ix.items() if v["state"] == "unclassified"]
    add("br:ledger", "pole:bridge",
        f"{len(data['claims'])} claimed lanes against {len(ix)} intake rows",
        "measure", "", {"count": len(ix)},
        "A claim is atomic; an intake row is prose. Rows without a claim are "
        "pre-coordination, which the collision gate already reports as advisory.")
    add("br:vocab", "pole:bridge",
        f"{len(set(v['raw'] for v in ix.values()))} distinct Status strings across "
        f"{len(ix)} rows",
        "defect" if len(unc) else "measure", "", {"count": len(unc)},
        "The Status column is free text, not a vocabulary -- the same "
        "underscore/hyphen split already found in proofs.yaml. "
        + (f"{len(unc)} row(s) bucket to 'unclassified' and are listed under Work state."
           if unc else "All rows bucket."))

    add("br:unmapped", "pole:bridge",
        f"{len(jn['unmapped'])} of {len(data['proofs'])} proof records map to no subsystem",
        "measure", "", {"count": len(jn["unmapped"])},
        "Not every proof is about code. Many of these record process, "
        "documentation or coordination results, which have no source directory "
        "to attach to. They are listed rather than dropped, because a join that "
        "silently discards what it cannot match will always look tidier than the "
        "thing it is describing.")
    for p in jn["unmapped"]:
        add(f"br:um:{p['id']}", "br:unmapped", p["id"], "proof",
            p.get("state", ""), {}, (p.get("label") or "")[:160])
    if jn["undeclared"]:
        add("br:undeclared", "pole:bridge",
            f"{len(jn['undeclared'])} proof(s) carry a state not in the declared vocabulary",
            "defect", "", {"count": len(jn["undeclared"])},
            "Found by this join. The header block in proofs.d/_header.yaml is the "
            "vocabulary; these records are outside it, in two different spellings.")
        for pid, st in jn["undeclared"]:
            add(f"br:ud:{pid}", "br:undeclared", pid, "defect", st, {},
                f"state '{st}' is not declared")

    return {"nodes": nodes, "kids": kids, "sclass": STATUS_CLASS}


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>x64base ecoschema -- drill-down map</title>
<style>
:root{--bg:#0d1117;--pan:#151b23;--pan2:#1b232d;--line:#2a3441;--tx:#d7e0ea;
--dim:#8b98a8;--acc:#5eb0ef;--acc2:#f0b429;--ok:#5dd39e;--warn:#e8834a;--bad:#f2777a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
header{padding:18px 22px;border-bottom:1px solid var(--line);
display:flex;gap:18px;align-items:baseline;flex-wrap:wrap}
h1{font-size:16px;margin:0}
.sub{color:var(--dim);font-size:12px}
#crumbs{padding:10px 22px;border-bottom:1px solid var(--line);
color:var(--dim);font-size:12px;display:flex;gap:6px;flex-wrap:wrap}
#crumbs b{color:var(--acc);cursor:pointer}
#crumbs b:hover{text-decoration:underline}
#search{margin-left:auto;background:var(--pan);border:1px solid var(--line);
color:var(--tx);padding:6px 10px;border-radius:4px;font:inherit;min-width:230px}
main{padding:20px 22px 60px}
/* Owner direction 2026-08-13: the bridge is a SPAN, so it lies horizontally
   across the top and the four piers stand under it. The previous layout put it
   in the middle column of three, which read as a third pole rather than as the
   thing connecting them. */
.span{margin-bottom:14px}
.span .pole{border-color:var(--acc2)}
.piers{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
@media(max-width:1100px){.piers{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.piers{grid-template-columns:1fr}}
.pole{background:var(--pan);border:1px solid var(--line);border-radius:8px;padding:20px;
cursor:pointer;transition:.15s}
.pole:hover{border-color:var(--acc);transform:translateY(-2px)}
.pole h2{margin:0 0 4px;font-size:22px;color:var(--acc)}
.pole.mid h2{color:var(--acc2)}
.pole .tag{color:var(--acc2);font-size:12px;margin-bottom:12px}
.pole.mid .tag{color:var(--acc)}
.pole p{color:var(--dim);margin:0 0 12px}
.pole .reads{color:var(--tx);font-size:12px;border-left:2px solid var(--acc);padding-left:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}
.card{background:var(--pan);border:1px solid var(--line);border-radius:6px;padding:14px;
cursor:pointer;transition:.12s}
.card:hover{border-color:var(--acc);background:var(--pan2)}
.card.leaf{cursor:default}.card.leaf:hover{border-color:var(--line)}
.card h3{margin:0 0 6px;font-size:13px;word-break:break-word}
.card .k{font-size:11px;color:var(--acc);text-transform:uppercase;letter-spacing:.06em}
.card .n{font-size:12px;color:var(--dim);margin-top:7px}
.badge{display:inline-block;font-size:10px;padding:2px 7px;border-radius:10px;
border:1px solid var(--line);color:var(--dim);margin:6px 6px 0 0}
.s-beta{color:var(--ok);border-color:var(--ok)}
.s-active{color:var(--acc);border-color:var(--acc)}
.s-seed{color:var(--acc2);border-color:var(--acc2)}
.s-plan{color:var(--dim)}
.s-proto{color:var(--warn);border-color:var(--warn)}
.s-pub{color:var(--acc);border-color:var(--acc)}
.card .k.defect,.badge.defect{color:var(--bad);border-color:var(--bad)}
.count{float:right;color:var(--dim);font-size:11px}
.empty{color:var(--dim);padding:30px;text-align:center}
footer{padding:14px 22px;border-top:1px solid var(--line);color:var(--dim);font-size:11px}
footer a,.home{color:var(--acc);text-decoration:none}
footer a:hover,.home:hover{text-decoration:underline}
.home{font-size:12px;white-space:nowrap}
</style>
</head>
<body>
<header>
  <a class="home" href="https://x64base.com/">&larr; x64base.com</a>
  <h1>x64base &mdash; ecoschema drill-down</h1>
  <span class="sub">GENERATED &middot; __NP__ projects &middot; __NL__ lanes &middot; __NC__ claims &middot; __NS__ subsystems scanned &middot; __NPF__ proof records</span>
  <input id="search" placeholder="filter (searches every level)">
</header>
<div id="crumbs"></div>
<main id="view"></main>
<footer>Generated by <code>tools/fullstack_docs/ecoschema_map.py</code> from
<code>projects.yaml</code>, <code>proofs.yaml</code>, <code>coordination/aif/*.claim</code>
and a scan of <code>src/*/</code>. Do not hand-edit; re-run the generator.
<br><a href="https://x64base.com/">Return to x64base.com</a> &middot;
<a href="https://x64base.com/docs">Documentation</a> &middot;
<a href="https://x64base.com/products">Products</a></footer>
<script>
const D = __DATA__;
let path = ["root"];
const label = id => id==="root" ? "root" : (D.nodes[id] ? D.nodes[id].label : id);

function crumbs(){
  const c=document.getElementById("crumbs"); c.innerHTML="";
  path.forEach((id,i)=>{
    const b=document.createElement("b"); b.textContent=label(id);
    b.onclick=()=>{path=path.slice(0,i+1);render();}; c.appendChild(b);
    if(i<path.length-1){const s=document.createElement("span");s.textContent="/";c.appendChild(s);}
  });
}
function poles(){
  const mk=(id,cls)=>{const n=D.nodes[id];return `<div class="pole ${cls||''}" onclick="go('${id}')">
    <h2>${n.label}</h2><div class="tag">${n.meta.tag}</div>
    <p>${n.note}</p><div class="reads">${n.meta.reads}</div></div>`;};
  // The span first, full width, then the piers under it. Selected by ID rather
  // than by index: the old code read k[0]/k[2]/k[1] positionally, which silently
  // reorders the moment a pole is added -- and a pole was added.
  const k=D.kids["root"];
  const piers=k.filter(id=>id!=="pole:bridge");
  document.getElementById("view").innerHTML=
    `<div class="span">${mk("pole:bridge","mid")}</div>` +
    `<div class="piers">${piers.map(id=>mk(id)).join("")}</div>`;
}
function go(id){path.push(id);render();}
function cards(id){
  const v=document.getElementById("view"), ch=D.kids[id]||[];
  if(!ch.length){v.innerHTML='<div class="empty">leaf &mdash; nothing below this</div>';return;}
  v.innerHTML='<div class="grid">'+ch.map(cid=>{
    const n=D.nodes[cid], nk=(D.kids[cid]||[]).length, def=n.kind==="defect";
    const st=n.status?`<span class="badge ${def?'defect':(D.sclass[n.status]||'')}">${n.status}</span>`:"";
    const fl=n.meta.files?`<span class="badge">${n.meta.files}</span>`:"";
    const kd=n.meta.kind?`<span class="badge">${n.meta.kind}</span>`:"";
    const af=n.meta.aif?`<span class="badge s-active">${n.meta.aif}</span>`:"";
    const mb=n.meta.member?`<span class="badge">${n.meta.member}</span>`:"";
    return `<div class="card ${nk?'':'leaf'}" ${nk?`onclick="go('${cid}')"`:''}>
      <div class="k ${def?'defect':''}">${n.kind}${nk?`<span class="count">${nk}</span>`:''}</div>
      <h3>${n.label}</h3>${n.note?`<div class="n">${n.note}</div>`:''}
      ${st}${fl}${kd}${af}${mb}</div>`;}).join("")+'</div>';
}
function render(){crumbs();const c=path[path.length-1];c==="root"?poles():cards(c);}
document.getElementById("search").addEventListener("input",e=>{
  const q=e.target.value.trim().toLowerCase();
  if(!q){render();return;} crumbs();
  const hits=Object.values(D.nodes).filter(n=>
    (n.label+" "+n.note+" "+(n.meta.aif||"")+" "+n.status).toLowerCase().includes(q));
  document.getElementById("view").innerHTML='<div class="grid">'+hits.slice(0,300).map(n=>{
    const nk=(D.kids[n.id]||[]).length;
    return `<div class="card ${nk?'':'leaf'}" ${nk?`onclick="path=['root'];go('${n.id}')"`:''}>
      <div class="k">${n.kind}</div><h3>${n.label}</h3>
      ${n.note?`<div class="n">${n.note}</div>`:''}
      ${n.status?`<span class="badge ${D.sclass[n.status]||''}">${n.status}</span>`:''}</div>`;
  }).join("")+'</div>';
});
render();
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate the ecoschema drill-down map.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = repo_root()
    os.chdir(root)
    data = load(root)
    jn = join_proofs(data)
    built = build(data, jn)

    built = scrub_tree(built)

    nl = sum(len(p.get("lanes") or []) for p in data["projects"])
    out = args.out or os.path.join(root, "docs/maintenance/ECOSCHEMA_MAP_V1.html")
    doc = (TEMPLATE.replace("__DATA__", json.dumps(built))
           .replace("__NP__", str(len(data["projects"])))
           .replace("__NL__", str(nl))
           .replace("__NC__", str(len(data["claims"])))
           .replace("__NS__", str(len(data["subsystems"])))
           .replace("__NPF__", str(len(data["proofs"]))))
    # Refuse to emit a leaking file. A scrub nobody checks is a scrub that stops
    # working the first time a note names a new path.
    leaks = [m for m in ANY_LOCAL_PATH.findall(doc) if not m.startswith("<")]
    if leaks:
        print("ecoschema-map: REFUSING to write -- local machine path(s) survived "
              "the scrub: " + ", ".join(sorted(set(leaks))[:5]), file=sys.stderr)
        return 2

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    covered = len([s for s in data["subsystems"] if jn["by_sub"].get(s["name"])])
    print(f"ecoschema-map: wrote {os.path.relpath(out, root)}")
    print(f"  projects {len(data['projects'])} | lanes {nl} | claims {len(data['claims'])}")
    print(f"  subsystems scanned {len(data['subsystems'])} | proof records {len(data['proofs'])}")
    print(f"  BRIDGE: {covered}/{len(data['subsystems'])} subsystems carry a registered proof")
    print(f"          {len(jn['unmapped'])}/{len(data['proofs'])} proof records map to no subsystem")
    print(f"          proof records point at: " +
          ", ".join(f"{k}={v}" for k, v in jn["where"].most_common()))
    print(f"          on disk but unindexed: {data['transcripts']} transcripts, "
          f"{data['dts']} .dts scripts")
    if jn["undeclared"]:
        print(f"  DEFECT: {len(jn['undeclared'])} proof(s) carry an undeclared state:")
        for pid, st in jn["undeclared"]:
            print(f"          '{st}' <- {pid}")
    print(f"  nodes {len(built['nodes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
