"""web_search.py
Wraps Tavily search. One function in, list of raw result dicts out.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")


def _fallback_http_search(query: str) -> Dict:
    """Zero-dependency fallback search using DuckDuckGo HTML / web scraping."""
    import re
    import urllib.parse
    import urllib.request

    results = []
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extract snippet text from result items
            snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL
            )
            urls = re.findall(
                r'class="result__url"[^>]*href="([^"]*)"', html, re.DOTALL
            )
            titles = re.findall(
                r'class="result__title"[^>]*>(.*?)</a>', html, re.DOTALL
            )
            for i in range(min(4, len(snippets))):
                clean_snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                clean_title = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else query
                clean_url = urls[i].strip() if i < len(urls) else ""
                results.append({
                    "title": clean_title or query,
                    "url": clean_url,
                    "content": clean_snippet,
                })
    except Exception as e:
        print(f"[web_search] Fallback HTTP search warning: {e}")

    return {
        "query": query,
        "answer": results[0]["content"] if results else "",
        "results": results,
    }


def _fallback_ddg_search(query: str) -> Dict:
    """Fallback search using duckduckgo_search or HTTP fallback if Tavily is unavailable."""
    try:
        from duckduckgo_search import DDGS  # type: ignore
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            formatted = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "content": r.get("body", r.get("snippet", "")),
                }
                for r in results
            ]
            return {
                "query": query,
                "answer": results[0].get("body", "") if results else "",
                "results": formatted,
            }
    except Exception:
        return _fallback_http_search(query)


def web_search(query_list: List[str], search_depth: str = "advanced") -> List[Dict]:
    """Run web search for each query in query_list.

    Uses TavilyClient if TAVILY_API_KEY is configured, else falls back to DuckDuckGo/HTTP search.
    Returns a list of result dicts (one per query).
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if api_key:
        try:
            from tavily import TavilyClient  # type: ignore

            client = TavilyClient(api_key=api_key)
            web_results = []
            for query in query_list:
                try:
                    res = client.search(
                        query=query, search_depth=search_depth, include_answer=True
                    )
                    web_results.append(res)
                except Exception as e:
                    print(f"[web_search] Tavily query failed: {query!r} -> {e}")
                    web_results.append(_fallback_ddg_search(query))
            return web_results
        except Exception as e:
            print(f"[web_search] TavilyClient initialization failed: {e}")

    # Fallback when Tavily key is not set
    return [_fallback_ddg_search(q) for q in query_list]
