import Link from "next/link";

export default function ContactPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Contact</h1>
        <p className="text-muted">
          For licensing, partnerships, educational use, or non-profit inquiries, please contact the author.
        </p>
      </header>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="text-sm font-semibold">Email</div>
            <p className="mt-2 text-sm text-muted">
              Set your preferred address in <code>app/contact/page.tsx</code>.
            </p>
            <Link
              href="mailto:hello@x64base.com"
              className="mt-4 inline-flex rounded-2xl border border-border bg-bg/30 px-4 py-2 text-sm font-semibold hover:bg-bg/40"
            >
              hello@x64base.com
            </Link>
          </div>
          <div>
            <div className="text-sm font-semibold">Notes</div>
            <ul className="mt-2 list-disc pl-5 text-sm text-muted">
              <li>Include the product name (Engine / DotTalk++ / Parallel GUI/TUI / Laboratory Campus) and intended usage.</li>
              <li>For education/non-profit, mention institution type and expected number of seats.</li>
              <li>For partnerships, include a short summary and timeline.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-card/20 p-6 text-sm text-muted">
        <p>
          x64base® <br />© 1993–2026 Derald R Grimwood Jr
        </p>
      </section>
    </div>
  );
}
