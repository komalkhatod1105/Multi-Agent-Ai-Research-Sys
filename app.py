import os
import re
from datetime import date
from html import escape
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain


st.set_page_config(
    page_title="Multi-Agent AI Research Paper",
    page_icon=":material/biotech:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,400,0,0&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #080B12;
        --surface: #101522;
        --panel: #151C2C;
        --border: #273149;
        --violet: #7C5CFF;
        --violet-soft: #A78BFA;
        --cyan: #22D3EE;
        --text: #F8FAFC;
        --muted: #A7B0C0;
        --dim: #78849A;
        --success: #34D399;
        --warning: #FBBF24;
        --error: #FB7185;
    }

    html, body, [class*="css"], button, input, textarea {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--text);
    }
    .stApp, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
    [data-testid="stHeader"] { background: rgba(8, 11, 18, 0.92); }
    [data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
    .block-container { max-width: 1440px; padding: 2.2rem 2.5rem 4rem; }
    #MainMenu, footer { visibility: hidden; }

    h1, h2, h3 { color: var(--text) !important; letter-spacing: 0 !important; }
    h1 { font-size: 2rem !important; font-weight: 700 !important; }
    h2 { font-size: 1.35rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.05rem !important; font-weight: 600 !important; }
    p, label, li { color: var(--muted); }
    [data-testid="stCaptionContainer"] p { color: var(--muted); }
    a { color: var(--cyan) !important; }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--panel);
        border-color: var(--border) !important;
        border-radius: 10px;
    }
    [data-testid="stMetric"] { background: transparent; border: 0; padding: 0.15rem 0.1rem; }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; }
    [data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700; }
    [data-testid="stMetricDelta"] { color: var(--success) !important; }

    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: var(--muted) !important; font-size: 0.84rem !important; font-weight: 600 !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: #0D1220 !important; color: var(--text) !important;
        border: 1px solid var(--border) !important; border-radius: 8px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #78849A !important; }
    .stTextInput input:focus, .stTextArea textarea:focus-within {
        border-color: var(--violet-soft) !important; box-shadow: 0 0 0 1px rgba(124, 92, 255, 0.28) !important;
    }
    .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button {
        min-height: 2.65rem; border: 1px solid var(--border) !important; border-radius: 8px !important;
        background: #1B2436 !important; color: var(--text) !important; font-weight: 600 !important;
        transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: var(--violet-soft) !important; background: #222C40 !important; transform: translateY(-1px);
    }
    [data-testid="stFormSubmitButton"] button[kind="primary"], .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
        background: var(--violet) !important; border-color: var(--violet) !important; color: #FFFFFF !important;
    }
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover, .stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover {
        background: #6A49F3 !important; border-color: #6A49F3 !important;
    }
    [data-testid="stRadio"] label { color: var(--muted) !important; }
    [data-testid="stRadio"] label:hover { color: var(--text) !important; }
    [data-testid="stTabs"] button { color: var(--muted) !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--violet-soft) !important; }
    [data-testid="stProgressBar"] > div > div { background: var(--violet) !important; }
    [data-testid="stAlert"] { border-radius: 8px; }
    [data-testid="stExpander"] { border-color: var(--border); border-radius: 8px; }

    .brand { display: flex; align-items: center; gap: 0.7rem; margin: 0.25rem 0 2rem; }
    .brand-mark {
        width: 38px; height: 38px; display: grid; place-items: center; border-radius: 10px;
        background: rgba(124, 92, 255, 0.18); border: 1px solid rgba(167, 139, 250, 0.32); color: var(--violet-soft);
    }
    .brand-mark .material-symbols-outlined { font-size: 22px; }
    .brand-name { color: var(--text); font-size: 0.96rem; font-weight: 700; }
    .brand-caption { color: var(--dim); font-size: 0.71rem; margin-top: 2px; }
    .eyebrow { color: var(--violet-soft); font-size: 0.78rem; font-weight: 600; margin-bottom: 0.45rem; }
    .page-intro { color: var(--muted); margin: -0.45rem 0 1.5rem; font-size: 0.94rem; }
    .section-title { color: var(--text); font-size: 1.1rem; font-weight: 700; margin: 1.8rem 0 0.25rem; }
    .section-subtitle { color: var(--muted); font-size: 0.82rem; margin: 0 0 0.85rem; }
    .inline-badge, .status-badge {
        display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.22rem 0.55rem;
        border: 1px solid var(--border); border-radius: 999px; color: var(--muted); font-size: 0.71rem; font-weight: 600;
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--dim); display: inline-block; }
    .status-dot.ready { background: var(--success); box-shadow: 0 0 8px rgba(52, 211, 153, 0.3); }
    .status-dot.attention { background: var(--warning); }
    .empty-state { padding: 1.1rem 0.2rem; color: var(--muted); font-size: 0.88rem; line-height: 1.7; }
    .empty-state strong { color: var(--text); font-weight: 600; }
    .report-copy { color: var(--muted); font-size: 0.89rem; line-height: 1.75; }
    .agent-row {
        display: grid; grid-template-columns: 38px minmax(0, 1fr) auto; align-items: center; gap: 0.9rem;
        padding: 0.86rem 0.9rem; background: var(--panel); border: 1px solid var(--border); border-radius: 9px;
        margin: 0 0 0.55rem; transition: border-color 150ms ease, background 150ms ease;
    }
    .agent-row:hover { border-color: #44516F; background: #182133; }
    .agent-icon {
        width: 36px; height: 36px; display: grid; place-items: center; border-radius: 9px;
        color: var(--violet-soft); background: rgba(124, 92, 255, 0.12);
    }
    .agent-icon.cyan { color: var(--cyan); background: rgba(34, 211, 238, 0.1); }
    .agent-icon .material-symbols-outlined { font-size: 19px; }
    .agent-name { color: var(--text); font-size: 0.86rem; font-weight: 600; }
    .agent-description { color: var(--muted); font-size: 0.75rem; margin-top: 0.18rem; }
    .agent-state { white-space: nowrap; color: var(--dim); font-size: 0.7rem; }
    .agent-state.done { color: var(--success); }
    .agent-state.preview { color: var(--warning); }
    .agent-track { height: 3px; border-radius: 3px; background: #273149; margin: 0.48rem 0 0 3.15rem; }
    .agent-progress { height: 100%; border-radius: 3px; background: var(--violet); }
    .agent-progress.done { background: var(--success); }
    .sidebar-status { display: flex; justify-content: space-between; gap: 0.5rem; color: var(--muted); font-size: 0.75rem; padding: 0.35rem 0; }
    .sidebar-status strong { color: var(--text); font-weight: 600; }
    .topline { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.6rem; }
    .topline-label { color: var(--muted); font-size: 0.78rem; }
    .muted-note { color: var(--dim); font-size: 0.75rem; }

    @media (max-width: 760px) {
        .block-container { padding: 1.35rem 1rem 3rem; }
        h1 { font-size: 1.65rem !important; }
        .agent-row { grid-template-columns: 34px minmax(0, 1fr); gap: 0.65rem; }
        .agent-state { grid-column: 2; }
        .agent-track { margin-left: 2.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "research" not in st.session_state:
    st.session_state.research = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "page" not in st.session_state:
    st.session_state.page = "New Research"

NAV_ITEMS = ["New Research", "Research History", "Papers", "Knowledge Base", "Agents", "Reports", "Settings"]
AGENT_STEPS = [
    ("planner", "conversion_path", "Research Planner Agent", "Breaks the question into searchable research tasks.", "Plans scope and evidence needs."),
    ("search", "travel_explore", "Literature Search Agent", "Finds relevant research and source material.", "Queries the web and collects candidate sources."),
    ("analysis", "find_in_page", "Document Analysis Agent", "Reads selected sources and captures useful context.", "Extracts details from the most relevant source."),
    ("extraction", "schema", "Knowledge Extraction Agent", "Organizes concepts, claims, and supporting evidence.", "Structures findings for downstream synthesis."),
    ("retrieval", "database", "RAG / Knowledge Retrieval", "Retrieves relevant context from indexed documents.", "Grounds answers in your knowledge base."),
    ("synthesis", "auto_awesome", "Research Synthesis Agent", "Turns evidence into a clear, structured report.", "Drafts and reviews the research report."),
    ("report", "description", "Final Report", "Presents findings, methodology, and source references.", "Ready to export when research is complete."),
]


def make_pdf(report_text):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Multi-Agent AI Research Paper Report",
        author="Multi-Agent AI Research Paper",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ResearchTitle", parent=styles["Title"], textColor=colors.HexColor("#181A28"), spaceAfter=14))
    styles.add(ParagraphStyle(name="ResearchBody", parent=styles["BodyText"], leading=15, spaceAfter=8))
    story = [Paragraph("Multi-Agent AI Research Paper", styles["ResearchTitle"]), Spacer(1, 4)]
    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
        elif line.startswith("#"):
            story.append(Paragraph(escape(line.lstrip("# ")), styles["Heading2"]))
        else:
            story.append(Paragraph(escape(line).replace("**", ""), styles["ResearchBody"]))
    document.build(story)
    return buffer.getvalue()


def download_report(report_text, key):
    if report_text:
        st.download_button(
            "Export PDF",
            data=make_pdf(report_text),
            file_name="multi-agent-ai-research-paper.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            type="primary",
            key=key,
        )
    else:
        st.button("Export PDF", icon=":material/picture_as_pdf:", disabled=True, key=key)


def current_stage_state(stage):
    research = st.session_state.research
    if stage == "search" and research.get("search"):
        return "done", 100
    if stage == "analysis" and research.get("reader"):
        return "done", 100
    if stage == "synthesis" and research.get("report"):
        return "done", 100
    if stage == "report" and research.get("critic"):
        return "done", 100
    if stage in ("extraction", "retrieval"):
        return "preview", 18
    if stage == "planner":
        return "ready", 0
    return "ready", 0


def render_agent_row(stage, icon, name, description):
    state, progress = current_stage_state(stage)
    labels = {"done": "Complete", "preview": "Not connected", "ready": "Ready", "running": "Processing"}
    icon_color = "cyan" if stage in ("search", "retrieval") else ""
    state_class = "done" if state == "done" else "preview" if state == "preview" else ""
    st.markdown(
        f"""
        <div class="agent-row">
            <div class="agent-icon {icon_color}"><span class="material-symbols-outlined">{escape(icon)}</span></div>
            <div><div class="agent-name">{escape(name)}</div><div class="agent-description">{escape(description)}</div></div>
            <div class="agent-state {state_class}">{labels[state]}</div>
        </div>
        <div class="agent-track"><div class="agent-progress {'done' if state == 'done' else ''}" style="width:{progress}%"></div></div>
        """,
        unsafe_allow_html=True,
    )


def render_flow():
    st.markdown('<div class="section-title">Multi-agent research flow</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">A traceable path from your question to a cited report.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            '<div class="agent-row"><div class="agent-icon cyan"><span class="material-symbols-outlined">search</span></div>'
            '<div><div class="agent-name">Your research question</div><div class="agent-description">The scope and intent that guide each stage.</div></div>'
            '<div class="agent-state">Input</div></div>',
            unsafe_allow_html=True,
        )
        for stage, icon, name, description, _ in AGENT_STEPS:
            render_agent_row(stage, icon, name, description)


def render_workspace(results):
    st.markdown('<div class="section-title">Research workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Sources and evidence stay alongside the generated synthesis.</div>', unsafe_allow_html=True)
    search_tab, paper_tab, insight_tab, citation_tab = st.tabs(["Search results", "Papers", "Insights", "Citations"])
    with search_tab:
        if results.get("search"):
            st.markdown(results["search"])
        else:
            st.markdown('<div class="empty-state"><strong>No search results yet.</strong><br>Start a research run to see relevant sources here.</div>', unsafe_allow_html=True)
    with paper_tab:
        if results.get("reader"):
            st.markdown(results["reader"])
        else:
            st.markdown('<div class="empty-state"><strong>No papers analyzed.</strong><br>Selected documents will appear here with their extracted context.</div>', unsafe_allow_html=True)
    with insight_tab:
        if results.get("report"):
            st.markdown(results["report"])
        else:
            st.markdown('<div class="empty-state"><strong>Insights will appear after synthesis.</strong><br>Findings are grounded in the retrieved research material.</div>', unsafe_allow_html=True)
    with citation_tab:
        urls = list(dict.fromkeys(re.findall(r"https?://[^\s)\]>]+", results.get("search", ""))))
        if urls:
            for index, url in enumerate(urls[:8], 1):
                st.markdown(f"{index}. [{url}]({url})")
        else:
            st.markdown('<div class="empty-state"><strong>No citations collected yet.</strong><br>Source references will be listed after the search stage.</div>', unsafe_allow_html=True)


def render_metrics():
    results = st.session_state.research
    source_count = len(set(re.findall(r"https?://[^\s)\]>]+", results.get("search", ""))))
    values = [
        ("Research sessions", str(len(st.session_state.history)), "history"),
        ("Sources found", str(source_count), "search results"),
        ("Reports generated", str(sum(bool(item.get("report")) for item in st.session_state.history)), "this workspace"),
        ("Indexed documents", "0", "knowledge base"),
    ]
    columns = st.columns(4)
    for column, (label, value, detail) in zip(columns, values):
        with column:
            with st.container(border=True):
                st.metric(label, value)
                st.caption(detail)


def run_research(topic):
    missing = []
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        missing.append("GEMINI_API_KEY (or GOOGLE_API_KEY)")
    if not os.getenv("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    if missing:
        st.error("Research is unavailable until you configure " + " and ".join(missing) + " in the app environment.")
        return

    results = {}
    try:
        with st.status("Research pipeline running", expanded=True) as status:
            st.write("Literature Search Agent is searching for relevant sources…")
            search_agent = build_search_agent()
            search_result = search_agent.invoke({"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]})
            results["search"] = search_result["messages"][-1].content

            status.update(label="Analyzing selected research source", state="running")
            st.write("Document Analysis Agent is reading the most relevant source…")
            reader_agent = build_reader_agent()
            reader_result = reader_agent.invoke({
                "messages": [HumanMessage(content=(
                    f"Based on the following search results about '{topic}', pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{results['search'][:800]}"
                ))]
            })
            results["reader"] = reader_result["messages"][-1].content

            status.update(label="Synthesizing the research report", state="running")
            research = f"SEARCH RESULTS:\n{results['search']}\n\nDETAILED SCRAPED CONTENT:\n{results['reader']}"
            results["report"] = writer_chain.invoke({"topic": topic, "research": research})

            status.update(label="Reviewing report quality", state="running")
            results["critic"] = critic_chain.invoke({"report": results["report"]})
            status.update(label="Research complete", state="complete", expanded=False)
        st.session_state.research = results
        st.session_state.history.insert(0, {"topic": topic, "date": date.today().isoformat(), **results})
        st.success("Research report is ready.")
    except Exception as error:
        st.error(f"Research stopped: {error}")


def render_dashboard():
    st.markdown('<div class="eyebrow">RESEARCH OVERVIEW</div>', unsafe_allow_html=True)
    st.title("Good research starts with a better question.")
    st.markdown('<div class="page-intro">Search, analyze, and synthesize reliable sources in one focused workspace.</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Start a research run")
        st.caption("Describe the topic, question, or hypothesis you want to investigate.")
        with st.form("research_form"):
            topic = st.text_input("Research question", placeholder="e.g. How are small language models changing on-device AI?")
            submitted = st.form_submit_button("Start Research", icon=":material/arrow_forward:", type="primary", use_container_width=True)
        if submitted:
            if topic.strip():
                run_research(topic.strip())
            else:
                st.warning("Enter a research question to begin.")
        st.caption("Try: multimodal retrieval · battery recycling policy · evaluation of AI agents")

    st.markdown('<div class="section-title">Workspace activity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Live counts from this session.</div>', unsafe_allow_html=True)
    render_metrics()

    render_flow()

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        render_workspace(st.session_state.research)
    with right:
        st.markdown('<div class="section-title">Knowledge base</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">RAG context available to future research runs.</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### No indexed documents")
            st.markdown('<div class="report-copy">Document storage and vector retrieval are not connected in this project yet. Search and source analysis are available; RAG retrieval is shown as a planned stage.</div>', unsafe_allow_html=True)
            st.progress(0, text="0 documents indexed")
            st.markdown('<span class="inline-badge">RAG connector · Not connected</span>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Final report</div>', unsafe_allow_html=True)
    report = st.session_state.research.get("report", "")
    with st.container(border=True):
        if report:
            st.markdown(report)
            download_report(report, "dashboard_pdf")
        else:
            st.markdown('<div class="empty-state"><strong>Your report will appear here.</strong><br>Run a search to generate an executive summary, findings, methodology, and source list.</div>', unsafe_allow_html=True)
            download_report("", "dashboard_pdf_empty")


def render_history():
    st.title("Research history")
    st.markdown('<div class="page-intro">Completed research runs saved in this session.</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        with st.container(border=True):
            st.markdown('<div class="empty-state"><strong>No research runs yet.</strong><br>Your completed sessions will be listed here.</div>', unsafe_allow_html=True)
        return
    for item in st.session_state.history:
        with st.container(border=True):
            st.markdown(f"### {escape(item['topic'])}")
            st.caption(f"{item['date']} · {'Report ready' if item.get('report') else 'Incomplete'}")
            if item.get("report"):
                with st.expander("View report"):
                    st.markdown(item["report"])


def render_papers():
    st.title("Papers and sources")
    st.markdown('<div class="page-intro">Research sources discovered during your active session.</div>', unsafe_allow_html=True)
    search_text = st.session_state.research.get("search", "")
    if not search_text:
        with st.container(border=True):
            st.markdown('<div class="empty-state"><strong>No sources collected.</strong><br>Run a literature search to review source links and extracted context here.</div>', unsafe_allow_html=True)
        return
    with st.container(border=True):
        st.markdown(search_text)
    if st.session_state.research.get("reader"):
        st.markdown("### Analyzed source")
        with st.container(border=True):
            st.markdown(st.session_state.research["reader"])


def render_knowledge_base():
    st.title("Knowledge base")
    st.markdown('<div class="page-intro">A source library for reusable, retrieval-grounded research.</div>', unsafe_allow_html=True)
    columns = st.columns(3)
    for column, label, value in zip(columns, ("Documents", "Text chunks", "Retrieved context"), ("0", "0", "Not connected")):
        with column:
            with st.container(border=True):
                st.metric(label, value)
    with st.container(border=True):
        st.markdown("### Retrieval is not connected yet")
        st.markdown('<div class="report-copy">The current backend does not include document ingestion, vector storage, or RAG retrieval. This workspace makes that boundary explicit instead of presenting placeholder documents as indexed sources.</div>', unsafe_allow_html=True)
        st.markdown('<span class="inline-badge">Sources · None indexed</span> &nbsp; <span class="inline-badge">Relevance scores · Not available</span>', unsafe_allow_html=True)


def render_agents():
    st.title("Research agents")
    st.markdown('<div class="page-intro">Current execution stages and their connection status.</div>', unsafe_allow_html=True)
    for stage, icon, name, description, detail in AGENT_STEPS:
        render_agent_row(stage, icon, name, description)
        if stage in ("extraction", "retrieval"):
            st.caption(detail + " This stage is a UI preview; it is not connected to the current backend.")


def render_reports():
    st.title("Reports")
    st.markdown('<div class="page-intro">Research syntheses generated in the current session.</div>', unsafe_allow_html=True)
    report = st.session_state.research.get("report", "")
    if not report:
        with st.container(border=True):
            st.markdown('<div class="empty-state"><strong>No report generated.</strong><br>Start a research run to create an executive summary, findings, methodology, and references.</div>', unsafe_allow_html=True)
            download_report("", "reports_pdf_empty")
        return
    with st.container(border=True):
        st.markdown(report)
        download_report(report, "reports_pdf")
    if st.session_state.research.get("critic"):
        st.markdown("### Review notes")
        with st.container(border=True):
            st.markdown(st.session_state.research["critic"])


def render_settings():
    st.title("Settings")
    st.markdown('<div class="page-intro">Provider configuration is read from the server environment and is never displayed.</div>', unsafe_allow_html=True)
    google_ready = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    tavily_ready = bool(os.getenv("TAVILY_API_KEY"))
    with st.container(border=True):
        st.markdown("### Connected services")
        for name, ready in (("Google Gemini", google_ready), ("Tavily Search", tavily_ready)):
            label = "Configured" if ready else "Needs API key"
            status = "ready" if ready else "attention"
            st.markdown(f'<div class="sidebar-status"><strong>{name}</strong><span><span class="status-dot {status}"></span> &nbsp;{label}</span></div>', unsafe_allow_html=True)
        if not google_ready or not tavily_ready:
            st.info("Add GEMINI_API_KEY (or GOOGLE_API_KEY) and TAVILY_API_KEY to the app's .env file, then restart Streamlit to enable live research.")
    with st.container(border=True):
        st.markdown("### Research pipeline")
        st.markdown("Search, source analysis, synthesis, and report review are implemented. Document indexing and RAG retrieval are not connected in the current backend.")


with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark"><span class="material-symbols-outlined">biotech</span></div>'
        '<div><div class="brand-name">Multi-Agent AI Research Paper</div><div class="brand-caption">Research workspace</div></div></div>',
        unsafe_allow_html=True,
    )
    selected_page = st.radio("Workspace", NAV_ITEMS, key="page", label_visibility="collapsed")
    st.divider()
    gemini_configured = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    tavily_configured = bool(os.getenv("TAVILY_API_KEY"))
    st.markdown('<div class="muted-note">PROVIDERS</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-status"><span>Gemini</span><span class="status-dot {"ready" if gemini_configured else "attention"}"></span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-status"><span>Tavily Search</span><span class="status-dot {"ready" if tavily_configured else "attention"}"></span></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Multi-Agent AI Research Paper · Research workspace")


st.markdown(
    f'<div class="topline"><div class="topline-label">Workspace / {escape(selected_page)}</div>'
    '<div class="inline-badge"><span class="status-dot ready"></span> Private workspace</div></div>',
    unsafe_allow_html=True,
)

if selected_page == "New Research":
    render_dashboard()
elif selected_page == "Research History":
    render_history()
elif selected_page == "Papers":
    render_papers()
elif selected_page == "Knowledge Base":
    render_knowledge_base()
elif selected_page == "Agents":
    render_agents()
elif selected_page == "Reports":
    render_reports()
else:
    render_settings()