"""The maintenance console must stay readable in BOTH themes.

WHY THIS EXISTS (AIF-118, 2026-08-17)
    The console shipped dark-only: `color-scheme: dark`, one `:root`, and 32 hex
    literals scattered through the rules. Adding a light theme is easy; keeping
    one is not, because the failure mode is silent and one-sided. A rule that
    hardcodes a dark background still renders -- it just renders dark text on
    dark, in the theme you were not looking at. Nothing errors, nothing logs,
    and the person who notices is a user, later.

    This project has already paid for that shape twice on the website:
      - a `prose` background overridden without its foreground, leaving code
        blocks at 1.2:1 in light mode ("ghost scripts");
      - a hero caption at 1.24:1 that survived review because the reviewer's
        browser was in dark mode.
    Both were found by measuring, neither by looking.

WHAT IT ASSERTS, AND WHY EACH ARM EARNS ITS PLACE
    1. no colour literal outside the two palette blocks -- the mechanical
       guarantee that a rule cannot pin one theme's colour;
    2. every var() referenced is actually defined -- an undefined custom
       property silently falls back to nothing, which for `color` means
       inherited text on a themed background;
    3. dark only OVERRIDES -- a variable defined solely in `html.dark` is
       undefined in light, arm 2's failure with extra steps;
    4. contrast >= 4.5:1 on both themes for the pairs that carry meaning;
    5. the no-flash script exists and precedes <style> -- otherwise the page
       paints light then snaps, which is what the script is for.

PROVEN TO FAIL. Four mutations, each reverted: reintroduce a hex literal in a
rule; reference an undefined variable; define a variable only in `html.dark`;
darken --bg toward --dim until a pair drops under 4.5:1.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

CONSOLE = Path(__file__).resolve().parents[1] / "maint_console.html"

# Pairs that carry meaning. Not exhaustive by design: every one of these is a
# place where text sits on a surface that the theme changes.
PAIRS = [
    ("body text", "tx", "bg"),
    ("muted text", "dim", "bg"),
    ("muted on panel", "dim", "panel"),
    ("links and accent", "acc", "bg"),
    ("accent on panel", "acc", "panel"),
    ("ok status", "ok", "panel"),
    ("warn status", "warn", "panel"),
    ("bad status", "bad", "panel"),
    ("closed rows", "dim2", "panel"),
    ("table head", "dim", "thead-bg"),
    ("pre output", "pre-tx", "pre-bg"),
    ("safety notice", "warn-tx", "warn-bg"),
    ("danger button", "bad-tx", "danger-bg"),
    ("readonly input", "dim", "ro-bg"),
    ("text on hovered row", "tx", "row-hover"),
    ("text on selected table", "tx", "sel-bg"),
    ("brandmark glyph", "mark-tx", "mark-a"),
]
MIN_RATIO = 4.5


def load():
    return CONSOLE.read_text(encoding="utf-8")


def palette(text: str, selector: str) -> dict[str, str]:
    i = text.find(selector + " {")
    assert i >= 0, f"{selector} block not found"
    i += len(selector) + 2
    j = text.find("\n}", i)
    return {
        k: v.split("/*")[0].strip()
        for k, v in re.findall(r"--([\w-]+):\s*([^;]+);", text[i:j])
    }


def rgb(value: str):
    m = re.match(r"#([0-9a-fA-F]{6})$", value)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    return tuple(int(x) for x in m.groups()) if m else None


def luminance(c):
    def chan(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(c[0]) + 0.7152 * chan(c[1]) + 0.0722 * chan(c[2])


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class ConsoleThemeTest(unittest.TestCase):
    def setUp(self):
        self.t = load()
        self.style = self.t[self.t.find("<style>"):self.t.find("</style>")]
        self.light = palette(self.t, ":root")
        self.dark = dict(self.light)
        self.dark.update(palette(self.t, "html.dark"))

    def test_no_colour_literal_outside_the_palette_blocks(self):
        after_dark = self.style[self.style.find("\n}", self.style.find("html.dark")):]
        found = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", after_dark)
        self.assertEqual(
            found, [],
            "colour literal in a rule: it cannot follow the theme, so it will be "
            f"wrong in one of them. Move it into both palettes. Found: {found}",
        )

    def test_every_referenced_variable_is_defined(self):
        used = set(re.findall(r"var\(--([\w-]+)\)", self.style))
        missing = sorted(used - set(self.light))
        self.assertEqual(
            missing, [],
            f"var() references an undefined property {missing}; it resolves to "
            "nothing rather than erroring, so the element inherits whatever it "
            "sat on",
        )

    def test_dark_only_overrides_and_never_introduces(self):
        only_dark = sorted(set(palette(self.t, "html.dark")) - set(self.light))
        self.assertEqual(
            only_dark, [],
            f"{only_dark} exist only under html.dark, so they are undefined in "
            "the light theme -- which is the default",
        )

    def test_contrast_holds_in_both_themes(self):
        for name, theme in (("light", self.light), ("dark", self.dark)):
            for label, fg, bg in PAIRS:
                with self.subTest(theme=name, pair=label):
                    f, b = rgb(theme.get(fg, "")), rgb(theme.get(bg, ""))
                    self.assertIsNotNone(f, f"--{fg} unresolved in {name}")
                    self.assertIsNotNone(b, f"--{bg} unresolved in {name}")
                    ratio = contrast(f, b)
                    self.assertGreaterEqual(
                        ratio, MIN_RATIO,
                        f"{name}: {label} is {ratio:.2f}:1, under {MIN_RATIO}:1. "
                        "This is the failure that looks fine to whoever is in the "
                        "other theme.",
                    )

    def test_no_flash_script_runs_before_the_stylesheet(self):
        script = self.t.find("localStorage.getItem('theme')")
        style = self.t.find("<style>")
        self.assertGreater(script, 0, "the no-flash theme script is missing")
        self.assertLess(script, style,
                        "the theme script must precede <style> so the class is "
                        "applied before first paint")

    def test_it_shares_the_website_preference_key(self):
        # One key across both surfaces. Three disagreeing theme implementations
        # is a defect this project has already recorded and paid for.
        self.assertIn("localStorage.getItem('theme')", self.t)
        self.assertIn('localStorage.setItem("theme"', self.t)

    def test_server_template_placeholders_survive(self):
        # maint_server.render() substitutes these; losing one serves a broken page.
        for token in ("__API_BASE__", "__WRITE__", "__WRITE_TOKEN__"):
            with self.subTest(token=token):
                self.assertIn(token, self.t)


if __name__ == "__main__":
    unittest.main()
