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
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# `read_vfp_binary` is the VFP binary reader and it lives in tools/vfp.
# gui/uidef/read_vfp_binary.py is a GITIGNORED working copy, so importing it
# from this directory made nine committed tools unimportable on a fresh clone --
# found by the house 'sweep for your own leftovers' rule, not by anything failing.
# tools/vfp goes on the path FIRST so the ignored copy can never shadow it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vfp'))
from read_vfp_binary import Dbf
from import_scx import SKIP        # one definition of "not a visual object"

# A DataEnvironment is not a layout group. Its children are cursors and relations,
# they all sit at top 0, and asking a coordinate heuristic about them yields `row`
# -- 9 times in this corpus. The importer has always skipped these (import_scx.SKIP
# turns them into SOURCE, not objects), so the design table was never polluted; the
# MEASUREMENT was. Reusing the importer's set rather than keeping a second opinion.

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

def is_visual(rows):
    """Map a parent path -> False when that object is one the importer skips."""
    base={}
    for r in rows:
        nm=(r['OBJNAME'] or '').strip().lower()
        par=(r['PARENT'] or '').strip().lower()
        full=(par+'.'+nm) if par else nm
        base[full]=(r['BASECLASS'] or '').strip().lower()
    def ok(parent):
        b=base.get((parent or '').strip().lower())
        return b not in SKIP
    return ok

def analyse(path, tol=6, verbose=False):
    rows=[r for r in Dbf(path).rows() if (r['PLATFORM'] or '').strip().upper()!='COMMENT']
    ok=is_visual(rows)
    kids=collections.defaultdict(list)
    for r in rows:
        par=(r['PARENT'] or '').strip()
        if par and ok(par): kids[par].append(r)
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
