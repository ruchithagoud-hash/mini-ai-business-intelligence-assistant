# Mini AI Business Intelligence Assistant

A simple AI-assisted Business Intelligence application that allows users to ask questions about sales data in plain English. It uses Python, Pandas, SQLite, FastAPI, and Streamlit to process sales data and present insights through answers, tables, and charts.

**No API key is required for the basic demo.**

## Architecture

```text
Sales CSV
   |
   v
db.py (Data validation, cleaning and loading)
   |
   v
SQLite Database (sales.db)
   |
   v
analytics.py (Question interpretation and approved SQL queries)
   |
   v
FastAPI (main.py)
   |
   v
Streamlit UI (app.py)
```

## Project Structure

| File | Description |
|---|---|
| `data/sales_data.csv` | Input sales dataset |
| `db.py` | Validates and cleans data, then loads it into SQLite |
| `analytics.py` | Interprets questions and executes approved SQL queries |
| `main.py` | FastAPI backend with health-check and question-answering endpoints |
| `app.py` | Streamlit interface for asking questions and viewing results |
| `test_app.py` | Automated tests using Pytest |
| `requirements.txt` | Python dependencies |
| `AI_DEVELOPMENT_NOTES.md` | Notes about the development process and AI assistance |

## Features

- Ask questions about sales data using natural language.
- Calculate total sales from completed transactions.
- Identify regions with the highest sales.
- Find top-selling products.
- Compare sales across product categories.
- Analyze monthly sales trends.
- Compare sales by sales channel.
- Display results through a chat-style interface, tables, and charts.
- Use a SQLite database for structured data storage.
- Apply SQL validation and read-only database access.
- Run automated tests to verify application behavior.

## How It Works

1. **Data preparation:** The application reads the sales CSV, validates fields, removes duplicate transaction IDs, and loads the cleaned records into SQLite.
2. **Question interpretation:** A rule-based system identifies supported questions. An optional OpenAI model can help select an intent when configured.
3. **Query execution:** Each supported intent maps to an approved, parameterized SQL query.
4. **Security:** Queries are restricted to approved read-only operations. Destructive SQL statements are rejected.
5. **Results:** The application calculates answers and displays the results in the Streamlit interface.

## Business Rules

- Sales are calculated as `Quantity × Unit_price − Discount_amount`.
- Only completed transactions are included in sales calculations.
- Missing or invalid quantities and unit prices are excluded rather than guessed.
- Missing discounts are treated as zero.
- Duplicate `Transaction_Id` records are removed, keeping the first occurrence.
- Unparseable dates are excluded from monthly analysis.
- The total-sales answer reports excluded records.

**Note:** The calculation assumes `Discount_amount` represents the total discount for a transaction. Confirm this interpretation against the dataset before using the results for business decisions.

## Technology Stack

- **Programming language:** Python
- **Data processing:** Pandas
- **Database:** SQLite
- **Backend API:** FastAPI
- **Frontend:** Streamlit
- **Validation:** Pydantic
- **Testing:** Pytest
- **Optional AI integration:** OpenAI API

## Prerequisites

- Python installed on your system
- PowerShell or another terminal
- Required Python packages listed in `requirements.txt`

## Installation and Setup

Open PowerShell in the project directory:

```powershell
cd C:\Users\Ruchitha\Downloads\ai_bi_assistant\ai_bi_assistant
```

Activate your existing virtual environment:

```powershell
& "C:\Users\Ruchitha\.venv\Scripts\Activate.ps1"
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

Prepare the database:

```powershell
python db.py
```

The script should report that 51 records were loaded.

## Running the Application

### 1. Start the FastAPI backend

Open the first PowerShell terminal, activate the virtual environment, and run:

```powershell
python -m uvicorn main:app --reload
```

API endpoints:

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Keep this terminal running.

### 2. Start the Streamlit interface

Open a second PowerShell terminal, activate the same virtual environment, and run:

```powershell
cd C:\Users\Ruchitha\Downloads\ai_bi_assistant\ai_bi_assistant
& "C:\Users\Ruchitha\.venv\Scripts\Activate.ps1"
python -m streamlit run app.py
```

Open http://localhost:8501 in your browser.

Keep both terminals running during the demo.

## Example Questions

- What are the total sales?
- Which region has the highest sales?
- What are the top-selling products?
- Show the top 3 products.
- Compare sales across product categories.
- Show monthly sales trends.
- Compare sales by sales channel.

## Testing

Run the automated test suite:

```powershell
python -m pytest -v
```

The tests cover sales calculations, regional and product analysis, category comparisons, monthly trends, unsupported questions, SQL safety, database access, data validation, and API behavior.

## Security Considerations

- Database queries use read-only SQLite connections.
- Only approved analysis queries are supported.
- Parameterized queries help prevent SQL injection.
- Destructive SQL operations are rejected.
- API keys should be stored in environment variables and must never be committed to GitHub.

## Limitations

- Only the supported analysis types are available.
- Simple keyword matching may not correctly interpret questions involving multiple topics.
- Currency is not assumed; amounts are displayed as plain numbers.
- Ambiguous dates may be interpreted according to Pandas date-parsing behavior.
- Running `python db.py` rebuilds the sales table.
- Results depend on the accuracy and meaning of the supplied dataset.

## Future Enhancements

- Support more natural-language questions.
- Add additional business KPIs and filtering options.
- Improve charts and dashboard customization.
- Add more datasets and configurable data sources.
- Expand automated testing and error handling.

## Author

Developed as a Mini AI Business Intelligence Assistant project for demonstrating data processing, SQL-based analytics, API development, and dashboard visualization.
