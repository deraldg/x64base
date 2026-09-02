<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SFTP

- Catalog/topic: `DOT` / `SFTP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Wrap the system OpenSSH sftp client for LS, GET, and PUT file transfer.

## Status

- implemented=yes; supported=yes

## Syntax

- SFTP USAGE
- SFTP LS &lt;user@host:/remote/path&gt;                      (alias: DIR)
- SFTP GET &lt;user@host:/remote/file&gt; TO &lt;local-file&gt;     (alias: FETCH)
- SFTP PUT &lt;local-file&gt; TO &lt;user@host:/remote/file&gt;     (alias: SEND)
- SFTP [USAGE|&lt;args...&gt;]
- SFTP LS &lt;user@host:/remote/path&gt;
- SFTP GET &lt;user@host:/remote/file&gt; TO &lt;local-file&gt;
- SFTP PUT &lt;local-file&gt; TO &lt;user@host:/remote/file&gt;

## Usage

- SFTP USAGE
- SFTP LS &lt;user@host:/remote/path&gt;                      (alias: DIR)
- SFTP GET &lt;user@host:/remote/file&gt; TO &lt;local-file&gt;     (alias: FETCH)
- SFTP PUT &lt;local-file&gt; TO &lt;user@host:/remote/file&gt;     (alias: SEND)

## Note

- SFTP USAGE prints usage and does not start the sftp client.
- DIR, FETCH and SEND are second spellings of LS, GET and PUT
- (cmd_sftp.cpp:529, :534, :539). All three dispatch and none appeared in this contract until 2026-08-28.
- This command stages a temporary sftp batch file and invokes the system sftp client.
- Password embedding in URLs is deliberately not supported.
- Set DOTTALK_ALLOW_HOST_COMMANDS=1 and DOTTALK_ALLOW_NETWORK=1 to enable transfer.

## Related

- WEB
- PSHELL

## Provenance

- Topic key: `DOT|SFTP`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
