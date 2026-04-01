"""
EnterpriseIQ - Streamlit chat interface.
Run with: streamlit run app.py
"""

import html
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from src.agent import build_agent, run_query


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "data" / "chinook.db"
QUESTION_SUGGESTIONS = [
    "Which country has the most customers?",
    "Top 5 customers by total spend?",
    "How many albums does each artist have?",
    "What is the average invoice total by country?",
    "Which employee supports the most customers?",
    "List all customers from Germany.",
]


st.set_page_config(
    page_title="EnterpriseIQ",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        :root {
            --bg: #071218;
            --text: #eef7f1;
            --muted: #88a0ad;
            --accent: #75f7b1;
            --accent-2: #8cabff;
            --warning: #ffd47a;
            --shadow: 0 28px 90px rgba(0, 0, 0, 0.32);
        }

        .stApp {
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(117, 247, 177, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(140, 170, 255, 0.12), transparent 24%),
                linear-gradient(180deg, #071218 0%, #09141b 36%, #081017 100%);
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"] {
            background: transparent;
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 7rem;
        }

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(13, 20, 28, 0.96), rgba(10, 17, 24, 0.92));
            border-right: 1px solid rgba(255, 255, 255, 0.06);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.4rem;
        }

        h1, h2, h3, h4, h5, h6, label, p, span, div {
            color: var(--text);
        }

        .hero-shell {
            position: relative;
            overflow: hidden;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(117, 247, 177, 0.08), rgba(140, 170, 255, 0.08)),
                linear-gradient(180deg, rgba(10, 18, 25, 0.95), rgba(11, 18, 25, 0.82));
            box-shadow: var(--shadow);
            animation: lift-in 420ms ease-out;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(180deg, rgba(0,0,0,0.9), transparent 85%);
            pointer-events: none;
        }

        .hero-grid {
            position: relative;
            display: grid;
            grid-template-columns: minmax(0, 1.5fr) minmax(300px, 0.85fr);
            gap: 1.6rem;
            align-items: end;
            z-index: 1;
        }

        .hero-kicker,
        .section-label,
        .sidebar-kicker,
        .message-label {
            font-size: 0.74rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .hero-title {
            margin: 0.45rem 0 0.7rem;
            font-size: clamp(2.5rem, 5vw, 4.35rem);
            line-height: 0.94;
            letter-spacing: -0.05em;
            color: #f5fff9;
        }

        .hero-copy {
            max-width: 650px;
            font-size: 1rem;
            line-height: 1.7;
            color: #cfe2d8;
        }

        .status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1.2rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.58rem 0.9rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(255, 255, 255, 0.03);
            color: #d8e7df;
            font-size: 0.88rem;
        }

        .status-pill strong {
            color: #f8fffb;
        }

        .status-dot {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 999px;
            background: var(--warning);
            box-shadow: 0 0 0 7px rgba(255, 212, 122, 0.12);
        }

        .status-dot.ready {
            background: var(--accent);
            box-shadow: 0 0 0 7px rgba(117, 247, 177, 0.12);
        }

        .hero-meta {
            display: grid;
            gap: 0.8rem;
        }

        .meta-row {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(6, 11, 16, 0.52);
            backdrop-filter: blur(12px);
        }

        .meta-label {
            display: block;
            margin-bottom: 0.22rem;
            font-size: 0.72rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .meta-value {
            font-size: 0.98rem;
            color: #eff9f3;
        }

        .empty-shell {
            margin-top: 1.2rem;
            padding: 1.5rem 1.6rem;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(9, 15, 22, 0.7);
        }

        .empty-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
        }

        .empty-list {
            margin: 0.7rem 0 0;
            padding-left: 1.1rem;
            color: #cddbd3;
            line-height: 1.8;
        }

        .message-shell {
            margin-top: 1rem;
            padding: 1rem 1.1rem 1.1rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(8, 14, 20, 0.74);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
            animation: lift-in 260ms ease-out;
        }

        .message-shell.user {
            background:
                linear-gradient(180deg, rgba(16, 31, 26, 0.92), rgba(13, 25, 22, 0.88));
            border-color: rgba(117, 247, 177, 0.18);
        }

        .message-shell.assistant {
            background:
                linear-gradient(180deg, rgba(13, 18, 30, 0.92), rgba(10, 15, 24, 0.9));
            border-color: rgba(140, 170, 255, 0.18);
        }

        .message-shell.user .message-label {
            color: var(--accent);
        }

        .message-shell.assistant .message-label {
            color: var(--accent-2);
        }

        .message-copy {
            margin-top: 0.55rem;
            color: #eef7f1;
            line-height: 1.75;
            font-size: 0.98rem;
        }

        .sidebar-block {
            margin-bottom: 1.35rem;
            padding-bottom: 1.1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .sidebar-note {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .key-status {
            margin-top: 0.65rem;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.52rem 0.78rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(255, 255, 255, 0.03);
            font-size: 0.84rem;
        }

        .schema-rail {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: rgba(5, 10, 14, 0.58);
            border: 1px solid rgba(255, 255, 255, 0.06);
            line-height: 1.85;
            color: #d6e2db;
        }

        .example-caption {
            margin: 0.3rem 0 0.7rem;
            color: var(--muted);
            font-size: 0.86rem;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stChatInput"] input {
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background: rgba(4, 8, 12, 0.6) !important;
            color: #f3fff8 !important;
            min-height: 3.1rem !important;
        }

        [data-testid="stTextInput"] label p {
            color: #dce8e1 !important;
        }

        [data-testid="stChatInput"] {
            background: transparent;
        }

        [data-testid="stChatInput"] > div {
            border-radius: 20px;
            background:
                linear-gradient(180deg, rgba(10, 18, 25, 0.92), rgba(10, 18, 25, 0.84));
            border: 1px solid rgba(255, 255, 255, 0.06);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
        }

        .stButton > button {
            width: 100%;
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            background:
                linear-gradient(180deg, rgba(117, 247, 177, 0.96), rgba(76, 224, 143, 0.96)) !important;
            color: #04110a !important;
            font-weight: 700 !important;
            min-height: 2.9rem !important;
            transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
            box-shadow: 0 10px 28px rgba(76, 224, 143, 0.22);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.02);
            box-shadow: 0 14px 34px rgba(76, 224, 143, 0.28);
        }

        .stButton > button:focus {
            box-shadow: 0 0 0 2px rgba(117, 247, 177, 0.22);
        }

        [data-testid="stSidebar"] .stButton > button {
            min-height: 3.2rem !important;
        }

        [data-testid="stAlert"] {
            border-radius: 16px;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        @keyframes lift-in {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 980px) {
            .hero-grid,
            .empty-grid {
                grid-template-columns: 1fr;
            }

            .hero-shell {
                padding: 1.4rem;
            }

            .main .block-container {
                padding-top: 1.4rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_streamlit_secret(name: str) -> str:
    """Safely fetch a secret when running locally or on Community Cloud."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        return ""
    return value.strip() if isinstance(value, str) else ""


def render_message(role: str, content: str) -> None:
    """Render a styled chat message."""
    safe_content = html.escape(content).replace("\n", "<br>")
    label = "You" if role == "user" else "EnterpriseIQ"
    role_class = "user" if role == "user" else "assistant"
    st.markdown(
        f"""
        <div class="message-shell {role_class}">
            <div class="message-label">{label}</div>
            <div class="message-copy">{safe_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "agent_error" not in st.session_state:
    st.session_state.agent_error = None

if "agent_api_key" not in st.session_state:
    st.session_state.agent_api_key = ""


configured_api_key = get_streamlit_secret("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "").strip()


with st.sidebar:
    st.markdown('<div class="sidebar-kicker">Launch Control</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-note">Deploy with a saved app secret, or paste a temporary Groq key for the current session.</div>',
        unsafe_allow_html=True,
    )

    sidebar_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Use a saved app secret on Streamlit Cloud, or paste a session key here.",
    ).strip()

    active_api_key = sidebar_api_key or configured_api_key
    active_key_source = "session override" if sidebar_api_key else ("app secret" if configured_api_key else "")

    if active_api_key:
        if active_api_key != st.session_state.agent_api_key:
            with st.spinner("Connecting EnterpriseIQ..."):
                try:
                    st.session_state.agent = build_agent(
                        db_path=str(DB_PATH),
                        api_key=active_api_key,
                    )
                    st.session_state.agent_api_key = active_api_key
                    st.session_state.agent_error = None
                except Exception as exc:
                    st.session_state.agent = None
                    st.session_state.agent_api_key = ""
                    st.session_state.agent_error = str(exc)

        st.markdown(
            (
                '<div class="key-status">'
                '<span class="status-dot ready"></span>'
                f"Using {active_key_source}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.agent = None
        st.session_state.agent_api_key = ""
        st.markdown(
            '<div class="key-status"><span class="status-dot"></span>Waiting for a Groq API key</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sidebar-block"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-kicker">Try Asking</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="example-caption">Use one of these prompts or type your own question below.</div>',
        unsafe_allow_html=True,
    )

    for index, question in enumerate(QUESTION_SUGGESTIONS):
        if st.button(question, key=f"example_{index}", use_container_width=True):
            st.session_state.pending_question = question
            st.rerun()

    st.markdown('<div class="sidebar-block"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-kicker">Data Scope</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="schema-rail">
            Artist, Album, Track<br>
            Customer, Invoice, InvoiceLine<br>
            Employee support hierarchy<br>
            SQLite database bundled in the repo
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


app_ready = st.session_state.agent is not None
status_class = "ready" if app_ready else ""
status_text = "Analyst online" if app_ready else "Groq key required"
status_source_text = active_key_source or "no key configured yet"


st.markdown(
    f"""
    <div class="hero-shell">
        <div class="hero-grid">
            <div>
                <div class="hero-kicker">SQL analyst workspace</div>
                <h1 class="hero-title">EnterpriseIQ</h1>
                <div class="hero-copy">
                    Ask business questions in plain English. The app inspects the bundled
                    Chinook SQLite dataset, writes SQL on the fly, and returns a direct answer
                    with enough context to act on it.
                </div>
                <div class="status-row">
                    <div class="status-pill">
                        <span class="status-dot {status_class}"></span>
                        <strong>{status_text}</strong>
                    </div>
                    <div class="status-pill"><strong>Database</strong> SQLite / Chinook</div>
                    <div class="status-pill"><strong>Deploy target</strong> Streamlit Community Cloud</div>
                </div>
            </div>
            <div class="hero-meta">
                <div class="meta-row">
                    <span class="meta-label">Inference</span>
                    <span class="meta-value">Groq llama-3.3-70b-versatile</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Authentication</span>
                    <span class="meta-value">{status_source_text.title()}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Entrypoint</span>
                    <span class="meta-value">app.py at repository root</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if st.session_state.agent_error:
    st.error(f"Agent initialization failed: {st.session_state.agent_error}")


if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-shell">
            <div class="empty-grid">
                <div>
                    <div class="section-label">Best questions</div>
                    <ul class="empty-list">
                        <li>Revenue, customer, and country rollups</li>
                        <li>Top-N rankings for customers, albums, and tracks</li>
                        <li>Support workload by employee or region</li>
                    </ul>
                </div>
                <div>
                    <div class="section-label">Deployment note</div>
                    <ul class="empty-list">
                        <li>Works locally with a pasted key or .env</li>
                        <li>Works on Streamlit Cloud with a saved secret</li>
                        <li>No backend rewrite required for the first deployment</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_columns = st.columns(3)
    for index, question in enumerate(QUESTION_SUGGESTIONS[:3]):
        with hero_columns[index]:
            if st.button(question, key=f"hero_prompt_{index}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()


for message in st.session_state.messages:
    render_message(message["role"], message["content"])


prompt = st.chat_input("Ask about revenue, customers, albums, or support operations")
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")

if prompt:
    if not st.session_state.agent:
        st.warning("Add your Groq API key in the sidebar or configure GROQ_API_KEY as a Streamlit secret.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Running SQL analysis..."):
            answer = run_query(st.session_state.agent, prompt)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
