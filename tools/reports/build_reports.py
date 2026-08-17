#!/usr/bin/env python3
"""
Human-readable HTML reports over live DotTalk++ state (AI Portal + BBS).

Reads, READ-ONLY:
  dottalkpp/data/metadata/bbs/{SYSBOARD,SYSTHREAD,SYSPOST}.dbf
  dottalkpp/data/metadata/identity/{SYSMEMBER,SYSROLE,SYSPERM,SYSMEMROLE,SYSROLEPERM,SYSUSER,SYSGRANT}.dbf
  labtalk/registries/{ai_runs,proofs}.yaml or authoritative {runs,proofs}.d fragments
  docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md

Writes: docs/reports/{index,AI_PORTAL_REPORT,BBS_BOARDS_REPORT,BBS_ACCESS_REPORT}.html

Safe to run while dottalk_bbsd is up: it opens the DBFs read-only and takes no lock.

  python tools/reports/build_reports.py [--root <repo>] [--out <dir>]

Owner: member.derald  . steward: member.ai.claude.cowork  . lane: AIF-060  . status: candidate
"""
import argparse, datetime, html, json, re, struct, sys
from pathlib import Path
import yaml

def read_dbf(path):
    b = Path(path).read_bytes()
    nrec, hlen, rlen = struct.unpack_from('<IHH', b, 4)
    fields, off = [], 96
    while off < len(b) and b[off] != 0x0D:
        raw = b[off:off+32]
        if len(raw) < 32: break
        name = raw[0:11].split(b'\x00')[0].decode('ascii', 'replace').strip()
        if not name: break
        ftype = chr(raw[11])
        disp  = struct.unpack_from('<I', raw, 12)[0]
        flen  = struct.unpack_from('<I', raw, 16)[0]
        fields.append((name, ftype, disp, flen))
        off += 32
    rows = []
    for i in range(nrec):
        base = hlen + i * rlen
        rec = b[base:base+rlen]
        if len(rec) < rlen or rec[0:1] == b'*':
            continue
        row = {}
        for (name, ftype, disp, flen) in fields:
            row[name] = rec[disp:disp+flen].decode('cp437', 'replace').strip()
        rows.append(row)
    return [f[0] for f in fields], rows

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument('--root', default=str(Path(__file__).resolve().parents[2]),
                 help='repo root (default: two levels up from this script)')
_ap.add_argument('--out', default=None, help='output dir (default: <root>/docs/reports)')
_ap.add_argument('--source', choices=['yaml', 'fragments', 'dbf'], default='yaml',
                 help='AI Portal lane/run/proof source: reviewed flat YAML snapshot (default), '
                      'authoritative local .d fragments composed read-only in memory, or the '
                      'DERIVED DBF tracking tables via tools/dbf/crud.read '
                      '(SYSLANE/SYSRUN/SYSRUNLANE/SYSPROOF). dbf dogfoods the tracking layer: '
                      'a landed lane IS a row, so it cannot be missing from the view.')
_ap.add_argument('--public', action='store_true',
                 help='emit only publishable reports for x64base.com: skip any report marked '
                      'sensitivity: private in portal.yaml, and apply the documented public omissions '
                      '(no auth-surface map, no connection recipe, no internal absolute paths/banner).')
_args = _ap.parse_args()

ROOT = Path(_args.root).resolve()
MD   = ROOT/'dottalkpp'/'data'/'metadata'
OUT  = Path(_args.out) if _args.out else ROOT/'docs'/'reports'
OUT.mkdir(parents=True, exist_ok=True)
if not MD.is_dir():
    sys.exit(f"no metadata dir at {MD} -- pass --root <repo>")
NOW  = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
PUBLIC = bool(_args.public)

