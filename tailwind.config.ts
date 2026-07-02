import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        card: "rgb(var(--card) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        brand: "rgb(var(--brand) / <alpha-value>)",
        teal: "rgb(var(--teal) / <alpha-value>)",
        orange: "rgb(var(--orange) / <alpha-value>)",
        green: "rgb(var(--green) / <alpha-value>)",
        purple: "rgb(var(--purple) / <alpha-value>)",
        red: "rgb(var(--red) / <alpha-value>)"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(0,0,0,.25)"
      }
    }
  },
  plugins: [typography]
} satisfies Config;
