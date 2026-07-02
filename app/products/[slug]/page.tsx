import type { Metadata } from "next";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Prose } from "@/components/Prose";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { resolveMdxPath, walkMdx } from "@/lib/content";

export async function generateStaticParams() {
  const all = walkMdx("products");
  return all.map((r) => ({ slug: r.slug[0] }));
}

export async function generateMetadata({
  params
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const filePath = resolveMdxPath("products", [params.slug]);
  const { frontmatter } = await compileMdxFromFile(filePath);
  return metadataFromFrontmatter(frontmatter, `/products/${params.slug}`);
}

export default async function ProductPage({ params }: { params: { slug: string } }) {
  const filePath = resolveMdxPath("products", [params.slug]);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Products", href: "/products" },
          { label: frontmatter.title ?? params.slug, href: `/products/${params.slug}` }
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
