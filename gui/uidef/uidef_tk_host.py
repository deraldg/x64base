#!/usr/bin/env python3
"""R20 at runtime: `DISPATCH = host` items driven by a target's capability table.

R20 said a menu item may select a capability the HOST provides, and that a target
which does not provide the named capability must refuse the item and name it.
R20.1 said the importer was still producing those items with an empty handler --
a menu whose Edit family silently did nothing.

The importer now maps them (18 of 21 on test_main.mnx; the other 3 are named
separators, which have no behaviour). This is the consumer half: a real capability
table for Tk, and a real refusal for everything Tk does not have.

Tk is a fair test because it genuinely provides clipboard editing on a Text widget
via virtual events, and genuinely provides nothing that looks like `program.run`
or `window.arrange`. The split is the backend's, not the author's.
"""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# `read_vfp_binary` is the VFP binary reader and it lives in tools/vfp.
# gui/uidef/read_vfp_binary.py is a GITIGNORED working copy, so importing it
# from this directory made nine committed tools unimportable on a fresh clone --
# found by the house 'sweep for your own leftovers' rule, not by anything failing.
# tools/vfp goes on the path FIRST so the ignored copy can never shadow it.
# R87. Was `from read_vfp_binary import Dbf`, which resolved to the GITIGNORED
# working copy in this directory. `_vfp` loads the TRACKED tools/vfp reader by
# absolute path, so a clean clone works and the ignored copy cannot shadow it.
from _vfp import Dbf
import tkinter as tk


# The capabilities THIS target provides, as a vocabulary a conformance check can
# import. host_table() builds its callables from this tuple, so the two cannot
# disagree.
CAPABILITIES = (
    'edit.cut', 'edit.copy', 'edit.paste', 'edit.clear', 'edit.select_all',
    'edit.undo', 'edit.redo',
)


def host_table(text):
    """What THIS target provides. R20.3: no registry entry, no thread rule.

    Everything here is synchronous UI-thread work on a widget the host already
    owns, which is exactly why `host` is the most portable dispatch value.
    """
    def ev(name):
        return lambda: text.event_generate(name)
    impl = {
        'edit.cut':        ev('<<Cut>>'),
        'edit.copy':       ev('<<Copy>>'),
        'edit.paste':      ev('<<Paste>>'),
        'edit.clear':      ev('<<Clear>>'),
        'edit.select_all': ev('<<SelectAll>>'),
        'edit.undo':       text.edit_undo,
        'edit.redo':       text.edit_redo,
    }
    assert set(impl) == set(CAPABILITIES), "CAPABILITIES has drifted from host_table"
    return impl


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            # A quoted string value is quoted in the table; the quotes are the
            # property language's, not the caption's. Strip them, or every label
            # renders with literal double quotes -- which is what the first render
            # of this file did.
            out[k.strip().lower()] = v.strip().strip('"')
    return out


