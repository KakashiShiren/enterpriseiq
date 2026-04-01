# EnterpriseIQ - SQL-Connected AI Analyst Chatbot

A LangChain-powered AI agent that connects to enterprise databases and answers natural language business questions without requiring SQL knowledge.

[EnterpriseIQ Demo]
https://enterpriseiq-app.streamlit.app/

## What It Does

EnterpriseIQ lets business users ask questions like:
- "Which country generates the most revenue?"
- "Who are our top 5 customers by total spend?"
- "How many albums does each artist have?"

It answers with database-backed results pulled from the connected dataset.

## Architecture

```text
User Question (Natural Language)
        ->
   Streamlit UI (app.py)
        ->
 LangChain SQL Agent (src/agent.py)
        ->
 Groq LLaMA model <-> SQL Toolkit
        ->
 Final Answer + SQLite Database
```

Key components:

| Layer | Technology |
|---|---|
| LLM | Groq LLaMA-3.3-70b-versatile |
| Agent Framework | LangChain SQL Agent (`create_sql_agent`) |
| Database | SQLite (Chinook dataset) |
| Frontend | Streamlit |
| Schema Introspection | LangChain `SQLDatabase` |

## Why This Project Stands Out

- It is not a static portfolio mockup. The app queries a real relational dataset through an LLM-driven SQL agent.
- It shows full-stack product thinking: prompt design, data-tool integration, UI polish, and deployment readiness.
- It is easy to demo in interviews because the app includes guided prompt starters, exploration views, and a clear deployment story.

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/KakashiShiren/enterpriseiq.git
cd enterpriseiq
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

### 4. Run the app

```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/).
3. Click **Create app** and select this repository.
4. Set **Branch** to `main`.
5. Set **Main file path** to `app.py`.
6. Open **Advanced settings** and choose Python `3.12`.
7. Paste this into **Secrets**:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

8. Click **Deploy**.

The bundled SQLite database already lives in the repo, so no extra storage setup is needed for the first deployment.

## Fast Demo Flow

1. Ask an executive-style question like "Which country generates the most revenue?"
2. Follow with a customer or operations drill-down.
3. Use the Explore view to reinforce that the app is grounded in live data.
4. Export the session as a lightweight analyst briefing.

## Database

The app ships with the [Chinook](https://github.com/lerocha/chinook-database) music store dataset, including:

- Artists and albums
- Tracks with pricing and media type
- Customers across multiple countries
- Invoices and transaction history
- Employees with org hierarchy

To connect your own database, update the `db_path` in `src/agent.py`:

```python
db = SQLDatabase.from_uri("postgresql://user:pass@localhost/mydb")
```

## Example Queries

| Question | What it demonstrates |
|---|---|
| "Which country has the most customers?" | Aggregation + GROUP BY |
| "Top 5 customers by total spend?" | JOIN across Invoice + Customer |
| "Which employee supports the most customers?" | Self-referencing FK traversal |
| "Average invoice total by country?" | Multi-table aggregation |

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | required | Free key from [console.groq.com](https://console.groq.com) |
| `model` in `agent.py` | `llama-3.3-70b-versatile` | Swap to `llama-3.1-8b-instant` for faster responses |
| `verbose` in `agent.py` | `False` | Keeps deployment logs cleaner |

## Roadmap

- [ ] Support PostgreSQL / MySQL connections
- [ ] Add conversation memory across sessions
- [ ] Export query results to CSV
- [ ] Add vector search over unstructured documents (RAG)
- [ ] Multi-agent: one agent for SQL, one for document QA

## Screenshot

<img width="2878" height="1450" alt="Screenshot 2026-03-20 165426" src="https://github.com/user-attachments/assets/99f7aee4-7e41-4c5c-b78a-274df86c6dd9" />

## License

MIT
