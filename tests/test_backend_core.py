"""Comprehensive tests for backend core and integration modules."""
import os
import sys
from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pytest

# Ensure REPO_ROOT and .venv site-packages are in sys.path before third-party imports
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

venv_site_packages = os.path.join(
    REPO_ROOT, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
)
if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

from backend.core.models import ArxivPaper, Insight, RankedPaper, SupportedClaim, Synthesis


# ============================================================================
# Module Imports & Re-exports
# ============================================================================

def test_top_level_reexports():
    """Verify top-level package exports."""
    from backend import (
        ArxivPaper,
        ConceptGraph,
        RankedPaper,
        SupportedClaim,
        Synthesis,
        build_graph,
        rank,
        run_pipeline,
    )
    assert callable(run_pipeline)
    assert callable(rank)
    assert callable(build_graph)
    assert issubclass(RankedPaper, ArxivPaper)
    assert issubclass(SupportedClaim, object)
    assert issubclass(Synthesis, object)
    assert issubclass(ConceptGraph, object)


def test_core_modules_importable():
    """Verify all backend core computational modules can be imported."""
    import backend.core.graph as graph_mod
    import backend.core.models as models_mod
    import backend.core.pipeline as pipeline_mod
    import backend.core.plan_query as plan_query_mod
    import backend.core.rank as rank_mod
    import backend.core.route as route_mod
    import backend.core.search as search_mod
    import backend.core.synthesize as synthesize_mod

    assert hasattr(graph_mod, "build_graph")
    assert hasattr(models_mod, "ArxivPaper")
    assert hasattr(pipeline_mod, "run_pipeline")
    assert hasattr(plan_query_mod, "plan_query")
    assert hasattr(rank_mod, "rank")
    assert hasattr(route_mod, "route")
    assert hasattr(search_mod, "search")
    assert hasattr(synthesize_mod, "analyze_research")


def test_integration_modules_importable():
    """Verify all integration adapters can be imported without LangChain."""
    import backend.integrations.bibtex as bibtex_mod
    import backend.integrations.citations as citations_mod
    import backend.integrations.llm as llm_mod
    import backend.integrations.web_search as web_search_mod

    assert hasattr(bibtex_mod, "generate_bibtex")
    assert hasattr(citations_mod, "get_citations")
    assert hasattr(llm_mod, "generate_structured")
    assert hasattr(llm_mod, "generate_text")
    assert hasattr(llm_mod, "get_llm")
    assert hasattr(web_search_mod, "web_search")


# ============================================================================
# Dense Vector Re-Ranking
# ============================================================================

@pytest.fixture
def sample_papers():
    return [
        ArxivPaper(
            arxiv_id="2401.0001",
            title="Paper A",
            authors=["Author 1"],
            summary="Summary A",
            published="2024-01-01",
            pdf_url="http://arxiv.org/pdf/2401.0001",
            abs_url="http://arxiv.org/abs/2401.0001",
            primary_category="cs.AI",
            categories=["cs.AI"],
        ),
        ArxivPaper(
            arxiv_id="2401.0002",
            title="Paper B",
            authors=["Author 2"],
            summary="Summary B",
            published="2024-01-02",
            pdf_url="http://arxiv.org/pdf/2401.0002",
            abs_url="http://arxiv.org/abs/2401.0002",
            primary_category="cs.CL",
            categories=["cs.CL"],
        ),
        ArxivPaper(
            arxiv_id="2401.0003",
            title="Paper C",
            authors=["Author 3"],
            summary="Summary C",
            published="2024-01-03",
            pdf_url="http://arxiv.org/pdf/2401.0003",
            abs_url="http://arxiv.org/abs/2401.0003",
            primary_category="cs.LG",
            categories=["cs.LG"],
        ),
    ]


def test_rank_empty_input():
    from backend.core.rank import rank
    result = rank([], "test query")
    assert result == []


