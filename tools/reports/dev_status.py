#!/usr/bin/env python3
"""
DEV STATUS -- a tight, local, close-work dashboard for x64base.

NOT the project reports. Those describe the project (portal narrative, boards, access)
and some of them publish. This is the maintainer's working view: what is open, what is
uncommitted, what the gates say, and where the last agent left off. Local only, never
staged to the site.

Answers, in one screen:
  1. What is uncommitted right now?          (the "just one more thing" leak, measured)
  2. What lanes are open and how proven?
  3. Do the static gates pass?
  4. Where did the last agent leave off?     (board.worklog handoffs)
  5. What is design-intended and awaiting a build?

  python tools/reports/dev_status.py [--root <repo>] [--out <dir>] [--open]

Writes <out>/DEV_STATUS.html (default: <root>/docs/reports/). Read-only; safe while the
daemon runs. Git queries are read-only and take no index lock.

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-063 . status: candidate
"""
import argparse, datetime, html, re, struct, subprocess, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml --break-system-packages", file=sys.stderr)
    raise SystemExit(2)

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
ap.add_argument('--out',  default=None)
ap.add_argument('--open', action='store_true', help='open in the default browser when done')
ap.add_argument('--gates', action='store_true',
                help='also run the static gates (slow: source_census rescans 1034 files). '
                     'Off by default so this stays a fast glance -- use '
                     'tools/gates/run_gates.py when you want the gate verdict.')
args = ap.parse_args()

ROOT = Path(args.root).resolve()
OUT  = Path(args.out) if args.out else ROOT/'docs'/'reports'
OUT.mkdir(parents=True, exist_ok=True)
NOW  = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
e    = lambda s: html.escape(str(s))


GIT_OK = True

def git(*a, timeout=20):
    """Read-only git. Never touches the index, so it cannot collide with a maintainer
    mid-commit (the Hot Potato hazard, AIF-059).

    Short timeout and graceful degradation on purpose: on a large tree behind a slow
    filesystem (network mount, LFS hooks) `ls-files --others` can take tens of seconds.
    A dashboard that hangs is worse than one that says it could not read git."""
    global GIT_OK
    try:
        r = subprocess.run(['git', '-C', str(ROOT), *a],
                           capture_output=True, text=True, errors='replace', timeout=timeout)
        return r.stdout if r.returncode == 0 else ''
    except subprocess.TimeoutExpired:
        GIT_OK = False
        print(f"  warn: git {' '.join(a)} timed out after {timeout}s -- section degraded",
              file=sys.stderr)
        return ''
    except Exception:
        GIT_OK = False
        return ''


def load(name):
    f = ROOT/'labtalk'/'registries'/name
    try:
        return yaml.safe_load(f.read_text(encoding='utf-8', errors='replace')) or {}
    except Exception:
        return {}


# ---------------------------------------------------------------- 1. working tree
modified = [l for l in git('ls-files', '--modified').splitlines() if l.strip()]
untracked_raw = git('ls-files', '--others', '--exclude-standard').splitlines()
untracked = [l for l in untracked_raw if l.strip()]

def bucket(paths):
    b = {}
    for p in paths:
        parts = p.split('/')
        key = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
        b[key] = b.get(key, 0) + 1
    return sorted(b.items(), key=lambda x: -x[1])

# closeouts specifically -- the measured "finished but uncommitted" gap
untracked_closeouts = [p for p in untracked if re.search(r'SESSION_(CLOSEOUT|REPORT)_', p)]
tracked_closeouts   = [p for p in git('ls-files', 'docs/maintenance').splitlines()
                       if 'SESSION_CLOSEOUT' in p]

ahead = git('rev-list', '--count', '@{u}..HEAD').strip() or '?'
head  = git('log', '-1', '--format=%h  %s').strip()
branch = git('rev-parse', '--abbrev-ref', 'HEAD').strip()

