"""web_search.py
Wraps Tavily search. One function in, list of raw result dicts out.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")


def web_search(query_list: List[str], search_depth: str = "advanced") -> List[Dict]:
    """Run Tavily search for each query in query_list, sequentially.

    Returns a list of Tavily result dicts (one per query).
    Each dict has: query, answer, results (list of {title, url, content, score, ...}), etc.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("[web_search] TAVILY_API_KEY not found in environment.")
        return []

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
    except Exception as e:
        print(f"[web_search] TavilyClient initialization failed: {e}")
        return []

    web_results = []

    for query in query_list:
        try:
            res = client.search(
                query=query, search_depth=search_depth, include_answer=True
            )
            web_results.append(res)
        except Exception as e:
            print(f"[web_search] query failed: {query!r} -> {e}")
            continue

    return web_results
