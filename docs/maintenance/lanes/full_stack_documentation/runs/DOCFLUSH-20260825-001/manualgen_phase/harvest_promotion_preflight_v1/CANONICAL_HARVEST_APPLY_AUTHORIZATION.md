# Canonical HELP/META Harvest Apply Authorization

Decision: authorized for canonical harvest apply.

Recorded: 2026-08-26, from the maintainer's current instruction: "begin, and
you may enter the selfdoc realm to streamline processes".

Authorized by: `member.derald`.

Plan run: `DOCFLUSH-20260825-001-E5-PLAN-001`.

Plan manifest SHA-256: `82DE396E110C6361B662FDD43C7FDE677692607DC2C5B3B0EBFC17A331E42AA0`.

Mutation ledger SHA-256: `E5B6A3D0E0918268AF9197A694E1BDF79A00EC872940ADA8089928A2ACDF5CA2`.

Mutation rows authorized: 7.

## Authorized scope

Apply the exact seven `replace` rows in the bound mutation ledger. The eight
byte-identical files classified `verify_noop` remain untouched.

Required controls:

1. Recheck the plan, ledger, authorization, before, and candidate hashes.
2. Prove the candidate passes the semantic E5 freshness audit before writing.
3. Preserve all seven canonical before states byte-for-byte.
4. Stage and hash all seven after states before the first replacement.
5. Use atomic same-directory replacements.
6. Roll back all seven targets if any write or after-state check fails.
7. Prove the canonical workspace passes 14/14 semantic E5 checks after apply.

## Excluded

This does not authorize manual acceptance, reader-pointer changes, website
work, `C:\x64base`, GitHub promotion, push, deployment, HELP/META DBF mutation,
or any file outside the bound seven-row ledger. SelfDoc streamlining is
authorized as a separate follow-on slice and must not broaden this apply.
