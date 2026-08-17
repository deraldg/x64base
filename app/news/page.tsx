import Link from "@/components/StaticLink";
import { getAllNewsPosts } from "@/lib/news";
import { getMilestonesSorted } from "@/lib/milestones";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "News",
  description:
    "Milestones and working announcements from the x64base, DotTalk++, and LabTalk lanes -- written from proofs, not positioning."
};

export default function NewsPage() {
  const allPosts = getAllNewsPosts().sort((a, b) => (b.frontmatter.date ?? "").localeCompare(a.frontmatter.date ?? ""));
  const posts = allPosts
    .filter((p) => p.category === "announcements")
    .slice(0, 8);
  const pressReleaseCount = allPosts.filter((p) => p.category === "press-releases").length;
  // Working log. Fed entirely by content/news/milestones.json -- do NOT add
  // entries here. See lib/milestones.ts.
  const milestones = getMilestonesSorted(12);

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">News</h1>
        <p className="text-muted">
          Milestones and working announcements from the engine, shell, and campus lanes. Entries are
          written from proofs and transcripts -- when something is demonstrated, it gets reported;
          when it is not, it does not appear here.
        </p>
      </header>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="flex items-end justify-between gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Latest announcements</h2>
          <Link href="/news/announcements" className="text-sm text-muted hover:text-fg">
            All announcements →
          </Link>
        </div>

        <div className="mt-4 grid gap-3">
          {posts.map((p) => (
            <Link
              key={`${p.category}/${p.slug}`}
              href={`/news/${p.category}/${p.slug}`}
              className="rounded-2xl border border-border bg-bg/20 p-4 hover:bg-bg/30"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="font-semibold">{p.frontmatter.title ?? p.slug}</div>
                <div className="font-mono text-xs text-muted">{p.frontmatter.date ?? ""}</div>
              </div>
              {p.frontmatter.description ? (
                <div className="mt-1 text-sm text-muted">{p.frontmatter.description}</div>
              ) : null}
              <div className="mt-3 text-xs uppercase tracking-[0.18em] text-muted">
                {p.category.replace(/-/g, " ")}
              </div>
            </Link>
          ))}
        </div>
      </section>

      {milestones.length > 0 ? (
        <section className="rounded-2xl border border-border bg-card/30 p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 className="text-lg font-semibold tracking-tight">Working log</h2>
            <p className="text-xs text-muted">
              Smaller milestones between announcements, newest first.
            </p>
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
      ) : null}

      <section className="rounded-2xl border border-dashed border-border bg-card/10 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Press releases</h2>
            <p className="mt-1 text-sm text-muted">
              Deliberately minimal for now: {pressReleaseCount} early posts are retained as history, and a
              proper press surface is an open to-do -- it will be built when there is a release to
              press about, not before.
            </p>
          </div>
          <Link href="/news/press-releases" className="text-sm text-muted hover:text-fg">
            Archive →
          </Link>
        </div>
      </section>
    </div>
  );
}
