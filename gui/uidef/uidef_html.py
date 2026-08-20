#!/usr/bin/env python3
"""A SECOND BACKEND: generate HTML from a UIDEF table. AIF-120.

Gate 11 (R28) tested whether a second AUTHOR could build a consumer from the
contract. This tests something else: whether the format survives a different
GEOMETRY MODEL. Tk gave place, pack and grid -- all pixels. A browser flows boxes,
and the contract's own section 5 names it as a candidate target for exactly that
reason. If `FLOW` is really the portable geometry, it has to land here without the
table changing.

Same author as `uidef_tk.py`, and that is stated rather than glossed: this is a
portability test, not an independence test. R28 was the independence test.
"""
import os, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf
from uidef import doc_source

# The profile this target declares, for manifest.py to import (R24.1).
KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'image', 'panel', 'page', 'group', 'pageset',
    # R66. A browser has a native element for four of the five -- table, ul, dl and
    # a footer div -- so this target renders their STRUCTURE rather than a box.
    'grid', 'tree', 'detail', 'summary', 'statusbar',
))
FRAME_KINDS = frozenset(('grid', 'tree', 'detail', 'summary', 'statusbar'))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui', 'worker', 'host'))
# A browser provides MORE host capabilities than Tk: find and replace are native.
CAPABILITIES = (
    'edit.cut', 'edit.copy', 'edit.paste', 'edit.clear', 'edit.select_all',
    'edit.undo', 'edit.redo', 'edit.find',
)

# R25: a bound control's width follows its mask. In a browser the honest unit is
# characters, not pixels -- `ch` is exactly "one zero-width", which is what a mask
# position is. So R25's SLOPE does not travel and its MECHANISM does.
CONTENT_SIZED = {'label', 'button', 'check', 'radio', 'group', 'page', 'form'}


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            out[k.strip().lower()] = v.strip().strip('"')
    return out


def parse_handlers(txt):
    out = []
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        comp = None
        if '->' in rest:
            rest, comp = rest.split('->', 1)
        parts = [p.strip() for p in rest.split('/')]
        out.append((ev.strip(), parts[0], (parts[1] if len(parts) > 1 else 'ui').lower()))
    return out


def load(path):
    rows = list(Dbf(path).rows())
    kind = lambda k: [r for r in rows if (r['RECKIND'] or '').strip() == k]
    return kind('DOC')[0], kind('FONT'), kind('OBJ')


def source_of(path):
    """The DOC's work areas and relation edges -- contract 4b(a). R66.

    Separate from `load` for the reason spelled out in uidef_tk.source_of: widening
    a shared three-value helper is a change to every caller, and the tk version of
    this broke two tools before it was reverted.
    """
    return doc_source(list(Dbf(path).rows()))


