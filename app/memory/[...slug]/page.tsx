import type { Metadata } from "next";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Prose } from "@/components/Prose";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { resolveMdxPath, walkMdx } from "@/lib/content";

export function generateStaticParams() {
  return walkMdx("memory").map((r) => ({ slug: r.slug }));
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ slug: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const filePath = resolveMdxPath("memory", slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  const base = metadataFromFrontmatter(frontmatter, `/memory/${slug.join("/")}`);
  // Private section: keep it out of search indexes until it is promoted.
  return { ...base, robots: { index: false, follow: false } };
}

export default async function MemoryPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  const filePath = resolveMdxPath("memory", slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);
  const href = `/memory/${slug.join("/")}`;

  return (
    <div className="min-w-0 flex-1" data-pagefind-ignore="all">
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Frontal Memory (private)", href: "/memory" },
          { label: frontmatter.title ?? slug[slug.length - 1], href }
        ]}
      />

      <h1 className="text-3xl font-semibold tracking-tight">{frontmatter.title}</h1>
      {frontmatter.description ? <p className="mt-2 text-muted">{frontmatter.description}</p> : null}

      <div className="mt-8">
        <Prose html={content} />
      </div>
    </div>
  );
}
