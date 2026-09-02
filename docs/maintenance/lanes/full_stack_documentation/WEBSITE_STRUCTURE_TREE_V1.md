# x64base-site -- structure map (DERIVED, do not hand-edit)

    generator  tools/fullstack_docs/build_website_tree.py
    joins      filesystem + website_content_manifest.yaml + git tracking
    regenerate whenever a page is added, removed, or reclassified

Every page below carries its MAINTENANCE CLASS, which decides how it may be
edited, and its TRACKING state. A page that is declared but untracked is a
defect, not a style: it resolves on one machine and nowhere else.

## Maintenance classes

| Class | Rule |
| --- | --- |
| `generated` | regenerated every push; NEVER hand-edit a generated region |
| `derived` | regenerate or review when its source evidence changes |
| `maintained` | hand-authored; review when the tracked subject changes |
| `maintained_current` | permanent route, replaceable present-state region |
| `reported` | append-only measurement with pinned provenance |
| `static` | website-owned copy; human review only |

## Content tree

```text
content/
|- about/                    6 page(s)
|  |- ai-assisted-history                                  reported            
|  |- brand-story                                          static              
|  |- contributors                                         static              
|  |- mission-vision                                       static              
|  |- origin-story                                         static              
|  |- timeline                                             static              
|- brand/                    4 page(s)
|  |- logo-concepts                                        static              
|  |- trademarks                                           static              
|  |- usage-guide                                          static              
|  |- visual-identity                                      static              
|- docs/                    100 page(s)
|  |- dev/application-ui-dsl-lane                          maintained          
|  |- dev/coding-standards                                 maintained          
|  |- dev/coined-vocabulary                                maintained          
|  |- dev/coined-vocabulary-index                          generated             <- tools/fullstack_docs/glossary_sync.py
|  |- dev/contribution-guide                               maintained          
|  |- dev/current-lanes                                    maintained_current  
|  |- dev/developer-handbook                               maintained          
|  |- dev/developer-manual                                 maintained_current  
|  |- dev/developer-profile                                maintained          
|  |- dev/documentation-progress                           maintained_current  
|  |- dev/experimental                                     maintained          
|  |- dev/full-stack-documentation-push                    maintained_current  
|  |- dev/help-message-selfdoc-dfd                         maintained          
|  |- dev/historical-family-tree                           reported            
|  |- dev/historical-source-files                          generated             <- tools/fullstack_docs/build_historical_source_museum.py
|  |- dev/historical-source-lineage                        reported            
|  |- dev/important-documents                              maintained          
|  |- dev/manual-assembly                                  maintained          
|  |- dev/naming-conventions                               maintained          
|  |- dev/onboarding-guide                                 maintained          
|  |- dev/project-truth                                    maintained_current  
|  |- dev/public-site-architecture                         maintained          
|  |- dev/recursive-co-development                         maintained          
|  |- dev/roadmap                                          maintained_current  
|  |- dev/selfdoc-feed-pipeline                            maintained          
|  |- dev/selfdoc-website-publication                      maintained          
|  |- dev/site-improvement-plan                            maintained          
|  |- dev/third-party-acknowledgements                     maintained          
|  |- dev/website-documentation-matrix                     maintained_current  
|  |- dottalk/command-catalog                              generated             <- tools/fullstack_docs/command_catalog_sync.py
|  |- dottalk/command-families                             generated             <- tools/fullstack_docs/command_catalog_sync.py
|  |- dottalk/command-reference                            generated             <- tools/manualgen
|  |- dottalk/curriculum                                   maintained          
|  |- dottalk/data-mutators                                derived             
|  |- dottalk/dotscript-language-guide                     derived             
|  |- dottalk/examples                                     maintained          
|  |- dottalk/function-catalog                             generated             <- tools/fullstack_docs/command_catalog_sync.py
|  |- dottalk/language-guide                               maintained          
|  |- dottalk/repl                                         derived             
|  |- dottalk/sdlc                                         maintained          
|  |- dottalk/set-family                                   derived             
|  |- dottalk/syntax                                       derived             
|  |- engine/acid-and-glass-box                            maintained          
|  |- engine/api-reference                                 derived             
|  |- engine/architecture                                  derived             
|  |- engine/cdx-lmdb-indexing                             derived             
|  |- engine/dbf-64-specification                          derived             
|  |- engine/dbf-flavors-and-indexes                       maintained          
|  |- engine/ecosystem-feature-comparison                  derived             
|  |- engine/error-codes                                   generated             <- fullstack error harvest
|  |- engine/feature-crosswalk                             derived             
|  |- engine/fpt64-memo-format                             derived             
|  |- engine/identity-security                             derived             
|  |- engine/in-memory-databases                           derived             
|  |- engine/indexing-rules                                maintained          
|  |- engine/messaging-and-localization                    generated             <- fullstack messaging harvest
|  |- engine/pinocchio-benchmarks                          reported            
|  |- engine/proven-capabilities                           maintained          
|  |- engine/python-integration                            derived             
|  |- engine/ram-dbf-vdisk                                 derived             
|  |- engine/regression-and-proof-testing                  maintained          
|  |- engine/runtime-footprint                             maintained          
|  |- engine/specifications                                maintained          
|  |- engine/sqlsel-and-sql-conformance                    derived             
|  |- engine/workspaces                                    maintained          
|  |- engine/x64-capacity-math                             derived             
|  |- engine/xbase-ecosystem-context                       maintained          
|  |- getting-started/faq                                  maintained          
|  |- getting-started/installation                         maintained          
|  |- getting-started/overview                             maintained          
|  |- getting-started/quickstart                           maintained          
|  |- labtalk/academic-positioning                         maintained          
|  |- labtalk/academic-start                               maintained          
|  |- labtalk/agent-sync                                   maintained_current  
|  |- labtalk/ai-portal                                    maintained          
|  |- labtalk/ai-portal-schemas                            maintained          
|  |- labtalk/career-lessons                               maintained          
|  |- labtalk/cases-storyboard                             maintained          
|  |- labtalk/current-work                                 maintained_current    <- tools/fullstack_docs/build_current_work_feed.py
|  |- labtalk/database-evolution                           maintained          
|  |- labtalk/education-features                           maintained          
|  |- labtalk/examples                                     maintained          
|  |- labtalk/lesson-records-fields-tables                 maintained          
|  |- labtalk/lessons                                      maintained          
|  |- labtalk/lms-integration-lane                         maintained          
|  |- labtalk/non-profit-guide                             maintained          
|  |- labtalk/overview                                     maintained          
|  |- labtalk/runtime-evidence                             reported            
|  |- labtalk/sdlc                                         maintained          
|  |- labtalk/selfdoc-lane                                 maintained          
|  |- labtalk/student-lessons                              maintained          
|  |- labtalk/suggest-a-lesson                             maintained          
|  |- talk-family/arctic                                   maintained          
|  |- talk-family/arctictalk                               maintained          
|  |- talk-family/parallel-gui-tui                         maintained          
|  |- talk-family/reltalk                                  maintained          
|  |- talk-family/sqlsel                                   maintained          
|  |- talk-family/tabletalk                                maintained          
|  |- talk-family/tuptalk                                  maintained          
|  |- talk-family/turbotalk                                maintained          
|- lab/                    3 page(s)
|  |- ai-portal-human-guide                                maintained             << UNTRACKED
|  |- experimental                                         maintained          
|  |- website-matrix-inspector                             maintained             << UNTRACKED
|- memory/                    3 page(s)
|  |- overview                                             maintained          
|  |- roadmap                                              maintained          
|  |- team-model                                           maintained          
|- news/                    19 page(s)
|  |- announcements/a-table-of-databases                   maintained          
|  |- announcements/bbs-concurrency-and-ollama-agent-designed maintained          
|  |- announcements/curriculum-update                      static              
|  |- announcements/developer-manual-gate5-published       static              
|  |- announcements/documentation-flush-pinocchio-progress static              
|  |- announcements/documentation-flush-v4-dev-tree-closeout maintained          
|  |- announcements/gptbase-advisor-bundle-derived         maintained          
|  |- announcements/message-catalog-and-locale-spine-promoted static              
|  |- announcements/regression-canary-lane-curated         static              
|  |- announcements/the-return-leg                         maintained          
|  |- announcements/tracking-console-write-path            maintained          
|  |- announcements/two-walkers-one-graph-cascade-milestone maintained          
|  |- announcements/website-local-preview-navigation-fixed maintained          
|  |- announcements/workspaces-in-memos-and-the-zoo        maintained          
|  |- announcements/wsl-and-wx-lanes-documented            static              
|  |- press-releases/launch-announcement                   static              
|  |- press-releases/manual-publication-refresh            static              
|  |- press-releases/open-architecture-doctrine-published  static              
|  |- press-releases/version-0-1                           static              
|- portal/                    2 page(s)
|  |- overview                                             maintained             << UNTRACKED
|  |- schemas                                              maintained             << UNTRACKED
|- products/                    12 page(s)
|  |- arctictalk                                           derived             
|  |- dotscript                                            derived             
|  |- dottalk                                              derived             
|  |- labtalk                                              derived             
|  |- memotalk                                             derived             
|  |- parallel-gui-tui                                     derived             
|  |- reltalk                                              derived             
|  |- sqlsel                                               derived             
|  |- tabletalk                                            derived             
|  |- tuptalk                                              derived             
|  |- turbotalk                                            derived             
|  |- x64base-engine                                       derived             
```

