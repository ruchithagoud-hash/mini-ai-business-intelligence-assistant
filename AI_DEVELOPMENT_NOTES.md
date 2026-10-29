# AI Development Notes

## AI tools used
| Tool | What it helped with |
|---|---|
| Claude (Anthropic) | Reviewed the project brief; wrote `analytics.py`, `main.py`, `app.py`, `test_app.py`, `requirements.txt`, `README.md` and these notes; produced a corrected `db.py` |
| [Fill in: tool that supplied the starter `analytics.py` / `db.py`] | [Fill in: what it produced] |

## Decisions made
- **Approved-intent design instead of free SQL generation.** The question is mapped to one of six fixed
  queries. This is safer and testable. The optional LLM can only choose an intent name.
- **Rule-based fallback** so the app works with no API key, and also when an LLM call fails.
- **Defence in depth for SQL:** validator (single SELECT, forbidden keywords, no comments) plus a
  read-only SQLite connection plus parameterised values (`LIMIT ?`).
- **Sales formula:** `quantity * unit_price - discount_amount`, Completed only. Discount is assumed to be a
  total amount per transaction. This is an assumption to confirm against the dataset's definition.
- **Missing data is excluded, not invented** (missing price/quantity); missing discount = 0.
- **Tests use a small hand-calculated CSV** so expected numbers are verifiable and independent of the real data.

## Issues encountered
- [Fill in any real errors you hit, e.g. venv activation, port in use, import errors, and how you fixed them.]
- Note: the generated code was tested by Claude against a synthetic 9-row CSV (24 tests passing, plus a
  live check of `/health`, `/ask` and the Streamlit page). It was **not** run against the real 51-row
  `sales_data.csv` by Claude; that must be done on your machine.

## How the code was reviewed and tested
1. Ran `python db.py` and confirmed the loaded record count matches the CSV (51).
2. Ran `python -m pytest -v` (all tests pass).
3. Hand-checked at least one real answer: e.g. open the CSV (or a SQLite viewer), filter Completed rows, compute
   `sum(quantity*unit_price - discount_amount)` and compare it with the app's total. [Record your result here.]
4. Started `uvicorn main:app` and `streamlit run app.py`, asked all five example questions, and compared
   the tables with the SQL shown under "How was this calculated?".
5. Confirmed that "delete all sales" is refused and that the data is unchanged.

## Honest summary
AI generated most of the code; I reviewed it, ran it, verified numbers against the data, and can explain
each file. [Edit this paragraph so it reflects what you actually did.]
