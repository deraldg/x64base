"use client";

import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";

/**
 * Theme preference: light (default, owner ruling 2026-08-11) / dark / system.
 * Persists to localStorage("theme"); the no-flash script in layout.tsx applies
 * the stored choice before first paint, so this component only has to keep the
 * class in sync after hydration and while the user cycles.
 */
type Mode = "light" | "dark" | "system";
const ORDER: Mode[] = ["light", "dark", "system"];

function apply(mode: Mode) {
  const dark =
    mode === "dark" ||
    (mode === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = (localStorage.getItem("theme") as Mode) || "light";
    setMode(ORDER.includes(stored) ? stored : "light");
    setMounted(true);
    // In system mode, follow the OS if it changes while the page is open.
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const cur = (localStorage.getItem("theme") as Mode) || "light";
      if (cur === "system") apply(cur);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const next = ORDER[(ORDER.indexOf(mode) + 1) % ORDER.length];
  const cycle = () => {
    localStorage.setItem("theme", next);
    setMode(next);
    apply(next);
  };

  const Icon = mode === "dark" ? Moon : mode === "system" ? Monitor : Sun;

  // Owner report 2026-08-11: the toggle "went missing". Measured: it was in the
  // built DOM the whole time. A bare 16px muted-grey glyph on a translucent
  // card reads as decoration rather than a control, and in light mode it
  // nearly vanishes -- so the defect was AFFORDANCE, not absence. Fixed with
  // full-contrast foreground, a solid card, and a text label naming the
  // current mode, so the control says what it is and what it will do next.
  // `mode` starts "light" on server and client alike, so labelling it
  // introduces no hydration mismatch.
  //
  // Round five, 2026-08-14, LIGHT MODE ONLY -- and that qualifier is the whole
  // finding. Rounds one through four were all reported and fixed against the
  // dark palette, so nobody checked the light one. Measured contrast of the
  // border against the banner strip it sits on:
  //
  //     dark   border-brand/60  4.14:1  passes
  //     light  border-brand/60  2.28:1  FAILS (WCAG wants 3:1 for a control)
  //
  // The fill contributes nothing in either theme (1.04:1 light, 1.05:1 dark):
  // the button is bg-card and the strip is bg-card/40 over a near-identical
  // --bg, so the two are the same colour. The border was the ONLY thing making
  // this look like a button, and in light mode --brand is darkened for contrast
  // on white, which at 60% opacity lands it under the threshold. Same markup,
  // same opacity, opposite outcome, because the palettes are not symmetric.
  // Full opacity takes light to 4.29:1 and dark to 9.74:1.
  //
  // Lesson worth more than the fix: "fixed the theme toggle" was said four
  // times about a control that was only ever checked in one theme.
  return (
    <button
      type="button"
      onClick={cycle}
      title={mounted ? `Theme: ${mode} -- click for ${next}` : "Theme"}
      aria-label={mounted ? `Theme is ${mode}. Switch to ${next}.` : "Theme"}
      className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-brand bg-card px-2 py-0.5 text-fg shadow-sm transition hover:bg-brand hover:text-bg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
    >
      <Icon size={14} />
      <span className="text-xs font-semibold capitalize">{mode}</span>
      <span className="text-[10px] text-muted">theme</span>
    </button>
  );
}
