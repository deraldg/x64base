import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const scanRoots = ["app", "components", "config", "content", "public"];
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
