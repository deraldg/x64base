#!/usr/bin/env python3
"""build_rulings_report.py -- generated view over the AIF ruling sheets.

Companion to build_reports.py, which renders live DBF state. This one renders
live DOCUMENT state: it parses the ruling sheet(s) under docs/maintenance/ and
the generated Tier 0 projection, and emits docs/reports/AIF_RULINGS_REPORT.html.

Nothing here is hand-entered. Every count, status and date is derived at run
time, so the page cannot disagree with the sheet the way a hand-written board
does (AIF-082 charter 12.x -- a perishable artifact in a folder of generated
ones is the drift this lane exists to name).

Style is not duplicated: the CSS and the classification BANDS are lifted out of
build_reports.py at run time, so the two reports cannot skew.

    python tools/reports/build_rulings_report.py
    python tools/reports/build_rulings_report.py --root D:/code/ccode

Read-only. Touches no store, runs no git.
"""
from __future__ import annotations
import argparse, datetime, html, re, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=None)
ap.add_argument('--out', default=None)
A = ap.parse_args()

ROOT = Path(A.root).resolve() if A.root else Path(__file__).resolve().parents[2]
OUT = Path(A.out) if A.out else ROOT / 'docs' / 'reports'
OUT.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
e = lambda s: html.escape(str(s), quote=False)

SHEET_GLOB = 'AIF_*RULING_SHEET*.md'
MAINT = ROOT / 'docs' / 'maintenance'
TIER0 = ROOT / 'labtalk' / 'ai_portal' / 'TIER0_STATE.md'


# --------------------------------------------------------------- shared style
def borrowed_style() -> tuple[str, dict]:
    """Lift CSS and BANDS out of build_reports.py so the two never diverge."""
    src = (ROOT / 'tools' / 'reports' / 'build_reports.py')
    css, bands = '', {}
    if src.is_file():
        t = src.read_text(encoding='utf-8', errors='replace')
        m = re.search(r'^CSS\s*=\s*"""(.*?)"""', t, re.S | re.M)
        if m:
            css = m.group(1)
        mb = re.search(r"^BANDS\s*=\s*\{(.*?)^\}", t, re.S | re.M)
        if mb:
            for key, cls, msg in re.findall(
                    r"'(\w+)':\s*\('([^']+)',\s*((?:'[^']*'\s*)+)\)", mb.group(1)):
                bands[key] = (cls, ''.join(re.findall(r"'([^']*)'", msg)))
    if not css:
        css = ('body{background:#0f1419;color:#dfe7ef;font-family:sans-serif}'
               '.wrap{max-width:1080px;margin:0 auto;padding:32px 22px}')
    if not bands:
        bands = {'internal': ('band int', 'INTERNAL -- review before any publication.')}
    return css, bands


def borrowed_theme_script() -> str:
    """Lift THEME_SCRIPT out of build_reports.py, for the same reason as the CSS.

    Added 2026-08-13 with the light/dark palette. Without it this page would
    borrow a stylesheet whose :root is light and never receive the class that
    selects the dark half -- themed CSS, no way to reach the theme. Borrowing
    beats copying here for the same reason the CSS is borrowed: one edit, and
    the reports cannot end up disagreeing about what 'dark' means.
    """
    src = (ROOT / 'tools' / 'reports' / 'build_reports.py')
    if src.is_file():
        t = src.read_text(encoding='utf-8', errors='replace')
        m = re.search(r'^THEME_SCRIPT\s*=\s*\((.*?)\)\s*$', t, re.S | re.M)
        if m:
            return ''.join(re.findall(r'"([^"]*)"', m.group(1)))
    return ''


# ------------------------------------------------------------------- parsing
ROW = re.compile(r'^\|\s*\*\*([0-9A-Za-z.]+)\*\*\s*\|(.*)$')
PARA = re.compile(r'^\*\*(R\d+[a-z0-9.]*)\s*--\s*(.+?)\.?\*\*', re.M)
GROUP = re.compile(r'^#{2,3}\s+(Group\s+\w+.*)$', re.M)
RATIFIED = re.compile(r'^#{2,3}\s+Group\s+(\w+)\s+ratified\s*--\s*(\S+)', re.M | re.I)
TOTAL = re.compile(r'Total open:\s*(\d+)', re.I)


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.split('|')]


