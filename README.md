# Mini AI Business Intelligence Assistant

Ask questions about a sales dataset in plain English. Each answer is calculated from a
SQLite database using approved SQL queries. **No API key is needed** for the basic demo.

## Architecture

```
Streamlit UI (app.py) --HTTP--> FastAPI (main.py) --> analytics.py --> SQLite (read-only)
                                                          ^
data/sales_data.csv --> db.py (validate, clean, load) ----+  data/sales.db
```

| File | Role |
|---|---|
| `db.py` | Validates/cleans the CSV (Pandas) and writes the `sales` table; opens read-only connections |
| `analytics.py` | Interprets the question, picks an **approved** query, runs it, writes the answer |
| `main.py` | FastAPI: `GET /health`, `POST /ask` (Pydantic models) |
| `app.py` | Streamlit chat-style UI with examples, tables and charts |
| `test_app.py` | Pytest suite (uses a small temporary database, not your real data) |

### How questions are answered
1. **Interpret**: rule-based keywords by default. If `OPENAI_API_KEY` is set, an LLM may pick the
   intent instead, but only from a fixed list. It never writes SQL. Any LLM failure falls back to the rules.
2. **Query**: each intent maps to a fixed, parameterised SQL template.
3. **Safety**: SQL is validated (single `SELECT` only; DROP/DELETE/UPDATE/INSERT/ALTER etc. rejected)
   and run on a read-only SQLite connection (`mode=ro`). Questions containing destructive words or raw SQL are refused.
4. **Answer**: the text is built from the returned rows, and the SQL is shown in the UI.

### Business rules
- **Sales = Quantity x Unit_price - Discount_amount**, counting only `Completed` transactions (case-insensitive).
- `Discount_amount` is treated as a **total amount off the whole transaction** (not per unit, not a percentage).
  Check this against your data's meaning; if it is per unit, change `SALES_EXPR` in `analytics.py`.
- Rows with a missing/invalid quantity or unit price are **excluded, never guessed**. A missing discount counts as 0.
- Duplicate `Transaction_Id` rows are dropped (first kept). Unparseable dates become NULL (left out of monthly results).
- The total-sales answer reports how many records were excluded.

## Setup (Windows PowerShell)

```powershell
cd C:\Users\Ruchitha\Downloads\AI_BI_Assistant_Starter\ai_bi_assistant
.\.venv\Scripts\Activate.ps1        # or your venv's activate script
pip install -r requirements.txt
python db.py                        # builds data\sales.db, prints "Loaded records: 51"
```

## Run

Terminal 1 (API):
```powershell
uvicorn main:app --reload
```
Check: http://127.0.0.1:8000/health and interactive docs at http://127.0.0.1:8000/docs

Terminal 2 (UI):
```powershell
streamlit run app.py
```
If the API is not running, the UI falls back to the local engine and says so.

Quick API test:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question":"What are the total sales?"}'
```

### Optional LLM
```powershell
$env:OPENAI_API_KEY = "your-key"       # never commit keys
$env:OPENAI_MODEL = "gpt-4o-mini"      # optional
```

## Example questions
- What are the total sales?
- Which region has the highest sales?
- What are the top-selling products? (or "top 3 products")
- Compare sales across product categories.
- Show monthly sales trends.
- Compare sales by sales channel.

## Testing
```powershell
python -m pytest -v
```
Tests cover totals, region, products, categories, months, unsupported questions, SQL-injection/destructive
SQL, read-only access, CSV validation and the API. They need no internet or API key.

## Limitations
- Only the six approved analyses are supported; other questions get a clear "unsupported" reply.
- Keyword matching is simple (a question mixing several topics maps to the first match).
- Currency is not assumed; amounts are shown as plain numbers.
- Dates in ambiguous formats (e.g. 03/04/2025) are parsed month-first by Pandas.
- `python db.py` replaces the `sales` table each time it runs.