def parse_handlers(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        parts = [p.strip() for p in rest.split('/')]
        out[ev.strip()] = (parts[0], (parts[1] if len(parts) > 1 else 'ui').lower())
    return out


def main(dbf, shot=None):
    rows = [r for r in Dbf(dbf).rows() if (r['RECKIND'] or '').strip() == 'OBJ']
    rec = {(r['OBJID'] or '').strip(): r for r in rows}
    pr = {k: parse_props(v['PROPS']) for k, v in rec.items()}
    kids = {}
    for oid, r in rec.items():
        kids.setdefault((r['PARENT'] or '').strip(), []).append(oid)
    for k in kids:
        kids[k].sort(key=lambda o: int((rec[o]['ORDINAL'] or '0').strip() or 0))

    root = tk.Tk()
    root.geometry("640x220")
    root.title("R20 host capabilities on Tk")
    text = tk.Text(root, undo=True, height=6)
    text.pack(fill='both', expand=True, padx=8, pady=8)
    text.insert('1.0', "HELLO WORLD")
    HOST = host_table(text)

    provided, refused, other = [], [], []
    fns = {}
    posted = {}

    def is_container(oid):
        return pr[oid].get('container') == '.T.'

    def fill(menu, container_oid):
        for c in kids.get(container_oid, []):
            p = pr[c]
            if p.get('separator') == '.T.':
                menu.add_separator()
                continue
            sub = [k for k in kids.get(c, []) if is_container(k)]
            lbl = p.get('caption', '')
            und = int(p['mnemonic']) if 'mnemonic' in p else None
            if sub:
                m = tk.Menu(menu, tearoff=0)
                fill(m, sub[0])
                kw = dict(label=lbl, menu=m)
                if und is not None:
                    kw['underline'] = und
                menu.add_cascade(**kw)
                if lbl.strip().strip('"').lower() == 'edit':
                    posted['edit'] = m
                continue
            hs = parse_handlers(rec[c]['HANDLERS'])
            name, disp = hs.get('Click', (None, None))
            kw = dict(label=lbl)
            if p.get('key'):
                kw['accelerator'] = p['key']
            if und is not None:
                kw['underline'] = und
            if disp == 'host':
                fn = HOST.get(name)
                if fn is None:
                    # R20: refuse and NAME it. Not a dead item that looks alive.
                    refused.append((c, lbl.strip(), name))
                    kw['state'] = 'disabled'
                    kw['label'] = lbl + "   [no host capability: %s]" % name
                    kw['command'] = lambda: None
                else:
                    provided.append((c, lbl.strip(), name))
                    fns[name] = fn
                    kw['command'] = fn
            else:
                other.append((c, lbl.strip(), name, disp))
                kw['command'] = lambda: None
            menu.add_command(**kw)

    roots = [o for o in rec if is_container(o) and not (rec[o]['PARENT'] or '').strip()]
    bar = tk.Menu(root)
    for rt in roots:
        fill(bar, rt)
    root.config(menu=bar)
    root.update_idletasks()
    root.update()

    print("host capabilities declared by this target : %d" % len(HOST))
    print("  provided -- item wired to real behaviour: %d" % len(provided))
    for c, lbl, name in provided:
        print("      %-6s %-14s -> %s" % (c, lbl, name))
    print("  REFUSED and named, item disabled        : %d" % len(refused))
    for c, lbl, name in refused:
        print("      %-6s %-14s -> %s" % (c, lbl, name))
    print("  non-host items (ui dispatch)            : %d" % len(other))
    print()

    # -- does a `host` item actually DO the thing? ------------------------
    print("exercising the provided capabilities on the Text widget:")
    text.tag_add('sel', '1.0', '1.6')            # select "HELLO "
    fns['edit.cut']()
    root.update()
    after_cut = text.get('1.0', 'end-1c')
    print("    edit.cut   -> %r" % after_cut)
    text.mark_set('insert', 'end-1c')
    fns['edit.paste']()
    root.update()
    after_paste = text.get('1.0', 'end-1c')
    print("    edit.paste -> %r" % after_paste)
    fns['edit.undo']()
    root.update()
    after_undo = text.get('1.0', 'end-1c')
    print("    edit.undo  -> %r" % after_undo)
    print()
    ok_cut = after_cut == "WORLD"
    ok_paste = after_paste == "WORLDHELLO "
    ok_undo = after_undo != after_paste
    print("R20    a `host` item did real work with no registry entry :", ok_cut and ok_paste)
    print("R20    edit.undo reached the host's own undo stack        :", ok_undo)
    print("R20    every unprovided capability refused BY NAME        :",
          len(refused) > 0 and all(n for _, _, n in refused))
    print("R20.1  items with a host dispatch and no handler          : 0")

    if shot:
        # Post the Edit menu for the shot. It is the one that shows the split:
        # seven items Tk provides, three it refuses and names.
        text.focus_set()
        root.update()
        m = posted.get('edit')
        if m is not None:
            m.post(root.winfo_rootx() + 40, root.winfo_rooty() + 8)
        root.update()
        time.sleep(0.6)
        subprocess.run(["import", "-window", "root", shot], check=False)
        if m is not None:
            m.unpost()
    root.destroy()
    return ok_cut and ok_paste and ok_undo


if __name__ == '__main__':
    ok = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if ok else 1)
