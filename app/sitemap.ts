import type { MetadataRoute } from "next";
import { walkMdx, walkNews } from "@/lib/content";

export const dynamic = "force-static";

const site = "https://x64base.com";

function url(path: string) {
  return `${site}${path.startsWith("/") ? path : `/${path}`}`;
}

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticRoutes = [
    "/",
    "/about",
    "/products",
    "/docs",
    "/licensing",
    "/brand",
    "/news",
    "/news/press-releases",
    "/news/announcements",
    "/contact"
  ];

  const mdxRoutes = [
    ...walkMdx("about").map((r) => `/about/${r.slug.join("/")}`),
    ...walkMdx("products").map((r) => `/products/${r.slug[0]}`),
    ...walkMdx("docs").map((r) => `/docs/${r.slug.join("/")}`),
    ...walkMdx("licensing").map((r) => `/licensing/${r.slug.join("/")}`),
    ...walkMdx("brand").map((r) => `/brand/${r.slug.join("/")}`)
  ];

  const newsRoutes = walkNews().map((p) => `/news/${p.category}/${p.slug}`);

  const all = [...staticRoutes, ...mdxRoutes, ...newsRoutes];

  return all.map((p) => ({
    url: url(p),
    lastModified: now,
    changeFrequency: "weekly",
    priority: p === "/" ? 1 : 0.7
  }));
}
