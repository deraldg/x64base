#!/usr/bin/env python3
"""A THIRD backend: a character-cell target. AIF-120, R35.

R34 showed the format crossing from Tk's pixels to a browser's flowed boxes. Both
are retained-mode widget toolkits with fonts and pixels. This one has neither.

A character grid is the harshest available test of the contract's geometry claims,
because everything measured in pixels has to DEGRADE rather than translate:

  * `ORIGIN` is in px and this target's unit is a cell. Section 8 enumerates units
    and gives conversions for none -- gate 11 logged that as G-6. So the conversion
    is a guess, and R12.3 says a guess must be declared.
  * `ORIGIN_SCALE = cell` exists in the vocabulary and **no document has ever
    produced it**: measured, 20 objects in the corpus declare a ScaleMode and all
    20 say pixels.
  * R16's content-sizing is exact here -- a label is as wide as its characters.
  * R17 and R25 size a bound control from its mask. On a character grid that stops
    being a regression and becomes an identity: the width IS the mask length.
  * Fonts do not exist. `FONTREF` must be ignored, and ignoring is a conformance
    outcome the contract has no word for.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# `read_vfp_binary` is the VFP binary reader and it lives in tools/vfp.
# gui/uidef/read_vfp_binary.py is a GITIGNORED working copy, so importing it
# from this directory made nine committed tools unimportable on a fresh clone --
# found by the house 'sweep for your own leftovers' rule, not by anything failing.
# tools/vfp goes on the path FIRST so the ignored copy can never shadow it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vfp'))
from read_vfp_binary import Dbf
from uidef import doc_source

KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'panel', 'page', 'group', 'pageset',
    # R66. The character grid is the target these five were MEASURED on -- dottalk++
    # renders exactly this shape in a terminal -- so this backend must not paraphrase
    # them the way a toolkit backend has to.
    'grid', 'tree', 'detail', 'summary', 'statusbar',
))
FRAME_KINDS = frozenset(('grid', 'tree', 'detail', 'summary', 'statusbar'))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui',))          # no threads, no host clipboard
CAPABILITIES = ()

# The conversion the contract does not give. Chosen from the fonts these documents
# were designed against -- R25 measured 7.00 px per character at Arial 9 and dates
# at 62 px -- so a cell is 7 px wide and 20 px tall. It is a DERIVED number and is
# reported as one on every render, never written back into ORIGIN (R12.3).
PX_PER_CELL_X = 7
PX_PER_CELL_Y = 20
BAND_TOL_PX = 8          # two controls within this are on the same visual row


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            out[k.strip().lower()] = v.strip().strip('"')
    return out


class Canvas:
    def __init__(self, w=100, h=40):
        self.g = [[' '] * w for _ in range(h)]
        self.w, self.h = w, h

    def put(self, row, col, text):
        if row < 0 or row >= self.h:
            return
        for i, ch in enumerate(text):
            c = col + i
            if 0 <= c < self.w:
                self.g[row][c] = ch

    def box(self, row, col, w, h, title=''):
        w = max(w, 2); h = max(h, 2)
        self.put(row, col, '+' + '-' * (w - 2) + '+')
        self.put(row + h - 1, col, '+' + '-' * (w - 2) + '+')
        for r in range(row + 1, row + h - 1):
            self.put(r, col, '|'); self.put(r, col + w - 1, '|')
        if title:
            self.put(row, col + 2, ' ' + title[:max(w - 6, 0)] + ' ')

    def text(self):
        return "\n".join("".join(r).rstrip() for r in self.g).rstrip("\n")


def render(path, width=100, height=40):
    rows = list(Dbf(path).rows())
    objs = [r for r in rows if (r['RECKIND'] or '').strip() == 'OBJ']
    fonts = [r for r in rows if (r['RECKIND'] or '').strip() == 'FONT']
    rec = {(r['OBJID'] or '').strip(): r for r in objs}
    src_aliases, src_rels = doc_source(rows)
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))

    cv = Canvas(width, height)
    notes = []
    if fonts:
        notes.append("IGNORED %d FONT row(s) and every FONTREF -- this target has "
                     "no fonts. The contract has no conformance word for `ignored`; "
                     "it is not refusal and it is not honouring." % len(fonts))

    def glyph(kind, pr, r):
        cap = pr.get('caption', '')
        mask = pr.get('mask', '')
        if kind == 'label':
            return cap
        if kind == 'text':
            # R17/R25 exactly: on a character grid the width IS the mask length.
            n = len(mask) if mask else 10
            return '[' + '_' * n + ']'
        if kind == 'button':
            return '< ' + (cap or '?') + ' >'
        if kind == 'check':
            return '[ ] ' + cap
        if kind == 'radio':
            return '( ) ' + cap
        if kind == 'combo':
            return '[' + '_' * 8 + ' v]'
        if kind == 'list':
            return '[' + '_' * 10 + ']'
        return cap

    def frame_block(kind, pr, ch):
        """R66/contract 4b -- the five regions of the ERSATZ frame, as characters.

        Every one of these is STRUCTURE, not data: a design-time preview has no
        records, exactly as `text` renders `[______]` rather than a value. What the
        frame kinds add is that their structure is DECLARED -- a grid's columns come
        from its BINDING (contract 10c, which is what answers R6) and a tree's edges
        come from SOURCE (4b(a)), so there is nothing here to invent.
        """
        b = (ch['BINDING'] or '').strip()
        specs = [x.strip() for x in b.split(',') if x.strip()]

        def spec_cols(default_alias):
            cols = []
            for sp in specs:
                if sp == '*':
                    cols.append((default_alias or '?').upper() + '.*')
                elif sp.endswith('.*'):
                    cols.append(sp.upper())
                else:
                    cols.append(sp.split('.')[-1].upper())
            return cols or ['*']

        if kind == 'grid':
            heads = spec_cols(src_aliases[0] if src_aliases else None)
            w = max([10] + [len(h) for h in heads])
            hdr = '  '.join(h.ljust(w) for h in heads)
            try:
                n = int(float(pr.get('rowlimit', 3) or 3))
            except ValueError:
                n = 3
            n = max(1, min(n, 5))
            body = ['  '.join('.' * w for _ in heads) for _ in range(n)]
            return [hdr, '-' * len(hdr)] + body
        if kind == 'tree':
            root = b.lower() or (src_aliases[0] if src_aliases else '?')
            out = [root.upper()]
            for a_, b_, expr in src_rels:
                if a_ == root:
                    out.append('  -> %s   ON %s' % (b_.upper(), expr or '?'))
            if len(out) == 1:
                out.append('  (no Relation edge from %s in SOURCE)' % root.upper())
            return out
        if kind == 'detail':
            names = spec_cols(src_aliases[0] if src_aliases else None)
            # An `alias.*` expands from the SCHEMA, which a design-time preview does
            # not have. Say that, rather than drawing a row called "STUDENTS.*".
            if any(n.endswith('.*') for n in names):
                return ['(every field of %s, from the schema at render time)'
                        % ', '.join(n[:-2] for n in names if n.endswith('.*'))]
            w = max([8] + [len(n) for n in names])
            return ['%s : %s' % (n.ljust(w), '.' * 8) for n in names]
        if kind == 'summary':
            root = b.lower() or (src_aliases[0] if src_aliases else '?')
            out = ['%s : %s' % (b_.upper().ljust(10), 'n')
                   for a_, b_, _e in src_rels if a_ == root]
            return out or ['(no child of %s in SOURCE)' % root.upper()]
        # statusbar -- 4b(c): it reports, it does not compute, and a value the
        # reader cannot supply is omitted rather than guessed.
        shows = [x.strip().lower()
                 for x in str(pr.get('shows', '')).replace(',', ' ').split()]
        seen = {'rows': 'ROWS SHOWN: n', 'limit': 'LIMIT m', 'order': 'ORDER: physical',
                'root': 'ROOT: %s' % ((src_aliases[0] if src_aliases else '?').upper()),
                'recno': 'RECNO: n', 'status': 'STATUS: OK'}
        parts = [seen[x] for x in shows if x in seen]
        return [' | '.join(parts) if parts else '(statusbar declares no Shows)']

    used = {'made': 0, 'refused': 0, 'derived': 0}

    def draw(oid, top, left, avail_w):
        """Draw the children of `oid`. Returns (rows, cols) consumed.

        A container cannot be sized before its content is measured -- the first
        version of this file sized every box by its TITLE and clipped everything
        wider, which is R30.3's lesson arriving on a third target: a container's
        size comes from its children unless something else supplies it.
        """
        pr = parse_props(rec[oid]['PROPS']) if oid in rec else {}
        flow = ((rec[oid]['FLOW'] or '').strip().lower()) if oid in rec else 'column'
        children = kids.get(oid, [])
        if not children:
            return 0, 0
        if flow == 'grid' and 'columns' not in pr:
            notes.append("REFUSED grid on %s -- FLOW=grid with no Columns (R23.2); "
                         "fell back to column" % oid)
            flow = 'column'
        r, c, maxr, maxc = top, left, top, left
        col_w = []
        if flow == 'grid':
            ncols = int(float(pr['columns']))
            cells = []
            for ch in children:
                cp = parse_props(ch['PROPS'])
                cells.append(glyph((ch['KIND'] or '').strip().lower(), cp, ch))
            col_w = [0] * ncols
            for i, g in enumerate(cells):
                col_w[i % ncols] = max(col_w[i % ncols], len(g))

        has_org = any((ch['ORIGIN'] or '').strip() for ch in children)
        used_free = flow == 'free' and has_org
        if flow == 'free' and not has_org:
            notes.append("DERIVED layout for %s -- FLOW=free with no ORIGIN on any "
                         "child; fell back to ORDINAL order (R23.3)" % oid)
            used['derived'] += 1
        if used_free:
            notes.append("DERIVED cell geometry for %s -- ORIGIN is px and this "
                         "target's unit is a cell; divided by %d x %d, which the "
                         "contract does not specify (R12.3, gate 11 G-6)"
                         % (oid, PX_PER_CELL_X, PX_PER_CELL_Y))
            used['derived'] += 1

        # R35.1: quantising each TOP independently splits a visual row in two,
        # because a label sits a few px off its own field's baseline. That is R19's
        # finding, and it turns out to govern RENDERING on a coarse grid and not
        # only INFERENCE. Band the TOPs first, then convert the band.
        band = {}
        if used_free:
            tops = sorted({float(parse_props(ch['ORIGIN'])['origin_top'])
                           for ch in children
                           if 'origin_top' in parse_props(ch['ORIGIN'])})
            idx, prev = -1, None
            for t in tops:
                if prev is None or t - prev > BAND_TOL_PX:
                    idx += 1
                band[t] = idx
                prev = t
            if len(tops) > len(set(band.values())):
                notes.append("BANDED %d ORIGIN_TOP values into %d visual rows on %s "
                             "within %d px -- quantising each one alone splits a row "
                             "in two (R19, R35.1)"
                             % (len(tops), len(set(band.values())), oid, BAND_TOL_PX))

        gi = 0
        for ch in children:
            kind = (ch['KIND'] or '').strip().lower()
            cp = parse_props(ch['PROPS'])
            org = parse_props(ch['ORIGIN'])
            cid = (ch['OBJID'] or '').strip()
            if kind not in KINDS_RENDERED:
                notes.append("REFUSED kind %r on %s -- contract s4" % (kind, cid))
                used['refused'] += 1
                continue
            if kind in ('group', 'panel', 'pageset', 'page'):
                title = cp.get('caption', '')
                # A container in a `free` parent is positioned like anything else
                # in it. Drawing containers sequentially while positioning controls
                # absolutely mixes two strategies inside one parent, and the first
                # version of this file did exactly that -- the empty button panel
                # landed on top of the first two rows of the form.
                if used_free and 'origin_top' in org and 'origin_left' in org:
                    br = top + band.get(float(org['origin_top']),
                                        int(float(org['origin_top'])) // PX_PER_CELL_Y)
                    bc = left + int(float(org['origin_left'])) // PX_PER_CELL_X
                else:
                    br, bc = r, c
                inner, innerw = draw(cid, br + 1, bc + 1, avail_w - 2)
                w = max(len(title) + 6, innerw + 3, 12)
                cv.box(br, bc, w, inner + 2, title)
                if not (used_free and 'origin_top' in org):
                    r = br + inner + 2
                maxr = max(maxr, br + inner + 2); maxc = max(maxc, bc + w)
                used['made'] += 1
                continue
            if kind in FRAME_KINDS:
                lines = frame_block(kind, cp, ch)
                # The engine titles each region of its frame; so does this.
                if cp.get('caption'):
                    lines = [cp['caption']] + lines
                if used_free and 'origin_top' in org and 'origin_left' in org:
                    fr = top + band.get(float(org['origin_top']),
                                        int(float(org['origin_top'])) // PX_PER_CELL_Y)
                    fc = left + int(float(org['origin_left'])) // PX_PER_CELL_X
                else:
                    fr, fc = r, c
                for i, ln in enumerate(lines):
                    cv.put(fr + i, fc, ln)
                    maxc = max(maxc, fc + len(ln))
                maxr = max(maxr, fr + len(lines))
                if not (used_free and 'origin_top' in org):
                    r = fr + len(lines)
                used['made'] += 1
                continue
            g = glyph(kind, cp, ch)
            used['made'] += 1
            if used_free and 'origin_top' in org and 'origin_left' in org:
                gr = top + band.get(float(org['origin_top']),
                                    int(float(org['origin_top'])) // PX_PER_CELL_Y)
                gc = left + int(float(org['origin_left'])) // PX_PER_CELL_X
                cv.put(gr, gc, g)
                maxr = max(maxr, gr + 1); maxc = max(maxc, gc + len(g))
            elif flow == 'row':
                cv.put(r, c, g); c += len(g) + 2
                maxr = max(maxr, r + 1); maxc = max(maxc, c)
            elif flow == 'grid':
                ncols = int(float(pr['columns']))
                span = int(float((ch['SPAN'] or '0').strip() or 0)) or 1
                ci = gi % ncols
                gc = c + sum(col_w[:ci]) + 2 * ci
                cv.put(r, gc, g)
                maxc = max(maxc, gc + len(g))
                gi += span
                if gi % ncols == 0:
                    r += 1
                maxr = max(maxr, r + 1)
            else:
                cv.put(r, c, g); r += 1
                maxr = max(maxr, r); maxc = max(maxc, c + len(g))
        return max(maxr - top, 1), max(maxc - left, 1)

    roots = kids.get('', [])
    r = 0
    for root in roots:
        oid = (root['OBJID'] or '').strip()
        cp = parse_props(root['PROPS'])
        if (root['KIND'] or '').strip().lower() == 'form':
            title = cp.get('caption', '')
            inner, innerw = draw(oid, r + 1, 1, width - 2)
            cv.box(r, 0, max(innerw + 3, len(title) + 6), inner + 2, title)
            r += inner + 2
    return cv.text(), notes, used


if __name__ == '__main__':
    txt, notes, used = render(sys.argv[1])
    print("%s -- %d cells wide, character grid" % (os.path.basename(sys.argv[1]), 100))
    print("  elements %d   refused %d   derived-geometry containers %d"
          % (used['made'], used['refused'], used['derived']))
    for n in dict.fromkeys(notes):
        print("  " + n)
    print()
    print(txt)
