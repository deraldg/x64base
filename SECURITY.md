# Security Policy

x64base is active beta research software. It should not be used for sensitive
or irreplaceable production data without independent review, backups, and
failure testing.

## Reporting a vulnerability

Do not publish credentials, private data, or a working exploit in a public
issue. Use GitHub's private vulnerability reporting when it is available for
this repository. Otherwise, contact the maintainer through the contact route
listed at <https://x64base.com/contact/> and request a private reporting
channel.

Include the affected commit, platform, build options, reproduction steps, and
the expected versus observed security boundary.

## Current security boundaries

- Host commands and delegated external processes are disabled by default.
- Network-capable commands require explicit opt-in.
- Transactional/atomic durability is not claimed for DBF, memo, and index
  coordination in the current beta.
- The project does not request or store SFTP passwords.

Security fixes are supported on the public `main` branch. Historical snapshots
and experimental branches are not supported release lines.
