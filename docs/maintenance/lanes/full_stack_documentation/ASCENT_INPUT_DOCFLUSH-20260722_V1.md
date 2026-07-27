# Ascent input -- what DOCFLUSH-20260722-001 must re-publish (by page kind)

- **Status**: ascent input / selective-merge review (gate 1), source-evidenced
- **Recorded**: 2026-07-27 (Cowork)
- **Predecessor**: `DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md` (DOCFLUSH-20260716-001, all
  9 gates PASS, live at x64base.com). This is the delta for the NEXT ascent.

> The manual comes before the web (member.derald): the manual regenerates from the
> normalized catalogs first; the web then consumes reviewed manual/catalog evidence.
> The site has three page KINDS, and each reacts differently to this flush -- which is
> what keeps the re-ascent surgical.

## The SelfDoc pipeline (BBOX lanes) -- where this flush enters the manual

The self-documentation system is seven black boxes (`BBOX LANES`), each
`data -> process -> information`. The manual is NOT regenerated straight from
`SYSCMD`/`SYSFUNC`; the catalog changes flow through the HELP lane first, then the
MANUALGEN lane assembles the manual, then the web ascent consumes it:

```
HELP lane        registry + DOTREF/FOXREF/EDREF + @dottalk.usage  --CMDHELP BUILD-->  HELP DATA
MANUALGEN lane   section files + appendices + media + manifests   --assemble-->       MAN* catalog + published manual
WEB ascent       published manual                                 --gates 6-9-->      static / data-driven / stamp pages
```

`BBOX MANUALGEN` states the manualgen box exactly:

```
DATA IN: section files, appendices, media anchors, review queues, manifests
PROCESS: assemble, normalize, validate, publish, catalog, runtime smoke
OUT:     published manual, MAN* catalog, MANUAL runtime command, regeneration evidence
```

So the manual's DATA-DRIVEN sections (command + function reference) are sourced from
HELP DATA, and the regen order is fixed:

1. **`CMDHELP BUILD`** -- refresh HELP DATA from the normalized catalogs (re-mines
   `registry U foxref U dotref U edref U usage-contracts`). This is where the five new
   functions, `SIMPLEBROWSER`/`SMARTBROWSER`, and the 212-row command set enter the
   pipeline. (Run 2026-07-27, ~minutes.)
2. **MANUALGEN** -- assemble / normalize / validate / publish / catalog / runtime-smoke
   the refreshed reference sections + the unchanged static sections -> new MAN* catalog
   and published manual.
3. **WEB ascent** (gates 6--9) -- consume the new manual; only the data-driven pages and
   the version stamp move.

Because the static manual sections and appendices do not change, both the MANUALGEN
assembly and the web feed packet stay small -- the payoff of the pipeline being
lane-separated.

## Page kinds and how this flush touches each

| kind | what it is | changed by this flush? |
|---|---|---|
| **static** | hand-authored site prose (intro, about, portal), no catalog derivation | **NO** -- do not touch |
| **data-driven** | generated FROM the catalogs (command reference, function reference) | **YES** -- regenerate; this is where the normalization flows to the web |
| **stamp** | one canonical URL updated in place (build/compile instructions, version) | **maybe** -- re-stamp only if the stamped fact changed |

## DATA-DRIVEN pages -- regenerate (the substance of this ascent)

These derive from `SYSCMD` / `SYSFUNC` / the `*ref` catalogs, all of which changed and
are now normalized (`normcheck`/`refcheck` green). The manual's command- and
function-reference sections regenerate first, then the site's data-driven pages follow.

1. **Function reference.** SYSFUNC 69 -> **74**: five FoxPro string functions now
   implemented and catalogued -- `STUFF`, `PADL`, `PADR`, `PADC`, `PROPER`
   (`fn_string.cpp`, runtime-proven `PROPER("john smith")="John Smith"`, etc.). The
   function-reference page must gain these five rows.
2. **Command reference.** SYSCMD 214 -> **212**, and the browser identity corrected:
   the dead `SIMPLEBROWSE`/`SMARTBROWSE` names are gone; `SIMPLEBROWSER`/`SMARTBROWSER`
   are the registered spellings (dotref/foxref already carry them). FOXREF is now a
   reference module, not a command (0 identity errors). The command-reference page must
   reflect the corrected names and the 212-row set.
3. **Provenance/labels.** Anything the site renders from the catalog carries new
   source anchors (this flush's commit) and proof labels.

## STAMP pages -- re-stamp only if the fact changed

- **Version/build stamp.** `v0.6`, new commit (the session's pushes). Re-stamp.
- **Compile/build instructions.** UNCHANGED this flush -- no build-step change (the
  five functions and the guards did not alter how the project is built). Do NOT
  re-stamp; the canonical page stays.
- **Developer-tooling / maintenance stamp (if one exists).** New this flush: the
  `refcheck` + `normcheck` catalog-drift guards, now wired into the prepush gate. If
  the site documents the dev gates, that stamp updates once; otherwise no site change.

## STATIC pages -- no change

No hand-authored site prose changed. Explicitly listed so the ascent does not
re-touch static routes (gate rule 3: website prose does not flow backward as
authority, and unchanged static pages are not re-published).

## Owed before the manual regen (precursors, not web work)

- **Harvest feeder -- DONE 2026-07-27.** The HELP/META CSV harvest (manualgen's
  input) is regenerable again via `HELP_META_HARVEST_EXPORT_v1.{dts,ps1}`; run
  `HELPMETA-20260727T233835Z` carries the current 10 tables (SYSCMD 212, SYSFUNC
  74, the five functions, the browser rename, 28k current HELP lines). The 4 stale
  `META_*` (SYSENTVAR/SYSFLDDIC/SYSHELP/SYSMSG) are carried-labelled and remain
  owed. See `docs/maintenance/SESSION_CLOSEOUT_HELP_META_HARVEST_FEEDER_2026-07-27.md`.
- **DDICT** PDLC turnover (still excluded from SYSCMD; a manual gap by design until
  repaired -- note it, do not block).
- **Browser `@dottalk.usage` contracts** on the repair list (register `SIMPLEBROWSER`/
  `SMARTBROWSER` in `command:` so they re-enter SYSCMD and the command-reference page;
  otherwise they publish as registered-but-uncatalogued).
- **3 HELP gaps** (`BBS`/`CANARY`/`NET`) -- generator closes; minor.

## The ascent path from here (which gates re-run)

Gate 1 (this review) done. Next: regenerate the manual command/function reference from
the normalized catalogs (gates 2--4, manualgen, runtime), re-promote to `C:\x64base`
(gate 5), rebuild the website feed packet for ONLY the data-driven + changed-stamp
routes (gate 6, `build_website_feed_packet.py`), integrate + build the site (gate 7,
`D:\dev\x64base-site`), publish (gate 8, GitHub Pages), live-verify (gate 9). Static
routes carry through untouched, so the packet is a small, surgical set -- the payoff of
sorting by page kind.
