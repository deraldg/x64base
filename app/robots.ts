import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/portal", "/portal/"] }],
    sitemap: "https://x64base.com/sitemap.xml",
    host: "https://x64base.com"
  };
}
