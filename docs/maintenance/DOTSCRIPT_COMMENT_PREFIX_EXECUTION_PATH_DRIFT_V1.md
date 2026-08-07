# DotScript Comment-Prefix Execution-Path Drift v1

Date: 2026-07-16.
Status: runtime-proven drift; source-defined split; correction decision pending.
AI Friendly route: AIF-022.
Mutation: documentation and proof only; no source, HELP, DBF, index, or runtime-state mutation.

## Finding

Semicolon-prefixed lines have different behavior depending on which script
entry path executes the same `.dts` file:

| Entry path | Source path | `;` behavior | Runtime result |
| --- | --- | --- | --- |
| `DOTSCRIPT <file>` | `cmd_DOTSCRIPT` in `src/cli/cmd_dotscript.cpp` | skipped as documented | no unknown-command line |
| `REGRESSION <name>` | `cmd_regression.cpp` calls `cmd_DOTSCRIPT` | skipped as documented | same as `DOTSCRIPT` |
| `dottalkpp.exe --script <file>` | `dottalk::startup::run_script_file` in `src/cli/init_script_runner.cpp` | passed to `shell_execute_line` | `Unknown command: ;` |

Both tested entry paths returned process exit code 0, so exit status alone does
not expose the disagreement.

## Source evidence

- `src/cli/cmd_dotscript.cpp` advertises: lines beginning with `*`, `//`, `&&`,
  or `;` after trimming are skipped.
- Its `looks_like_comment_or_blank` implementation explicitly recognizes all
  four prefixes, and the command loop calls that filter before execution.
- `src/cli/cmd_regression.cpp` delegates regression scripts directly to
  `cmd_DOTSCRIPT`, so Claude's semicolon comments were valid for the intended
  `REGRESSION LANGUAGE` path.
- `src/cli/init_script_runner.cpp` uses `read_script_command` and then sends each
  nonempty line directly to `shell_execute_line`; it has no equivalent comment
  filter.
- `src/cli/script_reader.cpp` handles hash comments and trailing-semicolon
  continuation, but does not normalize the four DOTSCRIPT comment prefixes for
  the top-level launcher.

## Runtime proof

Artifact:

```text
labtalk/proofs/runs/20260716_dotscript_comment_prefix_path_drift_v1.txt
SHA-256 5F9A3F3EA6AF1BEAFDD3AAAC2BC3F855CC1F92156D5F7C3D6B3B7562CAC4DF99
52 lines; 2,331 bytes
```

The proof runs the same two-line temporary script through:

1. the executable's top-level `--script` path; and
2. a `DOTSCRIPT <file>` command launched from a one-line top-level driver.

Path A emits one `Unknown command: ;`; Path B emits none. Both execute the body
marker and exit 0. Temporary scripts are removed after the proof.

## Audit correction

The initial Codex corrective audit treated the semicolon failures seen during a
direct `--script` run as proof that Claude ignored the documented DOTSCRIPT
convention. That attribution was wrong. Claude followed correct HELP for the
intended `REGRESSION` path. AIF-021 and the Claude handoff are amended to remove
that deficiency.

Converting the canary to `*` remains useful because `*` is proven safe across
both paths, but it is classified as cross-path hardening, not correction of
Claude's reading of `DOTSCRIPT USAGE`.

## Decision gate

Before changing source, choose one contract:

1. **Unify script semantics (recommended):** factor one shared
   comment/blank-line classifier into the common script reader or shared runner
   and prove identical behavior for `DOTSCRIPT`, `REGRESSION`, GUI bridge, and
   top-level `--script`.
2. **Document intentionally different entry paths:** narrow the HELP and launcher
   documentation, then add tests that make the difference explicit.

Do not silently remove `;` from `DOTSCRIPT USAGE`: its documented behavior is
currently correct on that command path. Until the decision is implemented,
authors should use `*` for scripts that may cross entry paths.

