// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: experimental

// src/cli/cmd_transaction.cpp
//
// TRANSACTION command -- explicit transaction-boundary control (BEGIN / COMMIT /
// ROLLBACK) over the WAL-backed write path.
//
// STUB (seeded 2026-08-04): the file carries its contract ahead of the
// implementation. The @dottalk.usage block below states the PLANNED surface.
// Keep it in step with the code as each arm lands, and never let it claim more
// than is implemented -- a usage contract that overstates a shipped capability
// is worse than none (docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md).

// @dottalk.usage v1
// owner: DOT|TRANSACTION
// command: TRANSACTION
// category: transactions
// status: experimental
// noargs: usage
// effect: transaction-control
// mutates: wal transaction-state table-data
// usage-access: TRANSACTION USAGE
// summary:
//   Explicit transaction-boundary control over the WAL-backed write path: open a
//   transaction, commit it as one unit, or roll it back.
// usage:
//   TRANSACTION USAGE
//   TRANSACTION BEGIN
//   TRANSACTION COMMIT
//   TRANSACTION ROLLBACK
//   TRANSACTION STATUS
// notes:
//   STUB -- the arms are being implemented; this block is the planned surface,
//     not a claim that every arm is live. Update per-arm as each one lands, and
//     demote status from experimental only when the arm is real and proven.
//   TRANSACTION drives the same WAL commit path as the standalone COMMIT
//     command; ROLLBACK discards the uncommitted span. See related.
// risk:
//   mutates_table_data: on COMMIT
//   writes_wal: yes
//   discards_uncommitted_changes: on ROLLBACK
//   requires_open_transaction: COMMIT and ROLLBACK
// related:
//   COMMIT
//   ROLLBACK
//   REBUILD
//

// TODO(member.derald): implement the TRANSACTION dispatcher (BEGIN/COMMIT/
// ROLLBACK/STATUS/USAGE) over the WAL commit path. Entry point follows the
// cmd_* convention, e.g. void cmd_TRANSACTION(xbase::DbArea& area,
// std::istringstream& args). Keep the @dottalk.usage block above in step with
// the arms as they land.
