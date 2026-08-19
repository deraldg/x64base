#!/usr/bin/env python3
"""Import a VFP .SCX into a UIDEF v1 table. AIF-120.

Per contract section 5b, imports land as FLOW=free with an ORIGIN group: real
forms do not express as row/column/grid from their coordinates. Nothing is
inferred that the source does not state.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf
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
GEO  = ('top','left','height','width')
# Contract section 9 event names
EVENTS = {'click':'Click','init':'Init','interactivechange':'Change','activate':'Activate',
          'deactivate':'Deactivate','destroy':'Destroy','error':'Error',
          'gotfocus':'Focus','lostfocus':'Blur','load':'Load'}

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

    out=[{'RECKIND':'DOC','OBJID':'DOC1','PROVENANCE':'imported',
          'PROPS':uidef.props([('Version','1'),('Origin','vfp-scx'),
                               ('SourceFile', os.path.basename(scx_path))]),
          'SOURCE':uidef.props(src) if src else ''}]
    # The RESERVED record's lines are the document's FONT TABLE, not a decoration:
    # measured, 1670 of 1688 objects that declare a FontName in the corpus resolve
    # to a line of their own file's cache on (name, size) -- 98.9%. So it is parsed,
    # not just carried. Field 1 is the name and field 3 the point size; the rest are
    # metrics whose meaning is not established here, so they ride as `Metrics`.
    font_index = {}          # (name.lower(), size) -> 1-based FONTREF
    for i,f in enumerate(fonts,1):
        parts=[x.strip() for x in f.split(',')]
        pairs=[('Metrics','%s'%f)]
        if len(parts)>=3:
            pairs=[('Name','"%s"'%parts[0]),('Size',parts[2]),('Metrics','%s'%f)]
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
        key=(nm.lower(), sz)
        if key in font_index: return font_index[key]
        # A cache may lag an edit -- 18 of 1688 in the corpus. The object's own
        # declaration is the truth, so add a row for it rather than snapping it to
        # the nearest cache line.
        i=len(fonts)+len(extra_fonts)+1
        extra_fonts.append({'RECKIND':'FONT','OBJID':'FONT%d'%i,'ORDINAL':i,
                            'PROVENANCE':'derived',
                            'PROPS':uidef.props([('Name','"%s"'%nm),('Size',sz or '0'),
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

    n=0; ordinal={}
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
              if k not in GEO and k not in ('name','scalemode','controlsource')}
        hs=[]
        m=(r['METHODS'] or '')
        for mname in re.findall(r'^\s*PROCEDURE\s+([A-Za-z_]\w*)', m, re.I|re.M):
            ev=EVENTS.get(mname.lower())
            if ev: hs.append((ev, '%s / ui' % mname))
        out.append({'RECKIND':'OBJ','OBJID':ids[path(r)],'PARENT':pid,
                    'ORDINAL':ordinal[pid],'KIND':KINDMAP[b],
                    'FLOW':'free' if b in ('form','container','pageframe') else '',
                    'BINDING':p.get('controlsource','').strip('"'),
                    'FONTREF':fontref(p),'PROVENANCE':'imported',
                    'PROPS':uidef.props(sorted(keep.items())),
                    'ORIGIN':uidef.props(org),'HANDLERS':uidef.props(hs)})
    # FONTREF is an index into this document's FONT rows in table order, so any
    # row added for a declaration the cache lacked goes on the end, keeping the
    # indices already handed out valid.
    out.extend(extra_fonts)
    nrec,rlen,hlen = uidef.write(out_stem+'.DBF', out_stem+'.FPT', out)
    return out, refused, (nrec,rlen,hlen)

if __name__=='__main__':
    scx=sys.argv[1]; stem=sys.argv[2]
    out,refused,(n,rl,hl)=convert(scx,stem)
    print("%s -> %s.DBF  records=%d rlen=%d hlen=%d" % (os.path.basename(scx),stem,n,rl,hl))
    if refused: print("  REFUSED kinds (not in v1 vocabulary):", sorted(set(refused)))
    f=uidef.validate(out)
    print("  conformance findings:", f if f else "none")
