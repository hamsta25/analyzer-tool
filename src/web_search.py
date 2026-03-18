"""
web_search.py — DuckDuckGo web search fallback (no API key required).

Usage:
    python src/web_search.py "search query" [--n 5] [--output out/]
"""

import argparse
import re
import sys
from pathlib import Path


def search(query: str, n: int = 5) -> list[dict]:
    """Return top-N DuckDuckGo results as a list of dicts."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        sys.exit("duckduckgo-search not found. Run: pip install duckduckgo-search")

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=n))


def results_to_markdown(query: str, results: list[dict]) -> str:
    lines = [f"# Web Search: {query}\n", f"_Top {len(results)} results from DuckDuckGo_\n"]
    for i, r in enumerate(results, start=1):
        title = r.get("title", "No title")
        url = r.get("href", "")
        body = r.get("body", "")
        lines.append(f"\n## {i}. {title}\n")
        lines.append(f"**URL:** {url}\n")
        if body:
            lines.append(f"\n{body}\n")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="DuckDuckGo web search fallback.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--output", default=None, help="Output directory (prints to stdout if omitted)")
    args = parser.parse_args()

    results = search(args.query, args.n)
    markdown = results_to_markdown(args.query, results)

    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^\w]+", "_", args.query)[:50]
        out_file = out_dir / f"search_{slug}.md"
        out_file.write_text(markdown, encoding="utf-8")
        print(f"→ {out_file}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
