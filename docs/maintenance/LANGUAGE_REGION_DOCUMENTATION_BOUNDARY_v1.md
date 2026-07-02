# Language, Region, and Documentation Boundary v1

Status: maintenance policy note
Scope: messaging, locale, manuals, help, educational distribution

## Purpose

This note records the intended boundary between:

- runtime message language
- future region/culture formatting
- multilingual manuals and educational documentation

These concerns are related, but they should not be forced into one implementation phase.

## Current Reality

The current runtime already exposes a limited language/locale control point:

- `SET LANGUAGE`
- `SET LOCALE`

That control point is currently a message-rendering locale selector. It is not yet a full region/culture subsystem for:

- dates
- numbers
- currency
- sorting/collation
- command keyword localization

This is consistent with the current messaging doctrine and runtime clues:

- `src/cli/cmd_set.cpp`
- `src/cli/cmd_msgmgr.cpp`
- `dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf`
- `dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf`
- `dottalkpp/data/locale/SYSTEM_LOCALES.dbf`
- `dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf`

## Boundary Decision

### 1. Runtime language support stays narrow in the near term

For the x64base/runtime distribution, multilingual runtime behavior is not the first priority.

Near-term runtime language support should be limited to essential operator-facing text such as:

- file not found
- no table open
- unsupported locale
- catalog load failure
- index/open failure
- selected startup/status/teaser messages

This keeps the runtime practical without forcing a full translation project across every command and developer-only surface.

### 2. Region is a later subsystem, not a synonym for language

Language selection and region/culture formatting are different concerns.

For now:

- `SET LANGUAGE` / `SET LOCALE` should be interpreted as message-template selection
- region-sensitive formatting should remain a later guarded phase

Future region work may govern:

- display date formatting
- numeric formatting
- currency formatting
- locale-specific parsing or presentation policy

That future work should not block the current messaging and documentation effort.

### 3. Command words remain stable

The current language/locale effort should not attempt to localize the command language itself.

Keep command keywords stable:

- `HELP`
- `USE`
- `SELECT`
- `SET`
- `DO`
- `WORKSPACE`

Localized output text is acceptable. Localized command grammar is a different problem and should be treated separately if ever pursued.

### 4. Educational documents are the high-value multilingual target

The strongest near-term multilingual investment should be:

- manuals
- educational documentation
- guided explanations
- curated help topics intended for learning

This best matches the educational purpose of the project and extends audience reach without destabilizing the runtime.

## Priority Order

### Priority 1

Keep English as the authoritative source language for:

- source code
- command contracts
- maintenance doctrine
- catalog identifiers
- default runtime text

### Priority 2

Use the messaging/locale spine for:

- basic runtime fallback
- core operator-facing messages
- locale selection proof
- catalog validation

### Priority 3

Apply real multilingual effort to educational outputs:

- manualgen publications
- documentation sets
- selected HELP material
- onboarding/tutorial content

### Priority 4

Defer broad region/culture formatting until later:

- full date/number/currency policy
- locale-sensitive parsing
- command-language localization

## Practical Rule for x64base

For `x64base`, it is acceptable if the runtime remains primarily English plus a small localized core for operational messages.

It is desirable if the educational/documentation surfaces become multilingual sooner:

- manuals in multiple languages
- translated documentation artifacts
- translated learning/help content where curated

That is a better use of effort than translating every runtime status line in the current phase.

## Practical Rule for dottalkpp Repo Runtime

For the full repo/runtime tree, the messaging lane should continue to mature as the system spine for:

- locale normalization
- fallback policy
- message identity
- placeholder validation
- proof/check/report surfaces

But this should still be done in stages, not as a forced all-at-once rewrite of every hard-coded string.

## Data and Schema Direction

Current live seed tables already justify continuing the lane:

- `SYSTEM_MESSAGES`
- `SYSTEM_MESSAGE_TEXT`
- `SYSTEM_LOCALES`
- `SYSTEM_LOCALE_FALLBACK`

Future x64base-oriented schema work can continue around:

- `MSGDEF`
- `MSGTEXT`
- `MSGARG`
- `MSGUSE`
- `MSGLANG`
- `MSGRUN`
- `MSGGATE`
- `MSGREVIEW`

But manual/document translation should not wait for a perfect runtime-wide message conversion.

## Manual and Documentation Guidance

Manual/document localization should follow this discipline:

- English source remains authoritative
- translated editions are derivative publications
- translation status must be explicit
- fallback to English is acceptable when a translated section is missing
- educational clarity matters more than literal UI-string coverage

This supports a larger educational audience without tying manual availability to the runtime’s current localization maturity.

## Non-Goals for This Phase

This note does not authorize:

- full runtime translation of every command
- localization of command keywords
- region-aware parsing changes
- currency/date formatting overhaul
- broad source-string replacement
- publication mutation by itself

It is a boundary note, not an apply package.

## Recommended Next Steps

### Messaging

- continue using `SET LANGUAGE` / `SET LOCALE` as the current message-locale selector
- keep the core message catalog report/check path read-only and testable
- localize only essential runtime/operator messages first

### Manuals and docs

- define which manualgen outputs are translation candidates first
- treat manuals and learning/help documents as the primary multilingual audience surface
- record translation coverage and fallback rules per publication

### Region

- capture a separate future note for date/number/currency formatting policy
- do not overload the messaging lane with full culture/formatting scope yet

## Bottom Line

Language, region, and documentation translation must not be treated as the same milestone.

For now:

- runtime language support should stay basic and operational
- region behavior should remain deferred
- multilingual manuals and educational documentation should be the primary audience-expansion target

That keeps the runtime stable while still extending DotTalk++ / x64base to a broader educational audience.
