# AIF-129 -- the contract sub-block vocabularies are uncontrolled

    Run    : COWORK-20260825-001 (member.ai.claude.cowork), for member.derald
    Claim  : coordination/aif/AIF-129.claim
    Found  : 2026-08-25, twice in one session and one sub-block apart --
             R127 (b) needed `status=` to be load-bearing, and Gate 1 Q3
             measured `risk:`.
    Tier   : MEASURED across the whole contract corpus.
    Status : CHARTERED, not started. Owner ruling 2026-08-25: one lane, both
             vocabularies.

---

## 1. The finding

Source contracts carry structured sub-blocks that LOOK machine-readable and are
not. Two are measured; they are the same defect.

### 1a. `status=` -- 19 spellings, and R127 just made it load-bearing

    supported (162)   experimental (19)   developer (8)   active (4)
    supported-conditional (4)   implementation-shim (2)
    implementation-helper (2)   supported-stub-mixed (2)
    sample-extension (2)   dev-tool   dev-canary   deprecated
    deprecated-compat   compatibility-alias   document-control-readonly
    backend-helper   implementation-present   review-needed   stub

R127 (b) ruled that a usage contract makes a command SUPPORTED **unless its own
`status=` says otherwise** -- so this string now decides whether a command is
supported, and it is an open set of nineteen hand-written spellings.

### 1b. `risk:` -- roughly 250 keys, prose values, and no consumer at all

**206 files carry a `risk:` block. ZERO rows reach the built HELP store** --
`RISK` is not among HELP_LINE's fifteen KIND values, and the literal string
does not occur in the store.

    mutates_table_data   182 uses, 16 distinct values
    mutates_cursor        43 uses, 14 distinct values
    requires_open_table   38 uses,  5 distinct values
    writes_files          18   reads_table_records 15   mutates_session 14
    ...then a tail of roughly 250 keys, MOST USED ONCE

`mutates_table_data` alone is written as: `no` (158), `yes` (5), `depends` (6),
and then `delegated`, `indirectly`, `schema`, `edit`, `create`,
`filesystem-level`, `interactive`, `on`, `IMPORTSQL`, `VALIDATE`, `REPAIR`,
`create/add/insert/move/delete/rebuild`. **Several of those are not values at
all -- they are the first word of a wrapped prose sentence.**

## 2. Why "looks structured" is worse than "is prose"

Nobody writes a parser for a paragraph. People do write parsers for
`key: value`.

A reader of `mutates_table_data` gets 158 `no` and 5 `yes` on its first run,
concludes it works, and silently mishandles the nineteen files that answer
`depends`, `delegated`, `indirectly` or `schema` -- the exact cases where
knowing whether a command mutates data matters most. **That is the
unsound-assertion family: a proxy that cannot answer the question put to it**,
and it is the same shape as the three withdrawn Gate 4 assertions and the
Python-port test that could not find an integer wrap.

The costume is the hazard. `risk:` has no consumer today, so nothing is broken
yet; the defect is that it is *ready* to be consumed wrongly.

## 3. What is NOT claimed

- **Not that the content is wrong.** 206 authors wrote real safety notes about
  real commands. The material is good; the container is not.
- **Not that `risk:` is a defect today.** It has zero consumers, so it misleads
  nobody yet. `status=` is different -- R127 (b) already made it decide
  something.
- **Not a proposal to delete either block.** The owner ruled the opposite for
  `risk:` (harvest it, see section 4).

## 4. Gate 1 Q3's answer, which this lane inherits

**Owner ruling 2026-08-25: harvest `risk:` as PROSE now; close the vocabulary
later.** So the first act is deliberately NOT a taxonomy: mine `risk:` into
HELP as a NOTE-like kind with NO key semantics, so 206 files of safety notes
stop being invisible, while making no claim that the keys mean anything.

**That act is BLOCKED ON COORDINATION, not on a decision.** It requires
changing `src/help/helpdata_source_miner.cpp` and rebuilding the HELP store,
and `dottalkpp/data/help/*` belongs to a concurrent session -- reads only for
this lane. It must be scheduled with that session, not taken.

## 5. The shape of the work, when it starts

1. **Enumerate** both vocabularies from the tree. Done for `status=` (19) and
   `risk:` (~250 keys); re-measure at start, because a corpus measurement is
   invalidated by the act of adding to the corpus (R126 s11).
2. **Close** each set. `status=` is small and already load-bearing, so it goes
   first. `risk:` needs a decision per key: keep, merge, or demote to prose.
3. **Make load-bearing only what is closed.** A key with an open value set must
   not be read by a consumer.
4. **Gate it**, so a new spelling fails rather than silently joining the tail.

Order matters: R127 (b) is already relying on `status=`, so that half is
repair, and `risk:` is prevention.

## 6. Good neighbour

    What changed:      this charter and its claim. No code, no contract edited.
    Whose area:        contracts are tree-wide; the HELP miner is `subsystem:
                       help`, owner member.derald, and the help STORE is a
                       concurrent session's.
    Authorization:     member.derald, 2026-08-25 -- "one lane, both
                       vocabularies", and Q3's "harvest as prose now, close the
                       vocabulary later".
    How to verify:     section 1b reproduces by parsing `risk:` blocks out of
                       src/**/*.cpp; section 1a from the harvested HELP lines
                       carrying `pattern=usage_contract`.
    How to undo:       delete this file and the claim. AIF-129 stays spent.
