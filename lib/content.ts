import fs from "node:fs";
import path from "node:path";

export type Section = "about" | "products" | "docs" | "licensing" | "brand" | "news";

export function contentDir(...parts: string[]) {
  return path.join(process.cwd(), "content", ...parts);
}

export function readTextFile(filePath: string) {
  return fs.readFileSync(filePath, "utf8");
}

export function fileExists(filePath: string) {
  try {
    fs.accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}

export function resolveMdxPath(section: Exclude<Section, "news">, slugParts: string[]) {
  const rel = slugParts.length ? slugParts.join("/") : "index";
  const filePath = contentDir(section, `${rel}.mdx`);
  if (!fileExists(filePath)) {
    throw new Error(`MDX not found: ${filePath}`);
  }
  return filePath;
}

export type WalkResult = { slug: string[]; filePath: string };

export function walkMdx(section: Exclude<Section, "news">): WalkResult[] {
  const root = contentDir(section);
  const out: WalkResult[] = [];

  const walk = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      if (entry.isFile() && entry.name.endsWith(".mdx")) {
        const rel = path.relative(root, full).replace(/\\/g, "/");
        const withoutExt = rel.replace(/\.mdx$/, "");
        out.push({ slug: withoutExt.split("/"), filePath: full });
      }
    }
  };

  walk(root);
  return out.sort((a, b) => a.slug.join("/").localeCompare(b.slug.join("/")));
}

export type NewsPost = {
  category: string;
  slug: string;
  filePath: string;
};

export function walkNews(): NewsPost[] {
  const root = contentDir("news");
  const out: NewsPost[] = [];

  const walk = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      if (entry.isFile() && entry.name.endsWith(".mdx")) {
        const rel = path.relative(root, full).replace(/\\/g, "/"); // category/slug.mdx
        const parts = rel.split("/");
        if (parts.length < 2) continue;
        const category = parts[0];
        const slug = parts.slice(1).join("/").replace(/\.mdx$/, "");
        out.push({ category, slug, filePath: full });
      }
    }
  };

  walk(root);
  return out.sort((a, b) => `${a.category}/${a.slug}`.localeCompare(`${b.category}/${b.slug}`));
}
