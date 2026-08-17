import fs from "node:fs";
import { contentDir } from "@/lib/content";

/**
 * Working-log feed for /news.
 *
 * The point of this module is that NOBODY EDITS THE PAGE TO ADD NEWS. The page
 * renders whatever `content/news/milestones.json` contains; adding a milestone
 * is appending one object to that file.
 *
 * On error handling, deliberately: this loader distinguishes THREE states and
 * says which it found, rather than returning an empty list for all of them.
 *
 *   file absent   -> [] plus a build-time warning naming the path
 *   file present, `items` empty -> [] silently, because that is a real answer
 *   file present, malformed     -> THROW, failing the build
 *
 * An empty list and an unreadable file must not look identical. A feed that
 * silently drops rows publishes a shorter history and reports success, which is
 * indistinguishable from having done less work.
 */

export type Milestone = {
  date: string;
  title: string;
  summary: string;
  href?: string;
  tag?: string;
};

const FEED = "milestones.json";
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function fail(detail: string): never {
  throw new Error(
    `milestones: content/news/${FEED} is malformed -- ${detail}. ` +
      `Fix the feed rather than the page; see the $comment block in that file.`
  );
}

export function getMilestones(): Milestone[] {
  const filePath = contentDir("news", FEED);

  if (!fs.existsSync(filePath)) {
    console.warn(`milestones: no feed at ${filePath} -- the working log will render empty.`);
    return [];
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (err) {
    fail(`not valid JSON (${(err as Error).message})`);
  }

  if (typeof parsed !== "object" || parsed === null) fail("top level is not an object");
  const items = (parsed as { items?: unknown }).items;
  if (items === undefined) fail("no `items` key");
  if (!Array.isArray(items)) fail("`items` is not an array");

  return items.map((raw, i) => {
    const at = `items[${i}]`;
    if (typeof raw !== "object" || raw === null) fail(`${at} is not an object`);
    const m = raw as Record<string, unknown>;

    for (const key of ["date", "title", "summary"] as const) {
      if (typeof m[key] !== "string" || (m[key] as string).trim() === "") {
        fail(`${at} is missing a non-empty \`${key}\``);
      }
    }
    if (!DATE_RE.test(m.date as string)) {
      fail(`${at}.date is "${String(m.date)}", expected YYYY-MM-DD`);
    }
    for (const key of ["href", "tag"] as const) {
      if (m[key] !== undefined && typeof m[key] !== "string") fail(`${at}.${key} must be a string`);
    }

    return {
      date: m.date as string,
      title: m.title as string,
      summary: m.summary as string,
      href: m.href as string | undefined,
      tag: m.tag as string | undefined
    };
  });
}

/** Newest first. Ties keep feed order, so same-day entries read top-down as written. */
export function getMilestonesSorted(limit?: number): Milestone[] {
  const sorted = [...getMilestones()].sort((a, b) => b.date.localeCompare(a.date));
  return typeof limit === "number" ? sorted.slice(0, limit) : sorted;
}
