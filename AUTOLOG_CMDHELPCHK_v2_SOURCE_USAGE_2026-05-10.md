# AUTOLOG 2026-05-10 - CMDHELPCHK v2 Source Usage Patch

Subsystem: HELP/source usage metadata, CMDHELPCHK v2 validation readiness

Files touched:
- `src/cli/cmd_help.cpp`
- `src/cli/command_helpchk.cpp`
- `src/cli/cmd_list.cpp`

Intent:
- Close the source-surface gaps reported by CMDHELPCHK v2 after source-root correction.
- Add command-local `@dottalk.usage v1` blocks to HELP, CMDHELPCHK, and LIST.
- Add explicit usage output for CMDHELPCHK and LIST.
- Add `HELP USAGE` handling while preserving no-argument HELP behavior.

Behavior preserved:
- HELP with no arguments still prints the top-level help router.
- CMDHELPCHK with no arguments still runs reflection validation.
- LIST with no arguments still lists records from the current cursor position.
- LIST still requires an open table except for LIST USAGE.

Tests performed here:
- Static patch construction only.
- Full local build/runtime must be run in the DotTalk++ tree.

Risk:
- Low. Changes are limited to usage/help surfaces and early usage branches.
- LIST argument stream is restored after peeking the first token.

Next recommended action:
- Build locally.
- Run HELP USAGE, CMDHELPCHK USAGE, LIST USAGE.
- Rerun CMDHELPCHK v2 scanner and review remaining gaps.
