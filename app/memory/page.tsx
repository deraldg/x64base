import type { Metadata } from "next";
import Link from "@/components/StaticLink";

export const metadata: Metadata = {
  title: "Frontal Memory (private)",
  description:
    "Private working reference: persistent memory for artificial minds -- consolidation, recall synapses, and the AI coordination substrate.",
  robots: { index: false, follow: false }
};

export default function MemoryIndex() {
  return (
    <div className="min-w-0 flex-1" data-pagefind-ignore="all">
      <h1 className="text-3xl font-semibold tracking-tight">Frontal Memory -- private reference</h1>
      <p className="mt-2 text-muted">
        Persistent memory for artificial minds: how a session&apos;s short-term working state is
        consolidated into a durable, owner-controlled store and recalled again, so the next session
        carries yesterday forward instead of starting from zero. Unlisted and not indexed; a working
        draft, not yet promoted to public navigation.
      </p>
      <ul className="mt-6 flex flex-col gap-2">
        <li>
          <Link href="/memory/overview" className="text-muted hover:text-fg">
            The thesis and the architecture -&gt;
          </Link>
        </li>
        <li>
          <Link href="/memory/team-model" className="text-muted hover:text-fg">
            The team model: AI agencies as coworkers -&gt;
          </Link>
        </li>
        <li>
          <Link href="/memory/roadmap" className="text-muted hover:text-fg">
            The triage program: development roadmap -&gt;
          </Link>
        </li>
      </ul>

      <h2 className="mt-10 text-xl font-semibold tracking-tight">Related private references</h2>
      <ul className="mt-4 flex flex-col gap-2">
        <li>
          <Link href="/portal" className="text-muted hover:text-fg">
            AI Portal -- architecture, schemas, and generated AI views -&gt;
          </Link>
        </li>
        <li>
          <Link href="/AI/" className="text-muted hover:text-fg">
            AI views -- live reports, console, and portal snapshots -&gt;
          </Link>
        </li>
      </ul>
    </div>
  );
}
