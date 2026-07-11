import Link from "@/components/StaticLink";
import { Archive, BookOpen, Download, FileText, Github, PackageCheck, ScrollText } from "lucide-react";
import { Card } from "@/components/Card";

const startingPoints = [
  {
    title: "Source Repository",
    description: "Public source, history, issues, and the GitHub Pages publication branch.",
    href: "https://github.com/deraldg/x64base",
    icon: Github,
    external: true
  },
  {
    title: "Build Instructions",
    description: "Current Windows, POSIX, WSL/Ubuntu, and macOS-oriented build notes.",
    href: "/docs/getting-started/installation",
    icon: BookOpen
  },
  {
    title: "Runtime Footprint",
    description: "Observed release payload: dottalkpp.exe, lmdb.dll, sqlite3.dll, and what each file does.",
    href: "/docs/engine/runtime-footprint",
    icon: PackageCheck
  },
  {
    title: "Command Catalog",
    description: "The reviewed command surface that should be regenerated as DotTalk++ changes.",
    href: "/docs/dottalk/command-catalog",
    icon: ScrollText
  },
  {
    title: "Runtime Evidence",
    description: "Screenshots and proof artifacts curated as evidence, not release polish claims.",
    href: "/docs/labtalk/runtime-evidence",
    icon: Archive
  },
  {
    title: "Important Documents",
    description: "A map of SelfDoc, MDO, generated manuals, matrices, and proof-backed documentation layers.",
    href: "/docs/dev/important-documents",
    icon: FileText
  },
  {
    title: "Project Truth",
    description: "Observed maintainer layout, authority boundaries, and the current source-to-site relationship.",
    href: "/docs/dev/project-truth",
    icon: FileText
  },
  {
    title: "Website Publication",
    description: "How implementation truth, staging, reviewed docs, GitHub Pages, and x64base.com are supposed to align.",
    href: "/docs/dev/selfdoc-website-publication",
    icon: Archive
  }
];

const stagedDownloads = [
  {
    title: "DotTalk++ / x64base Manual Preview",
    description: "Current DOCX manual preview staged from the implementation tree.",
    href: "/downloads/current/DotTalkPP_x64base_Manual_Preview_V1.docx"
  },
  {
    title: "Primary Reader Manual (Markdown)",
    description: "Current primary reader manual artifact from the manualgen publication lane.",
    href: "/downloads/current/developer_manual_publication_v1.md"
  },
  {
    title: "Messaging / Locale Alignment Packet",
    description: "Current documentation packet for the live runtime messaging and locale surfaces.",
    href: "/downloads/current/MDO-382E_MESSAGING_AND_LOCALE_RUNTIME_SURFACE_ALIGNMENT_PACKET.md"
  },
  {
    title: "Manual Family Runtime Surface Milestone Packet",
    description: "Milestone review packet for HELP, MANUAL, DDICT, BBOX, and MAINT alignment.",
    href: "/downloads/current/MDO-381E_MANUAL_FAMILY_RUNTIME_SURFACE_ALIGNMENT_MILESTONE_PACKET.md"
  },
  {
    title: "Manual Family Runtime Surface Crosswalk",
    description: "Crosswalk showing how the manual family maps onto current runtime command surfaces.",
    href: "/downloads/current/manual_family_runtime_surface_crosswalk_v1.md"
  },
  {
    title: "Messaging / Locale Runtime Surface Crosswalk",
    description: "Crosswalk for the live runtime message and locale command surfaces.",
    href: "/downloads/current/messaging_locale_runtime_surface_crosswalk_v1.md"
  },
  {
    title: "Messaging / Locale Command Surface Crosswalk",
    description: "Crosswalk for command-level messaging and locale publication work.",
    href: "/downloads/current/messaging_locale_command_surface_crosswalk_v1.md"
  },
  {
    title: "Download Manifest",
    description: "Machine-readable manifest of the currently staged important-document bundle.",
    href: "/downloads/current/DOWNLOAD_MANIFEST.json"
  }
];

