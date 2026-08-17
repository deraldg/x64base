import Link from "@/components/StaticLink";
import { getMilestonesSorted } from "@/lib/milestones";

/**
 * Working log -- the smaller milestones between full announcements.
 *
 * ONE renderer, used by /news and /news/announcements. It lives here rather
 * than inline in either page for a specific reason: the same markup copied into
 * two pages is two restatements of one thing, and they diverge. When this had a
 * single call site the copy was cheaper; it now has two, so it does not.
 *
 * Data comes from `content/news/milestones.json`. To add a milestone, append to
 * that file -- never edit this component and never edit a page.
 */

type WorkingLogProps = {
  /** Cap the number of entries. Omit to render the whole feed. */
  limit?: number;
  /** Heading text, so the archive page can title it differently if needed. */
  heading?: string;
  /** Short line under the heading. Pass null to omit it. */
  blurb?: string | null;
};

export default function WorkingLog({
  limit,
  heading = "Working log",
  blurb = "Smaller milestones between announcements, newest first."
}: WorkingLogProps) {
  const milestones = getMilestonesSorted(limit);
  if (milestones.length === 0) return null;

  return (
    <section className="rounded-2xl border border-border bg-card/30 p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight">{heading}</h2>
        {blurb ? <p className="text-xs text-muted">{blurb}</p> : null}
      </div>

      <ol className="mt-4 space-y-4">
        {milestones.map((m) => (
          <li key={`${m.date}-${m.title}`} className="border-l-2 border-border pl-4">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="font-mono text-xs text-muted">{m.date}</span>
              <span className="font-semibold">
                {m.href ? (
                  <Link href={m.href} className="hover:underline">
                    {m.title}
                  </Link>
                ) : (
                  m.title
                )}
              </span>
              {m.tag ? (
                <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-[0.14em] text-muted">
                  {m.tag}
                </span>
              ) : null}
            </div>
            <p className="mt-1 text-sm text-muted">{m.summary}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
