import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllNewsPosts, getNewsPostsByCategory } from "@/lib/news";

export function generateStaticParams() {
  const categories = new Set(getAllNewsPosts().map((post) => post.category));
  return Array.from(categories).map((category) => ({ category }));
}

export default function NewsCategoryPage({ params }: { params: { category: string } }) {
  const posts = getNewsPostsByCategory(params.category);
  if (!posts.length) return notFound();

  const label = params.category.replace(/-/g, " ");

  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">{label}</h1>
        <p className="text-muted">Updates and posts in this category.</p>
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
