# Developer Manual Pointer Audit V1

- PASS: 19
- REVIEW: 3
- FAIL: 0
- active reader: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md`
- active reader SHA-256: `EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F`

| Check | Status | Declared | Observed |
| --- | --- | --- | --- |
| ACTIVE_READER_POINTER_EXISTS | PASS | `file` | `True` |
| PRIMARY_READER_RECORD_EXISTS | PASS | `file` | `True` |
| ACTIVE_MANIFEST_POINTER_EXISTS | PASS | `file` | `True` |
| LEGACY_NAMED_ASSEMBLY_MANIFEST_EXISTS | PASS | `file` | `True` |
| SELECTED_ASSEMBLY_MANIFEST_EXISTS | PASS | `file` | `True` |
| ACTIVE_READER_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` | `True` |
| PRIMARY_READER_RECORD_TARGET_MATCH | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| PRIMARY_READER_RECORDED_HASH_CURRENT | PASS | `EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F` | `EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F` |
| PRIMARY_READER_RECORDED_LINES_CURRENT | PASS | `4118` | `4118` |
| PRIMARY_READER_RECORDED_HEADINGS_CURRENT | PASS | `237` | `237` |
| ACTIVE_MANIFEST_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json` | `True` |
| CANONICAL_REFERENCE_MATCHES_ACTIVE_READER | REVIEW | `D:\code\ccode\docs\manuals\developer\manualgen\published\developer_manual_publication_v1\developer_manual_publication_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| CANONICAL_REFERENCE_RECORDED_HASH_CURRENT | REVIEW | `EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F` | `` |
| SELECTED_ASSEMBLY_WORKSPACE_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1` | `True` |
| SELECTED_ASSEMBLY_COMBINED_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | `True` |
| SELECTED_ASSEMBLY_AUTHORITY_NOT_CLAIMED | PASS | `role=selected_assembly_reference;publication_authority_claimed=0` | `role=selected_assembly_reference;publication_authority_claimed=0` |
| PRIMARY_READER_ROLE_INDEXED | PASS | `developer_manual_publication_v1/developer_manual_publication_v1.md` | `True` |
| SELECTED_ASSEMBLY_ROLE_INDEXED | PASS | `developer_manual_publication_v1_media_section_v1/` | `SUPPORTING` |
| SELECTED_ASSEMBLY_ROLE_SEPARATE_FROM_ACTIVE_READER | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| CONTROLLED_PUBLICATION_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1_man_cli_reference_v1/developer_manual_publication_v1_media_section_v1.md` | `True` |
| CONTROLLED_PUBLICATION_RECORDED_HASH_CURRENT | PASS | `F45BCEB80C65D886D1A335830D1968B358972963FF357CD5DF7B7725AB12196B` | `F45BCEB80C65D886D1A335830D1968B358972963FF357CD5DF7B7725AB12196B` |
| CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER | REVIEW | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1_man_cli_reference_v1/developer_manual_publication_v1_media_section_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |

This audit is report-only. It does not promote a manifest, replace a publication, update a reader pointer, or mutate MAN* catalogs.
