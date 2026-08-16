/**
 * RETRO -- the capture manifest.
 *
 * LOCAL ONLY. This page is stripped from every build output and the publish
 * script aborts if it survives. See app/retro/page.tsx for the three layers.
 *
 * WHAT THIS IS
 *   One timeline, several parallel tracks. The point is CONTEMPORANEITY: what
 *   1985 looked like across machines, operating systems, Windows, browsers and
 *   consoles at the same moment -- which is the thing five separate "history
 *   of X" pages cannot show you, and the reason this is not five pages.
 *
 *   Every entry also carries the FEATURES it demonstrates, which gives the
 *   second reading: the arrival of the mouse, or of overlapping windows, laid
 *   out across every platform that got one. Same data, two lessons.
 *
 * WHAT THIS IS NOT
 *   The database lineage lives in docs/cases/CASE_HIST_* and has its own
 *   generator (tools/fullstack_docs/build_historical_source_museum.py). RETRO
 *   links there and does not restate it. One home per artifact -- the same
 *   rule that keeps labs in LabTalk.
 *
 * PROVENANCE IS NOT OPTIONAL
 *   This is headed for LabTalk as teaching material, so every capture must be
 *   attributable. A public educational page of unattributed screenshots pulled
 *   off the web is exactly the liability the project's licensing work exists to
 *   avoid. Recording the source also survives link rot: when a hotlink dies,
 *   an attributed citation still points a reader at the original.
 */

export type Tier =
  | "hotlink" // someone else's image, cited and linked, not copied
  | "local"   // your own capture -- yours outright, cannot rot
  | "live";   // runs in the page (SAE, v86)

export type TrackId =
  | "machines"
  | "os"
  | "windows"
  | "posix"
  | "browsers"
  | "consoles";

export type FeatureId =
  | "command-line"
  | "full-screen-text"
  | "mouse"
  | "overlapping-windows"
  | "color"
  | "multitasking"
  | "networking"
  | "filesystem"
  | "sound"
  | "hypertext";

export type Provenance = {
  /** The PAGE you found it on, not just the file. A reader can chase this. */
  source_page: string;
  /** Who to credit. "own capture" when it is yours. */
  credit: string;
  /** ISO date you retrieved it. Link rot is measured against this. */
  retrieved: string;
  /** Free text: licence, terms, or the capture route (VMware, SAE, hardware). */
  note?: string;
};

export type Capture = {
  id: string;
  era: string;
  track: TrackId;
  title: string;
  /** Year or range as displayed. Sorting uses `year`. */
  date: string;
  year: number;
  features: FeatureId[];
  /**
   * Full-size image. For hotlinks prefer the source's own resized derivative
   * (Wikimedia serves arbitrary widths by URL) so the full file is never pulled.
   */
  image_url?: string;
  /** Optional smaller derivative. Falls back to image_url. */
  thumb_url?: string;
  /**
   * Native resolution, e.g. "320x200". Does double duty: it sets the thumbnail
   * aspect ratio, and it IS a teaching fact. These screens were not all the
   * same shape -- CGA is 320x200 with non-square pixels, the Amiga runs
   * 640x256 interlaced, the Game Boy is 160x144. Forcing them into uniform
   * square tiles misrepresents every one of them, so thumbnails letterbox to a
   * fixed HEIGHT and let width vary. The grid looks different across eras
   * because the machines were different.
   */
  native_res?: string;
  tier: Tier;
  provenance?: Provenance;
  /** One line on why this capture is worth looking at. */
  note?: string;
};

export const TRACKS: { id: TrackId; label: string }[] = [
  { id: "machines", label: "Machines" },
  { id: "os", label: "Operating systems" },
  { id: "windows", label: "Windows" },
  { id: "posix", label: "POSIX / Unix" },
  { id: "browsers", label: "Browsers" },
  { id: "consoles", label: "Gaming machines" },
];

export const FEATURES: { id: FeatureId; label: string }[] = [
  { id: "command-line", label: "Command line" },
  { id: "full-screen-text", label: "Full-screen text UI" },
  { id: "mouse", label: "Mouse" },
  { id: "overlapping-windows", label: "Overlapping windows" },
  { id: "color", label: "Colour" },
  { id: "multitasking", label: "Multitasking" },
  { id: "networking", label: "Networking" },
  { id: "filesystem", label: "Filesystem" },
  { id: "sound", label: "Sound" },
  { id: "hypertext", label: "Hypertext" },
];

export const ERAS: { id: string; label: string; blurb: string }[] = [
  { id: "1979-84", label: "1979 - 1984", blurb: "8-bit home machines, CP/M, the IBM PC arrives." },
  { id: "1985-89", label: "1985 - 1989", blurb: "The Amiga, the AT, DOS matures, consoles return." },
  { id: "1990-95", label: "1990 - 1995", blurb: "Linux 0.x, Windows 3.1 and 95, Mosaic, the SNES." },
  { id: "1996-05", label: "1996 - 2005", blurb: "NT/XP, OS X, the browser wars, PS2." },
  { id: "2006-now", label: "2006 - now", blurb: "x86-64 and ARM, WSL, modern POSIX." },
];

/**
 * Entries. EMPTY ON PURPOSE.
 *
 * The page is designed to be useful at ten captures and better at five
 * hundred, so it renders honest empty slots rather than looking broken while
 * unfinished -- the same posture as the ECO map and the release stamp.
 *
 * Suggested first pass: 1985-89, where the assets are strongest (Amiga Forever
 * for Kickstart and Workbench, SAE for a live Amiga, v86 with FreeDOS for the
 * PC lane, your own VMware captures for MS-DOS).
 *
 * Adding one:
 *   {
 *     id: "1985-amiga-workbench",
 *     era: "1985-89", track: "machines",
 *     title: "AmigaOS Workbench 1.x", date: "1985", year: 1985,
 *     features: ["mouse", "overlapping-windows", "color", "multitasking"],
 *     image_url: "https://...", thumb_url: "https://...",
 *     native_res: "640x256",
 *     tier: "hotlink",
 *     provenance: {
 *       source_page: "https://commons.wikimedia.org/wiki/File:...",
 *       credit: "Wikimedia Commons",
 *       retrieved: "2026-08-16",
 *       note: "check the file's licence before this page goes public",
 *     },
 *     note: "Pre-emptive multitasking on a home machine, two years before Windows 2.0.",
 *   },
 */
export const CAPTURES: Capture[] = [];
