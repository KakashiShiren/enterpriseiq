"""
EnterpriseIQ - SQL-connected analyst agent.
"""

import os

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

load_dotenv()


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

Use this response format unless the user explicitly asks for something else:
Direct answer: 1-3 sentences with the core result.
Business takeaway:
- 1 or 2 concise bullets about why the result matters.
Assumption: only include when you made one.
Data limitation: only include when the schema or data cannot fully answer the question.

Keep the tone crisp, executive-friendly, and suitable for a live product demo.

Never make up data. If the database doesn't contain what's needed, say so clearly.
"""


def build_agent(db_path: str = "data/chinook.db", api_key: str | None = None):
    """
    Build and return the LangChain SQL agent.
    """
    resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not resolved_api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. Make sure it is set in your environment or Streamlit secrets."
        )

    db = SQLDatabase.from_uri(
        f"sqlite:///{db_path}",
        sample_rows_in_table_info=3,
        include_tables=[
            "Artist",
            "Album",
            "Track",
            "Customer",
            "Invoice",
            "InvoiceLine",
            "Employee",
        ],
    )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=resolved_api_key,
    )

    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        verbose=False,
        system_message=SystemMessage(content=SYSTEM_PROMPT),
        max_iterations=10,
        handle_parsing_errors=True,
    )

    return agent


def run_query(agent, question: str) -> str:
    """
    Run a natural-language question through the SQL agent.
    """
    try:
        result = agent.invoke({"input": question})
        return result.get("output", "No response generated.")
    except Exception as exc:
        return f"Error processing query: {exc}"


if __name__ == "__main__":
    print("Building EnterpriseIQ agent...")
    agent = build_agent()
    print("Agent ready!\n")

    test_questions = [
        "How many customers do we have in total?",
        "Which country has the most customers?",
        "What are the top 3 best-selling albums by revenue?",
        "Who is our highest-grossing customer?",
    ]

    for question in test_questions:
        print(f"\nQ: {question}")
        print(f"A: {run_query(agent, question)}")
        print("-" * 60)
