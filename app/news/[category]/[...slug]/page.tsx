import type { Metadata } from "next";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Prose } from "@/components/Prose";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { contentDir, walkNews, fileExists } from "@/lib/content";

function resolveNewsPath(category: string, slugParts: string[]) {
  const filePath = contentDir("news", category, `${slugParts.join("/")}.mdx`);
  if (!fileExists(filePath)) throw new Error(`News post not found: ${filePath}`);
  return filePath;
}

export async function generateStaticParams() {
  return walkNews().map((p) => ({ category: p.category, slug: p.slug.split("/") }));
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ category: string; slug: string[] }>;
}): Promise<Metadata> {
  const { category, slug } = await params;
  const filePath = resolveNewsPath(category, slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  return metadataFromFrontmatter(frontmatter, `/news/${category}/${slug.join("/")}`);
}

export default async function NewsPostPage({
  params
}: {
  params: Promise<{ category: string; slug: string[] }>;
}) {
  const { category, slug } = await params;
  const filePath = resolveNewsPath(category, slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  const href = `/news/${category}/${slug.join("/")}`;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "News", href: "/news" },
          { label: category.replace(/-/g, " "), href: `/news/${category}` },
          { label: frontmatter.title ?? slug[slug.length - 1], href }
        ]}
      />

      <h1 className="text-3xl font-semibold tracking-tight">{frontmatter.title}</h1>
      <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted">
        {frontmatter.date ? <span className="font-mono">{frontmatter.date}</span> : null}
        <span>Category: {category}</span>
      </div>
      {frontmatter.description ? <p className="mt-3 text-muted">{frontmatter.description}</p> : null}

      <div className="mt-8">
        <Prose html={content} />
      </div>
    </div>
  );
}
