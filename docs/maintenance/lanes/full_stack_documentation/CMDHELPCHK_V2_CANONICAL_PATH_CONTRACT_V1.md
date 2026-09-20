# CMDHELPCHK v2 Canonical Path Contract V1

Status: active path/lineage contract  
Canonical scanner: `dottalkpp/tools/help/cmdhelpchk_v2_scan.py`  
Compatibility launcher: `tools/help/cmdhelpchk_v2_scan.py`

The runtime-root-aware scanner under `dottalkpp/tools/help` is canonical. It
supports separate runtime/source roots and emits the runtime-mediated metadata
evidence consumed by the Phase 2 bridge.

The older root-level implementation diverged before this contract. Its exact
pre-disposition content is preserved at
`tools/help/attic/cmdhelpchk_v2_scan_precanonical_20260716.py`. The old public
path is now a thin launcher for the canonical implementation.

Rules:

- make functional scanner changes only in the canonical file;
- keep the root-level path as a launcher while historical invocations depend on it;
- do not import functions from the compatibility launcher;
- report and candidate outputs remain non-authoritative evidence;
- scanner execution never authorizes HELP, metadata, DBF, CDX, or LMDB mutation;
- retirement of the compatibility path requires a separate reference scan.

This disposition preserves lineage and removes dual-current implementation
authority without deleting historical code.
