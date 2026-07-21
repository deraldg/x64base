import Link from "@/components/StaticLink";
import { Archive, BookOpen, Download, FileText, Github, PackageCheck, ScrollText } from "lucide-react";
import { Card } from "@/components/Card";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Download DotTalk++ — Source, Beta Builds, and Manuals",
  description: "Find the canonical x64base source, CI artifacts, draft beta releases, checksums, manuals, and known limitations."
};

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
    title: "Command Reference",
    description: "The accepted 183-page command-reference snapshot and its public-source provenance.",
    href: "/docs/dottalk/command-reference",
    icon: BookOpen
  },
  {
    title: "Documentation Progress",
    description: "The nine-gate publication checkpoint, current follow-up delta, and machine-readable status.",
    href: "/docs/dev/documentation-progress",
    icon: FileText
  },
  {
    title: "Pinocchio Benchmarks",
    description: "Historical million-row navigation results, evidence limits, and machine identity rules.",
    href: "/docs/engine/pinocchio-benchmarks",
    icon: Archive
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
    title: "Accepted Developer Manual (Markdown)",
    description: "Current manual-reviewed artifact: 4,118 lines, 237 headings, 24 sections, and four appendices.",
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
  },
  {
    title: "Documentation Progress Metadata",
    description: "Machine-readable publication checkpoint, manual counts, benchmark state, and separate missions.",
    href: "/artifacts/documentation-progress-v1.json"
  }
];

export default function DownloadsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">downloads</p>
        <h1 className="text-3xl font-semibold tracking-tight">A place to start</h1>
        <p className="text-muted">
          Start with the canonical source and its green CI artifacts. Versioned beta ZIPs, checksums,
          release notes, and known limitations appear on GitHub Releases when a release gate passes.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Current public source</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              The public <code>main</code> branch is authoritative for source, CI, licensing, and
              releases. Feature branches and local maintainer trees are not public runtime truth.
            </p>
          </div>
          <a
            href="https://github.com/deraldg/x64base/releases"
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-border bg-bg/40 px-4 py-2 text-sm font-semibold text-fg transition hover:border-brand/60"
          >
            <Github size={16} aria-hidden="true" />
            GitHub Releases
          </a>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Public authority model</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              Outside contributors need one source of truth: the public <code>main</code> branch.
              Local implementation, staging, website, and generated-manual trees are maintainer
              workflow details until promoted through a reviewed public change.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-border/70 bg-bg/30 p-4">
              <h3 className="text-sm font-semibold tracking-tight">What is authoritative</h3>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                <li><span className="font-medium text-fg">Source:</span> public <code>main</code></li>
                <li><span className="font-medium text-fg">Build proof:</span> green CI for the referenced commit</li>
                <li><span className="font-medium text-fg">Distribution:</span> tagged GitHub release with checksum</li>
                <li><span className="font-medium text-fg">Limitations:</span> release notes and Current State page</li>
              </ul>
            </div>

            <div className="rounded-lg border border-border/70 bg-bg/30 p-4">
              <h3 className="text-sm font-semibold tracking-tight">Promotion convention</h3>
              <div className="mt-3 space-y-3 text-sm leading-6 text-muted">
                <p>
                  <span className="font-medium text-fg">Source flow:</span>
                  <br />
                  <code>feature branch -&gt; review + CI -&gt; public main</code>
                </p>
                <p>
                  <span className="font-medium text-fg">Website flow:</span>
                  <br />
                  <code>main evidence -&gt; reviewed site source -&gt; verified deployment</code>
                </p>
                <p>Website prose explains evidence; it does not create implementation truth.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/40 p-5">
        <h2 className="text-lg font-semibold tracking-tight">Accepted documentation snapshot</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          The current Markdown manual and 183-page command reference were reviewed and promoted from
          public source commit <code>be935053</code>. The manual carries the
          <code> manual-reviewed</code> proof label and contains 4,118 lines and 237 headings.
        </p>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <a
            href="https://github.com/deraldg/x64base/blob/be9350531251bb682f0476d652d99ca137861577/docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-brand hover:underline"
          >
            Manual acceptance manifest
          </a>
          <Link href="/docs/dottalk/command-reference" className="font-medium text-brand hover:underline">
            Command-reference snapshot
          </Link>
        </div>
      </section>

      <section className="rounded-lg border border-brand/40 bg-card/40 p-5">
        <h2 className="text-lg font-semibold tracking-tight">Latest assembled manual (always current)</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          These are permanent links. Every rebuild of the manifest-driven assembler overwrites the
          same files, so they always resolve to the newest build. This is an
          <code> assembled-candidate</code> regenerated from source by the assembler and guarded by a
          drift gate; the accepted snapshot above remains the reviewed baseline. See the build
          manifest for the exact source commit, part counts, and checksums.
        </p>
        <div className="mt-3 flex flex-wrap gap-4 text-sm">
          <a href="/downloads/current/developer-manual-latest.html" className="font-medium text-brand hover:underline">
            Read online (HTML)
          </a>
          <a href="/downloads/current/developer-manual-latest.pdf" className="font-medium text-brand hover:underline">
            PDF
          </a>
          <a href="/downloads/current/developer-manual-latest.md" className="font-medium text-brand hover:underline">
            Markdown
          </a>
          <a href="/downloads/current/DEVELOPER_MANUAL_LATEST.json" className="font-medium text-brand hover:underline">
            Build manifest
          </a>
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
