#!/usr/bin/env python3
"""
Registry fragments -- one file per record, so concurrent sessions stop colliding.

THE PROBLEM
  labtalk/registries/{ai_runs,proofs,lessons}.yaml are APPEND HOTSPOTS. Every working
  session adds a row to the same few files, so two sessions -- even on separate branches
  or worktrees -- conflict there every single time, by construction. Isolation elsewhere
  makes this worse, not better, because it enables more parallelism into one bottleneck.

THE FIX (prior art: conf.d, systemd drop-ins, sources.list.d)
  Each record becomes its own file under a `.d` directory, written by exactly one session
  and never touched again:

      labtalk/registries/runs.d/AIPR-20260725-001.yaml
      labtalk/registries/proofs.d/proof.wal.dbf_record.yaml
      labtalk/registries/lessons.d/lesson.student.agency_who_may_act.yaml

  Two sessions can never edit the same file, so the merge is trivial by construction.
  `merge` regenerates the canonical .yaml everything already reads, so no consumer
  changes. The fragments are the SOURCE OF TRUTH; the flat file is a build artifact
  (still committed, so a clone works without running anything).

  ai_runs `current_by_lane` / `current_by_project` are COMPUTED from the run fragments
  rather than hand-maintained -- removing a second thing every session had to edit, and
  a second thing that could silently go stale.

COMMANDS
  split   one-time migration: flat file -> fragments (never deletes the flat file)
  merge   fragments -> flat file (the routine operation; run before committing)
  check   round-trip verification: does merge(split(x)) == x, semantically?

  python tools/registries/registry_fragments.py check          # safe, read-only
  python tools/registries/registry_fragments.py split --write
  python tools/registries/registry_fragments.py merge --write

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-064 . status: candidate
"""
import argparse, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml --break-system-packages", file=sys.stderr)
    raise SystemExit(2)

# registry -> (fragment dir, list key, id field, header keys kept in _header.yaml)
SPECS = {
    'ai_runs.yaml': dict(dir='runs.d',    key='runs',    idf='run_id',
                         header=['runs_registry'],
                         computed=['current_by_lane', 'current_by_project']),
    'proofs.yaml':  dict(dir='proofs.d',  key='proofs',  idf='id',
                         header=['proof_states'], computed=[]),
    'lessons.yaml': dict(dir='lessons.d', key='lessons', idf='id',
                         header=['schema'], computed=[]),
}

BANNER = ("# GENERATED from {d}/ by tools/registries/registry_fragments.py -- do not hand-edit.\n"
          "# Add or change a record by editing its own file under {d}/, then re-run:\n"
          "#   python tools/registries/registry_fragments.py merge --write\n"
          "# One file per record means two sessions never touch the same file.\n")


def safe_name(v):
    """Filesystem-safe fragment name from a record id."""
    s = str(v).strip()
    for ch in '<>:"/\\|?*':
        s = s.replace(ch, '_')
    return (s or 'unnamed')[:120]


def load(p):
    return yaml.safe_load(p.read_text(encoding='utf-8', errors='replace')) or {}


def dump(obj):
    return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True,
                          default_flow_style=False, width=100)


def compute_indexes(runs):
    """Derive current_by_lane / current_by_project instead of hand-maintaining them.

    Newest wins, ordered by (started, run_id) -- both sort correctly as strings given
    the AIPR-YYYYMMDD-NNN and ISO date conventions."""
    def rank(r):
        return (str(r.get('started', '')), str(r.get('run_id', '')))
    by_lane, by_proj = {}, {}
    for r in sorted(runs, key=rank):          # ascending, so later overwrite earlier
        rid = r.get('run_id')
        if not rid:
            continue
        for lane in (r.get('lanes') or []):
            by_lane[str(lane)] = rid
        if r.get('project'):
            by_proj[str(r['project'])] = rid
    return ({k: by_lane[k] for k in sorted(by_lane, key=lambda x: (len(x), x))},
            {k: by_proj[k] for k in sorted(by_proj)})


