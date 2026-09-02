# DOCFLUSH-20260901-002 -- Gate 1, reference disposition record

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : REPORT-ONLY. No catalog, contract or registry was edited.
    motto     : normalize -- smooth -- improve

Phase 1 was run with the lane's own tools, in the cookbook's order, and no
crosswalk was hand-rolled. This gate is the first time Phase 1 has run since
DOCFLUSH-20260716-001.

## THE FINDING OF THIS GATE: Phase 1's default input is two months old

`build_reference_authority_crosswalk.py` defaults `--run-id` to
`DOCFLUSH-20260716-001` and reads its reference inventory from that run's
`evidence_inputs` in `selfdoc/reference_identity_authority_v1.json`, which names

    .../DOCFLUSH-20260716-001/reference_inventory/fullstack_reference_identity_inventory_v1.csv

Meanwhile `build_reference_identity_inventory.py` -- the step immediately before
it -- now emits the **v2** contract and writes
`fullstack_reference_identity_inventory_v2.csv` beside it. It takes no `--run-id`
at all.

**So the cookbook's Phase 1, run exactly as written, builds a fresh inventory and
then cross-walks the JULY one.** Nothing errors. Nothing warns. The manifest
records the path it used, which is the only reason this was visible.

Measured, the same crosswalk against each input:

    reference inventory      ALIGNED   REVIEW   CANDIDATE   rows
    v1  (2026-07-16)             168      139         286    593
    v2  (2026-09-01, today)      215       84         286    585

**55 review rows were an artifact of the stale default.** A reviewer working the
default output dispositions 139 rows by hand, of which 55 are already aligned in
the tree in front of them. That is the lane's own failure signature -- a fact
carried by copy rather than derived -- sitting inside the tool that exists to
detect it.

Not fixed here. The fix is a one-line default and it is a house-tool edit, which
by the owner's standing ruling is made when a mission closes and can be
back-verified, not mid-run off a hours-old finding. Two candidate shapes, for
whoever rules it:

  (a) have the crosswalk resolve the newest inventory contract present, so the
      inventory step's output is what the crosswalk step consumes by construction;
  (b) have `build_reference_identity_inventory.py` take `--run-id` / `--output-dir`
      and write into the CURRENT run directory, and let the crosswalk default to
      its own run. This is the stronger fix -- today the inventory step writes its
      output into a two-month-old run's directory no matter which run invokes it.

(b) also fixes a second oddity this run tripped over: v8's fresh inventory landed
in `runs/DOCFLUSH-20260716-001/reference_inventory/`. Run artifacts belong in
their own run.

**Everything below is measured against the v2 inventory**, bound explicitly with
`--reference-inventory`, and written to this run's own directory.

## Bindings

    inventory (v2)      B5A5B3EC92A39123D0F1DE2CB6FF07ED065B443FF1A59CED8298F14BAE86D728
    duplicates (v2)     A5F03920F7E6976531E12D1A14FFF03EE46E16BD434B01A77DA5EAC10D4A667A
    crosswalk csv       03C8271D66D81A72...  reference_phase/reference_identity_authority_crosswalk_v1.csv
    excluded csv        DAC572FCD672D8DB...  reference_phase/excluded_reference_topics_v1.csv
    dotref.hpp          6EC5E257CDA1CC66F082B9943E59D3FE6B1F602DAE4DED68C879CD9B99CC19E5
    foxref.hpp          82BD5CF8B55E5D7B6CBEAFE35BF5C7B1FCB5192B03D5F2634686AA6B6B1A7D39
    edref.hpp           69D86B3ECD869E2685ABDCA95CAE534FA309A5D5EE4F2F36169ADBCBA9613925
    usage catalog       0C092FBC655779D27395994198F17C85C881D9EFDD1C1BA942E4B85A1A2F71B8

    joined identities 323   static registry 255 rows / 245 unique   usage 221/215
    classification: ALIGNED_COMMAND 215, CURATED_REF_ONLY 54,
                    EDUCATIONAL_TOPIC 24, REGISTERED_REF_MISSING_USAGE 30

CSVs are regenerable and stay untracked; they are bound by SHA above.
Transcript: `reference_phase/disposition_recommendation_v1.txt`.

## Dispositions