def parse_sheet(p: Path) -> dict:
    txt = p.read_text(encoding='utf-8', errors='replace')
    lines = txt.split('\n')
    ratified = {g.upper(): d for g, d in RATIFIED.findall(txt)}
    items, group = [], '(ungrouped)'
    for ln in lines:
        g = GROUP.match(ln)
        if g:
            group = g.group(1).strip()
            continue
        m = ROW.match(ln)
        if not m:
            continue
        c = cells(ln)
        rid = m.group(1)
        # | id | proposal | cost | reversible | recommend | ruling |
        prop = c[2] if len(c) > 2 else ''
        rec = c[5] if len(c) > 6 else (c[-2] if len(c) > 2 else '')
        letter = re.search(r'Group\s+(\w+)', group)
        settled = bool(letter and letter.group(1).upper() in ratified)
        items.append(dict(id=rid, group=group, text=prop, rec=rec,
                          settled=settled,
                          date=ratified.get(letter.group(1).upper()) if letter else None))
    # narrative R-rulings (Group E and later addenda)
    for rid, head in PARA.findall(txt):
        i = txt.index(f'**{rid} --')
        nxt = txt.find('\n\n**', i + 4)
        body = txt[i:nxt if nxt > 0 else i + 1400]
        body = re.sub(r'^\*\*.*?\*\*\s*', '', body, count=1, flags=re.S)
        recm = re.search(r'[Rr]ecommend(?:ation)?(?:ed)?[:\s]+(?:is\s+)?\*\*(.+?)\*\*', body)
        items.append(dict(id=rid, group='Group E -- narrative rulings', text=head.strip(),
                          detail=' '.join(body.split())[:520],
                          rec=recm.group(1) if recm else '', settled=False, date=None))
    tot = TOTAL.findall(txt)
    # RUNNING-TOTAL RETIRED sentinel (owner ruling 2026-08-10): the hand-kept
    # footer drifted (declared 20, measured 18) and was retired per the
    # no-perishable-literals rule. Earlier "Total open" lines remain in the
    # sheet as historical record; once the sentinel is present this page owns
    # the count and stops comparing against them.
    retired = 'RUNNING-TOTAL RETIRED' in txt
    return dict(path=p, items=items, ratified=ratified,
                declared_open=None if retired else (int(tot[-1]) if tot else None),
                total_retired=retired,
                mtime=datetime.datetime.utcfromtimestamp(p.stat().st_mtime))


def parse_tier0() -> dict:
    d = {}
    if not TIER0.is_file():
        return d
    for ln in TIER0.read_text(encoding='utf-8', errors='replace').split('\n'):
        m = re.match(r'\s{2,}(\w[\w ]*?)\s*:\s*(.+?)\s*$', ln)
        if m:
            d.setdefault(m.group(1).strip(), m.group(2).strip())
        if ln.strip().startswith('- '):
            d.setdefault('_warn', []).append(ln.strip()[2:]) if isinstance(
                d.get('_warn'), list) else d.update(_warn=[ln.strip()[2:]])
    return d


# ------------------------------------------------- SYSRULING (dogfooded state)
RULING_DBF = ROOT / 'dottalkpp' / 'data' / 'metadata' / 'portal' / 'SYSRULING.dbf'
STATUS = {0: 'proposed', 1: 'ratified', 2: 'rejected', 3: 'superseded', 4: 'withdrawn'}


def _borrow_read_dbf():
    """Lift read_dbf() out of build_reports.py rather than copying it, for the
    same reason the CSS is borrowed: one definition, no skew. Returns None if the
    companion script is absent, which is not an error -- the markdown path still
    works and this module must stay runnable on a host with no data directory."""
    src = ROOT / 'tools' / 'reports' / 'build_reports.py'
    if not src.is_file():
        return None
    t = src.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'^def read_dbf\(path\):\n(?:[ \t].*\n|\n)+', t, re.M)
    if not m:
        return None
    ns: dict = {}
    try:
        exec('import struct\nfrom pathlib import Path\n' + m.group(0), ns)
    except Exception:
        return None
    return ns.get('read_dbf')


def parse_sysruling() -> dict | None:
    """Current status per RULEID plus the full dated transition log.

    APPEND-ONLY by design (ruling_schema.hpp): a status change is a new row with
    a later DECIDEDAT, never an update in place, so the table IS the history.
    Current status of a ruling is its row with the highest DECIDEDAT."""
    if not RULING_DBF.is_file():
        return None
    rd = _borrow_read_dbf()
    if rd is None:
        return None
    try:
        _, rows = rd(RULING_DBF)
    except Exception as ex:
        print(f'SYSRULING present but unreadable ({type(ex).__name__}: {ex}) -- '
              'falling back to the markdown sheets')
        return None

    def num(v):
        try:
            return int(str(v).strip() or 0)
        except ValueError:
            return 0

    cur, log = {}, []
    for r in rows:
        rid = (r.get('RULEID') or '').strip()
        if not rid:
            continue
        at = num(r.get('DECIDEDAT'))
        st = num(r.get('STATUS'))
        when = (datetime.datetime.utcfromtimestamp(at).strftime('%Y-%m-%dT%H:%MZ')
                if at else '--')
        log.append((when, f"{rid} -> {STATUS.get(st, f'status {st}')}"
                          + (f" ({r.get('NOTE','').strip()})" if r.get('NOTE', '').strip() else '')))
        if rid not in cur or at >= cur[rid]['_at']:
            cur[rid] = dict(id=rid, group=(r.get('RULEGROUP') or '').strip() or '(ungrouped)',
                            lane=(r.get('LANE') or '').strip(), status=STATUS.get(st, str(st)),
                            settled=st in (1, 2, 3, 4), blocks=(r.get('BLOCKS') or '').strip(),
                            text=(r.get('NOTE') or '').strip(), rec='', date=when, _at=at)
    return dict(current=cur, log=sorted(set(log)), rows=len(rows))


