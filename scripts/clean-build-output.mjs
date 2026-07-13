import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const generatedPaths = [".next", "out", "dist"];

for (const relativePath of generatedPaths) {
  fs.rmSync(path.join(root, relativePath), { recursive: true, force: true });
}

console.log(`Cleared generated build output: ${generatedPaths.join(", ")}`);
