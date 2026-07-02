import matter from "gray-matter";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";
import rehypeSlug from "rehype-slug";
import rehypeStringify from "rehype-stringify";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";
import { readTextFile } from "@/lib/content";

export type MdxFrontmatter = {
  title?: string;
  description?: string;
  date?: string;
};

export async function compileMdxFromFile(filePath: string) {
  const raw = readTextFile(filePath);
  const parsed = matter(raw);
  const rendered = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeSanitize)
    .use(rehypeSlug)
    .use(rehypeAutolinkHeadings, {
      behavior: "wrap",
      properties: { className: "no-underline" }
    })
    .use(rehypeStringify)
    .process(parsed.content);

  return { frontmatter: parsed.data as MdxFrontmatter, content: String(rendered) };
}
