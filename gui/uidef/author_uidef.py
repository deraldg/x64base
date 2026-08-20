#!/usr/bin/env python3
"""Author a UIDEF document by hand -- PROVENANCE = authored, never yet exercised.
Carries a `worker` handler with an ON_COMPLETE, to test R11 at runtime."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef
P=uidef.props
recs=[
 {'RECKIND':'DOC','OBJID':'DOC1','PROVENANCE':'authored',
  'PROPS':P([('Version','1'),('Origin','authored'),('Kind','form'),
             ('Title','"R11 dispatch test"')])},
 {'RECKIND':'FONT','OBJID':'FONT1','ORDINAL':1,'PROVENANCE':'authored',
  'PROPS':'Metrics = default\r\n'},
 # a form laid out by INTENT -- no ORIGIN at all. FLOW has never been exercised.
 {'RECKIND':'OBJ','OBJID':'F1','KIND':'form','FLOW':'column','ORDINAL':1,
  'PROVENANCE':'authored','PROPS':P([('Caption','"R11 dispatch test"')])},
 {'RECKIND':'OBJ','OBJID':'L1','PARENT':'F1','KIND':'label','ORDINAL':1,
  'PROVENANCE':'authored','PROPS':P([('Caption','"status: idle"')])},
 {'RECKIND':'OBJ','OBJID':'B1','PARENT':'F1','KIND':'button','ORDINAL':2,
  'PROVENANCE':'authored','PROPS':P([('Caption','"run on ui")')]),
  'HANDLERS':P([('Click','MarkUi / ui')])},
 {'RECKIND':'OBJ','OBJID':'B2','PARENT':'F1','KIND':'button','ORDINAL':3,
  'PROVENANCE':'authored','PROPS':P([('Caption','"run on worker"')]),
  'HANDLERS':P([('Click','SlowWork / worker -> WorkDone')])},
]
# fix a stray paren above
recs[4]['PROPS']=P([('Caption','"run on ui"')])
n,rl,hl=uidef.write('AUTHORED.DBF','AUTHORED.FPT',recs)
print("AUTHORED.DBF records=%d rlen=%d hlen=%d" % (n,rl,hl))
f=uidef.validate(recs); print("conformance:", f or "none")
