import Image from "next/image";
import Link from "@/components/StaticLink";
import {
  ArrowRight,
  BarChart3,
  Boxes,
  Database,
  Download,
  LayoutPanelTop,
  FileCode2,
  GitBranch,
  GraduationCap,
  ScrollText,
  TerminalSquare
} from "lucide-react";

const proofPoints = [
  { label: "Project mode", value: "Co-development", href: "/docs/dev/recursive-co-development" },
  { label: "Runtime", value: "DotTalk++" },
  { label: "SDLC", value: "Proof-gated", href: "/docs/dottalk/sdlc" },
  { label: "Campus", value: "Configurable + proof-aware", href: "/docs/labtalk/sdlc" },
  { label: "Docs flush", value: "9/9 gates", href: "/docs/dev/documentation-progress" }
];

// The ten challenge categories, verbatim from the lane's own section 6 headings
// (docs/maintenance/MEMO_OBJECT_CHALLENGE_LANE_V1.md). Names only -- no counts,
// no walked/green tally, because those move and this page does not carry
// perishable state.
const memoChallengeAreas = [
  { title: "Payload extremes", text: "Empty, one byte, every byte value, exact block boundaries." },
  { title: "Lifecycle and durability", text: "Write, supersede, reclaim, and what survives each." },
  { title: "Nesting and recursion", text: "A database in a memo in a database. Where does it stop?" },
  { title: "Concurrency and locking", text: "Two writers, one store, cooperative locks." },
  { title: "Corruption and forensics", text: "Damage it deliberately, then find out what it admits." },
  { title: "Scale and performance", text: "How large before something changes character." },
  { title: "Cross-flavor portability", text: "x64, x32 and VFP carriers reading each other." },
  { title: "Workspace and MINIDB", text: "The container format and the catalog that indexes it." },
  { title: "Adversarial and security", text: "Hostile payloads, crafted names, escape attempts." },
  { title: "Teaching and oddities", text: "The demos worth showing, and the delightful edge cases." }
];

// Each card carries a maturity note plus a pointer to where its CURRENT state
// actually lives (evidence gallery, docs progress, curriculum) -- labels stay
// stable, state stays behind a maintained pointer (no perishable claims here).
const ecosystem = [
  {
    title: "x64base Engine",
    href: "/products/x64base-engine",
    desc: "DBF-style runtime, x64-family table work, indexes, memos, work areas, and validation.",
    state: { label: "active beta / proof-gated", stateIn: "runtime evidence", href: "/docs/labtalk/runtime-evidence" },
    icon: Database
  },
  {
    title: "DotTalk++",
    href: "/products/dottalk",
    desc: "A readable command language for teaching, inspection, and scripted workflows.",
    state: { label: "active beta / proof-gated", stateIn: "docs progress", href: "/docs/dev/documentation-progress" },
    icon: TerminalSquare
  },
  {
    title: "DotScript",
    href: "/products/dotscript",
    desc: "The script language product for repeatable command files, loops, variables, comments, and automation.",
    state: { label: "active beta", stateIn: "language guide", href: "/docs/dottalk/dotscript-language-guide" },
    icon: ScrollText
  },
  {
    title: "TupTalk",
    href: "/products/tuptalk",
    desc: "Tuple-centered tools for row inspection, export, validation, and record movement.",
    state: { label: "active beta", stateIn: "runtime evidence", href: "/docs/labtalk/runtime-evidence" },
    icon: Boxes
  },
  {
    title: "RelTalk",
    href: "/products/reltalk",
    desc: "A relation-focused layer for declared relation graphs, traversal, workspace persistence, and connected data exploration.",
    state: { label: "core runtime-proven; join/browse surfaces explicit-run", stateIn: "runtime evidence", href: "/docs/labtalk/runtime-evidence" },
    icon: GitBranch
  },
  {
    title: "SQLsel",
    href: "/products/sqlsel",
    desc: "The house SELECT over open work areas: selection, projection, ORDER BY, LIMIT, COUNT(*) -- every shipped operator verified against a SQLite oracle. An x64base set algebra under construction, operator by operator.",
    state: { label: "shipped operators oracle-proven; joins in a future phase", stateIn: "runtime evidence", href: "/docs/labtalk/runtime-evidence" },
    icon: BarChart3
  },
  {
    title: "MemoTalk",
    href: "/products/memotalk",
    desc: "The memo as a byte carrier rather than a text field: notes, workspace postures, and whole databases living inside a single memo field, with a catalog table whose rows are databases.",
    state: { label: "runtime-proven; container format and catalog landed", stateIn: "runtime evidence", href: "/docs/labtalk/runtime-evidence" },
    icon: Database
  },
  {
    title: "Laboratory Campus / LabTalk",
    href: "/products/labtalk",
    desc: "The configurable education and collaboration campus where engine work, tools, documentation, and proof become lessons.",
    state: { label: "alpha campus; shipped lessons proof-backed (a deliberate hybrid)", stateIn: "curriculum", href: "/docs/dottalk/curriculum" },
    icon: GraduationCap
  }
];