# ---------------------------------------------------------------- 2. lanes + proofs
runs_y  = load('ai_runs.yaml')
proofs  = (load('proofs.yaml') or {}).get('proofs', []) or []
by_lane = runs_y.get('current_by_lane', {}) or {}

state_counts = {}
for p in proofs:
    s = str(p.get('state', '?'))
    state_counts[s] = state_counts.get(s, 0) + 1

# design-intended = built nothing yet; the awaiting-work queue
awaiting = [p for p in proofs if str(p.get('state', '')).startswith('design')]

# lane titles from the intake queue
lane_title = {}
q = ROOT/'docs'/'ai-friendly'/'AI_INTERACTION_INTAKE_QUEUE_V1.md'
if q.is_file():
    for l in q.read_text(encoding='utf-8', errors='replace').splitlines():
        m = re.match(r'^\|\s*(AIF-\d+)\s*\|\s*([^|]{0,140})', l)
        if m:
            lane_title[m.group(1)] = re.sub(r',\s*(Cowork|Claude|Grok)[^,]*$', '', m.group(2)).strip()

# ---------------------------------------------------------------- 3. gates
def run_gate(script, *extra):
    p = ROOT/script
    if not p.is_file():
        return ('SKIP', f'{script} not found')
    try:
        r = subprocess.run([sys.executable, str(p), '--root', str(ROOT), *extra],
                           capture_output=True, text=True, errors='replace', timeout=180)
        tail = [x for x in (r.stdout or '').splitlines() if x.strip()][-1:] or ['']
        return ('PASS' if r.returncode == 0 else 'FAIL', tail[0][:120])
    except Exception as ex:
        return ('ERR', str(ex)[:120])

if args.gates:
    gates = [
        ('@dottalk.file coverage', *run_gate('tools/fullstack_docs/source_census.py', '--strict')),
        ('registry citations',     *run_gate('tools/gates/validate_registries.py', '--strict', '--quiet')),
    ]
else:
    gates = [('(skipped -- pass --gates, or run tools/gates/run_gates.py)', 'SKIP', '')]

# ---------------------------------------------------------------- 4. worklog handoffs
def read_dbf(path):
    b = Path(path).read_bytes()
    nrec, hlen, rlen = struct.unpack_from('<IHH', b, 4)
    fields, off = [], 96
    while off < len(b) and b[off] != 0x0D:
        raw = b[off:off+32]
        if len(raw) < 32: break
        nm = raw[0:11].split(b'\x00')[0].decode('ascii', 'replace').strip()
        if not nm: break
        fields.append((nm, struct.unpack_from('<I', raw, 12)[0],
                           struct.unpack_from('<I', raw, 16)[0]))
        off += 32
    rows = []
    for i in range(nrec):
        rec = b[hlen + i*rlen: hlen + (i+1)*rlen]
        if len(rec) < rlen or rec[0:1] == b'*': continue
        rows.append({n: rec[d:d+l].decode('cp437', 'replace').strip() for n, d, l in fields})
    return rows

handoffs = []
try:
    MD = ROOT/'dottalkpp'/'data'/'metadata'/'bbs'
    boards = {b['ID']: b for b in read_dbf(MD/'SYSBOARD.dbf')}
    wl = next((b['ID'] for b in boards.values() if b['BKEY'] == 'board.worklog'), None)
    if wl:
        thr = {t['ID']: t for t in read_dbf(MD/'SYSTHREAD.dbf')}
        for p in read_dbf(MD/'SYSPOST.dbf'):
            if p['BOARDID'] == wl:
                handoffs.append({
                    'subject': thr.get(p['THREADID'], {}).get('SUBJECT', ''),
                    'body': p['BODY'],
                    'at': datetime.datetime.utcfromtimestamp(int(p['POSTAT'] or 0)).strftime('%Y-%m-%d %H:%M')
                          if (p['POSTAT'] or '').isdigit() else '--',
                })
        handoffs.reverse()
except Exception:
    pass

