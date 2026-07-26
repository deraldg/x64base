# DD-014 Next Actions v0

## Immediate safe next step

Run no runtime yet unless explicitly desired locally. First review:

1. `dd014_transcript_command_plan_v0.csv`
2. `dd014_mutation_boundary_matrix_v0.csv`
3. `dd014_workspace_relation_proof_template.dts`
4. `dd014_local_run_checklist_v0.csv`

## If local execution is authorized later

1. Copy `dd014_workspace_relation_proof_template.dts` to a local scratch run directory.
2. Keep only DD014B usage/report commands uncommented for the first run.
3. Capture transcript and hash it.
4. Review output markers.
5. Only then enable DD014C scratch workspace commands against a controlled non-production DBF root.
6. Preserve all transcripts and hashes before deriving manifest rows.

## Not authorized by DD-014

- No production data mutation.
- No HELP DATA rebuild.
- No CMDHELPCHK mutation.
- No metadata/catalog promotion.
- No source edits.
- No CMake/build-profile edits.
- No browser/edit-path proof.
- No TUPEXPORT filesystem-write proof.

## Recommended DD-015

DD-015 should be a physical DBF/CDX/MEMO runtime proof plan or a transcript parser skeleton, depending on whether local transcript evidence is available.
