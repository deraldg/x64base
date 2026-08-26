import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function assertInside(child, parent) {
  const relative = path.relative(parent, child);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Unsafe local-only output path: ${child}`);
  }
}

/**
 * Directories that exist for the maintainer and must never reach the public
 * site. One list, so adding a private surface is one edit rather than three.
 *
 *   reports -- the local report/console lane, local-only since it was built.
 *   retro   -- the RETRO playground (2026-08-15). Owner's words: "my private
 *              playground until I decide how much of it goes into labtalk and
 *              dottalkpp." It will hold emulator payloads and OS captures whose
 *              redistribution rights are unsettled, so leaking it is a
 *              licensing problem and not merely an untidy one.
 *   lab     -- the Lab (2026-08-17): work that is real but not yet a public
 *              claim. Prototypes and research inventories that would carry
 *              more authority on the public site than the work behind them
 *              justifies. First tenant: the Dewey / hierarchy experiments,
 *              moved out of /docs/dev/experimental.
 *   portal  -- the maintainer's local AI Portal console and working views.
 *              Public-safe Portal material is reviewed into /docs/labtalk;
 *              ignored local content/portal files must never become a release
 *              dependency or publication artifact.
 *
 * This list is the SECOND of three layers. The first is that the nav entry only
 * renders under local preview; the third is the publish script refusing outright
 * if a directory named here survived into out/. Any one layer failing leaves the
 * other two, which is the point.
 */
export const LOCAL_ONLY_DIRS = ["reports", "retro", "lab", "portal"];

export function stripLocalOnlyOutput({ root = process.cwd() } = {}) {
  const outDir = path.resolve(root, "out");
  const outputRoots = [
    outDir,
    path.resolve(root, "dist", "server", "public"),
    path.resolve(root, ".sites-artifact", "dist", "server", "public"),
  ];
  const removedPaths = [];

  for (const outputRoot of outputRoots) {
    for (const name of LOCAL_ONLY_DIRS) {
      const dir = path.resolve(outputRoot, name);
      assertInside(dir, outputRoot);
      if (!fs.existsSync(dir)) continue;
      fs.rmSync(dir, { recursive: true, force: true });
      removedPaths.push(dir);
    }
  }

  const staleArtifact = path.resolve(root, "x64base-sites-artifact.tar.gz");
  assertInside(staleArtifact, path.resolve(root));
  if (fs.existsSync(staleArtifact)) {
    fs.rmSync(staleArtifact, { force: true });
    removedPaths.push(staleArtifact);
  }

  return { removedPaths };
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const result = stripLocalOnlyOutput();
  if (result.removedPaths.length === 0) {
    console.log("No local-only report output found.");
  } else {
    for (const removedPath of result.removedPaths) {
      console.log(`Removed local-only or stale output: ${removedPath}`);
    }
  }
}
