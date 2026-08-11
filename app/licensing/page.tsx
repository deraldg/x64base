import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "x64base Licensing",
  description:
    "x64base is dual-licensed: free and open source under GPLv3 for everyone, with a separate commercial license for closed or proprietary use."
};

export default function LicensingPage() {
  return (
    <article className="max-w-3xl space-y-8">
      <header className="max-w-2xl space-y-3">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Licensing</p>
        <h1 className="text-3xl font-semibold tracking-tight">Open source, with a commercial door</h1>
        <p className="text-muted">
          x64base is <strong>dual-licensed</strong>. It is free and open source under the GNU
          General Public License v3 (GPL-3.0-only, committed to the repository 2026-08-11) for
          everyone, and available under a separate commercial license for anyone who wants to
          use it in a closed or proprietary product.
        </p>
      </header>

      <section className="space-y-3 rounded-lg border border-border bg-card/45 p-6 text-sm leading-7 text-muted">
        <h2 className="text-base font-semibold text-fg">1. Open source (GPLv3) -- free for everyone</h2>
        <p>
          Read it, run it, study it, teach with it, fork it, and preserve it -- at no cost,
          forever, under the terms of the GPLv3. Students, educators, hobbyists, researchers,
          and the retro / xBase community never pay. If you distribute a modified version, the
          GPL asks only that you share your changes under the same license.
        </p>
      </section>

      <section className="space-y-3 rounded-lg border border-border bg-card/45 p-6 text-sm leading-7 text-muted">
        <h2 className="text-base font-semibold text-fg">2. Commercial license -- for closed or proprietary use</h2>
        <p>
          If you want to embed x64base in a closed-source or commercial product, or use it on
          terms other than the GPL, a commercial license is available from the author. This is
          the only situation in which anyone pays for the engine itself. Contact us to discuss
          terms.
        </p>
      </section>

      <section className="space-y-3 rounded-lg border border-border bg-card/45 p-6 text-sm leading-7 text-muted">
        <h2 className="text-base font-semibold text-fg">3. The value layer -- optional, and gates nothing</h2>
        <p>
          The engine is free. What is offered for support are the things built <em>around</em>{" "}
          it: teaching materials and an "inside the engine" curriculum, architecture and
          lineage documentation, workshops and lectures, and institutional support or
          consulting. You are never buying access to the code -- only the teaching and
          understanding around it. Sponsorship is welcome and gates nothing.
        </p>
      </section>

      <p className="text-sm text-muted">
        Educational and non-commercial use is already free under the GPL. Accredited
        institutions that need commercial terms may request them at no or nominal cost.
        <br />
        The license covers the software; project names remain the author&apos;s.
      </p>

      <div className="flex flex-wrap gap-4 text-sm">
        <a className="font-semibold text-brand hover:underline" href="https://github.com/deraldg/x64base/blob/main/LICENSE">
          Repository LICENSE
        </a>
        <a className="text-muted hover:text-fg hover:underline" href="https://github.com/deraldg/x64base/blob/main/LICENSING.md">
          Full licensing strategy
        </a>
        <a className="text-muted hover:text-fg hover:underline" href="/brand">
          Brand
        </a>
        <a className="text-muted hover:text-fg hover:underline" href="/docs/dev/third-party-acknowledgements">
          Third-party credits
        </a>
        <a className="text-muted hover:text-fg hover:underline" href="/contact">
          Contact for commercial licensing
        </a>
      </div>
    </article>
  );
}