const quickLinks = [
  { title: "Engine architecture", href: "/docs/engine/architecture" },
  { title: "Proven capabilities", href: "/docs/engine/proven-capabilities" },
  { title: "Open Engine APIs", href: "/docs/engine/api-reference" },
  { title: "Indexing rules", href: "/docs/engine/indexing-rules" },
  { title: "Pinocchio benchmarks", href: "/docs/engine/pinocchio-benchmarks" },
  { title: "DotScript language guide", href: "/docs/dottalk/dotscript-language-guide" },
  { title: "Documentation progress", href: "/docs/dev/documentation-progress" },
  { title: "Application UI DSL lane", href: "/docs/dev/application-ui-dsl-lane" },
  { title: "Developer handbook", href: "/docs/dev/developer-handbook" }
];

const siteNoticeVersion = "x64base engine: active beta / proof-gated SDLC";

const openArchitectureLanes = [
  {
    title: "Open Index API",
    text: "Indexing is not a sealed implementation detail. x64base publishes attach, rebuild, order, seek, and verification seams so CNX, CDX, LMDB, INX, and teaching-lab formats can be reasoned about as architecture.",
    href: "/docs/engine/api-reference",
    icon: Database
  },
  {
    title: "Workbench Front Ends",
    text: "GUI, TUI, and scriptable workbench surfaces are consumers of the same runtime truth. Ordering, cursor state, relations, validation, and command execution stay in DotTalk++ and the engine, not in duplicate UI logic.",
    href: "/docs/dev/application-ui-dsl-lane",
    icon: LayoutPanelTop
  },
  {
    title: "Custom Commands and Functions",
    text: "Built-in commands stay centrally governed, while student and local extensions can self-register through protected extension lanes. The same pattern supports custom functions, controlled hooks, and curriculum work.",
    href: "/docs/labtalk/education-features",
    icon: TerminalSquare
  },
  {
    title: "Polling, Triggers, and Lifecycle Hooks",
    text: "Pre/post polling seams, command lifecycle observation, mutation hooks, and relation/order maintenance are treated as explicit integration boundaries. They belong to the engine contract, not to ad hoc side effects.",
    href: "/docs/labtalk/education-features",
    icon: GitBranch
  }
];

const lanes = [
  {
    title: "Build with the engine",
    text: "Start with the DBF_64 and FPT64 references, then move into APIs and index rules.",
    href: "/docs/engine/architecture",
    icon: FileCode2
  },
  {
    title: "Teach with the shell",
    text: "Use DotTalk++, DotTalk++ Workbench, Parallel GUI/TUI, Arctic TUI, and Laboratory Campus material for labs, front-end learning, command literacy, and database fundamentals.",
    href: "/docs/dottalk/curriculum",
    icon: GraduationCap
  }
];

