# Developer Manual Pointer Audit V1

- PASS: 21
- REVIEW: 1
- FAIL: 0
- active reader: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md`
- active reader SHA-256: `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95`

| Check | Status | Declared | Observed |
| --- | --- | --- | --- |
| ACTIVE_READER_POINTER_EXISTS | PASS | `file` | `True` |
| PRIMARY_READER_RECORD_EXISTS | PASS | `file` | `True` |
| ACTIVE_MANIFEST_POINTER_EXISTS | PASS | `file` | `True` |
| LEGACY_NAMED_ASSEMBLY_MANIFEST_EXISTS | PASS | `file` | `True` |
| SELECTED_ASSEMBLY_MANIFEST_EXISTS | PASS | `file` | `True` |
| ACTIVE_READER_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` | `True` |
| PRIMARY_READER_RECORD_TARGET_MATCH | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| PRIMARY_READER_RECORDED_HASH_CURRENT | PASS | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` |
| PRIMARY_READER_RECORDED_LINES_CURRENT | PASS | `3980` | `3980` |
| PRIMARY_READER_RECORDED_HEADINGS_CURRENT | PASS | `225` | `225` |
| ACTIVE_MANIFEST_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json` | `True` |
| CANONICAL_REFERENCE_MATCHES_ACTIVE_READER | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| CANONICAL_REFERENCE_RECORDED_HASH_CURRENT | PASS | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` |
| SELECTED_ASSEMBLY_WORKSPACE_EXISTS | PASS | `docs\manuals\developer\manualgen\published\developer_manual_publication_v1_media_section_v1` | `True` |
| SELECTED_ASSEMBLY_COMBINED_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | `True` |
| SELECTED_ASSEMBLY_AUTHORITY_NOT_CLAIMED | PASS | `role=selected_assembly_reference;publication_authority_claimed=0` | `role=selected_assembly_reference;publication_authority_claimed=0` |
| PRIMARY_READER_ROLE_INDEXED | PASS | `developer_manual_publication_v1/developer_manual_publication_v1.md` | `True` |
| SELECTED_ASSEMBLY_ROLE_INDEXED | PASS | `developer_manual_publication_v1_media_section_v1/` | `SUPPORTING` |
| SELECTED_ASSEMBLY_ROLE_SEPARATE_FROM_ACTIVE_READER | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |
| CONTROLLED_PUBLICATION_TARGET_EXISTS | PASS | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1_man_cli_reference_v1/developer_manual_publication_v1_media_section_v1.md` | `True` |
| CONTROLLED_PUBLICATION_RECORDED_HASH_CURRENT | PASS | `45706442FAA280A2BAB06C0E2FB01FC18525676C2052532A81F24D3D9FD8E8B2` | `45706442FAA280A2BAB06C0E2FB01FC18525676C2052532A81F24D3D9FD8E8B2` |
| CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER | REVIEW | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1_man_cli_reference_v1/developer_manual_publication_v1_media_section_v1.md` | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md` |

This audit is report-only. It does not promote a manifest, replace a publication, update a reader pointer, or mutate MAN* catalogs.
