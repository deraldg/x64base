<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RETRO

- Catalog/topic: `DOT` / `RETRO`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display retro computer/system splash screens with system-specific terminal profiles.

## Status

- implemented=yes; supported=yes

## Syntax

- RETRO USAGE
- RETRO LIST
- RETRO LIST LONG
- RETRO STYLES
- RETRO MODES
- RETRO SHOW &lt;system&gt;
- RETRO SHOW &lt;system&gt; NATIVE
- RETRO SHOW &lt;system&gt; ASCII
- RETRO SHOW &lt;system&gt; LEGACY
- RETRO SHOW &lt;system&gt; STYLE &lt;style&gt;
- RETRO SHOW &lt;system&gt; NOCLEAR
- RETRO SHOW &lt;system&gt; NOCAPTION
- RETRO &lt;system&gt;
- RETRO &lt;system&gt; INFO
- RETRO HELP
- RETRO [USAGE|LIST|SHOW &lt;system&gt;|&lt;system&gt;|HELP]

## Usage

- RETRO USAGE
- RETRO LIST
- RETRO LIST LONG
- RETRO STYLES
- RETRO MODES
- RETRO SHOW &lt;system&gt;
- RETRO SHOW &lt;system&gt; NATIVE
- RETRO SHOW &lt;system&gt; ASCII
- RETRO SHOW &lt;system&gt; LEGACY
- RETRO SHOW &lt;system&gt; STYLE &lt;style&gt;
- RETRO SHOW &lt;system&gt; NOCLEAR
- RETRO SHOW &lt;system&gt; NOCAPTION
- RETRO &lt;system&gt;
- RETRO &lt;system&gt; INFO
- RETRO HELP

## Argument

- NOCLEAR
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.
- NOCAPTION
- NOCLS

## Example

- RETRO C64
- RETRO C64 ASCII NOCLEAR
- RETRO C64 STYLE GREEN
- RETRO IBMPC NATIVE
- RETRO IBMPC STYLE MDA
- RETRO VT100
- RETRO AMIGA NATIVE
- RETRO GBC NATIVE
- RETRO PS2 NATIVE
- RETRO XBOX NATIVE
- RETRO C64 INFO

## Note

- NATIVE uses a system-specific profile and default ANSI style.
- ASCII uses the system-specific plate without ANSI color.
- LEGACY uses the older framed catalog plate where available.
- STYLE overrides the NATIVE default color treatment.
- NOCLEAR is useful for DotScript logs, tests, and transcript capture.
- RETRO writes console output only and does not mutate table data.

## Related

- ABOUT
- TVISION

## Provenance

- Topic key: `DOT|RETRO`
- Included HELP rows: `57`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
