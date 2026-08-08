# SQLSEL verb redundancy -- design note (AIF-074)

**Status:** open design question (owner ruling requested).
**Lane:** AIF-074 (`SQLSEL_PDLC_LANE_V1.md`). **Owner:** member.derald.
**Steward/author:** member.ai.claude.cowork. **Date:** 2026-08-07. ASCII (`--`, `->`).

## The question

Why does a SQLSEL statement start with **two redundant select verbs**?

Today the grammar is `SQLSEL SELECT <list> FROM <table> ...`. The parser *requires*
the inner `SELECT`: `src/cli/sqlsel_statement.cpp:150` returns false (falls out of the
SQL path) unless the first token after `SQLSEL` is `SELECT`, and the command's USAGE
(`sqlsel_statement.cpp:132-135`) documents `SQLSEL SELECT <col> FROM <table>`. So the user
types the select verb twice: once as the brand (`SQLSEL`), once as the keyword (`SELECT`).

## Why that is wrong (the brand argument)

`SQLSEL` is the **home SQL brand** -- it *is* the select verb. It exists to disambiguate
three different meanings of "select" in x64base:

1. **xBase `SELECT <area>`** (`src/cli/cmd_select.cpp`) -- switches the active work area.
   NOT a query. This is the historical collision.
2. **SQLite `SELECT`** -- the external oracle grammar the conformance tests compare against.
3. **x64base `SQLSEL`** -- the real, first-class SQL select.

A dialect names its verb **once**. We never write `foxpro select ...` or `sqlite select
...`; the dialect is chosen, then its verb is used. `SQLSEL SELECT` does exactly the thing
we would never do in the other two -- it prefixes the dialect *and* repeats the generic
verb. The brand name already carries "select" (`SQL`-`SEL`), so the inner `SELECT` is
pure redundancy and it half-undoes the very confusion SQLSEL was coined to remove.

## Proposed grammar

`SQLSEL` becomes the verb; drop the inner `SELECT`:

    SQLSEL <select-list> FROM <table> [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]
    SQLSEL * FROM <table>
    SQLSEL COUNT(*) FROM <table> [WHERE <predicate>]

Read aloud it is "SQL-select these columns from that table" -- the verb once, up front.

## Migration (owner leans "break it")

- **Clean break (owner's stated preference):** make `SQLSEL <list> FROM ...` the only form;
  the inner `SELECT` is no longer accepted. Smallest surface, no dual grammar to carry.
- **Soft landing (option):** make the `SELECT` keyword *optional* at
  `sqlsel_statement.cpp:150` -- accept both `SQLSEL SELECT * FROM` and `SQLSEL * FROM` for
  one release, document the bare form as canonical, then remove the keyword. Costs a
  deprecation window but breaks no existing script or transcript mid-flight.

Either way the bare `SQLSEL <list> FROM` is the **documented canonical** form.

## What changes (touch points)

- `src/cli/sqlsel_statement.cpp:150` -- the `up(tok) != "SELECT"` gate: remove it (clean
  break) or make it optional (soft landing). The FROM/WHERE/ORDER BY/LIMIT parse is
  unaffected -- it already keys off `FROM`, not off `SELECT`.
- `sqlsel_statement.cpp:132-135` -- USAGE block, rewrite to the bare form.
- `REGRESSION SQLSEL_SELECT_V1` (`sqlsel_select_v1_regression.dts`) -- exercise the bare
  form; if soft-landing, exercise both and assert identical result sets.
- `include/sql_ref.hpp` -- the SQL conformance map.
- **Website + all documentation** -- see the doc-wide rule below.

## Doc-wide rule (this is the bigger job)

Everywhere x64base documentation talks about selecting data it must **differentiate the
two SELECTs by name**, because they are different commands that look alike:

- **`SELECT <area>`** = xBase work-area switch (navigation), and
- **`SQLSEL ...`** = the real SQL query (the home SQL brand).

A reader must never have to guess which "select" a page means. Audit the website
(`content/docs/dottalk/**`, `content/docs/engine/**`) and the manuals for bare "SELECT"
that should be one or the other, and name it explicitly. This is the standing consequence
of having a home SQL brand: the brand only removes confusion if the docs use it
consistently and never let generic "SELECT" stand in for the SQL verb.

## Recommendation

Adopt `SQLSEL <select-list> FROM ...` as canonical. Take the clean break if no live
scripts/transcripts depend on `SQLSEL SELECT` (owner to confirm); otherwise the one-release
optional-keyword soft landing. Then sweep the docs for the two-SELECT differentiation.
