"""
EnterpriseIQ - Streamlit chat interface.
Run with: streamlit run app.py
"""

import html
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from src.agent import build_agent, run_query


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "data" / "chinook.db"
PROMPT_LIBRARY = {
    "Executive Overview": {
        "description": "Good for the first 60 seconds of a recruiter demo: revenue, customer reach, and market performance.",
        "questions": [
            "Which country generates the most revenue?",
            "What is the average invoice total by country?",
            "Who are the top 5 customers by total spend?",
        ],
    },
    "Revenue Analysis": {
        "description": "Focus on commercial performance, invoice value, and product ranking questions.",
        "questions": [
            "What is our total revenue so far?",
            "Which tracks are the most expensive?",
            "What are the top 3 best-selling albums by revenue?",
        ],
    },
    "Customer Intelligence": {
        "description": "Useful for market mix, customer distribution, and account-level exploration.",
        "questions": [
            "Which country has the most customers?",
            "List all customers from Germany.",
            "Who are our top 5 customers by total spend?",
        ],
    },
    "Operations": {
        "description": "Best for support-team coverage, staffing patterns, and operational load balancing.",
        "questions": [
            "Which employee supports the most customers?",
            "How many customers does each support rep handle?",
            "Which countries have the fewest customers?",
        ],
    },
}
QUESTION_SUGGESTIONS = PROMPT_LIBRARY["Executive Overview"]["questions"]
MESSAGE_SECTION_LABELS = {
    "direct answer",
    "business takeaway",
    "recommendation",
    "assumption",
    "data limitation",
    "sql summary",
    "next question",
}


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

        .proof-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 1.1rem;
        }

        .metric-card {
            min-height: 128px;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(8, 14, 20, 0.86), rgba(9, 17, 24, 0.74));
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.14);
        }

        .metric-label {
            font-size: 0.78rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .metric-value {
            margin-top: 0.55rem;
            font-size: 1.95rem;
            line-height: 1;
            letter-spacing: -0.04em;
            color: #f7fff9;
        }

        .metric-note {
            margin-top: 0.7rem;
            color: #bdd2c8;
            line-height: 1.55;
            font-size: 0.92rem;
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

        .message-paragraph {
            margin: 0 0 0.65rem;
        }

        .message-section-title,
        .message-section-heading {
            color: #f7fff9;
            font-weight: 700;
        }

        .message-list {
            margin: 0.15rem 0 0.85rem 1rem;
            padding-left: 1rem;
            color: #dceae2;
            line-height: 1.7;
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

        .mode-note,
        .table-note,
        .story-copy {
            color: #b7c8c0;
            line-height: 1.7;
            font-size: 0.93rem;
        }

        .story-shell {
            margin-top: 1.1rem;
            padding: 1.2rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(9, 15, 22, 0.72);
        }

        .story-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .story-card {
            min-height: 180px;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(9, 16, 22, 0.88), rgba(8, 14, 19, 0.78));
        }

        .story-title {
            margin-top: 0.45rem;
            font-size: 1.05rem;
            color: #f5fff8;
        }

        .rank-list {
            margin-top: 0.85rem;
            display: grid;
            gap: 0.7rem;
        }

        .rank-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.8rem 0.95rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .rank-name {
            color: #f5fff8;
            line-height: 1.45;
        }

        .rank-value {
            color: var(--accent);
            font-weight: 700;
            white-space: nowrap;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stChatInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
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

        [data-testid="stDownloadButton"] > button {
            width: 100%;
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            background:
                linear-gradient(180deg, rgba(140, 172, 255, 0.96), rgba(108, 140, 242, 0.96)) !important;
            color: #07111a !important;
            font-weight: 700 !important;
            min-height: 2.9rem !important;
        }

        button[data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            color: #dfeee5;
            padding: 0.55rem 1rem;
        }

        [data-baseweb="tab-list"] {
            gap: 0.5rem;
            margin-top: 0.8rem;
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
            .empty-grid,
            .proof-strip,
            .story-grid {
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


@st.cache_data(show_spinner=False)
def load_dataset_snapshot(db_path: str) -> dict:
    """Collect a lightweight analytics snapshot for recruiter-friendly exploration."""
    if not Path(db_path).exists():
        return {"available": False}

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        def scalar(query: str):
            return cursor.execute(query).fetchone()[0]

        metrics = {
            "customers": int(scalar("SELECT COUNT(*) FROM Customer")),
            "invoices": int(scalar("SELECT COUNT(*) FROM Invoice")),
            "countries": int(scalar("SELECT COUNT(DISTINCT Country) FROM Customer")),
            "revenue": float(scalar("SELECT ROUND(COALESCE(SUM(Total), 0), 2) FROM Invoice")),
        }

        top_countries = cursor.execute(
            """
            SELECT BillingCountry, ROUND(SUM(Total), 2) AS Revenue
            FROM Invoice
            GROUP BY BillingCountry
            ORDER BY Revenue DESC
            LIMIT 5
            """
        ).fetchall()
        top_customers = cursor.execute(
            """
            SELECT
                Customer.FirstName || ' ' || Customer.LastName AS CustomerName,
                ROUND(SUM(Invoice.Total), 2) AS Revenue
            FROM Customer
            JOIN Invoice ON Invoice.CustomerId = Customer.CustomerId
            GROUP BY Customer.CustomerId
            ORDER BY Revenue DESC
            LIMIT 5
            """
        ).fetchall()
        support_load = cursor.execute(
            """
            SELECT
                Employee.FirstName || ' ' || Employee.LastName AS RepName,
                COUNT(Customer.CustomerId) AS CustomersSupported
            FROM Employee
            JOIN Customer ON Customer.SupportRepId = Employee.EmployeeId
            GROUP BY Employee.EmployeeId
            ORDER BY CustomersSupported DESC
            LIMIT 5
            """
        ).fetchall()

    return {
        "available": True,
        "metrics": metrics,
        "top_countries": top_countries,
        "top_customers": top_customers,
        "support_load": support_load,
    }


def build_transcript(messages: list[dict]) -> str:
    """Create a simple export of the current conversation."""
    lines = [
        "# EnterpriseIQ session export",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    for message in messages:
        speaker = "User" if message["role"] == "user" else "EnterpriseIQ"
        lines.extend([f"## {speaker}", "", message["content"], ""])
    return "\n".join(lines)


def suggest_follow_ups(question: str) -> list[str]:
    """Offer next-step prompts based on the most recent user question."""
    lowered = question.lower()
    if any(token in lowered for token in ["revenue", "invoice", "sales", "spend"]):
        return [
            "Which country generates the most revenue?",
            "Who are our top 5 customers by total spend?",
            "What is the average invoice total by country?",
        ]
    if any(token in lowered for token in ["customer", "country"]):
        return [
            "Which employee supports the most customers?",
            "List all customers from Germany.",
            "What is our total revenue so far?",
        ]
    if any(token in lowered for token in ["employee", "support", "rep"]):
        return [
            "How many customers does each support rep handle?",
            "Which countries have the fewest customers?",
            "Who are our top 5 customers by total spend?",
        ]
    return [
        "Which country generates the most revenue?",
        "How many albums does each artist have?",
        "Which employee supports the most customers?",
    ]


def format_message_html(content: str) -> str:
    """Convert plain-text output into richer HTML for easier scanning."""
    html_parts = []
    list_items = []
    list_tag = "ul"

    def flush_list() -> None:
        nonlocal list_items, list_tag
        if list_items:
            html_parts.append(
                f"<{list_tag} class='message-list'>"
                + "".join(f"<li>{item}</li>" for item in list_items)
                + f"</{list_tag}>"
            )
            list_items = []
            list_tag = "ul"

    for raw_line in content.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            flush_list()
            continue

        if line.startswith(("- ", "* ")):
            if list_items and list_tag != "ul":
                flush_list()
            list_tag = "ul"
            list_items.append(html.escape(line[2:].strip()))
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if numbered_match:
            if list_items and list_tag != "ol":
                flush_list()
            list_tag = "ol"
            list_items.append(html.escape(numbered_match.group(1).strip()))
            continue

        flush_list()

        if ":" in line:
            label, rest = line.split(":", 1)
            if label.strip().lower() in MESSAGE_SECTION_LABELS:
                safe_label = html.escape(label.strip())
                safe_rest = html.escape(rest.strip())
                if safe_rest:
                    html_parts.append(
                        f"<p class='message-paragraph'><span class='message-section-title'>{safe_label}:</span> {safe_rest}</p>"
                    )
                else:
                    html_parts.append(
                        f"<div class='message-section-heading'>{safe_label}</div>"
                    )
                continue

        html_parts.append(f"<p class='message-paragraph'>{html.escape(line)}</p>")

    flush_list()
    return "".join(html_parts) or "<p class='message-paragraph'>No response generated.</p>"


def render_message(role: str, content: str) -> None:
    """Render a styled chat message."""
    label = "You" if role == "user" else "EnterpriseIQ"
    role_class = "user" if role == "user" else "assistant"
    st.markdown(
        f"""
        <div class="message-shell {role_class}">
            <div class="message-label">{label}</div>
            <div class="message-copy">{format_message_html(content)}</div>
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


snapshot = load_dataset_snapshot(str(DB_PATH))
configured_api_key = get_streamlit_secret("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "").strip()
mode_options = list(PROMPT_LIBRARY.keys())


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
    st.markdown('<div class="sidebar-kicker">Analyst Mode</div>', unsafe_allow_html=True)
    selected_mode = st.selectbox("Focus area", mode_options, label_visibility="collapsed")
    st.markdown(
        f'<div class="mode-note">{PROMPT_LIBRARY[selected_mode]["description"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-block"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-kicker">Prompt Starters</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="example-caption">Queue one of these and the chat will run it immediately.</div>',
        unsafe_allow_html=True,
    )

    active_questions = PROMPT_LIBRARY[selected_mode]["questions"]
    for index, question in enumerate(active_questions):
        if st.button(question, key=f"example_{selected_mode}_{index}", use_container_width=True):
            st.session_state.pending_question = question
            st.rerun()

    if st.session_state.messages:
        st.markdown('<div class="sidebar-block"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-kicker">Export Session</div>', unsafe_allow_html=True)
        st.download_button(
            "Download briefing",
            data=build_transcript(st.session_state.messages),
            file_name="enterpriseiq-session.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown('<div class="sidebar-block"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-kicker">Portfolio Signal</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="schema-rail">
            Live NL to SQL workflow<br>
            Streamlit product UI<br>
            Secret-aware deployment path<br>
            SQLite dataset bundled in the repo
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
                <div class="hero-kicker">AI analyst workspace</div>
                <h1 class="hero-title">EnterpriseIQ</h1>
                <div class="hero-copy">
                    A deployable analytics copilot that turns natural-language business questions
                    into SQL-backed answers. It is designed to show product sense, LLM orchestration,
                    data-tool integration, and deployment readiness in one focused demo.
                </div>
                <div class="status-row">
                    <div class="status-pill">
                        <span class="status-dot {status_class}"></span>
                        <strong>{status_text}</strong>
                    </div>
                    <div class="status-pill"><strong>Dataset</strong> Chinook / SQLite</div>
                    <div class="status-pill"><strong>Demo lens</strong> {selected_mode}</div>
                    <div class="status-pill"><strong>Deployment</strong> Streamlit Community Cloud</div>
                </div>
            </div>
            <div class="hero-meta">
                <div class="meta-row">
                    <span class="meta-label">What it proves</span>
                    <span class="meta-value">Prompt design, tool-calling, SQL reasoning, product polish, and practical deployment.</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Best demo path</span>
                    <span class="meta-value">Start with an executive question, follow with a market drill-down, then export the session as a briefing.</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Authentication</span>
                    <span class="meta-value">{status_source_text.title()}</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if st.session_state.agent_error:
    st.error(f"Agent initialization failed: {st.session_state.agent_error}")


if snapshot.get("available"):
    metric_items = [
        ("Customers", f"{snapshot['metrics']['customers']:,}", "Customer coverage for segmentation questions."),
        ("Invoices", f"{snapshot['metrics']['invoices']:,}", "Transaction history for rollups and rankings."),
        ("Countries", f"{snapshot['metrics']['countries']:,}", "Market breadth for geo analysis and comparison."),
        ("Revenue", f"${snapshot['metrics']['revenue']:,.0f}", "A clean KPI anchor for executive-style demos."),
    ]
    metric_columns = st.columns(4)
    for column, (label, value, note) in zip(metric_columns, metric_items):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


tab_ask, tab_explore, tab_story = st.tabs(
    ["Ask the analyst", "Explore the dataset", "Project story"]
)


with tab_ask:
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-shell">
                <div class="empty-grid">
                    <div>
                        <div class="section-label">What each answer should feel like</div>
                        <ul class="empty-list">
                            <li>A direct answer grounded in the database</li>
                            <li>A short business takeaway, not just raw numbers</li>
                            <li>A fast path to the next follow-up question</li>
                        </ul>
                    </div>
                    <div>
                        <div class="section-label">Why this demo lands</div>
                        <ul class="empty-list">
                            <li>Real database access instead of placeholder chat</li>
                            <li>Clear product framing instead of a one-off script</li>
                            <li>Deployment-ready secret handling and a polished UI</li>
                        </ul>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        hero_columns = st.columns(3)
        for index, question in enumerate(active_questions):
            with hero_columns[index]:
                if st.button(question, key=f"hero_prompt_{selected_mode}_{index}", use_container_width=True):
                    st.session_state.pending_question = question
                    st.rerun()

    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

    if st.session_state.messages:
        last_user_question = next(
            (message["content"] for message in reversed(st.session_state.messages) if message["role"] == "user"),
            "",
        )
        follow_ups = suggest_follow_ups(last_user_question)
        st.markdown('<div class="section-label">Next best questions</div>', unsafe_allow_html=True)
        follow_up_columns = st.columns(3)
        for index, question in enumerate(follow_ups):
            with follow_up_columns[index]:
                if st.button(question, key=f"follow_up_{index}", use_container_width=True):
                    st.session_state.pending_question = question
                    st.rerun()

    prompt = st.chat_input("Ask about revenue, customers, albums, or support operations")


with tab_explore:
    st.markdown(
        """
        <div class="story-shell">
            <div class="section-label">Exploration surface</div>
            <div class="story-copy">
                This tab makes the project feel more like an analytics product and less like a bare chat window.
                It gives hiring managers a fast proof that the app is grounded in a real dataset.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if snapshot.get("available"):
        market_column, customer_column = st.columns(2)
        with market_column:
            st.markdown('<div class="section-label">Top revenue markets</div>', unsafe_allow_html=True)
            st.markdown('<div class="table-note">A quick executive view of where revenue is concentrated.</div>', unsafe_allow_html=True)
            market_rows = "".join(
                f"<div class='rank-row'><div class='rank-name'>{html.escape(country)}</div><div class='rank-value'>${revenue:,.0f}</div></div>"
                for country, revenue in snapshot["top_countries"]
            )
            st.markdown(f"<div class='rank-list'>{market_rows}</div>", unsafe_allow_html=True)

        with customer_column:
            st.markdown('<div class="section-label">Top customers</div>', unsafe_allow_html=True)
            st.markdown('<div class="table-note">High-value accounts you can use for follow-up analysis and storytelling.</div>', unsafe_allow_html=True)
            customer_rows = "".join(
                f"<div class='rank-row'><div class='rank-name'>{html.escape(name)}</div><div class='rank-value'>${revenue:,.0f}</div></div>"
                for name, revenue in snapshot["top_customers"]
            )
            st.markdown(f"<div class='rank-list'>{customer_rows}</div>", unsafe_allow_html=True)

        support_column, library_column = st.columns(2)
        with support_column:
            st.markdown('<div class="section-label">Support coverage snapshot</div>', unsafe_allow_html=True)
            st.markdown('<div class="table-note">Useful when you want to show operations or staffing questions.</div>', unsafe_allow_html=True)
            support_rows = "".join(
                f"<div class='rank-row'><div class='rank-name'>{html.escape(name)}</div><div class='rank-value'>{count} customers</div></div>"
                for name, count in snapshot["support_load"]
            )
            st.markdown(f"<div class='rank-list'>{support_rows}</div>", unsafe_allow_html=True)

        with library_column:
            st.markdown('<div class="section-label">Prompt library</div>', unsafe_allow_html=True)
            st.markdown('<div class="table-note">These grouped prompts help the app feel opinionated and demo-friendly.</div>', unsafe_allow_html=True)
            for mode_name, mode_config in PROMPT_LIBRARY.items():
                st.markdown(
                    f"""
                    <div class="story-shell">
                        <div class="section-label">{mode_name}</div>
                        <div class="story-copy">{mode_config["description"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.warning("The bundled database was not found, so the exploration snapshot is unavailable.")


with tab_story:
    st.markdown(
        """
        <div class="story-shell">
            <div class="section-label">Project framing</div>
            <div class="story-copy">
                EnterpriseIQ is strongest when it is presented as a compact product demo:
                real data access, a usable interface, and a deployment path that proves it
                can move beyond a local prototype.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="story-grid">
            <div class="story-card">
                <div class="section-label">Why it matters</div>
                <div class="story-title">LLM plus tools, not just chat</div>
                <div class="story-copy">The agent is grounded in a live SQLite database and uses SQL tooling instead of inventing answers.</div>
            </div>
            <div class="story-card">
                <div class="section-label">Why it matters</div>
                <div class="story-title">Product thinking</div>
                <div class="story-copy">The interface now has onboarding, exploration surfaces, quick-start prompts, and export so the demo feels like software.</div>
            </div>
            <div class="story-card">
                <div class="section-label">Why it matters</div>
                <div class="story-title">Deployment discipline</div>
                <div class="story-copy">Secret-aware configuration, Streamlit Cloud readiness, and a stronger README turn this into a cleaner portfolio piece.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    story_columns = st.columns(2)
    with story_columns[0]:
        st.markdown(
            """
            <div class="story-shell">
                <div class="section-label">What recruiters can evaluate fast</div>
                <ul class="empty-list">
                    <li>Prompt design and structured-response thinking</li>
                    <li>Practical LangChain agent wiring over a real database</li>
                    <li>Secrets handling and deployment awareness</li>
                    <li>UI polish and communication of technical work</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with story_columns[1]:
        st.markdown(
            """
            <div class="story-shell">
                <div class="section-label">60-second demo path</div>
                <ul class="empty-list">
                    <li>Show the Executive Overview prompt set</li>
                    <li>Ask a revenue or customer question live</li>
                    <li>Use the Explore tab to reinforce the data connection</li>
                    <li>Download the session as a mini analyst briefing</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


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
