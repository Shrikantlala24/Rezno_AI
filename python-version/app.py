"""Streamlit chat over the research pipeline.

Three-zone layout:
  Zone 1 — Left sidebar: Pipeline Controls (per_query, top_k, num_queries,
            response_length) + Session Overview + Clear session.
  Zone 2 — Center column: Conversation only — user messages, assistant
            synthesis/answers, evidence expanders, and unsourced badges.
            No citation chaining or screening controls here.
  Zone 3 — Right panel: Paper Workspace — search-run selector, Papers tab
            (with screening controls + citation chaining per card),
            Concept graph tab, Compare searches tab.

Memory is session-scoped: everything lives in st.session_state, which
survives Streamlit's reruns for as long as the browser tab is open and
dies with it. No database, no accounts, no cross-session persistence.
"""

import time
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

from bibtex import generate_bibtex
from citations import get_citations
from models import ChatMessage, RankedPaper, SearchRun, Synthesis
from pipeline import run_pipeline
from route import route
from synthesize import follow_up, follow_up_general

PAPER_COLOR = "#4C6EF5"
CONCEPT_COLOR = "#F59F00"
SIMILAR_COLOR = "#ADB5BD"
MENTIONS_COLOR = "#DEE2E6"
MAX_SEARCH_RUNS = 10

st.set_page_config(page_title="Research Agent", layout="wide")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "messages": [],       # List[ChatMessage]
        "search_runs": [],    # List[SearchRun]
        "selected_run_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def get_selected_run() -> SearchRun | None:
    runs = st.session_state.search_runs
    if not runs:
        return None
    for r in runs:
        if r.id == st.session_state.selected_run_id:
            return r
    return runs[-1]


def run_concepts(run: SearchRun | None) -> list[str]:
    if not run:
        return []
    seen: dict[str, None] = {}
    for insight in run.insights:
        for c in insight.concepts:
            seen.setdefault(c, None)
    return list(seen)


# ---------------------------------------------------------------------------
# Zone 3 — Right panel renderers
# ---------------------------------------------------------------------------

