# DD-015 Transcript Parser Skeleton v0

## Status

Report-only package. No DotTalk++ runtime was launched and no repository/catalog files were mutated.

## Purpose

DD-014 defined a guarded workspace/relation/tuple transcript proof plan. DD-015 adds the first parser skeleton for turning future controlled transcripts into structured, review-required runtime-proof evidence.

The parser does not decide that a behavior is proven. It only extracts command blocks, hashes outputs, maps commands back to DD-014 plan rows when possible, and emits a manifest for review.

## Inputs

- Future captured DotTalk++ transcript text files.
- Optional `dd014_transcript_command_plan_v0.csv` for command-to-catalog target matching.

## Outputs

- Transcript parse manifest JSON.
- Command block rows suitable for review.
- Output-block hashes for provenance.
- Warning markers and unmatched-command diagnostics.

## Sample parser run

The included sample transcript was parsed successfully.

| Metric | Count |
|---|---:|
| Plan rows loaded | 24 |
| Command blocks parsed | 6 |
| Blocks matched to DD-014 plan | 6 |
| Blocks with warning markers | 0 |
| Unique command tokens | 6 |

## Parser support

The parser supports two styles:

```text
### DD015 CMD seq=1 phase=DD014B command="WORKSPACE USAGE"
... command output ...
### DD015 END
```

and prompt-style fallback:

```text
. WORKSPACE USAGE
... command output ...
dottalk> RELATIONS ALL
... command output ...
```

Explicit DD015 markers are preferred because they reduce ambiguity.

## Catalog bridge

DD-015 prepares evidence for these catalog families:

- `DD_TRANSCRIPT_RUN`
- `DD_TRANSCRIPT_COMMAND`
- `DD_RUNTIME_PROOF`
- `DD_REVIEW_QUEUE`
- `DD_WORKSPACE_SNAPSHOT`
- `DD_WORKAREA`
- `DD_REL_VERIFY`
- `DD_TUPLE_VERIFY`

## Trust boundary

Parsed transcript text is not automatically runtime proof. Promotion requires:

1. original transcript hash preserved,
2. command block boundaries reviewed,
3. command outputs reviewed against expected evidence markers,
4. warning markers triaged,
5. data root confirmed as controlled/non-production where applicable,
6. separate authorization before DBF/catalog import.

## Files

- `tools/dd015_transcript_parser.py`
- `sample_inputs/dd015_usage_only_sample_transcript.txt`
- `sample_output/dd015_sample_transcript_manifest_v0.json`
- `sample_output/dd015_sample_command_blocks_v0.csv`
- `dd015_parser_module_map_v0.csv`
- `dd015_transcript_marker_contract_v0.csv`
- `dd015_command_pattern_map_v0.csv`
- `dd015_manifest_projection_v0.csv`
- `dd015_trust_gates_v0.csv`
- `DD015_NEXT_ACTIONS_v0.md`
- `DD015_AUTOLOG_v0.md`
