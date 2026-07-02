# BBOX CMDHELP / DOTREF Integration Plan v1

BBOX proof is now green across runtime, CMDHELP/current HELP DATA, canonical DOTREF, and HELP /DOT, but the proof layers still must remain conceptually separate:

- CMDHELP visibility should come from source usage contract mining and current HELP DATA generation.
- DOTHELP and HELP /DOT visibility come from the compiled DOTREF catalog path.
- Raw HELP DBF applies are not the first choice for BBOX.

Current continuity note:

- `CMDHELP` green does not by itself prove `HELP /DOT`
- for BBOX, later closeout evidence shows both are now green
- canonical live DOTREF header is `include\dotref.hpp`

Planned smoke commands:

```text
CMDHELP BBOX
BBOX USAGE
DOTHELP BBOX
HELP /DOT BBOX
```

No mutation is authorized by this plan.