def _render_paper_card(p: RankedPaper, run: SearchRun, i: int) -> None:
    """Full paper card: metadata + abstract + screening + citation chaining."""
    # Meta row
    st.markdown(
        f"`{p.arxiv_id}` · {p.primary_category} · {p.published[:10]} · "
        f"score **{p.relevance_score:.3f}**"
    )
    st.caption(", ".join(p.authors[:6]) + (" et al." if len(p.authors) > 6 else ""))
    st.write(p.summary)
    st.markdown(f"[abstract]({p.abs_url}) · [pdf]({p.pdf_url})")

    # --- Screening state -------------------------------------------------
    st.divider()
    st.markdown("**Screening**")
    btn_cols = st.columns([1, 1, 1, 2])
    with btn_cols[0]:
        if st.button("📌 Keep", key=f"keep_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "keep"
            st.rerun()
    with btn_cols[1]:
        if st.button("🤔 Maybe", key=f"maybe_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "maybe"
            st.rerun()
    with btn_cols[2]:
        if st.button("🚫 Skip", key=f"skip_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "skip"
            st.rerun()
    with btn_cols[3]:
        st.caption(f"Status: **{p.status.upper()}**")

    new_note = st.text_input(
        "Note:",
        value=p.note or "",
        key=f"note_{run.id}_{p.arxiv_id}_{i}",
        placeholder="Add screening thoughts…",
    )
    if new_note != (p.note or ""):
        p.note = new_note

    # --- Citation chaining -----------------------------------------------
    st.divider()
    with st.expander("🔗 Citation Chaining (Semantic Scholar)", expanded=False):
        cit_key = f"cit_data_{p.arxiv_id}"
        if st.button("Fetch References & Citing Papers", key=f"fetch_cit_{run.id}_{p.arxiv_id}_{i}"):
            with st.spinner("Fetching from Semantic Scholar…"):
                st.session_state[cit_key] = get_citations(p.arxiv_id)

        cit_data = st.session_state.get(cit_key)
        if cit_data is not None:
            refs = cit_data.get("references", [])
            cits = cit_data.get("citations", [])

            if not refs and not cits:
                st.caption("No citation data available for this paper.")
            else:
                st.markdown(f"**References ({len(refs)})**")
                for ref in refs[:8]:
                    r_col1, r_col2 = st.columns([4, 1])
                    with r_col1:
                        st.caption(f"• **{ref['title']}** ({ref['year']})")
                    with r_col2:
                        if ref.get("arxiv_id") and st.button(
                            "Add", key=f"add_ref_{run.id}_{p.arxiv_id}_{ref['arxiv_id']}"
                        ):
                            if not any(x.arxiv_id == ref["arxiv_id"] for x in run.papers):
                                run.papers.append(
                                    RankedPaper(
                                        arxiv_id=ref["arxiv_id"],
                                        title=ref["title"],
                                        authors=ref["authors"],
                                        summary="Retrieved via reference citation chaining.",
                                        published=ref["year"],
                                        pdf_url="",
                                        abs_url=f"https://arxiv.org/abs/{ref['arxiv_id']}",
                                        primary_category="cs.AI",
                                        categories=["cs.AI"],
                                        relevance_score=p.relevance_score * 0.9,
                                    )
                                )
                                st.rerun()

                st.markdown(f"**Citing Papers ({len(cits)})**")
                for cit in cits[:8]:
                    c_col1, c_col2 = st.columns([4, 1])
                    with c_col1:
                        st.caption(f"• **{cit['title']}** ({cit['year']})")
                    with c_col2:
                        if cit.get("arxiv_id") and st.button(
                            "Add", key=f"add_cit_{run.id}_{p.arxiv_id}_{cit['arxiv_id']}"
                        ):
                            if not any(x.arxiv_id == cit["arxiv_id"] for x in run.papers):
                                run.papers.append(
                                    RankedPaper(
                                        arxiv_id=cit["arxiv_id"],
                                        title=cit["title"],
                                        authors=cit["authors"],
                                        summary="Retrieved via forward citation chaining.",
                                        published=cit["year"],
                                        pdf_url="",
                                        abs_url=f"https://arxiv.org/abs/{cit['arxiv_id']}",
                                        primary_category="cs.AI",
                                        categories=["cs.AI"],
                                        relevance_score=p.relevance_score * 0.9,
                                    )
                                )
                                st.rerun()


def render_papers(run: SearchRun | None) -> None:
    if not run or not run.papers:
        st.caption("Ask a research question to load papers.")
        return

    hdr_col1, hdr_col2 = st.columns([3, 1])
    with hdr_col1:
        st.caption(f"Top {len(run.papers)} papers for: *{run.query}*")
    with hdr_col2:
        st.download_button(
            label="📥 BibTeX",
            data=generate_bibtex(run.papers),
            file_name=f"papers_{run.id}.bib",
            mime="text/x-bibtex",
            key=f"bibtex_{run.id}",
            use_container_width=True,
        )

    for i, p in enumerate(run.papers, 1):
        status_badge = f" `[{p.status.upper()}]`" if p.status != "unreviewed" else ""
        with st.expander(f"{i}. {p.title}{status_badge}", expanded=False):
            _render_paper_card(p, run, i)


def render_graph(run: SearchRun | None) -> None:
    if not run or not run.graph or not run.graph.nodes:
        st.caption("The concept graph appears after a search.")
        return

    graph = run.graph
    labels = {n.id: n.label for n in graph.nodes}
    nodes = [
        Node(
            id=n.id,
            label=n.label if n.type == "concept" else n.id,
            title=labels[n.id],
            size=22 if n.type == "paper" else 14,
            color=PAPER_COLOR if n.type == "paper" else CONCEPT_COLOR,
        )
        for n in graph.nodes
    ]
    edges = [
        Edge(
            source=e.source,
            target=e.target,
            color=SIMILAR_COLOR if e.type == "SIMILAR_TO" else MENTIONS_COLOR,
            label="" if e.type == "MENTIONS" else "similar",
        )
        for e in graph.edges
    ]
    st.caption(
        f"{sum(1 for n in graph.nodes if n.type == 'paper')} papers (blue) · "
        f"{sum(1 for n in graph.nodes if n.type == 'concept')} concepts (orange) · "
        f"{len(edges)} edges"
    )
    agraph(nodes=nodes, edges=edges, config=Config(height=650, width=900, directed=False))


def render_comparison() -> None:
    runs = st.session_state.search_runs
    if len(runs) < 2:
        st.caption("Perform at least 2 searches to enable result-set comparison.")
        return

    options = {r.id: f"{r.query[:35]}…" if len(r.query) > 35 else r.query for r in runs}
    c1, c2 = st.columns(2)
    with c1:
        run_a_id = st.selectbox("Run A", list(options.keys()), format_func=lambda x: options[x], index=0)
    with c2:
        run_b_id = st.selectbox(
            "Run B", list(options.keys()), format_func=lambda x: options[x], index=min(1, len(runs) - 1)
        )

    run_a = next(r for r in runs if r.id == run_a_id)
    run_b = next(r for r in runs if r.id == run_b_id)

    papers_a = {p.arxiv_id: p for p in run_a.papers}
    papers_b = {p.arxiv_id: p for p in run_b.papers}
    shared_ids = set(papers_a) & set(papers_b)
    only_a = set(papers_a) - set(papers_b)
    only_b = set(papers_b) - set(papers_a)

    concepts_a = set(run_concepts(run_a))
    concepts_b = set(run_concepts(run_b))
    shared_concepts = concepts_a & concepts_b

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Shared papers", len(shared_ids))
    m2.metric(f"Unique to A", len(only_a))
    m3.metric(f"Unique to B", len(only_b))

    if shared_ids:
        st.markdown("**Papers in both:**")
        for pid in shared_ids:
            st.caption(f"• `{pid}` — {papers_a[pid].title}")

    if shared_concepts:
        st.markdown(f"**Shared concepts ({len(shared_concepts)}):**")
        st.write(", ".join(f"`{c}`" for c in sorted(shared_concepts)))


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def handle_new_search(
    question: str, status, per_query: int, top_k: int, num_queries: int, response_length: str
) -> tuple[Synthesis, SearchRun]:
    result = run_pipeline(
        question,
        top_k=top_k,
        per_query=per_query,
        num_queries=num_queries,
        response_length=response_length,
        on_progress=lambda m: status.write(m),
    )

    run_id = f"run_{int(time.time() * 1000)}"
    search_run = SearchRun(
        id=run_id,
        query=question,
        queries=result.queries,
        candidate_count=result.candidate_count,
        papers=result.papers,
        insights=result.insights,
        graph=result.graph,
        synthesis=result.synthesis,
        timestamp=time.strftime("%H:%M:%S"),
    )

    st.session_state.search_runs.append(search_run)
    if len(st.session_state.search_runs) > MAX_SEARCH_RUNS:
        st.session_state.search_runs.pop(0)
    st.session_state.selected_run_id = run_id

    synthesis = result.synthesis or Synthesis(summary="No results found.", citations=[], claims=[])
    return synthesis, search_run


def handle_follow_up_grounded(
    question: str, status, run: SearchRun | None, top_k: int, response_length: str
) -> Synthesis:
    status.write("Answering from papers already in context — no new search")
    papers = run.papers if run else []
    c_list = run_concepts(run)
    return follow_up(
        question,
        st.session_state.messages,
        papers,
        c_list,
        top_n=top_k,
        response_length=response_length,
    )


def handle_follow_up_general(question: str, status) -> str:
    status.write("Answering using live web search — not from retrieved papers")
    return follow_up_general(question, st.session_state.messages)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

init_state()

st.title("Research Agent")
st.caption("arXiv search, ranking, synthesis, and citation intelligence.")

# ----- Zone 1: Left sidebar -----------------------------------------------
with st.sidebar:
    st.subheader("Pipeline Controls")

    per_query_val = st.slider(
        "Papers per query variant", min_value=10, max_value=150, value=80, step=10,
        format="%d",
    )
    per_query = per_query_val
    st.caption(f"Current: **{per_query}** papers per variant")

    top_k_val = st.slider(
        "Ranking top-k", min_value=5, max_value=50, value=20, step=5,
        format="%d",
    )
    top_k = top_k_val
    st.caption(f"Current: **{top_k}** papers ranked")

    num_queries_val = st.slider(
        "Query variants", min_value=1, max_value=6, value=4, step=1,
        format="%d",
    )
    num_queries = num_queries_val
    st.caption(f"Current: **{num_queries}** query variants")

    st.divider()

    st.subheader("Response Length")
    length_options = ["Brief", "Standard", "Detailed"]
    # Use segmented_control if available (Streamlit ≥ 1.40), else radio
    try:
        response_length_label = st.segmented_control(
            "response_length_ctrl",
            options=length_options,
            default="Standard",
            label_visibility="collapsed",
        )
    except AttributeError:
        response_length_label = st.radio(
            "response_length_radio",
            options=length_options,
            index=1,
            horizontal=True,
            label_visibility="collapsed",
        )

    response_length = (response_length_label or "Standard").lower()
    st.caption(
        {
            "brief": "1-2 sentences, ≤2 claims",
            "standard": "3-5 sentences, moderate claims",
            "detailed": "5-8 sentences, full evidence set",
        }[response_length]
    )

    st.divider()
    st.subheader("Session Overview")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Search Runs", len(st.session_state.search_runs))

    active_run = get_selected_run()
    if active_run and active_run.synthesis and active_run.synthesis.citations:
        st.caption(f"Citations — *{active_run.query[:22]}…*")
        st.code("\n".join(active_run.synthesis.citations))

    if st.button("Clear session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.search_runs = []
        st.session_state.selected_run_id = None
        st.rerun()

# ----- Zones 2 + 3: Chat column + Paper workspace -------------------------
chat_col, panel_col = st.columns([1, 1], gap="large")

# Zone 2 — Conversation only
with chat_col:
    for message in st.session_state.messages:
        role = message.role if isinstance(message, ChatMessage) else message["role"]
        content = message.content if isinstance(message, ChatMessage) else message["content"]
        is_unsourced = getattr(message, "is_unsourced", False)
        is_fallback = getattr(message, "is_fallback", False)
        claims = getattr(message, "claims", [])
        msg_response_length = getattr(message, "response_length", "standard")

        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant":
                if is_unsourced:
                    fallback_note = " *(router fallback)*" if is_fallback else ""
                    st.caption(
                        f"ℹ️ *Answered using live web search — not from your retrieved papers*{fallback_note}"
                    )
                elif claims:
                    evidence_expanded = msg_response_length == "detailed"
                    with st.expander(
                        f"🔍 View Evidence & Supporting Quotes ({len(claims)})",
                        expanded=evidence_expanded,
                    ):
                        for claim in claims:
                            st.markdown(f"• **{claim.claim}** (`[{claim.arxiv_id}]`)")
                            st.caption(f'   > "{claim.supporting_sentence}"')

# Zone 3 — Paper workspace
with panel_col:
    if st.session_state.search_runs:
        run_options = {}
        for i, r in enumerate(st.session_state.search_runs):
            label = r.query[:38] + "…" if len(r.query) > 38 else r.query
            run_options[r.id] = f"#{i+1} ({r.timestamp}) {label}"

        if st.session_state.selected_run_id not in run_options:
            st.session_state.selected_run_id = st.session_state.search_runs[-1].id

        selected_id = st.selectbox(
            "Select Search Run",
            options=list(run_options.keys()),
            format_func=lambda x: run_options[x],
            index=list(run_options.keys()).index(st.session_state.selected_run_id),
        )
        st.session_state.selected_run_id = selected_id

    current_run = get_selected_run()

    papers_tab, graph_tab, compare_tab = st.tabs(["Papers", "Concept graph", "Compare searches"])
    with papers_tab:
        render_papers(current_run)
    with graph_tab:
        render_graph(current_run)
    with compare_tab:
        render_comparison()

# Chat input
if question := st.chat_input("Ask a research question…"):
    user_msg = ChatMessage(role="user", content=question)
    st.session_state.messages.append(user_msg)

    current_run = get_selected_run()
    context_papers = current_run.papers if current_run else []

    with chat_col:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.status("Thinking…", expanded=True) as status:
                intent, is_fallback = route(
                    question, context_papers, st.session_state.messages[:-1]
                )
                label_text = intent.replace("_", " ")
                if is_fallback:
                    label_text += " (fallback)"
                status.write(f"Routed as **{label_text}**")

                if intent == "new_search":
                    synthesis_obj, new_run = handle_new_search(
                        question, status, per_query, top_k, num_queries, response_length
                    )
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=synthesis_obj.summary,
                        intent="new_search",
                        search_run_id=new_run.id,
                        is_unsourced=False,
                        is_fallback=False,
                        claims=synthesis_obj.claims,
                        response_length=response_length,
                    )

                elif intent == "follow_up_grounded":
                    synthesis_obj = handle_follow_up_grounded(
                        question, status, current_run, top_k, response_length
                    )
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=synthesis_obj.summary,
                        intent="follow_up_grounded",
                        search_run_id=current_run.id if current_run else None,
                        is_unsourced=False,
                        is_fallback=False,
                        claims=synthesis_obj.claims,
                        response_length=response_length,
                    )

                else:  # follow_up_general
                    answer = handle_follow_up_general(question, status)
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=answer,
                        intent="follow_up_general",
                        search_run_id=None,
                        is_unsourced=True,
                        is_fallback=is_fallback,
                        claims=[],
                        response_length=response_length,
                    )

                status.update(label=label_text, state="complete", expanded=False)

            # Render the just-produced message inline (before rerun)
            st.markdown(assistant_msg.content)
            if assistant_msg.is_unsourced:
                fallback_note = " *(router fallback)*" if assistant_msg.is_fallback else ""
                st.caption(
                    f"ℹ️ *Answered using live web search — not from your retrieved papers*{fallback_note}"
                )
            elif assistant_msg.claims:
                evidence_expanded = response_length == "detailed"
                with st.expander(
                    f"🔍 View Evidence & Supporting Quotes ({len(assistant_msg.claims)})",
                    expanded=evidence_expanded,
                ):
                    for claim in assistant_msg.claims:
                        st.markdown(f"• **{claim.claim}** (`[{claim.arxiv_id}]`)")
                        st.caption(f'   > "{claim.supporting_sentence}"')

    st.session_state.messages.append(assistant_msg)
    st.rerun()
