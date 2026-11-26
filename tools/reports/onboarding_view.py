"""Render the local Portal's read-only overview from the onboarding sources."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from labtalk.ai_portal import recall  # noqa: E402


ONBOARDING_PATH = "/AI/onboarding"
SEED = "labtalk/ai_portal/AI_TIER1_SEED_V1.md"
LAWS = "labtalk/ai_portal/AI_AGENT_LAWS_SEED_V1.md"
SNAPSHOT = "labtalk/ai_portal/TIER0_STATE.md"
READERS = {
    SEED: ("tier-1-seed", "Tier 1 Seed"),
    LAWS: ("agent-laws", "Agent Laws"),
    SNAPSHOT: ("tier-0-snapshot", "Tier 0 snapshot"),
}

STYLE = """
:root{color-scheme:light;font:16px/1.55 system-ui,sans-serif;color:#0f172a;background:#f3f6f9}
*{box-sizing:border-box}body{margin:0}
header{background:#0f172a;color:#dbeafe;padding:.75rem max(1rem,calc((100% - 66rem)/2))}
header a{color:#bfdbfe}main{max-width:68rem;margin:auto;padding:1.75rem 1rem 4rem}
h1,h2{line-height:1.18}h1{margin:.35rem 0}h2{margin:.2rem 0 .65rem}
a{color:#0b6673;text-underline-offset:.18em}
.badge{display:inline-block;border-radius:999px;padding:.15rem .65rem;background:#dcfce7;color:#14532d;font-size:.84rem}
.intro,.meta{color:#475569}.jump{display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;margin:.9rem 0}
section,.order{background:#fff;border:1px solid #d8e2ec;border-radius:.8rem;padding:1.2rem;margin-top:1rem}
.order ol{display:flex;flex-wrap:wrap;gap:.35rem 2.4rem;margin:.4rem 0 0;padding-left:1.4rem}
details{border-top:1px solid #e2e8f0;margin-top:.7rem;padding-top:.7rem}
summary{cursor:pointer;font-weight:600;color:#155e75}
summary:hover{text-decoration:underline}summary:focus-visible,a:focus-visible{outline:2px solid #13798a;outline-offset:3px}
li{margin:.25rem 0}code{overflow-wrap:anywhere}small{display:block;color:#475569}
pre{padding:1rem;background:#f8fafc;border-radius:.5rem;border:1px solid #e2e8f0;
white-space:pre-wrap;overflow-wrap:anywhere;max-height:35rem;overflow:auto}
"""


def source_file(root: Path, relative: str) -> Path:
    """Read only fixed sources within the local repository."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise FileNotFoundError(relative)
    return path


def reader(root: Path, relative: str, *, expanded: bool = False) -> str:
    anchor, title = READERS[relative]
    try:
        text = source_file(root, relative).read_text(encoding="utf-8-sig")
        content = f'<pre tabindex="0">{escape(text)}</pre>'
    except (OSError, UnicodeError):
        content = '<p role="status">Source unavailable in this checkout.</p>'
    opened = " open" if expanded else ""
    return (
        f'<details id="{anchor}"{opened}><summary>{title}</summary>'
        f'<p class="meta"><code>{relative}</code></p>{content}</details>'
    )


def inventory(nodes: list[dict], *, in_recall_order: bool = False) -> str:
    items = []
    ordered = nodes if in_recall_order else sorted(
        nodes, key=lambda item: (item.get("label") or item["id"]).casefold()
    )
    for node in ordered:
        label = escape(node.get("label") or node["id"])
        source = escape(node["path"])
        anchor = escape(node.get("anchor") or "")
        extra = f" &mdash; {anchor}" if anchor else ""
        items.append(f'<li>{label}<small><code>{source}</code>{extra}</small></li>')
    tag = "ol" if in_recall_order else "ul"
    return f"<{tag}>" + "".join(items) + f"</{tag}>"


def counts(nodes: list[dict]) -> str:
    files = len({node["path"] for node in nodes})
    return f"{len(nodes)} indexed entries across {files} source files"


def render(root: Path) -> str:
    source_file(root, recall.REGISTRY)
    graph = recall.load(root)
    tiers = {
        tier: [node for node in graph["nodes"] if str(node.get("tier")) == str(tier)]
        for tier in (0, 1, 2)
    }
    order = []
    for entry in graph["entry_path"]:
        relative = entry["path"]
        if relative in READERS:
            anchor, title = READERS[relative]
            order.append(f'<li><a href="#{anchor}">{title}</a></li>')
        else:
            order.append(f'<li><code>{escape(relative)}</code></li>')
    triggers = []
    for trigger in graph["triggers"]:
        nodes = [node for _, _, node in recall.walk(graph, trigger["id"])]
        label = escape(trigger.get("label") or trigger["id"])
        triggers.append(
            f'<details><summary>{label}</summary>{inventory(nodes, in_recall_order=True)}</details>'
        )
    tier1 = [node for node in tiers[1] if node["path"] not in {SEED, LAWS}]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>AI Portal Onboarding | DotTalk++</title><style>{STYLE}</style></head>
<body><header><a href="/AI/">AI Portal</a> / Onboarding</header><main>
<span class="badge">Local only &middot; Read-only</span>
<h1>AI Portal Onboarding</h1>
<p class="intro">One guide to the startup rules, the current checkout, and the references you need for a task.</p>
<nav class="jump" aria-label="Jump to a tier">
<a href="#tier-1">Tier 1: Startup rules</a>
<a href="#tier-0">Tier 0: Current state</a>
<a href="#tier-2">Tier 2: Reference</a></nav>
<div class="order"><strong>Read in this order</strong><ol>{''.join(order)}</ol>
<p class="meta">Use Tier 2 as needed after the startup reads.</p></div>
<section id="tier-1"><h2>Tier 1 &mdash; Startup rules</h2>
<p>Repository roles, authorization, safety rules, and the checks to make before you act.</p>
{reader(root, SEED)}{reader(root, LAWS)}
<details><summary>Tier 1 reference index &middot; {counts(tiers[1])}</summary>
<p class="meta">The index count includes the seed and laws above.</p>
{inventory(tier1)}</details></section>
<section id="tier-0"><h2>Tier 0 &mdash; Current state</h2>
<p>Branch and target, lane claims, handoff guidance, and recorded staleness warnings.</p>
<p class="meta">This is the saved, generated snapshot. Reloading this page reads the file again;
it does not refresh or verify the snapshot.</p>{reader(root, SNAPSHOT, expanded=True)}</section>
<section id="tier-2"><h2>Tier 2 &mdash; Reference on demand</h2>
<p>Procedures, design decisions, and evidence indexed by the Recall graph.</p>
<details><summary>Browse by task ({len(triggers)} Recall triggers)</summary>
{''.join(triggers)}</details>
<details><summary>All Tier 2 entries &middot; {counts(tiers[2])}</summary>
{inventory(tiers[2])}</details></section>
</main></body></html>"""
