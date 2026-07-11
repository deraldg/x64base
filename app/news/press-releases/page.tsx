import Link from "@/components/StaticLink";
import { getNewsPostsByCategory } from "@/lib/news";

export default function PressReleasesPage() {
  const posts = getNewsPostsByCategory("press-releases");

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Press Releases</h1>
        <p className="text-muted">Launch announcement, version updates, educational partnerships.</p>
      </header>

      <div className="grid gap-3">
        {posts.map((p) => (
          <Link
            key={p.slug}
            href={`/news/${p.category}/${p.slug}`}
            className="rounded-2xl border border-border bg-card/30 p-5 hover:bg-card/40"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="font-semibold">{p.frontmatter.title ?? p.slug}</div>
              <div className="font-mono text-xs text-muted">{p.frontmatter.date ?? ""}</div>
            </div>
            {p.frontmatter.description ? <p className="mt-2 text-sm text-muted">{p.frontmatter.description}</p> : null}
          </Link>
        ))}
      </div>
    </div>
  );
}
