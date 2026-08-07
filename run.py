import argparse
import time
from collections import Counter

from pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Research agent — full pipeline, CLI")
    parser.add_argument("query", help="natural-language research question")
    parser.add_argument("--top-k", type=int, default=20, help="papers kept after ranking")
    parser.add_argument("--show", type=int, default=8, help="papers printed and synthesized")
    parser.add_argument("--no-synth", action="store_true", help="skip the LLM synthesis call")
    parser.add_argument("--no-expand", action="store_true", help="skip query expansion")
    parser.add_argument("--no-graph", action="store_true", help="skip extraction and graph")
    args = parser.parse_args()

    t0 = time.time()
    last = {"t": t0}

    def progress(message: str) -> None:
        now = time.time()
        print(f"  [{now - t0:5.1f}s] {message}")
        last["t"] = now

    result = run_pipeline(
        args.query,
        top_k=args.top_k,
        show=args.show,
        expand=not args.no_expand,
        with_graph=not args.no_graph,
        with_synthesis=not args.no_synth,
        on_progress=progress,
    )

    print(f"\nqueries ({len(result.queries)}):")
    for q in result.queries:
        print(f"  {q}")
    print(f"\n{result.candidate_count} candidates -> top {len(result.papers)}\n")

    for i, p in enumerate(result.papers[: args.show], 1):
        print(f"{i:2}. [{p.relevance_score:.3f}] {p.title}")
        print(f"    {p.arxiv_id}  {p.primary_category}  {p.published[:10]}")

    if result.graph:
        kinds = Counter(e.type for e in result.graph.edges)
        concepts = sum(1 for n in result.graph.nodes if n.type == "concept")
        print(
            f"\ngraph: {len(result.graph.nodes)} nodes ({concepts} concepts), "
            f"{kinds['MENTIONS']} MENTIONS, {kinds['SIMILAR_TO']} SIMILAR_TO"
        )

    if result.synthesis:
        print("\n--- summary ---")
        print(result.synthesis.summary)
        print(f"\ncitations: {', '.join(result.synthesis.citations)}")

    print(f"\ntotal: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
