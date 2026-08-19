#!/usr/bin/env python3
"""Import a VFP .SCX into a UIDEF v1 table. AIF-120.

Per contract section 5b, imports land as FLOW=free with an ORIGIN group: real
forms do not express as row/column/grid from their coordinates. Nothing is
inferred that the source does not state.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf
import classlib
import uidef

# .SCX BASECLASS -> UIDEF KIND. Only the v1 vocabulary; anything else is REFUSED.
KINDMAP = {
    'form':'form', 'container':'panel', 'commandgroup':'group', 'optiongroup':'group',
    'pageframe':'pageset', 'page':'page',
    'label':'label', 'textbox':'text', 'editbox':'text', 'commandbutton':'button',
    'checkbox':'check', 'optionbutton':'radio', 'listbox':'list', 'combobox':'combo',
    'image':'image',
}
SKIP = {'dataenvironment','cursor','relation'}          # become SOURCE, not objects

# Properties the shared language NAMES, because a consumer must understand them.
# R15 set up a `name = value` property language with shared keys; R20.2 said the
# vocabulary is the DSL's, not VFP's spelling. Everything else still passes through
# verbatim under VFP's own key -- 648 distinct keys across the corpus, measured --
# which is fine for decoration and wrong for anything the layout depends on.
#
# `InputMask` is load-bearing: R25 measures that a bound control's width follows
# its MASK, not its field. A consumer that cannot find the mask cannot reproduce
# the width, so the mask gets a name.
RENAME_PROPS = {'inputmask': 'Mask'}

# Promoted to a COLUMN, not a property. Tab order is a second ordinal over the same
# children; see AIF120_TAB_ORDER_MEASUREMENT_V1.md and the owner's decision of
# 2026-08-19. Removed from PROPS so it is not carried twice.
PROMOTED = ('tabindex',)

# R31: a subclassed object is an INSTANCE. Its class's members are materialised
# into the document so the table stays self-contained -- a consumer should not need
# a `.VCX` reader to draw a form -- and they carry PROVENANCE `inherited` so the
# flattening is reversible and honest about where each row came from.
PROV_INHERITED = 'inherited'
CLASS_KEYS = ('Class', 'ClassSource')

# R30, the composition rule. A composite control stores its members as dotted
# property names on itself; they are part of the control, not children of the
# form. Measured: 272 member names behind 72 parents across the corpus.
# `KIND` of a member is fixed by the composite; nothing else is needed, because
# PARENT/ORDINAL/KIND/PROPS/ORIGIN could always express this.
COMPOSITE = {
    'optiongroup':  ('radio',  'buttoncount'),
    'commandgroup': ('button', 'buttoncount'),
    'pageframe':    ('page',   'pagecount'),
    'grid':         ('column', 'columncount'),   # `grid` is refused in v1 (R7)
}
# Member properties that become table fields rather than PROPS text.
MEMBER_GEO = ('top', 'left', 'width', 'height')
MEMBER_ORDER = ('pageorder', 'columnorder')

# Set by convert(): [(objid, kind, [child names]), ...] -- see implied_children.
LAST_IMPLIED = []
LAST_MATERIALISED = []      # R30: [(parent, kind, member name), ...]
LAST_COUNT_MISMATCH = []    # R30.1: [(parent, baseclass, key, declared, actual), ...]
LAST_INHERITED = []         # R31: [(instance, class, member), ...]
LAST_UNRESOLVED = []        # R31: [(instance, class, classloc, why), ...]
LAST_INH_HANDLERS = 0       # R32: event handlers inherited from a class
LAST_INH_CUSTOM = []        # R32: custom method names v1 cannot carry


def split_members(p):
    """Group an object's dotted properties into {member: {prop: value}}."""
    mem = {}
    for k, v in p.items():
        if '.' not in k:
            continue
        head, rest = k.split('.', 1)
        if '.' in rest:            # two levels deep -- R30 section 6, not handled
            continue
        mem.setdefault(head.strip().lower(), {})[rest.strip().lower()] = v
    return mem


def member_ordinal(name, mp, fallback):
    """Declared order if the member states one, else the suffix the name carries."""
    for k in MEMBER_ORDER:
        if k in mp:
            try:
                return int(float(mp[k]))
            except ValueError:
                pass
    digits = ''.join(c for c in name if c.isdigit())
    return int(digits) if digits else fallback


