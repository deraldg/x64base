# Messaging Normalization -- Registry-Wide Lane (Plan v1)

Codename: **Messaging** -- the localized, severity-aware output spine every command
routes through.
Status: **ACTIVE -- lane opened 2026-07-15.** Delivery vehicle already exists
(`cli::cmdout` + `message_catalog` + the Phase 23 locale spine); this lane makes
it the normalization contract for the registry-finishing campaign.

## The question

We are about to send an agent through the `cmd_*` registry to "finish each
program." What does *finished* mean for output? Answer: every command speaks
through one localized, severity-aware channel -- so a single normalization pass
buys regional language, error severity, `SET ERRORSTOP`, and consistent
formatting at once, instead of four separate campaigns.

## What already exists (do not rebuild)

- **`cli::cmdout`** (`src/cli/command_output.hpp`) -- the delivery vehicle:
  - `print_message(MessageId, vars)` -- localized, parameterized text.
  - `print_prefixed_message(cmd, MessageId, vars)` -- the same, `cmd:`-prefixed.
  - `print_error(cmd, xbase::error::code)` / `print_warning(cmd, code)` --
    **severity-carrying** diagnostics.
  - `print_info` / `print_note` -- non-diagnostic status.
- **`message_catalog`** (`src/cli/message_catalog.*`, `src/help/message_catalog.*`)
  and **`ERROR_STATUS` / `ERROR_CLEAR`** verbs over `tls_last_error`.
- **The locale spine** -- Phase 23A-U packages (repo root `LOCALE_PHASE23*.md`),
  the regional-language backbone under the catalog. This lane pulls that scattered
  work under one home; it does not restart it.
- **`xbase_error_context.hpp`** -- `tls_last_error`, `set_last_error/get/clear`,
  `error_guard`. The thread-local the runner reads for stop-on-error.

## The one wiring that ties it together (do this FIRST)

`cmdout` does **not** yet touch the error context. Wire the sink once:

```cpp
// src/cli/command_output.cpp
void print_error(const char* cmd, xbase::error::code ec) {
    xbase::error::set_last_error(ec);      // <-- ties messaging to STOP ON ERROR
    out() << ...;
}
void print_warning(const char* cmd, xbase::error::code ec) {
    xbase::error::set_last_error(ec);      // severity::warning; ERRORSTOP WARN can act on it
    out() << ...;
}
```

After this single change, every command later converted to `print_error(cmd, code)`
becomes `SET ERRORSTOP`-aware for free (see the ERRORSTOP intake finding). This is
why the wiring precedes the registry walk -- order is load-bearing.

### `SET ERRORSTOP` default: OFF (decided 2026-07-15)

`SET ERRORSTOP` defaults **OFF**. Rationale: the existing **regression suite runs
with stop-on-error off** -- those scripts deliberately execute past failing lines
(negative cases, expected-error assertions, full-sweep coverage) and would halt
prematurely under a default-ON flag. Default OFF preserves today's
run-through-everything behavior for the entire `.dts` corpus; scripts that want
fail-fast (Pinocchio-style QA, build/candidate scripts) opt in explicitly with
`SET ERRORSTOP ON` at the top. Do not flip the default; make fail-fast opt-in.

## The per-command contract ("definition of done")

A command is *messaging-finished* when:

1. **Diagnostics go through `cmdout`.** No raw `std::cout` for errors, warnings,
   or status. Errors use `print_error(cmd, code)` with a real
   `xbase::error::code` (severity + facility); warnings use `print_warning`.
2. **Text is catalogued.** User-facing message strings resolve through
   `MessageId` / `message_catalog`, not inline literals -- so the locale spine can
   translate them.
3. **`cmd:` prefixing is consistent** via the `cmd` argument.
4. **The data/result channel is untouched** (see boundary below).
5. **Failure sets the error code** at the failure site, so `ERROR_STATUS` and
   `ERRORSTOP` see it.

## The boundary that must not blur -- messages != data

Localize and cataloging apply to **diagnostics and status**, never to **tabular
result payload**. Commands that stream rows keep their data on the result/print
channel; do not force `LIST`/`DUMP`/`SMARTLIST` output through the message
catalog. Known payload-output commands to leave on the data channel (audit each,
but presumed data-first): `cmd_list`, `cmd_dump`, `cmd_smartlist`, `cmd_browse`,
`cmd_dir`, `cmd_dbarea(s)`, `cmd_calc`. Miss this line and you will try to
translate student rows.

