# Manualgen Assembly Workspace Selection Contract V1

Status: active contract; report and candidate generation only  
Established: 2026-07-16  
Authority root: `D:\code\ccode`

## Purpose

Make the manualgen section-inventory and dry-run assembly input explicit without
conflating that input with the primary reader, an accepted manifest, or a
publication target.

## Selector

Evidence-bearing runs must pass:

```text
--publication-workspace <discovered-workspace-id-or-path>
```

The historical option name is retained for CLI compatibility. Its contract is
now assembly selection only. The selector accepts a discovered workspace id,
a repo-relative path, or an absolute path that resolves to a discovered
workspace.

An explicit value that does not resolve to a discovered workspace fails closed:

- `assembly_selection_mode = explicit_invalid`;
- `assembly_selection_valid = 0`;
- no assembly workspace or section set is selected;
- validation returns a failure.

## Roles

The selector must emit a role for the chosen workspace:

- `primary_reader_workspace` for the base reader workspace;
- `supporting_assembly_reference` for a workspace indexed under supporting
  publication workspaces;
- `unclassified_publication_workspace` when no role can be proven.

Selection never grants authority. Generated state and dry-run manifests must
emit `publication_authority_claimed = 0` for an assembly reference.

## Compatibility Boundary

When the selector is omitted, manualgen retains its historical selection order
so existing automation does not break. That run is labeled `legacy_default`,
`legacy_fallback`, or `legacy_last_discovered`; validation emits REVIEW rather
than treating the implicit choice as evidence-grade.

The fields `current_publication_workspace` and `current_publication_id` remain
temporary read compatibility aliases. New code and reports must use:

- `selected_assembly_workspace`;
- `selected_assembly_id`;
- `selected_workspace_role`;
- `assembly_selection_mode`;
- `assembly_selection_requested`;
- `assembly_selection_valid`.

The legacy-named `manualgen_current_publication_manifest_v1.json` is a
compatibility export and must declare
`manifest_role = legacy_compatibility_assembly_reference_export` and
`publication_authority_claimed = 0`. The authoritative report-layer expression
of the selection is `manualgen_selected_assembly_manifest_v1.json`; it is not an
accepted manual manifest.

## Required Validation

An evidence-bearing run passes this contract only when:

1. selection is explicit and resolves to a discovered workspace;
2. workspace role is classified;
3. selected combined Markdown and section inputs exist;
4. section parity has zero failures;
5. boundary checks have zero failures;
6. accepted reader, accepted manifest pointer, MAN* catalogs, COMMENTS escrow,
   HELP data, product source, and runtime data are not promoted or mutated by
   the selector run.

Exact combined-file hash parity may remain REVIEW when generated headers or a
classified overlay explain the difference and all inventoried section bodies
pass.

## Promotion Boundary

This contract authorizes selector implementation, report/manifests refresh,
generated dry runs, parity review, tests, and audit evidence. It does not
authorize:

- primary-reader replacement;
- accepted-manifest or pointer changes;
- publication replacement;
- overlay acceptance;
- MAN* refresh;
- COMMENTS load;
- HELP rebuild;
- public projection.

