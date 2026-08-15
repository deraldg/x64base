# Spike goal and proof bar

**AIF:** AIF-112
**Baseline:** development @ ea420f9b7
**Style:** dogfood x64base (D1/D7)

## Goal

Demonstrate, through a live x64base / DotTalk++ instance:

1. Register inventory items (including at least one capsule-shaped reference).
2. Acquire an exclusive check-out.
3. Fail a second exclusive acquire on the same item (lock holds).
4. Release the check-out.
5. Re-acquire successfully after release.
6. List current check-outs (who / what / when / exclusive vs advisory).
7. Keep the ledger private (nothing proposed for the GitHub publication tree).

## Non-goals

- No C++ engine changes.
- No new public command family yet (HELP/contracts come later).
- No multi-user stress beyond single-writer exclusive-lock proof.
- No free-standing sqlite3 side channel.
- No Fossil adoption unless evidence shows a required property the runtime surface cannot express.

## Proof bar (spike exit)

Spike exits green when all of the following are true and recorded in the evidence note:

- [ ] Ledger tables (or equivalent runtime structures) exist and were created through x64base / DotTalk++ surfaces.
- [ ] At least three inventory items registered, one of them capsule-shaped.
- [ ] Exclusive acquire succeeds for member A.
- [ ] Second exclusive acquire by member B (or same member in a second session) fails while lock is held.
- [ ] Release succeeds; subsequent acquire succeeds.
- [ ] Inventory / check-out list query returns the expected rows.
- [ ] No files were written that belong in the public/GitHub tree.
- [ ] Evidence note filled (schema as seen through runtime, commands used, results, any gap that would justify Fossil).

## Status vocabulary

- **PLANNED** -- this package (definition only)
- **PARTIAL** -- only after runtime proof on a later package that includes the real command surface + HELP
- **SUPPORTED** -- only after cold-clone + teaching-grade contracts

This spike itself does not advance status past evidence collection.
