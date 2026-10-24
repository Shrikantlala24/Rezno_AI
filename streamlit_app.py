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

Styling: custom theme via .streamlit/config.toml (see that file) plus a
CSS injection block below for anything config.toml can't reach (fonts,
card treatment, chat bubbles). Graph rendering uses st_link_analysis
(Cytoscape.js) instead of streamlit-agraph for real interactivity.

Layout architecture (both rails use the SAME pattern, on purpose):

    +----------------------------+
    | fixed header(s)            |  <- flex: 0 0 auto, never moves
    +----------------------------+
    | single scrolling container |  <- flex: 1 1 auto, overflow-y: auto
    | (only this part scrolls)   |
    +----------------------------+
    | fixed footer (chat only)   |  <- flex: 0 0 auto, never moves
    +----------------------------+

The left (chat) rail already followed this. The right (workspace) rail
previously tried to fake it with `position: sticky` elements stacked at
hand-computed pixel offsets on top of one big scrolling column — that
breaks the instant any header wraps to a second line or a pixel of
padding shifts, because the offsets are guesses, not real layout. It has
been rebuilt to use the identical fixed-parent / single-scroller pattern:
the settings header, run-status strip, and tab bar are all `flex: 0 0
auto` parents that never move, and only the *active tab's own content*
lives in one scrollable child container per tab (papers_scroll /
graph_scroll / compare_scroll).
"""

import html
import time
import streamlit as st
import xml.etree.ElementTree as ET

try:
    from simpleicons.all import icons as simple_icons
except Exception:
    simple_icons = None

from st_link_analysis import EdgeStyle, Event, NodeStyle, st_link_analysis

from bibtex import generate_bibtex
from citations import get_citations
from models import ChatMessage, RankedPaper, SearchRun, Synthesis
from pipeline import run_pipeline
from route import route
from synthesize import follow_up, follow_up_general

from textwrap import dedent


def ra_html(body, **kwargs):
    """Render UI HTML directly, bypassing Markdown entirely.

    Streamlit's st.html renders HTML without routing it through the
    Markdown parser. This is important for layout primitives because
    indented HTML can otherwise be interpreted as a fenced/preformatted
    block by Markdown.
    """
    kwargs.pop("unsafe_allow_html", None)
    if isinstance(body, str):
        body = dedent(body).strip()
    return st.html(body)


# ---------------------------------------------------------------------------
# Simple Icons
# ---------------------------------------------------------------------------
# Simple Icons is a brand/source icon library. We use it for real source
# identities such as arXiv; generic UI actions remain typographic so we do not
# force unrelated brand marks into interface controls.
#
# Documented Python API:
#   from simpleicons.all import icons
#   icon = icons.get("arxiv")
#   icon.get_xml(fill="#B31B1B")
# ---------------------------------------------------------------------------


def simple_icon(slug: str, color: str = "#17171C", size: int = 16) -> str:
    """Render a Simple Icons mark as inline SVG, decorative by default.

    Simple Icons ships a <title> inside every SVG. That title becomes an
    accessible name, so it is stripped here: these marks sit beside real text
    labels and must not be announced twice.
    """
    try:
        if simple_icons is None:
            return ""
        icon = simple_icons.get(slug)
        if icon is None:
            return ""
        root = icon.get_xml(fill=color)
        for title in root.findall("{http://www.w3.org/2000/svg}title"):
            root.remove(title)
        for title in root.findall("title"):
            root.remove(title)
        svg = ET.tostring(root, encoding="unicode")
        svg = svg.replace(
            "<svg ",
            f'<svg width="{size}" height="{size}" '
            'style="display:block;flex:0 0 auto;" '
            'aria-hidden="true" focusable="false" ',
        )
        return svg
    except Exception:
        return ""


def fallback_mark(label: str) -> str:
    return f'<span class="ra-fallback-mark">{html.escape(label)}</span>'


ARXIV_ICON = simple_icon("arxiv", "#B31B1B", 17) or fallback_mark("A")
STREAMLIT_ICON = simple_icon("streamlit", "#FF4B4B", 17) or fallback_mark("S")
SCHOLAR_ICON = simple_icon("semanticscholar", "#1857B6", 13) or fallback_mark("S")

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

BG = "#FFFFFF"
SURFACE = "#FFFFFF"
SOFT = "#F7F7F5"
SOFTER = "#FBFBFA"
INK = "#17171C"
INK_2 = "#24242A"
MUTED = "#7B7B86"
FAINT = "#A5A5AE"
LINE = "#E3E3E7"
LINE_SOFT = "#EEEEF0"
GREEN = "#003C33"
GREEN_SOFT = "#EDFCE9"
CORAL = "#FF7759"
BLUE = "#1863DC"

PAPER_COLOR = GREEN
CONCEPT_COLOR = "#5F7F70"
SIMILAR_COLOR = "#C6C7C4"
MENTIONS_COLOR = "#D9DCD8"

MAX_SEARCH_RUNS = 10

st.set_page_config(
    page_title="Research Agent",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------


def inject_css() -> None:
    ra_html(
        f"""
        <style>
        :root {{
            --bg: {BG};
            --surface: {SURFACE};
            --soft: {SOFT};
            --softer: {SOFTER};
            --ink: {INK};
            --ink2: {INK_2};
            --muted: {MUTED};
            --faint: {FAINT};
            --line: {LINE};
            --line-soft: {LINE_SOFT};
            --green: {GREEN};
            --green-soft: {GREEN_SOFT};
            --coral: {CORAL};
            --blue: {BLUE};
        }}

        html, body, .stApp, button, input, textarea, select {{
            font-family: "GeistPixel", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
        }}

        .stApp {{
            background: var(--bg);
            color: var(--ink);
        }}

        /* Keep Streamlit controls available. Hide only the unnecessary chrome. */
        #MainMenu, footer, [data-testid="stDecoration"] {{
            display: none !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        .block-container {{
            max-width: 1680px !important;
            padding: 10px 26px 96px !important;
        }}

        .element-container {{
            margin-bottom: 0 !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: #FBFBFA;
            border-right: 1px solid var(--line);
            width: 290px !important;
            min-width: 260px !important;
        }}

        section[data-testid="stSidebar"] > div {{
            padding: 18px 16px 22px 18px !important;
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown p {{
            color: var(--ink2) !important;
        }}

        .ra-side-brand {{
            display:flex;
            align-items:center;
            gap:10px;
            font-size: 18.48px;
            font-weight: 500;
            letter-spacing: -0.04em;
            margin-bottom: 20px;
        }}

        .ra-side-kicker {{
            color: var(--muted);
            font-size: 10.39px;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin: 0 0 12px;
        }}

        .ra-side-section {{
            color: var(--muted);
            font-size: 10.39px;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin: 16px 0 10px;
        }}

        .ra-side-help {{
            color: var(--muted);
            font-size: 10.39px;
            line-height: 1.6;
            margin-top: 6px;
        }}

        section[data-testid="stSidebar"] [data-testid="stMetric"] {{
            background: transparent !important;
            border: 0 !important;
            border-top: 1px solid var(--line) !important;
            border-radius: 0 !important;
            padding: 10px 0 8px !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
            color: var(--muted) !important;
            font-size: 9.24px !important;
            text-transform: uppercase;
            letter-spacing: .10em;
        }}

        section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{
            color: var(--ink) !important;
            font-size: 20.79px !important;
            font-weight: 400 !important;
        }}

        /* Header */
        .ra-header {{
            display:flex;
            align-items:flex-end;
            justify-content:space-between;
            gap: 18px;
            min-height: 58px;
            padding: 2px 0 14px;
            margin: 0 0 16px;
            border-bottom: 1px solid var(--line);
        }}

        .ra-brand {{
            display:flex;
            align-items:center;
            gap: 10px;
        }}

        .ra-brand-icon {{
            width: 30px;
            height: 30px;
            display:grid;
            place-items:center;
            border: 1px solid var(--line);
            border-radius: 10px;
            background: #fff;
            overflow: hidden;
        }}

        .ra-brand-icon svg {{
            width: 16px;
            height: 16px;
        }}

        .ra-fallback-mark {{
            display:grid;
            place-items:center;
            width:100%;
            height:100%;
            color: var(--coral);
            font-size: 11.55px;
            font-weight: 500;
        }}

        .ra-title {{
            font-size: 23.1px;
            line-height: 1;
            letter-spacing: -0.05em;
            font-weight: 500;
        }}

        .ra-subtitle {{
            color: var(--muted);
            font-size: 10.39px;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-top: 8px;
        }}

        .ra-system {{
            display:flex;
            align-items:center;
            gap: 8px;
            color: var(--muted);
            font-size: 10.39px;
            letter-spacing: .09em;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .ra-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #4B8D63;
            box-shadow: 0 0 0 3px #EEF7F0;
        }}

        /* Controls */
        div[data-testid="stSegmentedControl"] {{
            background: #F1F1EE !important;
            border: 1px solid var(--line) !important;
            padding: 3px !important;
            border-radius: 999px !important;
            gap: 2px !important;
        }}

        div[data-testid="stSegmentedControl"] label {{
            border-radius: 999px !important;
            font-size: 10.39px !important;
            font-weight: 400 !important;
        }}

        div[data-testid="stSegmentedControl"] label[data-selected="true"] {{
            background: var(--ink) !important;
            color: white !important;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            min-height: 36px !important;
            border-radius: 999px !important;
            border: 1px solid var(--line) !important;
            background: white !important;
            color: var(--ink) !important;
            font-family: inherit !important;
            font-size: 10.39px !important;
            letter-spacing: .02em !important;
            transition: border-color .15s ease, transform .15s ease, background .15s ease !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            border-color: var(--ink) !important;
            transform: translateY(-1px);
            background: var(--soft) !important;
        }}

        button[kind="primary"] {{
            background: var(--ink) !important;
            color: white !important;
            border-color: var(--ink) !important;
        }}

        button[kind="primary"]:hover {{
            background: #2B2B31 !important;
            color: white !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {{
            border: 1px solid var(--line) !important;
            border-radius: 12px !important;
            background: white !important;
            color: var(--ink) !important;
            box-shadow: none !important;
            font-family: inherit !important;
            font-size: 12.71px !important;
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus {{
            border-color: #A4A4AC !important;
            box-shadow: 0 0 0 3px rgba(23,23,28,.05) !important;
        }}

        .stSlider [role="slider"] {{
            background: var(--ink) !important;
            border-color: var(--ink) !important;
        }}

        /* Layout section headers */
        .ra-grid-head {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:12px;
            border-bottom: 1px solid var(--line);
            padding: 0 0 10px;
            margin-bottom: 14px;
        }}

        .ra-grid-title {{
            color: var(--ink);
            font-size: 12.71px;
            font-weight: 500;
            letter-spacing: -.01em;
        }}

        .ra-grid-meta {{
            color: var(--muted);
            font-size: 9.24px;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}

        .ra-grid-meta-right {{
            text-align: right;
            white-space: nowrap;
        }}

        .ra-workspace-run {{
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap: 10px;
            border-bottom: 1px solid var(--line);
            padding: 0 0 9px;
            margin-bottom: 10px;
            color: var(--muted);
            font-size: 9.24px;
            letter-spacing: .07em;
            text-transform: uppercase;
        }}

        .ra-workspace-run strong {{
            color: var(--ink);
            font-weight: 400;
        }}

        .ra-chat-rail-head {{
            display:flex;
            align-items:baseline;
            justify-content:space-between;
            gap:12px;
            min-height: 32px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--line);
            margin-bottom: 8px;
        }}

        .ra-rail-title {{
            color: var(--ink);
            font-size: 12.71px;
            font-weight: 500;
            letter-spacing: -.01em;
        }}

        .ra-rail-meta {{
            color: var(--muted);
            font-size: 9.24px;
            letter-spacing: .08em;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .ra-chat-rail-head + .ra-empty {{
            margin-top: 0;
        }}


        /* Typography for markdown responses */
        .stMarkdown p {{
            font-size: 15.02px;
            line-height: 1.75;
            color: var(--ink2);
            margin: 0 0 10px;
        }}

        .stMarkdown h1 {{
            font-size: 25.41px;
            line-height: 1.15;
            letter-spacing: -0.05em;
            margin: 0 0 10px;
            color: var(--ink);
        }}

        .stMarkdown h2 {{
            font-size: 18.48px;
            line-height: 1.25;
            letter-spacing: -0.035em;
            margin: 16px 0 8px;
            color: var(--ink);
        }}

        .stMarkdown h3 {{
            font-size: 15.02px;
            line-height: 1.3;
            letter-spacing: -0.02em;
            margin: 14px 0 6px;
            color: var(--ink);
        }}

        .stMarkdown ul, .stMarkdown ol {{
            margin: 0 0 12px 18px;
            padding: 0;
        }}

        .stMarkdown li {{
            margin: 3px 0;
            font-size: 13.86px;
            line-height: 1.65;
            color: var(--ink2);
        }}

        .stMarkdown blockquote {{
            margin: 12px 0;
            padding: 10px 12px;
            border-left: 3px solid var(--line);
            background: var(--softer);
            color: var(--muted);
            border-radius: 0 10px 10px 0;
        }}

        .stMarkdown code {{
            background: var(--soft);
            color: var(--ink);
            border: 1px solid #E7E7EA;
            padding: 1px 5px;
            border-radius: 6px;
            font-size: 0.95em;
        }}

        .stMarkdown pre {{
            background: #111318;
            color: #EAEAF0;
            border-radius: 12px;
            padding: 14px 16px;
            overflow: auto;
            border: 1px solid #23262F;
        }}

        .stMarkdown pre code {{
            background: transparent;
            border: 0;
            color: inherit;
            padding: 0;
        }}

        .stMarkdown table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0 14px;
            font-size: 12.71px;
        }}

        .stMarkdown th, .stMarkdown td {{
            border-bottom: 1px solid var(--line);
            padding: 8px 10px;
            text-align: left;
            vertical-align: top;
        }}

        .stMarkdown th {{
            color: var(--muted);
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-size: 9.24px;
        }}

        .stMarkdown a {{
            color: var(--blue);
            text-decoration: none;
        }}

        .stMarkdown a:hover {{
            text-decoration: underline;
        }}

        /* Source attribution note with brand mark */
        .ra-source-note {{
            display: flex;
            align-items: center;
            gap: 7px;
            color: var(--muted);
            font-size: 10.89px;
            line-height: 1.55;
        }}

        /* Empty states */
        .ra-empty {{
            min-height: 38vh;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            padding: 24px 16px;
        }}

        .ra-empty-card {{
            max-width: 440px;
        }}

        .ra-empty-icon {{
            width: 44px;
            height: 44px;
            border: 1px solid var(--line);
            border-radius: 12px;
            display:grid;
            place-items:center;
            margin: 0 auto 16px;
            background: white;
            overflow: hidden;
        }}

        .ra-empty-icon svg {{
            width: 18px;
            height: 18px;
        }}

        .ra-empty-title {{
            font-size: 25.41px;
            line-height: 1.15;
            letter-spacing: -0.05em;
            margin-bottom: 10px;
            color: var(--ink);
        }}

        .ra-empty-copy {{
            color: var(--muted);
            font-size: 11.55px;
            line-height: 1.7;
            max-width: 420px;
            margin: 0 auto 18px;
        }}

        .ra-empty-flow {{
            display:flex;
            justify-content:center;
            flex-wrap:wrap;
            gap: 8px;
        }}

        .ra-flow-step {{
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 9.24px;
            text-transform: uppercase;
            letter-spacing: .10em;
            color: var(--ink);
            background: white;
        }}

        .ra-flow-arrow {{
            color: var(--faint);
            align-self:center;
            font-size: 11.55px;
        }}

        .ra-workspace-empty {{
            min-height: 260px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            border: 1px dashed var(--line);
            border-radius: 14px;
            background: #FCFCFB;
            color: var(--muted);
            padding: 28px;
        }}

        .ra-workspace-empty-title {{
            color: var(--ink);
            font-size: 16.17px;
            letter-spacing: -.02em;
            margin-bottom: 5px;
        }}

        .ra-workspace-empty-copy {{
            font-size: 10.39px;
            line-height: 1.6;
            color: var(--muted);
        }}

        .ra-compare-empty {{
            border: 1px dashed var(--line);
            border-radius: 12px;
            padding: 28px 18px;
            text-align: center;
            color: var(--muted);
            font-size: 10.39px;
            line-height: 1.7;
            background: #FCFCFB;
        }}

        /* Paper list */
        .ra-paper-row {{
            border: 1px solid var(--line);
            border-radius: 14px;
            background: white;
            padding: 14px 14px 12px;
        }}

        .ra-paper-top {{
            display:flex;
            align-items:flex-start;
            gap: 12px;
            justify-content:space-between;
        }}

        .ra-paper-left {{
            display:flex;
            gap: 10px;
            min-width: 0;
            flex: 1;
        }}

        .ra-paper-icon {{
            width: 28px;
            height: 28px;
            border-radius: 10px;
            border: 1px solid var(--line);
            display:grid;
            place-items:center;
            flex: 0 0 auto;
            background: #FBFBFA;
            overflow:hidden;
        }}

        .ra-paper-icon svg {{
            width: 15px;
            height: 15px;
        }}

        .ra-paper-index {{
            color: var(--muted);
            font-size: 9.24px;
            text-transform: uppercase;
            letter-spacing: .09em;
            margin-bottom: 4px;
        }}

        .ra-paper-title {{
            color: var(--ink);
            font-size: 17.33px;
            font-weight: 600;
            line-height: 1.35;
            letter-spacing: -.03em;
            margin-bottom: 6px;
            word-break: break-word;
        }}

        .ra-paper-meta {{
            color: var(--muted);
            font-size: 10.39px;
            line-height: 1.55;
        }}

        .ra-paper-score {{
            color: var(--ink);
            font-size: 11.55px;
            letter-spacing: .04em;
            text-transform: uppercase;
            white-space: nowrap;
            padding-top: 2px;
        }}

        .ra-paper-links {{
            display:flex;
            gap: 10px;
            align-items:center;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--line-soft);
        }}

        .ra-paper-links a {{
            color: var(--blue);
            font-size: 9.24px;
            text-decoration: none;
        }}

        /* Paper summaries sit directly below the metadata card. */
        .ra-paper-row + div[data-testid="stMarkdownContainer"] p {{
            margin-top: 10px !important;
            margin-bottom: 10px !important;
        }}

        /* Native workspace containers */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--line) !important;
            border-radius: 14px !important;
            background: #FCFCFB !important;
            box-shadow: none !important;
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            color: var(--muted) !important;
            font-family: inherit !important;
            font-size: 11.55px !important;
            font-weight: 400 !important;
            padding: 8px 12px 10px !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--ink) !important;
        }}

        div[data-baseweb="tab-highlight"] {{
            background: var(--ink) !important;
            height: 2px !important;
        }}

        /* Keep the research composer visually attached to the conversation rail. */
        div[data-testid="stForm"] {{
            margin-top: 8px !important;
        }}

        /* Graph host: the Streamlit container, not an HTML opening/closing tag,
           owns the graph boundary. */
        .ra-graph-host {{
            min-height: 520px;
            border-radius: 14px;
            overflow: hidden;
            background:
                radial-gradient(circle at 1px 1px, rgba(23,23,28,.045) 1px, transparent 1px) 0 0 / 16px 16px,
                #FCFCFB;
        }}

        /* Expanders / status */
        div[data-testid="stExpander"] {{
            background: var(--softer) !important;
            border: 1px solid var(--line) !important;
            border-radius: 12px !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }}

        div[data-testid="stExpander"] summary {{
            color: var(--muted) !important;
            font-size: 10.39px !important;
            padding: 10px 12px !important;
        }}

        div[data-testid="stStatus"] {{
            border: 1px solid var(--line) !important;
            border-radius: 14px !important;
            background: #FFFFFF !important;
            box-shadow: 0 8px 24px rgba(23,23,28,.045) !important;
            overflow: hidden !important;
        }}

        div[data-testid="stStatus"] summary {{
            padding: 11px 13px !important;
            color: var(--ink) !important;
            font-size: 12.65px !important;
            font-weight: 500 !important;
            letter-spacing: -.01em !important;
        }}

        /* The progress log scrolls on its own so long runs never clip. */
        div[data-testid="stStatus"] > div {{
            padding: 10px 13px 12px !important;
            border-top: 1px solid var(--line) !important;
            color: var(--muted) !important;
            font-size: 12.65px !important;
            max-height: 220px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            scrollbar-width: thin !important;
            scrollbar-color: #c9c9ce transparent !important;
        }}

        /* Chat */
        [data-testid="stChatMessage"] {{
            padding: 8px 0 18px !important;
            margin: 0 !important;
        }}

        [data-testid="stChatMessageContent"] {{
            max-width: none !important;
        }}

        [data-testid="stChatMessage"] .stMarkdown p {{
            font-size: 13.86px;
            line-height: 1.75;
            color: var(--ink2);
        }}

        .ra-user-message {{
            display:inline-block;
            max-width: 100%;
            background: #101114;
            color: white;
            padding: 10px 12px;
            border-radius: 14px 14px 4px 14px;
            font-size: 12.71px;
            line-height: 1.55;
            letter-spacing: -.01em;
        }}

        .ra-message-meta {{
            color: var(--muted);
            font-size: 9.24px;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-top: 8px;
        }}

        div[data-testid="stForm"], form {{
            border: 1px solid var(--line);
            border-radius: 18px;
            background: white;
            padding: 10px 10px 12px;
            box-shadow: 0 10px 30px rgba(23,23,28,.06);
        }}

        .ra-chat-composer-label {{
            color: var(--muted);
            font-size: 9.24px;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        div[data-testid="stForm"] textarea {{
            min-height: 88px !important;
            resize: vertical !important;
            border: 0 !important;
            border-radius: 10px !important;
            background: #F8F8F6 !important;
            padding: 12px !important;
        }}

        div[data-testid="stForm"] textarea:focus {{
            box-shadow: inset 0 0 0 1px #CFCFD4 !important;
            background: #FFFFFF !important;
        }}

        div[data-testid="stForm"] button[kind="secondary"] {{
            min-height: 34px !important;
            border-radius: 10px !important;
            background: #F7F7F5 !important;
        }}

        div[data-testid="stForm"] button[kind="secondary"]:hover {{
            background: #EFEFED !important;
        }}


        /* Responsive */
        @media (max-width: 1200px) {{
            .block-container {{
                padding-left: 18px !important;
                padding-right: 18px !important;
            }}

            section[data-testid="stSidebar"] {{
                width: 270px !important;
                min-width: 240px !important;
            }}
        }}

        @media (max-width: 900px) {{
            .ra-header {{
                align-items:flex-start;
                flex-direction:column;
            }}

            .ra-system {{
                display:none;
            }}

            .block-container {{
                padding: 18px 14px 110px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout shell
# ---------------------------------------------------------------------------


def inject_layout_overrides() -> None:
    """Install the single Streamlit 1.58 application-shell layout.

    Both rails (chat, workspace) use the exact same pattern: the outer
    rail is a flex column; every fixed piece (headers, tab bar, composer)
    is `flex: 0 0 auto` so it never moves; and there is exactly ONE
    scrolling element per rail, sized with `flex: 1 1 auto` +
    `overflow-y: auto`. Nothing here relies on `position: sticky` with a
    guessed pixel offset — those break the moment a header wraps a line.
    """
    ra_html(
        """
        <style>
        :root {
            --ra-shell-header-height: 78px;
            --ra-shell-pad-top: 10px;
            --ra-rail-height: calc(
                100dvh - var(--ra-shell-header-height) - var(--ra-shell-pad-top)
            );
        }

        /* Streamlit 1.58 shell: neither the browser document nor stMain scrolls. */
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        section[data-testid="stMain"] {
            height: 100dvh !important;
            min-height: 0 !important;
            max-height: 100dvh !important;
            overflow: hidden !important;
        }

        [data-testid="stMainBlockContainer"].block-container,
        .block-container {
            width: 100% !important;
            max-width: 1680px !important;
            height: 100dvh !important;
            min-height: 0 !important;
            max-height: 100dvh !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
            padding: var(--ra-shell-pad-top) 26px 0 !important;
            margin: 0 auto !important;
            display: flex !important;
            flex-direction: column !important;
        }

        .ra-header {
            height: var(--ra-shell-header-height) !important;
            min-height: 0 !important;
            flex: 0 0 auto !important;
            box-sizing: border-box !important;
            margin: 0 !important;
        }

        /* The main 30/70 row is a fixed frame; its two columns never page-scroll. */
        div[data-testid="stVerticalBlock"].st-key-app_rails {
            width: 100% !important;
            height: var(--ra-rail-height) !important;
            min-height: 0 !important;
            max-height: var(--ra-rail-height) !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        div[data-testid="stVerticalBlock"].st-key-app_rails > div[data-testid="stHorizontalBlock"],
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] {
            width: 100% !important;
            height: var(--ra-rail-height) !important;
            min-height: 0 !important;
            max-height: var(--ra-rail-height) !important;
            overflow: hidden !important;
            align-items: stretch !important;
            box-sizing: border-box !important;
        }

        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            height: 100% !important;
            min-height: 0 !important;
            max-height: 100% !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        /* ============================= LEFT: chat rail ======================
           fixed header -> ONE scroller (conversation) -> fixed composer. */

        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child > div[data-testid="stVerticalBlock"],
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            min-height: 0 !important;
            max-height: 100% !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }

        /* The keyed container IS the scroller. Binding overflow to a child that
           may not exist is what silently disabled scrolling. */
        div.st-key-conversation_scroll {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            scrollbar-width: thin !important;
            scrollbar-color: #c9c9ce transparent !important;
            padding-right: 8px !important;
            box-sizing: border-box !important;
        }

        div.st-key-conversation_scroll > div[data-testid="stVerticalBlock"] {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            overflow: visible !important;
        }

        /* Head and composer are SIBLINGS of the scroller, not children. The flex
           column pins them; sticky would have no scrolling ancestor here. */
        /* Explicit flex `order` decouples VISUAL position from CODE/DOM
           order. The composer is rendered early in Python (so we know
           `submitted`/`question` before deciding whether to show the empty
           state), but it must still visually sit at the bottom, pinned,
           like the input bar in a normal chat UI — order:3 does that
           regardless of where its markup actually lands in the DOM. */
        .ra-chat-rail-head {
            flex: 0 0 auto !important;
            order: 1 !important;
            position: relative !important;
            z-index: 5 !important;
            background: #fff !important;
        }

        div.st-key-conversation_scroll {
            order: 2 !important;
        }

        div.st-key-composer_area {
            flex: 0 0 auto !important;
            order: 3 !important;
            position: relative !important;
            z-index: 10 !important;
            margin-top: 10px !important;
            background: #fff !important;
        }

        /* Composer label sits between scroller and form; it must not absorb
           flex space or the scroller loses its height. */
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child > div[data-testid="stVerticalBlock"] > div[data-testid="stHtml"],
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"] > div[data-testid="stHtml"] {
            flex: 0 0 auto !important;
        }

        /* ========================= RIGHT: workspace rail =====================
           Same pattern as the chat rail: the column is a flex column. The
           settings header, the run-status strip, and the tab bar are all
           flex:0 0 auto parents that never move. Only the ACTIVE tab's own
           inner container (papers_scroll / graph_scroll / compare_scroll,
           created in Python) scrolls. No position:sticky, no pixel offsets. */

        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
        div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            min-height: 0 !important;
            max-height: 100% !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
            box-sizing: border-box !important;
        }

        div.st-key-workspace_chrome {
            flex: 0 0 auto !important;
            position: relative !important;
            background: #fff !important;
            padding: 2px 8px 8px 0 !important;
        }

        .ra-workspace-run {
            flex: 0 0 auto !important;
            position: relative !important;
            background: #fff !important;
        }

        /* st.tabs() renders the tab bar and every panel in one wrapper. Making
           that wrapper a flex column keeps the tab bar fixed (flex:0 0 auto)
           and lets the panel area fill + clip the remaining height, handing
           the actual scrolling off to the keyed container placed inside each
           panel body in Python. */
        div[data-testid="stTabs"] {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
        }

        div[data-baseweb="tab-list"] {
            flex: 0 0 auto !important;
            position: relative !important;
            background: #fff !important;
        }

        div[data-baseweb="tab-panel"],
        div[role="tabpanel"] {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }

        div[role="tabpanel"] > div[data-testid="stVerticalBlock"] {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }

        /* The single scroller inside each tab panel. */
        div.st-key-papers_scroll,
        div.st-key-graph_scroll,
        div.st-key-compare_scroll {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            scrollbar-width: thin !important;
            scrollbar-color: #c9c9ce transparent !important;
            padding-right: 8px !important;
            box-sizing: border-box !important;
        }

        div[data-testid="stPopoverBody"] {
            min-width: 350px !important;
            max-width: min(390px, calc(100vw - 32px)) !important;
            max-height: min(78dvh, 760px) !important;
            overflow-y: auto !important;
        }

        div.st-key-settings_popover {
            width: 36px !important;
            min-width: 36px !important;
            height: 36px !important;
            margin-left: auto !important;
        }

        div.st-key-settings_popover button {
            width: 36px !important;
            min-width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 !important;
            background: #fff !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            box-shadow: none !important;
        }

        /* Narrow viewports: Streamlit stacks the two columns vertically.
           The fixed-height, overflow:hidden shell above assumes a
           side-by-side layout with exactly one scroller per rail — on a
           stacked layout that shell just hides everything below the first
           screenful with no way to reach it. Below this breakpoint we drop
           the fixed shell entirely and let the page scroll normally, and
           give each rail's own scroller a bounded height instead of trying
           to fill 100dvh, so both the composer and the workspace stay
           reachable by ordinary scrolling. */
        @media (max-width: 900px) {
            html,
            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            section[data-testid="stMain"] {
                height: auto !important;
                max-height: none !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
            }

            [data-testid="stMainBlockContainer"].block-container,
            .block-container {
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
                display: block !important;
                padding-left: 14px !important;
                padding-right: 14px !important;
            }

            div[data-testid="stVerticalBlock"].st-key-app_rails,
            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] {
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
            }

            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
            }

            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child > div[data-testid="stVerticalBlock"],
            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"],
            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
            div.st-key-app_rails > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"] {
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
            }

            /* Each scroller keeps its own bounded height + scrollbar so a
               long "Thinking…" log or a long paper list never eats the
               whole page — but the composer and the workspace below it
               are always reachable via the normal page scroll. */
            div.st-key-conversation_scroll {
                max-height: 60vh !important;
            }

            div.st-key-composer_area {
                position: sticky !important;
                bottom: 0 !important;
            }

            div[data-testid="stTabs"] {
                height: auto !important;
                min-height: 0 !important;
                overflow: visible !important;
            }

            div[data-baseweb="tab-panel"],
            div[role="tabpanel"] {
                height: auto !important;
                overflow: visible !important;
            }

            div.st-key-papers_scroll,
            div.st-key-graph_scroll,
            div.st-key-compare_scroll {
                max-height: 60vh !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


def init_state() -> None:
    defaults = {
        "messages": [],  # List[ChatMessage]
        "search_runs": [],  # List[SearchRun]
        "selected_run_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def message_value(message: ChatMessage | dict, field: str, default):
    """Read a ChatMessage field from either current models or legacy dictionaries."""
    value = getattr(message, field, None)
    if value is not None:
        return value
    if isinstance(message, dict):
        return message.get(field, default)
    getter = getattr(message, "get", None)
    return getter(field, default) if callable(getter) else default


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
    """Editorial paper detail with compact screening and citation utilities."""
    title = html.escape(p.title)
    arxiv_id = html.escape(p.arxiv_id)
    authors = html.escape(
        ", ".join(p.authors[:5]) + (" et al." if len(p.authors) > 5 else "")
    )
    primary_category = html.escape(p.primary_category)
    published = html.escape(p.published[:10])
    abs_url = html.escape(p.abs_url)
    pdf_url = html.escape(p.pdf_url or "")
    ra_html(
        f"""
        <div class="ra-paper-row">
            <div class="ra-paper-top">
                <div class="ra-paper-left">
                    <div class="ra-paper-icon">{ARXIV_ICON}</div>
                    <div style="min-width:0;flex:1;">
                        <div class="ra-paper-index">{i:02d} · {primary_category} · {published}</div>
                        <div class="ra-paper-title">{title}</div>
                        <div class="ra-paper-meta">{arxiv_id}<br>{authors}</div>
                    </div>
                </div>
                <div class="ra-paper-score">{p.relevance_score:.3f}</div>
            </div>
            <div class="ra-paper-links">
                <a href="{abs_url}" target="_blank">Abstract</a>
                <span style="color:#C8C8CC;font-size:9.24px;">·</span>
                <a href="{pdf_url}" target="_blank">PDF</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render the summary as a normal Markdown block. The card itself is an
    # independent HTML element above; using separate opening/closing HTML
    # fragments cannot wrap a later Streamlit element.
    st.markdown(p.summary)

    btn_cols = st.columns([1, 1, 1, 2])
    with btn_cols[0]:
        if st.button("Keep", key=f"keep_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "keep"
            st.rerun()
    with btn_cols[1]:
        if st.button("Maybe", key=f"maybe_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "maybe"
            st.rerun()
    with btn_cols[2]:
        if st.button("Skip", key=f"skip_{run.id}_{p.arxiv_id}_{i}"):
            p.status = "skip"
            st.rerun()
    with btn_cols[3]:
        st.caption(f"SCREENING · {p.status.upper()}")

    new_note = st.text_input(
        "Screening note",
        value=p.note or "",
        key=f"note_{run.id}_{p.arxiv_id}_{i}",
        placeholder="Add a short screening note…",
        label_visibility="collapsed",
    )
    if new_note != (p.note or ""):
        p.note = new_note

    with st.expander("Citation chaining", expanded=False):
        cit_key = f"cit_data_{p.arxiv_id}"

        if st.button(
            "Fetch references and citing papers",
            key=f"fetch_cit_{run.id}_{p.arxiv_id}_{i}",
        ):
            with st.spinner("Fetching citation data…"):
                st.session_state[cit_key] = get_citations(p.arxiv_id)

        cit_data = st.session_state.get(cit_key)
        if cit_data is None:
            ra_html(
                f'<div class="ra-source-note">{SCHOLAR_ICON}'
                f"<span>Pull references and forward citations from "
                f"Semantic&nbsp;Scholar.</span></div>",
                unsafe_allow_html=True,
            )
            return

        refs = cit_data.get("references", [])
        cits = cit_data.get("citations", [])

        if not refs and not cits:
            st.caption("No citation data available.")
            return

        if refs:
            st.caption(f"REFERENCES · {len(refs)}")
            for ref in refs[:8]:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.caption(f"{ref['title']} · {ref['year']}")
                with c2:
                    if ref.get("arxiv_id") and st.button(
                        "Add",
                        key=f"add_ref_{run.id}_{p.arxiv_id}_{ref['arxiv_id']}",
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

        if cits:
            st.caption(f"CITING PAPERS · {len(cits)}")
            for cit in cits[:8]:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.caption(f"{cit['title']} · {cit['year']}")
                with c2:
                    if cit.get("arxiv_id") and st.button(
                        "Add",
                        key=f"add_cit_{run.id}_{p.arxiv_id}_{cit['arxiv_id']}",
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
        ra_html(
            """
            <div class="ra-workspace-empty">
                <div class="ra-workspace-empty-title">
                    No papers in this workspace yet.
                </div>
                <div class="ra-workspace-empty-copy">
                    Run a research question to populate the evidence set.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    hdr_col1, hdr_col2 = st.columns([3, 1])
    with hdr_col1:
        st.caption(f"{len(run.papers)} papers · ranked evidence set")
    with hdr_col2:
        st.download_button(
            label="Download BibTeX",
            data=generate_bibtex(run.papers),
            file_name=f"papers_{run.id}.bib",
            mime="text/x-bibtex",
            key=f"bibtex_{run.id}",
            use_container_width=True,
        )

    for i, p in enumerate(run.papers, 1):
        status = f" · {p.status}" if p.status != "unreviewed" else ""
        with st.expander(f"{i:02d}  {p.title}{status}", expanded=False):
            _render_paper_card(p, run, i)


def render_graph(run: SearchRun | None) -> None:
    """Renders the concept graph using st_link_analysis (Cytoscape.js-based)
    in place of the previous streamlit-agraph rendering. Real interactivity:
    zoom/pan/fit, element selection with a properties side panel, and
    neighbor highlighting on click — none of which the old library offered.
    """
    if not run or not run.graph or not run.graph.nodes:
        st.caption("The concept graph appears after a search.")
        return

    graph = run.graph

    elements = {
        "nodes": [
            {
                "data": {
                    "id": n.id,
                    "label": "PAPER" if n.type == "paper" else "CONCEPT",
                    "name": n.label,
                }
            }
            for n in graph.nodes
        ],
        "edges": [
            {
                "data": {
                    "id": f"e{i}",
                    "label": e.type,  # "MENTIONS" or "SIMILAR_TO"
                    "source": e.source,
                    "target": e.target,
                }
            }
            for i, e in enumerate(graph.edges)
        ],
    }

    node_styles = [
        NodeStyle("PAPER", PAPER_COLOR, "name", icon="description"),
        NodeStyle("CONCEPT", CONCEPT_COLOR, "name", icon="label"),
    ]
    edge_styles = [
        EdgeStyle("MENTIONS", caption="", color=MENTIONS_COLOR, directed=True),
        EdgeStyle("SIMILAR_TO", caption="similar", color=SIMILAR_COLOR, directed=False),
    ]

    n_papers = sum(1 for n in graph.nodes if n.type == "paper")
    n_concepts = sum(1 for n in graph.nodes if n.type == "concept")
    st.caption(
        f"{n_papers} papers · {n_concepts} concepts · {len(graph.edges)} edges — "
        f"click a paper node to open its PDF"
    )

    events = [Event("click", "node", ["id", "label"])]
    result = st_link_analysis(
        elements,
        layout="cose",
        node_styles=node_styles,
        edge_styles=edge_styles,
        events=events,
        height=600,
        key=f"graph_{run.id}",
    )

    # Click behavior: paper node click opens its PDF directly — no follow-up
    # question, no LLM call, matching the original spec exactly. Concept
    # node clicks currently do nothing extra (no equivalent spec existed);
    # left as pure selection/highlight, which st_link_analysis handles
    # natively via its side panel.
    if result and result.get("label") == "PAPER":
        clicked_id = result.get("id")
        clicked_paper = next((p for p in run.papers if p.arxiv_id == clicked_id), None)
        if clicked_paper and clicked_paper.pdf_url:
            ra_html(
                f'<a href="{clicked_paper.pdf_url}" target="_blank">'
                f"Opening PDF for {clicked_paper.title}…</a>",
                unsafe_allow_html=True,
            )
            ra_html(
                f'<meta http-equiv="refresh" content="0; url={clicked_paper.pdf_url}">',
                unsafe_allow_html=True,
            )


def render_comparison() -> None:
    runs = st.session_state.search_runs
    if len(runs) < 2:
        ra_html(
            """
            <div class="ra-compare-empty">
                Run at least two searches to compare result sets,
                shared papers, and shared concepts.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    options = {r.id: f"{r.query[:35]}…" if len(r.query) > 35 else r.query for r in runs}
    c1, c2 = st.columns(2)
    with c1:
        run_a_id = st.selectbox(
            "Run A", list(options.keys()), format_func=lambda x: options[x], index=0
        )
    with c2:
        run_b_id = st.selectbox(
            "Run B",
            list(options.keys()),
            format_func=lambda x: options[x],
            index=min(1, len(runs) - 1),
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
    m2.metric("Unique to A", len(only_a))
    m3.metric("Unique to B", len(only_b))

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
    question: str,
    status,
    per_query: int,
    top_k: int,
    num_queries: int,
    response_length: str,
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
        search_status=result.search_status,
        search_error=result.search_error,
        timestamp=time.strftime("%H:%M:%S"),
    )

    st.session_state.search_runs.append(search_run)
    if len(st.session_state.search_runs) > MAX_SEARCH_RUNS:
        st.session_state.search_runs.pop(0)
    st.session_state.selected_run_id = run_id

    synthesis = result.synthesis or Synthesis(
        summary="Search temporarily failed.", citations=[], claims=[]
    )
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
inject_css()
inject_layout_overrides()

# Ignore obsolete layout settings left over from an older session.
for _obsolete_key in (
    "chat_rail_width_pct",
    "settings_rail_width_pct",
    "chat_rail_width",
    "settings_rail_width",
):
    st.session_state.pop(_obsolete_key, None)

# Settings are read before the conversation submit handler.
# The popover is rendered later, but the backend needs these values now.
st.session_state.setdefault("pipeline_per_query", 10)
st.session_state.setdefault("pipeline_top_k", 5)
st.session_state.setdefault("pipeline_num_queries", 4)
st.session_state.setdefault("response_length_setting", "Standard")

per_query = int(st.session_state.get("pipeline_per_query", 10))
top_k = int(st.session_state.get("pipeline_top_k", 5))
num_queries = int(st.session_state.get("pipeline_num_queries", 4))
response_length = str(
    st.session_state.get("response_length_setting", "Standard")
).lower()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

ra_html(
    f"""
    <div class="ra-header">
        <div>
            <div class="ra-brand">
                <div class="ra-brand-icon">{ARXIV_ICON}</div>
                <div>
                    <div class="ra-title">Research Agent</div>
                    <div class="ra-subtitle">
                        arXiv retrieval · ranking · synthesis · citation intelligence
                    </div>
                </div>
            </div>
        </div>

        <div class="ra-system">
            <span class="ra-dot"></span>
            <span>session active</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Main application layout
# ---------------------------------------------------------------------------
#
# Conversation is intentionally fixed at 30%.
# Research workspace owns the remaining 70%.
#
# There is no settings column.
# ---------------------------------------------------------------------------

app_shell = st.container(key="app_rails")
chat_col, workspace_col = app_shell.columns(
    [30, 70],
    gap="large",
)


# ---------------------------------------------------------------------------
# Left — Conversation
# ---------------------------------------------------------------------------

with chat_col:

    ra_html(
        """
        <div class="ra-chat-rail-head">
            <div class="ra-rail-title">Conversation</div>
            <div class="ra-rail-meta">grounded synthesis</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # The composer is rendered here, BEFORE the message list / empty state
    # below, so `submitted` and `question` reflect this run's real values
    # by the time the empty-state check runs. (Previously the form was
    # rendered after that check, so `submitted` was always still its stale
    # initial False when the empty-state decision was made — on the exact
    # run someone hit "Send," the empty state rendered anyway, stacked on
    # top of the thinking box that appeared right below it, and the growing
    # combined height pushed the composer off-screen with no way back to
    # it.) CSS `order: 3` on composer_area keeps it visually pinned at the
    # bottom regardless of this earlier code position — the composer never
    # moves, only the message list scrolls, like a normal chat UI.
    composer_area = st.container(key="composer_area")
    with composer_area:
        ra_html(
            '<div class="ra-chat-composer-label">' "Ask a research question" "</div>",
            unsafe_allow_html=True,
        )

        with st.form(
            "research_composer",
            clear_on_submit=True,
        ):

            question = st.text_area(
                "research_question",
                label_visibility="collapsed",
                placeholder="Ask a research question…",
                height=96,
            )

            submitted = st.form_submit_button(
                "Send",
                use_container_width=True,
            )

    # The placeholder lets the empty-state disappear during the same
    # Streamlit run in which the user submits the first question.
    conversation_content = st.container(
        key="conversation_scroll",
        height="stretch",
    )
    empty_state = conversation_content.empty()

    # Transient thinking/status state for the current turn.
    status_anchor = conversation_content.container()

    for message in st.session_state.messages:

        role = message_value(message, "role", "assistant")
        content = message_value(message, "content", "")
        is_unsourced = message_value(message, "is_unsourced", False)
        is_fallback = message_value(message, "is_fallback", False)
        claims = message_value(message, "claims", [])
        msg_response_length = message_value(message, "response_length", "standard")

        with conversation_content.chat_message(role):

            if role == "user":

                ra_html(
                    f'<div class="ra-user-message">'
                    f"{html.escape(content)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(content)

                if is_unsourced:

                    fallback_note = " · router fallback" if is_fallback else ""

                    ra_html(
                        f'<div class="ra-message-meta">'
                        f"LIVE WEB SEARCH{fallback_note} · "
                        f"NOT FROM RETRIEVED PAPERS"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                elif claims:

                    evidence_expanded = msg_response_length == "detailed"

                    with st.expander(
                        (
                            f"Evidence · {len(claims)} "
                            f"supporting claim" + ("" if len(claims) == 1 else "s")
                        ),
                        expanded=evidence_expanded,
                    ):

                        for claim in claims:

                            st.markdown(f"**{html.escape(claim.claim)}**")

                            st.caption(
                                f"{claim.arxiv_id} · "
                                f"*“{claim.supporting_sentence}”*"
                            )

    if not st.session_state.messages and not submitted:
        empty_state.markdown(
            f"""
            <div class="ra-empty">
                <div class="ra-empty-card">
                    <div class="ra-empty-icon">{ARXIV_ICON}</div>
                    <div class="ra-empty-title">What are you researching?</div>
                    <div class="ra-empty-copy">
                        Ask a question. The agent will generate search variants,
                        retrieve and rank papers, synthesize evidence, and build
                        a concept map around the result set.
                    </div>
                    <div class="ra-empty-flow">
                        <span class="ra-flow-step">retrieve</span>
                        <span class="ra-flow-arrow">→</span>
                        <span class="ra-flow-step">rank</span>
                        <span class="ra-flow-arrow">→</span>
                        <span class="ra-flow-step">synthesize</span>
                        <span class="ra-flow-arrow">→</span>
                        <span class="ra-flow-step">map</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Auto-scroll to bottom of conversation. On an ordinary rerun this only
    # nudges the scroller if the user was already near the bottom (so it
    # doesn't yank them away mid-read). On the run where a question was
    # just submitted, it always scrolls to bottom — the same way a normal
    # chat UI jumps to show your message and the reply/status as soon as
    # you hit send, rather than leaving it buried below the fold.
    ra_html(
        f"""
        <script>
        setTimeout(function() {{
            var doc = window.parent ? window.parent.document : document;
            var container = doc.querySelector('div.st-key-conversation_scroll');
            if (container && container.scrollHeight > container.clientHeight) {{
                var force = {str(bool(submitted)).lower()};
                var atBottom = container.scrollHeight - container.scrollTop
                    <= container.clientHeight + 80;
                if (force || atBottom) {{
                    container.scrollTop = container.scrollHeight;
                }}
            }}
        }}, 120);
        </script>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # EXISTING BACKEND LOGIC — unchanged
    # -----------------------------------------------------------------------

    if submitted and question.strip():

        user_question = question.strip()

        user_msg = ChatMessage(
            role="user",
            content=user_question,
        )

        st.session_state.messages.append(user_msg)

        current_run = get_selected_run()

        context_papers = current_run.papers if current_run else []

        with status_anchor:
            with st.status(
                "Thinking…",
                expanded=True,
            ) as status:

                intent, is_fallback = route(
                    user_question,
                    context_papers,
                    st.session_state.messages[:-1],
                )

                label_text = intent.replace(
                    "_",
                    " ",
                )

                if is_fallback:
                    label_text += " · fallback"

                status.write(f"Route: **{label_text}**")

                if intent == "new_search":

                    synthesis_obj, new_run = handle_new_search(
                        user_question,
                        status,
                        per_query,
                        top_k,
                        num_queries,
                        response_length,
                    )

                    _no_papers = len(new_run.papers) == 0
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=synthesis_obj.summary,
                        intent="new_search",
                        search_run_id=new_run.id,
                        is_unsourced=_no_papers,
                        is_fallback=False,
                        claims=synthesis_obj.claims,
                        response_length=response_length,
                    )

                elif intent == "follow_up_grounded":

                    synthesis_obj = handle_follow_up_grounded(
                        user_question,
                        status,
                        current_run,
                        top_k,
                        response_length,
                    )

                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=synthesis_obj.summary,
                        intent="follow_up_grounded",
                        search_run_id=(current_run.id if current_run else None),
                        is_unsourced=False,
                        is_fallback=False,
                        claims=synthesis_obj.claims,
                        response_length=response_length,
                    )

                else:

                    answer = handle_follow_up_general(
                        user_question,
                        status,
                    )

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

                status.update(
                    label="Answer ready",
                    state="complete",
                    expanded=False,
                )

        st.session_state.messages.append(assistant_msg)

        st.rerun()


# ---------------------------------------------------------------------------
# Center — Research workspace
# ---------------------------------------------------------------------------

with workspace_col:

    # Settings trigger is deliberately part of this header row.
    workspace_chrome = st.container(key="workspace_chrome")
    workspace_head_left, workspace_head_right = workspace_chrome.columns(
        [1, 0.46],
        gap="small",
        vertical_alignment="center",
    )

    with workspace_head_left:
        ra_html(
            '<div class="ra-grid-title ra-workspace-head">Research workspace</div>',
            unsafe_allow_html=True,
        )

    with workspace_head_right:
        action_meta, action_gear = st.columns(
            [1, 0.18],
            gap="small",
            vertical_alignment="center",
        )

        with action_meta:
            ra_html(
                '<div class="ra-grid-meta ra-grid-meta-right">'
                "papers · graph · comparison"
                "</div>",
                unsafe_allow_html=True,
            )

        with action_gear:
            with st.popover(
                "",
                icon=":material/settings:",
                help="Research settings",
                key="settings_popover",
                width=390,
            ):
                ra_html(
                    '<div class="ra-popover-title">Settings</div>',
                    unsafe_allow_html=True,
                )
                ra_html(
                    '<div class="ra-popover-subtitle">'
                    "research controls · response · session"
                    "</div>",
                    unsafe_allow_html=True,
                )

                ra_html(
                    '<div class="ra-side-section">Pipeline controls</div>',
                    unsafe_allow_html=True,
                )

                per_query = st.slider(
                    "Papers per query",
                    min_value=10,
                    max_value=150,
                    value=int(st.session_state.get("pipeline_per_query", 10)),
                    step=10,
                    format="%d",
                    help="Number of papers retrieved for each generated query variant.",
                    key="pipeline_per_query",
                )

                ra_html(
                    '<div class="ra-side-help">'
                    "Candidate retrieval depth for every generated query."
                    "</div>",
                    unsafe_allow_html=True,
                )

                top_k = st.slider(
                    "Ranking top-k",
                    min_value=5,
                    max_value=50,
                    value=int(st.session_state.get("pipeline_top_k", 5)),
                    step=5,
                    format="%d",
                    help="Number of ranked papers retained for synthesis.",
                    key="pipeline_top_k",
                )

                ra_html(
                    '<div class="ra-side-help">'
                    "Number of papers retained after ranking."
                    "</div>",
                    unsafe_allow_html=True,
                )

                num_queries = st.slider(
                    "Query variants",
                    min_value=1,
                    max_value=6,
                    value=int(st.session_state.get("pipeline_num_queries", 4)),
                    step=1,
                    format="%d",
                    help="Number of query formulations generated for the research question.",
                    key="pipeline_num_queries",
                )

                ra_html(
                    '<div class="ra-side-help">'
                    "Parallel formulations used to widen retrieval."
                    "</div>",
                    unsafe_allow_html=True,
                )

                ra_html(
                    '<div class="ra-side-section">Response</div>',
                    unsafe_allow_html=True,
                )

                length_options = ["Brief", "Standard", "Detailed"]

                try:
                    response_length_label = st.segmented_control(
                        "response_length_ctrl",
                        options=length_options,
                        default="Standard",
                        key="response_length_widget",
                        label_visibility="collapsed",
                    )
                except AttributeError:
                    response_length_label = st.radio(
                        "response_length_radio",
                        options=length_options,
                        index=1,
                        key="response_length_widget_fallback",
                        horizontal=True,
                        label_visibility="collapsed",
                    )

                response_length_label = (
                    response_length_label
                    or st.session_state.get(
                        "response_length_setting",
                        "Standard",
                    )
                    or "Standard"
                )

                response_length = str(response_length_label).lower()
                st.session_state["response_length_setting"] = response_length_label

                ra_html(
                    {
                        "brief": (
                            '<div class="ra-side-help">'
                            "1–2 sentences · tight evidence."
                            "</div>"
                        ),
                        "standard": (
                            '<div class="ra-side-help">'
                            "3–5 sentences · balanced evidence."
                            "</div>"
                        ),
                        "detailed": (
                            '<div class="ra-side-help">'
                            "5–8 sentences · expanded evidence."
                            "</div>"
                        ),
                    }[response_length],
                    unsafe_allow_html=True,
                )

                ra_html(
                    '<div class="ra-side-section">Session</div>',
                    unsafe_allow_html=True,
                )

                m1, m2 = st.columns(2)

                with m1:
                    st.metric(
                        "Messages",
                        len(st.session_state.messages),
                    )

                with m2:
                    st.metric(
                        "Runs",
                        len(st.session_state.search_runs),
                    )

                active_run = get_selected_run()

                if (
                    active_run
                    and active_run.synthesis
                    and active_run.synthesis.citations
                ):
                    with st.expander(
                        "Citation IDs",
                        expanded=False,
                    ):
                        st.code(
                            "\n".join(active_run.synthesis.citations),
                            language=None,
                        )

                if st.button(
                    "Clear session",
                    use_container_width=True,
                    key="clear_session_popover",
                ):
                    st.session_state.messages = []
                    st.session_state.search_runs = []
                    st.session_state.selected_run_id = None
                    st.rerun()

            # ---------------------------------------------------------------------------

    # Resolve the currently selected research run AFTER the settings
    # popover block. This must exist before the workspace rendering below.
    current_run = get_selected_run()

    if current_run:

        if current_run.search_status == "search_error":
            st.warning(
                "Search temporarily failed. Please retry; no papers were returned."
            )
        elif current_run.search_status == "partial_results":
            st.info("Partial search results: at least one arXiv query failed.")
        elif current_run.search_status == "no_results":
            st.info("No papers found for this query.")

        ra_html(
            f"""
            <div class="ra-workspace-run">

                <span>
                    <strong>{len(current_run.papers)}</strong>
                    papers ·

                    <strong>
                        {
                            len(current_run.graph.nodes)
                            if current_run.graph
                            else 0
                        }
                    </strong>
                    nodes ·

                    <strong>
                        {
                            len(current_run.graph.edges)
                            if current_run.graph
                            else 0
                        }
                    </strong>
                    edges
                </span>

                <span>
                    {current_run.timestamp}
                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        ra_html(
            """
            <div class="ra-workspace-run">
                <span>NO ACTIVE RESEARCH RUN</span>
                <span>WAITING</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    papers_tab, graph_tab, compare_tab = st.tabs(
        [
            "Papers",
            "Concept graph",
            "Compare",
        ]
    )

    # Each tab gets its OWN fixed-height scroller. The tab bar itself stays
    # put (flex:0 0 auto from the CSS above); only the content below it
    # inside the active tab scrolls, and it starts completely independent
    # scroll-wise from the other tabs since each has its own keyed container.

    with papers_tab:
        with st.container(key="papers_scroll", height="stretch"):
            with st.container(border=True):
                st.markdown('<div id="ra-paper-panel"></div>', unsafe_allow_html=True)
                render_papers(current_run)

    with graph_tab:
        with st.container(key="graph_scroll", height="stretch"):
            if current_run:
                with st.container(border=True):
                    st.markdown(
                        '<div id="ra-graph-panel"></div>', unsafe_allow_html=True
                    )
                    render_graph(current_run)
            else:
                render_graph(current_run)

    with compare_tab:
        with st.container(key="compare_scroll", height="stretch"):
            render_comparison()
