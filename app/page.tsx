import Image from "next/image";
import Link from "next/link";
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
  { label: "Project mode", value: "Co-development" },
  { label: "Runtime", value: "DotTalk++" },
  { label: "Documentation", value: "SelfDoc + MDO" },
  { label: "Architecture", value: "Open cross-platform" }
];

const ecosystem = [
  {
    title: "x64base Engine",
    href: "/products/x64base-engine",
    desc: "DBF-style runtime, x64-family table work, indexes, memos, work areas, and validation.",
    icon: Database
  },
  {
    title: "DotTalk++",
    href: "/products/dottalk",
    desc: "A readable command language for teaching, inspection, and scripted workflows.",
    icon: TerminalSquare
  },
  {
    title: "DotScript",
    href: "/products/dotscript",
    desc: "The script language product for repeatable command files, loops, variables, comments, and automation.",
    icon: ScrollText
  },
  {
    title: "TupTalk",
    href: "/products/tuptalk",
    desc: "Tuple-centered tools for row inspection, export, validation, and record movement.",
    icon: Boxes
  },
  {
    title: "RelTalk",
    href: "/products/reltalk",
    desc: "A relation-focused layer for joins, algebra, and connected data exploration.",
    icon: GitBranch
  },
  {
    title: "Laboratory Campus / LabTalk",
    href: "/products/labtalk",
    desc: "The education and collaboration campus for labs, proof-backed lessons, pycrud, and runtime evidence.",
    icon: GraduationCap
  }
];

const quickLinks = [
  { title: "Engine architecture", href: "/docs/engine/architecture" },
  { title: "Open Engine APIs", href: "/docs/engine/api-reference" },
  { title: "DotScript language guide", href: "/docs/dottalk/dotscript-language-guide" },
  { title: "Application UI DSL lane", href: "/docs/dev/application-ui-dsl-lane" },
  { title: "Developer handbook", href: "/docs/dev/developer-handbook" }
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
  }
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="grid min-h-[620px] items-center gap-10 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">x64base</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-fg md:text-6xl">
            A 64-bit database engine for the xBase lineage.
          </h1>
          <p className="mt-5 text-lg leading-8 text-muted">
            x64base is an open, cross-platform database architecture being built in co-development with
            its documentation system. The same runtime that develops DBF_64 tables, FPT64 memos, indexes,
            workspaces, APIs, and DotTalk++ also documents itself through SelfDoc and a Master
            Documentation Organizer.
          </p>
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
          </div>

          <dl className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {proofPoints.map((item) => (
              <div key={item.label} className="rounded-lg border border-border bg-card/55 p-4">
                <dt className="text-xs text-muted">{item.label}</dt>
                <dd className="mt-1 font-mono text-sm text-fg">{item.value}</dd>
              </div>
            ))}
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

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {ecosystem.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group rounded-lg border border-border bg-card/70 p-5 shadow-soft transition hover:border-brand/60 hover:bg-card/90"
            >
              <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
              <h2 className="mt-4 text-lg font-semibold tracking-tight">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{item.desc}</p>
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand">
                Open <ArrowRight size={14} aria-hidden="true" />
              </span>
            </Link>
          );
        })}
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
          <div className="grid gap-3 lg:grid-cols-4">
            {startPoints.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
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
              href={item.href}
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
            <div className="font-mono text-xs uppercase text-muted">thesis</div>
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

      <section className="rounded-lg border border-border bg-card/45 p-6 text-sm leading-6 text-muted">
        <p>
          x64base, xBase_64, DotTalk++, DotTalk++ Workbench, TupTalk, TableTalk, RelTalk,
          Arctic, and LabTalk are project marks used to describe the engine, teaching shell,
          workbench surfaces, table-buffering lane, TUI code-name surface, and related tooling.
        </p>
      </section>
    </div>
  );
}
