# Evidence template -- AIF-112 Phase-1 spike

Fill this when the exercise runs. ASCII only.

```
AIF: AIF-112
Package: AIPR-20260815-GROK-003
Baseline tip: ea420f9b7
Runner: <member>
Date: <YYYY-MM-DD>
Instance: <how x64base / DotTalk++ was started>
Dogfood confirmed: yes / no  (must be yes)
Side-channel sqlite3 used: no  (must be no)

--- Schema ---
Existing lock/reservation tables found: <none | list>
Tables created through runtime: <list>
Create path used: <SQLITE DDL via runtime | other -- describe>
Capsule REF accepted without path assumption: yes / no

--- Register ---
Items registered: <count and kinds>
Query result (summary): ...

--- Exclusive lock ---
Acquire as spike.a: PASS / FAIL
Second exclusive acquire while held: FAIL (expected) / unexpected PASS
List active check-outs: ...

--- Release / re-acquire ---
Release: PASS / FAIL
Re-acquire: PASS / FAIL

--- Advisory ---
Behavior observed: ...

--- Capsule ---
Friction notes: ...

--- Gaps (Fossil justification test) ---
Required property the runtime SQLite surface could NOT express:
  <none | describe precisely>

--- Publication hygiene ---
Any file written that belongs on the public/GitHub tree: no / yes (list)

--- Commands / pydottalk script (summary) ---
1. ...
2. ...
3. ...

--- Conclusion ---
Spike proof bar met: yes / no
Recommend next gate:
  [ ] proceed toward command-family design (still dogfooded)
  [ ] more spike work needed (list)
  [ ] reopen Fossil consideration (only if a concrete gap is recorded above)
```
