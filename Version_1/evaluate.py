import argparse
import time

from eval_cases import CASES, _base, score_case
from rank import rank
from search import search


def run(top_k: int = 20, expand: bool = False) -> None:
    if expand:
        from plan_query import plan_query

    total_recall = 0.0
    total_pool_recall = 0.0

    for case in CASES:
        query, expected = case["query"], case["expected"]
        t0 = time.time()

        queries = plan_query(query) if expand else [query]
        papers = search(queries)
        ranked = rank(papers, query, top_k=top_k)

        # pool recall isolates search from ranking: a paper that never entered
        # the candidate pool is a search failure, not a ranking failure
        pool_ids = {_base(p.arxiv_id) for p in papers}
        pool_recall = len([e for e in expected if e in pool_ids]) / len(expected)
        r = score_case(expected, ranked, k=top_k)

        total_recall += r["recall"]
        total_pool_recall += pool_recall

        print(f"\n{query}")
        if expand:
            for q in queries:
                print(f"    q: {q}")
        print(
            f"  pool {len(papers):4}  pool_recall {pool_recall:.0%}"
            f"  recall@{top_k} {r['recall']:.0%}  ({time.time() - t0:.1f}s)"
        )
        if r["ranks"]:
            hits = ", ".join(f"{k}@{v}" for k, v in sorted(r["ranks"].items(), key=lambda x: x[1]))
            print(f"  hits:   {hits}")
        if r["misses"]:
            in_pool = [m for m in r["misses"] if m in pool_ids]
            print(f"  missed: {', '.join(r['misses'])}")
            if in_pool:
                print(f"          ({', '.join(in_pool)} were in pool but ranked out — ranking issue)")

    n = len(CASES)
    print(f"\n{'=' * 60}")
    print(f"mean pool_recall  {total_pool_recall / n:.1%}   (search quality)")
    print(f"mean recall@{top_k}   {total_recall / n:.1%}   (search + ranking)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieval eval")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--expand", action="store_true", help="use plan_query expansion")
    args = parser.parse_args()
    run(top_k=args.top_k, expand=args.expand)
