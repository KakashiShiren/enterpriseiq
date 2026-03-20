"""
EnterpriseIQ — SQL-Connected AI Analyst Agent
Core agent logic using LangChain SQL Agent + conversation memory
"""

import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

load_dotenv()

# ── System prompt that gives the agent its persona ───────────────────────────
SYSTEM_PROMPT = """You are EnterpriseIQ, an expert AI data analyst for a music distribution company.
You have direct access to the company's enterprise database containing:
  - Artists and Albums
  - Tracks and media
  - Customers (with country, city, company)
  - Invoices and sales transactions
  - Employees and support reps

Your job is to answer business questions by querying the database and returning
clear, concise, actionable insights. Always:
1. Write and execute the correct SQL query
2. Interpret the raw results into a human-friendly answer
3. Highlight any business implications where relevant
4. If a question is ambiguous, make a reasonable assumption and state it

Never make up data. If the database doesn't contain what's needed, say so clearly.
"""


def build_agent(db_path: str = "data/chinook.db"):
    """
    Builds and returns the LangChain SQL agent.
    Uses GPT-3.5-turbo for cost efficiency; swap to gpt-4o for better accuracy.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. Make sure it's set in your .env file."
        )

    # Connect to SQLite database
    db = SQLDatabase.from_uri(
        f"sqlite:///{db_path}",
        sample_rows_in_table_info=3,   # shows 3 sample rows in schema context
        include_tables=[               # whitelist tables — good practice for security
            "Artist", "Album", "Track",
            "Customer", "Invoice", "InvoiceLine", "Employee"
        ]
    )

    # LLM — Groq's llama-3.3-70b is fast and free, temperature=0 for deterministic SQL
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=api_key
    )

    # Build the SQL agent
    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",   # Groq supports tool-calling mode
        verbose=True,                # set False in production to hide chain-of-thought
        system_message=SystemMessage(content=SYSTEM_PROMPT),
        max_iterations=10,           # prevents infinite loops on complex queries
        handle_parsing_errors=True   # gracefully handles LLM output errors
    )

    return agent


def run_query(agent, question: str) -> str:
    """
    Runs a natural language question through the SQL agent.
    Returns the agent's final answer as a string.
    """
    try:
        result = agent.invoke({"input": question})
        return result.get("output", "No response generated.")
    except Exception as e:
        return f"⚠️ Error processing query: {str(e)}"


# ── Quick CLI test (run this file directly to verify setup) ──────────────────
if __name__ == "__main__":
    print("🔧 Building EnterpriseIQ agent...")
    agent = build_agent()
    print("✅ Agent ready!\n")

    test_questions = [
        "How many customers do we have in total?",
        "Which country has the most customers?",
        "What are the top 3 best-selling albums by revenue?",
        "Who is our highest-grossing customer?",
    ]

    for q in test_questions:
        print(f"\n📊 Q: {q}")
        print(f"💬 A: {run_query(agent, q)}")
        print("-" * 60)