export default function DownloadsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">downloads</p>
        <h1 className="text-3xl font-semibold tracking-tight">A place to start</h1>
        <p className="text-muted">
          This page collects the practical starting points for x64base and DotTalk++. It is not a
          packaged-product storefront; it points to source, build notes, runtime evidence, command
          references, and the current release-shape documentation.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Current public source</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              The canonical public project location is GitHub. Built runtime bundles should be
              treated as staged artifacts only when they are explicitly published and versioned.
            </p>
          </div>
          <a
            href="https://github.com/deraldg/x64base"
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-border bg-bg/40 px-4 py-2 text-sm font-semibold text-fg transition hover:border-brand/60"
          >
            <Github size={16} aria-hidden="true" />
            GitHub
          </a>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Observed maintainer layout</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              Outside contributors should start from GitHub. The current maintainer workflow also
              uses explicit local source, staging, and website trees so publication work does not
              silently replace implementation truth.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-border/70 bg-bg/30 p-4">
              <h3 className="text-sm font-semibold tracking-tight">Local source and staging paths</h3>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                <li><span className="font-medium text-fg">implementation checkout</span>: primary implementation/source truth</li>
                <li><span className="font-medium text-fg">DotTalk++ runtime tree</span>: runtime/help/data tree inside the implementation checkout</li>
                <li><span className="font-medium text-fg">Laboratory Campus / LabTalk tree</span>: campus/portal consumer layer</li>
                <li><span className="font-medium text-fg">local staging mirror</span>: clean source/runtime promotion mirror</li>
                <li><span className="font-medium text-fg">website source tree</span>: reviewed publication source checkout</li>
              </ul>
            </div>

            <div className="rounded-lg border border-border/70 bg-bg/30 p-4">
              <h3 className="text-sm font-semibold tracking-tight">Promotion convention</h3>
              <div className="mt-3 space-y-3 text-sm leading-6 text-muted">
                <p>
                  <span className="font-medium text-fg">Normal source flow:</span>
                  <br />
                  <code>implementation checkout -&gt; local staging mirror -&gt; GitHub repository</code>
                </p>
                <p>
                  <span className="font-medium text-fg">Normal website flow:</span>
                  <br />
                  <code>website source tree -&gt; build/public artifact -&gt; GitHub Pages -&gt; x64base.com</code>
                </p>
                <p>Do not reverse the authority chain by copying website prose into manuals or source-side technical truth.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {startingPoints.map((item) => {
          const Icon = item.icon;
          const body = (
            <Card title={item.title} description={item.description}>
              <Icon className="h-5 w-5 text-brand" aria-hidden="true" />
            </Card>
          );

          return item.external ? (
            <a key={item.href} href={item.href} target="_blank" rel="noreferrer" className="block">
              {body}
            </a>
          ) : (
            <Link key={item.href} href={item.href} className="block">
              {body}
            </Link>
          );
        })}
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Current staged downloads</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            These files are staged from the current implementation tree as reviewed or operator-useful
            artifacts. They are public derivatives or direct maintainer aids, not replacements for
            runtime/source proof.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {stagedDownloads.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="block rounded-lg border border-border bg-card/35 p-5 transition hover:border-brand/60"
            >
              <div className="flex items-start gap-3">
                <Download className="mt-1 h-5 w-5 shrink-0 text-brand" aria-hidden="true" />
                <div>
                  <h3 className="font-semibold tracking-tight">{item.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-muted">{item.description}</p>
                </div>
              </div>
            </a>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/35 p-5 text-sm leading-6 text-muted">
        <div className="flex items-start gap-3">
          <Download className="mt-1 h-5 w-5 shrink-0 text-brand" aria-hidden="true" />
          <p>
            As release packaging matures, this page can grow into a manifest for reviewed binaries,
            source archives, generated manuals, diagrams, checksums, and proof bundles. Until then,
            it stays deliberately simple: start with the source, build notes, and evidence pages.
          </p>
        </div>
      </section>
    </div>
  );
}
