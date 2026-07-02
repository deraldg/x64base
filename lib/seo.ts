import type { Metadata } from "next";
import type { MdxFrontmatter } from "@/lib/mdx";

export function metadataFromFrontmatter(fm: MdxFrontmatter, canonicalPath: string): Metadata {
  const title = fm.title ?? "x64base";
  const description = fm.description ?? "x64base documentation and resources.";
  return {
    title,
    description,
    alternates: { canonical: canonicalPath },
    openGraph: {
      title,
      description,
      url: canonicalPath,
      images: [{ url: "/og.svg", width: 1200, height: 630, alt: "x64base" }]
    },
    twitter: { card: "summary_large_image", title, description, images: ["/og.svg"] }
  };
}