# ------------------------------------------------------------------- history
def history(sheets: list[dict]) -> list[tuple[str, str]]:
    """Dated events the SHEETS actually record. Not invented: if a ruling has
    no recorded date, it does not appear here, and that absence is the finding."""
    ev = []
    for s in sheets:
        ev.append((s['mtime'].strftime('%Y-%m-%dT%H:%MZ'),
                   f"{s['path'].name} last modified"))
        for grp, when in s['ratified'].items():
            n = sum(1 for i in s['items'] if i['settled']
                    and re.search(rf'Group\s+{grp}\b', i['group'], re.I))
            ev.append((when, f'Group {grp} ratified -- {n} row(s) settled'))
    return sorted(set(ev))


# --------------------------------------------------------------------- render
def main() -> int:
    sheets = [parse_sheet(p) for p in sorted(MAINT.glob(SHEET_GLOB))]
    if not sheets:
        sys.exit(f'no ruling sheet matching {SHEET_GLOB} under {MAINT}')
    items = [i for s in sheets for i in s['items']]
    sysr = parse_sysruling()
    if sysr:
        # SYSRULING is authoritative for STATUS where it has a row; the sheet
        # still supplies the proposal text, which deliberately does not live in
        # the table (ruling_schema.hpp -- state here, prose in the sheet).
        for i in items:
            r = sysr['current'].get(i['id'])
            if r:
                i['settled'], i['date'], i['status'] = r['settled'], r['date'], r['status']
                i['blocks'] = r.get('blocks', '')
        for rid, r in sysr['current'].items():
            if not any(i['id'] == rid for i in items):
                items.append(dict(r, text=r['text'] or '(row in SYSRULING with no sheet entry)'))
    openi = [i for i in items if not i['settled']]
    done = [i for i in items if i['settled']]
    t0 = parse_tier0()
    css, bands = borrowed_style()
    theme_script = borrowed_theme_script()

    kpi = [(len(openi), 'open rulings'), (len(done), 'ratified'),
           (len(sheets), 'sheet(s) parsed')]
    for label, key in (('unpushed', 'unpushed'), ('HEAD', 'HEAD')):
        if key in t0:
            kpi.append((t0[key].split()[0], label))
    b = ['<div class="grid">' + ''.join(
        f'<div class="kpi"><div class="n">{e(n)}</div><div class="l">{e(l)}</div></div>'
        for n, l in kpi) + '</div>']

    declared = sheets[0]['declared_open']
    if declared is not None and declared != len(openi):
        b.append(f'<div class="note w"><b>Count disagreement -- derived vs hand-maintained</b><br>'
                 f'The sheet declares <code>Total open: {declared}</code>; parsing finds '
                 f'<b>{len(openi)}</b>. A hand-kept running total drifts every time a row is added '
                 'without updating the footer; the derived figure is the measurement. '
                 'Correct the sheet, or drop the hand-kept total and let this page own it.</div>')
    elif sheets[0].get('total_retired'):
        b.append('<div class="note"><b>Hand-kept total retired</b> (owner ruling 2026-08-10) -- '
                 'this page caught the footer drifting (declared 20, measured 18) and now owns '
                 'the count. Historical "Total open" lines remain in the sheet as record; the '
                 'derived figure above is the measurement.</div>')

    by = {}
    for i in openi:
        by.setdefault(i['group'], []).append(i)
    for grp, rows in by.items():
        b.append(f'<h2>{e(grp)}</h2>')
        for i in rows:
            rec = f'<div class="small"><span class="pill acc">{e(i["rec"])}</span></div>' \
                if i.get('rec') else ''
            det = f'<div class="dim small" style="margin-top:6px">{e(i.get("detail",""))}</div>' \
                if i.get('detail') else ''
            b.append(f'<div class="card"><h3 style="margin-top:0">'
                     f'<span class="m">{e(i["id"])}</span> &mdash; {e(i["text"])[:300]}</h3>'
                     f'{det}{rec}</div>')

    if done:
        b.append('<h2>Ratified</h2><table><tr><th>id</th><th>group</th><th>when</th>'
                 '<th>proposal</th></tr>')
        for i in done:
            b.append(f'<tr><td class="m">{e(i["id"])}</td><td class="dim small">'
                     f'{e(i["group"])}</td><td class="m small">{e(i.get("date") or "--")}</td>'
                     f'<td class="small">{e(i["text"])[:220]}</td></tr>')
        b.append('</table>')

    ev = history(sheets)
    b.append('<h2>Recorded history</h2>')
    if sysr:
        b.append(f'<div class="note"><b>Source: <code>SYSRULING</code></b> &mdash; '
                 f'{sysr["rows"]} append-only row(s) in the DBF store. A status change is a new '
                 'row with a later <code>DECIDEDAT</code>, never an update in place, so the table '
                 'IS the history. Current status of a ruling is its row with the highest '
                 '<code>DECIDEDAT</code>.</div>')
        b.append('<table><tr><th>when</th><th>transition</th></tr>' + ''.join(
            f'<tr><td class="m small">{e(w)}</td><td class="small">{e(x)}</td></tr>'
            for w, x in sysr['log']) + '</table>')
    elif ev:
        b.append('<table><tr><th>when</th><th>event</th></tr>' + ''.join(
            f'<tr><td class="m small">{e(w)}</td><td class="small">{e(x)}</td></tr>'
            for w, x in ev) + '</table>')
    if not sysr:
        b.append('<div class="note w"><b>History is thin, and that is a finding, not a bug.</b><br>'
                 'Only two kinds of dated event exist to render: a group ratification header and a '
                 'file mtime. Individual rulings carry no dated status transition, because the sheet '
                 'stores them as prose with an empty <code>Ruling</code> cell. '
                 'The schema that fixes this is authored -- <code>include/portal/ruling_schema.hpp</code>, '
                 '<code>SYSRULING</code>, append-only, <code>proposed / ratified / rejected / '
                 'superseded / withdrawn</code> with a UTC stamp per transition -- but the table is '
                 'not created or seeded yet, so this page is still deriving from markdown. '
                 'Recipe: <code>docs/maintenance/RULING_STATE_DOGFOOD_V1.md</code>. '
                 'Until it is seeded, this section can only show what was written down, and most of '
                 'it was not.</div>')

    if t0:
        rows = ''.join(f'<tr><td class="dim small">{e(k)}</td><td class="m small">{e(v)}</td></tr>'
                       for k, v in t0.items() if not k.startswith('_'))
        b.append(f'<h2>Tree state (from Tier 0)</h2><table>{rows}</table>')
        if t0.get('_warn'):
            b.append('<div class="note w"><b>Tier 0 staleness warnings</b><ul>' + ''.join(
                f'<li class="small">{e(w)}</li>' for w in t0['_warn']) + '</ul></div>')
    else:
        b.append('<div class="note w">No <code>TIER0_STATE.md</code> found -- tree state omitted '
                 'rather than guessed. Regenerate with '
                 '<code>python labtalk/ai_portal/generate_tier0_state.py</code>.</div>')

    b.append('<div class="note"><b>Regenerate</b><br><pre class="m" style="margin:7px 0 0">'
             'python tools/reports/build_rulings_report.py</pre>'
             '<div class="small dim" style="margin-top:7px">Derives every figure from the ruling '
             'sheet and Tier 0. Runs no git and writes to no store.</div></div>')

    cls, msg = bands.get('internal', ('band int', 'INTERNAL'))
    src = ', '.join(s['path'].name for s in sheets)
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DotTalk++ AI Portal -- Open Rulings</title>
<style>{css}</style><script>{theme_script}</script></head><body><div class="wrap">
<div class="{cls}">{e(msg)}</div>
<h1>AI Portal -- Open Rulings</h1>
<div class="sub">Owner decisions outstanding across AIF lanes. Generated from {e(src)}
and <code>TIER0_STATE.md</code> -- nothing on this page is hand-entered.</div>
{''.join(b)}
<div class="foot">Generated {NOW} from <code>docs/maintenance/{e(SHEET_GLOB)}</code>.
Read-only -- regenerate with <code>tools/reports/build_rulings_report.py</code>.</div>
</div></body></html>"""
    (OUT / 'AIF_RULINGS_REPORT.html').write_text(page, encoding='utf-8')
    print(f'wrote AIF_RULINGS_REPORT.html  '
          f'({len(openi)} open, {len(done)} ratified, {len(ev)} dated event(s))')
    return 0


if __name__ == '__main__':
    sys.exit(main())