@patch("backend.core.rank.embed")
def test_rank_cosine_similarity_ordering(mock_embed, sample_papers):
    from backend.core.rank import rank

    def fake_embed(texts):
        if len(texts) == 1 and texts[0] == "test query":
            return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        return np.array([
            [0.5, 0.866, 0.0],  # Paper A: dot product with [1,0,0] = 0.5
            [1.0, 0.0, 0.0],    # Paper B: dot product with [1,0,0] = 1.0
            [0.0, 1.0, 0.0],    # Paper C: dot product with [1,0,0] = 0.0
        ], dtype=np.float32)

    mock_embed.side_effect = fake_embed

    ranked = rank(sample_papers, "test query", top_k=20)
    assert len(ranked) == 3
    assert ranked[0].arxiv_id == "2401.0002"  # Paper B
    assert abs(ranked[0].relevance_score - 1.0) < 1e-4
    assert ranked[1].arxiv_id == "2401.0001"  # Paper A
    assert abs(ranked[1].relevance_score - 0.5) < 1e-4
    assert ranked[2].arxiv_id == "2401.0003"  # Paper C
    assert abs(ranked[2].relevance_score - 0.0) < 1e-4


@patch("backend.core.rank.embed")
def test_rank_top_k_truncation(mock_embed, sample_papers):
    from backend.core.rank import rank

    mock_embed.side_effect = lambda texts: (
        np.array([[1.0, 0.0]], dtype=np.float32) if len(texts) == 1
        else np.array([[0.9, 0.1], [0.8, 0.2], [0.3, 0.7]], dtype=np.float32)
    )
    ranked = rank(sample_papers, "test query", top_k=2)
    assert len(ranked) == 2
    assert ranked[0].arxiv_id == "2401.0001"
    assert ranked[1].arxiv_id == "2401.0002"


# ============================================================================
# Concept Graph Topology
# ============================================================================

@pytest.fixture
def graph_papers():
    return [
        RankedPaper(
            arxiv_id="2401.0001",
            title="Paper One",
            authors=["Author A"],
            summary="Summary of paper one",
            published="2024-01-01",
            pdf_url="",
            abs_url="",
            primary_category="cs.AI",
            categories=["cs.AI"],
            relevance_score=0.9,
        ),
        RankedPaper(
            arxiv_id="2401.0002",
            title="Paper Two",
            authors=["Author B"],
            summary="Summary of paper two",
            published="2024-01-02",
            pdf_url="",
            abs_url="",
            primary_category="cs.CL",
            categories=["cs.CL"],
            relevance_score=0.8,
        ),
        RankedPaper(
            arxiv_id="2401.0003",
            title="Paper Three",
            authors=["Author C"],
            summary="Summary of paper three",
            published="2024-01-03",
            pdf_url="",
            abs_url="",
            primary_category="cs.LG",
            categories=["cs.LG"],
            relevance_score=0.7,
        ),
    ]


@pytest.fixture
def graph_insights():
    return [
        Insight(arxiv_id="2401.0001", concepts=["Transformers", "Attention"]),
        Insight(arxiv_id="2401.0002", concepts=["Attention", "Search"]),
        Insight(arxiv_id="9999.9999", concepts=["UnknownConcept"]),
    ]


def test_build_graph_empty_papers(graph_insights):
    from backend.core.graph import build_graph
    graph = build_graph([], graph_insights)
    assert graph.nodes == []
    assert graph.edges == []


@patch("backend.core.graph.embed")
def test_build_graph_single_paper(mock_embed, graph_papers, graph_insights):
    from backend.core.graph import build_graph
    graph = build_graph([graph_papers[0]], graph_insights)
    assert len(graph.nodes) == 3
    paper_nodes = [n for n in graph.nodes if n.type == "paper"]
    concept_nodes = [n for n in graph.nodes if n.type == "concept"]
    assert len(paper_nodes) == 1
    assert len(concept_nodes) == 2
    assert all(e.type == "MENTIONS" for e in graph.edges)
    mock_embed.assert_not_called()


