#!/usr/bin/env python3
"""Maintenance UI for the AI-Portal tracking system (AIF-086).

A small local web console over tools/dbf/crud.py for the tracking tables
(SYSLANE / SYSRUN / SYSRUNLANE / SYSPROOF / SYSTASK) and, read-only, every other
SYS* table. It is a maintenance surface, not a public report:

  READ  is the pure DBF path (crud.read_rows) -- no engine, works anywhere.
  WRITE reuses crud's CRUD with posture-A semantics:
        - soft-close by default, --purge (tombstone) behind an explicit confirm,
        - bbs tables write-guarded, append-only refused, crosswalk rules enforced,
        - two modes: EXECUTE (through pydottalk) or EMIT (return the DotScript /
          fsram dry run so you can feed it via datarun yourself).

Loopback only. Single-writer (pydottalk takes no lock). Run:

    python tools/dbf/maint_server.py            # http://127.0.0.1:8770
    python tools/dbf/maint_server.py --port 8771

The EMIT mode needs no engine and works in any environment; EXECUTE needs a
pydottalk built with xbase (see the capability review).
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_registry as reg   # noqa: E402
import crud                     # noqa: E402


# ---- JSON API helpers ---------------------------------------------------------
def _tables_payload() -> dict:
    out = []
    for name in sorted(reg.TABLES):
        s = reg.TABLES[name]
        out.append({"name": name, "subdir": s.subdir, "writable": s.writable,
                    "close": s.close.kind, "append_only": s.append_only,
                    "pk": s.pk, "key": s.key, "ckey": list(s.ckey)})
    return {"tables": out}


def _table_payload(name: str, include_deleted: bool) -> dict:
    spec = reg.get(name)
    rows = crud.read_rows(name, include_deleted=include_deleted)
    live = [crud.is_live(spec, r) for r in rows]
    return {
        "name": spec.name, "subdir": spec.subdir, "writable": spec.writable,
        "append_only": spec.append_only, "close": spec.close.kind,
        "pk": spec.pk, "key": spec.key, "ckey": list(spec.ckey),
        "columns": list(spec.field_names()),
        "rows": [{"_live": lv, **r} for r, lv in zip(rows, live)],
        "count": len(rows), "live": sum(live),
    }


def _do_op(body: dict) -> dict:
    """Dispatch a write. mode: 'execute' | 'dts' | 'ram'."""
    cmd = body.get("op")
    table = body.get("table", "")
    spec = reg.get(table)
    values = body.get("set", {}) or {}
    key = body.get("key")
    where = body.get("where", {}) or {}
    purge = bool(body.get("purge"))
    mode = body.get("mode", "execute")

    if cmd not in ("create", "update", "delete"):
        raise crud.CrudError(f"unknown op: {cmd}")

    if mode in ("dts", "ram"):
        fn = crud.emit_ram if mode == "ram" else crud.emit_dts
        lines = fn(cmd, spec, values, key, where, purge, bool(body.get("indexed")))
        return {"ok": True, "mode": mode, "dotscript": "\n".join(lines)}

    # EXECUTE via pydottalk. Refuse a write that cannot land BEFORE opening the engine
    # (bbs guard / append-only update), so we never spin up the lock-less writer for it.
    crud._require_writable(spec)
    if cmd == "update" and spec.append_only:
        raise crud.CrudError(f"{spec.name} is append-only: update-in-place is refused; "
                             f"create a superseding row instead.")
    area = crud._open_real_area(spec)
    try:
        if cmd == "create":
            res = crud.op_create(area, spec, values)
        elif cmd == "update":
            res = crud.op_update(area, spec, key, where, values)
        else:  # delete
            res = crud.op_purge(area, spec, key, where) if purge \
                else crud.op_soft_close(area, spec, key, where)
        return {"ok": True, "mode": "execute", "result": res}
    finally:
        area.close()


# ---- HTTP handler -------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, obj=None, html=None):
        self.send_response(code)
        if html is not None:
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = html.encode("utf-8")
        else:
            self.send_header("Content-Type", "application/json")
            body = json.dumps(obj).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                return self._send(200, html=PAGE)
            if u.path == "/api/tables":
                return self._send(200, _tables_payload())
            if u.path.startswith("/api/table/"):
                name = u.path.rsplit("/", 1)[-1]
                inc = parse_qs(u.query).get("deleted", ["0"])[0] == "1"
                return self._send(200, _table_payload(name, inc))
            return self._send(404, {"error": "not found"})
        except (crud.CrudError, KeyError) as exc:
            return self._send(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return self._send(500, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if self.path != "/api/op":
                return self._send(404, {"error": "not found"})
            return self._send(200, _do_op(body))
        except (crud.CrudError, KeyError) as exc:
            return self._send(400, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})


PAGE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tracking Maintenance</title><style>
:root{--bg:#0f1419;--panel:#171e26;--line:#26323f;--tx:#dfe7ef;--dim:#8ba0b4;--acc:#5cc8ff;
--ok:#4ec9a0;--warn:#e8b84b;--bad:#e86a6a;--mono:ui-monospace,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;display:flex;height:100vh}
#side{width:210px;background:var(--panel);border-right:1px solid var(--line);padding:12px;overflow:auto}
#side h1{font-size:14px;margin:0 0 10px;color:var(--acc)}
.tbtn{display:block;width:100%;text-align:left;background:none;border:1px solid var(--line);
color:var(--tx);padding:6px 8px;border-radius:6px;margin:3px 0;cursor:pointer;font-family:var(--mono);font-size:12px}
.tbtn:hover{border-color:var(--acc)}.tbtn.on{background:#1d262f;border-color:var(--acc)}
.tbtn .ro{color:var(--warn);font-size:10px}.tbtn .rw{color:var(--ok);font-size:10px}
#main{flex:1;padding:16px;overflow:auto}
.bar{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.bar h2{margin:0;font-size:17px}.pill{font-family:var(--mono);font-size:11px;border:1px solid var(--line);
border-radius:10px;padding:1px 8px;color:var(--dim)}.pill.ok{color:var(--ok)}.pill.warn{color:var(--warn)}
button.act{background:#1d262f;border:1px solid var(--line);color:var(--tx);border-radius:6px;padding:5px 10px;cursor:pointer}
button.act:hover{border-color:var(--acc)}button.act:disabled{opacity:.4;cursor:not-allowed}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}
th{position:sticky;top:0;background:var(--bg);text-align:left;color:var(--dim);font-size:11px;
text-transform:uppercase;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:5px 8px;border-bottom:1px solid #1e2731;font-family:var(--mono);max-width:220px;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr.closed td{color:var(--dim)}tr:hover td{background:#141c24}
.rowbtns{display:flex;gap:4px}.mini{font-size:11px;padding:2px 6px}
#panel{position:fixed;right:0;top:0;height:100vh;width:380px;background:var(--panel);
border-left:1px solid var(--line);padding:16px;overflow:auto;transform:translateX(100%);transition:.15s}
#panel.open{transform:none}#panel h3{margin:0 0 10px;font-size:15px}
label{display:block;font-size:11px;color:var(--dim);margin:8px 0 2px;font-family:var(--mono)}
input,select{width:100%;background:var(--bg);border:1px solid var(--line);color:var(--tx);
border-radius:5px;padding:5px 7px;font-family:var(--mono);font-size:12px}
.note{font-size:11px;color:var(--dim);margin:8px 0}.err{color:var(--bad)}
pre{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:10px;
font-size:11.5px;white-space:pre-wrap;color:var(--ok);max-height:40vh;overflow:auto}
.close{float:right;cursor:pointer;color:var(--dim)}
</style></head><body>
<div id="side"><h1>Tracking tables</h1><div id="tables"></div>
<div class="note">read = pure DBF (no engine)<br>write = pydottalk / emit</div></div>
<div id="main"><div class="bar"><h2 id="ttl">Select a table</h2>
<span id="meta"></span>
<label style="margin:0"><input type="checkbox" id="del" style="width:auto"> show deleted</label>
<button class="act" id="new" style="display:none">+ New row</button>
<button class="act" id="refresh">Refresh</button></div>
<div id="grid"></div></div>
<div id="panel"><span class="close" onclick="closePanel()">x close</span>
<h3 id="pttl">Edit</h3><div id="form"></div>
<label>Mode</label><select id="mode">
<option value="execute">Execute (pydottalk)</option>
<option value="dts">Emit DotScript</option>
<option value="ram">Emit fsram dry run</option></select>
<div style="margin-top:12px"><button class="act" id="save">Save</button></div>
<div id="pmsg" class="note"></div><pre id="pout" style="display:none"></pre></div>
<script>
let cur=null, spec=null, editRow=null;
const $=s=>document.querySelector(s);
async function jget(u){const r=await fetch(u);const j=await r.json();if(!r.ok)throw new Error(j.error||r.status);return j}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return await r.json()}
async function loadTables(){const j=await jget('/api/tables');const box=$('#tables');box.innerHTML='';
 j.tables.forEach(t=>{const b=document.createElement('button');b.className='tbtn';
  b.innerHTML=`${t.name} <span class="${t.writable?'rw':'ro'}">${t.writable?'rw':'RO'}</span>`;
  b.onclick=()=>selTable(t.name,b);box.appendChild(b)})}
async function selTable(name,btn){document.querySelectorAll('.tbtn').forEach(x=>x.classList.remove('on'));
 if(btn)btn.classList.add('on');cur=name;await load()}
async function load(){if(!cur)return;const inc=$('#del').checked?'?deleted=1':'';
 const j=await jget('/api/table/'+cur+inc);spec=j;
 $('#ttl').textContent=cur;
 $('#meta').innerHTML=`<span class="pill">${j.subdir}</span> <span class="pill ${j.writable?'ok':'warn'}">${j.writable?'writable':'read-only'}</span> <span class="pill">close: ${j.close}</span>${j.append_only?' <span class="pill warn">append-only</span>':''} <span class="pill">${j.live}/${j.count} live</span>`;
 $('#new').style.display=j.writable?'':'none';
 let h='<table><tr>'+j.columns.map(c=>`<th>${c}</th>`).join('')+'<th></th></tr>';
 j.rows.forEach((r,i)=>{h+=`<tr class="${r._live?'':'closed'}">`+j.columns.map(c=>`<td title="${esc(r[c])}">${esc(r[c])}</td>`).join('');
  h+='<td class="rowbtns">';
  if(j.writable){h+=`<button class="act mini" onclick="edit(${i})">edit</button>`;
   if(j.close!=='crosswalk'&&!j.append_only)h+=`<button class="act mini" onclick="close_(${i})">close</button>`;
   h+=`<button class="act mini" onclick="purge(${i})">purge</button>`}
  h+='</td></tr>'});
 h+='</table>';$('#grid').innerHTML=h}
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function keyOf(r){if(spec.ckey.length)return null; return r[spec.key||spec.pk]}
function openPanel(title){$('#pttl').textContent=title;$('#panel').classList.add('open');$('#pmsg').textContent='';$('#pout').style.display='none'}
function closePanel(){$('#panel').classList.remove('open')}
function fieldForm(r){return spec.columns.map(c=>`<label>${c}</label><input id="f_${c}" value="${esc(r?r[c]:'')}">`).join('')}
function edit(i){editRow={mode:'update',row:spec.rows[i]};openPanel('Edit '+cur);
 $('#form').innerHTML=fieldForm(spec.rows[i])}
function newRow(){editRow={mode:'create',row:null};openPanel('New '+cur);$('#form').innerHTML=fieldForm(null)}
function close_(i){editRow={mode:'close',row:spec.rows[i]};openPanel('Soft-close '+cur);
 $('#form').innerHTML='<div class="note">Applies the close policy ('+spec.close+'). Reversible.</div>'}
function purge(i){editRow={mode:'purge',row:spec.rows[i]};openPanel('PURGE '+cur);
 $('#form').innerHTML='<div class="note err">Tombstone (xBase deleted flag). IRREVERSIBLE via pydottalk; not space-reclaiming. Confirm by Save.</div>'}
$('#save').onclick=async()=>{if(!editRow)return;const m=$('#mode').value;const r=editRow.row;
 let body={table:cur,mode:m};
 const sel=()=>{if(spec.ckey.length){body.where={};spec.ckey.forEach(k=>body.where[k]=r[k])}else{body.key=r[spec.key||spec.pk]}};
 if(editRow.mode==='create'){body.op='create';body.set=collect()}
 else if(editRow.mode==='update'){body.op='update';sel();body.set=collect(r)}
 else if(editRow.mode==='close'){body.op='delete';sel()}
 else if(editRow.mode==='purge'){body.op='delete';body.purge=true;sel()}
 const j=await jpost('/api/op',body);
 if(j.dotscript){$('#pout').style.display='';$('#pout').textContent=j.dotscript;$('#pmsg').textContent='Emitted (feed via datarun).'}
 else if(j.ok){$('#pmsg').textContent='OK: '+JSON.stringify(j.result);await load();setTimeout(closePanel,700)}
 else{$('#pmsg').innerHTML='<span class="err">'+esc(j.error)+'</span>'}}
function collect(orig){const o={};spec.columns.forEach(c=>{const el=$('#f_'+c);if(!el)return;
 const v=el.value;if(orig){if(v!==String(orig[c]||''))o[c]=v}else if(v!=='')o[c]=v});return o}
$('#refresh').onclick=load;$('#del').onchange=load;$('#new').onclick=newRow;
loadTables();
</script></body></html>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tracking maintenance UI")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"tracking maintenance UI: http://{a.host}:{a.port}  (loopback only, Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
