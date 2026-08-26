# Canonical HELP/META Harvest Apply Authorization -- Post E2

Decision: authorized for canonical harvest apply.

Recorded: 2026-08-26, from the maintainer's instruction to continue after the
guarded E2 HELP refresh.

Authorized by: `member.derald`.

Plan run: `DOCFLUSH-20260825-001-E5-POST-E2-001`.

Plan manifest SHA-256: `A7B3E6AEC87AE31389DFD79C90180592E96580BF187BE2A0F94C4259BAC8E4F0`.

Mutation ledger SHA-256: `F0022A62CE2DE225DC424573CA04DBDEBAD587A790478D02652D32BE25E6823B`.

Mutation rows authorized: 6.

## Authorized scope

Apply the exact six `replace` rows in the bound mutation ledger. The nine
byte-identical files classified `verify_noop` remain untouched.

Required controls:

1. Recheck the plan, ledger, authorization, before, and candidate hashes.
2. Prove the post-E2 candidate passes the semantic E5 audit before writing.
3. Preserve all six canonical before states byte-for-byte.
4. Stage and hash all six after states before the first replacement.
5. Use atomic same-directory replacements.
6. Roll back all six targets if any write or after-state check fails.
7. Prove canonical 14/14 semantic freshness after apply.

## Excluded

This does not authorize manual publication, website work, `C:\x64base`, GitHub
promotion, push, deployment, HELP/META DBF mutation, or any file outside the
bound six-row ledger.
