#!/usr/bin/env python3
"""Import a VFP .MNX menu into a UIDEF v1 table. AIF-120, contract section 11.

Structure, measured: OBJTYPE 1 is the menu header; OBJTYPE 2 declares a container
whose name is in LEVELNAME and whose child count is in NUMITEMS; OBJTYPE 3 is an
item parented by its LEVELNAME and ordered by ITEMNUM.

Per R12.4 a menu row carries NO ORIGIN -- the format has no geometry column of any
kind, measured across 205 records in four files. Per R8 the mnemonic escape `\\<`
and separator `\\-` are the language's own syntax and are carried, not stripped.
NUMITEMS is verified against the observed child count, in the spirit of R13's
RESERVED2: a declared count that can be checked should be checked.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf
import uidef

def caption(prompt):
    """Return (caption, mnemonic_index, is_separator). R8: \\< marks the mnemonic."""
    p = prompt or ''
    if p.strip() == '\\-':
        return '', None, True
    i = p.find('\\<')
    if i >= 0:
        return p[:i] + p[i+2:], i, False
    return p, None, False

def convert(mnx_path, out_stem):
    t = Dbf(mnx_path); rows = list(t.rows())
    hdr = [r for r in rows if (r['OBJTYPE'] or '').strip() == '1']
    conts = [r for r in rows if (r['OBJTYPE'] or '').strip() == '2']
    items = [r for r in rows if (r['OBJTYPE'] or '').strip() == '3']

    # NESTING. The item -> submenu link is NOT a column. Measured: OBJCODE = 77
    # marks an item that opens a popup (1 of 1 in test_go, 9 of 9 in test_main,
    # matching the submenu count exactly), and the container that follows it in
    # DOCUMENT ORDER is the popup it opens -- 9 of 9.
    #
    # Do NOT pair them by name. Two of the nine openers in test_main.mnx have an
    # EMPTY NAME ("M\<acros...", "\<Error Logs"), so a name-keyed importer drops
    # them silently. That is R5's lesson arriving in a second format: a link must
    # not be inferred from a field that is allowed to be blank.
    opens = {}                      # container LEVELNAME.lower() -> opener record
    pending = None
    for r in rows:
        ot = (r['OBJTYPE'] or '').strip()
        if ot == '3' and (r['OBJCODE'] or '').strip() == '77':
            pending = r
        elif ot == '2':
            lvl = (r['LEVELNAME'] or '').strip().lower()
            if pending is not None and lvl != '_msysmenu':
                opens[lvl] = pending
                pending = None

    out = [{'RECKIND':'DOC','OBJID':'DOC1','PROVENANCE':'imported',
            'PROPS':uidef.props([('Version','1'),('Origin','vfp-mnx'),
                                 ('Kind','menu'),
                                 ('SourceFile', os.path.basename(mnx_path))])}]
    ids = {}; n = 0
    for r in conts:
        lvl=(r['LEVELNAME'] or '').strip().lower()
        n += 1; ids[lvl] = 'M%03d' % n
    # a container's own row becomes an OBJ; its items become its children
    findings=[]
    for r in conts:
        lvl=(r['LEVELNAME'] or '').strip()
        oid=ids[lvl.lower()]
        declared=(r['NUMITEMS'] or '').strip()
        actual=sum(1 for i in items if (i['LEVELNAME'] or '').strip().lower()==lvl.lower())
        if declared and declared.isdigit() and int(declared)!=actual:
            findings.append("container %s declares NUMITEMS=%s, observed %d children"
                            % (lvl, declared, actual))
        # a submenu's parent is the ITEM that opens it, not the document root
        opener = opens.get(lvl.lower())
        out.append({'RECKIND':'OBJ','OBJID':oid,
                    'PARENT':'','ORDINAL':n,
                    'KIND':'menu','FLOW':'column','PROVENANCE':'imported',
                    'PROPS':uidef.props([('Name', lvl), ('Container','.T.'),
                                         ('OpenedBy', (opener['NAME'] or '').strip()
                                                      if opener is not None else ''),
                                         ('OpenerPrompt', (opener['PROMPT'] or '').strip()
                                                      if opener is not None else ''),
                                         ('DeclaredItems', declared or '0')])})
    k=0
    for r in items:
        lvl=(r['LEVELNAME'] or '').strip().lower()
        pid=ids.get(lvl,'')
        k+=1; oid='I%03d'%k
        cap, mn, sep = caption(r['PROMPT'])
        pairs=[]
        if sep: pairs.append(('Separator','.T.'))
        else:
            pairs.append(('Caption','"%s"'%cap))
            if mn is not None: pairs.append(('Mnemonic', str(mn)))
        for col,key in (('KEYNAME','Key'),('KEYLABEL','KeyLabel'),
                        ('MESSAGE','Message'),('MARK','Mark'),('SKIPFOR','SkipFor')):
            v=(r[col] or '').strip()
            if v: pairs.append((key,'"%s"'%v))
        hs=[]
        cmd=(r['COMMAND'] or '').strip()
        proc=(r['PROCEDURE'] or '').strip()
        if cmd:  hs.append(('Click', '%s / ui' % cmd.split()[0][:40]))
        elif proc: hs.append(('Click', '%s / ui' % ((r['NAME'] or oid).strip() or oid)))
        out.append({'RECKIND':'OBJ','OBJID':oid,'PARENT':pid,
                    'ORDINAL':int((r['ITEMNUM'] or '0').strip() or 0),
                    'KIND':'menu','PROVENANCE':'imported',
                    'PROPS':uidef.props(pairs),'HANDLERS':uidef.props(hs)})
    # items now have OBJIDs; reparent each submenu container onto its opener item
    by_rec = {}
    k2 = 0
    for r in items:
        k2 += 1
        by_rec[id(r)] = 'I%03d' % k2
    linked = 0
    for rec in out:
        pr = rec.get('PROPS','')
        if 'Container = .T.' not in pr: continue
        lvl = None
        for line in pr.split('\r\n'):
            if line.startswith('Name = '): lvl = line[7:].strip()
        op = opens.get((lvl or '').lower())
        if op is not None and id(op) in by_rec:
            rec['PARENT'] = by_rec[id(op)]
            linked += 1
    findings.append("submenu containers linked to their opener item: %d of %d"
                    % (linked, max(0, len(conts)-1)))
    nrec,rlen,hlen = uidef.write(out_stem+'.DBF', out_stem+'.FPT', out)
    return out, findings, (nrec,rlen,hlen)

if __name__=='__main__':
    out,findings,(n,rl,hl)=convert(sys.argv[1], sys.argv[2])
    print("%s -> %s.DBF  records=%d rlen=%d hlen=%d" % (os.path.basename(sys.argv[1]),sys.argv[2],n,rl,hl))
    print("  NUMITEMS cross-check:", findings if findings else "every declared count matches")
    v=uidef.validate(out)
    print("  conformance findings:", v if v else "none")
    orig=[r for r in out if r.get('ORIGIN')]
    print("  rows carrying ORIGIN (R12.4 requires 0):", len(orig))
