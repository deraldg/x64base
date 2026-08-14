# LabTalk Source-to-Case Inventory v1

Status: controlled planning artifact.

This inventory maps source/evidence material to normalized runtime-readable case records. It does not move, rewrite, or promote historical source files.

## Source Roots

| Root | Role | Handling |
|---|---|---|
| `dottalkpp/cases` | Primary source/evidence folder for uploaded DOCX files and older case folders. | Preserve as source evidence. Do not normalize in place. |
| `dottalkpp/docs/dottalkpp_legacy_doc_review_2026_05_09/02_EDU_CURRICULUM_INCUBATOR` | Legacy education/curriculum intake material. | Use as additional source evidence after review. |
| `docs/cases` | Runtime-readable normalized case catalog. | Maintain as derived CASE_*.md records and registries. |
| `x64base/docs` | Storyboard deck and LabTalk publication notes. | Treat as derived publication/media material. |

## Evidence Files Seen

| File | Current source path | Notes |
|---|---|---|
| `Case Studies Core Track.docx` | `dottalkpp/cases/Case Studies Core Track.docx` | Broad source for overview and engineering case framing. |
| `DottalkEd.docx` | `dottalkpp/cases/DottalkEd.docx` | Source for DotTalk++/LabTalk education framing. |
| `FoxPro -> DotTalkpp crosswalk (1).docx` | `dottalkpp/cases/FoxPro -> DotTalkpp crosswalk (1).docx` | Source for xBase/FoxPro crosswalk. Registry now preserves the actual filename spelling. |
| `Army_73C.docx` | `dottalkpp/cases/case001/Army_73C.docx` | Source for JUMPS/73C case. |
| `JUMPS in 1983 ran on IBM mainframes.docx` | `dottalkpp/cases/case001/JUMPS in 1983 ran on IBM mainframes.docx` | Source for JUMPS/73C case. |
| `unisys.docx` | `dottalkpp/cases/case003/unisys.docx` | Source for Unisys/CODASYL/ALCOA case. |
| `PAXON.docx` | `dottalkpp/cases/case004/PAXON.docx` | Source candidate for TitleSCAN/Paxon transfer case. |
| `LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` | `x64base/docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` | Derived storyboard/publication deck. |
| `LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md` | `x64base/docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md` | Derived storyboard notes. |

## Case State Matrix

| Case | Source state | Normalized CASE_*.md | Storyboard/media | Runtime state | Publication state |
|---|---|---|---|---|---|
| HIST-000 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate. |
| HIST-010 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-020 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs fact review. |
| HIST-030 | Source doc identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs source review. |
| HIST-040 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs source review. |
| HIST-050 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-060 | PAXON source candidate identified. | Yes, stub. | Shared media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-070 | Source still needs attachment/review. | Yes, stub. | Shared media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-080 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-090 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate. |
| ENG-010 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-020 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-030 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-040 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-050 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |

## Promotion Gate

The five first-wave historical cases are promoted only to `first_wave_review_candidate`. They remain `hidden_until_reviewed` until source review, factual review, media review, and runtime/lab review are complete.
