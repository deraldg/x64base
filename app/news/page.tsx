import Link from "@/components/StaticLink";
import { Card } from "@/components/Card";
import { getAllNewsPosts } from "@/lib/news";

export default function NewsPage() {
  const allPosts = getAllNewsPosts().sort((a, b) => (b.frontmatter.date ?? "").localeCompare(a.frontmatter.date ?? ""));
  const posts = allPosts
    .sort((a, b) => (b.frontmatter.date ?? "").localeCompare(a.frontmatter.date ?? ""))
    .slice(0, 6);
  const pressReleaseCount = allPosts.filter((p) => p.category === "press-releases").length;
  const announcementCount = allPosts.filter((p) => p.category === "announcements").length;

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">News</h1>
        <p className="text-muted">
          Press releases, announcements, and milestone updates across x64base, DotTalk++, LabTalk, and the
          emerging Arctic workbench lanes.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Card
          title="Press Releases"
          description="Architecture milestones, publication notes, release positioning, and major ecosystem updates."
          href="/news/press-releases"
        >
          <div className="text-xs uppercase tracking-[0.2em] text-muted">{pressReleaseCount} posts</div>
        </Card>
        <Card
          title="Announcements"
          description="Runtime improvements, messaging/catalog work, regression lanes, curriculum, and build updates."
          href="/news/announcements"
        >
          <div className="text-xs uppercase tracking-[0.2em] text-muted">{announcementCount} posts</div>
        </Card>
      </div>

      <section className="rounded-2xl border border-border bg-card/30 p-6">
        <div className="flex items-end justify-between gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Latest</h2>
          <Link href="/news/press-releases" className="text-sm text-muted hover:text-fg">
            Press releases →
          </Link>
          <Link href="/news/announcements" className="text-sm text-muted hover:text-fg">
            Announcements →
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
    </div>
  );
}
