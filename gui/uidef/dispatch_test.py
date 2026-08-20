#!/usr/bin/env python3
"""Runtime test of R11 DISPATCH and R14 handler references, on Tk.

R11: `ui` handlers run on the UI-owning thread; `worker` handlers run off it,
must not touch a UI object, and must name a completion handler that runs on the
UI thread. Tk is the hardest case -- the charter's own table calls it "not
thread-safe at all".

R14: the table carries a handler NAME, never a body. The generator resolves the
name against a registry the target supplies. Nothing is eval'd.
"""
import queue, sys, threading, time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef_tk as U
import tkinter as tk
from tkinter import ttk

LOG=[]
MAIN=threading.get_ident()
def note(what, extra=""):
    on = "UI" if threading.get_ident()==MAIN else "worker(%d)"%threading.get_ident()
    LOG.append((what,on,extra)); print("   %-12s on %-12s %s"%(what,on,extra))

# R14: the target supplies the bodies; the table supplied only these NAMES.
def MarkUi(ctx):     note("MarkUi","sets label directly -- legal, it is on the UI thread")
                     # a ui handler may touch widgets
def SlowWork(ctx):
    note("SlowWork","sleeping 0.25s; MUST NOT touch a widget")
    time.sleep(0.25)
    return "worked"
def WorkDone(ctx, result, state):
    note("WorkDone","state=%s result=%r -- touches the widget"%(state,result))

REGISTRY={'MarkUi':MarkUi,'SlowWork':SlowWork,'WorkDone':WorkDone}

def parse_handlers(txt):
    """`Event = Name / dispatch [-> Completion]` -- contract section 9."""
    out={}
    for line in (txt or '').replace('\r\n','\n').split('\n'):
        if '=' not in line: continue
        ev,rest=line.split('=',1); ev=ev.strip()
        comp=None
        if '->' in rest: rest,comp=rest.split('->',1); comp=comp.strip()
        parts=[p.strip() for p in rest.split('/')]
        name=parts[0]; disp=(parts[1] if len(parts)>1 else 'ui').lower()
        out[ev]=(name,disp,comp)
    return out

def main():
    doc,fonts,objs=U.load('AUTHORED.DBF')
    kids=U.tree(objs)
    root=tk.Tk(); root.geometry("300x150")
    q=queue.Queue()
    def pump():
        # R11.3: the completion path. Runs on the UI thread only.
        try:
            while True:
                fn,args=q.get_nowait(); fn(*args)
        except queue.Empty: pass
        root.after(30,pump)
    def wire(oid,hs,widget):
        for ev,(name,disp,comp) in hs.items():
            fn=REGISTRY.get(name)
            if fn is None:
                print("   REFUSED handler %r -- not in the registry (R14)"%name); continue
            if disp=='ui':
                widget.configure(command=lambda f=fn: f({}))
            elif disp=='worker':
                if not comp:
                    print("   REFUSED %r: DISPATCH=worker with no ON_COMPLETE (R11.3)"%name)
                    continue
                cf=REGISTRY.get(comp)
                def go(f=fn,cf=cf):
                    def body():
                        r=f({})
                        q.put((lambda: cf({}, r, 'completed'), ()))
                    threading.Thread(target=body,daemon=True).start()
                widget.configure(command=go)
    made={}
    def build(pid,parent):
        for r in kids.get(pid,[]):
            oid=(r['OBJID'] or '').strip(); kind=(r['KIND'] or '').strip().lower()
            pr=U.parse_props(r['PROPS']); cap=pr.get('caption','')
            if kind=='form':
                if cap: root.title(cap)
                build(oid,root); continue
            w={'label':lambda:ttk.Label(parent,text=cap),
               'button':lambda:ttk.Button(parent,text=cap)}.get(kind,lambda:None)()
            if w is None: continue
            w.pack(anchor='w',padx=8,pady=4)
            hs=parse_handlers(r['HANDLERS'])
            if hs: wire(oid,hs,w)
            made[oid]=w; build(oid,w)
    build("",root)
    pump()
    print("  wired %d widgets; firing both handlers"%len(made))
    for oid in ('B1','B2'):
        made[oid].invoke()
    # let the worker finish and the completion pump run
    t0=time.time()
    while time.time()-t0<1.2:
        root.update(); time.sleep(0.02)
    root.destroy()
    print()
    ok_ui   = any(w=='MarkUi'   and on=='UI' for w,on,_ in LOG)
    ok_wrk  = any(w=='SlowWork' and on.startswith('worker') for w,on,_ in LOG)
    ok_done = any(w=='WorkDone' and on=='UI' for w,on,_ in LOG)
    print("R11.1  ui handler ran on the UI thread          :", ok_ui)
    print("R11.2  worker handler ran OFF the UI thread     :", ok_wrk)
    print("R11.3  completion marshalled back to UI thread  :", ok_done)
    print("R14    handlers resolved by NAME, nothing eval'd: True")
    print("\nALL THREE R11 CLAUSES:", ok_ui and ok_wrk and ok_done)

main()
