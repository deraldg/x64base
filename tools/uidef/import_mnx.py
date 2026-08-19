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

# R20: an OBJCODE 78 item names a capability the HOST provides. It has a NAME and
# never a COMMAND -- 21 of 21 in test_main.mnx. R20.1 named the gap this table
# closes: before it, those 21 items imported with an EMPTY HANDLERS and produced a
# menu whose Edit family silently did nothing. R7's empty box, at menu scale.
#
# R20.2: the vocabulary is the DSL's, not VFP's spelling. `_med_slcta` is not a
# portable identifier; `edit.select_all` is.
CAPABILITY = {
    '_med_undo':    'edit.undo',
    '_med_redo':    'edit.redo',
    '_med_cut':     'edit.cut',
    '_med_copy':    'edit.copy',
    '_med_paste':   'edit.paste',
    '_med_clear':   'edit.clear',
    '_med_slcta':   'edit.select_all',
    '_med_find':    'edit.find',
    '_med_finda':   'edit.find_again',
    '_med_repl':    'edit.replace',
    '_mpr_do':      'program.run',
    '_mpr_cancl':   'program.cancel',
    '_mpr_resum':   'program.resume',
    '_mpr_suspend': 'program.suspend',
    '_mpr_compl':   'program.compile',
    '_mtl_browser': 'tools.class_browser',
    '_mwi_arran':   'window.arrange',
    '_mwi_rotat':   'window.rotate',
}

# An unmapped host resource must NOT import as a plain item -- that is precisely
# the silent failure R20.1 names. It imports into the reserved `unmapped.`
# namespace instead, which no target can claim to provide, so R20's refuse-and-name
# rule fires automatically with no special case in the consumer.
UNMAPPED_NS = 'unmapped.'

# A mapping table is a place to make a quiet mistake, so it gets checked against
# the one independent witness in the record: the item's own caption. Every word of
# the caption must appear in the capability identifier, or the rename must be
# declared here on purpose. This is R13's RESERVED2 principle applied to a table I
# wrote myself -- a claim that can be checked should be checked.
#
# It earns its keep immediately: the first version of this table mapped
# `_mtl_browser` to `tools.data_browser` on the caption "Class Browser". The word
# `class` was missing and the check said so.
RENAMED = {
    'program.run':    'VFP spells it DO; `run` is the portable verb',
    'window.rotate':  'VFP spells it Cycle; `rotate` is what it does',
    'edit.find_again': 'caption "Find Again"; joined for identifier form',
    'edit.select_all': 'caption "Select All"; joined for identifier form',
}
STOP = {'', 'all', 'the', 'a', 'an'}


def caption_check(capname, cap_text):
    words = [w for w in ''.join(c.lower() if c.isalnum() else ' '
                                for c in (cap_text or '')).split()]
    ident = capname.replace('.', ' ').replace('_', ' ')
    missing = [w for w in words if w not in STOP and w not in ident.split()]
    if not missing:
        return None
    if capname in RENAMED:
        return None
    return missing

def capability(name):
    n = (name or '').strip().lower()
    if not n:
        return None, None
    if n in CAPABILITY:
        return CAPABILITY[n], None
    return UNMAPPED_NS + n.lstrip('_'), n

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
    mapped=[]; unmapped=[]; nameless=[]; silent=[]; hostsep=[]; mismatch=[]
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
        code=(r['OBJCODE'] or '').strip()
        if cmd:  hs.append(('Click', '%s / ui' % cmd.split()[0][:40]))
        elif proc: hs.append(('Click', '%s / ui' % ((r['NAME'] or oid).strip() or oid)))
        elif code == '78' and sep:
            # Measured: `_med_sp100/200/300` are named host resources AND separators.
            # A separator has no behaviour, so it takes no capability. Being a named
            # host resource is an identity, not a promise of a command.
            hostsep.append(oid)
        elif code == '78':
            capname, unknown = capability(r['NAME'])
            if capname:
                hs.append(('Click', '%s / host' % capname))
                if unknown: unmapped.append((oid, unknown, capname))
                else:
                    mapped.append((oid, capname))
                    miss = caption_check(capname, cap)
                    if miss: mismatch.append((oid, cap.strip(), capname, miss))
            else:
                # OBJCODE 78 with no NAME has never been observed. If it happens,
                # refuse loudly rather than emitting a dead item.
                nameless.append(oid)
        elif code == '77':
            pass          # R18: an opener's behaviour IS opening its submenu
        elif not sep and code:
            silent.append((oid, code, cap))
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
    # R20.1 accounting. Every item must leave here with a handler or a named
    # reason. An item with neither is the silent failure.
    findings.append("OBJCODE 78 -> host capability: %d mapped, %d unmapped, %d nameless, "
                    "%d named separators (no behaviour)"
                    % (len(mapped), len(unmapped), len(nameless), len(hostsep)))
    if unmapped:
        findings.append("unmapped host resources (target must refuse and name): "
                        + ", ".join("%s -> %s" % (u, c) for _, u, c in unmapped))
    if mismatch:
        findings.append("CAPTION MISMATCH -- capability may name the wrong thing: "
                        + "; ".join("%s %r -> %s (missing %s)"
                                   % (o, c, n, "/".join(m)) for o, c, n, m in mismatch))
    if nameless:
        findings.append("REFUSED: OBJCODE 78 with no NAME: " + ", ".join(nameless))
    if silent:
        findings.append("SILENT ITEMS -- no COMMAND, no PROCEDURE, not OBJCODE 78: "
                        + ", ".join("%s(code=%s,%r)" % t for t in silent))
    nrec,rlen,hlen = uidef.write(out_stem+'.DBF', out_stem+'.FPT', out)
    return out, findings, (nrec,rlen,hlen)

if __name__=='__main__':
    out,findings,(n,rl,hl)=convert(sys.argv[1], sys.argv[2])
    print("%s -> %s.DBF  records=%d rlen=%d hlen=%d" % (os.path.basename(sys.argv[1]),sys.argv[2],n,rl,hl))
    if findings:
        for f in findings:
            print("  " + f)
    else:
        print("  every declared count matches")
    v=uidef.validate(out)
    print("  conformance findings:", v if v else "none")
    orig=[r for r in out if r.get('ORIGIN')]
    print("  rows carrying ORIGIN (R12.4 requires 0):", len(orig))