84 REVIEW command rows plus 16 duplicate rows. The recommender auto-recommends
the deliberate structure and leaves the genuinely undecided:

    DELIBERATE_SUBFORM        19      FUNCTION_AUTHORITY        24
    DELIBERATE_ALIAS          12      FOXPRO_COMPAT_REFERENCE    8
    DELIBERATE_DUAL_HOME       7      EDUCATION_SURFACE          4
    EDUCATION_TOPIC            2      NEEDS_HUMAN_DISPOSITION    8
    dup: DELIBERATE_DUAL_HOME  6      dup: EDUCATION_SURFACE     3
    dup: CLI_EDU_VARIANT       2      dup: DELIBERATE_ALIAS      1
    dup: NEEDS_HUMAN_DISPOSITION 4

**ACCEPTED as deliberate structure**, per the plan's rule that aliases, subforms
and FoxPro compatibility references are design rather than drift: all rows above
except the 14 below. No downstream layer replaces any of them.

**14 rows carry to a human**, and they are not a random tail -- they are the
already-open rulings, arriving from a second direction:

    BUILD, BUILD INFO, BUILD VECTORS      AIF-131's family. BUILD INFO is also
                                          DOTREF_COV/SUBCOMMAND_ONLY -- typeable
                                          through the router, never independently
                                          registered, so no contract, no SYSCMD
                                          row, no HELP topic.
    ERROR CLEAR, ERROR STATUS, ERROR TEST AIF-134, runtime-proven 2026-08-27,
                                          ruling open: router or delete. Phase 1
                                          reaches the same three rows from the
                                          catalog side without being told to.
    DDICT                                 the block-form contract the cookbook
                                          names as the classic normalization case.
    SMTP                                  no rule matched; undecided.
    [registry] BBS, NET, SQLHELP          REG_POLICY/SPLIT_REGISTRATION: registered
                                          both in shell_commands.cpp and in their
                                          own TU, against that file's stated
                                          policy. Last writer wins, no diagnostic.
    [usage] PSHELL                        cmd_pshell.cpp:10 vs cmd_pshell_help.cpp:12
    [usage] ERP, IDX                      recommended CLI_EDU_VARIANT (cli/ vs edu/);
                                          accept unless the owner reads them as drift.

**AIF-134 does not need reopening and is not reopened.** What this gate adds is
independent arrival: the ruling that lane awaits is the same ruling Phase 1's
review queue cannot clear. Three instruments now name it -- `DEAD_REG` from the
registry, the runtime proof from the engine, and the disposition queue from the
catalog.

## E4 -- re-proven at this baseline, not inherited

    refcheck_v1   PASS   GUARDED phantoms (dotref+foxref) = 0
                         dotref 266 / 250 cmd / 2 fn / 14 sub
                         foxref 176 / 139 cmd / 29 fn / 8 sub
                         edref, pshell_ref, sql_ref phantoms are namespace-owned
                         devref empty by declaration
    normcheck_v1  PASS   0 findings in every fail-severity lane
                         REGISTRY 245  SYSCMD 212  HELP(*ref) 323  REFLECTION 28
                         IDENTITY 0, FN_IDENTITY 0 (both fail-severity)
                         functions: 75 implemented / 75 catalogued

Informational, not gated: 17 registered commands absent from SYSCMD (policy
exclusions); `command_catalog` curates 25/240 (10%) by design.

Both arms read source and catalogs, not the HELP store, so neither is affected by
the stale store recorded at Gate 0.5.

## Deferred, with evidence, to follow-up lanes

Genuine defects, named here and not fixed in a doc run:

    REG_POLICY/SPLIT_REGISTRATION   9 commands, dual-registered against policy
    REG_POLICY/WRAPPER_ASYMMETRY    DELETE and RECALL differ in whether they call
                                    relations_api::refresh_if_enabled(); which is
                                    live depends on static-init order, not a rule
    REG_POLICY/DUPLICATE_IN_HUB     EXAMPLE registered twice inside
                                    shell_commands.cpp (505, 614)
    DEAD_REG/REWRITTEN_BEFORE_DISPATCH  RELATIONS is rewritten by
                                    preprocess_for_dispatch before the registry is
                                    consulted, so the registration never fires
    SRCFILE_DRIFT                   60 tracked files absent from SRCFILE;
                                    15 SRCFILE rows no longer tracked

## Gate 1: CLOSED

Inventory built, crosswalk bound to today's inputs, every review row dispositioned
or escalated by name, E4 re-proven. Phase 2 is next and needs the engine.
