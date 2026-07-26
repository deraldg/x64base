# DD-015 Next Actions v0

## Immediate safe next step

Review the parser skeleton and marker contract:

1. `tools/dd015_transcript_parser.py`
2. `dd015_transcript_marker_contract_v0.csv`
3. `dd015_command_pattern_map_v0.csv`
4. `sample_output/dd015_sample_transcript_manifest_v0.json`

## Recommended local use later

1. Capture a DD-014 usage-only transcript first.
2. Prefer explicit `### DD015 CMD ...` / `### DD015 END` markers around each command block.
3. Run the parser against the captured transcript.
4. Review command block boundaries and hashes.
5. Only after review, derive `DD_TRANSCRIPT_RUN`, `DD_TRANSCRIPT_COMMAND`, and `DD_RUNTIME_PROOF` rows.

## Not authorized by DD-015

- No DotTalk++ runtime launch by this package.
- No source edits.
- No CMake/build-profile edits.
- No HELP DATA rebuild.
- No CMDHELPCHK execution.
- No catalog/DBF/CDX/LMDB mutation.
- No automatic promotion of parsed text into proven dictionary rows.

## Recommended DD-016

DD-016 should be a physical DBF/CDX/MEMO runtime proof plan. It should mirror the DD-014 transcript-proof pattern but focus on table header, field descriptor, memo backend attach/readback, CDX tag enumeration, and LMDB build-status evidence.
