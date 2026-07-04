import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Boxes, Database, FileCode2, GitBranch, GraduationCap, TerminalSquare } from "lucide-react";

const proofPoints = [
  { label: "Project status", value: "Active beta" },
  { label: "Runtime", value: "DotTalk++" },
  { label: "Index model", value: "INX/CNX/CDX" },
  { label: "GUI lane", value: "wx/Tk/TUI" }
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
  }
];

const quickLinks = [
  { title: "Engine architecture", href: "/docs/engine/architecture" },
  { title: "DBF_64 specification", href: "/docs/engine/dbf-64-specification" },
  { title: "DotTalk++ guide", href: "/docs/dottalk/language-guide" },
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
    text: "Use DotTalk++, ArcticTalk, and LabTalk material for labs, front-end learning, command literacy, and database fundamentals.",
    href: "/docs/dottalk/curriculum",
    icon: GraduationCap
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
            x64base is the modern home for DBF_64 tables, FPT64 memo storage, stable indexing, and the
            DotTalk++ command shell. The current local project is an active educational and research
            runtime: useful, inspectable, and intentionally honest about beta and canary boundaries.
          </p>
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

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">documentation</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">Readable status for real implementation work.</h2>
          <p className="mt-4 leading-7 text-muted">
            The site now tracks the local `D:\code\ccode` truth: C++20 CMake build options, DotTalk++
            command surfaces, xindex, memo, datadict, GUI lanes, and runtime validation work.
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

      <section className="grid gap-4 md:grid-cols-2">
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
          x64base, xBase_64, DotTalk++, TupTalk, TableTalk, RelTalk, ArcticTalk, and LabTalk are project
          marks used to describe the engine, teaching shell, and related tooling.
        </p>
      </section>
    </div>
  );
}
