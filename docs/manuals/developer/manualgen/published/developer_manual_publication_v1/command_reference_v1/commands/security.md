<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SECURITY

- Catalog/topic: `DOT` / `SECURITY`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display x64Base security policy/runtime diagnostics or run built-in security self-tests.

## Status

- implemented=yes; supported=yes

## Syntax

- SECURITY USAGE
- SECURITY SHOW
- SECURITY SELFTEST
- SECURITY RUNTIME
- SECURITY LOGIN &lt;DEVELOPER|TEACHER|STUDENT&gt; [AS &lt;worker&gt;]
- SECURITY WHOAMI
- SECURITY ASSIGNMENTS
- SECURITY LOGOUT
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
- LOGIN establishes only the legacy diagnostic role selector used by this
- SECURITY command; it is not USER authentication and grants no RBAC access.
- WHOAMI reports that legacy diagnostic role selector.
- ASSIGNMENTS reports the assignment lane bound to the active role.
- LOGOUT clears the legacy diagnostic role selector.
- Use USER LOGIN/LOGOUT/WHOAMI for authenticated identity, effective member, role/permission evaluation, owner-gated administration, and enforcement.
- SECURITY does not mutate table data.

## Related

- USER
- ERROR_TEST
- VALIDATE

## Provenance

- Topic key: `DOT|SECURITY`
- Included HELP rows: `35`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
