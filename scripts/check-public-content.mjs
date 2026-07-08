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
  }
];

const ignoreDirs = new Set([".git", ".next", "node_modules", "out"]);
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
  for (const rule of blocked) {
    for (let i = 0; i < lines.length; i += 1) {
      rule.pattern.lastIndex = 0;
      const line = lines[i];
      if (!rule.pattern.test(line)) continue;
      findings.push({
        file: path.relative(root, file),
        line: i + 1,
        rule: rule.name,
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
