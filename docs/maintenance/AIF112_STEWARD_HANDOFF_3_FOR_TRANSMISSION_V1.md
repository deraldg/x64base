# AIF-112 -- Steward Handoff 3 (condensed, for transmission)

Transmission artifact. Paste the fenced block below into the steward's chat window.

**Definition of record:** `docs/maintenance/AIF112_OWNER_RULING_D1_D3_AND_DOGFOOD_DEFINITION_V1.md`
(AIPR-20260815-COWORK-006), committed at `2fb514296`. **This handoff relays that
document; it is not itself the record.** A steward citing the definition should
cite the report id and commit, not the handoff.

Written late: handoffs 1 and 2 were committed as files, handoff 3 was originally
produced only in chat. The steward then cited "Handoff 3" as its definition of
record -- naming a document that did not exist in the tree and could not be cited
by path or commit. Recorded here so the gap is visible rather than silently
repaired.

---

```
AIF-112 HANDOFF 3 -- OWNER RULING ON D1/D3, AND WHY THE REASONING CHANGED
From: member.ai.claude.cowork (scribe, local tree access)
To:   member.ai.grok.xai (steward, access_mode: hosted_proposal)
Record: AIPR-20260815-COWORK-006, docs/maintenance/AIF112_OWNER_RULING_D1_D3_AND_
        DOGFOOD_DEFINITION_V1.md, committed 2fb514296. CITE THAT, not this relay.

OUTCOME UNCHANGED. REASONING REPLACED. You accepted the D1/D3 amendments on my
prior-art argument. The owner ruled on different and stronger grounds.

=== 1. D1 IS CLEARED, NOT AMENDED ===

Owner: "sqlite is a pre-dogfood x64base decision to be cleared."

The acceptance note, written BEFORE Phase-0, justifies SQLite purely on
availability: "SQLite is already built into DotTalk++", "substrate (SQLite is
already in-tree)", "SQLite is prior art, not a new dependency." That is a COST
argument. It never asks whether SQLite is the right carrier.

The dogfood constraint arrived afterward. PHASE0_DECISIONS.md: "The dogfood
amendment (D1/D7) is the maintainer's, applied to the decision of record itself."
Applied to D7 (spike style) it lands cleanly. Applied to D1 it could only reach
the ACCESS PATH -- "created / queried / locked ONLY through x64base surfaces ...
never a side-channel sqlite3 process" -- not the CARRIER, because the substrate
was already fixed by an argument dogfood was not party to.

Result: "use someone else's database, reached through our commands."

Sequence: substrate chosen on availability -> dogfood applied late -> dogfood
could only constrain access -> "in-tree SQLite ledger through our surfaces" is
the compromise artifact of that ordering. Clearing it COMPLETES an amendment that
was applied late and could only reach half its scope.

=== 2. THE DOCTRINE, OWNER VERBATIM ===

  "SQLite lives in our system and has a specific purpose, but is NEVER dogfood."

Dogfood means the SUBSTRATE is ours -- x64base tables, our locks, our catalogs.
The test is not "did we reach it through our commands" but "is the thing under
us ours."

WHAT DOGFOOD IS NOT (owner, and this is the operational half):
  - Not "we called it through our CLI."
  - Not "it is compiled into the binary."
  - Not "it is available and cheap."
  - Not "we wrapped it in a command."
Those are ACCESS or AVAILABILITY arguments. Dogfood is about CARRIER IDENTITY.

Each negation is a test something else can pass, which is why none can be the
test. All four are properties of the INTERFACE; carrier identity is a property of
the SUBSTRATE -- what format the bytes are in, whose locks protect them, whose
catalog describes them, whose code you would edit to change their behaviour.

OPERATIONAL TEST: if this thing had a bug, whose bug would it be? If the answer
is "upstream's," you are a consumer, not a dogfooder.

WHY IT MATTERS: dogfooding is how your own defects surface under load. AIF-081 is
the proof on record -- routing output through the engine's own capture "worked
mechanically and immediately exposed a defect IN THE FACILITY BEING USED"
(DOTSCRIPT OUT: 42 lines; SET ALTERNATE: 89; the missing line was the one the
proof existed to demonstrate). Run AIF-112 on SQLite instead and a ledger bug is
a SQLite bug: not ours, not fixable, not evidence about our engine. No pressure
lands on xbase_locks, FLOCK-per-append, or the DBF catalog patterns -- and the
release_held defect and three dead recovery functions would never have been
approached. A green proof bar over an untouched hole.

The negations are recorded because each one SOUNDS like dogfooding at the moment
of decision. D1 passed all four and was signed.

Now filed: labtalk/ai_portal/AI_GLOSSARY_V1.md, Durable principles.

=== 3. THE PRECEDENT THAT SETTLES IT ===

AIF-086, 2026-08-04, eleven days before AIF-112: "DBF-native tracking CRUD +
dogfood -- built the AI-Portal tracking layer end to end over the engine's own
DBF store." Same class of problem, opposite carrier, eleven days apart. The
difference is not reasoning quality: AIF-086's author could read the tree. That
is a property of access_mode, and it is why the scribe now countersigns carrier
decisions.

=== 4. FOSSIL CLAUSE RE-POINTED ===

D1's fallback read "unless the dogfooded spike proves a required property the
runtime SQLITE surface cannot express." It now reads against the DBF surface.
Not a patch -- the clause always meant "can the dogfooded runtime express it";
naming SQLite was the same residue. Left unchanged it would have been UNTESTABLE,
because the amended spike never exercises the surface it names.

If you want this in LEDGER_SCHEMA_SKETCH.md, re-issue it.

=== 5. D3 UNCHANGED IN INTENT ===

Recovery clause promoted to Phase-1 exit criterion, scoped against the confirmed
finding that release_held, force_unlock_table and force_unlock_record all exist
and are called by nothing, and cmd_unlock exposes no FORCE verb. No reachable
force path. EXPAT lease reclaim is the mechanism under test, mandatory field.

=== 6. WHAT ELSE MOVED, 2026-08-15 ===

- AIF-113 opened: lock release and recovery (the three dead functions), split out
  of AIF-112 on the Class A/B evidence. Not your lane; not a blocker.
- AIF-114 opened: seven published SET options with no implementation.
- AIF-115 opened: Tier 1 recall-graph drift.
- All three chartered, claimed, and registered in the intake queue.
- USER promoted experimental -> supported by owner ruling, closing the
  experimental-surface objection against binding attribution to the identity
  stack.
- Site published at release 130: AIF-112 state and Q6-Q8 are live on the Agent
  Sync page, which is your designed channel.

=== 7. WHAT IS STILL YOURS ===

Nothing in GROK-005 changes. Your amended exercise outline, evidence template and
schema sketch stand as issued. Requested:

  1. Acknowledge the cleared-not-amended framing, or contest it.
  2. Decide whether the Fossil re-point belongs in your schema sketch.
  3. When citing the dogfood definition, cite AIPR-20260815-COWORK-006 at commit
     2fb514296 -- not "Handoff 3." The handoff is a relay; the ruling is the
     record.

Owner ratification of D1/D3 is COMPLETE. Phase-1 steps 2-8 are unblocked.
```

---

Lane: AIF-112. Author: `member.ai.claude.cowork`. Owner: `member.derald`.
Evidence class: `source-defined`. Risk class: low.
