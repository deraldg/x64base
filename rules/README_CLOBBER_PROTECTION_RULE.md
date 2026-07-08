# README Clobber Protection Rule

Status: source rule.

## Rule

Do not clobber, overwrite, truncate, regenerate, or replace any `README.*`
file without explicit user authorization for that exact file.

README files are sacred orientation and provenance artifacts. They may be
improved, annotated, or superseded, but if they are replaced the prior version
must be preserved as a versioned artifact so the old entry point remains
recoverable and comparable.

This includes:

- `README.md`
- `README.txt`
- `README.mdx`
- `README.rst`
- generated or staged names such as `README_*`
- nested project, package, tool, lab, proof, and third-party README files

## Required Behavior

Before changing a `README.*` file:

1. Read the current file.
2. Identify the owning lane or project.
3. Preserve existing useful content.
4. If replacement is required, preserve the prior version first.
5. Make a narrow patch instead of replacing the whole file.
6. Report the changed sections and preservation path in closeout.

If a README needs a rewrite, create a candidate file or patch proposal first,
unless the user explicitly asks for direct replacement.

## Rationale

README files are entry points, local contracts, and context anchors. In this
repo they may represent project boundaries, tool instructions, staging policy,
publication state, or third-party source context. Losing one can break future
AI orientation and human handoff.

## Allowed Exceptions

Direct replacement is allowed only when:

- the user explicitly requests replacing that exact README file,
- the file is newly created in the current task,
- the file is generated output and the generator contract says replacement is
  expected,
- the previous content is preserved as a versioned artifact and the closeout
  names that preservation path.

## Related Pointers

- `AI_README.md`
- `docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md`
- `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
- `docs/contracts/CONTRACT_LIFECYCLE_V1.md`
- `docs/governance/authority_order.md`
