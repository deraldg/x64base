# DD-006 Physical Dictionary Manifest Schema v0

Date: 2026-05-27  
Repo package examined: `ccode_homegrown_20260527-055727.zip`  
Repo package SHA-256: `6e19963fa1d975128bc14b39a3d4ca1262743f3c2563759873f6b63ea33f36b4`  
Mode: report-only schema design / no execution

## Purpose

DD-006 turns the DD-005 physical dictionary source map into a concrete manifest contract.

The goal is to define what DD-007 should emit before any catalog table, DBF, HELP, META, CMDHELPCHK, source, or runtime data mutation is considered.

DD-006 is still an organizing artifact. It does not harvest live runtime DBFs and does not execute DotTalk++.

## Design center

The first physical dictionary manifest is a JSON envelope with these object arrays:

```text
sources
  Common provenance spine.

tables
  Table identity, physical path, flavor, header/record/field counts.

fields
  Field identity, logical/descriptor name, type, width, decimals, ordinal, offset.

field_name_policy
  Long-name, truncation, mangling, and sanitized descriptor-token evidence.

table_verify
  Header/dialect/record-length/field-count verification rows.

memo_status
  Memo field, sidecar, backend attach, readback, and orphan-scan status.

indexes
  CDX/tag/order/backend status rows; LMDB remains backend evidence.

schemas
  Declared schema sidecar facts; declarations do not overwrite runtime proof.

workareas
  Runtime workspace/alias/selected-slot snapshots.

relations
  Parent/child relation state, aliases, expressions, active/valid flags.

rules
  Validation/business rule rows and resolved table/field bindings.

expressions
  xexpr parse/eval/reference evidence for rules, indexes, filters, relations.

import_profiles
  AUTODBF/import/export inference and mapping evidence.

runtime_proof
  Runtime transcript, command, script, or introspection proof rows.

warnings
  Extractor warnings and review queue entries.
```

## Required minimal manifest

A minimal manifest must contain:

```text
manifest header
sources[]
tables[]
fields[]
```

All other arrays may be empty in DD-007 source-scan mode, but the keys should still exist to keep the manifest stable.

## Trust rule

Physical runtime facts win over declared or inferred facts, but only after conflict review.

```text
runtime_proven
  strongest physical evidence

source_defined
  C++/registry/script source says this exists

declared
  schema/sidecar says this should exist

inferred
  import/AUTODBF/sample scan guesses this exists

generated_report
  report-only DD/MDO/SelfDoc evidence

ai_draft
  proposal only, not promotable without review/evidence
```

## Profile rule

The manifest carries a `profile` and every source row carries `profile_scope`.

```text
engine
  x64base physical engine facts only; no LabTalk/student/case/media requirement.

professional
  DotTalk++ neutral runtime; dictionary, HELP, commands, scripting, import/export.

educational
  optional LabTalk/student/case/media overlay.

dev
  developer diagnostics, SelfDoc, MDO, tests, review queues.
```

This preserves the architectural rule: x64base must build and operate without student artifacts, and DotTalk++ should be usable without visible student artifacts where practical.

## MetaFact alignment

DD-006 deliberately aligns with the existing `dt::meta::MetaFact` skeleton:

```text
MetaFactDomain::FieldDictionary
MetaFactDomain::RuntimeProof
MetaFactEvidenceKind::SourceCatalog
MetaFactEvidenceKind::SourceRegistry
MetaFactEvidenceKind::MetadataTable
MetaFactEvidenceKind::RuntimeTranscript
MetaFactEvidenceKind::GeneratedReport
```

DD-006 extends this contract at the manifest level rather than replacing it. Future C++ changes can either extend MetaFact domains/evidence kinds or map DD manifest rows into MetaFact rows.

## Files in this package

```text
physical_dictionary_manifest_v0.schema.json
  JSON Schema skeleton for the manifest envelope.

dd006_sample_manifest_minimal_v0.json
  Small valid-shaped example manifest.

dd006_manifest_objects_v0.csv
  Object-array definitions and promotion gates.

dd006_manifest_fields_v0.csv
  Field-by-field manifest contract.

dd006_evidence_kind_matrix_v0.csv
  Evidence kind to trust-level and MetaFact mapping.

dd006_trust_gates_v0.csv
  Promotion rules for runtime/source/declared/inferred/generated/AI evidence.

dd006_profile_scope_rules_v0.csv
  Engine/professional/educational/dev profile rules.
```

## Boundary

- No repo source files were changed.
- No CMake/build files were changed.
- No scripts were executed.
- No DotTalk++ runtime was launched.
- No DBF, CDX, LMDB, HELP, META, CMDHELPCHK, or catalog data was mutated.
- No generated dictionary rows were promoted to runtime metadata.

## Recommended next package

DD-007 should create a report-only Python 3.12 extractor skeleton that emits this manifest shape from source/package evidence only.

It should not yet open runtime DBFs, run DotTalk++, or write x64base catalog tables.
