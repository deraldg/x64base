#!/usr/bin/env python3
"""Derive FLOW/ORDINAL from absolute coordinates. AIF-120, the 5b problem.

5b clustered TOP and LEFT independently and demanded a strict lattice; that fails
because a label is baseline-aligned with its field, so their TOPs differ by a few
units while a human sees one row.

Different decomposition: COLUMNS ARE CRISP, ROWS ARE NOT. Cluster on LEFT to get
columns, sort each column by TOP, then read rows off by index within column. A
baseline offset is a within-row difference, so it never crosses a column boundary
and cannot corrupt the row assignment.
"""
import sys, collections
sys.path.insert(0,'/tmp/gen')
from read_vfp_binary import Dbf

def props(r):
    d={}
    for l in (r.get('PROPERTIES') or '').splitlines():
        if '=' in l: k,v=l.split('=',1); d[k.strip().lower()]=v.strip()
    return d
def num(p,k):
    try: return float(p[k])
    except (KeyError,ValueError): return None
def clust(vals,tol):
    out=[]
    for v in sorted(vals):
        if out and v-out[-1][-1]<=tol: out[-1].append(v)
        else: out.append([v])
    return out

def infer(children, tol=6):
    """children: list of (top,left,tag). Returns (flow, assignment, why)."""
    pts=[(t,l,g) for t,l,g in children if t is not None and l is not None]
    if len(pts)<2: return ('free',None,'fewer than two positioned children')
    lefts=clust([l for _,l,_ in pts],tol)
    ncol=len(lefts)
    if ncol==1: return ('column',None,'one left cluster')
    tops=clust([t for t,_,_ in pts],tol)
    if len(tops)==1: return ('row',None,'one top cluster')
    # assign each point to its left-cluster
    colof={}
    for ci,c in enumerate(lefts):
        for v in c: colof[v]=ci
    cols=collections.defaultdict(list)
    for t,l,g in pts: cols[colof[l]].append((t,g))
    for ci in cols: cols[ci].sort()
    depths={ci:len(v) for ci,v in cols.items()}
    # A REAL FORM IS A GRID PLUS OUTLIERS. Requiring every column to have equal
    # depth rejects STUDENTS.SCX -- nine labels, nine fields, and one button
    # container that belongs to neither column. So: take the MODAL depth as the
    # grid, and treat shallower columns as separate blocks ordered after it.
    counts=collections.Counter(depths.values())
    mode,mode_n=counts.most_common(1)[0]
    grid_cols=[ci for ci,d in depths.items() if d==mode]
    outlier_cols=[ci for ci,d in depths.items() if d!=mode]
    n_out=sum(depths[ci] for ci in outlier_cols)
    if mode>=2 and len(grid_cols)>=2 and n_out<=max(1,0.25*len(pts)):
        assign={}
        for ci in grid_cols:
            for ri,(t,g) in enumerate(cols[ci]): assign[g]=(ri,ci)
        base=mode
        for ci in outlier_cols:
            for ri,(t,g) in enumerate(cols[ci]): assign[g]=(base+ri,0)
        return ('grid',assign,
                '%d grid columns x %d rows + %d outlier(s)'%(len(grid_cols),mode,n_out))
    return ('free',None,'no modal grid: column depths %s'%sorted(depths.values()))

def analyse(path, tol=6, verbose=False):
    rows=[r for r in Dbf(path).rows() if (r['PLATFORM'] or '').strip().upper()!='COMMENT']
    kids=collections.defaultdict(list)
    for r in rows:
        par=(r['PARENT'] or '').strip()
        if par: kids[par].append(r)
    out=collections.Counter()
    for parent,cs in kids.items():
        ch=[]
        for c in cs:
            p=props(c)
            ch.append((num(p,'top'),num(p,'left'),(c['OBJNAME'] or '').strip()))
        flow,assign,why=infer(ch,tol)
        out[flow]+=1
        if verbose: print("   %-18s %-7s %s" % (parent[:18],flow,why))
    return out

if __name__=='__main__':
    for f in sys.argv[1:]:
        print("=== %s" % f); analyse(f,verbose=True)