## Structures that are not pages

```text
app/                    Next.js routes. Buckets use catch-all [...slug];
                        /lab is [[...slug]] so the index emits as an EMPTY
                        optional slug -- both /lab and each child must build.
components/             React components (client components need hydration;
                        see start-ai.ps1 on :3000 vs :3002).
config/
|- nav.ts               top navigation
|- sidebars.ts          docs sidebar registration
|- analytics.ts, retro.ts
public/
|- artifacts/           THE AUTHORITIES the site binds to:
|  |- documentation-progress-v1.json   11 of 13 freshness contracts read this
|  |- current-work-v1.json             generated task feed
|  '- site-release.json                release stamp
|- downloads/current/   DEVELOPER_MANUAL_LATEST.json + staged manual
|- diagrams/            generated images; sources live in diagrams/
|- AI/, eco/            raw artifacts served as-is; NEVER hand-edit
'- images/              evidence screenshots, brand, story figures
scripts/                THE GATES. All run by `npm run build`:
|- check-diagrams.mjs           diagrams generated and current
|- check-public-content.mjs     public content policy
|- check-site-freshness.mjs     13 contracts; --self-test proves they bite
|- site-freshness-contracts.json  the contract definitions
|- check-opacity-scale.mjs      Tailwind opacity on-scale
|- clean-build-output.mjs       clears .next/out/dist
|- strip-local-only-output.mjs  removes lab/reports/retro/portal from out/
'- publish-github-pages.mjs     the ONLY publication route
diagrams/               .mmd / .drawio SOURCES, kept with their images
apache/                 alternate static host config
```

