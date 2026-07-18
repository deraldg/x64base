<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SECURITY

- Catalog/topic: `DOT` / `SECURITY`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect DotTalk++ security policy/runtime rules and manage the current shell-session role identity and assignment view.

- Display x64Base security policy/runtime diagnostics or run built-in security self-tests.

## Status

- implemented=yes; supported=yes

## Syntax

- SECURITY [USAGE|SHOW|SELFTEST|RUNTIME|LOGIN &lt;role&gt; [AS &lt;worker&gt;]|WHOAMI|ASSIGNMENTS|LOGOUT]

## Usage

- SECURITY USAGE
- SECURITY SHOW
- SECURITY SELFTEST
- SECURITY RUNTIME
- SECURITY LOGIN &lt;DEVELOPER|TEACHER|STUDENT&gt; [AS &lt;worker&gt;]
- SECURITY WHOAMI
- SECURITY ASSIGNMENTS
- SECURITY LOGOUT

## Note

- SECURITY with no arguments prints usage.
- SHOW displays the active policy and profile roots.
- SELFTEST runs built-in security tests.
- RUNTIME describes runtime enforcement rules.
- LOGIN establishes a role/session identity for the current shell session.
- WHOAMI reports the active shell-session role identity.
- ASSIGNMENTS reports the assignment lane bound to the active role.
- LOGOUT clears the active shell-session role identity.
- SECURITY does not mutate table data.

## Provenance

- Topic key: `DOT|SECURITY`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