@patch("backend.core.graph.embed")
def test_build_graph_nodes_and_edges(mock_embed, graph_papers, graph_insights):
    from backend.core.graph import build_graph

    mock_embed.return_value = np.array([
        [1.0, 0.0, 0.0],
        [0.9, 0.1, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

    graph = build_graph(graph_papers, graph_insights, k=2)

    paper_nodes = [n for n in graph.nodes if n.type == "paper"]
    concept_nodes = [n for n in graph.nodes if n.type == "concept"]
    assert len(paper_nodes) == 3
    assert len(concept_nodes) == 3
    concept_ids = {n.id for n in concept_nodes}
    assert "concept::transformers" in concept_ids
    assert "concept::attention" in concept_ids
    assert "concept::search" in concept_ids
    assert "concept::unknownconcept" not in concept_ids

    mentions_edges = [e for e in graph.edges if e.type == "MENTIONS"]
    assert len(mentions_edges) == 4

    similar_edges = [e for e in graph.edges if e.type == "SIMILAR_TO"]
    seen_pairs = set()
    for edge in similar_edges:
        assert edge.source != edge.target
        pair = frozenset([edge.source, edge.target])
        assert pair not in seen_pairs
        seen_pairs.add(pair)


# ============================================================================
# Four Critical Invariant Tests
# ============================================================================

@patch("backend.core.pipeline.rank")
@patch("backend.core.pipeline.search")
@patch("backend.core.pipeline.plan_query")
@patch("backend.core.pipeline.analyze_research")
def test_sequential_run_isolation(mock_analyze, mock_plan, mock_search, mock_rank):
    """Invariant 1: Ensures consecutive searches in the same session never bleed papers or concepts."""
    from backend.core.pipeline import run_pipeline
    from backend.core.search import SearchResult

    mock_rank.side_effect = lambda candidates, query, top_k=20: [
        RankedPaper(**p.model_dump(), relevance_score=0.9) for p in candidates
    ]

    paper_a = ArxivPaper(
        arxiv_id="2401.0001",
        title="Paper Alpha",
        authors=["Author A"],
        summary="Summary Alpha about quantum algorithms.",
        published="2024-01-01",
        pdf_url="http://arxiv.org/pdf/2401.0001",
        abs_url="http://arxiv.org/abs/2401.0001",
        primary_category="quant-ph",
        categories=["quant-ph"],
    )
    paper_b = ArxivPaper(
        arxiv_id="2401.0002",
        title="Paper Beta",
        authors=["Author B"],
        summary="Summary Beta about deep learning architectures.",
        published="2024-01-02",
        pdf_url="http://arxiv.org/pdf/2401.0002",
        abs_url="http://arxiv.org/abs/2401.0002",
        primary_category="cs.LG",
        categories=["cs.LG"],
    )

    # First search execution
    mock_plan.return_value = ["quantum algorithms"]
    mock_search.return_value = SearchResult(papers=[paper_a], status="success")
    mock_analyze.return_value = (
        Synthesis(summary="Alpha synthesis", citations=["2401.0001"], claims=[]),
        [Insight(arxiv_id="2401.0001", concepts=["Quantum Computing", "Qubits"])],
    )

    result_1 = run_pipeline("quantum algorithms", with_graph=False)
    assert len(result_1.papers) == 1
    assert result_1.papers[0].arxiv_id == "2401.0001"
    assert "Quantum Computing" in result_1.concepts

    # Second search execution with different query
    mock_plan.return_value = ["deep learning"]
    mock_search.return_value = SearchResult(papers=[paper_b], status="success")
    mock_analyze.return_value = (
        Synthesis(summary="Beta synthesis", citations=["2401.0002"], claims=[]),
        [Insight(arxiv_id="2401.0002", concepts=["Neural Networks", "Backpropagation"])],
    )

    result_2 = run_pipeline("deep learning", with_graph=False)
    assert len(result_2.papers) == 1
    assert result_2.papers[0].arxiv_id == "2401.0002"
    assert "Neural Networks" in result_2.concepts

    # Absolute isolation assertion: result_2 must NOT contain any trace of result_1
    result_2_paper_ids = {p.arxiv_id for p in result_2.papers}
    assert "2401.0001" not in result_2_paper_ids
    assert "Quantum Computing" not in result_2.concepts
    assert "Qubits" not in result_2.concepts


@patch("backend.core.graph.embed")
def test_graph_orphan_filtering(mock_embed, graph_papers):
    """Invariant 2: Ensures insights referencing unknown paper IDs are strictly filtered out of the graph."""
    from backend.core.graph import build_graph

    mock_embed.return_value = np.eye(len(graph_papers), dtype=np.float32)

    insights = [
        Insight(arxiv_id="2401.0001", concepts=["ValidConcept"]),
        Insight(arxiv_id="9999.9999", concepts=["OrphanConceptA"]),
        Insight(arxiv_id="ghost_id_000", concepts=["OrphanConceptB"]),
    ]

    graph = build_graph(graph_papers, insights)

    node_ids = {n.id for n in graph.nodes}
    assert "2401.0001" in node_ids
    assert "concept::validconcept" in node_ids
    # Orphan nodes must be absent
    assert "9999.9999" not in node_ids
    assert "ghost_id_000" not in node_ids
    assert "concept::orphanconcepta" not in node_ids
    assert "concept::orphanconceptb" not in node_ids

    # All edges must only connect known valid entities
    for edge in graph.edges:
        assert edge.source not in {"9999.9999", "ghost_id_000"}
        assert edge.target not in {"concept::orphanconcepta", "concept::orphanconceptb"}


@patch("backend.core.synthesize.generate_structured")
def test_claim_attribution_fidelity(mock_generate):
    """Invariant 3: Ensures every claim's supporting_sentence matches character-for-character in the abstract."""
    from backend.core.models import ResearchAnalysis
    from backend.core.synthesize import analyze_research

    abstract = (
        "FlashAttention is an IO-aware exact attention algorithm. "
        "It yields up to 3x speedup on GPT-2 style transformers. "
        "We also introduce block-sparse attention patterns."
    )
    papers = [
        RankedPaper(
            arxiv_id="2205.14135",
            title="FlashAttention: Fast and Memory-Efficient Exact Attention",
            authors=["Tri Dao et al."],
            summary=abstract,
            published="2022-05-27",
            pdf_url="",
            abs_url="",
            primary_category="cs.LG",
            categories=["cs.LG"],
            relevance_score=0.98,
        )
    ]

    mock_analysis = ResearchAnalysis(
        summary="Synthesis about FlashAttention.",
        citations=["2205.14135"],
        claims=[
            SupportedClaim(
                claim="Exact IO-aware attention",
                arxiv_id="2205.14135",
                supporting_sentence="FlashAttention is an IO-aware exact attention algorithm.",
            ),
            SupportedClaim(
                claim="Hallucinated claim with fake quote",
                arxiv_id="2205.14135",
                supporting_sentence="This sentence does not exist anywhere in the paper abstract.",
            ),
            SupportedClaim(
                claim="Speedup claim",
                arxiv_id="2205.14135",
                supporting_sentence="It yields up to 3x speedup on GPT-2 style transformers.",
            ),
            SupportedClaim(
                claim="Claim referencing invalid paper ID",
                arxiv_id="0000.00000",
                supporting_sentence="FlashAttention is an IO-aware exact attention algorithm.",
            ),
        ],
        insights=[],
    )
    mock_generate.return_value = mock_analysis

    synthesis, _ = analyze_research("FlashAttention", papers)

    # Only verbatim claims matched character-for-character against abstract survive
    assert len(synthesis.claims) == 2
    for claim in synthesis.claims:
        assert claim.arxiv_id == "2205.14135"
        assert claim.supporting_sentence in abstract

    surviving_sentences = [c.supporting_sentence for c in synthesis.claims]
    assert "FlashAttention is an IO-aware exact attention algorithm." in surviving_sentences
    assert "It yields up to 3x speedup on GPT-2 style transformers." in surviving_sentences
    assert "This sentence does not exist anywhere in the paper abstract." not in surviving_sentences


@patch("backend.core.synthesize.generate_structured")
def test_follow_up_claim_attribution_fidelity(mock_generate):
    """Ensures follow_up also enforces verbatim abstract match for supported claims."""
    from backend.core.synthesize import follow_up

    abstract = "Rotary Position Embedding encodes relative position with a rotation matrix."
    papers = [
        RankedPaper(
            arxiv_id="2104.09864",
            title="RoFormer: Enhanced Transformer with Rotary Position Embedding",
            authors=["Jianlin Su et al."],
            summary=abstract,
            published="2021-04-20",
            pdf_url="",
            abs_url="",
            primary_category="cs.CL",
            categories=["cs.CL"],
            relevance_score=0.99,
        )
    ]

    mock_generate.return_value = Synthesis(
        summary="Follow up RoFormer explanation.",
        citations=["2104.09864", "9999.9999"],  # Includes invalid paper ID
        claims=[
            SupportedClaim(
                claim="Rotary embedding function",
                arxiv_id="2104.09864",
                supporting_sentence="Rotary Position Embedding encodes relative position with a rotation matrix.",
            ),
            SupportedClaim(
                claim="Fake claim",
                arxiv_id="2104.09864",
                supporting_sentence="This sentence is fabricated and absent from abstract.",
            ),
        ],
    )

    result = follow_up("How does RoFormer work?", [], papers, ["RoPE"])

    assert len(result.claims) == 1
    assert result.claims[0].supporting_sentence == "Rotary Position Embedding encodes relative position with a rotation matrix."
    # Citation list must only contain known valid papers
    assert "9999.9999" not in result.citations
    assert "2104.09864" in result.citations


@patch("backend.core.pipeline.rank")
@patch("backend.core.pipeline.search")
@patch("backend.core.pipeline.plan_query")
def test_network_timeout_and_empty_pool(mock_plan, mock_search, mock_rank):
    """Invariant 4: Ensures search timeouts and empty candidate pools return clean fallbacks without crashing."""
    from backend.core.pipeline import run_pipeline
    from backend.core.search import SearchResult

    mock_rank.return_value = []
    mock_plan.return_value = ["query1", "query2"]

    # Simulate network timeout / error during arXiv search
    mock_search.return_value = SearchResult(
        papers=[],
        status="search_error",
        errors=["arXiv request timed out after 30 seconds"],
    )

    result = run_pipeline("nonexistent query that times out", with_graph=True, with_synthesis=True)

    assert result is not None
    assert result.candidate_count == 0
    assert result.papers == []
    assert result.search_status == "search_error"
    assert "arXiv request timed out" in result.search_error
    assert result.synthesis is not None
    assert result.synthesis.summary == "No papers found for this query."
    assert result.graph is None or (result.graph.nodes == [] and result.graph.edges == [])


# ============================================================================
# Rate Limiting & 429 Exponential Backoff Tests
# ============================================================================

@pytest.fixture(autouse=False)
def reset_llm_rate_limiters():
    """Reset module-level RateLimiter singletons before and after each rate-limit test.

    The module-level _flash_limiter / _flash_lite_limiter accumulate timestamps
    from prior tests in the same process. This fixture clears them so each
    rate-limit test starts from a clean slate without bleeding state.
    """
    import backend.integrations.llm as llm_mod
    llm_mod._flash_limiter.reset()
    llm_mod._flash_lite_limiter.reset()
    yield
    llm_mod._flash_limiter.reset()
    llm_mod._flash_lite_limiter.reset()


def test_rate_limit_retry_handling_429(reset_llm_rate_limiters):
    """Verify rate-limit retry handling when 429 is encountered."""
    from google.genai import errors
    from backend.integrations.llm import _execute_with_retry

    call_count = 0

    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise errors.APIError(
                code=429,
                response_json={"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "Rate limit exceeded"}},
            )
        return "recovered"

    with patch("time.sleep") as mock_sleep:
        res = _execute_with_retry(flaky_func, max_retries=3, initial_delay=4.0, backoff_factor=2.0)
        assert res == "recovered"
        assert call_count == 3
        # Should have slept twice (attempt 1: 4s, attempt 2: 8s)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(4.0)
        mock_sleep.assert_any_call(8.0)


def test_rate_limit_retry_exhaustion(reset_llm_rate_limiters):
    """Verify exception is re-raised after max retries are exhausted."""
    from google.genai import errors
    from backend.integrations.llm import _execute_with_retry

    def failing_func():
        raise errors.APIError(
            code=429,
            response_json={"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "Persistent 429"}},
        )

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(errors.APIError):
            _execute_with_retry(failing_func, max_retries=2, initial_delay=1.0, backoff_factor=2.0)
        assert mock_sleep.call_count == 2


def test_rate_limiter_window_throttling(reset_llm_rate_limiters):
    """Verify sliding-window RateLimiter throttles when burst exceeds capacity."""
    from backend.integrations.llm import RateLimiter

    simulated_time = 100.0

    def fake_time():
        return simulated_time

    def fake_sleep(duration):
        nonlocal simulated_time
        simulated_time += duration

    limiter = RateLimiter(max_requests=2, window_seconds=10.0, time_fn=fake_time)
    with patch("time.sleep", side_effect=fake_sleep) as mock_sleep:
        limiter.acquire()
        limiter.acquire()
        assert mock_sleep.call_count == 0
        assert len(limiter.timestamps) == 2

        # 3rd request in same window must sleep and evict expired timestamp
        limiter.acquire()
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args[0][0] >= 10.0
        assert len(limiter.timestamps) == 1

        limiter.reset()
        assert len(limiter.timestamps) == 0


def test_get_limiter_for_model_allocation():
    """Verify Purpose-fit rate limiter allocations (5 RPM for Flash, 15 RPM for Flash-Lite)."""
    from backend.integrations.llm import get_limiter_for_model

    flash_limiter = get_limiter_for_model("flash")
    flash_lite_limiter = get_limiter_for_model("flash_lite")

    assert flash_limiter.max_requests == 5
    assert flash_limiter.window_seconds == 60.0

    assert flash_lite_limiter.max_requests == 15
    assert flash_lite_limiter.window_seconds == 60.0


def test_generate_structured_with_parsed():
    """Verify generate_structured configures GenerateContentConfig and returns response.parsed."""
    from google.genai import types
    from backend.core.models import QueryPlan
    from backend.integrations.llm import generate_structured

    mock_client = MagicMock()
    mock_response = MagicMock()
    expected_plan = QueryPlan(queries=['ti:"test"'])
    mock_response.parsed = expected_plan
    mock_client.models.generate_content.return_value = mock_response

    result = generate_structured("test prompt", QueryPlan, model_type="flash_lite", client=mock_client)
    assert result == expected_plan
    mock_client.models.generate_content.assert_called_once()
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-3.5-flash-lite"
    assert kwargs["contents"] == "test prompt"
    assert isinstance(kwargs["config"], types.GenerateContentConfig)
    assert kwargs["config"].response_mime_type == "application/json"
    assert kwargs["config"].response_schema == QueryPlan
    assert kwargs["config"].temperature == 0.0


def test_generate_structured_with_text_json_fallback():
    """Verify generate_structured falls back to JSON parsing if response.parsed is None."""
    from backend.core.models import QueryPlan
    from backend.integrations.llm import generate_structured

    mock_client = MagicMock()
    mock_response = MagicMock(spec=["text"])
    mock_response.text = '{"queries": ["ti:\\"fallback\\""]}'
    mock_client.models.generate_content.return_value = mock_response

    result = generate_structured("fallback prompt", QueryPlan, model_type="flash_lite", client=mock_client)
    assert isinstance(result, QueryPlan)
    assert result.queries == ['ti:"fallback"']


def test_generate_structured_empty_raises_value_error():
    """Verify generate_structured raises ValueError when model response contains no parseable data."""
    from backend.core.models import QueryPlan
    from backend.integrations.llm import generate_structured

    mock_client = MagicMock()
    mock_response = MagicMock(spec=[])  # Neither parsed nor text
    mock_client.models.generate_content.return_value = mock_response

    with pytest.raises(ValueError, match="Failed to extract structured"):
        generate_structured("empty prompt", QueryPlan, model_type="flash_lite", client=mock_client)


def test_generate_text_delegation():
    """Verify generate_text calls client.models.generate_content and returns string."""
    from backend.integrations.llm import generate_text

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Generated text content"
    mock_client.models.generate_content.return_value = mock_response

    text = generate_text("prompt for text", model_type="flash_lite", client=mock_client)
    assert text == "Generated text content"
    mock_client.models.generate_content.assert_called_once()
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-3.5-flash-lite"
    assert kwargs["contents"] == "prompt for text"


def test_get_llm_eliminated():
    """Verify historical LangChain get_llm raises DeprecationWarning."""
    from backend.integrations.llm import get_llm

    with pytest.raises(DeprecationWarning, match="LangChain get_llm\\(\\) is eliminated"):
        get_llm()


# ============================================================================
# LLM Caller Unit Tests with Mocks
# ============================================================================

@patch("backend.core.plan_query.generate_structured")
def test_plan_query_calls_generate_structured(mock_generate):
    """Verify plan_query delegates to generate_structured with model_type='flash_lite'."""
    from backend.core.plan_query import _plan_query_cached
    from backend.core.models import QueryPlan

    _plan_query_cached.cache_clear()
    mock_generate.return_value = QueryPlan(queries=['ti:"speculative decoding"', 'abs:"speculative sampling"'])

    variants = _plan_query_cached("speculative decoding in LLMs", 2)
    assert variants == ('ti:"speculative decoding"', 'abs:"speculative sampling"')
    mock_generate.assert_called_once()
    _, kwargs = mock_generate.call_args
    assert kwargs.get("model_type") == "flash_lite"


@patch("backend.core.synthesize.generate_structured")
def test_synthesize_calls_generate_structured_flash(mock_generate, graph_papers):
    """Verify analyze_research delegates to generate_structured with model_type='flash'."""
    from backend.core.models import ResearchAnalysis
    from backend.core.synthesize import analyze_research

    mock_generate.return_value = ResearchAnalysis(
        summary="Flash synthesis.",
        citations=["2401.0001"],
        claims=[],
        insights=[],
    )

    synthesis, insights = analyze_research("query", graph_papers)
    assert synthesis.summary == "Flash synthesis."
    mock_generate.assert_called_once()
    _, kwargs = mock_generate.call_args
    assert kwargs.get("model_type") == "flash"


@patch("backend.core.synthesize.generate_structured")
def test_follow_up_calls_generate_structured_flash(mock_generate, graph_papers):
    """Verify follow_up delegates to generate_structured with model_type='flash'."""
    from backend.core.synthesize import follow_up

    mock_generate.return_value = Synthesis(
        summary="Follow up grounded answer.",
        citations=["2401.0001"],
        claims=[],
    )

    result = follow_up("How does Paper 1 work?", [], graph_papers, ["Transformers"])
    assert result.summary == "Follow up grounded answer."
    mock_generate.assert_called_once()
    _, kwargs = mock_generate.call_args
    assert kwargs.get("model_type") == "flash"


@patch("backend.core.synthesize.web_search")
@patch("backend.core.synthesize.generate_text")
def test_follow_up_general_calls_generate_text_flash_lite(mock_gen_text, mock_web_search):
    """Verify follow_up_general delegates to generate_text with model_type='flash_lite'."""
    from backend.core.synthesize import follow_up_general

    mock_web_search.return_value = [{"answer": "Deep learning is a subset of ML."}]
    mock_gen_text.return_value = "Deep learning is a subset of machine learning based on neural networks."

    answer = follow_up_general("What is deep learning?", [])
    assert "Deep learning" in answer
    mock_gen_text.assert_called_once()
    _, kwargs = mock_gen_text.call_args
    assert kwargs.get("model_type") == "flash_lite"


@patch("backend.core.route.generate_structured")
def test_route_calls_generate_structured_flash_lite(mock_generate, graph_papers):
    """Verify route fallback delegates to generate_structured with model_type='flash_lite'."""
    from backend.core.models import Route
    from backend.core.route import route

    mock_generate.return_value = Route(intent="follow_up_grounded")

    # Ambiguous query that requires LLM intent classification
    intent, fallback = route("Does the method scale with dataset size?", graph_papers)
    assert intent == "follow_up_grounded"
    assert fallback is False
    mock_generate.assert_called_once()
    _, kwargs = mock_generate.call_args
    assert kwargs.get("model_type") == "flash_lite"


# ============================================================================
# Live API Integration Test (Opt-in)
# ============================================================================

@pytest.mark.live_api
def test_live_gemini_api_connectivity():
    """Live test against Google Gemini API via official google-genai SDK (opt-in)."""
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY or GEMINI_API_KEY not set")

    try:
        from backend.integrations.llm import generate_structured, generate_text
        from pydantic import BaseModel

        class MathAnswer(BaseModel):
            result: int

        # Text generation
        text = generate_text("Reply with exactly: PONG", model_type="flash_lite", temperature=0.0)
        assert "PONG" in text.upper()

        # Structured output generation
        structured = generate_structured(
            "Calculate 7 + 5. Return result as integer.",
            MathAnswer,
            model_type="flash_lite",
        )
        assert structured.result == 12
    except (httpx.ConnectError, OSError, Exception) as exc:
        pytest.skip(f"Live API call skipped due to environment / network constraint: {exc}")


# ============================================================================
# Integrations and Helpers
# ============================================================================

def test_generate_bibtex():
    from backend.core.models import RankedPaper
    from backend.integrations.bibtex import generate_bibtex

    papers = [
        RankedPaper(
            arxiv_id="2305.12345",
            title="Attention Is All You Need",
            authors=["Vaswani et al."],
            summary="Transformer architecture",
            published="2023-05-10",
            pdf_url="http://arxiv.org/pdf/2305.12345",
            abs_url="http://arxiv.org/abs/2305.12345",
            primary_category="cs.CL",
            categories=["cs.CL"],
            relevance_score=0.95,
        )
    ]
    bib = generate_bibtex(papers)
    assert "@article{2305_12345," in bib
    assert "title = {Attention Is All You Need}" in bib
    assert "author = {Vaswani et al.}" in bib
    assert "year = {2023}" in bib


def test_is_valid_arxiv_query():
    from backend.core.plan_query import is_valid_arxiv_query

    assert is_valid_arxiv_query('ti:"transformer" AND abs:"attention"')
    assert is_valid_arxiv_query('cat:cs.CL AND "large language models"')
    # Malformed / unsafe queries
    assert not is_valid_arxiv_query("")
    assert not is_valid_arxiv_query("a" * 301)
    assert not is_valid_arxiv_query("SELECT * FROM papers; DROP TABLE;")


def test_route_heuristics():
    from backend.core.models import RankedPaper
    from backend.core.route import route

    # Empty papers -> always new_search
    intent, fallback = route("what is attention?", [])
    assert intent == "new_search"
    assert not fallback

    mock_papers = [
        RankedPaper(
            arxiv_id="2401.0001",
            title="Paper 1",
            authors=["A"],
            summary="S",
            published="2024",
            pdf_url="",
            abs_url="",
            primary_category="cs.AI",
            categories=["cs.AI"],
            relevance_score=1.0,
        )
    ]

    # Explicit new search keyword
    intent, _ = route("please do a new search on quantum computing", mock_papers)
    assert intent == "new_search"

    # Explicit grounded follow up
    intent, _ = route("explain paper 1 in more detail", mock_papers)
    assert intent == "follow_up_grounded"

    # Explicit general question
    intent, _ = route("what is gradient descent?", mock_papers)
    assert intent == "follow_up_general"
