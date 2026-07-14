# Diagram Provenance Contract v1

Generated diagrams are derivative views. They do not replace source, runtime,
HELP, metadata, contracts, review packets, or proof.

Every newly generated diagram record must include its artifact path,
`derived_from` (normalized by readers to a list), generator, generation time
when available, and review/truth status. Conversions must preserve this record.
An intermediate SelfDoc report is recorded alongside its upstream evidence.

Local viewers expose every registered source. Missing provenance disables the
source action and is audited; sources are never guessed from filenames. A
generated artifact must not list itself as a source. Published records use
approved public URLs and must not expose local absolute paths.

Audit states are `provenance_ok`, `provenance_partial`, `provenance_missing`,
`provenance_target_missing`, and `provenance_not_public_safe`.

`tools/diagram/diagram_provenance.py` writes a JSON sidecar suitable for
Mermaid, Draw.io, SVG, HTML, and other generated formats.
