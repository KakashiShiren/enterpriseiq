# 🧠 EnterpriseIQ — SQL-Connected AI Analyst Chatbot

A LangChain-powered AI agent that connects to enterprise databases and answers natural language business questions — no SQL knowledge required.

![EnterpriseIQ Demo](https://via.placeholder.com/800x400?text=EnterpriseIQ+Demo)

## 🎯 What It Does

EnterpriseIQ lets business users ask questions like:
- *"Which country generates the most revenue?"*
- *"Who are our top 5 customers by total spend?"*
- *"How many albums does each artist have?"*

...and get back accurate, database-sourced answers — no SQL needed.

## 🏗️ Architecture

```
User Question (Natural Language)
        ↓
   Streamlit UI  (app.py)
        ↓
 LangChain SQL Agent  (src/agent.py)
        ↓
  OpenAI GPT-3.5/4   ←→   SQL Toolkit
        ↓                       ↓
   Final Answer           SQLite Database
                         (data/chinook.db)
```

**Key components:**
| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-3.5-turbo (swappable to GPT-4o) |
| Agent Framework | LangChain SQL Agent (`create_sql_agent`) |
| Database | SQLite (Chinook music store dataset) |
| Frontend | Streamlit |
| Schema Introspection | LangChain `SQLDatabase` utility |

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/enterpriseiq.git
cd enterpriseiq
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Enter your API key in the sidebar and start asking questions.

## 🗄️ Database

The app ships with a [Chinook](https://github.com/lerocha/chinook-database) music store dataset — a realistic enterprise schema with:

- **Artists** and **Albums**
- **Tracks** with pricing and media type
- **Customers** across 10+ countries
- **Invoices** and transaction history
- **Employees** with org hierarchy

To connect your own database, update the `db_path` in `src/agent.py`:
```python
db = SQLDatabase.from_uri("postgresql://user:pass@localhost/mydb")
```

## 💡 Example Queries

| Question | What it demonstrates |
|---|---|
| "Which country has the most customers?" | Aggregation + GROUP BY |
| "Top 5 customers by total spend?" | JOIN across Invoice + Customer |
| "Which employee supports the most customers?" | Self-referencing FK traversal |
| "Average invoice total by country?" | Multi-table aggregation |

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | required | Your OpenAI API key |
| `model` in `agent.py` | `gpt-3.5-turbo` | Swap to `gpt-4o` for better accuracy |
| `verbose` in `agent.py` | `True` | Set False to hide SQL chain-of-thought |

## 🗺️ Roadmap

- [ ] Support PostgreSQL / MySQL connections
- [ ] Add conversation memory across sessions
- [ ] Export query results to CSV
- [ ] Add vector search over unstructured documents (RAG)
- [ ] Multi-agent: one agent for SQL, one for document QA

## 📄 License

MIT
