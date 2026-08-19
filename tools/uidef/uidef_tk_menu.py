import subprocess, sys, time
sys.path.insert(0,'/tmp/gen')
import uidef_tk as U
import tkinter as tk

def build(path,out=None,w=700,h=260):
    doc,fonts,objs=U.load(path)
    dp=U.parse_props(doc['PROPS'])
    rec={}; pr={}
    for r in objs:
        oid=(r['OBJID'] or '').strip(); rec[oid]=r; pr[oid]=U.parse_props(r['PROPS'])
    kids={}
    for oid,r in rec.items():
        kids.setdefault((r['PARENT'] or '').strip(), []).append(oid)
    for k in kids: kids[k].sort(key=lambda o: int((rec[o]['ORDINAL'] or '0').strip() or 0))
    root=tk.Tk(); root.geometry("%dx%d"%(w,h)); root.title(dp.get('sourcefile','UIDEF menu'))
    stats={'cascade':0,'item':0,'sep':0}
    def is_container(oid): return pr[oid].get('container')=='.T.'
    def fill(menu, container_oid):
        for c in kids.get(container_oid,[]):
            p=pr[c]
            if p.get('separator')=='.T.':
                menu.add_separator(); stats['sep']+=1; continue
            sub=[k for k in kids.get(c,[]) if is_container(k)]
            lbl=p.get('caption','')
            und=int(p['mnemonic']) if 'mnemonic' in p else None
            if sub:
                m=tk.Menu(menu,tearoff=0); fill(m, sub[0])
                kw=dict(label=lbl,menu=m)
                if und is not None: kw['underline']=und
                menu.add_cascade(**kw); stats['cascade']+=1
            else:
                kw=dict(label=lbl,command=lambda: None)
                if p.get('key'): kw['accelerator']=p['key']
                if und is not None: kw['underline']=und
                menu.add_command(**kw); stats['item']+=1
    # the root container is the one with no opener
    roots=[o for o in rec if is_container(o) and not (rec[o]['PARENT'] or '').strip()]
    bar=tk.Menu(root)
    for rt in roots: fill(bar, rt)
    root.config(menu=bar)
    root.update_idletasks(); root.update(); time.sleep(0.5)
    if out:
        subprocess.run(["import","-window","root",out],check=False)
    print("  root containers=%d  top cascades=%d  items=%d  separators=%d" %
          (len(roots),stats['cascade'],stats['item'],stats['sep']))
    return root
if __name__=='__main__':
    o=sys.argv[2] if len(sys.argv)>2 else None
    r=build(sys.argv[1],o)
    if not o: r.mainloop()
