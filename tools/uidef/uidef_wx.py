#!/usr/bin/env python3
"""A FOURTH backend: generate wx C++ from a UIDEF table. AIF-120, R40.

The three backends so far are Python and interpreted. `src/gui/wx/` in this tree is
C++, and the closeout has named wx as the top of the queue since R34 for a reason:
it is the only candidate that tests a **compiled** target and wx's **sizer** model,
which is a third geometry engine again -- box sizers and a grid-bag sizer, not
`place`/`pack` and not flowed boxes.

This emits C++, and the C++ is compiled and run. A generator whose output is never
built is a text formatter.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf

KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'panel', 'page', 'group', 'pageset',
))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui', 'worker', 'host'))
# wx gives a wxTextCtrl these natively, and has no Find.
CAPABILITIES = ('edit.cut', 'edit.copy', 'edit.paste', 'edit.undo', 'edit.redo',
                'edit.select_all')

CONTENT_SIZED = {'label', 'button', 'check', 'radio', 'group', 'page', 'form'}


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            out[k.strip().lower()] = v.strip().strip('"')
    return out


def cstr(s):
    return '"' + (s or '').replace('\\', '\\\\').replace('"', '\\"') + '"'


def generate(path, title=None):
    rows = list(Dbf(path).rows())
    objs = [r for r in rows if (r['RECKIND'] or '').strip() == 'OBJ']
    fonts = [r for r in rows if (r['RECKIND'] or '').strip() == 'FONT']
    rec = {(r['OBJID'] or '').strip(): r for r in objs}
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))

    body, notes = [], []
    made = [0]

    def var(oid):
        return 'w_' + oid.replace('.', '_')

    def fontexpr(r):
        fr = int(float((r['FONTREF'] or '0').strip() or 0))
        if not fr or fr > len(fonts):
            if fr:
                notes.append("FONTREF %d on %s names no usable FONT row"
                             % (fr, (r['OBJID'] or '').strip()))
            return None
        fp = parse_props(fonts[fr - 1]['PROPS'])
        if not (fp.get('name') and fp.get('size')):
            return None
        return ('wxFont(%s, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, '
                'wxFONTWEIGHT_NORMAL, false, %s)' % (fp['size'], cstr(fp['name'])))

    def emit(r, parent_var, parent_flow, sizer_var, depth):
        oid = (r['OBJID'] or '').strip()
        kind = (r['KIND'] or '').strip().lower()
        pr = parse_props(r['PROPS'])
        org = parse_props(r['ORIGIN'])
        flow = (r['FLOW'] or '').strip().lower()
        cap = pr.get('caption', '')
        v = var(oid)
        ind = '  ' * depth
        if kind not in KINDS_RENDERED:
            notes.append("REFUSED kind %r on %s -- contract s4" % (kind, oid))
            body.append('%s// REFUSED kind %s on %s' % (ind, kind, oid))
            return
        made[0] += 1

        # position and size, for `free` parents only (contract s8)
        pos, size = 'wxDefaultPosition', 'wxDefaultSize'
        if parent_flow == 'free' and 'origin_top' in org and 'origin_left' in org:
            pos = 'wxPoint(%d,%d)' % (int(float(org['origin_left'])),
                                      int(float(org['origin_top'])))
            if 'origin_width' in org and kind not in CONTENT_SIZED:
                size = 'wxSize(%d,-1)' % int(float(org['origin_width']))   # R16
        mask = pr.get('mask')
        if mask and kind not in CONTENT_SIZED and size == 'wxDefaultSize':
            size = 'wxSize(%d,-1)' % (7 * len(mask) + 10)                   # R25

        ctor = {
            'label':  'new wxStaticText(%s, wxID_ANY, %s, %s, %s)',
            'text':   'new wxTextCtrl(%s, wxID_ANY, wxEmptyString, %s, %s)',
            'button': 'new wxButton(%s, wxID_ANY, %s, %s, %s)',
            'check':  'new wxCheckBox(%s, wxID_ANY, %s, %s, %s)',
            'radio':  'new wxRadioButton(%s, wxID_ANY, %s, %s, %s)',
            'list':   'new wxListBox(%s, wxID_ANY, %s, %s)',
            'combo':  'new wxComboBox(%s, wxID_ANY, wxEmptyString, %s, %s)',
            'panel':  'new wxPanel(%s, wxID_ANY, %s, %s)',
            'page':   'new wxPanel(%s, wxID_ANY, %s, %s)',
            'pageset': 'new wxNotebook(%s, wxID_ANY, %s, %s)',
        }.get(kind)

        if kind == 'form':
            body.append('%sauto* %s = new wxFrame(nullptr, wxID_ANY, %s, '
                        'wxDefaultPosition, wxSize(%s,%s));'
                        % (ind, v, cstr(cap or title or 'UIDEF'),
                           org.get('origin_width', '620'),
                           str(int(float(org.get('origin_height', 420))) + 40)))
            sub = child_sizer(oid, flow, pr, v, ind)
            for c in kids.get(oid, []):
                emit(c, v, flow, sub, depth)
            close_sizer(oid, flow, v, sub, ind)
            if sub:
                body.append('%s%s->Layout();' % (ind, v))
            body.append('%s%s->Show();' % (ind, v))
            return

        if kind == 'group':
            # wx's idiom: a wxStaticBoxSizer OWNS the box, and the box is the
            # parent of the children. Creating a bare wxStaticBox and parenting to
            # it -- which the first version of this file did -- compiles, runs, and
            # renders an empty overlapping label. Compiling is not rendering.
            szname = '%s_sizer' % v
            orient = 'wxHORIZONTAL' if flow == 'row' else 'wxVERTICAL'
            if flow == 'grid' and 'columns' in pr:
                body.append('%sauto* %s_sb = new wxStaticBoxSizer(wxVERTICAL, %s, %s);'
                            % (ind, v, parent_var, cstr(cap)))
                body.append('%sauto* %s = %s_sb->GetStaticBox();' % (ind, v, v))
                body.append('%sauto* %s = new wxGridBagSizer(4, 8);' % (ind, szname))
                body.append('%sint %s_i = 0; const int %s_n = %s;'
                            % (ind, szname, szname, pr['columns']))
                gridsizers.add(szname)
                for c in kids.get(oid, []):
                    emit(c, v, flow, szname, depth + 1)
                body.append('%s%s_sb->Add(%s, 0, wxALL, 3);' % (ind, v, szname))
                outer = '%s_sb' % v
            else:
                if flow == 'grid':
                    notes.append("REFUSED grid on %s -- FLOW=grid with no Columns "
                                 "property (R23.2); fell back to column" % oid)
                    orient = 'wxVERTICAL'
                body.append('%sauto* %s = new wxStaticBoxSizer(%s, %s, %s);'
                            % (ind, szname, orient, parent_var, cstr(cap)))
                body.append('%sauto* %s = %s->GetStaticBox();' % (ind, v, szname))
                for c in kids.get(oid, []):
                    emit(c, v, flow, szname, depth + 1)
                outer = szname
            if sizer_var:
                add_to(sizer_var, outer, ind, is_sizer=True)
            return

        if ctor is None:
            return
        if kind in ('label', 'button', 'check', 'radio'):
            body.append('%sauto* %s = %s;' % (ind, v, ctor % (parent_var, cstr(cap), pos, size)))
        else:
            body.append('%sauto* %s = %s;' % (ind, v, ctor % (parent_var, pos, size)))

        f = fontexpr(r)
        if f:
            body.append('%s%s->SetFont(%s);' % (ind, v, f))

        if kind in ('panel', 'page', 'pageset'):
            sub = child_sizer(oid, flow, pr, v, ind)
            for c in kids.get(oid, []):
                if kind == 'pageset':
                    emit(c, v, flow, None, depth + 1)
                    body.append('%s%s->AddPage(%s, %s);'
                                % (ind, v, var((c['OBJID'] or '').strip()),
                                   cstr(parse_props(c['PROPS']).get('caption', ''))))
                else:
                    emit(c, v, flow, sub, depth + 1)
            if kind != 'pageset':
                close_sizer(oid, flow, v, sub, ind)
        if sizer_var:
            add_to(sizer_var, v, ind,
                   span=int(float((r['SPAN'] or '0').strip() or 0)) or 1)

    def child_sizer(oid, flow, pr, owner, ind, staticbox=None):
        name = '%s_sizer' % var(oid)
        if flow == 'row':
            body.append('%sauto* %s = new wxBoxSizer(wxHORIZONTAL);' % (ind, name))
        elif flow == 'column':
            body.append('%sauto* %s = new wxBoxSizer(wxVERTICAL);' % (ind, name))
        elif flow == 'grid':
            if 'columns' not in pr:
                notes.append("REFUSED grid on %s -- FLOW=grid with no Columns "
                             "property (R23.2); fell back to column" % oid)
                body.append('%sauto* %s = new wxBoxSizer(wxVERTICAL);' % (ind, name))
                return name
            # wxGridBagSizer is the only wx sizer with SPAN, which is why it is here
            body.append('%sauto* %s = new wxGridBagSizer(4, 8);' % (ind, name))
            body.append('%sint %s_i = 0; const int %s_n = %s;'
                        % (ind, name, name, pr['columns']))
            gridsizers.add(name)
        else:
            kidsl = kids.get(oid, [])
            if kidsl and not any((c['ORIGIN'] or '').strip() for c in kidsl):
                notes.append("DERIVED layout for %s -- FLOW=free with no ORIGIN on "
                             "any child; fell back to ORDINAL order (R23.3)" % oid)
                body.append('%sauto* %s = new wxBoxSizer(wxVERTICAL);' % (ind, name))
                return name
            return None                          # absolute positioning, no sizer
        return name

    gridsizers = set()


    def add_to(sizer_var, thing, ind, is_sizer=False, span=1):
        if not sizer_var:
            return
        if sizer_var in gridsizers and not is_sizer:
            body.append('%s%s->Add(%s, wxGBPosition(%s_i / %s_n, %s_i %% %s_n), '
                        'wxGBSpan(1,%d)); %s_i += %d;'
                        % (ind, sizer_var, thing, sizer_var, sizer_var,
                           sizer_var, sizer_var, span, sizer_var, span))
        else:
            body.append('%s%s->Add(%s, 0, wxALL, 6);' % (ind, sizer_var, thing))

    def close_sizer(oid, flow, owner, sizer_var, ind, staticbox=False):
        if not sizer_var:
            return
        if staticbox:
            return
        body.append('%s%s->SetSizer(%s);' % (ind, owner, sizer_var))

    roots = kids.get('', [])
    for r in roots:
        emit(r, 'nullptr', '', None, 1)

    src = ['#include <wx/wx.h>', '#include <wx/notebook.h>', '#include <wx/gbsizer.h>',
           '#include <wx/statbox.h>', '',
           'class App : public wxApp { public: bool OnInit() override {'] + body + [
           '  if (wxTheApp->argc > 1) CallAfter([]{ wxTheApp->ExitMainLoop(); });',
           '  return true; } };', 'wxIMPLEMENT_APP(App);']
    return "\n".join(src), notes, made[0]


if __name__ == '__main__':
    src, notes, n = generate(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if out:
        open(out, 'w').write(src)
    print("%s -> %s   %d widget(s)" % (os.path.basename(sys.argv[1]), out or '(stdout)', n))
    for x in dict.fromkeys(notes):
        print("  " + x)
    if not out:
        print(src)
