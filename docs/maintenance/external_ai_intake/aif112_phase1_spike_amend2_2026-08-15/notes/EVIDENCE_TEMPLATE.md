# Evidence template -- AIF-112 Phase-1 spike (Handoff 2)

**Scribe note.** GROK-004's template with the steward's Handoff 2 section 5 delta
applied: the I5 probe is demoted to an optional field, EXPAT reclaim is mandatory,
the exclusive-refusal field now records whether the refusal was under-FLOCK, and an
attribution line was added. Authority: steward ruling section 5 and outline step 4.

Fill this when the exercise runs. ASCII only.

```
AIF: AIF-112
Package: AIPR-20260815-GROK-003, amended by GROK-004 and GROK-005
Baseline tip: <record the INSTANCE BANNER stamp, not git rev-parse HEAD>
Runner: <member>
Date: <YYYY-MM-DD>
Instance: <how x64base / DotTalk++ was started>
Dogfood confirmed: yes / no  (must be yes)
Side-channel sqlite3 used: no  (must be no)
Carrier: DBF catalogs (SQLite oracle only)
Attribution mode: string stamp via current_member() / N(20) FK  (steward
  recommends string stamp for Phase-1)

--- 1. Reuse audit ---
SYSGRANT findings: ...
WORKSPACES findings: ...
session_coordinator status/lock verbs: ...
Anything suitable to extend rather than create: <none | describe>

--- 2. Schema ---
Tables created through runtime: <list>
Location: <path -- must be private runtime, never staged>
Create path used: ...
ID allocation: max(id)+1 under catalog FLOCK  confirmed: yes / no
Tables visible via runtime table list: yes / no

--- 3. Register ---
Items registered: <count and kinds>
Capsule REF accepted without path assumption: yes / no
Query result (summary): ...

--- 4. Exclusive proof (mandatory) ---
Acquire exclusive as spike.a: PASS / FAIL
Second exclusive acquire on the held ITEMID: REFUSED (expected) / unexpected PASS
Refusal enforced UNDER the FLOCK (check and insert in one lock scope): yes / no
  -- if no, describe what actually enforced it
Active check-outs listed (highest ACQAT per ITEMID where STATE=Held): ...

--- 5. Release / re-acquire ---
Release (append Released / supersede Held): PASS / FAIL
No active exclusive holder after release: yes / no
Re-acquire: PASS / FAIL

--- 6. EXPAT lease reclaim (MANDATORY) ---
Short EXPAT lease set: yes / no
Lapsed and reclaimed WITHOUT any force path: reachable / not reachable
Notes: ...
  (force_unlock_table / force_unlock_record are confirmed unreachable from any
   command; the ledger must not need one)

--- 7. SQLite oracle ---
Final INVCHKOUT state mirrored and agreed: yes / no / not run

--- 8. Publication hygiene ---
Any file written where it promotes to publication: no / yes (list)

--- OPTIONAL: I5 probe (NOT a proof-bar gate for this lane) ---
Run: yes / no
I5 reproduces: yes / no / not run
Surviving lock artifact after normal area close: yes / no
Conflicting acquire from other pid: refused / succeeded
Cleared by: normal unlock / nothing exposed / not tested
Route: engine lane (release_held + force_unlock_* dead code), NOT AIF-112

--- Gaps (Fossil justification test) ---
Required property the runtime DBF surface could NOT express:
  <none | describe precisely>

--- Commands / script (summary) ---
1. ...
2. ...
3. ...

--- Conclusion ---
Proof bar met: yes / no
  (mandatory: dogfood, no side-channel, exclusive under-FLOCK refusal,
   release/re-acquire, EXPAT reclaim, publication hygiene, SQLite oracle)
Recommend next gate:
  [ ] proceed toward command-family design (dogfooded, DBF carrier)
  [ ] more spike work needed (list)
  [ ] open separate engine lane for release_held / force_unlock_* (not this lane)
  [ ] reopen Fossil consideration (only if a concrete gap is recorded above)
```
