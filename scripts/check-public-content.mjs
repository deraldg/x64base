import fs from "node:fs";
import path from "node:path";
import { LOCAL_ONLY_DIRS } from "./strip-local-only-output.mjs";

const root = process.cwd();
const scanRoots = ["app", "components", "config", "content", "public"];

/**
 * Routes that never reach a visitor are out of scope for a PUBLIC content guard.
 *
 * This guard scans SOURCE and explicitly ignores out/, which is correct for
 * everything that publishes. But it had no concept of a local-only route, so on
 * 2026-08-16 it blocked a publish over app/retro/page.tsx -- a page that
 * strip-local-only-output.mjs deletes from every build output and that the
 * publish script aborts over if it ever survives. The guard was policing a file
 * that cannot reach a reader.
 *
 * That matters beyond the inconvenience. A guard that fires on content it does
 * not govern creates pressure to weaken the RULE (here: the retirement of
 * derald.com as a support host, c244300da, 2026-07-10) when the right fix is to
 * narrow the SCOPE. Rules get relaxed under deadline; scope corrections do not
 * cost anything.
 *
 * Derived from LOCAL_ONLY_DIRS so this cannot drift from the stripper -- the
 * third list in this repo to be pointed at that one authority after two of them
 * had already fallen behind.
 */
const localOnlyRoutePrefixes = LOCAL_ONLY_DIRS.flatMap((name) => [
  path.join(root, "app", name),
  path.join(root, "public", name),
]);

function isLocalOnly(file) {
  return localOnlyRoutePrefixes.some(
    (p) => file === p || file.startsWith(p + path.sep)
  );
}
const extensions = new Set([
  ".css",
  ".csv",
  ".html",
  ".js",
  ".json",
  ".md",
  ".mdx",
  ".svg",
  ".ts",
  ".tsx",
  ".txt"
]);

const blocked = [
  {
    name: "Windows absolute path",
    pattern: /(^|[^A-Za-z])([A-Za-z]:[\\/][^`"'<>\r\n)]*)/g
  },
  {
    name: "private user profile path",
    pattern: /C:[\\/]Users[\\/]deral\b/gi
  },
  {
    name: "temporary local artifact path",
    pattern: /\b(AppData|codex-clipboard|Local[\\/]Temp)\b/gi
  },
  {
    name: "retired derald.com support host",
    pattern: /\b(?:www\.)?derald\.com\b/gi
  },
  {
    name: "Next client navigation on static hosting",
    pattern: /\bfrom\s+["']next\/link["']/g
  }
];

const ignoreDirs = new Set([".git", ".next", "node_modules", "out"]);
const historicalSourceArchivePrefix = [
  "public",
  "artifacts",
  "source-lineage",
  "historical-source",
  ""
].join(path.sep);
const findings = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!ignoreDirs.has(entry.name)) walk(full);
      continue;
    }
    if (!entry.isFile() || !extensions.has(path.extname(entry.name))) continue;
    if (isLocalOnly(full)) continue; // never reaches a visitor; out of scope
    scanFile(full);
  }
}

function scanFile(file) {
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split(/\r?\n/);
  const relativeFile = path.relative(root, file);
  for (const rule of blocked) {
    for (let i = 0; i < lines.length; i += 1) {
      rule.pattern.lastIndex = 0;
      const line = lines[i];
      if (!rule.pattern.test(line)) continue;
      // The historical source museum is a SHA-256-bound, byte-preserved
      // publication of 1993-1996 source. DOS paths in that source are program
      // literals, not workstation-path leaks. Keep every other rule active.
      if (
        rule.name === "Windows absolute path" &&
        relativeFile.startsWith(historicalSourceArchivePrefix)
      ) {
        continue;
      }
      findings.push({
        file: relativeFile,
        line: i + 1,
        rule: rule.name,
        text: line.trim().slice(0, 220)
      });
    }
  }

  if ([".md", ".mdx"].includes(path.extname(file))) {
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      if (!/^\s*\|/.test(line)) continue;
      const withoutInlineCode = line.replace(/`[^`]*`/g, "");
      if (!/<\/?[A-Za-z][^>]*>/.test(withoutInlineCode)) continue;
      findings.push({
        file: path.relative(root, file),
        line: i + 1,
        rule: "raw HTML-like token in Markdown table",
        text: line.trim().slice(0, 220)
      });
    }
  }
}

for (const dir of scanRoots) {
  const full = path.join(root, dir);
  if (fs.existsSync(full)) walk(full);
}

if (findings.length) {
  console.error("Public content guard failed. Remove local machine paths before publishing.\n");
  for (const finding of findings) {
    console.error(`${finding.file}:${finding.line} [${finding.rule}] ${finding.text}`);
  }
  process.exit(1);
}

console.log("Public content guard passed.");
