DotScript staged set

This GitHub-facing copy keeps a small flat set of useful DotScript files.

Preferred runtime pattern:
- use `DO X64`, `DO CMDHELP`, or `DO METADATA` to switch lanes
- use `WORKSPACE LOAD <name>` for curated workspace files
- use `WORKSPACE OPEN DBF` or `WORKSPACE OPEN DBF CDX` for flat lane opens

Kept here:
- demo or smoke scripts
- helpful browser/workflow examples
- one-off maintenance scripts that are still useful to operators or developers

Removed from this staging copy:
- nested canary/case/suite scaffolding
- local regression sprawl
- historical subdirectory organization that is better kept in the dev tree

Current flat set:
- beta-0_shakedown.dts
- dottalkpp_non_destructive_smoke.dts
- ersatz_browser.dts
- ersatz_rel_enum_browser.dts
- pydottalk_shakedown.dts
- rebuild_stage_lmdb_snapshot_128m.dts
- rebuild_large_lmdb_envs_128m_20260621.dts
- stable_demo.dts
