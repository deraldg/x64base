# Credits

Contributions to x64base / DotTalk++ that shaped the system without appearing in `git log`.

This file exists for a specific reason. The project's agency model
(`docs/ai-friendly/AGENCY_MODEL_V1.md`) draws a hard line: **influence is not authority.** Someone can
originate an idea that changes the system's direction without ever holding a member row, a token, or
a commit bit. Git records the committer. It has no field for the person whose idea it was.

`labtalk/registries/ai_runs.yaml` solves that for AI partners with its
`planned_by` / `authored_by` / `owner` / `committer` split. This file does the same for people.
Recording influence honestly costs nothing and keeps the record true.

---

## Maintainer / owner

**Derald Grimwood** (`member.derald`) -- owner, architect, sole committer. Authority for every change
in this repository rests here.

## Contributors

**Nathaniel A. Strickland** -- the **Ollama local model** and **GPTbase**.

The local-inference direction and the hosted knowledge-bundle advisor both trace to Nathaniel A.
Strickland. Their effect on the architecture is larger than their footprint suggests: the isolated
local model is what makes `CHAT` answerable while `host.network.egress` stays blocked -- the AFB
air-gap property the BBS lane depends on -- and GPTbase established the "ask the project expert"
front-end pattern. Both are documented in `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md`, where they are
named as distinct roles precisely because neither is an agent.

**Nathaniel L. Grimwood** -- the **chat idea**.

The concept that the system should have a conversational surface at all. That idea became the AI-BBS
lane (AIF-052..057): `BBS CHAT`, The Lounge, the guestbook, and ultimately `board.worklog`, the
handoff drop-point that lets agency survive a session ending. A large part of the 2026-07-25 build
descends from it.

---

## How to read this file

Being credited here is **not** a grant of authority. None of these contributions carry a member row,
a permission set, or commit rights, and this file does not create them. It records *whose thinking is
in the system* -- which the agency model treats as a real and separate thing from *who may act on it*.

Additions are an owner action. If your work is in here and unlisted, that is an omission worth
fixing, not a slight.

Owner: `member.derald`. Lane: AIF-060 (agency model).