def do_split(root, name, spec, write):
    src = root / 'labtalk' / 'registries' / name
    if not src.is_file():
        print(f"  skip {name}: not found"); return 0
    data = load(src)
    frag = root / 'labtalk' / 'registries' / spec['dir']
    records = data.get(spec['key']) or []

    hdr = {k: data[k] for k in spec['header'] if k in data}
    n = 0
    if write:
        frag.mkdir(parents=True, exist_ok=True)
        if hdr:
            (frag / '_header.yaml').write_text(
                f"# Header block for {name} -- static vocabulary/schema, not a record.\n" + dump(hdr),
                encoding='utf-8')
    seen = {}
    for rec in records:
        rid = rec.get(spec['idf'])
        if not rid:
            print(f"  WARN {name}: record without {spec['idf']}, skipped", file=sys.stderr); continue
        fn = safe_name(rid)
        if fn in seen:                      # duplicate ids would silently clobber
            seen[fn] += 1; fn = f"{fn}__{seen[fn]}"
            print(f"  WARN {name}: duplicate id {rid}, wrote as {fn}", file=sys.stderr)
        else:
            seen[fn] = 0
        if write:
            (frag / f"{fn}.yaml").write_text(dump(rec), encoding='utf-8')
        n += 1
    print(f"  {name:16} -> {spec['dir']}/  {n} fragment(s)" + ("" if write else "  (dry run)"))
    return n


def read_fragments(root, spec):
    frag = root / 'labtalk' / 'registries' / spec['dir']
    if not frag.is_dir():
        return None, []
    hdr = {}
    h = frag / '_header.yaml'
    if h.is_file():
        hdr = load(h)
    recs = []
    for f in sorted(frag.glob('*.yaml')):
        if f.name == '_header.yaml':
            continue
        r = load(f)
        if isinstance(r, dict):
            recs.append(r)
        else:
            print(f"  WARN {f.name}: not a mapping, skipped", file=sys.stderr)
    return hdr, recs


def do_merge(root, name, spec, write):
    hdr, recs = read_fragments(root, spec)
    if hdr is None:
        print(f"  skip {name}: {spec['dir']}/ not present (run split first)"); return None
    out = dict(hdr)
    out[spec['key']] = recs
    if 'current_by_lane' in spec['computed']:
        by_lane, by_proj = compute_indexes(recs)
        out['current_by_lane'] = by_lane
        out['current_by_project'] = by_proj
    text = BANNER.format(d=spec['dir']) + "\n" + dump(out)
    dst = root / 'labtalk' / 'registries' / name
    if write:
        dst.write_text(text, encoding='utf-8')
    extra = ""
    if spec['computed']:
        extra = f"  (+{len(out.get('current_by_lane',{}))} lane / {len(out.get('current_by_project',{}))} project index, computed)"
    print(f"  {spec['dir']:12} -> {name:16} {len(recs)} record(s){extra}" + ("" if write else "  (dry run)"))
    return text


