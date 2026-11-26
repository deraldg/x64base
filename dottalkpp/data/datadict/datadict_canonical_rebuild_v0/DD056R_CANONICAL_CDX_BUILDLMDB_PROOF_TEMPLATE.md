DD-056R LOCAL CANONICAL CDX / ADDTAG / INFO / BUILDLMDB STAGING PROOF

Date: 2026-05-27
Run id: DD056R-canonical-cdx-buildlmdb-prepare-v0
Repo: D:\code\ccode

Target:
  dottalkpp\data\metadata\datadict_canonical_rebuild_v0

Runtime command:
  DO D:\code\ccode\dottalkpp\data\metadata\datadict_canonical_rebuild_v0\dd056r_canonical_cdx_buildlmdb_staging.dts

Canonical workflow:
  CDX CREATE
  CDX ADDTAG <tag>
  CDX INFO
  CDX TAGS
  BUILDLMDB CLEAN YES
  SET INDEX TO <table>
  SET ORDER TO TAG <tag>
  LIST

Per-table proof:
  - DDRUN: CDX CREATE / ADDTAG 3 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDBASE: CDX CREATE / ADDTAG 3 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDSOURCE: CDX CREATE / ADDTAG 3 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDOBJECT: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDATTR: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDEDGE: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDEVID: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDGATE: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDREVIEW: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDARTIF: CDX CREATE / ADDTAG 4 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING
  - DDPROFILE: CDX CREATE / ADDTAG 3 / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING

Representative indexed-read proof:
  - DDRUN.RUNID: PENDING
  - DDBASE.BASEID: PENDING
  - DDOBJECT.OBJID: PENDING
  - DDATTR.OBJID: PENDING
  - DDEDGE.FROMOBJ: PENDING
  - DDEDGE.TOOBJ: PENDING
  - DDGATE.STATUS: PENDING
  - DDPROFILE.NAME: PENDING

Expected evidence:
  CDX INFO and/or CDX TAGS shows created tags.
  BUILDLMDB reports LMDB environment creation/rebuild.
  SET INDEX TO <table> attaches <table>.cdx.
  SET ORDER TO TAG <tag> selects tag.
  LIST output reports MODE LMDB and the active tag.

Result:
  PENDING

Boundary:
  active datadict catalog not promoted
  HELP/META/CMDHELPCHK not mutated
  source not edited by DD-056R
  no CREATE X64 / IMPORT performed by DD-056R