def handlers_of(rec):
    """Event handlers a record defines, as NAMES. R14: never a body.

    Returns [(event, "Name / ui"), ...]. A method whose name is not one of the
    contract's section 9 events is a custom method -- real behaviour that v1 has
    no concept for. Counted by the caller, never invented into an event.
    """
    out = []
    for mname in re.findall(r'^\s*PROCEDURE\s+([A-Za-z_]\w*)',
                            rec.get('METHODS') or '', re.I | re.M):
        ev = EVENTS.get(mname.lower())
        if ev:
            out.append((ev, '%s / ui' % mname))
    return out


def custom_methods(rec):
    """Named behaviour that is not an event. R32 counts these; v1 carries none."""
    out = []
    for mname in re.findall(r'^\s*PROCEDURE\s+([A-Za-z_]\w*)',
                            rec.get('METHODS') or '', re.I | re.M):
        if mname.lower() not in EVENTS:
            out.append(mname)
    return out


def implied_children(keep):
    """Child objects that exist only as dotted property names on their parent.

    R28.1, found by the gate 11 implementer: `UIDEF_STUDENTS`'s button panel has
    no child records at all. Its ten buttons live here --
    `cmdadd.caption = "\\<Add"`, `cmddelete.enabled = .F.` -- and R6 puts implicit
    children out of v1, so a conformant reader renders an empty panel and says
    nothing. Every wizard form loses its whole navigation bar that way.

    v1 still does not MATERIALISE them; that is a scope change and the owner's.
    What it must not do is lose them silently. Returns the names so the importer
    can name what it dropped.
    """
    names = []
    for k in keep:
        if '.' not in k:
            continue
        head = k.split('.', 1)[0].strip().lower()
        if head and head not in names:
            names.append(head)
    return sorted(names)
GEO  = ('top','left','height','width')
# Contract section 9 event names
EVENTS = {'click':'Click','init':'Init','interactivechange':'Change','activate':'Activate',
          'deactivate':'Deactivate','destroy':'Destroy','error':'Error',
          'gotfocus':'Focus','lostfocus':'Blur','load':'Load',
          # R32.2. Nine standard events the contract's section 9 list omits,
          # measured on 92 handlers in the corpus. `Unload` is 72 of them, and
          # section 9 carries `Load` without it -- an asymmetry that loses exactly
          # the teardown R21 spent a ruling on.
          'unload':'Unload', 'mousemove':'MouseMove', 'mousedown':'MouseDown',
          'mouseup':'MouseUp', 'dblclick':'DoubleClick', 'dragover':'DragOver',
          'dragdrop':'DragDrop', 'keypress':'KeyPress', 'valid':'Validate'}

def sprops(r):
    d={}
    for l in (r.get('PROPERTIES') or '').splitlines():
        if '=' in l:
            k,v=l.split('=',1); d[k.strip().lower()]=v.strip()
    return d