def generate(path):
    doc, fonts, objs = load(path)
    src_aliases, src_rels = source_of(path)
    rec = {(r['OBJID'] or '').strip(): r for r in objs}
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))

    notes = []
    fontcss = {}
    for i, f in enumerate(fonts, 1):
        fp = parse_props(f['PROPS'])
        if fp.get('name') and fp.get('size'):
            css = "font-family:%s;font-size:%spt" % (fp['name'], fp['size'])
            if (fp.get('bold') or '').upper().startswith('.T'):
                css += ";font-weight:bold"          # R56
            if (fp.get('italic') or '').upper().startswith('.T'):
                css += ";font-style:italic"
            fontcss[i] = css

    def esc(t):
        return html.escape(t or '')

    FALSEY = ('false', '.f.', 'f', '0', 'no', 'off')

    def weight_of(pr):
        v = str(pr.get('weight', '')).strip()
        if not v:
            return 0
        try:
            n = int(float(v))
        except ValueError:
            return 0
        return n if n > 0 else 0

    def fill_of(pr):
        v = str(pr.get('fill', '')).strip().lower()
        return bool(v) and v not in FALSEY

    def style_for(r, kind, org, parent_flow, parent_kind):
        st = []
        fr = int(float((r['FONTREF'] or '0').strip() or 0))
        if fr:
            if fr in fontcss:
                st.append(fontcss[fr])
            else:
                notes.append("FONTREF %d on %s names no usable FONT row"
                             % (fr, (r['OBJID'] or '').strip()))
        if parent_flow == 'free' and 'origin_top' in org and 'origin_left' in org:
            st.append("position:absolute;top:%spx;left:%spx"
                      % (org['origin_top'], org['origin_left']))
            if 'origin_width' in org and kind not in CONTENT_SIZED:
                st.append("width:%spx" % org['origin_width'])   # R16
        # R80, contract 5c. flex-grow IS this target's Weight and align-self IS
        # its Fill -- but both only mean something inside a container that HAS
        # free space, which is why section 3 of R80 had to give `.form` a size
        # before either did anything. CSS having the property is not the same as
        # the layout having room.
        _pr = parse_props(r['PROPS'])
        _w = weight_of(_pr)
        if _w and parent_flow in ('row', 'column'):
            st.append("flex-grow:%d" % _w)
            st.append("flex-basis:0")
        if fill_of(_pr) and parent_flow in ('row', 'column'):
            st.append("align-self:stretch")

        # Contract s5: SPAN gives the cells a member consumes in a `grid` flow.
        # CSS grid has the concept natively, which is a point for FLOW being the
        # portable geometry rather than a Tk convenience.
        if parent_flow == 'grid':
            span = int(float((r['SPAN'] or '0').strip() or 0)) or 1
            if span > 1:
                st.append("grid-column:span %d" % span)
        mask = parse_props(r['PROPS']).get('mask')
        if mask and kind not in CONTENT_SIZED:
            # R25's mechanism, in the unit this target actually has.
            st.append("width:%dch" % (len(mask) + 1))
        return ";".join(st)

    def container_style(oid, flow, pr):
        if flow == 'row':
            return "display:flex;flex-direction:row;gap:6px;align-items:center"
        if flow == 'column':
            return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
        if flow == 'grid':
            if 'columns' not in pr:
                notes.append("REFUSED grid on %s -- FLOW=grid with no Columns "
                             "property (R23.2)" % oid)
                return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
            return ("display:grid;grid-template-columns:repeat(%s,max-content);"
                    "gap:4px 8px;align-items:center" % pr['columns'])
        if flow == 'free':
            kidsl = kids.get(oid, [])
            if kidsl and not any((c['ORIGIN'] or '').strip() for c in kidsl):
                notes.append("DERIVED layout for %s -- FLOW=free with no ORIGIN on "
                             "any child; fell back to ORDINAL order (R23.3)" % oid)
                return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
            return "position:relative;min-height:%spx" % (
                parse_props(rec[oid]['ORIGIN']).get('origin_height', '0')
                if oid in rec else '0')
        return ""

    out = []
    counts = {'made': 0, 'refused': 0, 'host_ok': 0, 'host_no': 0}

    def emit(r, parent_flow, parent_kind, depth):
        oid = (r['OBJID'] or '').strip()
        kind = (r['KIND'] or '').strip().lower()
        pr = parse_props(r['PROPS'])
        org = parse_props(r['ORIGIN'])
        flow = (r['FLOW'] or '').strip().lower()
        cap = pr.get('caption', '')
        pad = '  ' * depth
        if kind not in KINDS_RENDERED:
            out.append('%s<!-- REFUSED kind %s on %s (contract s4) -->' % (pad, kind, oid))
            counts['refused'] += 1
            notes.append("REFUSED kind %r on %s -- contract s4" % (kind, oid))
            return
        counts['made'] += 1
        st = style_for(r, kind, org, parent_flow, parent_kind)
        # R27: TABORDINAL is a second ordinal over the same children. A browser has
        # exactly that concept and spells it `tabindex`.
        tab = ''
        t = str(r['TABORDINAL'] or '').strip()
        if t and t != '0':
            tab = ' tabindex="%s"' % int(float(t))
        # R20/R22.4: a `host` item is wired if this target provides the capability,
        # and refused BY NAME if it does not.
        onclick = ''
        for ev, name, disp in parse_handlers(r['HANDLERS']):
            if ev != 'Click':
                continue
            if disp == 'host':
                if name in CAPABILITIES:
                    counts['host_ok'] += 1
                    onclick = ' onclick="hostcap(\'%s\')"' % name
                else:
                    counts['host_no'] += 1
                    notes.append("REFUSED capability %s on %s -- this target does "
                                 "not provide it (R20, R22.4)" % (name, oid))
                    cap = cap + "  [no host capability: %s]" % name
                    onclick = ' disabled'
        cs = container_style(oid, flow, pr) if flow else ''
        full = ";".join(x for x in (st, cs) if x)
        sattr = ' style="%s"' % full if full else ''
        child = kids.get(oid, [])

        if kind in FRAME_KINDS:
            # R66/contract 4b. Structure, not data -- the same choice `text` makes
            # when it emits an empty <input>. A grid's columns are DECLARED by its
            # BINDING (10c) and a tree's edges by SOURCE (4b(a)), so nothing here is
            # generated from a count property, which is what R6 refused.
            b = (r['BINDING'] or '').strip()
            specs = [x.strip() for x in b.split(',') if x.strip()]
            if cap:
                out.append('%s<h2>%s</h2>' % (pad, esc(cap)))
            if kind == 'grid':
                heads = [(sp.upper() if sp.endswith('.*') or sp == '*'
                          else sp.split('.')[-1].upper()) for sp in specs] or ['*']
                try:
                    n = max(1, min(int(float(pr.get('rowlimit', 3) or 3)), 5))
                except ValueError:
                    n = 3
                out.append('%s<table class="grid"%s><thead><tr>%s</tr></thead><tbody>'
                           % (pad, sattr,
                              ''.join('<th>%s</th>' % esc(h) for h in heads)))
                for _ in range(n):
                    out.append('%s  <tr>%s</tr>'
                               % (pad, ''.join('<td></td>' for _ in heads)))
                out.append('%s</tbody></table>' % pad)
            elif kind == 'tree':
                root = b.lower() or (src_aliases[0] if src_aliases else '?')
                edges = [(c, e) for a_, c, e in src_rels if a_ == root]
                out.append('%s<ul class="tree"%s><li>%s<ul>'
                           % (pad, sattr, esc(root.upper())))
                for c, e in edges:
                    out.append('%s  <li>%s <em>ON %s</em></li>'
                               % (pad, esc(c.upper()), esc(e or '?')))
                if not edges:
                    out.append('%s  <li><em>no Relation edge in SOURCE</em></li>' % pad)
                out.append('%s</ul></li></ul>' % pad)
            elif kind == 'detail':
                out.append('%s<dl class="detail"%s>' % (pad, sattr))
                if any(sp.endswith('.*') or sp == '*' for sp in specs):
                    out.append('%s  <dt><em>every field of %s</em></dt><dd></dd>'
                               % (pad, esc(', '.join(
                                   (sp[:-2] or '?').upper() if sp.endswith('.*')
                                   else (src_aliases[0] if src_aliases else '?').upper()
                                   for sp in specs))))
                else:
                    for sp in specs:
                        out.append('%s  <dt>%s</dt><dd></dd>'
                                   % (pad, esc(sp.split('.')[-1].upper())))
                out.append('%s</dl>' % pad)
            elif kind == 'summary':
                root = b.lower() or (src_aliases[0] if src_aliases else '?')
                out.append('%s<ul class="summary"%s>' % (pad, sattr))
                kidsx = [c for a_, c, _e in src_rels if a_ == root]
                for c in kidsx or []:
                    out.append('%s  <li>%s : <span class="n"></span></li>'
                               % (pad, esc(c.upper())))
                if not kidsx:
                    out.append('%s  <li><em>no child of %s in SOURCE</em></li>'
                               % (pad, esc(root.upper())))
                out.append('%s</ul>' % pad)
            else:
                labels = {'rows': 'ROWS SHOWN', 'limit': 'LIMIT', 'order': 'ORDER',
                          'root': 'ROOT', 'recno': 'RECNO', 'status': 'STATUS'}
                shows = [x.strip().lower() for x in
                         str(pr.get('shows', '')).replace(',', ' ').split()]
                cells = ''.join('<span class="cell">%s: <b></b></span>'
                                % esc(labels[x]) for x in shows if x in labels)
                out.append('%s<div class="statusbar"%s>%s</div>'
                           % (pad, sattr, cells or '<em>no Shows declared</em>'))
            return
        if kind == 'form':
            # R80. A form that declares ORIGIN dimensions becomes a SIZED flex
            # column, because that is the only way its children's flex-grow means
            # anything. Emitting flex-grow into an inline-block container is the
            # exact failure this ruling was written about: the property is
            # present, correct, and inert.
            _fw = org.get('origin_width')
            _fh = org.get('origin_height')
            if _fw and _fh:
                _fs = 'width:%spx;height:%spx' % (_fw, _fh)
                _fs = (full + ';' + _fs) if full else _fs
                out.append('%s<div class="form sized" style="%s">' % (pad, _fs))
            else:
                notes.append('DROPPED Weight/Fill inside form %s -- no ORIGIN '
                             'dimensions, so the container is content-sized and '
                             'there is no free space to divide (R80)'
                             % (r['OBJID'] or '').strip())
                out.append('%s<div class="form"%s>' % (pad, sattr))
            if cap:
                out.append('%s  <h1>%s</h1>' % (pad, esc(cap)))
        elif kind == 'label':
            out.append('%s<label%s%s>%s</label>' % (pad, sattr, tab, esc(cap)))
        elif kind == 'text':
            out.append('%s<input type="text"%s%s>' % (pad, sattr, tab))
        elif kind == 'button':
            out.append('%s<button%s%s%s>%s</button>' % (pad, sattr, tab, onclick, esc(cap)))
        elif kind in ('check', 'radio'):
            ty = 'checkbox' if kind == 'check' else 'radio'
            out.append('%s<label%s><input type="%s"%s> %s</label>'
                       % (pad, sattr, ty, tab, esc(cap)))
        elif kind == 'combo':
            out.append('%s<select%s%s></select>' % (pad, sattr, tab))
        elif kind == 'list':
            out.append('%s<select multiple size="4"%s%s></select>' % (pad, sattr, tab))
        elif kind == 'image':
            out.append('%s<div class="img"%s>[image]</div>' % (pad, sattr))
        elif kind == 'group':
            out.append('%s<fieldset%s><legend>%s</legend>' % (pad, sattr, esc(cap)))
        elif kind == 'pageset':
            out.append('%s<div class="tabs"%s>' % (pad, sattr))
        elif kind == 'page':
            out.append('%s<details open><summary>%s</summary><div%s>'
                       % (pad, esc(cap) or oid, sattr))
        else:
            out.append('%s<div%s>' % (pad, sattr))

        for c in child:
            emit(c, flow, kind, depth + 1)

        if kind == 'group':
            out.append('%s</fieldset>' % pad)
        elif kind == 'page':
            out.append('%s</div></details>' % pad)
        elif kind in ('form', 'pageset', 'panel'):
            out.append('%s</div>' % pad)

    for r in kids.get('', []):
        emit(r, '', '', 1)

    dp = parse_props(doc['PROPS'])
    page = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
            "<title>%s</title>" % esc(dp.get('sourcefile', 'UIDEF')),
            "<style>body{font-family:sans-serif;font-size:9pt;margin:12px}",
            ".form{border:1px solid #999;padding:10px;display:inline-block}",
            # R80: a form carrying ORIGIN dimensions is sized from them, so a
            # flex child has something to grow INTO. Without this the CSS was
            # emitted and inert -- inline-block is content-sized and flex-grow
            # distributes free space that does not exist.
            ".form.sized{display:flex;flex-direction:column}",
            "fieldset{border:1px solid #aaa;margin:2px 0}",
            "details{border:1px solid #ccc;padding:2px 6px;margin:2px 0}",
            "button[disabled]{color:#999}",
            ".img{border:1px dashed #999;padding:6px;color:#666}</style>",
            "<script>function hostcap(c){document.execCommand("
            "{'edit.cut':'cut','edit.copy':'copy','edit.paste':'paste',"
            "'edit.undo':'undo','edit.redo':'redo','edit.clear':'delete',"
            "'edit.select_all':'selectAll'}[c]||c)}</script>",
            "</head><body>"] + out + ["</body></html>"]
    return "\n".join(page), notes, counts


if __name__ == '__main__':
    doc, notes, counts = generate(sys.argv[1])
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    if outp:
        open(outp, 'w', encoding='utf-8').write(doc)
    print("%s -> %s" % (os.path.basename(sys.argv[1]), outp or '(stdout)'))
    print("  elements %d   refused kinds %d   host capabilities wired %d, refused %d"
          % (counts['made'], counts['refused'], counts['host_ok'], counts['host_no']))
    for n in notes:
        print("  " + n)
    if not outp:
        print(doc)
