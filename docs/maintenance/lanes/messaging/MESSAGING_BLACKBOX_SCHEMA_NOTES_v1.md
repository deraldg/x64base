# Messaging Blackbox Schema Notes v1

Status: captured maintenance manifest
Lane: messaging

## Purpose

The messaging lane will replace scattered runtime output text with catalog-backed, typed, language-aware message strings.

## Current runtime clue

SET LANGUAGE / SET LOCALE already exists as a message-rendering locale setting. It selects message text templates; it does not localize command keywords and is not yet a full region/currency/date setting.

Known message locale examples:

- en-US
- es
- fr
- de
- it
- DEFAULT -> en-US

## Blackbox model

DATA IN

- hard-coded source text
- message intent
- message identifier
- message arguments
- command/runtime owner
- language or locale rows

PROCESS

- extract text literals
- classify message purpose
- assign message identifiers
- catalog message templates
- validate placeholders
- localize text
- gradually replace source strings
- smoke language fallback

INFORMATION OUT

- typed runtime messages
- localized output
- consistent warnings/errors/status/help text
- reportable message catalog
- testable message behavior

## Candidate x64base tables

- MSGDEF: canonical message definition
- MSGTEXT: language-specific message template
- MSGARG: placeholder/argument definitions
- MSGUSE: source/runtime usage evidence
- MSGLANG: supported languages and fallback policy
- MSGRUN: import/build/validation runs
- MSGGATE: promotion and validation gates
- MSGREVIEW: review/disposition records

## Safety boundary

Do not replace source strings directly until the message schema, extraction report, candidate catalog, and smoke/fallback rules are defined.

## Relationship to BBOX

Messaging is a clear teaching example:

```text
source text and locale data -> message catalog processing -> localized information output
```