## Publication boundary -- EXPOSURE IS NOT THE SAME AS SUBJECT

`strip-local-only-output.mjs` removes these from the published build, and the
publisher ABORTS if any survives:

    lab  reports  retro  portal

They exist in the working tree and on the local preview; they must never reach
x64base.com. `/memory` and `/portal` are additionally excluded from the search
index via `data-pagefind-ignore`.

**TWO SURFACES CAN SHARE A SUBJECT AND HAVE OPPOSITE EXPOSURE.** This pair is
the one that catches people, and it caught the steward on 2026-09-02:

    /portal/overview, /portal/schemas          LOCAL ONLY. Stripped from the
                                               build, unlisted, noindex, absent
                                               from search. Working references.
    /docs/labtalk/ai-portal                    PUBLIC. Describes the same
    /docs/labtalk/ai-portal-schemas            subject for readers.

Same words in the route, opposite audiences. Read the maintenance class and
the strip list before describing a page's reach -- a page being about the AI
Portal says nothing about whether anyone outside can see it.

**AND THE SUBJECT ITSELF IS NARROWER THAN THE NAME SUGGESTS.** Owner, 2026-09-02:
the AI Portal is not promised in any product and is separate; there is no
student portal; the only portal offered is for LabTalk, as custom end-user
development work, and it is neither the house AI Portal nor the BBS. The public
page already states this -- "It is not a student portal for accessing an AI
service" -- and that sentence is load-bearing. Do not soften it.

## Counts

| Class | Pages |
| --- | ---: |
| `derived` | 30 |
| `generated` | 8 |
| `maintained` | 78 |
| `maintained_current` | 9 |
| `reported` | 5 |
| `static` | 19 |
| **total** | **149** |

## FINDINGS

- DECLARED BUT UNTRACKED, resolves on one machine only: `content/lab/ai-portal-human-guide.mdx`
- DECLARED BUT UNTRACKED, resolves on one machine only: `content/lab/website-matrix-inspector.mdx`
- DECLARED BUT UNTRACKED, resolves on one machine only: `content/portal/overview.mdx`
- DECLARED BUT UNTRACKED, resolves on one machine only: `content/portal/schemas.mdx`

