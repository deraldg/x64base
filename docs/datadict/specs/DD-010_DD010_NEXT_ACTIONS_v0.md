# DD-010 Next Actions v0

## Preferred next package

DD-011: Rules / Constraints / xexpr Dictionary Link Map.

Goal: connect rule catalog, field constraints, xexpr expression parsing, validation messages, and dictionary fields without mutating runtime data.

## Held until explicit authorization

- Running `CMDHELPCHK REFLECT`.
- Running `CMDHELPCHK ARTIFACTS`.
- Running `CMDHELP BUILD`.
- Reading live runtime HELP DATA DBFs from a local runtime estate.
- Importing HELP DATA rows into x64base metadata/catalog tables.

## If runtime validation is authorized later

Use a separate guarded package, probably DD-010B, with:

1. Confirm runtime root and HELP slot/path.
2. Verify artifact files exist before running validators.
3. Run read-only `CMDHELPCHK` modes first.
4. Capture transcript.
5. Emit staging CSV/JSON only.
6. Do not run `CMDHELP BUILD` unless separately authorized.
