# Blackbox Educational Model v1

Status: captured maintenance manifest
Lane: blackbox
Future source file: src/cli/cmd_bbox.cpp

## Concept

Blackbox is the educational name for the classic computing model:

```text
DATA IN -> PROCESSING -> INFORMATION OUT
```

It should be used to teach how DotTalk++ SelfDoc systems transform data into information.

## Future command surface

Possible initial command family:

- BBOX
- BBOX USAGE
- BBOX MODEL
- BBOX LANES
- BBOX COMMENTS
- BBOX HELP
- BBOX MANUAL
- BBOX DATADICT
- BBOX MESSAGING
- BBOX MAINT

## Boundary

BBOX should teach and inspect. MAINT should govern operational maintenance. BBOX should not be the first place to launch mutating maintenance scripts.

## Example lanes

COMMENTS: source comments -> SRC* evidence
HELP: registry/source/DOTREF -> HELP DATA and help output
MANUALGEN: manual sources -> MAN* catalog and published manual
DATADICT: schema/evidence -> DD* catalog and DDICT output
MESSAGING: source text + locale -> typed localized messages
