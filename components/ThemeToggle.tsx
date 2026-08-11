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

  return (
    <button
      type="button"
      onClick={cycle}
      title={mounted ? `Theme: ${mode} — click for ${next}` : "Theme"}
      aria-label={mounted ? `Theme is ${mode}. Switch to ${next}.` : "Theme"}
      className="inline-flex items-center justify-center rounded-xl border border-border bg-card/60 p-2 text-muted transition hover:text-fg"
    >
      <Icon size={16} />
    </button>
  );
}
