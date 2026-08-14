AUTOLOG 2026-05-11
Subsystem: pydottalk / non-memo proof suite

Files added:
  bindings/pydottalk_nonmemo_common.py
  bindings/pydottalk_cursor_matrix_sandbox.py
  bindings/pydottalk_fixed_field_type_matrix_sandbox.py
  bindings/pydottalk_append_update_delete_lifecycle_sandbox.py
  bindings/pydottalk_error_contract_sandbox.py
  bindings/pydottalk_x64_read_matrix.py
  bindings/run_pydottalk_nonmemo_proofs.ps1

Intent:
  Continue pydottalk hardening while memos are pinned.
  Expand proof coverage for cursor semantics, fixed-field mutation, append/update/delete lifecycle, error contracts, and x64 read behavior.

Behavior preserved:
  No semantic memo mutation.
  No FPT/DBT sidecar writes.
  No x64 memo payload writes.
  Mutation tests use scratch DBF copies.
  Read matrix uses pydottalk/DbArea runtime surface, not raw file scraping.
