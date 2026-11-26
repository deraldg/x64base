DotScript processing batch v2

This is a decomposition/sorting pass, not a semantic rewrite.
Categories:
- main: likely entry-point scripts
- suites: grouped functional runs
- cases: focused small tests
- canaries: smoke, shakedown, repro, unstable probes
- manual: interactive/manual scripts
- legacy: older backend-era or ambiguous scripts retained for mining

Use this as a staging package for further modernization.

Current rule:
- canonical runtime regressions should live in canaries, suites, or an explicit lane subfolder
- every regression .dts must set up its own environment first (for example DO X32 / DO VFP / DO X64 / DO SANDBOX / DO METADATA / DO MESSAGING)
- nested scripts below data/scripts should climb back to the data root when bootstrapping, for example DO ..\..\X64
- then open its own tables/workspaces/ersatz state explicitly
- tests, backup, tmp, and nested scripts/scripts are not authoritative long-term roots
