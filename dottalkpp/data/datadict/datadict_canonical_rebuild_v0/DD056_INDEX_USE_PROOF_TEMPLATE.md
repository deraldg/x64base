DD-056 LOCAL CATALOG INDEX USE / ORDER READBACK PROOF

Date: 2026-05-27
Run id: DD056-catalog-index-use-proof-prepare-v0
Repo: D:\code\ccode

Target:
  dottalkpp\data\metadata\datadict_canonical_rebuild_v0

Runtime command:
  DO D:\code\ccode\dottalkpp\data\metadata\datadict_canonical_rebuild_v0\dd056_index_use_order_readback.dts

Representative tag checks:
  - DDRUN.RUNID: PENDING
  - DDBASE.BASEID: PENDING
  - DDOBJECT.OBJID: PENDING
  - DDATTR.OBJID: PENDING
  - DDEDGE.FROMOBJ: PENDING
  - DDEDGE.TOOBJ: PENDING
  - DDGATE.STATUS: PENDING
  - DDPROFILE.NAME: PENDING

Expected evidence:
  For each representative table/tag:
    USE <table> succeeds.
    COUNT succeeds.
    SET ORDER TO <tag> succeeds, or the accepted DotTalk++ order syntax is documented.
    COUNT still succeeds under ordered path.
    GOTO 1 / TUP reads a record for non-empty tables.

Result:
  PENDING

Boundary:
  active datadict catalog not promoted
  HELP/META/CMDHELPCHK not mutated
  LMDB not built
  source not edited by DD-056
  no new CREATE/IMPORT performed by DD-056
