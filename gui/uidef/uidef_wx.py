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
from uidef import doc_source

KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'panel', 'page', 'group', 'pageset',
    # R66. wx has a native control for each: wxListCtrl in report mode is the grid,
    # wxTreeCtrl the tree, and a frame owns its own status bar.
    'grid', 'tree', 'detail', 'summary', 'statusbar',
))
FRAME_KINDS = frozenset(('grid', 'tree', 'detail', 'summary', 'statusbar'))
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


def domains_from_source(src):
    """R36: the lock domains, straight out of the DOC record's SOURCE."""
    aliases, edges = [], []
    for line in (src or '').replace('\r\n', '\n').split('\n'):
        if ' = ' not in line:
            continue
        k, v = line.split(' = ', 1)
        k = k.strip().lower()
        if k == 'alias':
            aliases.append(v.strip().lower())
        elif k == 'relation':
            body = v.split(' ON ', 1)[0]
            if ' -> ' in body:
                a, b = body.split(' -> ', 1)
                edges.append((a.strip().lower(), b.strip().lower()))
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    for a in aliases:
        find(a)
    g = {}
    for x in par:
        g.setdefault(find(x), []).append(x)
    return sorted((sorted(v) for v in g.values()), key=lambda d: (-len(d), d))


def parse_handlers(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        comp = ''
        if '->' in rest:
            rest, comp = rest.split('->', 1)
            comp = comp.strip()
        parts = [p.strip() for p in rest.split('/')]
        out[ev.strip()] = (parts[0], (parts[1] if len(parts) > 1 else 'ui').lower(), comp)
    return out


def generate(path, title=None, dispatch=False, stream=False):
    rows = list(Dbf(path).rows())
    src_aliases, src_rels = doc_source(rows)
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
    stream_vars = []      # R70: [(objid, cvar)] -- one entry per BOUND grid
    # R70.1. The first version of --stream bound EVERY grid, including the three
    # the contract already refuses (editable, ordinal spec, unjoined two-alias
    # spec). A generator that ships a binding its own gate refused is worse than
    # no gate. The predicates live in manifest.py so the reasons exist once.
    stream_refused = {}
    if stream:
        import manifest as _mf
        stream_refused = _mf.stream_refusals(_mf.manifest(path))
    # R70.5, found by RUNNING the generated window: the tree drew
    # "STUDENTS -> ENROLL ON SID" from SOURCE while the stream returned ENROLL
    # record 1 on every row, because nothing had told the ENGINE about the join.
    # The document declared a relation the runtime never established, and the
    # result was three rows that looked right and were wrong. Contract 10c makes
    # a cross-alias spec legal only when SOURCE relates the aliases, so the SAME
    # declaration must reach the engine -- through the house's own
    # relations_api, not a re-derived join.
    # Correction 49, caught by the fixture sweep: the relation calls were gated on
    # "this document HAS relations" while the includes were gated on "a grid was
    # actually bound" -- so nine of eighteen fixtures emitted relations_api calls
    # with no header. The two must be the SAME condition, and it can only be
    # answered before the walk, because the form is emitted before its children.
    will_bind = bool(stream) and any(
        (r['KIND'] or '').strip().lower() == 'grid'
        and (r['BINDING'] or '').strip()
        and (r['OBJID'] or '').strip() not in stream_refused
        for r in objs)
    stream_relations = list(src_rels) if will_bind else []
    made_rels = []
    rec = {(r['OBJID'] or '').strip(): r for r in objs}

    def var(oid):
        return 'w_' + oid.replace('.', '_')

    def has_statusbar(form_oid):
        return any((c['KIND'] or '').strip().lower() == 'statusbar'
                   for c in kids.get(form_oid, []))

    # R44: R39 fixed this on Tk and the wx generator was written from R38, so it
    # shipped the defect R39 had already named -- one scope for the whole window,
    # which makes ANY container's destruction cancel every SIBLING's queued work.
    # R21.4 scopes cancellation to the container. The generator now emits one
    # std::shared_ptr<Scope> per container and each handler captures its nearest
    # enclosing one BY VALUE, so the scope outlives the widget that owned it and
    # a late completion finds an object to ask rather than a dangling pointer.
    CONTAINER_KINDS = ('form', 'group', 'panel', 'page', 'pageset')
    scopes = {}

    def emit_scope(oid, v, ind):
        """Create this container's scope, and cancel ONLY this container's work
        when it is destroyed. wxEVT_DESTROY propagates up from children, so the
        handler checks the event's window -- without that guard the first child
        destroyed would cancel its parent, which is the same off-by-one-container
        error in the other direction."""
        sc = 'sc_' + oid.replace('.', '_')
        scopes[oid] = sc
        # A target cannot exercise R21.4 without a handle to the container, and
        # unlike Tk (which hands back a dict of widgets) a generated OnInit keeps
        # its locals. wx already has the mechanism: name the window after the
        # OBJID and `wxWindow::FindWindowByName` resolves it.
        body.append('%s%s->SetName("%s");' % (ind, v, oid))
        body.append('%sauto %s = std::make_shared<uidef::Scope>("%s");'
                    % (ind, sc, oid))
        # Both the scope AND the window pointer must be captured: the window is a
        # local of the generated OnInit, so naming it inside the lambda without
        # capturing it does not compile. It is captured BY VALUE as a raw pointer
        # for identity comparison only -- the handler never dereferences it, which
        # matters because it fires while that window is being destroyed.
        body.append('%s%s->Bind(wxEVT_DESTROY, [%s, %s](wxWindowDestroyEvent& e){ '
                    'if (e.GetWindow() == %s) %s->destroy(); e.Skip(); });'
                    % (ind, v, sc, v, v, sc))
        return sc

    def scope_for(oid):
        cur = oid
        while cur:
            if cur in scopes:
                return scopes[cur]
            cur = (rec[cur]['PARENT'] or '').strip() if cur in rec else ''
        return 'g_scope'

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
        # R56: the four components of a font's identity, not three.
        slant = ('wxFONTSTYLE_ITALIC'
                 if (fp.get('italic') or '').upper().startswith('.T')
                 else 'wxFONTSTYLE_NORMAL')
        weight = ('wxFONTWEIGHT_BOLD'
                  if (fp.get('bold') or '').upper().startswith('.T')
                  else 'wxFONTWEIGHT_NORMAL')
        return ('wxFont(%s, wxFONTFAMILY_DEFAULT, %s, %s, false, %s)'
                % (fp['size'], slant, weight, cstr(fp['name'])))

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
            if stream and stream_relations and not made_rels:
                made_rels.append(1)
                body.append('%srelations_api::attach_engine(shell_engine());' % ind)
                for pa, ch, ed in stream_relations:
                    if not ed:
                        notes.append('SKIPPED relation %s -> %s -- no ON field '
                                     'in SOURCE' % (pa, ch))
                        continue
                    body.append('%srelations_api::add_relation(%s, %s, {%s});'
                                % (ind, cstr(pa.upper()), cstr(ch.upper()),
                                   cstr(ed.upper())))
                body.append('%srelations_api::set_current_parent_name(%s);'
                            % (ind, cstr((src_aliases[0] if src_aliases else '')
                                         .upper())))
                body.append('%srelations_api::set_autorefresh(true);' % ind)
            if dispatch:
                body.append('%sg_rt = new uidef::Runtime(%s, DOMAINS, '
                            'wxTheApp->argc > 2);' % (ind, v))
                body.append('%sg_scope = std::make_shared<uidef::Scope>("%s");'
                            % (ind, oid))
                # The frame's own scope IS g_scope -- a window-wide cancel is still
                # correct FOR THE WINDOW. What R44 removes is every container
                # sharing it.
                scopes[oid] = 'g_scope'
                body.append('%sg_scope_owner = %s;' % (ind, v))
                body.append('%suidef_register(*g_rt);' % ind)
            sub = child_sizer(oid, flow, pr, v, ind)
            for c in kids.get(oid, []):
                emit(c, v, flow, sub, depth)
            close_sizer(oid, flow, v, sub, ind)
            if stream and has_statusbar(oid):
                if len(stream_vars) == 1:
                    body.append('%s%s->SetStatusText(wxString::FromUTF8('
                                '%s.status_line().c_str()));'
                                % (ind, v, stream_vars[0][1]))
                elif len(stream_vars) > 1:
                    body.append('%s// R70 OPEN: %d bound grid(s), one statusbar -- '
                                'contract 4b(c) names ONE status source and does '
                                'not say which. Left unset rather than guessed.'
                                % (ind, len(stream_vars)))
            if sub:
                body.append('%s%s->Layout();' % (ind, v))
            body.append('%s%s->Show();' % (ind, v))
            if dispatch:
                body.append('%suidef_after_init(%s);' % (ind, v))
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
                if dispatch:
                    emit_scope(oid, v, ind)
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
                if dispatch:
                    emit_scope(oid, v, ind)
                for c in kids.get(oid, []):
                    emit(c, v, flow, szname, depth + 1)
                outer = szname
            if sizer_var:
                add_to(sizer_var, outer, ind, is_sizer=True)
            return

        if kind in FRAME_KINDS:
            # R66/contract 4b -- the five ERSATZ regions in wx. Structure, not data:
            # a generated frontend has no records until a handler supplies them, the
            # same way a wxTextCtrl is generated empty. The columns come from
            # BINDING (contract 10c) and the tree edges from SOURCE (4b(a)), so
            # nothing is generated from a count property -- R6's objection answered.
            b = (r['BINDING'] or '').strip()
            specs = [x.strip() for x in b.split(',') if x.strip()]
            first = (src_aliases[0] if src_aliases else '?')

            def _heads():
                out = []
                for sp in specs:
                    if sp == '*':
                        out.append(first.upper() + '.*')
                    elif sp.endswith('.*'):
                        out.append(sp.upper())
                    else:
                        out.append(sp.split('.')[-1].upper())
                return out or ['*']

            if kind == 'grid':
                body.append('%sauto* %s = new wxListCtrl(%s, wxID_ANY, %s, %s, '
                            'wxLC_REPORT | wxLC_SINGLE_SEL);'
                            % (ind, v, parent_var, pos, size))
                for i, h in enumerate(_heads()):
                    body.append('%s%s->InsertColumn(%d, %s, wxLIST_FORMAT_LEFT, 90);'
                                % (ind, v, i, cstr(h)))
                # BETA-7.1 / contract 4b(b): the browse is read-only, and wxLC_REPORT
                # without wxLC_EDIT_LABELS is read-only by construction rather than
                # by convention. Stated so a later edit does not quietly add it.
                body.append('%s// read-only by construction: no wxLC_EDIT_LABELS '
                            '(BETA-7.1, contract 4b(b))' % ind)
                if stream and oid in stream_refused:
                    body.append('%s// R70 REFUSED stream binding: %s'
                                % (ind, stream_refused[oid]))
                    notes.append('REFUSED stream binding on %s -- %s'
                                 % (oid, stream_refused[oid]))
                elif stream and not specs:
                    notes.append('REFUSED stream binding on %s -- no BINDING' % oid)
                if stream and specs and oid not in stream_refused:
                    spec = b
                    if spec.strip() == '*':
                        spec = '%s.*' % first
                    sv = '%s_stream' % v
                    body.append('%sg_streams.push_back('
                                'std::make_unique<dottalk::DbTupleStream>(%s));'
                                % (ind, cstr(spec)))
                    body.append('%sauto& %s = *g_streams.back();' % (ind, sv))
                    o = str(pr.get('order', '')).strip().lower()
                    if o in ('physical', 'inx', 'cnx'):
                        body.append('%s%s.set_order_%s();' % (ind, sv, o))
                    elif o:
                        # Unreachable while stream_refusals gates Order, and left
                        # in on purpose: R70.2 was this branch dropping a declared
                        # property in silence. If the gate is ever loosened the
                        # drop is reported instead of vanishing.
                        notes.append('DROPPED Order=%s on %s -- not a stream order'
                                     % (o, oid))
                    filt = str(pr.get('filter', '')).strip()
                    if filt:
                        body.append('%s%s.set_filter_for(%s);' % (ind, sv, cstr(filt)))
                    body.append('%s%s.top();' % (ind, sv))
                    nrows = max(1, min(int(float(pr.get('rowlimit', 20) or 20)), 200))
                    body.append('%suidef_fill_grid(%s, %s, %d);' % (ind, v, sv, nrows))
                    stream_vars.append((oid, sv))
            elif kind == 'tree':
                root = b.lower() or first
                body.append('%sauto* %s = new wxTreeCtrl(%s, wxID_ANY, %s, %s, '
                            'wxTR_DEFAULT_STYLE);'
                            % (ind, v, parent_var, pos, size))
                body.append('%sauto %s_root = %s->AddRoot(%s);'
                            % (ind, v, v, cstr(root.upper())))
                edges = [(c, e) for a_, c, e in src_rels if a_ == root]
                for c, e in edges:
                    body.append('%s%s->AppendItem(%s_root, %s);'
                                % (ind, v, v, cstr('%s   ON %s' % (c.upper(),
                                                                   e or '?'))))
                if not edges:
                    body.append('%s%s->AppendItem(%s_root, %s);'
                                % (ind, v, v, cstr('(no Relation edge in SOURCE)')))
                body.append('%s%s->Expand(%s_root);' % (ind, v, v))
            elif kind in ('detail', 'summary'):
                szn = '%s_sizer' % v
                body.append('%sauto* %s = new wxStaticBoxSizer(wxVERTICAL, %s, %s);'
                            % (ind, szn, parent_var, cstr(cap)))
                body.append('%sauto* %s = %s->GetStaticBox();' % (ind, v, szn))
                if kind == 'detail':
                    if any(sp.endswith('.*') or sp == '*' for sp in specs):
                        lines = ['(every field of %s)' % first.upper()]
                    else:
                        lines = ['%s :' % h for h in _heads()]
                else:
                    root = b.lower() or first
                    kidsx = [c for a_, c, _e in src_rels if a_ == root]
                    lines = (['%s : n' % c.upper() for c in kidsx]
                             or ['(no child of %s in SOURCE)' % root.upper()])
                for i, ln in enumerate(lines):
                    body.append('%s%s->Add(new wxStaticText(%s, wxID_ANY, %s), '
                                '0, wxALL, 2);' % (ind, szn, v, cstr(ln)))
                if sizer_var:
                    add_to(sizer_var, szn, ind, is_sizer=True)
                return
            else:
                labels = {'rows': 'ROWS SHOWN', 'limit': 'LIMIT', 'order': 'ORDER',
                          'root': 'ROOT', 'recno': 'RECNO', 'status': 'STATUS'}
                shows = [x.strip().lower() for x in
                         str(pr.get('shows', '')).replace(',', ' ').split()]
                txt = ' | '.join('%s: --' % labels[x] for x in shows if x in labels)
                pk = (rec.get((r['PARENT'] or '').strip(), {}) or {})
                pkind = ((pk.get('KIND') or '').strip().lower()
                         if hasattr(pk, 'get') else '')
                if pkind == 'form':
                    # wx idiom: a frame OWNS its status bar. Adding a bordered
                    # static text to the frame's sizer instead compiles and renders
                    # something that is not a status bar -- R40's lesson.
                    body.append('%s%s->CreateStatusBar();'
                                % (ind, var((r['PARENT'] or '').strip())))
                    body.append('%s%s->SetStatusText(%s);'
                                % (ind, var((r['PARENT'] or '').strip()),
                                   cstr(txt or '(statusbar declares no Shows)')))
                    return
                body.append('%sauto* %s = new wxStaticText(%s, wxID_ANY, %s, %s, %s, '
                            'wxBORDER_SUNKEN);'
                            % (ind, v, parent_var,
                               cstr(txt or '(statusbar declares no Shows)'),
                               pos, size))
            f = fontexpr(r)
            if f:
                body.append('%s%s->SetFont(%s);' % (ind, v, f))
            if sizer_var:
                add_to(sizer_var, v, ind)
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

        if dispatch and kind == 'button':
            hs = parse_handlers(r['HANDLERS'])
            if 'Click' in hs:
                name, disp, comp = hs['Click']
                alias = (r['BINDING'] or '').strip().split('.')[0].lower()
                own = scope_for((r['PARENT'] or '').strip())
                # R58: `g_scope` is a global, and capturing a global by value is
                # redundant -- gcc warns "capture of variable with non-automatic
                # storage duration", which is an error under -Werror. Container
                # scopes ARE locals and must still be captured.
                cap = '' if own == 'g_scope' else own
                body.append('%s%s->Bind(wxEVT_BUTTON, [%s](wxCommandEvent&){ '
                            'g_rt->fire("%s", "%s", %s, "%s", "%s"); });'
                            % (ind, v, cap, name, disp, own, alias, comp))

        if kind in ('panel', 'page', 'pageset'):
            if dispatch:
                emit_scope(oid, v, ind)
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

    doc = [r for r in rows if (r['RECKIND'] or '').strip() == 'DOC'][0]
    doms = domains_from_source(doc['SOURCE'])
    # R66: <wx/wx.h> does not pull in listctrl or treectrl, and the generator that
    # emits a wxListCtrl without them produces a file that does not compile -- which
    # is the cheapest possible version of R40's lesson and still had to be found by
    # building. Included unconditionally: the cost is compile time, and a
    # conditional include is one more thing that can be wrong per document.
    head = ['#include <wx/wx.h>', '#include <wx/notebook.h>', '#include <wx/gbsizer.h>',
            '#include <wx/statbox.h>', '#include <wx/listctrl.h>',
            '#include <wx/treectrl.h>']
    pre = []
    # R70.3. Emitting the helper for a document with no bound grid gives
    # -Wunused-function, and `-fsyntax-only` cannot see it -- gcc only warns
    # once it generates code. A syntax check is not a build (R40 again).
    if will_bind:
        head += ['#include "xbase.hpp"', '#include "db_tuple_stream.hpp"',
                 '#include "set_relations.hpp"',
                 '#include <memory>', '#include <string>', '#include <vector>']
        pre += [
            '// R70: the frame\'s runtime contract (contract 4c) is TupleStream. The',
            '// generated file OWNS the streams for the life of the window; a stream',
            '// holds engine cursor state and must outlive the fill.',
            '// The engine is the HOST\'s, not the generated file\'s: shell.cpp defines',
            '// this seam and a wx host supplies its own. Declared, never defined here.',
            'extern "C" xbase::XBaseEngine* shell_engine();',
            '',
            'std::vector<std::unique_ptr<dottalk::DbTupleStream>> g_streams;',
            '',
            '// The only place rows enter a generated grid. next_page(max_rows) is the',
            '// paging verb (contract 4c); the house clamps max_rows to 1..200 and the',
            '// generator has already clamped RowLimit to the same range.',
            '//',
            '// R70.4. The generator declares one column per comma-separated spec, which',
            '// is right for `alias.field` and WRONG for `*` and `alias.*`: those are one',
            '// spec and N values, and N is a property of the SCHEMA, which the generator',
            '// does not have. The first version set items on columns that did not exist',
            '// -- it compiled, it linked, and it dropped every field after the first.',
            '// So the columns are reconciled against the engine on the first row: the',
            '// arity and the LABELS both come from TupleRow::columns, which is the only',
            '// place that knows them. The generated heads are the pre-fill placeholder,',
            '// exactly as they are without --stream.',
            'static void uidef_fill_grid(wxListCtrl* grid, dottalk::TupleStream& s,',
            '                            std::size_t max_rows) {',
            '    grid->DeleteAllItems();',
            '    long row = 0;',
            '    bool reconciled = false;',
            '    for (const auto& t : s.next_page(max_rows)) {',
            '        if (t.values.empty()) continue;',
            '        if (!reconciled) {',
            '            const int have = grid->GetColumnCount();',
            '            const int want = static_cast<int>(t.values.size());',
            '            for (int c = have; c < want; ++c)',
            '                grid->InsertColumn(c, wxEmptyString, wxLIST_FORMAT_LEFT, 90);',
            '            for (int c = 0; c < want; ++c) {',
            '                const std::string nm =',
            '                    (static_cast<std::size_t>(c) < t.columns.size())',
            '                        ? t.columns[static_cast<std::size_t>(c)].name',
            '                        : std::string();',
            '                if (nm.empty()) continue;',
            '                wxListItem col;',
            '                col.SetMask(wxLIST_MASK_TEXT);',
            '                col.SetText(wxString::FromUTF8(nm.c_str()));',
            '                grid->SetColumn(c, col);',
            '            }',
            '            reconciled = true;',
            '        }',
            '        const long i = grid->InsertItem(',
            '            row, wxString::FromUTF8(t.values[0].c_str()));',
            '        for (std::size_t c = 1; c < t.values.size(); ++c)',
            '            grid->SetItem(i, static_cast<int>(c),',
            '                          wxString::FromUTF8(t.values[c].c_str()));',
            '        ++row;',
            '    }',
            '}',
            '']
    if dispatch:
        head += ['#include "uidef_rt.h"', '#include <cstdio>']
        # Correction 50: this was `pre =`, which SILENTLY discarded the stream
        # block above whenever both flags were given. --dispatch and --stream are
        # independent modes and must compose; found by asking whether they did,
        # not by anything failing.
        pre += ['uidef::Runtime* g_rt = nullptr;',
               'std::shared_ptr<uidef::Scope> g_scope;',
               'wxWindow* g_scope_owner = nullptr;',
               'void uidef_register(uidef::Runtime&);   // the TARGET supplies these',
               'void uidef_after_init(wxWindow*);        // and its own entry point',
               '']
    # Without dispatch the app has nothing to do, so a run flag exits it after the
    # window is up. With dispatch the target's own `uidef_after_init` owns the exit,
    # and emitting both made the second argument quit before anything ran.
    tail = ([] if dispatch else
            ['  if (wxTheApp->argc > 1) CallAfter([]{ wxTheApp->ExitMainLoop(); });'])
    src = head + [''] + pre + [
           'class App : public wxApp { public: bool OnInit() override {'] + (
           ['  static const std::vector<std::vector<std::string>> DOMAINS = {%s};'
            % ', '.join('{%s}' % ', '.join('"%s"' % a for a in d) for d in doms)]
           if dispatch else []) + body + [

           ] + tail + ['  return true; } };', 'wxIMPLEMENT_APP(App);']
    return "\n".join(src), notes, made[0]


if __name__ == '__main__':
    src, notes, n = generate(sys.argv[1], dispatch='--dispatch' in sys.argv,
                             stream='--stream' in sys.argv)
    args = [a for a in sys.argv[2:] if not a.startswith('--')]
    out = args[0] if args else None
    if out:
        open(out, 'w').write(src)
    print("%s -> %s   %d widget(s)" % (os.path.basename(sys.argv[1]), out or '(stdout)', n))
    for x in dict.fromkeys(notes):
        print("  " + x)
    if not out:
        print(src)
