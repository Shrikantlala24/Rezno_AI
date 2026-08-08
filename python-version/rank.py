from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from models import ArxivPaper, RankedPaper

MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: List[str]) -> np.ndarray:
    """Normalized embeddings, so a dot product is the cosine similarity."""
    return _get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)


def rank(papers: List[ArxivPaper], query: str, top_k: int = 20) -> List[RankedPaper]:
    """Semantic-only ranking: cosine similarity of MiniLM embeddings against the query."""
    if not papers:
        return []

    doc_vecs = embed([f"{p.title}. {p.summary}" for p in papers])
    query_vec = embed([query])[0]

    scores = doc_vecs @ query_vec
    order = np.argsort(-scores)[:top_k]

    return [
        RankedPaper(**papers[i].model_dump(), relevance_score=float(scores[i]))
        for i in order
    ]
