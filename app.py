"""Streamlit chat over the research pipeline.

Memory is session-scoped: everything lives in st.session_state, which survives
Streamlit's reruns for as long as the browser tab is open and dies with it. No
database, no accounts, no cross-session persistence.
"""

import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

from pipeline import run_pipeline
from route import route
from synthesize import follow_up

PAPER_COLOR = "#4C6EF5"
CONCEPT_COLOR = "#F59F00"
SIMILAR_COLOR = "#ADB5BD"
MENTIONS_COLOR = "#DEE2E6"

st.set_page_config(page_title="Research Agent", layout="wide")


def init_state() -> None:
    defaults = {
        "messages": [],  # [{role, content}]
        "papers": [],
        "insights": [],
        "graph": None,
        "citations": [],
        "active_query": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def concepts() -> list[str]:
    seen: dict[str, None] = {}
    for insight in st.session_state.insights:
        for c in insight.concepts:
            seen.setdefault(c, None)
    return list(seen)


def render_papers() -> None:
    papers = st.session_state.papers
    if not papers:
        st.caption("Ask a research question to load papers.")
        return

    st.caption(f"Top {len(papers)} for: *{st.session_state.active_query}*")
    for i, p in enumerate(papers, 1):
        with st.expander(f"{i}. {p.title}", expanded=False):
            st.markdown(
                f"`{p.arxiv_id}` · {p.primary_category} · {p.published[:10]} · "
                f"score {p.relevance_score:.3f}"
            )
            st.caption(", ".join(p.authors[:6]) + (" et al." if len(p.authors) > 6 else ""))
            st.write(p.summary)
            st.markdown(f"[abstract]({p.abs_url}) · [pdf]({p.pdf_url})")


def render_graph() -> None:
    graph = st.session_state.graph
    if not graph or not graph.nodes:
        st.caption("The concept graph appears after a search.")
        return

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


def handle_new_search(question: str, status) -> str:
    result = run_pipeline(question, on_progress=lambda m: status.write(m))

    st.session_state.papers = result.papers
    st.session_state.insights = result.insights
    st.session_state.graph = result.graph
    st.session_state.active_query = question
    st.session_state.citations = (
        result.synthesis.citations if result.synthesis else []
    )

    if not result.papers:
        return "No papers matched that query. Try rephrasing it with different terminology."

    answer = result.synthesis.summary if result.synthesis else ""
    return (
        f"{answer}\n\n"
        f"*Searched {result.candidate_count} candidates across {len(result.queries)} "
        f"query variants; showing the top {len(result.papers)}.*"
    )


def handle_follow_up(question: str, status) -> str:
    status.write("Answering from papers already in context — no new search")
    return follow_up(
        question,
        st.session_state.messages[:-1],
        st.session_state.papers,
        concepts(),
    )


init_state()

st.title("Research Agent")
st.caption("arXiv search, ranking, and synthesis. Memory lasts as long as this tab.")

chat_col, panel_col = st.columns([1, 1], gap="large")

with chat_col:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with panel_col:
    papers_tab, graph_tab = st.tabs(["Papers", "Concept graph"])
    with papers_tab:
        render_papers()
    with graph_tab:
        render_graph()

if question := st.chat_input("Ask a research question…"):
    st.session_state.messages.append({"role": "user", "content": question})

    with chat_col:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.status("Thinking…", expanded=True) as status:
                intent = route(
                    question, st.session_state.papers, st.session_state.messages[:-1]
                )
                status.write(f"Routed as **{intent.replace('_', ' ')}**")
                if intent == "new_search":
                    answer = handle_new_search(question, status)
                else:
                    answer = handle_follow_up(question, status)
                status.update(label=intent.replace("_", " "), state="complete", expanded=False)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

with st.sidebar:
    st.subheader("Session")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Papers in context", len(st.session_state.papers))
    st.metric("Concepts", len(concepts()))
    if st.session_state.citations:
        st.caption("Citations from the last search")
        st.code("\n".join(st.session_state.citations))
    if st.button("Clear session", use_container_width=True):
        for key in ["messages", "papers", "insights", "graph", "citations", "active_query"]:
            st.session_state.pop(key, None)
        st.rerun()
