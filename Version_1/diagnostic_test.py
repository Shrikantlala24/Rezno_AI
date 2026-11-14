"""Diagnostic test: probe arXiv search configuration and relevance ranking."""
import arxiv
import sys

# Target papers we're searching for
TARGETS = {
    "2005.11401": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    "2106.09685": "LoRA: Low-Rank Adaptation of Large Language Models",
    "2004.05150": "Longformer: The Long-Document Transformer",
}

# Verify targets exist
print("=" * 70)
print("STEP 1: Verify target papers exist via direct ID lookup")
print("=" * 70)
client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
for paper_id, title in TARGETS.items():
    request = arxiv.Search(id_list=[paper_id])
    results = list(client.results(request))
    if results:
        r = results[0]
        print(f"✓ {paper_id}: {r.title}")
    else:
        print(f"✗ {paper_id}: NOT FOUND")

# Test queries for each target
print("\n" + "=" * 70)
print("STEP 2: Search with different configurations")
print("=" * 70)

test_configs = [
    {
        "name": "Relevance, max=80",
        "sort": arxiv.SortCriterion.Relevance,
        "max_results": 80,
    },
    {
        "name": "Relevance, max=200",
        "sort": arxiv.SortCriterion.Relevance,
        "max_results": 200,
    },
    {
        "name": "Relevance, max=500",
        "sort": arxiv.SortCriterion.Relevance,
        "max_results": 500,
    },
    {
        "name": "SubmittedDate desc, max=200",
        "sort": arxiv.SortCriterion.SubmittedDate,
        "max_results": 200,
    },
]

test_queries = [
    ("raw: retrieval augmented generation", "retrieval augmented generation"),
    ("exact: retrieval-augmented generation", "retrieval-augmented generation"),
    ("title field: retrieval-augmented generation", 'ti:"Retrieval-Augmented Generation"'),
    ("abs + category", 'abs:"retrieval-augmented generation" AND cat:cs.CL'),
]

for query_name, query_text in test_queries:
    print(f"\nQuery: {query_name}")
    print(f"  Text: {query_text}")
    
    for config in test_configs:
        request = arxiv.Search(
            query=query_text,
            max_results=config["max_results"],
            sort_by=config["sort"],
        )
        
        results = list(client.results(request))
        
        # Look for target paper (2005.11401)
        found_ids = {r.get_short_id(): i for i, r in enumerate(results, 1)}
        
        if "2005.11401" in found_ids:
            rank = found_ids["2005.11401"]
            print(f"    [{config['name']}] ✓ 2005.11401 at rank {rank}")
        else:
            print(f"    [{config['name']}] ✗ 2005.11401 NOT FOUND (checked {len(results)} results)")

# Deep dive on a specific query
print("\n" + "=" * 70)
print("STEP 3: Deep dive on Relevance search (max=500)")
print("=" * 70)

request = arxiv.Search(
    query="retrieval augmented generation",
    max_results=500,
    sort_by=arxiv.SortCriterion.Relevance,
)

results = list(client.results(request))
print(f"Total results returned: {len(results)}")

target_ranks = {}
for i, r in enumerate(results, 1):
    if r.get_short_id() in TARGETS:
        target_ranks[r.get_short_id()] = (i, r.title)

print("\nTarget papers found in Relevance-sorted pool:")
for paper_id in sorted(TARGETS.keys()):
    if paper_id in target_ranks:
        rank, title = target_ranks[paper_id]
        print(f"  Rank {rank:4d}: {paper_id} - {title[:60]}")
    else:
        print(f"  NOT FOUND: {paper_id}")

# Show top 20 for context
print("\nTop 20 results from 'retrieval augmented generation' (Relevance):")
for i, r in enumerate(results[:20], 1):
    print(f"  {i:2d}. {r.get_short_id()} - {r.title[:70]}")

print("\nDone.")
