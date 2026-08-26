# Manualgen controlled acceptance plan v1

Run: `DOCFLUSH-20260716-001`  
Candidate: `MANRUN-20260718T031554Z-F1F59445`  
State: `AUTHORIZED_APPLY_PASS`  
Publication authority currently claimed: `0`

## Purpose

Accept the reviewed eight-topic selective merge without treating a generated
candidate as authority, changing the active reader pointer, or losing a
verifiable before state. This plan defines a future guarded operation. It does
not authorize or perform that operation.

## Immutable inputs

The guarded operation must fail unless these inputs match exactly:

| Input | Required SHA-256 |
| --- | --- |
| Active primary reader | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` |
| Runtime Evidence base section | `264766287B11B86F4F1E3945267DDF13F181445AED5DEEECA30B531E1A3557B6` |
| Runtime Evidence accepted candidate | `80FDE98C8845DA47376A08129BA29FE36A1E750B62BBB15195D73C4DC5151926` |
| Command Surface base section | `C51E94ADF4BE95E1AFDC801A1D2545979D37C3AC044D7826B9E705AD4C55824F` |
| Command Surface accepted candidate | `28535CE3AA4C9592E17A6B7ADDBCE7615B805DC1CBF8AAFDD55228B032970182` |
| Partial HELP appendix candidate | `3846066EBC426877A03BD52C83E6CE4AAB9BAB8D61397D89CE93451EF015D568` |
| Selective-merge manifest | use its freshly observed hash and require internal status `PASS` |
| Context-review decision | use its freshly observed hash and require all eight topics approved |

The accepted pointer audit must also be green at 21 PASS, 1 intentional REVIEW,
and 0 FAIL immediately before apply.

## Future mutation set

Apply mode may change only these canonical surfaces:

1. `published/developer_manual_publication_v1/sections/sections/runtime_evidence_source_verification_and_canary_closure.md`;
2. `published/developer_manual_publication_v1/sections/sections/command_surface_dispatch_and_entry_variants.md`;
3. new `published/developer_manual_publication_v1/appendices/partial_help_reference.md`;
4. `published/developer_manual_publication_v1/developer_manual_publication_v1_appendices.md`;
5. `published/developer_manual_publication_v1/developer_manual_publication_v1.md`;
6. `accepted_artifacts/primary_reader_artifact_v1.json`;
7. `accepted_manifests/developer_manual_canonical_manifest_v1.json`;
8. a new append-only appendix acceptance record superseding the three-item
   inventory in `MDO-215_ACCEPTED_APPENDIX_MANIFEST_v1.md` without rewriting
   that historical manifest;
9. the publication workspace `README.md` only if needed to describe the newly
   accepted appendix role.

No active pointer, MAN* catalog, HELP/META table, source file, `C:\x64base`
staging file, website file, commit, push, or deployment is in this mutation set.

## Required guarded command

Manualgen now provides `build-controlled-acceptance-plan`. Its implemented
mode is deliberately report-only:

- current `plan`/dry-run: validate hashes, compute the exact output set,
  emit diffs/manifests, and write only beneath a generated run directory;
- future `--apply --authorization-record <path>`: require a durable maintainer
  authorization record, recheck every precondition, create the backup set, and
  replace only the allow-listed files.

The command must reject implicit workspace selection, candidate-only status
headers in canonical output, deletions in either section, duplicate headings,
missing anchors, unexpected files, stale inputs, or a non-green pointer audit.

## Assembly rule

Do not copy `developer_manual_selective_merge_candidate.md` verbatim: it
contains a candidate-only header. Rebuild deterministically from the verified
active reader and the three accepted merge products, or from the accepted
section order plus appendix inventory. The resulting reader must:

- contain the two reviewed section additions exactly once;
- append `partial_help_reference.md` exactly once with an explicit partial and
  legacy authority label;
- omit all candidate-only banner comments;
- preserve every unrelated byte/section semantically and introduce zero
  unreviewed deletions;
- agree with the rebuilt section and appendix files.

## Backup and rollback

Before apply, create a timestamped run directory containing byte-preserved
copies of every existing allow-listed file, a `before_manifest.json` with
SHA-256/size/line/heading data, the absent/present state of the new appendix,
and a generated rollback command. After apply, emit the corresponding
`after_manifest.json`. Rollback must be possible without Git and must remove the
new appendix only when the before manifest proves it was absent.

## Validation gates

Apply succeeds only if all checks pass:

1. exact input and authorization hashes;
2. two section diffs are additive only: 33 and 22 additions, 0 deletions;
3. all eight reviewed topic identities appear once in their accepted surface;
4. appendix aggregate and reader inventory agree;
5. reader has no candidate-only banner and no duplicate new headings;
6. accepted reader evidence is regenerated from observed output, including
   hash, line count, and heading count;
7. canonical reference hash equals the observed rebuilt reader hash;
8. pointer audit has 0 FAIL and only the documented role-split REVIEW;
9. Manualgen and full-stack documentation suites pass;
10. a contextual diff confirms no unrelated manual change.

On any failure, restore from the before set, emit a failed execution record,
and leave the reader pointer unchanged.

## Authorization boundary

Implementing and exercising dry-run mode is report-only work. Running apply
mode changes protected accepted documentation and therefore requires a new,
explicit maintainer authorization naming this plan and the generated dry-run
package.

## Dry-run execution result

The first plan run, `MANRUN-20260718T031402Z-B472B856`, failed closed because
the original selective-merge writer trimmed two and one trailing blank lines
from its written section candidates after calculating zero-deletion diffs. A
second diagnostic run, `MANRUN-20260718T031643Z-2AAEB361`, retained the failure
while the planner's own reconstruction normalization was removed.

The selective-merge writer now preserves the canonical EOF bytes. Regenerated
run `MANRUN-20260718T031554Z-F1F59445` has the same approved prose, byte-identical
appendix and contextual reader, 55 section additions, and zero deletions.

Passing plan-only run: `MANRUN-20260718T031714Z-1A3F1333`.

- planned mutation rows: 8;
- reviewed topics: 8;
- validation findings: 0;
- apply available: 0;
- canonical files mutated: 0;
- planned reader SHA-256:
  `7437C555BA108DF56A9DE30556239945873072653900C26D2D85A2EBF21D6C0E`;
- planned reader: 4,082 lines, 237 headings, no candidate-only banner.

The package was reviewed and separately authorized through
`CANONICAL_APPLY_AUTHORIZATION_2026-07-18.md`.

## Authorized apply result

Apply run `MANRUN-20260718T032528Z-F8C6EB67` completed all eight rows with zero
findings and zero rollback findings. The byte-preserved before set, staged
after set, execution manifest, and guarded Python 3.12 rollback command are in:

`docs/manuals/developer/manualgen/backups/docflush_controlled_acceptance_MANRUN-20260718T032528Z-F8C6EB67/`

Post-apply verification:

- Runtime Evidence: 33 additions, 0 deletions;
- Command Surface: 22 additions, 0 deletions;
- primary reader: 102 publication additions, 0 deletions;
- active reader: 4,082 lines, 237 headings, SHA-256
  `7437C555BA108DF56A9DE30556239945873072653900C26D2D85A2EBF21D6C0E`;
- Partial HELP appears exactly once in the reader, appendix aggregate, and
  standalone appendix;
- candidate-only banner count: 0;
- pointer audit: 21 PASS, 1 intentional role-split REVIEW, 0 FAIL;
- all eight current hashes match the post-apply manifest;
- 14 full-stack and 35 Manualgen tests pass under Python 3.12.9.

One accepted-record wording canary was corrected after apply: the finalized
appendix record no longer carries its obsolete preview instruction. Before and
after hashes plus the complete current eight-row state are retained in
`post_apply_current_manifest.json`. Manual content and authority were unchanged
by that wording correction.
