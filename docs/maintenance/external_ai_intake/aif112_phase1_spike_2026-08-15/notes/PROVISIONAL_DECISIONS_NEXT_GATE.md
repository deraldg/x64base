# Provisional decisions for the next gate

These are not locked. The spike evidence will confirm or amend them.

| ID | Topic | Provisional lean |
|----|-------|------------------|
| P1 | Keep INV_ prefix (or local equivalent) | Yes, unless runtime already has a stronger convention |
| P2 | Member field in spike | Free text OK for Phase-1; bind to identity stack later if easy |
| P3 | INV_EVENT table | Optional; skip if INV_CHECKOUT history is enough |
| P4 | First real command family name | TBD after spike (e.g. INV / CHECKOUT / DOCCTL) -- do not invent until evidence exists |
| P5 | HELP / contracts timing | With the first public command package, not in this spike |
| P6 | Fossil | Still considered-not-adopted unless evidence records a concrete gap |
| P7 | Capsule integration depth | Spike only needs REF to accept a capsule id; deep AIF-055 integration is later |

## After spike evidence returns

1. Accept or amend P1-P7.
2. If proof bar met and no Fossil gap: draft the next package (command-family design + HELP plan), still no unnecessary C++ until required.
3. If a concrete gap is recorded: open a short decision on whether that gap justifies Fossil or a deeper runtime extension.
