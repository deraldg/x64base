import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "x64base Project Notice",
  description: "A concise notice about the tentative license status of the public x64base source."
};

export default function LicensingPage() {
  return (
    <article className="max-w-3xl space-y-8">
      <header className="max-w-2xl space-y-3">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Project notice</p>
        <h1 className="text-3xl font-semibold tracking-tight">Licensing status</h1>
        <p className="text-muted">
          x64base is a research and education project. The public source currently carries a tentative MIT
          license while final maintainer and legal review remains open.
        </p>
      </header>

      <section className="space-y-3 rounded-lg border border-border bg-card/45 p-6 text-sm leading-7 text-muted">
        <p>
          The repository’s root <code>LICENSE</code> file is the only current project license statement.
          No separate educational, non-profit, subscription, pricing, or commercial licensing program is
          being presented on this website.
        </p>
        <p>
          Third-party components remain subject to their own terms and attribution requirements.
        </p>
      </section>

      <div className="flex flex-wrap gap-4 text-sm">
        <a className="font-semibold text-brand hover:underline" href="https://github.com/deraldg/x64base/blob/main/LICENSE">
          Read the repository notice
        </a>
        <a className="text-muted hover:text-fg hover:underline" href="/docs/dev/third-party-acknowledgements">
          Third-party credits
        </a>
      </div>
    </article>
  );
}
