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
    for i,f in enumerate(fonts,1):
        out.append({'RECKIND':'FONT','OBJID':'FONT%d'%i,'ORDINAL':i,
                    'PROVENANCE':'imported','PROPS':'Metrics = %s\r\n'%f})

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
        keep={k:v for k,v in p.items()
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
                    'FONTREF':1 if fonts else 0,'PROVENANCE':'imported',
                    'PROPS':uidef.props(sorted(keep.items())),
                    'ORIGIN':uidef.props(org),'HANDLERS':uidef.props(hs)})
    nrec,rlen,hlen = uidef.write(out_stem+'.DBF', out_stem+'.FPT', out)
    return out, refused, (nrec,rlen,hlen)

if __name__=='__main__':
    scx=sys.argv[1]; stem=sys.argv[2]
    out,refused,(n,rl,hl)=convert(scx,stem)
    print("%s -> %s.DBF  records=%d rlen=%d hlen=%d" % (os.path.basename(scx),stem,n,rl,hl))
    if refused: print("  REFUSED kinds (not in v1 vocabulary):", sorted(set(refused)))
    f=uidef.validate(out)
    print("  conformance findings:", f if f else "none")
