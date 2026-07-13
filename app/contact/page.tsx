import Link from "@/components/StaticLink";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact x64base",
  description: "Contact x64base about technical review, academic use, licensing, security, or collaboration."
};

export default function ContactPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Contact</h1>
        <p className="text-muted">
          For licensing, academic interest, educational use, non-profit inquiries, or technical collaboration,
          please contact the author.
        </p>
      </header>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="text-sm font-semibold">Email</div>
            <p className="mt-2 text-sm text-muted">
              Use this address for professional, academic, and project inquiries.
            </p>
            <Link
              href="mailto:deraldg@msn.com"
              className="mt-4 inline-flex rounded-2xl border border-border bg-bg/30 px-4 py-2 text-sm font-semibold hover:bg-bg/40"
            >
              deraldg@msn.com
            </Link>
          </div>
          <div>
            <div className="text-sm font-semibold">Notes</div>
            <ul className="mt-2 list-disc pl-5 text-sm text-muted">
              <li>Include the product name (Engine / DotTalk++ / Parallel GUI/TUI / Laboratory Campus) and intended usage.</li>
              <li>For academic or education input, mention your area: CS, databases, technical writing, curriculum, general education, or learning theory.</li>
              <li>For non-profit or partnership inquiries, include a short summary and expected timeline.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-card/20 p-6 text-sm text-muted">
        <p>
          x64base™ <br />© 1993–2026 Derald R Grimwood Jr
        </p>
      </section>
    </div>
  );
}
