# SelfDoc Web Diagnostic Feedback Policy v0

Status: POLICY / META
Safety class: REPORT_ONLY / REVIEW_BEFORE_MUTATION
Date: 2026-07-09

## Purpose

This policy records a high-level SelfDoc rule: when x64base.com exposes a
runtime, capacity, command, or documentation inconsistency, the finding is not
just a website defect. It is a diagnostic that has crossed from source/runtime
evidence into the public documentation layer.

The correct response is to preserve the signal, name the affected vector, and
route the correction back through source, proof, manual, and website lanes.

## Origin

The x64 capacity/math section produced early evidence of this feedback loop.
The generated feed exposed an `_int16` boundary problem, which was repaired in
the source/runtime lane after it became visible at the website layer.

On July 8-9, 2026, the same lane surfaced an arbitrary record-length
inconsistency. That inconsistency was intentionally left alone temporarily as
runtime proof and as evidence that diagnostics can reach the web level.

## Core Rule

```text
Website diagnostics are first-class SelfDoc findings.
```

Do not treat them as simple copy fixes when they concern source behavior,
limits, field widths, record widths, indexes, memo storage, command behavior,
or generated claims.

## Vector Promotion

Every web-level diagnostic should be promoted into a named vector before the
public claim is corrected.

Initial vector families:

```text
max_areas
max_record_length
max_field_length
max_fields
max_records
max_table_name
max_field_name
memo_object_id_width
index_key_length
header_mirror_width
x64_extension_width
```

Additional vectors should be added when a recurring diagnostic has a stable
name, a source location, and a manual or website target.

## Required Fields

Where practical, each vector record should preserve:

```text
vector_name
source_evidence
runtime_evidence
generated_claim
public_claim
observed_inconsistency
canary_or_transcript
proof_status
fix_status
manual_target
website_target
review_status
```

## Promotion Path

```text
web diagnostic
  -> named vector
  -> source/runtime proof
  -> SelfDoc/MDO/manualgen note
  -> reviewed manual update
  -> reviewed website update
```

This path keeps x64base.com from becoming an isolated truth source while still
allowing the website to act as a valuable diagnostic surface.

## Non-Mutation Rule

This policy does not authorize source edits, generated-file rewrites, manual
replacement, or website publication by itself.

It authorizes preserving the diagnostic, classifying it, and routing it through
the normal evidence and review gates.
