# AI Development Notes

## AI tools used
| Tool | What it helped with |
|---|---|
| Claude (Anthropic) | Reviewed the project brief; generated `analytics.py`, `main.py`, `app.py`, `test_app.py`, `requirements.txt`, `README.md`, and these notes; helped correct `db.py`. |

  ## Decisions made
- **Approved-intent design instead of free SQL generation:** Each question is mapped to one of six predefined analysis types. This makes the application more controlled and easier to test. The optional LLM can select an approved intent but does not generate SQL.
- **Rule-based fallback:** The application can work without an API key and falls back to rule-based question interpretation if the LLM call fails.
- **SQL safety:** Queries are validated to reject multiple statements, SQL comments, and forbidden operations. The database is opened in read-only mode, and parameterized values are used where needed.
- **Sales formula:** `quantity * unit_price - discount_amount`. Only completed transactions with a known quantity and unit price are counted. The discount is treated as a total amount deducted from the transaction; this assumption should be checked against the dataset definition.
- **Missing data:** Missing or invalid quantities and unit prices are excluded from sales calculations rather than guessed. A missing discount is treated as zero.
- **Independent testing:** Automated tests use a small, hand-calculated test dataset so expected results can be checked independently of the real sales data.

## Issues encountered
- [Fill in any real errors you hit, e.g. venv activation, port in use, import errors, and how you fixed them.]
- Note: the generated code was tested by Claude against a synthetic 9-row CSV (24 tests passing, plus a
  live check of `/health`, `/ask` and the Streamlit page). It was **not** run against the real 51-row
  `sales_data.csv` by Claude; that must be done on your machine.

## How the code was reviewed and tested
1. **Data loading:** Ran `python db.py` and confirmed that 51 records were loaded from the sales CSV, with no duplicate transaction IDs or invalid dates reported.
2. **Automated tests:** Ran `python -m pytest -v` and confirmed that all 24 tests passed.
3. **Sales calculation verification:** Calculated the expected total from the official CSV using `quantity * unit_price - discount_amount`, counting only completed transactions with a valid quantity and unit price. The expected total is **1,439,200.00 across 49 valid completed transactions**. Two records are excluded: one returned transaction and one completed transaction with a missing unit price. Compare this expected result with the application's output.
4. **Application testing:** Started the FastAPI backend and Streamlit interface. The application was tested with the question "What are the total sales?" Additional supported questions should be tested, and their results should be compared with the displayed SQL queries.
5. **SQL safety:** The automated test suite includes checks for destructive SQL and read-only database access. Confirm that the application refuses the question "delete all sales" and that the database remains unchanged before recording this manual check as complete.

## Honest summary
AI generated most of the code; I reviewed it, ran it, verified numbers against the data, and can explain
each file.
AI tools helped generate most of the initial code for this project. I set up the project in my local environment, ran the application and automated tests, and worked through setup and Git issues. I am reviewing the code to understand the purpose of each file, how sales calculations are performed, how the API communicates with the UI, and how the application validates database queries. I will verify the results against the supplied sales dataset and document any remaining limitations before submission.

