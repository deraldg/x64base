"use client";

import { useEffect } from "react";

// Pagefind's UI script attaches this global once loaded from the generated /pagefind/ bundle.
declare global {
  interface Window {
    PagefindUI: new (opts: Record<string, unknown>) => void;
  }
}

// Loads the Pagefind UI (built into /pagefind/ by `pagefind --site out` during the build) and
// mounts it into #search. The bundle exists only in a built/served site, not under `next dev`.
export default function SearchClient() {
  useEffect(() => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "/pagefind/pagefind-ui.css";
    document.head.appendChild(css);

    const js = document.createElement("script");
    js.src = "/pagefind/pagefind-ui.js";
    js.async = true;
    js.onload = () => {
      new window.PagefindUI({ element: "#search", showSubResults: true });
    };
    document.body.appendChild(js);
  }, []);

  return <div id="search" />;
}
