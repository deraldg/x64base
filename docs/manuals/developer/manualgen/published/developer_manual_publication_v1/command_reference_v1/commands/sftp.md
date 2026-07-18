<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SFTP

- Catalog/topic: `DOT` / `SFTP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

File-transfer helper surface for SFTP-oriented workflows where enabled by local policy.

- Wrap the system OpenSSH sftp client for LS, GET, and PUT file transfer.

## Status

- implemented=yes; supported=yes

## Syntax

- SFTP [USAGE|&lt;args...&gt;]

## Usage

- SFTP USAGE

## Note

- SFTP USAGE prints usage and does not start the sftp client.
- This command stages a temporary sftp batch file and invokes the system sftp client.
- Password embedding in URLs is deliberately not supported.
- Set DOTTALK_ALLOW_HOST_COMMANDS=1 and DOTTALK_ALLOW_NETWORK=1 to enable transfer.

## Provenance

- Topic key: `DOT|SFTP`
- Included HELP rows: `9`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
