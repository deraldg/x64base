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
  params: { category: string; slug: string[] };
}): Promise<Metadata> {
  const filePath = resolveNewsPath(params.category, params.slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  return metadataFromFrontmatter(frontmatter, `/news/${params.category}/${params.slug.join("/")}`);
}

export default async function NewsPostPage({
  params
}: {
  params: { category: string; slug: string[] };
}) {
  const filePath = resolveNewsPath(params.category, params.slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  const href = `/news/${params.category}/${params.slug.join("/")}`;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "News", href: "/news" },
          { label: params.category.replace(/-/g, " "), href: `/news/${params.category}` },
          { label: frontmatter.title ?? params.slug[params.slug.length - 1], href }
        ]}
      />

      <h1 className="text-3xl font-semibold tracking-tight">{frontmatter.title}</h1>
      <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted">
        {frontmatter.date ? <span className="font-mono">{frontmatter.date}</span> : null}
        <span>Category: {params.category}</span>
      </div>
      {frontmatter.description ? <p className="mt-3 text-muted">{frontmatter.description}</p> : null}

      <div className="mt-8">
        <Prose html={content} />
      </div>
    </div>
  );
}
