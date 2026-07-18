# Partial HELP Reference

## Reading this appendix

This appendix preserves command identities whose collected HELP evidence is
partial. An entry here is not a support promise. `registered` means a name is
visible in a command surface; `legacy syntax` preserves a compatibility form;
`unsupported` means the current evidence does not authorize behavior prose or
runtime availability claims.

## CANARY

Status: registered; unsupported pending curated DOTREF review.

`CANARY` is a registered DotTalk++ command, but its curated support status and
help summary are pending. Keep the identity visible for audit and reconciliation
without documenting an inferred behavior. Move it to a normal command section
only after the support contract and runtime evidence agree.

## FOX DO

Status: legacy compatibility syntax; not currently implemented or supported.

Legacy form: `DO <program> [WITH <args>]`.

Retain this form only to help readers interpret older FoxPro-style material.
Use `DOTSCRIPT` for current script execution. The redirect does not claim that
`DOTSCRIPT` reproduces every historical `DO` semantic.

## FOX RUN

Status: legacy compatibility syntax; not currently implemented or supported.

Legacy forms: `RUN /N <command>` and `RUN <file>`.

Retain these forms only as compatibility reference. Do not infer current
runtime support, background-process semantics, or equivalence to another shell
launcher until separately established by contract and runtime proof.

## Promotion boundary

Partial entries remain segregated from supported command prose. Promotion out
of this appendix requires an explicit support decision, source/HELP identity
agreement, and appropriate runtime evidence.
