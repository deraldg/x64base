import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const configPath = path.join(root, "scripts", "site-freshness-contracts.json");

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function valueAt(source, expression) {
  const [keyPath, format] = expression.split(":", 2);
  const value = keyPath.split(".").reduce((current, key) => {
    if (current === null || current === undefined || !(key in current)) {
      throw new Error(`authority field not found: ${keyPath}`);
    }
    return current[key];
  }, source);

  if (format === "comma") {
    if (typeof value !== "number") {
      throw new Error(`comma format requires a number: ${keyPath}`);
    }
    return value.toLocaleString("en-US");
  }
  if (format) throw new Error(`unknown authority format: ${format}`);
  return String(value);
}

function expand(template, authority) {
  return template.replace(/\{([^{}]+)\}/g, (_, expression) =>
    valueAt(authority, expression)
  );
}

function evaluate(contract, authority, targetText) {
  const findings = [];
  for (const template of contract.mustContain ?? []) {
    const expected = expand(template, authority);
    if (!targetText.includes(expected)) findings.push(expected);
  }
  for (const [beforeTemplate, afterTemplate] of contract.mustAppearBefore ?? []) {
    const before = expand(beforeTemplate, authority);
    const after = expand(afterTemplate, authority);
    const beforeIndex = targetText.indexOf(before);
    const afterIndex = targetText.indexOf(after);
    if (beforeIndex < 0 || afterIndex < 0 || beforeIndex >= afterIndex) {
      findings.push(`expected order: ${before} BEFORE ${after}`);
    }
  }
  return findings;
}

const config = readJson(configPath);
const loaded = config.contracts.map((contract) => {
  const authorityPath = path.join(root, contract.authority);
  const targetPath = path.join(root, contract.target);
  if (!fs.existsSync(authorityPath)) {
    throw new Error(`${contract.id}: authority missing: ${contract.authority}`);
  }
  if (!fs.existsSync(targetPath)) {
    throw new Error(`${contract.id}: target missing: ${contract.target}`);
  }
  return {
    contract,
    authority: readJson(authorityPath),
    targetText: fs.readFileSync(targetPath, "utf8")
  };
});

let failed = false;
for (const item of loaded) {
  const findings = evaluate(item.contract, item.authority, item.targetText);
  if (!findings.length) continue;
  failed = true;
  console.error(`Freshness contract failed: ${item.contract.id}`);
  for (const expected of findings) console.error(`  missing: ${expected}`);
}

if (failed) process.exit(1);

if (process.argv.includes("--self-test")) {
  for (const item of loaded) {
    const expected = expand(item.contract.mustContain[0], item.authority);
    const staleText = item.targetText.split(expected).join("__STALE_SNAPSHOT__");
    if (staleText === item.targetText) {
      throw new Error(`${item.contract.id}: self-test could not create a stale snapshot`);
    }
    if (!evaluate(item.contract, item.authority, staleText).length) {
      throw new Error(`${item.contract.id}: self-test accepted deliberate staleness`);
    }
  }
  console.log(
    `Site freshness self-test passed: deliberate staleness was rejected by ${loaded.length} contract(s).`
  );
}

console.log(`Site freshness check passed: ${loaded.length} contract(s).`);
