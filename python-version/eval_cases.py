"""Retrieval eval — do the papers we know should surface actually surface?

Each case lists arxiv_ids hand-picked as clearly relevant. These are recall
anchors, not an exhaustive answer key: a paper missing from `expected` is not
necessarily irrelevant, but every id in `expected` should rank highly. Compare
runs against each other, not against an absolute target.
"""

from typing import List

from models import RankedPaper

CASES = [
    {
        "query": "how do retrieval augmented generation systems reduce hallucination in LLMs",
        # RAG (Lewis), Self-RAG, FreshLLMs, Atlas, REALM
        "expected": ["2005.11401", "2310.11511", "2310.03214", "2208.03299", "2002.08909"],
    },
    {
        "query": "methods for extending the context window of transformers efficiently",
        # Longformer, BigBird, RoFormer/RoPE, FlashAttention, Ring Attention
        "expected": ["2004.05150", "2007.14062", "2104.09864", "2205.14135", "2310.01889"],
    },
    {
        "query": "parameter efficient fine tuning of large language models",
        # LoRA, QLoRA, Prefix-Tuning, Adapters, Power of Scale (prompt tuning)
        "expected": ["2106.09685", "2305.14314", "2101.00190", "1902.00751", "2104.08691"],
    },
    {
        "query": "training language models to follow instructions with human feedback",
        # InstructGPT, DPO, Constitutional AI, Summarize from HF, Llama 2
        "expected": ["2203.02155", "2305.18290", "2212.08073", "2009.01325", "2307.09288"],
    },
    {
        "query": "mixture of experts architectures for scaling model capacity",
        # Switch Transformer, GShard, Outrageously Large NN, ST-MoE, Mixtral
        "expected": ["2101.03961", "2006.16668", "1701.06538", "2202.08906", "2401.04088"],
    },
]


def _base(arxiv_id: str) -> str:
    """Strip version suffix: '2005.11401v4' -> '2005.11401'."""
    return arxiv_id.split("v")[0]


def score_case(expected: List[str], ranked: List[RankedPaper], k: int = 20) -> dict:
    found = {_base(p.arxiv_id) for p in ranked[:k]}
    hits = [e for e in expected if e in found]
    misses = [e for e in expected if e not in found]
    ranks = {}
    for i, p in enumerate(ranked[:k], 1):
        b = _base(p.arxiv_id)
        if b in expected and b not in ranks:
            ranks[b] = i
    return {
        "recall": len(hits) / len(expected),
        "hits": hits,
        "misses": misses,
        "ranks": ranks,
        "pool_hits": len(hits),
    }
