import Link from "next/link";
import { Card } from "@/components/Card";
import { getAllNewsPosts } from "@/lib/news";

export default function NewsPage() {
  const posts = getAllNewsPosts()
    .sort((a, b) => (b.frontmatter.date ?? "").localeCompare(a.frontmatter.date ?? ""))
    .slice(0, 6);

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">News</h1>
        <p className="text-muted">Press releases, announcements, and updates across the ecosystem.</p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Card
          title="Press Releases"
          description="Launch announcements, version updates, and partnerships."
          href="/news/press-releases"
        />
        <Card
          title="Announcements"
          description="New features, curriculum updates, community events."
          href="/news/announcements"
        />
      </div>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="flex items-end justify-between gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Latest</h2>
          <Link href="/news/announcements" className="text-sm text-muted hover:text-fg">
            View all →
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
              <div className="mt-3 text-xs text-muted">Category: {p.category}</div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
