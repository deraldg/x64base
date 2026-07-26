# DD-001 Catalog Schema Sketch v0

This is a planning sketch, not an implementation authorization.

## Core physical catalog

```text
DD_TABLE
  table_id, canonical_name, display_name, table_kind, physical_path,
  table_flavor, record_count, header_length, record_length,
  memo_backend_status, index_backend_status, runtime_proven,
  source_id, visibility_profile, review_status

DD_FIELD
  field_id, table_id, field_name, canonical_name, display_name,
  type, width, decimals, ordinal, physical_offset,
  nullable, default_expr_id, validation_class, sensitive_class,
  source_id, runtime_proven, review_status

DD_INDEX
  index_id, table_id, tag_name, key_expr_id, filter_expr_id,
  unique_flag, primary_flag, backend_kind, source_id,
  runtime_proven, review_status

DD_MEMO_STATUS
  memo_id, table_id, field_id, sidecar_path, backend_attached,
  readback_verified, last_verified, source_id
```

## Declaration/provenance bridge

```text
DD_SOURCE
  source_id, source_kind, source_path, source_hash,
  source_line, source_block, harvest_run, evidence_kind,
  trust_level, review_status

DD_FACT
  fact_id, metafact_domain, evidence_kind, canonical_name,
  owner, source_id, evidence_value, runtime_proven,
  generated, curated, active
```

## Command/help/messaging bridge

```text
DD_COMMAND
  command_id, canonical_name, handler, category, status,
  public_surface, visibility_profile, mutability_class,
  risk_class, source_id

DD_USAGE_CONTRACT
  usage_id, command_id, usage_access, noargs_behavior,
  effect, mutates, scans_records, requires_open_table,
  notes, source_id

DD_HELP_LINK
  help_link_id, object_kind, object_id, help_topic,
  source_id, coverage_status

DD_MESSAGE
  message_id, canonical_name, severity, owner,
  message_text, source_id
```

## Runtime and maintenance scripts

```text
DD_SCRIPT
  script_id, script_path, script_kind, role, owner,
  required_for_profile, present_in_package, source_id,
  active, review_status

DD_SCRIPT_BOUNDARY
  script_id, boundary_class, may_read, may_write,
  may_mutate_runtime, may_mutate_help, may_mutate_metadata,
  may_mutate_source, requires_confirmation

DD_SCRIPT_RUN
  run_id, script_id, timestamp, operator, status,
  transcript_path, mutation_summary, savepoint_id

DD_SCRIPT_OBJECT
  script_id, object_kind, object_id, relation_kind
```

## Optional educational overlay

```text
DD_TEACHING_NOTE
DD_CASE_LINK
DD_LESSON_PATH
DD_STUDENT_EXAMPLE
DD_MEDIA_ANCHOR
```

These overlay tables must not be required by ENGINE profile.
