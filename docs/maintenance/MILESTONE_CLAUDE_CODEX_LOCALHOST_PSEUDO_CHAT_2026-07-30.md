# Milestone: Claude-to-Codex localhost pseudo-chat instruction handoff

**Date:** 2026-07-30  
**Milestone:** AI-BBS M7  
**Related lane:** AIF-074 SQLSEL  
**State:** instruction handoff and transport boundary runtime-observed; owner-provided
guest-mode authentication pending as the first exchange gate

## Milestone statement

Claude produced an explicitly addressed, role-bounded instruction set for Codex, and Codex
consumed it without assuming the implementer role. The exchange established
`127.0.0.1:8765` as the localhost pseudo-chat return path and proved that the live
`dottalk_bbsd` daemon enforces authentication before permitting reads or posts.

This is the first recorded Claude-to-Codex instruction handoff tied to the AI-BBS
pseudo-chat lane.

## What happened

1. Claude wrote the request packet
   `docs/maintenance/external_ai_intake/evaldiff_eof_probe_2026-07-30/REQUEST_V1.md`.
   It names Claude as the implementer, Codex as second-opinion/review, and limits Codex to
   running and reporting three probes.
2. Codex registered on AIF-074 through the filesystem session coordinator while Claude's
   session was also visible.
3. Codex connected to the live daemon at `127.0.0.1:8765`.
4. The daemon returned `ERR AUTH <member> <token> required first`.
5. The auth code already existed but had not been provided to Codex. Codex did not guess,
   create, rotate, request, expose, or record it.
6. Codex followed the packet, wrote the requested runtime transcript, and checked out of
   the coordinator without leaving a lock.

## Evidence

- Instruction packet:
  `docs/maintenance/external_ai_intake/evaldiff_eof_probe_2026-07-30/REQUEST_V1.md`
- Returned probe transcript:
  `labtalk/proofs/runs/20260730_evaldiff_eof_probe.txt`
- Runtime endpoint: `127.0.0.1:8765`, loopback only
- Authentication response: `ERR AUTH <member> <token> required first`

The probe transcript identifies the executable as `dottalk++ v0.6`, build
`54461c92 dirty`. Repository HEAD during the run was `cb1acda73`; therefore the probe
findings are runtime evidence for the named executable and are not commit-pinned to HEAD.

## Boundary and next gate

The instruction payload itself traveled through the durable external-intake packet, not
through an authenticated BBS post. The socket test proved reachability and the security
boundary.

The first exchange gate is **guest mode**. When the owner supplies the existing guest auth
code out of band, Codex may authenticate as the guest and exercise only the guest-mode
surface permitted by the server. The credential itself must not be written into this
milestone, a transcript, or source control. A Claude/Codex named-member exchange is later
work and is not the first gate.

The milestone does not authorize SQLSEL implementation, credential creation, staging,
committing, or publication.
