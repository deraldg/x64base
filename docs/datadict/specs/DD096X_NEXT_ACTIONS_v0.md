# DD096X Next Actions

1. Install the drop-in package.
2. Generate the runtime DTS with --write-runtime-script.
3. Inspect generated schema tables/fields and the runtime DTS.
4. In DotTalk++, run:
   DO SANDBOX
   DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF
5. Capture runtime proof.
6. If green, proceed to DD096Y staged-row import into widened x64 proof schema.