# ---------------------------------------------------------------- render
CSS = """
:root{--bg:#0f1419;--panel:#171e26;--line:#26323f;--tx:#dfe7ef;--dim:#8ba0b4;--acc:#5cc8ff;
--ok:#4ec9a0;--warn:#e8b84b;--bad:#e86a6a;--mono:ui-monospace,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 70px}
h1{font-size:22px;margin:0 0 3px}h2{font-size:16px;margin:26px 0 9px;padding-bottom:6px;
border-bottom:1px solid var(--line);color:var(--acc)}
.sub{color:var(--dim);font-size:12px;margin-bottom:16px}
.band{background:#2a2118;border:1px solid #5c4a22;color:#e8c98b;border-radius:6px;
padding:8px 13px;margin-bottom:16px;font-size:12px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px;margin:7px 0}
th{text-align:left;color:var(--dim);font-size:10.5px;letter-spacing:.5px;text-transform:uppercase;
padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:6px 8px;border-bottom:1px solid #1e2731;vertical-align:top}
code,.m{font-family:var(--mono);font-size:12px}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10.5px;
font-family:var(--mono);border:1px solid var(--line);background:#1d262f;color:var(--dim)}
.pill.ok{color:var(--ok);border-color:#2c5c4c}.pill.warn{color:var(--warn);border-color:#5c4c22}
.pill.bad{color:var(--bad);border-color:#5c2c2c}.pill.acc{color:var(--acc);border-color:#28516b}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:11px 13px}
.kpi .n{font-size:23px;font-weight:600;color:var(--acc);line-height:1.1}
.kpi .n.warn{color:var(--warn)}.kpi .n.bad{color:var(--bad)}.kpi .n.ok{color:var(--ok)}
.kpi .l{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.4px;margin-top:2px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:9px 0}
.hand{border-left:2px solid var(--acc);padding-left:11px;margin:10px 0}
.hand .h{font-size:11px;color:var(--dim);font-family:var(--mono)}
.hand .b{margin-top:4px;white-space:pre-wrap;word-break:break-word;font-size:12.5px}
.dim{color:var(--dim)}.small{font-size:12px}
.foot{margin-top:34px;padding-top:12px;border-top:1px solid var(--line);color:var(--dim);font-size:11px}
"""

def kpi(n, l, cls=''):
    return f'<div class="kpi"><div class="n {cls}">{n}</div><div class="l">{e(l)}</div></div>'

# uncommitted
mod_rows = ''.join(f'<tr><td><code>{e(k)}</code></td><td style="text-align:right">{v}</td></tr>'
                   for k, v in bucket(modified)[:10]) or \
           '<tr><td class="dim" colspan="2">nothing modified -- clean</td></tr>'
unt_rows = ''.join(f'<tr><td><code>{e(k)}</code></td><td style="text-align:right">{v}</td></tr>'
                   for k, v in bucket(untracked)[:10]) or \
           '<tr><td class="dim" colspan="2">nothing untracked</td></tr>'

gate_rows = ''.join(
    f'<tr><td>{e(n)}</td><td><span class="pill {"ok" if s=="PASS" else "bad" if s=="FAIL" else "warn"}">{s}</span></td>'
    f'<td class="small dim">{e(d)}</td></tr>' for n, s, d in gates)

lane_rows = ''.join(
    f'<tr><td><code>{e(k)}</code></td><td class="small">{e(lane_title.get(k,""))[:95]}</td>'
    f'<td class="small"><code>{e(v)}</code></td></tr>'
    for k, v in sorted(by_lane.items(), key=lambda x: (len(x[0]), x[0])))

await_rows = ''.join(
    f'<tr><td><code>{e(p.get("id",""))}</code></td><td class="small">{e(p.get("label",""))[:80]}</td></tr>'
    for p in awaiting) or '<tr><td class="dim" colspan="2">nothing design-intended</td></tr>'

state_rows = ''.join(
    f'<span class="pill {"ok" if "runtime" in k or k=="validated" else "acc" if "source" in k else "warn"}">'
    f'{e(k)}: {v}</span> ' for k, v in sorted(state_counts.items(), key=lambda x: -x[1]))

