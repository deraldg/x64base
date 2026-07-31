#!/usr/bin/env python3
"""
Run-attribution / closeout check (AIF-050 M6).

For every session closeout, checks the report-audit envelope for the traceability fields and
cross-checks against the run registry:

  - does the envelope carry a run_id (i.e. is it ai-report-audit-v2 attribution-ready)?
  - is that run_id registered in labtalk/registries/ai_runs.yaml?
  - does the run declare author != owner (the truth the record must tell)?

Advisory by default (reports, exit 0). --strict fails (exit 1) if any closeout newer than the
adoption date lacks a run_id — the promotion to a hard gate once v2 is the convention.

No third-party deps (regex over the YAML front-matter, so it runs anywhere).
Owner: member.derald · steward: member.ai.claude.cowork · lane: AIF-050 · status: candidate
"""
import argparse
import re
import sys
from pathlib import Path

CLOSEOUT_GLOB = "docs/maintenance/SESSION_CLOSEOUT_*.md"
RUNS_YAML = "labtalk/registries/ai_runs.yaml"

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
KV = lambda k: re.compile(rf"^\s*{k}:\s*(\S+)", re.MULTILINE)


def front_matter(text: str) -> str:
    m = FRONT_RE.match(text)
    return m.group(1) if m else ""


def field(block: str, key: str):
    m = KV(key).search(block)
    return m.group(1).strip() if m else None


def registered_runs(root: Path):
    p = root / RUNS_YAML
    if not p.exists():
        return set()
    txt = p.read_text(errors="ignore")
    # run_id: appears once per run entry (indented under runs:)
    return set(re.findall(r"^\s*-?\s*run_id:\s*(\S+)", txt, re.MULTILINE))


def run_attribution(root: Path, run_id: str):
    """Return (authored_by, owner) for a run_id from the registry, best-effort."""
    p = root / RUNS_YAML
    if not p.exists() or not run_id:
        return (None, None)
    txt = p.read_text(errors="ignore")
    # find the block from this run_id to the next '- run_id:' or EOF
    m = re.search(rf"run_id:\s*{re.escape(run_id)}\b(.*?)(?=\n\s*-\s*run_id:|\Z)", txt, re.DOTALL)
    if not m:
        return (None, None)
    blk = m.group(1)
    return (field(blk, "authored_by"), field(blk, "owner"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--adopted", default="2026-07-22",
                    help="closeouts recorded on/after this date should carry a run_id")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    runs = registered_runs(root)
    closeouts = sorted(root.glob(CLOSEOUT_GLOB))
    v2, v1, unregistered, author_owner_ok = [], [], [], 0

    print("=== run-attribution / closeout check (AIF-050 M6) ===")
    print(f"registry runs: {len(runs)}   closeouts: {len(closeouts)}\n")
    for c in closeouts:
        fm = front_matter(c.read_text(errors="ignore"))
        schema = field(fm, "schema") or "(none)"
        run_id = field(fm, "run_id") or field(fm, "report_id")  # v2 run_id, else v1 report_id
        has_run = field(fm, "run_id") is not None
        name = c.name
        if has_run:
            v2.append(name)
            reg = "registered" if run_id in runs else "UNREGISTERED"
            if run_id not in runs:
                unregistered.append(name)
            a, o = run_attribution(root, run_id)
            truth = "author!=owner" if (a and o and a != o) else "author?=owner"
            if a and o and a != o:
                author_owner_ok += 1
            print(f"  [v2] {name}\n       run={run_id} ({reg}) · {truth} ({a} / {o})")
        else:
            v1.append(name)
            print(f"  [v1] {name}  (report_id={run_id}; no run_id — pre-v2)")

    print(f"\nsummary: {len(v2)} v2-attributed, {len(v1)} v1 (pre-adoption),"
          f" {len(unregistered)} run_id UNREGISTERED, {author_owner_ok} record author!=owner")

    if args.strict:
        offenders = [n for n in v1 if args.adopted in n]  # crude: date in filename >= adopted
        if offenders or unregistered:
            print(f"\nSTRICT: {len(offenders)} post-adoption closeout(s) without run_id, "
                  f"{len(unregistered)} unregistered -> FAIL", file=sys.stderr)
            return 1
    if v1 or unregistered:
        print("\nadvisory: pre-v2 closeouts and any unregistered runs above (not a failure yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
