import type { Metadata } from "next";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Prose } from "@/components/Prose";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { resolveMdxPath, walkMdx } from "@/lib/content";

export async function generateStaticParams() {
  const all = walkMdx("about");
  return all.map((r) => ({ slug: r.slug }));
}

export async function generateMetadata({
  params
}: {
  params: { slug: string[] };
}): Promise<Metadata> {
  const filePath = resolveMdxPath("about", params.slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  return metadataFromFrontmatter(frontmatter, `/about/${params.slug.join("/")}`);
}

export default async function AboutSlugPage({ params }: { params: { slug: string[] } }) {
  const filePath = resolveMdxPath("about", params.slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "About", href: "/about" },
          { label: frontmatter.title ?? params.slug[params.slug.length - 1], href: `/about/${params.slug.join("/")}` }
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