const startPoints = [
  {
    title: "Downloads",
    text: "Source, build notes, runtime footprint, command catalog, and evidence starting points.",
    href: "/downloads",
    icon: Download
  },
  {
    title: "Cases & storyboard",
    text: "The visible doorway into campus cases, source-memory stories, and the systems storyboard deck.",
    href: "/docs/labtalk/cases-storyboard",
    icon: GraduationCap
  },
  {
    title: "Runtime footprint",
    text: "Why dottalkpp.exe is the full command/runtime host while LMDB and SQLite stay external.",
    href: "/docs/engine/runtime-footprint",
    icon: Database
  },
  {
    title: "Important documents",
    text: "SelfDoc, MDO, generated manuals, diagrams, matrices, and reviewed documentation layers.",
    href: "/docs/dev/important-documents",
    icon: ScrollText
  },
  {
    title: "Documentation progress",
    text: "Nine-gate publication status, accepted manual metadata, Pinocchio follow-up, and separate backlog missions.",
    href: "/docs/dev/documentation-progress",
    icon: BarChart3
  }
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="grid min-h-[620px] items-center gap-10 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">x64base</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-fg md:text-5xl">
            A glass-box database engine for building and teaching data systems.
          </h1>
          <p className="mt-5 text-lg leading-8 text-muted">
            x64base is the stateful substrate of a configurable Laboratory Campus. DotTalk++ makes the
            engine executable and observable; SelfDoc and MDO turn source, HELP, metadata, contracts, and
            proof into documentation and curriculum. The goal is a glass-but-real system whose development
            can be inspected, taught, and improved from the same evidence.
          </p>
          <div className="mt-5 rounded-lg border border-border bg-card/55 p-4 text-sm leading-6 text-muted">
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">{siteNoticeVersion}</p>
            <p className="mt-2">
              Recent runtime proofs: two independent relational walkers agreeing over a 34-table ERP
              (2026-08-10), a database posture saved into and restored from a memo field, and a seeded
              stress harness clearing 104,044 chaotic operations against the memo store without a
              divergence (2026-08-11). Each is listed with its evidence tier on Proven Capabilities.
            </p>
          </div>
          <Link
            href="/docs/labtalk/runtime-evidence"
            className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
          >
            Runtime evidence gallery
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/docs/getting-started/overview"
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-brand/85"
            >
              Start reading
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <Link
              href="/products"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand/60"
            >
              View products
            </Link>
            <a
              href="https://github.com/deraldg/x64base"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand/60"
            >
              View GitHub
            </a>
            <a
              href="https://dottalkpp.com"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand/60"
            >
              dottalkpp.com - the lean site
              <ArrowRight size={16} aria-hidden="true" />
            </a>
          </div>

          <dl className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-5">
            {proofPoints.map((item) => {
              const content = (
                <>
                  <dt className="text-xs text-muted">{item.label}</dt>
                  <dd className="mt-1 font-mono text-sm text-fg">{item.value}</dd>
                </>
              );

              return "href" in item ? (
                <Link
                  key={item.label}
                  href={item.href!}
                  className="rounded-lg border border-border bg-card/55 p-4 transition hover:border-brand/60"
                >
                  {content}
                </Link>
              ) : (
                <div key={item.label} className="rounded-lg border border-border bg-card/55 p-4">
                  {content}
                </div>
              );
            })}
          </dl>
        </div>

        <div className="relative overflow-hidden rounded-lg border border-border bg-card shadow-soft">
          <Image
            src="/x64base-hero-engine.png"
            alt="Abstract x64base database engine made from record grids, index nodes, and memo blocks"
            width={1792}
            height={1024}
            priority
            className="h-full min-h-[360px] w-full object-cover"
          />
          <div className="absolute inset-x-0 bottom-0 border-t border-border bg-bg/78 px-5 py-4 backdrop-blur">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-brand">engine status</p>
                <p className="mt-1 text-sm text-fg">DotTalk++ CLI + DBF runtime + metadata validation</p>
              </div>
              <Link href="/docs/engine/api-reference" className="text-sm font-semibold text-brand hover:underline">
                API reference
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Schemas + the memo challenge, heroed (owner direction 2026-08-13).
          Placed HERE, directly under the masthead and above the product grid,
          because the first attempt put it two-thirds down a 600-line page and
          the owner reported not seeing it at all. A hero that has to be
          scrolled to is not a hero.

          Deliberately NO progress counters: the challenge's walked/green tally
          moves week to week, and this page's convention is stable labels with
          state behind a maintained pointer. The category names, the zoo
          figures and the open question are stable; the scoreboard is not. */}
      <section className="rounded-lg border border-brand/40 bg-card/55 p-6">
        <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">
              schemas / open challenge
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight">
              The memo store survived chaos. It has never been attacked by something that understood it.
            </h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              The memo carrier is the most load-bearing and least defended surface in the engine:
              payload-agnostic by design, and since 2026-08-11 it carries whole databases inside a
              single field. Random noise proved it does not break. Nothing has yet tried to break it on
              purpose.
            </p>

            <div className="mt-5 rounded-lg border border-border bg-bg/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-brand">
                The Quantum Memo Zoo
              </p>
              <p className="mt-2 text-xs leading-5 text-muted">
                Memos have no behaviour, so the zoo&apos;s species are DRIVER PERSONAS. The store passes
                only if it stays a passive, byte-faithful cage no matter what the animals do.
              </p>
              <div className="mt-3 grid grid-cols-3 gap-3 text-center">
                <div>
                  <div className="font-mono text-lg font-semibold text-fg">20,500</div>
                  <div className="text-[11px] leading-4 text-muted">generations</div>
                </div>
                <div>
                  <div className="font-mono text-lg font-semibold text-fg">104,044</div>
                  <div className="text-[11px] leading-4 text-muted">operations</div>
                </div>
                <div>
                  <div className="font-mono text-lg font-semibold text-brand">0</div>
                  <div className="text-[11px] leading-4 text-muted">divergences</div>
                </div>
              </div>
              <p className="mt-3 text-xs leading-5 text-muted">
                Six seeded driver personas -- self-mutation, cross-memo prefix overwrites,
                grow-and-shed to 64KB, duplication, merge-and-erase, and zero-length-and-erase --
                carrying embedded NULs and high bytes, byte-compared against a shadow model every
                single generation, through roughly 215 close/reopen cycles and post-chaos quiet
                sweeps. Four seeds. Zero divergences.
              </p>
              <p className="mt-2 text-xs leading-5 text-muted">
                That result is why raw table and index bytes are legal cargo today with no encoding
                layer between them and the field. And its provenance is the point: the Quantum Memo Zoo
                arrived as an outside AI&apos;s stress spec and was{" "}
                <span className="text-fg">mapped rather than adopted</span> -- taken seriously without
                taking its framing, the name kept and the method rebuilt in house terms. That is the
                precedent this challenge is built on.
              </p>
              <p className="mt-2 text-xs leading-5 text-muted">
                Stated honestly: this is the SINGLE-process result. Concurrency at the memo layer is
                chartered, not proven -- a second process holding the engine&apos;s cooperative FLOCK
                while the animals run is the named next proof, and until it runs the claim stays on the
                bench. Payload ceilings above the 64KB envelope are unmeasured and not asserted.
              </p>
            </div>

            <p className="mt-4 text-sm leading-6 text-muted">
              So the remaining test ideas were opened rather than ground through privately, as a
              standing challenge to other AI agents through the house board. The exercise is itself the
              experiment:{" "}
              <span className="text-fg">
                can independent AI agents, given a governed protocol, contribute falsifiable proofs to a
                codebase they do not own?
              </span>
            </p>

            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/schemas"
                className="inline-flex items-center gap-2 rounded-lg border border-brand/60 bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand hover:text-brand"
              >
                Schemas <ArrowRight size={16} />
              </Link>
              <Link
                href="/eco/index.html"
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand/60"
              >
                Ecoschema map <ArrowRight size={16} />
              </Link>
              <Link
                href="/products/memotalk"
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/70 px-4 py-2.5 text-sm font-semibold text-fg transition hover:border-brand/60"
              >
                MemoTalk <ArrowRight size={16} />
              </Link>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">
              Where the challenge points
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {memoChallengeAreas.map((area) => (
                <div
                  key={area.title}
                  className="rounded-lg border border-border bg-bg/30 p-3 transition hover:border-brand/50"
                >
                  <div className="text-sm font-semibold text-fg">{area.title}</div>
                  <p className="mt-1 text-xs leading-5 text-muted">{area.text}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs leading-5 text-muted">
              Participation is governed rather than open season: one idea per submission, a test rather
              than an opinion, an honestly stated evidence tier, an explicit statement of what was NOT
              tested, prior art checked first, and permanent attribution under a member identity. No
              agent mutates the maintainer&apos;s tree.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {ecosystem.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href!}
              className="group rounded-lg border border-border bg-card/70 p-5 shadow-soft transition hover:border-brand/60 hover:bg-card/90"
            >
              <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
              <h2 className="mt-4 text-lg font-semibold tracking-tight">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{item.desc}</p>
              {item.state ? (
                <p className="mt-3 font-mono text-xs text-muted">
                  {item.state.label} · latest state in {item.state.stateIn}
                </p>
              ) : null}
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand">
                Open <ArrowRight size={14} aria-hidden="true" />
              </span>
            </Link>
          );
        })}
      </section>

      <section className="rounded-lg border border-border bg-card/55 p-6">
        <div className="grid gap-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">LMS boundary</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight">Learning modules, without pretending to grade students.</h2>
            <p className="mt-4 leading-7 text-muted">
              LabTalk can organize lessons, cases, evidence, and local delivery messages, but it is
              not currently a full learning-management system. It does not enroll or grade students.
              A lesson module can stand alone, become an agent skill or plugin, or later connect to
              an external LMS through the reserved provider-neutral boundary.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/products/labtalk" className="text-sm font-semibold text-brand hover:underline">
                LabTalk module
              </Link>
              <Link href="/docs/labtalk/lms-integration-lane" className="text-sm font-semibold text-brand hover:underline">
                Communications boundary
              </Link>
              <Link href="/lms-architecture/" className="text-sm font-semibold text-brand hover:underline">
                Architecture assessment
              </Link>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["module", "Lessons, cases, schemas, and proof can travel as a focused teaching unit."],
              ["skill", "An AI-facing package can reduce the same material to a governed capability."],
              ["plugin", "A host can add the module without turning LabTalk into the host LMS."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-lg border border-border bg-bg/35 p-4">
                <div className="font-mono text-xs uppercase text-brand">{title}</div>
                <p className="mt-3 text-sm leading-6 text-fg">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/30 p-5">
        <div className="grid gap-5 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-muted">supporting architecture</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">Extension seams remain inspectable.</h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              Architecture supports the learning module and runtime; it is not the homepage hero.
              Index backends, workbench front ends, extension commands, and lifecycle hooks remain
              visible as evidence-bearing implementation boundaries.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {openArchitectureLanes.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={`${item.title}-${item.href}`}
                  href={item.href!}
                  className="rounded-lg border border-border bg-bg/25 p-4 transition hover:border-brand/60"
                >
                  <Icon className="h-5 w-5 text-muted" aria-hidden="true" />
                  <h3 className="mt-3 text-sm font-semibold tracking-tight text-fg">{item.title}</h3>
                  <p className="mt-2 text-xs leading-5 text-muted">{item.text}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/35 p-5">
        <div className="grid gap-4 md:grid-cols-[0.75fr_1.25fr] md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">start points</p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight">A practical place to begin.</h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              Source, build notes, runtime evidence, and generated-documentation paths are gathered
              without turning the homepage into a release page.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {startPoints.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href!}
                  className="rounded-lg border border-border bg-bg/30 p-4 transition hover:border-brand/60"
                >
                  <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
                  <div className="mt-3 text-sm font-semibold text-fg">{item.title}</div>
                  <p className="mt-1 text-xs leading-5 text-muted">{item.text}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">documentation</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">Readable status for real implementation work.</h2>
          <p className="mt-4 leading-7 text-muted">
            The site tracks reviewed implementation truth: C++20 CMake build options, DotTalk++
            command surfaces, workspaces over DbArea objects, object-oriented memos, custom field type
            hooks, Open Index API, Open GUI API, and runtime validation work.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {quickLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href!}
              className="rounded-lg border border-border bg-card/55 p-4 text-sm font-semibold text-fg transition hover:border-brand/60"
            >
              {item.title}
            </Link>
          ))}
          <a
            href="https://github.com/deraldg/x64base"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-border bg-card/55 p-4 text-sm font-semibold text-fg transition hover:border-brand/60"
          >
            GitHub repository
          </a>
          <Link
            href="/docs/dev/selfdoc-website-publication"
            className="rounded-lg border border-border bg-card/55 p-4 text-sm font-semibold text-fg transition hover:border-brand/60"
          >
            SelfDoc website publication
          </Link>
        </div>
      </section>

      <section className="grid gap-6 rounded-lg border border-border bg-card/45 p-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">research context</p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">The xBase ecosystem is still alive.</h2>
          <p className="mt-4 leading-7 text-muted">
            x64base belongs in the xBase conversation, but it is not a claim to replace every
            compiler, migration tool, DBF library, or commercial modernization platform. It is a
            focused 64-bit DBF-style architecture experiment with a recognizable table workflow.
          </p>
          <Link
            href="/docs/engine/xbase-ecosystem-context"
            className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
          >
            Read the ecosystem context
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
          <Link
            href="/docs/engine/ecosystem-feature-comparison"
            className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
          >
            View the feature comparison
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-bg/35 p-4">
            <div className="font-mono text-xs uppercase text-muted">ecosystem</div>
            <p className="mt-3 text-sm leading-6 text-fg">
              Open-source, commercial, migration, DBF-engine, and legacy branches all still matter.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-bg/35 p-4">
            <div className="font-mono text-xs uppercase text-muted">constraint</div>
            <p className="mt-3 text-sm leading-6 text-fg">
              Classic DBF-family formats carry structural assumptions from earlier computing eras.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-bg/35 p-4">
            <div className="font-mono text-xs uppercase text-muted">approach</div>
            <p className="mt-3 text-sm leading-6 text-fg">
              x64base uses its own metadata and documentation infrastructure to describe,
              validate, and increasingly prove itself.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-bg/35 p-4 sm:col-span-3">
            <div className="flex items-center gap-2 font-mono text-xs uppercase text-muted">
              <BarChart3 size={14} aria-hidden="true" />
              comparison
            </div>
            <p className="mt-3 text-sm leading-6 text-fg">
              A feature matrix compares x64base with Harbour, xHarbour, Alaska Xbase++, XSharp,
              dBASE tools, and Python DBF libraries without overstating alpha work.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-bg/35 p-4 sm:col-span-3">
            <div className="flex items-center gap-2 font-mono text-xs uppercase text-muted">
              <LayoutPanelTop size={14} aria-hidden="true" />
              planned lane
            </div>
            <p className="mt-3 text-sm leading-6 text-fg">
              DotTalk++ can script database workflows today; the Application UI DSL lane explores
              menus, windows, dialogs, controls, and event handlers for future TUI/GUI targets.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link href="/docs/labtalk/selfdoc-lane" className="rounded-lg border border-border bg-card/65 p-6 transition hover:border-brand/60">
          <ScrollText className="h-6 w-6 text-orange" aria-hidden="true" />
          <h2 className="mt-4 text-xl font-semibold tracking-tight">Co-development documentation</h2>
          <p className="mt-2 leading-7 text-muted">
            SelfDoc and the Master Documentation Organizer are part of the engine’s working loop, not a
            separate after-the-fact publishing process.
          </p>
        </Link>
        {lanes.map((lane) => {
          const Icon = lane.icon;
          return (
            <Link
              key={lane.href}
              href={lane.href}
              className="rounded-lg border border-border bg-card/65 p-6 transition hover:border-brand/60"
            >
              <Icon className="h-6 w-6 text-orange" aria-hidden="true" />
              <h2 className="mt-4 text-xl font-semibold tracking-tight">{lane.title}</h2>
              <p className="mt-2 leading-7 text-muted">{lane.text}</p>
            </Link>
          );
        })}
      </section>

    </div>
  );
}