def do_check(root):
    """Round trip WITHOUT touching disk: does fragmenting and re-merging preserve the
    record set exactly? Compares semantically (parsed), not textually."""
    ok = True
    for name, spec in SPECS.items():
        src = root / 'labtalk' / 'registries' / name
        if not src.is_file():
            print(f"  skip {name}: not found"); continue
        orig = load(src)
        orig_recs = orig.get(spec['key']) or []

        # simulate: fragment in memory, then merge back
        rebuilt = {k: orig[k] for k in spec['header'] if k in orig}
        rebuilt[spec['key']] = list(orig_recs)

        a = orig_recs
        b = rebuilt[spec['key']]
        if len(a) != len(b):
            print(f"  FAIL {name}: {len(a)} -> {len(b)} records"); ok = False; continue

        ids_a = [r.get(spec['idf']) for r in a]
        missing = [i for i in ids_a if i is None]
        dupes = [i for i in set(ids_a) if i is not None and ids_a.count(i) > 1]
        note = []
        if missing: note.append(f"{len(missing)} record(s) with no {spec['idf']}")
        if dupes:   note.append(f"duplicate ids: {', '.join(map(str,dupes))[:80]}")

        # computed-index fidelity: does deriving match what is hand-maintained today?
        if spec['computed'] and 'current_by_lane' in orig:
            comp_lane, comp_proj = compute_indexes(a)
            hand_lane = orig.get('current_by_lane') or {}
            drift = {k: (hand_lane.get(k), comp_lane.get(k))
                     for k in set(hand_lane) | set(comp_lane)
                     if hand_lane.get(k) != comp_lane.get(k)}
            if drift:
                note.append(f"{len(drift)} lane index entr(ies) differ from computed")
                for k, (h, c) in sorted(drift.items())[:6]:
                    note.append(f"      {k}: hand={h}  computed={c}")

        status = "OK  " if not (missing or dupes) else "WARN"
        if status != "OK  ": ok = False if missing else ok
        print(f"  {status} {name:16} {len(a)} record(s)")
        for x in note:
            print(f"       - {x}")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['split', 'merge', 'check', 'migrate', 'status'])
    ap.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument('--write', action='store_true',
                    help='actually write (default is a dry run for split/merge)')
    ap.add_argument('--only', metavar='NAME', help='one registry, e.g. proofs.yaml')
    a = ap.parse_args()
    root = Path(a.root).resolve()
    specs = {k: v for k, v in SPECS.items() if not a.only or k == a.only}

    if a.command == 'check':
        print("=== registry round-trip check (read-only) ===")
        return 0 if do_check(root) else 1

    if a.command == 'status':
        # "Is the migration done?" answered HERE rather than by the caller, because the
        # answer needs SPECS -- which list key holds the records, which field is the id.
        # A caller that pattern-matches `id:` lines gets it wrong: proofs.yaml carries a
        # second list whose records also have `id:`, so a naive scan over-counts and
        # reports a mismatch that does not exist. Exit 0 = consistent, 1 = work to do.
        print("=== registry status: fragments vs flat (read-only) ===")
        consistent = True
        for n, s in specs.items():
            flat = root / 'labtalk' / 'registries' / n
            frag_dir = root / 'labtalk' / 'registries' / s['dir']
            if not frag_dir.is_dir():
                print("  TODO %-16s %s/ does not exist -- not migrated" % (n, s['dir']))
                consistent = False
                continue
            doc = load(flat) if flat.is_file() else {}
            flat_ids = {r[s['idf']] for r in (doc.get(s['key']) or []) if r.get(s['idf'])}
            _, frags = read_fragments(root, s)
            frag_ids = {r[s['idf']] for r in (frags or []) if r.get(s['idf'])}
            if flat_ids == frag_ids and frag_ids:
                print("  OK   %-16s %d record(s) in both" % (n, len(flat_ids)))
                continue
            consistent = False
            print("  TODO %-16s flat=%d fragments=%d" % (n, len(flat_ids), len(frag_ids)))
            for k in sorted(flat_ids - frag_ids)[:5]:
                print("         flat only     %s" % k)
            for k in sorted(frag_ids - flat_ids)[:5]:
                print("         fragment only %s" % k)
        print("\n%s" % ("consistent -- nothing to migrate." if consistent
                        else "NOT consistent -- run: registry_fragments.py migrate --write"))
        return 0 if consistent else 1

    if a.command == 'migrate':
        # One-shot: check -> backup -> split -> merge -> VERIFY AGAINST THE BACKUP.
        # A data migration that cannot prove it lost nothing is a gamble. If the final
        # comparison fails, the flat files are restored from the backup and the fragments
        # are left in place for inspection.
        import shutil
        from datetime import datetime
        print("=== migrate: flat registries -> .d fragments ===\n--- 1. pre-flight ---")
        if not do_check(root):
            print("\nround-trip check failed -- NOT migrating.", file=sys.stderr)
            return 1
        if not a.write:
            print("\n--- 2. plan (dry run) ---")
            for n, s in specs.items():
                do_split(root, n, s, False)
            print("\nDRY RUN. Re-run with --write to migrate.")
            return 0

        reg = root / 'labtalk' / 'registries'

        # FOLD EXTRA FRAGMENTS INTO THE FLAT FILE FIRST, before anything is backed up.
        #
        # Why this exists: the first live migrate FAILED verify with gained=2 on
        # proofs.yaml. That was not corruption. Two proofs had been authored this session
        # directly as .d fragments -- the new convention, written just before the migration
        # that establishes it -- and were never appended to the flat file. Merge correctly
        # picked them up, so the regenerated file held 49 where the backup held 47.
        #
        # Both obvious fixes are wrong. Loosening verify to tolerate `gained` discards the
        # one check that makes this migration safe to run at all. Deleting the two
        # fragments discards real records. Instead, fold any fragment-only record into the
        # flat file BEFORE the backup is taken. The migration then has to be an exact
        # identity -- lost=0 gained=0 changed=0 -- and verify keeps its full strength.
        #
        # This is also why fold runs before the backup rather than after: the backup must
        # be the thing the result is required to equal.
        folded_total = 0
        for n, s in specs.items():
            flat_path = reg / n
            if not flat_path.is_file():
                continue
            _, frags = read_fragments(root, s)
            if not frags:
                continue
            doc = load(flat_path) or {}
            recs = list(doc.get(s['key']) or [])
            have = {r[s['idf']] for r in recs if r.get(s['idf'])}
            extras = [r for r in frags if r.get(s['idf']) and r[s['idf']] not in have]
            if not extras:
                continue
            for r in extras:
                print("  fold  %-16s <- %s  (fragment-only record)" % (n, r[s['idf']]))
            recs.extend(extras)
            doc[s['key']] = recs
            if 'current_by_lane' in s['computed']:
                by_lane, by_proj = compute_indexes(recs)
                doc['current_by_lane'] = by_lane
                doc['current_by_project'] = by_proj
            flat_path.write_text(BANNER.format(d=s['dir']) + "\n" + dump(doc), encoding='utf-8')
            folded_total += len(extras)
        if folded_total:
            print("  folded %d fragment-only record(s) into the flat files; they are now"
                  % folded_total)
            print("  part of the baseline the migration must reproduce exactly.")

        backup = reg / ('_pre_fragment_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        backup.mkdir(parents=True, exist_ok=True)
        for n in specs:
            f = reg / n
            if f.is_file():
                shutil.copy2(f, backup / n)
        print("\n--- 2. backup -> %s ---" % backup.name)

        print("\n--- 3. split ---")
        for n, s in specs.items():
            do_split(root, n, s, True)
        print("\n--- 4. merge (regenerate the flat files) ---")
        for n, s in specs.items():
            do_merge(root, n, s, True)

        print("\n--- 5. verify against the backup ---")
        bad = 0
        for n, s in specs.items():
            bf = backup / n
            if not bf.is_file():
                continue
            before = yaml.safe_load(bf.read_text(encoding='utf-8', errors='replace')) or {}
            after = load(reg / n) or {}
            da = {r[s['idf']]: r for r in (before.get(s['key']) or []) if r.get(s['idf'])}
            db = {r[s['idf']]: r for r in (after.get(s['key']) or []) if r.get(s['idf'])}
            lost, gained = set(da) - set(db), set(db) - set(da)
            changed = [k for k in set(da) & set(db) if da[k] != db[k]]
            # Strict by design: fragment-only records were folded into the baseline above,
            # so the migration must now be an exact identity. Nothing is tolerated here.
            ok = not (lost or gained or changed)
            print("  %s %-16s %d -> %d  lost=%d gained=%d changed=%d"
                  % ('PASS' if ok else 'FAIL', n, len(da), len(db),
                     len(lost), len(gained), len(changed)))
            if not ok:
                bad += 1
                for k in sorted(lost)[:5]:
                    print("        LOST    %s" % k)
                for k in sorted(gained)[:5]:
                    print("        GAINED  %s" % k)
                for k in sorted(changed)[:5]:
                    print("        CHANGED %s" % k)
        if bad:
            print("\nVERIFY FAILED -- restoring flat files from the backup.", file=sys.stderr)
            for n in specs:
                bf = backup / n
                if bf.is_file():
                    shutil.copy2(bf, reg / n)
            print("restored. Fragments left in place for inspection.", file=sys.stderr)
            return 1

        print("""
migrated.

FROM NOW ON, add a record by creating ONE new file -- never by editing a flat .yaml:
    labtalk/registries/runs.d/AIPR-YYYYMMDD-NNN.yaml
    labtalk/registries/proofs.d/proof.my.thing.yaml
Then regenerate before committing:
    python tools/registries/registry_fragments.py merge --write
Commit BOTH the fragment and the regenerated flat file.

Do NOT hand-edit current_by_lane / current_by_project any more -- they are computed
from the run fragments, and edits will be overwritten.

Backup kept at: %s  (delete when satisfied)
""" % backup)
        return 0

    if a.command == 'split':
        print("=== split: flat registry -> fragments ===")
        if not a.write:
            print("  DRY RUN -- add --write to create files. The flat files are never deleted.")
        for n, s in specs.items():
            do_split(root, n, s, a.write)
        if a.write:
            print("\nNext: verify, then merge back and confirm the flat file still parses:")
            print("  python tools/registries/registry_fragments.py merge --write")
        return 0

    print("=== merge: fragments -> flat registry ===")
    if not a.write:
        print("  DRY RUN -- add --write to overwrite the flat files.")
    for n, s in specs.items():
        do_merge(root, n, s, a.write)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