hand_html = ''.join(
    f'<div class="hand"><div class="h">{e(h["subject"])} &middot; {e(h["at"])}</div>'
    f'<div class="b">{e(chr(10).join(x.strip() for x in h["body"].split("|")))}</div></div>'
    for h in handoffs[:3]) or '<div class="dim small">no worklog handoffs found</div>'

n_unc = len(modified) + len(untracked_closeouts)
cap = (f"{len(tracked_closeouts)}/{len(tracked_closeouts)+len(untracked_closeouts)}"
       if (tracked_closeouts or untracked_closeouts) else "--")

git_warn = ('' if GIT_OK else
    '<div class="band" style="background:#2a1818;border-color:#6b2f2f;color:#ffb3b3">'
    'GIT READ TIMED OUT -- the working-tree section below is incomplete. Common on a slow '
    'or network-mounted repo. Re-run locally, or raise the timeout in git().</div>')

body = f"""
<div class="band">LOCAL DEV VIEW -- never staged to the site. Working state, not a project report.</div>
{git_warn}
<div class="grid">
{kpi(len(modified), 'modified (uncommitted)', 'warn' if modified else 'ok')}
{kpi(ahead, 'commits ahead of remote', 'warn' if ahead not in ('0','?') else '')}
{kpi(len(untracked_closeouts), 'closeouts not committed', 'bad' if untracked_closeouts else 'ok')}
{kpi(cap, 'closeout capture', 'warn' if untracked_closeouts else 'ok')}
{kpi(len(by_lane), 'tracked lanes')}
{kpi(len(awaiting), 'awaiting build', 'warn' if awaiting else 'ok')}
</div>

<h2>Gates</h2>
<table><tr><th>Gate</th><th>State</th><th>Detail</th></tr>{gate_rows}</table>

<h2>Uncommitted right now</h2>
<div class="card"><b>Branch</b> <code>{e(branch)}</code> &middot; <b>HEAD</b> <code>{e(head)}</code></div>
<table><tr><th>Modified (tracked) -- top areas</th><th style="text-align:right">files</th></tr>{mod_rows}</table>
<table style="margin-top:12px"><tr><th>Untracked -- top areas</th><th style="text-align:right">files</th></tr>{unt_rows}</table>
<div class="small dim" style="margin-top:7px">Modified-tracked is the risk column: edits that exist only on
this machine. Untracked is usually scratch, but check it for real work before assuming.</div>

<h2>Where the last agent left off</h2>
{hand_html}

<h2>Lanes</h2>
<div style="margin:8px 0">{state_rows}</div>
<table><tr><th>Lane</th><th>What</th><th>Newest run</th></tr>{lane_rows}</table>

<h2>Awaiting a build (design-intended)</h2>
<table><tr><th>Proof</th><th>Label</th></tr>{await_rows}</table>
"""

page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>x64base -- Dev Status</title><style>{CSS}</style></head><body><div class="wrap">
<h1>x64base -- Dev Status</h1>
<div class="sub">Close-work view for {e(branch)} &middot; generated {NOW} local</div>
{body}
<div class="foot">Generated by <code>tools/reports/dev_status.py</code> from git state, the
LabTalk registries, and the live BBS store. Read-only; git calls take no index lock, so this is
safe to run while committing. Regenerate any time.</div>
</div></body></html>"""

target = OUT/'DEV_STATUS.html'
target.write_text(page, encoding='utf-8')
print(f"wrote {target}")
print(f"  modified={len(modified)}  untracked={len(untracked)}  "
      f"uncommitted closeouts={len(untracked_closeouts)}  lanes={len(by_lane)}  "
      f"awaiting={len(awaiting)}")
for n, s, d in gates:
    print(f"  gate {s:5} {n}")

if args.open:
    import webbrowser
    webbrowser.open(target.as_uri())
