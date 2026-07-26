#!/usr/bin/env python3
"""
Human-readable HTML reports over live DotTalk++ state (AI Portal + BBS).

Reads, READ-ONLY:
  dottalkpp/data/metadata/bbs/{SYSBOARD,SYSTHREAD,SYSPOST}.dbf
  dottalkpp/data/metadata/identity/{SYSMEMBER,SYSROLE,SYSPERM,SYSMEMROLE,SYSROLEPERM,SYSUSER,SYSGRANT}.dbf
  labtalk/registries/{ai_runs,proofs}.yaml
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
_args = _ap.parse_args()

ROOT = Path(_args.root).resolve()
MD   = ROOT/'dottalkpp'/'data'/'metadata'
OUT  = Path(_args.out) if _args.out else ROOT/'docs'/'reports'
OUT.mkdir(parents=True, exist_ok=True)
if not MD.is_dir():
    sys.exit(f"no metadata dir at {MD} -- pass --root <repo>")
NOW  = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

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

CSS = """
:root{--bg:#0f1419;--panel:#171e26;--line:#26323f;--tx:#dfe7ef;--dim:#8ba0b4;
--acc:#5cc8ff;--ok:#4ec9a0;--warn:#e8b84b;--bad:#e86a6a;--mono:ui-monospace,"Cascadia Code",Consolas,monospace}
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
td{padding:8px 9px;border-bottom:1px solid #1e2731;vertical-align:top}
tr:last-child td{border-bottom:none}
code,.m{font-family:var(--mono);font-size:12.5px}
.pill{display:inline-block;padding:1.5px 8px;border-radius:11px;font-size:11px;font-family:var(--mono);
border:1px solid var(--line);background:#1d262f;color:var(--dim)}
.pill.ok{color:var(--ok);border-color:#2c5c4c}.pill.warn{color:var(--warn);border-color:#5c4c22}
.pill.bad{color:var(--bad);border-color:#5c2c2c}.pill.acc{color:var(--acc);border-color:#28516b}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:11px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.kpi .n{font-size:26px;font-weight:600;color:var(--acc);line-height:1.1}
.kpi .l{font-size:11.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;margin-top:3px}
.post{border-left:2px solid var(--line);padding:2px 0 2px 13px;margin:13px 0}
.post .h{font-size:12px;color:var(--dim);font-family:var(--mono)}
.post .b{margin-top:5px;white-space:pre-wrap;word-break:break-word}
.dim{color:var(--dim)}.small{font-size:12.5px}
.note{border-left:3px solid var(--acc);background:#141c24;padding:10px 14px;margin:13px 0;border-radius:0 6px 6px 0}
.note.w{border-left-color:var(--warn)}
ul{margin:7px 0;padding-left:20px}li{margin:3px 0}
a{color:var(--acc)}
.foot{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);color:var(--dim);font-size:12px}
.band{border-radius:7px;padding:9px 14px;margin:0 0 18px;font-size:12.5px;font-weight:600;
letter-spacing:.3px}
.band.priv{background:#3a1d1d;border:1px solid #6b2f2f;color:#ffb3b3}
.band.int{background:#1d2a33;border:1px solid #2e4a5c;color:#9fd0ea}
kbd{font-family:var(--mono);background:#1d262f;border:1px solid var(--line);border-radius:4px;padding:1px 6px;font-size:12px}
"""

BANDS = {
 'private': ('band priv',
   'PRIVATE -- DO NOT PUBLISH. Authentication-surface map (member keys, permission '
   'matrix, port and protocol). Internal use only. See docs/reports/REPORTS_PUBLICATION_NOTE_V1.md'),
 'internal': ('band int',
   'INTERNAL -- review before any publication to x64base.com or public main. '
   'See docs/reports/REPORTS_PUBLICATION_NOTE_V1.md'),
}

def page(title, sub, body, sensitivity='internal'):
    cls, msg = BANDS.get(sensitivity, BANDS['internal'])
    band = f'<div class="{cls}">{e(msg)}</div>'
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<style>{CSS}</style></head><body><div class="wrap">
{band}
<h1>{e(title)}</h1><div class="sub">{sub}</div>
{body}
<div class="foot">Generated {NOW} from live DotTalk++ state
(<code>dottalkpp/data/metadata/</code>). Read-only snapshot -- regenerate with
<code>tools/reports/build_reports.py</code>.</div>
</div></body></html>"""

# =====================================================================
# REPORT 1 -- BBS BOARDS (the rooms and what is in them)
# =====================================================================
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

howto="""<div class="note"><b>How to read a board yourself</b><br>
Start the daemon (or <kbd>BBS SERVE</kbd> in the shell), then from any socket client:
<pre class="m" style="margin:7px 0 0">AUTH member.derald &lt;token&gt;
BBS READ board.worklog
QUIT</pre></div>"""

r1=page("DotTalk++ BBS -- Boards and Traffic",
        "Every room on the board, who may post to it, and everything posted so far.",
        kpi+board_tbl+howto+"<h2>All posts, by board</h2>"+feed)
(OUT/'BBS_BOARDS_REPORT.html').write_text(r1,encoding='utf-8')
print("wrote BBS_BOARDS_REPORT.html")

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
        + "<h2>Members</h2>" + mem_tbl
        + "<h2>Who may post where</h2>" + who_tbl
        + "<h2>Roles and their permissions</h2>" + role_tbl
        + "<h2>Connecting</h2>" + conn,
        sensitivity='private')
(OUT/'BBS_ACCESS_REPORT.html').write_text(r2,encoding='utf-8')
print("wrote BBS_ACCESS_REPORT.html")

# =====================================================================
# REPORT 3 -- AI PORTAL: lanes, runs, proofs, who is working what
# =====================================================================
RG = ROOT/'labtalk'/'registries'
rd = lambda n: yaml.safe_load((RG/n).read_text(encoding='utf-8',errors='replace'))
runs_y   = rd('ai_runs.yaml')
proofs_y = rd('proofs.yaml')
runs   = runs_y.get('runs',[])
by_lane= runs_y.get('current_by_lane',{})
by_proj= runs_y.get('current_by_project',{})
proofs = proofs_y.get('proofs',[])

# lane rows from the intake queue table
lane_rows={}
qtxt=(ROOT/'docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md').read_text(encoding='utf-8',errors='replace')
for l in qtxt.splitlines():
    if re.match(r'^\|\s*AIF-\d+', l):
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        if len(c)>=6:
            lane_rows[c[0]]={'title':c[1],'tags':c[2],'evidence':c[5] if len(c)>5 else '','notes':c[-1]}

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

portal_map="""<div class="note"><b>The portal front door, in order</b>
<ol style="margin:7px 0 0">
<li><code>AI_README.md</code> -- entry point; step 0b says check <code>board.worklog</code> first.</li>
<li><code>AI_PORTAL.md</code> -- what this repo is, and what <code>C:\\x64base</code> is not.</li>
<li><code>labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md</code> -- contracts, regression doctrine,
definition of done, house conventions, git hygiene.</li>
<li><code>docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md</code> -- which kind of AI you are talking to.</li>
<li>The lane doc for whatever you are touching, then its newest run below.</li>
</ol></div>"""

howret="""<div class="note w"><b>How to return to the last agent on a lane</b><br>
<code>current_by_lane[LANE]</code> -&gt; <code>runs[run_id]</code> -&gt; <code>chat_handle</code>.
Every run here is <code>MAINTAINER_ATTESTED</code>: the platform stamps the session id
<i>not_exposed</i>, so the <b>closeout is the recovery path</b>, not the chat link.
That is by design -- the record lives in the repo, not in a vendor's session store.</div>"""

r3=page("DotTalk++ AI Portal -- Lanes, Runs and Proofs",
        "Who worked what, what is proven, and where to pick the thread back up.",
        f"""<div class="grid">
<div class="kpi"><div class="n">{len(by_lane)}</div><div class="l">Tracked lanes</div></div>
<div class="kpi"><div class="n">{len(runs)}</div><div class="l">Recorded runs</div></div>
<div class="kpi"><div class="n">{nobs}</div><div class="l">Runtime-observed proofs</div></div>
<div class="kpi"><div class="n">{nsrc}</div><div class="l">Source-defined proofs</div></div>
</div>"""
        + portal_map
        + "<h2>Lanes -- and the newest run on each</h2>" + lane_tbl + howret
        + "<h2>Runs</h2>" + runcards
        + "<h2>Proof ledger</h2>" + proof_tbl)
(OUT/'AI_PORTAL_REPORT.html').write_text(r3,encoding='utf-8')
print("wrote AI_PORTAL_REPORT.html")

# =====================================================================
# INDEX
# =====================================================================
idx=page("DotTalk++ Reports",
 "Human-readable views over live project state. Regenerate any time.",
 f"""<div class="grid">
<div class="kpi"><div class="n">{len(B['SYSBOARD'])}</div><div class="l">BBS boards</div></div>
<div class="kpi"><div class="n">{len(B['SYSPOST'])}</div><div class="l">Posts</div></div>
<div class="kpi"><div class="n">{len(I['SYSMEMBER'])}</div><div class="l">Members</div></div>
<div class="kpi"><div class="n">{len(by_lane)}</div><div class="l">Lanes</div></div>
</div>

<div class="card"><h3 style="margin-top:0"><a href="AI_PORTAL_REPORT.html">AI Portal -- Lanes, Runs and Proofs</a></h3>
<div class="dim small">The front door in reading order, every tracked lane with its evidence class,
each recorded run with its owner/committer/author split, and the full proof ledger.
Answers: <i>what has been worked, what is actually proven, and where do I pick it back up?</i></div>
<div style="margin-top:8px"><span class="pill ok">publication candidate -- after review</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="BBS_BOARDS_REPORT.html">BBS -- Boards and Traffic</a></h3>
<div class="dim small">All six rooms, their post permissions, and every post ever made, rendered by board
with handoff posts pretty-printed. Answers: <i>what is on the board right now?</i></div>
<div style="margin-top:8px"><span class="pill warn">selective -- exclude board.worklog</span></div></div>

<div class="card"><h3 style="margin-top:0"><a href="BBS_ACCESS_REPORT.html">BBS -- Access and Identity</a></h3>
<div class="dim small">Members, roles, the full permission matrix, who may post to which room,
and the connection recipe. Answers: <i>who can do what, and how do I get in?</i></div>
<div style="margin-top:8px"><span class="pill bad">private -- never publish</span></div></div>

<div class="note"><b>Regenerate</b><br>
<pre class="m" style="margin:7px 0 0">python tools/reports/build_reports.py</pre>
<div class="small dim" style="margin-top:7px">Reads the DBF tables and YAML registries directly. Read-only --
it never writes to the store, so it is safe to run while the daemon is up.</div></div>""")
(OUT/'index.html').write_text(idx,encoding='utf-8')
print("wrote index.html")
