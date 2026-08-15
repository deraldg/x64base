# Evidence template -- AIF-112 Phase-1 spike (amended)

Fill this when the exercise runs. ASCII only.

```
AIF: AIF-112
Package: AIPR-20260815-GROK-003 (amended by steward ruling on prior art)
Baseline tip: <record actual tip at run time>
Runner: <member>
Date: <YYYY-MM-DD>
Instance: <how x64base / DotTalk++ was started>
Dogfood confirmed: yes / no  (must be yes)
Side-channel sqlite3 used: no  (must be no)
Carrier: DBF catalogs (SQLite oracle only)

--- Discover ---
LOCK/UNLOCK/SET EXCLUSIVE/SET MULTILOCKS surface: ...

--- Reuse audit ---
SYSGRANT / WORKSPACES / session_coordinator findings: ...

--- I5 probe (mandatory) ---
I5 reproduces: yes / no
Surviving lock artifact after normal area close: yes / no
Conflicting acquire from other pid: refused / succeeded / FORCE UNLOCK only
Notes: ...

--- Schema ---
Existing lock/reservation tables reused: <none | list>
Tables created through runtime: <list>
Create path used: ...
Capsule REF accepted without path assumption: yes / no

--- Register ---
Items registered: <count and kinds>
Query result (summary): ...

--- Exclusive lock ---
Acquire as spike.a: PASS / FAIL
Second exclusive acquire while held: FAIL (expected) / unexpected PASS
Failure mode: engine-enforced / SELECT-then-decide / other
List active check-outs: ...

--- Release / re-acquire ---
Release: PASS / FAIL
Re-acquire: PASS / FAIL

--- Stale recovery / EXPAT (mandatory) ---
Short EXPAT lease reclaim without FORCE UNLOCK: reachable / not reachable
Notes: ...

--- Advisory ---
Behavior observed: ...

--- Capsule ---
Friction notes: ...

--- SQLite oracle ---
Final INVCHKOUT state mirrored and agreed: yes / no / not run

--- Gaps (Fossil justification test) ---
Required property the runtime DBF surface could NOT express:
  <none | describe precisely>

--- Publication hygiene ---
Any file written that belongs on the public/GitHub tree: no / yes (list)

--- Commands / script (summary) ---
1. ...
2. ...
3. ...

--- Conclusion ---
Spike proof bar met: yes / no
I5 headline required: yes / no
Recommend next gate:
  [ ] proceed toward command-family design (still dogfooded, DBF carrier)
  [ ] more spike work needed (list)
  [ ] open separate lane for release_held wiring (engine change)
  [ ] reopen Fossil consideration (only if a concrete gap is recorded above)
```
