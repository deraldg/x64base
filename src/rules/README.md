# x64base / DotTalk++ Rule Lane

Status: source-side AI and documentation governance seed.

This folder mirrors the active project rules inside the implementation tree.
The root `rules/` folder remains the informal human-facing rule scratchpad;
`src/rules/` is the source-side lane for rules that should be visible to
SelfDoc, MDO, manual generation, and AI portal workflows.

## Source / Manual / Website Gates

Rule 1: most technical data and information on `x64base.com` must be derived,
harvested, calculated, or reviewed from the implementation checkout. The website
may frame and organize material, but it must not become the source of truth for
runtime behavior, command syntax, file formats, index behavior, memo behavior,
HELP, metadata, or manual truth.

Rule 2: manuals may contribute reviewed sections, diagrams, summaries, and
publication-ready explanations to the website. Manuals must not consume website
copy as technical truth unless the website artifact is not derivable from the
implementation checkout and is maintained separately as a public artifact.

Rule 3: `README.*` files are sacred orientation and provenance artifacts. They
may be improved, annotated, or superseded, but if replaced the prior version
must be preserved as a versioned artifact. Do not clobber README files during
website, manual, staging, or AI-assisted work.

## Direction Model

Normal simplex flow:

```text
implementation checkout
  -> HELP / metadata / contracts / SelfDoc / MDO / manualgen
  -> reviewed manual
  -> reviewed website summary
```

Allowed duplex flow:

```text
reviewed manual section -> website summary
```

Blocked by default:

```text
website prose -> manual technical truth
```

Allowed exception:

```text
website-owned public artifact -> manual
```

The exception is valid only when the artifact is non-derivable elsewhere,
separately maintained, provenance-labeled, and owned.

## README Handling

Before changing any `README.*` file:

1. read the existing file;
2. identify the owning lane or project;
3. preserve useful content;
4. preserve the previous version before any replacement;
5. prefer a narrow patch over a rewrite; and
6. report the changed sections and preservation path.