def _report_sensitivity():
    """basename -> sensitivity ('public'/'internal'/'private') from portal.yaml (portal.reports).
    Governs the public build: a report marked 'private' is never emitted with --public."""
    sens = {}
    try:
        data = yaml.safe_load((ROOT/'labtalk'/'registries'/'portal.yaml').read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return sens
    def walk(o):
        if isinstance(o, dict):
            p, s = o.get('path'), o.get('sensitivity')
            if isinstance(p, str) and isinstance(s, str) and p.lower().endswith('.html'):
                sens[Path(p).name] = s.strip().lower()
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(data)
    return sens
SENS = _report_sensitivity()
def is_private(fname): return SENS.get(fname, '') == 'private'

def _redacted_boards():
    """Boards to omit from a --public build, read from portal.yaml:

        - id: portal.reports
          redacted_boards: [board.example]

    Empty by default. board.worklog is deliberately NOT redacted -- see the note at
    the REDACTED_BOARDS assignment."""
    try:
        import yaml
        data = yaml.safe_load(
            (ROOT/'labtalk'/'registries'/'portal.yaml').read_text(
                encoding='utf-8', errors='replace'))
        for s in (data or {}).get('sections', []) or []:
            if s.get('id') == 'portal.reports':
                return [str(x) for x in (s.get('redacted_boards') or [])]
    except Exception:
        pass
    return []
def emit(fname, htmltext):
    if PUBLIC and is_private(fname):
        print(f"SKIPPED (private per portal.yaml): {fname}"); return False
    (OUT/fname).write_text(htmltext, encoding='utf-8')
    print(("wrote (public): " if PUBLIC else "wrote ")+fname); return True

T = lambda d,n: read_dbf(MD/d/f'{n}.dbf')[1]
B  = {n:T('bbs',n)      for n in ['SYSBOARD','SYSTHREAD','SYSPOST']}
I  = {n:T('identity',n) for n in ['SYSMEMBER','SYSROLE','SYSPERM','SYSMEMROLE','SYSROLEPERM','SYSUSER','SYSGRANT']}

def ts(v):
    try:
        n=int(v); return datetime.datetime.utcfromtimestamp(n).strftime('%Y-%m-%d %H:%M') if n else '--'
    except: return '--'
e = lambda s: html.escape(str(s))

KIND_B={'0':'governance','1':'chat','2':'notice'}
KIND_M={'0':'Human','1':'AI','2':'Service','3':'External'}
AK    ={'0':'system','1':'AI','2':'service','3':'external','4':'human'}

mem  = {m['ID']:m for m in I['SYSMEMBER']}
usr  = {u['ID']:u for u in I['SYSUSER']}
role = {r['ID']:r for r in I['SYSROLE']}
perm = {p['ID']:p for p in I['SYSPERM']}
brd  = {b['ID']:b for b in B['SYSBOARD']}
thr  = {t['ID']:t for t in B['SYSTHREAD']}

rperm={}
for rp in I['SYSROLEPERM']: rperm.setdefault(rp['ROLEID'],[]).append(perm.get(rp['PERMID'],{}).get('PKEY',''))
mrole={}
for mr in I['SYSMEMROLE']: mrole.setdefault(mr['MEMBERID'],[]).append(mr['ROLEID'])

def mlabel(mid):
    m=mem.get(str(mid))
    if not m: return f'(unknown id {mid})'
    return m['MKEY']
def mdisplay(mid):
    m=mem.get(str(mid))
    if not m: return ''
    return usr.get(m['USERID'],{}).get('DISPLAY','')

# These pages are served from x64base.com/AI/ as static passthroughs, so they do
# NOT inherit the site's Next.js layout and were permanently dark while the site
# defaults to LIGHT (owner report 2026-08-13: "the ai section does not respect
# the theme"). The site keeps its preference in localStorage['theme'] and marks
# <html class="dark">; THEME_SCRIPT below reads the same key, so the navbar
# toggle now reaches these pages too.
#
# :root is the light palette and html.dark restores the original console values
# unchanged -- the dark look nobody complained about is preserved byte for byte.
# Every colour the rules below need is a variable now; hardcoded hexes could not
# follow the theme, which is why the panel, pill, note and band colours moved up
# here rather than staying inline.
CSS = """
:root{--bg:#f6f9fc;--panel:#ffffff;--line:#d0ddeb;--tx:#0a1320;--dim:#374960;
--acc:#0b8491;--ok:#15803d;--warn:#ba5c14;--bad:#b93030;
--tdline:#e2eaf2;--pillbg:#eef3f8;--notebg:#eef5f8;
--pok:#9fd3b8;--pwarn:#e0bb8a;--pbad:#e0a5a5;--pacc:#a9d6e2;
--privbg:#fdecec;--privline:#e8a9a9;--privtx:#8c1d1d;
--intbg:#eaf2f8;--intline:#b9d4e6;--inttx:#14506e;
--mono:ui-monospace,"Cascadia Code",Consolas,monospace}
html.dark{--bg:#0f1419;--panel:#171e26;--line:#26323f;--tx:#dfe7ef;--dim:#8ba0b4;
--acc:#5cc8ff;--ok:#4ec9a0;--warn:#e8b84b;--bad:#e86a6a;
--tdline:#1e2731;--pillbg:#1d262f;--notebg:#141c24;
--pok:#2c5c4c;--pwarn:#5c4c22;--pbad:#5c2c2c;--pacc:#28516b;
--privbg:#3a1d1d;--privline:#6b2f2f;--privtx:#ffb3b3;
--intbg:#1d2a33;--intline:#2e4a5c;--inttx:#9fd0ea}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 22px 80px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.3px}
h2{font-size:19px;margin:34px 0 12px;padding-bottom:7px;border-bottom:1px solid var(--line);color:var(--acc)}
h3{font-size:15px;margin:20px 0 8px;color:var(--tx)}
.sub{color:var(--dim);font-size:13px;margin-bottom:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:15px 17px;margin:11px 0}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:9px 0}
th{text-align:left;color:var(--dim);font-weight:600;font-size:11.5px;letter-spacing:.5px;
text-transform:uppercase;padding:7px 9px;border-bottom:1px solid var(--line)}
td{padding:8px 9px;border-bottom:1px solid var(--tdline);vertical-align:top}
tr:last-child td{border-bottom:none}
code,.m{font-family:var(--mono);font-size:12.5px}
.pill{display:inline-block;padding:1.5px 8px;border-radius:11px;font-size:11px;font-family:var(--mono);
border:1px solid var(--line);background:var(--pillbg);color:var(--dim)}
.pill.ok{color:var(--ok);border-color:var(--pok)}.pill.warn{color:var(--warn);border-color:var(--pwarn)}
.pill.bad{color:var(--bad);border-color:var(--pbad)}.pill.acc{color:var(--acc);border-color:var(--pacc)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:11px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.kpi .n{font-size:26px;font-weight:600;color:var(--acc);line-height:1.1}
.kpi .l{font-size:11.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;margin-top:3px}
.post{border-left:2px solid var(--line);padding:2px 0 2px 13px;margin:13px 0}
.post .h{font-size:12px;color:var(--dim);font-family:var(--mono)}
.post .b{margin-top:5px;white-space:pre-wrap;word-break:break-word}
.dim{color:var(--dim)}.small{font-size:12.5px}
.note{border-left:3px solid var(--acc);background:var(--notebg);padding:10px 14px;margin:13px 0;border-radius:0 6px 6px 0}
.note.w{border-left-color:var(--warn)}
ul{margin:7px 0;padding-left:20px}li{margin:3px 0}
a{color:var(--acc)}
.foot{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);color:var(--dim);font-size:12px}
.band{border-radius:7px;padding:9px 14px;margin:0 0 18px;font-size:12.5px;font-weight:600;
letter-spacing:.3px}
.band.priv{background:var(--privbg);border:1px solid var(--privline);color:var(--privtx)}
.band.int{background:var(--intbg);border:1px solid var(--intline);color:var(--inttx)}
kbd{font-family:var(--mono);background:var(--pillbg);border:1px solid var(--line);border-radius:4px;padding:1px 6px;font-size:12px}
"""

# Byte-identical to the no-flash script in the site's app/layout.tsx (line 68).
# Same key, same 'light' default, same 'system' handling -- if that ruling ever
# changes, both copies have to change together. Kept inline and synchronous so
# the page never paints the wrong theme first.
THEME_SCRIPT = ("(function(){try{var t=localStorage.getItem('theme')||'light';"
                "var d=t==='dark'||(t==='system'&&window.matchMedia("
                "'(prefers-color-scheme: dark)').matches);"
                "document.documentElement.classList.toggle('dark',d);}catch(e){}})();")

BANDS = {
 'private': ('band priv',
   'PRIVATE -- DO NOT PUBLISH. Authentication-surface map (member keys, permission '
   'matrix, port and protocol). Internal use only. See docs/reports/REPORTS_PUBLICATION_NOTE_V1.md'),
 'internal': ('band int',
   'INTERNAL -- review before any publication to x64base.com or public main. '
   'See docs/reports/REPORTS_PUBLICATION_NOTE_V1.md'),
}

# The wrap div carries data-pagefind-body so these pages enter site search;
# Pagefind indexes ONLY tagged pages, and until 2026-08-13 nothing under /AI/
# was tagged, so the portal report, the boards report and the diagrams could not
# be found by anyone searching x64base.com.
#
# The band and the footer are marked data-pagefind-ignore. Both are identical on
# every page, so indexing them would make each page match every other page's
# boilerplate -- the search equivalent of a table where one column is constant.
def page(title, sub, body, sensitivity='internal'):
    if PUBLIC:
        band = ('<div class="band int" data-pagefind-ignore>Public snapshot &mdash; a read-only view generated from live '
                'DotTalk++ state. Credentials and the authentication-surface map are deliberately excluded.</div>')
        foot = f'<div class="foot" data-pagefind-ignore>Generated {NOW} from live DotTalk++ state. Read-only snapshot &middot; x64base.com</div>'
    else:
        cls, msg = BANDS.get(sensitivity, BANDS['internal'])
        band = f'<div class="{cls}" data-pagefind-ignore>{e(msg)}</div>'
        foot = ('<div class="foot" data-pagefind-ignore>Generated ' + NOW + ' from live DotTalk++ state\n'
                '(<code>dottalkpp/data/metadata/</code>). Read-only snapshot -- regenerate with\n'
                '<code>tools/reports/build_reports.py</code>.</div>')
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<style>{CSS}</style><script>{THEME_SCRIPT}</script></head><body><div class="wrap" data-pagefind-body>
{band}
<div class="small" style="margin-bottom:10px"><a href="/">&larr; x64base main site</a></div>
<h1>{e(title)}</h1><div class="sub">{sub}</div>
{body}
{foot}
</div></body></html>"""

# =====================================================================
# REPORT 1 -- BBS BOARDS (the rooms and what is in them)
# =====================================================================
# PUBLIC mode: content-level redaction, complementing the file-level skip that
# emit()/is_private() already do from portal.yaml.
#
# DEFAULT IS EMPTY -- nothing is redacted, including board.worklog.
#
# An earlier pass hardcoded board.worklog out of the public build, reasoning that agent
# handoffs are internal coordination. The maintainer overruled it, and correctly: this is
# an ALPHA open-source project, the worklog is not secret, and the agent-handoff surface
# (AIF-057) is one of the more interesting things the BBS lane has to show. Redacting it
# left the online BBS presence with nothing distinctive in it. Visibility widens at beta.
#
# Redaction is opt-in and registry-driven, like sensitivity itself: set
#   redacted_boards: [board.x, board.y]
# under the portal.reports section of labtalk/registries/portal.yaml. Keeping the
# mechanism (it cost little and a genuinely sensitive board may appear later) without
# keeping the judgement call baked into the tool.
REDACTED_BOARDS = set(_redacted_boards()) if PUBLIC else set()
if REDACTED_BOARDS:
    _drop = {b['ID'] for b in B['SYSBOARD'] if b['BKEY'] in REDACTED_BOARDS}
    B['SYSBOARD'] = [b  for b  in B['SYSBOARD']  if b['ID']      not in _drop]
    B['SYSPOST']  = [p  for p  in B['SYSPOST']   if p['BOARDID'] not in _drop]
    B['SYSTHREAD']= [t_ for t_ in B['SYSTHREAD'] if t_['BOARDID'] not in _drop]
    brd = {b['ID']: b   for b  in B['SYSBOARD']}
    thr = {t_['ID']: t_ for t_ in B['SYSTHREAD']}
    print(f"  redacted {len(_drop)} board(s) from the public build: "
          + ", ".join(sorted(REDACTED_BOARDS)))

posts_by_board={}
for p in B['SYSPOST']: posts_by_board.setdefault(p['BOARDID'],[]).append(p)

kpi=f"""<div class="grid">
<div class="kpi"><div class="n">{len(B['SYSBOARD'])}</div><div class="l">Boards</div></div>
<div class="kpi"><div class="n">{len(B['SYSTHREAD'])}</div><div class="l">Threads</div></div>
<div class="kpi"><div class="n">{len(B['SYSPOST'])}</div><div class="l">Posts</div></div>
<div class="kpi"><div class="n">{len([m for m in I['SYSMEMBER'] if m['KIND']=='1'])}</div><div class="l">AI members</div></div>
</div>"""

rows=''
for b in B['SYSBOARD']:
    n=len(posts_by_board.get(b['ID'],[]))
    pp=b['POSTPERM'] or '(owner only)'
    cls='ok' if b['POSTPERM']=='bbs.post' else ('warn' if b['POSTPERM']=='bbs.guest' else 'acc')
    rows+=f"""<tr><td><code>{e(b['BKEY'])}</code><br><span class="dim small">{e(b['NAME'])}</span></td>
<td><span class="pill">{KIND_B.get(b['KIND'],b['KIND'])}</span></td>
<td><span class="pill {cls}">{e(pp)}</span></td>
<td style="text-align:right">{n}</td><td class="small dim">{ts(b['VFROM'])}</td></tr>"""

board_tbl=f"""<table><tr><th>Board</th><th>Kind</th><th>Post permission</th>
<th style="text-align:right">Posts</th><th>Created</th></tr>{rows}</table>"""

feed=''
for b in B['SYSBOARD']:
    ps=posts_by_board.get(b['ID'],[])
    if not ps: 
        feed+=f"""<h3>{e(b['NAME'])} <code class="dim">{e(b['BKEY'])}</code></h3>
<div class="dim small" style="padding-left:13px">-- empty --</div>"""
        continue
    feed+=f"""<h3>{e(b['NAME'])} <code class="dim">{e(b['BKEY'])}</code></h3>"""
    for p in ps:
        t=thr.get(p['THREADID'],{})
        who=mlabel(p['AUTHORID']) if p['AUTHORID']!='0' else 'system'
        disp=mdisplay(p['AUTHORID'])
        body=p['BODY']
        # pretty-print handoff posts (pipe separated)
        if body.count('|')>=3 and 'RUN=' in body:
            parts=[x.strip() for x in body.split('|')]
            body='\n'.join(parts)
        feed+=f"""<div class="post"><div class="h">#{e(p['ID'])} &middot; <b>{e(t.get('SUBJECT','(no subject)'))}</b>
&middot; {e(who)}{' ('+e(disp)+')' if disp else ''} &middot; {ts(p['POSTAT'])}
&middot; <span class="pill">{AK.get(p['AUTHKIND'],p['AUTHKIND'])}</span></div>
<div class="b">{e(body)}</div></div>"""

# The connection recipe names a member key + the AUTH command form (access surface);
# omit it from the public build.
howto="" if PUBLIC else """<div class="note"><b>How to read a board yourself</b><br>
Start the daemon (or <kbd>BBS SERVE</kbd> in the shell), then from any socket client:
<pre class="m" style="margin:7px 0 0">AUTH member.derald &lt;token&gt;
BBS READ board.worklog
QUIT</pre></div>"""

r1=page("DotTalk++ BBS -- Boards and Traffic",
        "Every room on the board, who may post to it, and everything posted so far.",
        kpi+board_tbl+howto+"<h2>All posts, by board</h2>"+feed)
emit('BBS_BOARDS_REPORT.html', r1)

# =====================================================================
# REPORT 2 -- BBS ACCESS: members, roles, permissions, connection
# =====================================================================
posts_by_author={}
for p in B['SYSPOST']: posts_by_author.setdefault(p['AUTHORID'],[]).append(p)

mrows=''
for m in I['SYSMEMBER']:
    u=usr.get(m['USERID'],{})
    rl=[role.get(r,{}).get('RKEY','') for r in mrole.get(m['ID'],[])]
    perms=sorted({p for r in mrole.get(m['ID'],[]) for p in rperm.get(r,[]) if p})
    bbsp=[p for p in perms if p.startswith('bbs.') or p=='chat.invoke']
    risky=[p for p in perms if p in ('source.mutate','host.network.egress','git.push','git.commit')]
    cred='<span class="pill ok">token set</span>' if u.get('CRED') else '<span class="pill">no token</span>'
    kind=KIND_M.get(m['KIND'],m['KIND'])
    kcls={'Human':'acc','AI':'ok','External':'warn'}.get(kind,'')
    n=len(posts_by_author.get(m['ID'],[]))
    mrows+=f"""<tr>
<td><code>{e(m['MKEY'])}</code><br><span class="dim small">{e(u.get('DISPLAY',''))}</span></td>
<td><span class="pill {kcls}">{kind}</span></td>
<td class="small">{' '.join('<code>'+e(x)+'</code>' for x in rl)}</td>
<td class="small">{' '.join('<span class="pill ok">'+e(x)+'</span>' for x in bbsp) or '<span class="dim">--</span>'}</td>
<td class="small">{' '.join('<span class="pill bad">'+e(x)+'</span>' for x in risky) or '<span class="dim">none</span>'}</td>
<td>{cred}</td><td style="text-align:right">{n}</td></tr>"""

mem_tbl=f"""<table><tr><th>Member</th><th>Kind</th><th>Roles</th><th>BBS / chat</th>
<th>High-risk</th><th>Credential</th><th style="text-align:right">Posts</th></tr>{mrows}</table>"""

# role -> permission matrix
rrows=''
for r in I['SYSROLE']:
    ps=sorted([x for x in rperm.get(r['ID'],[]) if x])
    hot=[p for p in ps if p in ('source.mutate','host.network.egress','git.push','git.commit',
                                'user.manage','role.assign','authorization.grant','host.shell')]
    normal=[p for p in ps if p not in hot]
    rrows+=f"""<tr><td><code>{e(r['RKEY'])}</code><br><span class="dim small">{e(r['DESCR'])}</span></td>
<td><span class="pill">{e(r['RKIND'])}</span></td>
<td class="small">{' '.join('<span class="pill">'+e(x)+'</span>' for x in normal) or '<span class="dim">--</span>'}
{' '.join('<span class="pill bad">'+e(x)+'</span>' for x in hot)}</td>
<td style="text-align:right">{len(ps)}</td></tr>"""
role_tbl=f"""<table><tr><th>Role</th><th>Class</th><th>Permissions</th>
<th style="text-align:right">#</th></tr>{rrows}</table>"""

# who can post where
wrows=''
for b in B['SYSBOARD']:
    need=b['POSTPERM']
    who=[]
    for m in I['SYSMEMBER']:
        perms={p for r in mrole.get(m['ID'],[]) for p in rperm.get(r,[])}
        if m['MKEY']=='member.derald': who.append((m['MKEY'],'owner')); continue
        if need and need in perms: who.append((m['MKEY'],'granted'))
    lst=' '.join(f'<span class="pill {"acc" if k=="owner" else "ok"}">{e(x)}</span>' for x,k in who) or '<span class="dim">owner only</span>'
    wrows+=f"""<tr><td><code>{e(b['BKEY'])}</code></td>
<td><span class="pill">{e(need or '(none)')}</span></td><td class="small">{lst}</td></tr>"""
who_tbl=f"""<table><tr><th>Board</th><th>Requires</th><th>Who may post</th></tr>{wrows}</table>"""

# --- agency view: the four legs, per member -----------------------------------
AGENCY_LEGS = """<div class="note"><b>Agency = capacity to act + accountability for having acted</b>
<div class="small" style="margin-top:6px">Four legs. Remove one and it is not agency.
See <code>docs/ai-friendly/AGENCY_MODEL_V1.md</code>.</div>
<table style="margin-top:9px"><tr><th>Leg</th><th>Question</th><th>Represented by</th></tr>
<tr><td><b>Identity</b></td><td>Who is acting?</td><td><code>SYSMEMBER</code></td></tr>
<tr><td><b>Authority</b></td><td>What may they do?</td>
<td><code>SYSMEMROLE -&gt; SYSROLEPERM -&gt; SYSPERM</code></td></tr>
<tr><td><b>Authentication</b></td><td>Can they prove it?</td><td>Argon2id token, <code>AUTH</code></td></tr>
<tr><td><b>Accountability</b></td><td>Who answers for it?</td>
<td><code>owner</code>/<code>committer</code> in <code>ai_runs.yaml</code></td></tr></table>
<div class="small dim" style="margin-top:9px"><b>Not agency:</b> the local Ollama model has
<i>capability</i> but no member row, no token, no permission -- a service, not an actor
(its absence from this table is correct, not an omission). A hosted advisor has
<i>influence</i> but no authority.</div></div>"""

def agency_rows():
    out = ""
    for m in I['SYSMEMBER']:
        u = usr.get(m['USERID'], {})
        perms = sorted({p for r in mrole.get(m['ID'], []) for p in rperm.get(r, []) if p})
        rl = [role.get(r, {}).get('RKEY', '') for r in mrole.get(m['ID'], [])]
        owner_class = (m['MKEY'] == 'member.derald')
        auth = 'token set' if u.get('CRED') else 'no token'
        acct = 'self (owner)' if owner_class else 'member.derald'
        if owner_class:       lvl, lcls = 'full', 'acc'
        elif len(perms) <= 1: lvl, lcls = 'minimal (designed floor)', 'warn'
        else:                 lvl, lcls = 'bounded', 'ok'
        out += f"""<tr><td><code>{e(m['MKEY'])}</code><br>
<span class="dim small">{e(u.get('DISPLAY',''))} &middot; {KIND_M.get(m['KIND'],'')}</span></td>
<td class="small">{' '.join('<code>'+e(x)+'</code>' for x in rl)}</td>
<td style="text-align:right">{len(perms)}</td>
<td><span class="pill {'ok' if u.get('CRED') else ''}">{auth}</span></td>
<td class="small"><code>{acct}</code></td>
<td><span class="pill {lcls}">{lvl}</span></td></tr>"""
    out += """<tr><td><code class="dim">(Ollama, local)</code><br>
<span class="dim small">no member row -- correct, not an omission</span></td>
<td class="dim small">--</td><td style="text-align:right" class="dim">--</td>
<td><span class="pill">cannot authenticate</span></td><td class="dim small">--</td>
<td><span class="pill bad">none -- capability only</span></td></tr>
<tr><td><code class="dim">(GPTbase, hosted)</code><br>
<span class="dim small">advisory front-end</span></td>
<td class="dim small">--</td><td style="text-align:right" class="dim">--</td>
<td><span class="pill">cannot authenticate</span></td><td class="dim small">--</td>
<td><span class="pill bad">none -- influence only</span></td></tr>"""
    return out

agency_tbl = f"""<table><tr><th>Actor</th><th>Roles</th>
<th style="text-align:right">Permissions</th><th>Authentication</th>
<th>Accountable party</th><th>Agency</th></tr>{agency_rows()}</table>
<div class="small dim" style="margin-top:8px"><b>Reading the owner row:</b> <code>member.derald</code>
shows no BBS token yet holds full agency -- not a contradiction. The owner acts at the local console as
the <i>acting member</i>, so the authentication leg is the machine session, not a socket token. Tokens
exist for actors reaching the server <i>over the wire</i>. The four legs still all hold.</div>"""

sec="""<div class="note w"><b>Security invariants in force</b>
<ul>
<li>Server binds <b>127.0.0.1 only</b>. Nothing is reachable from the network.</li>
<li>The <b>token is the trust boundary</b> -- Argon2id (libsodium), CSPRNG-minted, verified constant-time.</li>
<li>Agents (<code>role.ai_partner</code>) never hold <code>source.mutate</code> or
<code>host.network.egress</code>. They read, propose, and post; they do not change source or reach the network.</li>
<li><code>member.derald</code> is the only owner-class identity and the sole committer.</li>
<li><code>member.guest</code> may post to the guestbook and <b>nothing else</b> -- it cannot even read.</li>
</ul></div>"""

conn="""<div class="note"><b>Connecting</b>
<pre class="m" style="margin:7px 0 0">dottalk_bbsd --data &lt;DATA&gt; --port 8765          &lt;- or `BBS SERVE` in the shell
AUTH &lt;member.key&gt; &lt;token&gt;                      &lt;- required first
BBS BOARDS | BBS READ &lt;board&gt; | BBS POST &lt;board&gt; &lt;subject&gt; :: &lt;body&gt;
CHAT &lt;text&gt;                                     &lt;- needs chat.invoke; bridged to local Ollama
QUIT</pre>
<div class="small dim" style="margin-top:8px">Mint a token with <code>USER TOKEN &lt;member&gt;</code> in the shell (owner only).
Idle connections drop after 120s (<code>DOTTALK_BBS_IDLE_TIMEOUT_SEC</code>) so one stuck client cannot wedge the simplex loop.</div></div>"""

r2=page("DotTalk++ BBS -- Access and Identity",
        "Who exists, what they may do, and which rooms they can reach.",
        f"""<div class="grid">
<div class="kpi"><div class="n">{len(I['SYSMEMBER'])}</div><div class="l">Members</div></div>
<div class="kpi"><div class="n">{len(I['SYSROLE'])}</div><div class="l">Roles</div></div>
<div class="kpi"><div class="n">{len(I['SYSPERM'])}</div><div class="l">Permissions</div></div>
<div class="kpi"><div class="n">{len([u for u in I['SYSUSER'] if u['CRED']])}</div><div class="l">Tokens issued</div></div>
</div>"""
        + sec
        + "<h2>Agency -- who may act, and who answers for it</h2>" + AGENCY_LEGS + agency_tbl
        + "<h2>Members</h2>" + mem_tbl
        + "<h2>Who may post where</h2>" + who_tbl
        + "<h2>Roles and their permissions</h2>" + role_tbl
        + "<h2>Connecting</h2>" + conn,
        sensitivity='private')
emit('BBS_ACCESS_REPORT.html', r2)

# =====================================================================
# REPORT 3 -- AI PORTAL: lanes, runs, proofs, who is working what
# =====================================================================
RG = ROOT/'labtalk'/'registries'
rd = lambda n: yaml.safe_load((RG/n).read_text(encoding='utf-8',errors='replace'))

def _load_from_fragments():
    """Compose run/proof registries in memory from their authoritative .d files."""
    import importlib.util
    source = ROOT/'tools'/'registries'/'registry_fragments.py'
    spec = importlib.util.spec_from_file_location('dottalk_registry_fragments', source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load fragment registry helper: {source}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return (module.compose_registry(ROOT, 'ai_runs.yaml'),
            module.compose_registry(ROOT, 'proofs.yaml'))

def _load_from_dbf():
    """Derive (runs, by_lane, by_proj, proofs, lane_rows) from the tracking DBFs via
    tools/dbf/crud.read -- the same shapes the YAML path yields, so the HTML below is
    unchanged. This is the dogfood: the view is DERIVED from the engine's own store,
    so a landed lane (a row) cannot be missing from it (the AIF-087 drift dies here).
    Pure-Python read (no engine), so it stays runnable anywhere the report does."""
    sys.path.insert(0, str(ROOT/'tools'/'dbf'))
    import crud
    lanes_r  = crud.read_rows('SYSLANE')
    runs_r   = crud.read_rows('SYSRUN')
    links    = crud.read_rows('SYSRUNLANE')
    proofs_r = crud.read_rows('SYSPROOF')
    lanes_by_run = {}
    for lk in links:
        lanes_by_run.setdefault(lk['RUNKEY'], []).append(lk['LANEKEY'])
    def _si(v):
        try: return int(v or '0')
        except ValueError: return 0
    runs_o = [{
        'run_id': r['RKEY'], 'member': r['MEMBERKEY'], 'role': r['ROLE'],
        'owner': r['OWNERKEY'], 'committer': r['COMMITKEY'], 'authored_by': r['AUTHORKEY'],
        'planned_by': r['PLANKEY'], 'product': '', 'project': r['PROJECT'],
        'status': 'active' if r['STATUS'] in ('0', '') else 'closed',
        'started': ts(r['STARTAT']), 'git': {'branch': r['BRANCH']},
        'handle_binding': r['HANDLE'], 'lanes': lanes_by_run.get(r['RKEY'], []),
        'closeouts': [r['REPORT']] if r.get('REPORT') else [],
    } for r in runs_r]
    by_lane_o, best = {}, {}
    for r in runs_r:                       # newest run (max STARTAT) per lane
        for lane in lanes_by_run.get(r['RKEY'], []):
            s = _si(r.get('STARTAT'))
            if lane not in best or s >= best[lane]:
                best[lane] = s; by_lane_o[lane] = r['RKEY']
    proofs_o = [{'id': p['PKEY'], 'label': p['LABEL'], 'state': p['STATE'],
                 'notes': p['SOURCE']} for p in proofs_r]
    lane_rows_o = {ln['LKEY']: {'title': ln['TITLE'], 'tags': '', 'anchor': ln['ANCHOR'],
                                'evidence': '', 'notes': ln['ANCHOR']} for ln in lanes_r}
    return runs_o, by_lane_o, {}, proofs_o, lane_rows_o

if _args.source == 'dbf':
    runs, by_lane, by_proj, proofs, lane_rows = _load_from_dbf()
    print(f"AI Portal source: DBF tracking tables "
          f"({len(lane_rows)} lanes, {len(runs)} runs, {len(proofs)} proofs)")
else:
    if _args.source == 'fragments':
        runs_y, proofs_y = _load_from_fragments()
    else:
        runs_y, proofs_y = rd('ai_runs.yaml'), rd('proofs.yaml')
    runs   = runs_y.get('runs',[])
    by_lane= runs_y.get('current_by_lane',{})
    by_proj= runs_y.get('current_by_project',{})
    proofs = proofs_y.get('proofs',[])
    if _args.source == 'fragments':
        print(f"AI Portal source: current local registry fragments "
              f"({len(by_lane)} lanes, {len(runs)} runs, {len(proofs)} proofs)")
    # lane rows from the intake queue table
    lane_rows={}
    qtxt=(ROOT/'docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md').read_text(encoding='utf-8',errors='replace')
    for l in qtxt.splitlines():
        if re.match(r'^\|\s*AIF-\d+', l):
            c=[x.strip() for x in l.strip().strip('|').split('|')]
            if len(c)>=6:
                lane_rows[c[0]]={'title':c[1],'tags':c[2],'anchor':c[4] if len(c)>4 else '','evidence':c[5] if len(c)>5 else '','notes':c[-1]}

EV={'runtime-observed':'ok','runtime_observed':'ok','source-defined':'acc','source_defined':'acc',
    'design-intended':'warn','design-intended -- not started':'warn','draft':'warn','chat-intended':''}
def evpill(v):
    v=(v or '').strip(); return f'<span class="pill {EV.get(v,"")}">{e(v or "--")}</span>'

# --- active run card
act=[r for r in runs if r.get('status')=='active']
runcards=''
for r in runs:
    st=r.get('status','')
    cls={'active':'ok','closed':''}.get(st,'')
    lanes=' '.join(f'<span class="pill acc">{e(x)}</span>' for x in r.get('lanes',[]))
    co='<br>'.join(f'<span class="small dim">{e(c)}</span>' for c in (r.get('closeouts') or [])) or '<span class="dim small">--</span>'
    g=r.get('git') or {}
    runcards+=f"""<div class="card"><b><code>{e(r.get('run_id'))}</code></b>
<span class="pill {cls}">{e(st)}</span>
<span class="pill">{e(r.get('product',''))}</span>
<div class="small dim" style="margin:5px 0">{e(r.get('member',''))} as <b>{e(r.get('role',''))}</b>
&middot; owner <code>{e(r.get('owner',''))}</code> &middot; committer <code>{e(r.get('committer',''))}</code>
{('&middot; planned by <code>'+e(r['planned_by'])+'</code>') if r.get('planned_by') else ''}</div>
<div style="margin:7px 0">{lanes}</div>
<div class="small dim">project <code>{e(r.get('project',''))}</code>
{('&middot; branch <code>'+e(g.get('branch',''))+'</code>') if g else ''}
&middot; started {e(r.get('started',''))}
&middot; handle <span class="pill warn">{e(r.get('handle_binding',''))}</span></div>
<div style="margin-top:7px" class="small">closeouts:<br>{co}</div></div>"""

# --- lane table (current_by_lane joined to intake rows)
lrows=''
for lane in sorted(by_lane, key=lambda x:(len(x),x)):
    info=lane_rows.get(lane,{})
    run=by_lane[lane]
    title=info.get('title','')
    title=re.sub(r',\s*(Cowork|Claude)[^,]*$','',title)
    lrows+=f"""<tr><td><code>{e(lane)}</code></td>
<td class="small">{e(title) or '<span class="dim">--</span>'}</td>
<td>{evpill(info.get('evidence'))}</td>
<td class="small"><code>{e(run)}</code></td></tr>"""
lane_tbl=f"""<table><tr><th>Lane</th><th>What it is</th><th>Evidence</th>
<th>Newest run (return here)</th></tr>{lrows}</table>"""

# --- closed / documented-only lanes (owner request 2026-08-04): every intake-queue
#     AIF NOT in current_by_lane, surfaced COLLAPSED and linked to its record, so
#     nothing is hidden just because it is closed out. Additive; the active-lane
#     table above is unchanged.
_docpat=re.compile(r'([\w./-]+\.(?:md|csv|json|yaml|html|cpp|hpp|py))')
_ghblob='https://github.com/deraldg/x64base/blob/development/'
_inactive=[a for a in sorted(lane_rows, key=lambda x:(len(x),x)) if a not in by_lane]
_crows=''
for _a in _inactive:
    _info=lane_rows[_a]
    _title=re.sub(r',\s*(Cowork|Claude|Codex|Grok|ChatGPT)[^,]*$','',_info.get('title',''))
    _m=_docpat.search(_info.get('anchor','')) or _docpat.search(_info.get('notes',''))
    _claim=f'coordination/aif/{_a}.claim'
    if _m and (ROOT/_m.group(1)).exists():
        _rec=f'<a href="{_ghblob}{e(_m.group(1))}">{e(_m.group(1))}</a>'
    elif _m:
        _rec=f'<span class="pill warn">doc missing</span> <code>{e(_m.group(1))}</code>'
        if (ROOT/_claim).exists(): _rec+=f' &middot; <a href="{_ghblob}{e(_claim)}">claim</a>'
    elif (ROOT/_claim).exists():
        _rec=f'<a href="{_ghblob}{e(_claim)}">{e(_claim)}</a>'
    else:
        _rec='<span class="pill warn">no record on disk</span>'
    _crows+=f"""<tr><td><code>{e(_a)}</code></td>
<td class="small">{e(_title) or '<span class="dim">--</span>'}</td>
<td class="small">{_rec}</td></tr>"""
closed_block=(f"""<details style="margin-top:10px"><summary style="cursor:pointer">
<b>Closed / documented-only lanes ({len(_inactive)})</b> -- every AIF in the intake
queue with no current run, linked to its record. Click to expand.</summary>
<table style="margin-top:8px"><tr><th>Lane</th><th>What it is</th><th>Record</th></tr>
{_crows}</table></details>""" if _inactive else '')

# --- proofs
prows=''
for p in proofs:
    st=p.get('state','')
    prows+=f"""<tr><td><code>{e(p.get('id',''))}</code><br>
<span class="small">{e(p.get('label',''))}</span></td>
<td>{evpill(st)}</td>
<td class="small dim">{e(str(p.get('notes',''))[:230])}{'...' if len(str(p.get('notes','')))>230 else ''}</td></tr>"""
proof_tbl=f"""<table><tr><th>Proof</th><th>State</th><th>Evidence note</th></tr>{prows}</table>"""

nobs=len([p for p in proofs if p.get('state')=='runtime_observed'])
nsrc=len([p for p in proofs if p.get('state')=='source_defined'])

# --- tasks (SYSTASK) via tools/dbf/crud.read; graceful if not loaded yet -------
def _task_rows():
    try:
        sys.path.insert(0, str(ROOT/'tools'/'dbf'))
        import crud
        return crud.read_rows('SYSTASK')
    except Exception:
        return []
TASK_ST={'0':('open',''),'1':('in progress','ok'),'2':('done','acc'),
         '3':('returned','warn'),'4':('parked','')}
_tasks=_task_rows()
if _tasks:
    _trows=''
    for t in sorted(_tasks, key=lambda r:(r.get('STATUS','9'), r.get('TKEY',''))):
        lbl,cls=TASK_ST.get(t.get('STATUS',''),(t.get('STATUS',''),''))
        _trows+=f"""<tr><td><code>{e(t.get('TKEY',''))}</code><br>
<span class="small">{e(t.get('TITLE',''))}</span></td>
<td><code>{e(t.get('LANEKEY','') or '--')}</code></td>
<td class="small dim">{e(t.get('CHANNEL',''))}</td>
<td><span class="pill {cls}">{e(lbl)}</span></td>
<td class="small"><code>{e(t.get('ASSIGNKEY','') or '--')}</code></td></tr>"""
    _open=len([t for t in _tasks if t.get('STATUS','')=='0'])
    _prog=len([t for t in _tasks if t.get('STATUS','')=='1'])
    tasks_block=(f"""<h2>Tasks <span class="pill acc">source: SYSTASK</span></h2>
<div class="grid">
<div class="kpi"><div class="n">{len(_tasks)}</div><div class="l">Tasks tracked</div></div>
<div class="kpi"><div class="n">{_open}</div><div class="l">Open</div></div>
<div class="kpi"><div class="n">{_prog}</div><div class="l">In progress</div></div></div>
<table><tr><th>Task</th><th>Lane</th><th>Channel</th><th>Status</th><th>Assignee</th></tr>
{_trows}</table>""")
else:
    tasks_block=('<h2>Tasks</h2><div class="note w">SYSTASK is not loaded yet. Seed it '
                 '(<code>python tools/tracking/seed_tracking.py</code>) and load it '
                 '(<code>DO tools\\tracking\\load_tracking_tables.dts</code> via datarun), '
                 'then regenerate with <code>--source dbf</code>.</div>')

portal_map="""<div class="note"><b>The portal front door, in order</b>
<ol style="margin:7px 0 0">
<li><code>AI_README.md</code> -- entry point; step 0b says check <code>board.worklog</code> first.</li>
<li><code>AI_PORTAL.md</code> -- what this repo is, and what <code>C:\\x64base</code> is not.</li>
<li><code>labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md</code> -- contracts, regression doctrine,
definition of done, house conventions, git hygiene.</li>
<li><code>docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md</code> -- which kind of AI you are talking to.</li>
<li>The lane doc for whatever you are touching, then its newest run below.</li>
</ol></div>"""
if PUBLIC:
    portal_map = portal_map.replace('what <code>C:\\x64base</code> is not',
                                    'what the publication-staging tree is not')

howret="""<div class="note w"><b>How to return to the last agent on a lane</b><br>
<code>current_by_lane[LANE]</code> -&gt; <code>runs[run_id]</code> -&gt; <code>chat_handle</code>.
Every run here is <code>MAINTAINER_ATTESTED</code>: the platform stamps the session id
<i>not_exposed</i>, so the <b>closeout is the recovery path</b>, not the chat link.
That is by design -- the record lives in the repo, not in a vendor's session store.</div>"""

_source_pill = {
    'dbf': ' <span class="pill acc">source: DBF tracking tables</span>',
    'fragments': ' <span class="pill acc">source: current local registry fragments</span>',
}.get(_args.source, '')
_sub3=("Who worked what, what is proven, and where to pick the thread back up."
       + _source_pill)
r3=page("DotTalk++ AI Portal -- Lanes, Runs and Proofs",
        _sub3,
        f"""<div class="grid">
<div class="kpi"><div class="n">{len(by_lane)}</div><div class="l">Tracked lanes</div></div>
<div class="kpi"><div class="n">{len(runs)}</div><div class="l">Recorded runs</div></div>
<div class="kpi"><div class="n">{nobs}</div><div class="l">Runtime-observed proofs</div></div>
<div class="kpi"><div class="n">{nsrc}</div><div class="l">Source-defined proofs</div></div>
</div>"""
        + portal_map
        + "<h2>Lanes -- and the newest run on each</h2>" + lane_tbl + closed_block + howret
        + "<h2>Runs</h2>" + runcards
        + tasks_block
        + "<h2>Proof ledger</h2>" + proof_tbl)
emit('AI_PORTAL_REPORT.html', r3)

# =====================================================================
# RULINGS -- delegated to build_rulings_report.py (document state, not DBF)
# =====================================================================
def _build_rulings():
    """Run the rulings generator in-process and return (open, ratified) or None.

    Kept as a separate module because it reads DOCUMENT state (the ruling sheets
    and Tier 0) rather than the DBF store, and must stay runnable on a host that
    has no data directory. Failure here is advisory: the rest of the console is
    still worth emitting, so this never aborts the build."""
    import io, runpy, contextlib, re as _re
    script = ROOT / 'tools' / 'reports' / 'build_rulings_report.py'
    if not script.is_file():
        return None
    # The rulings view is PRIVATE (portal.yaml: report.aif_rulings) -- unratified
    # decisions, steward recommendations, declared biases, the open error ledger.
    # It does not route through emit(), so the private-skip there cannot protect
    # it; refuse at the source instead. Gate on PUBLIC alone, NOT on is_private():
    # `private` means never PUBLISH, not never GENERATE -- BBS_ACCESS_REPORT is
    # private and still builds for internal use. An earlier revision checked
    # `PUBLIC or is_private(...)`, which blocked the leak AND suppressed the
    # internal copy, i.e. the report's only reason to exist. Gating on the flag
    # also fails closed if the registry entry is ever removed.
    if PUBLIC:
        print('SKIPPED (private per portal.yaml): AIF_RULINGS_REPORT.html')
        return None
    argv = sys.argv[:]
    buf = io.StringIO()
    try:
        sys.argv = [str(script), '--root', str(ROOT), '--out', str(OUT)]
        with contextlib.redirect_stdout(buf):
            runpy.run_path(str(script), run_name='__main__')
    except SystemExit as ex:
        if ex.code not in (0, None):
            print(f'rulings report: FAILED (exit {ex.code}) -- console emitted without it')
            return None
    except Exception as ex:
        print(f'rulings report: FAILED ({type(ex).__name__}: {ex}) -- console emitted without it')
        return None
    finally:
        sys.argv = argv
    out = buf.getvalue().strip()
    print(out or 'rulings report: wrote AIF_RULINGS_REPORT.html')
    m = _re.search(r'\((\d+) open, (\d+) ratified', out)
    return (int(m.group(1)), int(m.group(2))) if m else None

_rulings = _build_rulings()

# =====================================================================
# INDEX
# =====================================================================
_idx_kpi = f"""<div class="grid">
<div class="kpi"><div class="n">{len(B['SYSBOARD'])}</div><div class="l">BBS boards</div></div>
<div class="kpi"><div class="n">{len(B['SYSPOST'])}</div><div class="l">Posts</div></div>
<div class="kpi"><div class="n">{len(I['SYSMEMBER'])}</div><div class="l">Members</div></div>
<div class="kpi"><div class="n">{len(by_lane)}</div><div class="l">Lanes</div></div>
{f'<div class="kpi"><div class="n">{_rulings[0]}</div><div class="l">Open rulings</div></div>' if _rulings else ''}
</div>"""

_rulings_card = ('' if _rulings is None else f"""
<div class="card"><h3 style="margin-top:0"><a href="AIF_RULINGS_REPORT.html">AI Portal -- Open Rulings</a></h3>
<div class="dim small">Every owner decision outstanding across AIF lanes, with the steward's
recommendation and any declared bias, plus what each ruling blocks.
Answers: <i>what is waiting on me, and what unblocks if I decide it?</i>
Currently <b>{_rulings[0]} open</b>, {_rulings[1]} ratified.</div>
<div style="margin-top:8px"><span class="pill bad">private -- never publish</span></div></div>""")

_regenerate_command = f"python tools/reports/build_reports.py --source {_args.source}"
_regenerate_source = {
    "fragments": "authoritative local registry fragments",
    "dbf": "derived DBF tracking tables",
    "yaml": "reviewed flat YAML snapshot inputs",
}[_args.source]

if PUBLIC:
    idx_body = _idx_kpi + """
<div class="card"><h3 style="margin-top:0"><a href="AI_PORTAL_REPORT.html">AI Portal -- Lanes, Runs and Proofs</a></h3>
<div class="dim small">Every tracked lane with its evidence class, each recorded run with its
owner/committer/author split, and the full proof ledger.
Answers: <i>what has been worked, what is actually proven, and where do I pick it back up?</i></div></div>

<div class="card"><h3 style="margin-top:0"><a href="BBS_BOARDS_REPORT.html">AI-BBS -- Boards and Traffic</a></h3>
<div class="dim small">The local bulletin-board structure, post permissions, and public traffic,
including the agent handoff worklog. Answers: <i>what is on the board right now?</i></div></div>

<div class="card"><h3 style="margin-top:0"><a href="diagrams">AI-BBS -- Process &amp; Data-Flow Diagrams</a></h3>
<div class="dim small">ERD + DFD + PFDs: how identity/RBAC, the boards, and the submission-to-curation
ledger connect. Answers: <i>how does the AI-BBS actually work?</i></div></div>

<div class="note">Read-only snapshots that run entirely locally (the BBS listener is loopback-only).
The access-and-identity report -- the authentication-surface map -- is kept internal by design and is not
published here.</div>"""
else:
    idx_body = _idx_kpi + """
<div class="card"><h3 style="margin-top:0"><a href="console">Tracking Maintenance Console</a></h3>
<div class="dim small">Interactive CRUD over the DBF tracking tables -- lanes, runs, proofs, tasks.
The console visibly reports its current posture. Execute is available only when the gateway is launched
with <code>--enable-write</code>; otherwise operations emit the DotScript to run. Answers:
<i>inspect or maintain the tracking state.</i></div>
<div style="margin-top:8px"><span class="pill acc">posture shown at runtime</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="AI_PORTAL_REPORT.html">AI Portal -- Lanes, Runs and Proofs</a></h3>
<div class="dim small">The front door in reading order, every tracked lane with its evidence class,
each recorded run with its owner/committer/author split, and the full proof ledger.
Answers: <i>what has been worked, what is actually proven, and where do I pick it back up?</i></div>
<div style="margin-top:8px"><span class="pill ok">publication candidate -- after review</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="BBS_BOARDS_REPORT.html">BBS -- Boards and Traffic</a></h3>
<div class="dim small">All six rooms, their post permissions, and every post ever made, rendered by board
with handoff posts pretty-printed. Answers: <i>what is on the board right now?</i></div>
<div style="margin-top:8px"><span class="pill warn">registry policy -- board.worklog currently included</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="BBS_ACCESS_REPORT.html">BBS -- Access and Identity</a></h3>
<div class="dim small">Members, roles, the full permission matrix, who may post to which room,
and the connection recipe. Answers: <i>who can do what, and how do I get in?</i></div>
<div style="margin-top:8px"><span class="pill bad">private -- never publish</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="/memory">Frontal Memory -- persistent-memory architecture</a></h3>
<div class="dim small">The private site section for the persistent-memory system: the thesis and
architecture, the AI coordination team model, and the triage optimization roadmap. Answers:
<i>how does cross-session memory work here?</i></div>
<div style="margin-top:8px"><span class="pill acc">private -- unlisted site section</span></div></div>
""" + _rulings_card + f"""

<div class="note"><b>Regenerate</b><br>
<pre class="m" style="margin:7px 0 0">{e(_regenerate_command)}</pre>
<div class="small dim" style="margin-top:7px">Reads {e(_regenerate_source)} directly. Read-only --
it never writes to the store, so it is safe to run while the daemon is up.</div></div>"""

idx = page("DotTalk++ AI", "Human-readable views over live project state.", idx_body)
emit('index.html', idx)

# Static passthrough: the process/data-flow diagram gallery (conceptual, not
# data-driven). Emitting it here keeps it in the governed set, so stage_public's
# wholesale replace does not drop it. Source of truth: labtalk/diagrams/*.mmd.
_diag = ROOT/'tools'/'reports'/'static'/'PROCESS_DIAGRAMS.html'
if _diag.exists():
    emit('PROCESS_DIAGRAMS.html', _diag.read_text(encoding='utf-8'))
