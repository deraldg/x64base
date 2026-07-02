import matter from "gray-matter";
import { walkNews, readTextFile, type NewsPost } from "@/lib/content";
import type { MdxFrontmatter } from "@/lib/mdx";

export type NewsFrontmatter = MdxFrontmatter & { date?: string; author?: string };

export type NewsIndexItem = NewsPost & { frontmatter: NewsFrontmatter };

export function getAllNewsPosts(): NewsIndexItem[] {
  return walkNews().map((p) => {
    const raw = readTextFile(p.filePath);
    const parsed = matter(raw);
    return { ...p, frontmatter: parsed.data as NewsFrontmatter };
  });
}

export function getNewsPostsByCategory(category: string) {
  return getAllNewsPosts()
    .filter((p) => p.category === category)
    .sort((a, b) => (b.frontmatter.date ?? "").localeCompare(a.frontmatter.date ?? ""));
}
