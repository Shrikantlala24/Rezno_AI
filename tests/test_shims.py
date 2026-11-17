"""Tests for Version_1 backward-compatibility shims."""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

venv_site_packages = os.path.join(
    REPO_ROOT, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
)
if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)


def test_pipeline_shim():
    import Version_1.pipeline as v1_pipe
    import backend.core.pipeline as backend_pipe

    assert hasattr(v1_pipe, "run_pipeline")
    assert hasattr(v1_pipe, "PipelineResult")
    assert v1_pipe.run_pipeline is backend_pipe.run_pipeline
    assert v1_pipe.PipelineResult is backend_pipe.PipelineResult


def test_rank_shim():
    import Version_1.rank as v1_rank
    import backend.core.rank as backend_rank

    assert hasattr(v1_rank, "rank")
    assert hasattr(v1_rank, "embed")
    assert v1_rank.rank is backend_rank.rank
    assert v1_rank.embed is backend_rank.embed


def test_models_shim():
    import Version_1.models as v1_models
    import backend.core.models as backend_models

    assert hasattr(v1_models, "ArxivPaper")
    assert hasattr(v1_models, "RankedPaper")
    assert hasattr(v1_models, "Synthesis")
    assert hasattr(v1_models, "SupportedClaim")
    assert hasattr(v1_models, "ConceptGraph")
    assert v1_models.ArxivPaper is backend_models.ArxivPaper
    assert v1_models.RankedPaper is backend_models.RankedPaper
    assert v1_models.SupportedClaim is backend_models.SupportedClaim


def test_search_shim():
    import Version_1.search as v1_search
    import backend.core.search as backend_search

    assert hasattr(v1_search, "search")
    assert v1_search.search is backend_search.search


def test_graph_shim():
    import Version_1.graph as v1_graph
    import backend.core.graph as backend_graph

    assert hasattr(v1_graph, "build_graph")
    assert v1_graph.build_graph is backend_graph.build_graph


def test_synthesize_shim():
    import Version_1.synthesize as v1_synth
    import backend.core.synthesize as backend_synth

    assert hasattr(v1_synth, "analyze_research")
    assert v1_synth.analyze_research is backend_synth.analyze_research


def test_route_shim():
    import Version_1.route as v1_route
    import backend.core.route as backend_route

    assert hasattr(v1_route, "route")
    assert v1_route.route is backend_route.route


def test_plan_query_shim():
    import Version_1.plan_query as v1_pq
    import backend.core.plan_query as backend_pq

    assert hasattr(v1_pq, "plan_query")
    assert hasattr(v1_pq, "is_valid_arxiv_query")
    assert v1_pq.plan_query is backend_pq.plan_query


def test_run_shim():
    import Version_1.run as v1_run
    import backend.cli as backend_cli

    assert hasattr(v1_run, "main")
    assert v1_run.main is backend_cli.main

    import Version_1.main as v1_main
    assert hasattr(v1_main, "main")
    assert v1_main.main is backend_cli.main

    import Version_1.diagnostic_test as v1_diag
    import backend.evaluation.diagnostic_test as backend_diag
    assert hasattr(v1_diag, "TARGETS")
    assert v1_diag.TARGETS is backend_diag.TARGETS


def test_evaluate_and_cases_shims():
    import Version_1.evaluate as v1_eval
    import Version_1.eval_cases as v1_cases
    import backend.evaluation.evaluate as backend_eval
    import backend.evaluation.eval_cases as backend_cases

    assert hasattr(v1_eval, "run")
    assert v1_eval.run is backend_eval.run
    assert hasattr(v1_cases, "CASES")
    assert hasattr(v1_cases, "score_case")
    assert v1_cases.CASES is backend_cases.CASES
    assert v1_cases.score_case is backend_cases.score_case


def test_integrations_shims():
    import Version_1.citations as v1_cit
    import Version_1.bibtex as v1_bib
    import Version_1.llm as v1_llm
    import Version_1.web_search as v1_ws
    import backend.integrations.citations as b_cit
    import backend.integrations.bibtex as b_bib
    import backend.integrations.llm as b_llm
    import backend.integrations.web_search as b_ws

    assert v1_cit.get_citations is b_cit.get_citations
    assert v1_bib.generate_bibtex is b_bib.generate_bibtex
    assert hasattr(v1_llm, "generate_structured")
    assert hasattr(v1_llm, "generate_text")
    assert v1_llm.generate_structured is b_llm.generate_structured
    assert v1_llm.generate_text is b_llm.generate_text
    assert v1_llm.get_llm is b_llm.get_llm
    assert v1_ws.web_search is b_ws.web_search