## Coverage ledger (seed -- 2026-07-15)

Source of truth is the tree; regenerate with the commands below.

- **Total `cmd_*.cpp`: 184**
- **Route through `cli::cmdout`: 88** (~=48%)
- **Still raw `std::cout`: 98** (the migration backlog)
- **Use severity-coded `print_error`/`print_warning`: 0** <- the real gap
- **`cmdout` wired to `set_last_error`: no** <- do first (above)

Regenerate the ledger:

```bash
ls src/cli/cmd_*.cpp | wc -l
grep -lE 'cli::cmdout::'          src/cli/cmd_*.cpp | wc -l
grep -lE 'std::cout'              src/cli/cmd_*.cpp | wc -l
grep -lE 'print_error|print_warning' src/cli/cmd_*.cpp | wc -l
```

Diagnostics-first backlog (raw `std::cout`, not primarily payload) includes:
`cmd_create`, `cmd_import`, `cmd_export`, `cmd_copy`, `cmd_pack`, `cmd_zap`,
`cmd_delete`, `cmd_recall`, `cmd_reindex`, `cmd_rebuild`, `cmd_rel`, `cmd_sort`,
`cmd_scan`, `cmd_struct`, `cmd_fields`, `cmd_ddl`, `cmd_ddict`, `cmd_security`,
`cmd_status`, `cmd_workspace`, `cmd_var`, `cmd_if`/`cmd_while`/`cmd_until`/`cmd_loop`,
`cmd_sql*`, `cmd_lmdb*`, plus the rest of the 98. Prioritize commands that can
fail on user input (`create`, `import`, `export`, `copy`, `pack`, `delete`,
`reindex`, `rel`, `sort`) -- they yield the biggest `ERRORSTOP` payoff first.

## Agent marching orders (the campaign)

1. **Land the sink wiring** (`print_error/print_warning` -> `set_last_error`) and
   `SET ERRORSTOP ON|OFF|WARN`. One PR, no per-command churn.
2. **Walk the registry** command by command, applying the definition-of-done.
   For each: convert diagnostics to `cmdout`, assign/reuse a `MessageId`, set the
   error code at failure sites, leave payload on the data channel, tick the
   ledger.
3. **Assert, don't trust exit codes.** For each converted command, prove a forced
   failure now: (a) prints the localized message, (b) sets `ERROR_STATUS`, and
   (c) trips a `SET ERRORSTOP ON` DotScript. That triple is the acceptance test.
4. **Batch by facility** (io, dbf64, cli...) so related error codes land together
   and the catalog grows coherently.

## Progress log

- **Data-mutation group -- COMPLETE (2026-07-16).** Every command that writes,
  compacts, copies, or rebuilds is now on the localized, severity-tagged catalog:
  `DELETE`, `RECALL`, `ERASE`, `IMPORT`, `EXPORT`, `CREATE`, `ZAP`, `PACK`,
  `COPY`, `COMMIT`, `TURBOPACK`, `REBUILD`, `SORT`, `REINDEX` (plus `CALC`,
  `REPLACE`, `CALCWRITE`, `REPLACE_MULTI`, and `BUILDLMDB` which were already
  done). Each error/warning is registered with `ERROR`/`WARNING` severity, so the
  entire data-mutation surface is ERRORSTOP-ready the moment `cmdout::print_error`
  is wired to `set_last_error`.
- **Ledger:** ~78 `cmd_*.cpp` still emit raw `cout`/`cerr` (accurate count --
  includes bare `cout` from `using namespace std`, which the earlier `std::cout`
  ledger undercounted). Regenerate: `for p in src/cli/cmd_*.cpp; do grep -qE
  '(std::)?c(out|err) *<<' "$p" && echo "$p"; done | wc -l`.