def convert(scx_path, out_stem):
    rows=list(Dbf(scx_path).rows())
    objs=[r for r in rows if (r['PLATFORM'] or '').strip().upper()!='COMMENT']
    fonts=[]
    for r in rows:
        if (r['PLATFORM'] or '').strip().upper()=='COMMENT' \
           and (r['UNIQUEID'] or '').strip().upper()=='RESERVED':
            fonts=[l.strip() for l in (r['PROPERTIES'] or '').replace('\r\n','\n').split('\n') if l.strip()]

    src=[]
    for r in objs:
        if (r['BASECLASS'] or '').strip().lower()=='cursor':
            p=sprops(r)
            if 'alias' in p: src.append(('Alias', p['alias'].strip('"')))
            if 'cursorsource' in p: src.append(('Table', p['cursorsource'].strip('"')))
            if 'order' in p: src.append(('Order', p['order'].strip('"')))
    # R36, closing R26.2. A `relation` record in the DataEnvironment says which work
    # areas move together, and R26 makes that a CORRECTNESS requirement: the lock
    # domain is the transitive closure of related areas, so a frontend that cannot
    # see the relations cannot know what to serialize. The importer discarded every
    # one of them -- `relation` is in SKIP -- while R26 was being written.
    for r in objs:
        if (r['BASECLASS'] or '').strip().lower()!='relation': continue
        p=sprops(r)
        par=p.get('parentalias','').strip('"'); ch=p.get('childalias','').strip('"')
        expr=p.get('relationalexpr','').strip('"')
        if par and ch:
            src.append(('Relation', '%s -> %s ON %s' % (par, ch, expr or '?')))

    out=[{'RECKIND':'DOC','OBJID':'DOC1','PROVENANCE':'imported',
          'PROPS':uidef.props([('Version','1'),('Origin','vfp-scx'),
                               ('SourceFile', os.path.basename(scx_path))]),
          'SOURCE':uidef.props(src) if src else ''}]
    # The RESERVED record's lines are the document's FONT TABLE, not a decoration:
    # measured, 1670 of 1688 objects that declare a FontName in the corpus resolve
    # to a line of their own file's cache on (name, size) -- 98.9%. So it is parsed,
    # not just carried. Field 1 is the name and field 3 the point size; the rest are
    # metrics whose meaning is not established here, so they ride as `Metrics`.
    font_index = {}          # (name.lower(), size) -> 1-based FONTREF, cache lines
    styled_index = {}        # (name.lower(), size, bold, italic) -> ref, derived
    # R56: a font's IDENTITY is name + size + weight + slant. The cache line's
    # fields beyond 1 and 3 are still uninterpreted, so a cache row is recorded as
    # NOT bold and NOT italic; an object that declares either gets a derived row.
    # Measured: 561 corpus objects declare FontBold (158 of them .T.) and 3 declare
    # FontItalic (all .T.), so 161 objects carried an emphasis the table dropped.
    for i,f in enumerate(fonts,1):
        parts=[x.strip() for x in f.split(',')]
        pairs=[('Metrics','%s'%f)]
        if len(parts)>=3:
            pairs=[('Name','"%s"'%parts[0]),('Size',parts[2]),
                   ('Bold','.F.'),('Italic','.F.'),('Metrics','%s'%f)]
            font_index[(parts[0].lower(), parts[2])]=i
        out.append({'RECKIND':'FONT','OBJID':'FONT%d'%i,'ORDINAL':i,
                    'PROVENANCE':'imported','PROPS':uidef.props(pairs)})
    extra_fonts=[]           # declarations the source cache does not contain

    def fontref(p):
        """Resolve an object's OWN declared font. 0 means the target's default.

        The old code was `1 if fonts else 0` -- every object pointed at cache line
        one. That discards a real declaration on 56% of corpus objects and asserts a
        font for the other 44%. The field table says 0 is the target default, so an
        object that states no font gets 0.
        """
        nm=(p.get('fontname') or '').strip().strip('"')
        if not nm: return 0
        sz=(p.get('fontsize') or '').strip()
        bold=(p.get('fontbold') or '').strip().upper().startswith('.T')
        ital=(p.get('fontitalic') or '').strip().upper().startswith('.T')
        if bold or ital:
            # R56: emphasis is part of the font, so a bold object cannot share the
            # plain cache line. Give it its own row, keyed on all four components.
            skey=(nm.lower(), sz, bold, ital)
            if skey in styled_index: return styled_index[skey]
            i=len(fonts)+len(extra_fonts)+1
            extra_fonts.append({'RECKIND':'FONT','OBJID':'FONT%d'%i,'ORDINAL':i,
                                'PROVENANCE':'derived',
                                'PROPS':uidef.props([('Name','"%s"'%nm),('Size',sz or '0'),
                                                     ('Bold','.T.' if bold else '.F.'),
                                                     ('Italic','.T.' if ital else '.F.'),
                                                     ('Metrics','(emphasis declared on the '
                                                      'object; the source cache has no '
                                                      'styled line)')])})
            styled_index[skey]=i
            return i
        key=(nm.lower(), sz)
        if key in font_index: return font_index[key]
        # A cache may lag an edit -- 18 of 1688 in the corpus. The object's own
        # declaration is the truth, so add a row for it rather than snapping it to
        # the nearest cache line.
        i=len(fonts)+len(extra_fonts)+1
        extra_fonts.append({'RECKIND':'FONT','OBJID':'FONT%d'%i,'ORDINAL':i,
                            'PROVENANCE':'derived',
                            'PROPS':uidef.props([('Name','"%s"'%nm),('Size',sz or '0'),
                                                 ('Bold','.F.'),('Italic','.F.'),
                                                 ('Metrics','(declared on the object; '
                                                  'not in the source font cache)')])})
        font_index[key]=i
        return i

    # OBJID per source object, keyed on the dotted path (R5: identity is the path)
    # R5: identity is the DOTTED PATH, never OBJNAME. form1.scx carries three
    # records named Header1 and four named Text1, distinguished only by PARENT.
    # Keying on OBJNAME collapses them -- the exact failure R5 was written for,
    # and the first version of this importer committed it.
    def path(r):
        par=(r['PARENT'] or '').strip(); nm=(r['OBJNAME'] or '').strip()
        return (par + '.' + nm).lower() if par else nm.lower()
    ids={}; n=0; refused=[]
    for r in objs:
        b=(r['BASECLASS'] or '').strip().lower()
        if b in SKIP: continue
        if b not in KINDMAP: refused.append(b); continue
        n+=1; ids[path(r)] = 'O%03d'%n

    n=0; ordinal={}; implied=[]; materialised=[]; counts=[]; mn_total=[0]
    inherited=[]; unresolved=[]; inherited_refused=[]
    inh_handlers=[0]; inh_custom=[]
    for r in objs:
        b=(r['BASECLASS'] or '').strip().lower()
        if b in SKIP or b not in KINDMAP: continue
        p=sprops(r); par=(r['PARENT'] or '').strip()
        pid=ids.get(par.lower(),'')
        ordinal[pid]=ordinal.get(pid,0)+1
        org=[]
        for g in GEO:
            if g in p: org.append(('ORIGIN_'+g.upper(), p[g]))
        if org: org.append(('ORIGIN_SCALE','px' if p.get('scalemode','3')=='3' else 'cell'))
        keep={RENAME_PROPS.get(k, k): v for k,v in p.items()
              if k not in GEO and k not in PROMOTED
              and k not in ('name','scalemode','controlsource')}
        try:
            tabord = int(float(p.get('tabindex') or 0))
        except ValueError:
            tabord = 0
        hs = handlers_of(r)
        oid = ids[path(r)]

        # R30: materialise a composite control's members as ordinary rows. Only
        # for a composite that is NOT subclassed -- when CLASS differs from
        # BASECLASS the members live in the class library and these properties are
        # overrides to them (R30 section 4, mechanism A), which v1 does not
        # resolve.
        cls = (r['CLASS'] or '').strip().lower()

        # R31, mechanism A: the object is an instance of a class. Materialise the
        # class's members here, applying this instance's overrides, so the design
        # table is self-contained. Failure is named, never silent (R20, R22.4).
        if cls and cls != b:
            keep['Class'] = '"%s"' % cls
            cl = (r['CLASSLOC'] or '').strip()
            if cl:
                keep['ClassSource'] = '"%s"' % cl
            lib_path, why = classlib.resolve_classloc(cl, scx_path)
            block = None
            if lib_path:
                try:
                    block = classlib.read_library(lib_path, Dbf).get(cls)
                except Exception as e:
                    why = 'library unreadable: %s' % e
            if block is None:
                unresolved.append((ids[path(r)], cls, cl, why))
            else:
                # R32: the class root's handlers are the instance's, unless the
                # instance defines the same event itself. An override replaces;
                # everything else inherits.
                own = {ev for ev, _ in hs}
                for ev, ref in handlers_of(block['root']):
                    if ev not in own:
                        hs.append((ev, ref))
                        inh_handlers[0] += 1
                inh_custom.extend(custom_methods(block['root']))
                over = split_members(p)
                for mi, m in enumerate(block['members'], 1):
                    mname = (m['OBJNAME'] or '').strip()
                    mb = (m['BASECLASS'] or '').strip().lower()
                    if mb in SKIP or mb not in KINDMAP:
                        inherited_refused.append((ids[path(r)], mname, mb))
                        continue
                    mp = sprops(m)
                    mp.update(over.get(mname.lower(), {}))   # instance wins
                    for dk in [k for k in keep
                               if k.split('.', 1)[0].strip().lower() == mname.lower()]:
                        keep.pop(dk, None)
                    morg = []
                    for g in GEO:
                        if g in mp:
                            morg.append(('ORIGIN_' + g.upper(), mp[g]))
                    if morg:
                        morg.append(('ORIGIN_SCALE',
                                     'px' if mp.get('scalemode', '3') == '3' else 'cell'))
                    mkeep = {RENAME_PROPS.get(k, k): v for k, v in mp.items()
                             if k not in GEO and k not in PROMOTED
                             and '.' not in k
                             and k not in ('name', 'scalemode', 'controlsource')}
                    mn_total[0] += 1
                    out.append({'RECKIND': 'OBJ', 'OBJID': 'M%03d' % mn_total[0],
                                'PARENT': ids[path(r)], 'ORDINAL': mi,
                                'KIND': KINDMAP[mb], 'FLOW': '',
                                'BINDING': (mp.get('controlsource') or '').strip('"'),
                                'FONTREF': fontref(mp), 'PROVENANCE': PROV_INHERITED,
                                'PROPS': uidef.props(sorted(mkeep.items())),
                                'ORIGIN': uidef.props(morg) if morg else '',
                                # R32: a member's event handlers inherit with it.
                                'HANDLERS': uidef.props(handlers_of(m))})
                    inh_handlers[0] += len(handlers_of(m))
                    inh_custom.extend(custom_methods(m))
                    inherited.append((ids[path(r)], cls, mname))

        members = []
        if b in COMPOSITE and (not cls or cls == b):
            mkind, countkey = COMPOSITE[b]
            mem = split_members(p)
            for i, (mname, mp) in enumerate(sorted(mem.items()), 1):
                members.append((mname, mp, member_ordinal(mname, mp, i)))
            if members:
                declared = p.get(countkey)
                try:
                    declared = int(float(declared)) if declared is not None else None
                except ValueError:
                    declared = None
                # R30.1: the composite states its own member count, so check it.
                if declared is not None and declared != len(members):
                    counts.append((oid, b, countkey, declared, len(members)))
                for mname, mp, morder in sorted(members, key=lambda t: t[2]):
                    # the member is a row now, so its dotted keys leave PROPS
                    for dk in [k for k in keep
                               if k.split('.', 1)[0].strip().lower() == mname]:
                        keep.pop(dk, None)
                    morg = []
                    for g in MEMBER_GEO:
                        if g in mp:
                            morg.append(('ORIGIN_' + g.upper(), mp[g]))
                    if morg:
                        # R30.2: member coordinates are already parent-relative,
                        # which is what section 8 means everywhere else.
                        morg.append(('ORIGIN_SCALE',
                                     'px' if p.get('scalemode', '3') == '3' else 'cell'))
                    mkeep = {RENAME_PROPS.get(k, k): v for k, v in mp.items()
                             if k not in MEMBER_GEO and k not in MEMBER_ORDER
                             and k not in PROMOTED
                             and k not in ('name', 'controlsource')}
                    mn_total[0] += 1
                    out.append({'RECKIND': 'OBJ', 'OBJID': 'M%03d' % mn_total[0],
                                'PARENT': oid, 'ORDINAL': morder,
                                'KIND': mkind, 'FLOW': '',
                                'BINDING': (mp.get('controlsource') or '').strip('"'),
                                'FONTREF': fontref(mp), 'PROVENANCE': 'imported',
                                'PROPS': uidef.props(sorted(mkeep.items())),
                                'ORIGIN': uidef.props(morg) if morg else ''})
                    materialised.append((oid, mkind, mname))

        imp = implied_children(keep)
        if imp:
            implied.append((oid, KINDMAP[b], imp))
        out.append({'RECKIND':'OBJ','OBJID':ids[path(r)],'PARENT':pid,
                    'ORDINAL':ordinal[pid],'KIND':KINDMAP[b],
                    'FLOW':'free' if b in ('form','container','pageframe') else '',
                    'BINDING':p.get('controlsource','').strip('"'),
                    'TABORDINAL':tabord,
                    'FONTREF':fontref(p),'PROVENANCE':'imported',
                    'PROPS':uidef.props(sorted(keep.items())),
                    'ORIGIN':uidef.props(org),'HANDLERS':uidef.props(hs)})
    # FONTREF is an index into this document's FONT rows in table order, so any
    # row added for a declaration the cache lacked goes on the end, keeping the
    # indices already handed out valid.
    # R28.1: name what is dropped. Kept as a module-level record rather than a
    # fourth return value, so every existing caller of convert() keeps working.
    global LAST_IMPLIED, LAST_MATERIALISED, LAST_COUNT_MISMATCH
    LAST_IMPLIED = implied
    LAST_MATERIALISED = materialised
    LAST_COUNT_MISMATCH = counts
    global LAST_INHERITED, LAST_UNRESOLVED
    LAST_INHERITED = inherited
    LAST_UNRESOLVED = unresolved
    global LAST_INH_HANDLERS, LAST_INH_CUSTOM
    LAST_INH_HANDLERS = inh_handlers[0]
    LAST_INH_CUSTOM = inh_custom
    out.extend(extra_fonts)
    nrec,rlen,hlen = uidef.write(out_stem+'.DBF', out_stem+'.FPT', out)
    return out, refused, (nrec,rlen,hlen)

