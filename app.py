"""
EnterpriseIQ — Streamlit Chat Interface
Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from src.agent import build_agent, run_query

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EnterpriseIQ",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { background-color: #0d0d0d; }
    .stApp { background-color: #0d0d0d; color: #e8e8e8; }

    /* Header */
    .iq-header {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #00ff9d;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
    }
    .iq-subheader {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 2rem;
        font-family: 'Space Mono', monospace;
    }

    /* Chat messages */
    .user-msg {
        background: #1a1a2e;
        border-left: 3px solid #00ff9d;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 0.95rem;
    }
    .agent-msg {
        background: #111827;
        border-left: 3px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .msg-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .user-label { color: #00ff9d; }
    .agent-label { color: #3b82f6; }

    /* Sidebar */
    .sidebar-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
    }
    .example-chip {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #aaa;
        cursor: pointer;
    }
    .schema-box {
        background: #111;
        border: 1px solid #222;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        color: #555;
        line-height: 1.8;
    }

    /* Input */
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: #e8e8e8 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stButton > button {
        background: #00ff9d !important;
        color: #000 !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button:hover {
        background: #00cc7a !important;
    }

    /* Spinner */
    .stSpinner { color: #00ff9d; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "agent_error" not in st.session_state:
    st.session_state.agent_error = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙ Configuration</div>', unsafe_allow_html=True)

    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get your free key at console.groq.com — no credit card needed"
    )

    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        if st.session_state.agent is None:
            with st.spinner("Initializing agent..."):
                try:
                    st.session_state.agent = build_agent(
                        db_path=os.path.join(os.path.dirname(__file__), "data/chinook.db")
                    )
                    st.session_state.agent_error = None
                except Exception as e:
                    st.session_state.agent_error = str(e)

    st.markdown("---")
    st.markdown('<div class="sidebar-title">💡 Try asking</div>', unsafe_allow_html=True)

    example_questions = [
        "Which country has the most customers?",
        "Top 5 customers by total spend?",
        "How many albums does each artist have?",
        "What's the average invoice total by country?",
        "Which employee supports the most customers?",
        "List all customers from Germany",
        "What's our total revenue so far?",
        "Which tracks are the most expensive?",
    ]

    for q in example_questions:
        if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
            st.session_state.pending_question = q

    st.markdown("---")
    st.markdown('<div class="sidebar-title">🗄 Database Schema</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="schema-box">
    📁 Artist (ArtistId, Name)<br>
    📁 Album (AlbumId, Title, ArtistId)<br>
    📁 Track (TrackId, Name, AlbumId, ...)<br>
    📁 Customer (CustomerId, Name, Country...)<br>
    📁 Invoice (InvoiceId, CustomerId, Total)<br>
    📁 InvoiceLine (TrackId, UnitPrice, Qty)<br>
    📁 Employee (EmployeeId, Title, ReportsTo)
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown('<div class="iq-header">🧠 EnterpriseIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-subheader">Natural language → SQL → Business insights</div>', unsafe_allow_html=True)

# Show error if agent failed to init
if st.session_state.agent_error:
    st.error(f"Agent initialization failed: {st.session_state.agent_error}")

# Show welcome message if no chat yet
if not st.session_state.messages:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2937; border-radius:12px; padding:24px; margin:20px 0; text-align:center;">
        <div style="font-size:2.5rem; margin-bottom:12px;">📊</div>
        <div style="font-family:'Space Mono',monospace; color:#00ff9d; font-size:1rem; margin-bottom:8px;">Ready to analyze your data</div>
        <div style="color:#555; font-size:0.85rem;">Enter your OpenAI API key in the sidebar, then ask any business question about the database.</div>
    </div>
    """, unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="user-msg">
            <div class="msg-label user-label">▶ You</div>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="agent-msg">
            <div class="msg-label agent-label">◆ EnterpriseIQ</div>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# ── Input handling ────────────────────────────────────────────────────────────
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "Ask a question",
        label_visibility="collapsed",
        placeholder="e.g. Which country generates the most revenue?",
        key="user_input"
    )
with col2:
    submit = st.button("Ask →", use_container_width=True)

# Handle example question clicks from sidebar
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
    submit = True

# Process the question
if submit and user_input:
    if not st.session_state.agent:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar first.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("🔍 Querying database..."):
            answer = run_query(st.session_state.agent, user_input)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