- **Two i18n follow-ups accrued during the group** (queue, don't block): commands
  that compose their own error strings internally and emit them via a `{detail}`
  passthrough -- `CREATE`, `PACK`, `COPY`, `SORT` -- leave the *error text* itself
  un-tokenized (routed but not translated). A later pass should give those
  internal `err` strings their own `MessageId`s. Same for `CREATE`/`COPY` X64
  descriptor-warning clause fragments.
- **Interactive prompts stay raw.** `REBUILD`/`REINDEX` keep the y/N COMMIT
  prompt on `std::cout`+`std::cin` (2 sites each) -- chrome, like the REPL prompt.

- **Index/schema group + localization + runtime proof -- IMPLEMENTED, THEN
  CORRECTED AFTER AUDIT (2026-07-16, session 2).** This is a completed batch,
  not a claim that the Messaging Normalization lane is complete; the sink wiring,
  ERRORSTOP, and acceptance-triple gates below remain open.
  - **Localization of the whole modified surface.** The first pass localized 173
    command messages; the corrective audit removed the unused result-payload
    identity, so 172 useful messages now carry `es`/`fr`/`de`/`it` (688 inserted
    locale rows) -- pack, copy, commit,
    turbopack, rebuild, sort, reindex, scx, exportfunctions, indexseek, on top
    of the earlier data-mutation batch. The compiled validation catalog is now
    1323 messages / 2599 text rows, locales `{en-US, es, fr, de, it}`,
    `SET MESSAGE CATALOG CHECK` issues = 0. The active development DBF provider
    remains 1006 messages / 1270 text rows and resolves new symbols through
    compiled fallback; no DBF/CDX/LMDB synchronization was authorized. Inserted
    via a session-local scratch
    `outputs/i18n/insert_locales.py` that was not retained in the repository;
    its behavior is reported for provenance, not as a durable tool. Placeholder-set
    parity was verified per row.
  - **Usage cleanup and result-boundary correction.** `cmd_export_functions.cpp`
    usage/diagnostic/status text and `cmd_indexseek.cpp` usage text are catalogued.
    The first pass also routed five `INDEXSEEK(): <recno>` result emissions through
    the message catalog; the corrective audit restored those emissions to
    `std::cout` because record numbers are result payload, not localizable messages.
    The newly added `IndexseekResultText` row and five text rows were removed
    after confirming they existed only in this uncommitted/unpromoted batch and
    were absent from the active DBF catalog. See AIF-021 and the corrective closeout.
  - **Registration fix (real pre-existing bug).** `SCX` and `EXPORTFUNCTIONS`
    were unreachable from the shell -- only the dead `#if DT_HAVE_DLI_REGISTRY`
    self-registration path existed. Registered both canonical names in
    `shell_commands.cpp` and declared `cmd_SCX` in `shell_commands.hpp`; their
    new translations are now live from the CLI.
  - **Runtime proof.** `canaries\language_shakedown_canary.dts` drives
    `SET LANGUAGE {en-US,es,fr,de,it}` across the localized USAGE surface;
    verified every locale renders the right labels (`Uso:`/`Utilisation :`/
    `Verwendung:`/`Uso:`+`Esempi:`). Wired as a **default-suite `LANGUAGE`
    entry** in the `REGRESSION` launcher (curated list + `USAGE` notes), so
    `REGRESSION ALL` / `REGRESSION LANGUAGE` run it. The corrective audit
    converted the script's documented `;` comments to cross-path-safe `*`, added the
    required readiness block and a stable no-table `INDEXSEEK(): 0` probe, then
    ran `REGRESSION LANGUAGE` through the exact corrected Release binary with
    exit 0 and zero unknown-command/failure-pattern matches. The retained
    artifact is the full launcher-console transcript; `DOTSCRIPT OUT` alone did
    not capture every `cmdout` line during this audit. AIF-022 later proved that
    `;` was correctly skipped by this REGRESSION/DOTSCRIPT path but not by the
    separate top-level `--script` runner; the conversion is portability hardening.
  - **Corrective compliance record.** AIF-021 records that the first closeout
    skipped the dashboard Session Log, omitted the DotScript readiness block and
    durable transcript, understated its diff, crossed the result-channel boundary,
    and did not close the source-mutation contract gate. The correction restored
    the boundary, strengthened the canary,
    completed the missing documentation, and retained the unresolved
    `EXPORTFUNCTIONS` error-code choice as an explicit next gate rather than
    inventing a code during cleanup. AIF-022 corrects the initial Codex audit's
    semicolon attribution and records the actual split-runner drift.
  - **Console note.** Accented output shows mojibake under the default Windows
    codepage -- cosmetic only; bytes are correct UTF-8 (`chcp 65001` or a UTF-8
    log viewer to view). Native Read/Edit is authoritative; bash-mount reads of
    the 12k-line catalog can be truncated/stale.

- **First ERRORSTOP-sink vertical slice -- EXPORTFUNCTIONS error identity (2026-07-16, PROVEN).**
  A single reviewed command, upstream of any registry sweep, to settle the
  failure-emission contract before adoption:
  - Added the first `io`-facility canonical code `e_io_write_failed()` (io/0x0001)
    in `include/xbase_error_codes.hpp` with `to_string`/`symbol` arms.
  - Added the lane's failure-emission primitive
    `cli::cmdout::emit_error`/`emit_warning(MessageId, code, vars)` = localized
    `print_message` + `xbase::error::set_last_error`. One localized line; the
    English `to_string(code)` is never the user-facing line. This is the answer to
    "how a severity/error code and a localized MessageId emit together" without
    duplicate lines or English-generic replacement.
  - `EXPORTFUNCTIONS` adopts it: write failure -> `e_io_write_failed()`, bad format
    -> existing `e_invalid_argument()`, success -> `clear_last_error()`.
  - Also mapped the io code in `cmd_error_status.cpp`'s **local** `error_to_string`
    (that reader reimplements the header mapper and was missing the code -- first
    proof showed "Unknown or unmapped"; flagged for a collapse-into-header
    follow-up, out of this slice).
  - **Proven live** (retain console at
    `labtalk/proofs/runs/20260716_exportfunctions_error_identity_v1.txt`):
    `EXPORTFUNCTIONS MD docs` -> localized `EXPORTFUNCTIONS failed:` (en-US and es)
    + `ERROR_STATUS` = severity error / facility io (0x6) / number 1 /
    HRESULT 0xC0060001 / Message "I/O write failed."; positive control succeeds and
    clears. **ERRORSTOP halt itself is NOT wired -- out of scope; this proves error
    identity + localized emission + `ERROR_STATUS` only.**
  - Scope held: no `SET ERRORSTOP` wiring, no registry-wide `print_error` sweep, no
    active DBF sync, no legacy `print_error(cmd,code)` refactor, AIF-022 untouched.
    Preflight/design: `PREFLIGHT_EXPORTFUNCTIONS_ERROR_IDENTITY_2026-07-16.md`.

## Exclusions & conventions (decided during the walk)

- **REPL chrome is not a conversion target.** `shell.cpp` and reader/prompt code
  stay on raw `std::cout`/`std::cerr`: the `>` / `..` prompt, `rdbuf`/`pubsetbuf`
  buffering, `flush()`, and `[EXIT TRACE]` debug are infrastructure, not
  localizable command language. Do not catalog them.
- **TIMER instrumentation stays raw.** `TIMER START:` / `TIMER END  :` /
  `ELAPSED    :` are machine-parsed (the Pinocchio measure tooling reads the
  exact strings). Leave them; cataloging risks breaking measurement.
- **Non-command runtime messages use a `RUNTIME:<subsystem>` owner** (e.g.
  `RUNTIME:SCRIPT` for the init/script runner), distinct from `COMMAND:<X>`. This
  is the first sanctioned non-`COMMAND:` owner tag.
- **Data vs message, restated by example:** expression/value results (shell
  expression fallback, CALC) go to the data channel via `cmdout::print_line`;
  diagnostics/status go to the catalog via `print_message`/`print_prefixed_message`.

## Isolation & promotion

Unlike Pinocchio (disposable data lane), this lane edits **source** -- it rides the
normal dev -> staging -> GitHub authority chain and the source-mutation gate. Each
batch is a reviewable diff; the ledger percentage is the promotion signal. The
locale spine's own promotion (Phase 23F/G) governs catalog/schema changes; this
lane governs *consumer adoption* across the command registry.

## Definition of lane-complete

- `cmdout` wired to the error context; `SET ERRORSTOP` shipped.
- Raw-`std::cout` diagnostics count -> 0 (payload channel excepted and documented).
- `print_error/print_warning` adoption across all fail-capable commands.
- Every command passes the message/ERROR_STATUS/ERRORSTOP acceptance triple.
- Ledger at 100% of the diagnostics surface, tracked in this file.

## Related

- ERRORSTOP / stop-on-error design -- `CONTRACT_INTAKE_QUEUE_V1.md` (runtime
  findings) and the `cmd_dotscript.cpp` run loop.
- Locale spine -- `LOCALE_PHASE23*` packages, `SHARED_LOCALE_CONTRACT_v1.md`.
- Lane pattern -- `PINOCCHIO_STRESS_TEST_PLAN_V1.md`.
