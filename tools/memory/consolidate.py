#!/usr/bin/env python3
"""consolidate.py -- Frontal_Mem triage / consolidation value function (Lane 2 M2 core).

The thesis's "heart of it" as running code. Given a session's working-set of candidate
memories, score each on the five value signals, apply a promotion threshold tuned by the
domain's cost-asymmetry, and emit a HYBRID promotion proposal: the agent PROPOSES, the owner
CONFIRMS. Dependency-free (stdlib only).

By design this tool does NOT write to the durable store. Promotion into Lane 1 (the attributed
BBS/DBF post path, AIF-075) is a separate, confirmed adapter step. The judgment (what is worth
keeping) is decoupled from the storage (where it goes), so the same value function serves the
future C++ `PSEUDO PROMOTE` (Lane 2) and the Ollama-chat promotion (Lane 3).

References:
  Frontal_Mem thesis Section 4  -- the triage value function (acted-on, costly-to-learn,
                                   re-referenced, contradiction, novelty; deferred "sleep";
                                   over- vs under-promotion asymmetry).
  DESIGN_bbs_pseudochat_two_lanes.md -- hybrid promotion, normalize-on-collect, grandfather.
  PLAN_pseudochat_lane.md, M2 -- the milestone this realizes.

Subcommands:
  propose   score a working-set and emit a promotion proposal (agent proposes)
  confirm   apply owner decisions to a proposal, emit a to-write manifest (owner confirms)
  weights   print the default value-function weights and thresholds
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

# --- value function -----------------------------------------------------------------------

# Weights sum to 1.0. "acted_on" leads because reasoning that moved something is the strongest
# proxy for future value (thesis 4.2); "costly-to-learn" is next because its value is exactly
# the cost of rediscovering it (the one-hour lesson).
DEFAULT_WEIGHTS = {
    "acted_on": 0.30,
    "cost_to_learn": 0.25,
    "referenced": 0.15,
    "contradiction": 0.15,
    "novelty": 0.15,
}

COST_SATURATION_MIN = 60.0   # an hour to (re)learn saturates the cost-to-learn signal
REF_SATURATION = 3.0         # three or more recalls saturate the re-referenced signal

BASE_PROMOTE = 0.55
BASE_DISCARD = 0.30

# thesis 4.4: the two errors are not symmetric, so the threshold is a tuning parameter set with
# the domain's cost asymmetry in view. A positive bias raises both bars (over-promotion is the
# graver sin -- a small, trusted store); a negative bias lowers them (under-promotion is graver
# -- where re-learning is expensive).
DOMAIN_BIAS = {
    "small_trusted_store": 0.10,
    "balanced": 0.0,
    "expensive_relearn": -0.10,
}


def clamp(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def normalize_signals(sig):
    """Map raw evidence to five 0..1 signals."""
    return {
        "acted_on": 1.0 if sig.get("acted_on") else 0.0,
        "cost_to_learn": clamp(float(sig.get("cost_to_learn_min", 0) or 0) / COST_SATURATION_MIN),
        "referenced": clamp(float(sig.get("references", 0) or 0) / REF_SATURATION),
        "contradiction": 1.0 if sig.get("contradicts") not in (None, "", False) else 0.0,
        "novelty": clamp(float(sig.get("novelty", 0.0) or 0.0)),
    }


def score_candidate(sig, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    norm = normalize_signals(sig)
    total = sum(weights[k] * norm[k] for k in weights)
    return round(total, 4), norm


def decide(total, bias=0.0):
    promote_at = BASE_PROMOTE + bias
    discard_at = BASE_DISCARD + bias
    if total >= promote_at:
        return "PROMOTE"
    if total <= discard_at:
        return "DISCARD"
    return "HOLD"


def reason(norm, weights=None):
    """Name the two signals that contributed most to the score."""
    weights = weights or DEFAULT_WEIGHTS
    contrib = sorted(((weights[k] * norm[k], k) for k in weights), reverse=True)
    top = [k for v, k in contrib if v > 0.0][:2]
    if not top:
        return "no positive signal"
    return "driven by " + " + ".join(top)


# --- normalize on collect (dedupe + contradiction flag) -----------------------------------

def dedupe_key(cand):
    key = cand.get("dedupe_key")
    if key:
        return str(key).strip().lower()
    return " ".join(str(cand.get("summary", "")).split()).strip().lower()


def normalize_on_collect(scored):
    """Collapse duplicates (keep the highest-scoring), surface contradictions. Compression is
    itself a kind of forgetting: drop redundancy, keep the canonical claim (design note)."""
    best = {}
    dropped = 0
    for c in scored:
        k = dedupe_key(c)
        if k in best:
            dropped += 1
            if c["score"] > best[k]["score"]:
                best[k] = c
        else:
            best[k] = c
    return list(best.values()), dropped


# --- proposal -----------------------------------------------------------------------------

def build_proposal(workingset, weights=None, bias_name="balanced"):
    weights = weights or DEFAULT_WEIGHTS
    bias = DOMAIN_BIAS.get(bias_name, 0.0)
    session = workingset.get("session", {})
    scored = []
    for cand in workingset.get("candidates", []):
        total, norm = score_candidate(cand.get("signals", {}), weights)
        decision = decide(total, bias)
        contradicts = cand.get("signals", {}).get("contradicts")
        # superseded items are demotions regardless of raw score (thesis 5.2 supersedes)
        if cand.get("superseded_by"):
            decision, note = "DISCARD", "superseded by " + str(cand["superseded_by"])
        else:
            note = reason(norm, weights)
        scored.append({
            "id": cand.get("id"),
            "class": cand.get("class"),
            "summary": cand.get("summary"),
            "score": total,
            "decision": decision,
            "reason": note,
            "signals": norm,
            "needs_reconsolidation": bool(contradicts),   # thesis 5.5: never silently pick
            "contradicts": contradicts,
            "links": cand.get("links", []),
            "provenance": {
                "session": session.get("id"),
                "agent": session.get("agent"),
                "date": session.get("date"),
                "project": session.get("project"),
                "source_lane": cand.get("source_lane", session.get("source_lane", "session")),
            },
        })
    kept, dropped = normalize_on_collect(scored)
    kept.sort(key=lambda c: c["score"], reverse=True)
    counts = {"PROMOTE": 0, "HOLD": 0, "DISCARD": 0}
    for c in kept:
        counts[c["decision"]] += 1
    return {
        "schema": "frontal-mem-triage-proposal-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": session,
        "config": {"weights": weights, "domain_bias": bias_name, "bias": bias,
                   "promote_at": round(BASE_PROMOTE + bias, 3),
                   "discard_at": round(BASE_DISCARD + bias, 3)},
        "counts": counts,
        "duplicates_collapsed": dropped,
        "candidates": kept,
    }


def recall_stub(cand):
    cid = str(cand.get("id", "mem")).lower().replace(" ", "_")
    return {
        "id": "mem." + cid,
        "label": cand.get("summary", cid),
        "class": {"semantic": "semantic", "episodic": "episodic",
                  "procedural": "procedural"}.get(cand.get("class"), "semantic"),
        "enforced_by": None, "hard_fails": False, "tier": 2,
    }


# --- confirm (owner authority) ------------------------------------------------------------

def confirm(proposal, decisions):
    """Hybrid promotion: keep only items the owner approved. Confirmation is itself a signal
    (thesis 4.5) -- recorded here so an autonomous share can be learned later."""
    out = []
    for c in proposal.get("candidates", []):
        verdict = decisions.get(c["id"])
        if verdict == "approve" and c["decision"] in ("PROMOTE", "HOLD"):
            item = dict(c)
            item["owner_confirmed"] = True
            out.append(item)
    return {
        "schema": "frontal-mem-triage-manifest-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": proposal.get("session", {}),
        "to_write": out,
        "note": "Owner-confirmed set. Actual write to Lane 1 (attributed BBS/DBF post path) is a "
                "separate adapter step; this manifest is the input to it.",
    }


# --- cli ----------------------------------------------------------------------------------

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _emit(obj, out):
    text = json.dumps(obj, indent=2)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _print_table(proposal):
    print("triage proposal  promote_at=%(promote_at)s discard_at=%(discard_at)s bias=%(domain_bias)s"
          % proposal["config"], file=sys.stderr)
    for c in proposal["candidates"]:
        flag = " [contradiction]" if c["needs_reconsolidation"] else ""
        print("  %-8s %.3f  %-26s %s%s" % (c["decision"], c["score"], c["id"], c["reason"], flag),
              file=sys.stderr)
    print("  counts: %s  duplicates_collapsed=%d"
          % (proposal["counts"], proposal["duplicates_collapsed"]), file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("propose", help="score a working-set and emit a promotion proposal")
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--bias", default="balanced", choices=sorted(DOMAIN_BIAS))
    p.add_argument("--emit-recall", action="store_true",
                   help="also print recall-graph node stubs for PROMOTE items")
    p.add_argument("--quiet", action="store_true")

    c = sub.add_parser("confirm", help="apply owner decisions, emit a to-write manifest")
    c.add_argument("--proposal", required=True)
    c.add_argument("--decisions", required=True, help="JSON map {candidate_id: approve|reject}")
    c.add_argument("--out", default=None)

    sub.add_parser("weights", help="print default weights and thresholds")

    args = ap.parse_args(argv)

    if args.cmd == "weights":
        _emit({"weights": DEFAULT_WEIGHTS, "base_promote": BASE_PROMOTE,
               "base_discard": BASE_DISCARD, "domain_bias": DOMAIN_BIAS,
               "cost_saturation_min": COST_SATURATION_MIN, "ref_saturation": REF_SATURATION}, None)
        return 0

    if args.cmd == "propose":
        ws = _load(args.infile)
        proposal = build_proposal(ws, bias_name=args.bias)
        if not args.quiet:
            _print_table(proposal)
        if args.emit_recall:
            stubs = [recall_stub(c) for c in proposal["candidates"] if c["decision"] == "PROMOTE"]
            proposal["recall_stubs"] = stubs
        _emit(proposal, args.out)
        return 0

    if args.cmd == "confirm":
        proposal = _load(args.proposal)
        decisions = _load(args.decisions)
        _emit(confirm(proposal, decisions), args.out)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