if __name__=='__main__':
    scx=sys.argv[1]; stem=sys.argv[2]
    out,refused,(n,rl,hl)=convert(scx,stem)
    print("%s -> %s.DBF  records=%d rlen=%d hlen=%d" % (os.path.basename(scx),stem,n,rl,hl))
    if refused: print("  REFUSED kinds (not in v1 vocabulary):", sorted(set(refused)))
    if LAST_INH_HANDLERS or LAST_INH_CUSTOM:
        print("  INHERITED HANDLERS (R32): %d event handler(s) carried; "
              "%d custom method(s) NOT carried -- v1 has no concept for them"
              % (LAST_INH_HANDLERS, len(LAST_INH_CUSTOM)))
        if LAST_INH_CUSTOM:
            u=sorted(set(LAST_INH_CUSTOM))
            print("    custom: %s%s" % (", ".join(u[:8]), " ..." if len(u)>8 else ""))
    if LAST_INHERITED:
        byc={}
        for _,c,_ in LAST_INHERITED: byc[c]=byc.get(c,0)+1
        print("  INHERITED MEMBERS materialised (R31): %d from %d class(es) -- %s"
              % (len(LAST_INHERITED), len(byc),
                 ", ".join("%s x%d"%(c,n) for c,n in sorted(byc.items()))))
    if LAST_UNRESOLVED:
        # One line per distinct class, not per instance. Naming a refusal is the
        # rule (R20, R22.4); repeating it twenty times is noise, which is the same
        # defect one level up.
        g = {}
        for oid, c, cl, why in LAST_UNRESOLVED:
            g.setdefault((c, cl, why), []).append(oid)
        print("  REFUSED classes (R31) -- %d instance(s) across %d class(es):"
              % (len(LAST_UNRESOLVED), len(g)))
        for (c, cl, why), oids in sorted(g.items()):
            print("    %-16s x%-3d %s" % (c, len(oids), why))
            print("        CLASSLOC %s" % cl)
    if LAST_MATERIALISED:
        byk={}
        for _,k,_ in LAST_MATERIALISED: byk[k]=byk.get(k,0)+1
        print("  COMPOSITE MEMBERS materialised (R30): %d -- %s"
              % (len(LAST_MATERIALISED),
                 ", ".join("%s x%d"%(k,v) for k,v in sorted(byk.items()))))
    for oid,b,key,dec,act in LAST_COUNT_MISMATCH:
        print("  R30.1 COUNT MISMATCH on %s (%s): %s says %d, %d materialised"
              % (oid,b,key,dec,act))
    if LAST_IMPLIED:
        tot=sum(len(v) for _,_,v in LAST_IMPLIED)
        print("  IMPLIED CHILDREN dropped -- %d object(s) name %d child(ren) only as"
              " dotted properties (R6 scope, R28.1 naming):" % (len(LAST_IMPLIED), tot))
        for oid,kind,names in LAST_IMPLIED:
            print("    %-6s %-8s %2d: %s" % (oid, kind, len(names), ", ".join(names)))
    f=uidef.validate(out)
    print("  conformance findings:", f if f else "none")
