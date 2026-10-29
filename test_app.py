"""Automated tests. They build a small temporary database from a known CSV, so results
are repeatable and need no API key, internet access, or your real data/sales.db."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

import analytics
import db
import main

CSV_TEXT = """Transaction_Id,Order_date,Product,Category,Region,Sales_channel,Quantity,Unit_price,Discount_amount,Status
T1,2025-01-05,Laptop,Electronics,North,Online,2,500,50,Completed
T2,2025-01-20,Mouse,Accessories,South,Store,10,20,0,Completed
T3,2025-02-03,Laptop,Electronics,South,Online,1,500,0,completed
T4,2025-02-14,Keyboard,Accessories,North,Store,5,40,10,Completed
T5,2025-02-20,Monitor,Electronics,West,Online,3,150,0,Cancelled
T6,2025-03-01,Mouse,Accessories,West,Store,4,20,5,Completed
T7,2025-03-09,Monitor,Electronics,North,Online,2,,0,Completed
T8,2025-03-15,Laptop,Electronics,West,Online,1,500,100,Completed
T1,2025-01-05,Laptop,Electronics,North,Online,2,500,50,Completed
"""
# Hand-calculated expectations (completed, price known; sales = qty*price - discount):
#   T1=950 T2=200 T3=500 T4=190 T6=75 T8=400  -> total 2315 over 6 orders
#   T5 cancelled, T7 missing price, second T1 is a duplicate -> all excluded


@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    folder = tmp_path_factory.mktemp("bi")
    csv_file = folder / "sales.csv"
    csv_file.write_text(CSV_TEXT)
    path = folder / "sales.db"
    db.load_csv_to_db(csv_file, path)
    return path


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ----------------------------------------------------------------- loading
def test_csv_loading_cleans_and_deduplicates(tmp_path):
    csv_file = tmp_path / "s.csv"
    csv_file.write_text(CSV_TEXT)
    stats = db.load_csv_to_db(csv_file, tmp_path / "x.db")
    assert stats["rows_read"] == 9
    assert stats["duplicates_removed"] == 1
    assert stats["records_loaded"] == 8
    assert stats["missing_unit_price"] == 1  # not invented


def test_missing_required_column_is_rejected(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("Transaction_Id,Product\n1,A\n")
    with pytest.raises(ValueError, match="missing required columns"):
        db.load_csv_to_db(bad, tmp_path / "bad.db")


# ------------------------------------------------------------- the 5 required
def test_total_sales(db_path):
    result = analytics.total_sales(db_path)
    assert result["total_sales"] == 2315.00
    assert result["completed_orders"] == 6


def test_sales_by_region(db_path):
    rows = analytics.sales_by_region(db_path)
    assert [(r["region"], r["total_sales"]) for r in rows] == [
        ("North", 1140.0),
        ("South", 700.0),
        ("West", 475.0),
    ]


def test_top_products(db_path):
    rows = analytics.top_products(2, db_path)
    assert [(r["product"], r["total_sales"]) for r in rows] == [
        ("Laptop", 1850.0),
        ("Mouse", 275.0),
    ]


def test_monthly_sales(db_path):
    rows = analytics.monthly_sales(db_path)
    assert [(r["month"], r["total_sales"]) for r in rows] == [
        ("2025-01", 1150.0),
        ("2025-02", 690.0),
        ("2025-03", 475.0),
    ]


def test_unsupported_question_is_handled(db_path):
    result = analytics.answer_question("What is the weather in Paris?", db_path)
    assert result["supported"] is False
    assert result["rows"] == []
    assert "could not map" in result["answer"]


# ------------------------------------------------------------ more behaviour
def test_sales_by_category(db_path):
    rows = analytics.sales_by_category(db_path)
    assert [(r["category"], r["total_sales"]) for r in rows] == [
        ("Electronics", 1850.0),
        ("Accessories", 465.0),
    ]


def test_questions_map_to_database_answers(db_path):
    answer = analytics.answer_question("Which region has the highest sales?", db_path)
    assert answer["intent"] == "sales_by_region"
    assert answer["method"] == "rules"  # no API key needed
    assert answer["answer"].startswith("North has the highest sales at 1,140.00")
    assert "Top 1" in analytics.answer_question("top 1 product", db_path)["answer"]


def test_natural_phrasing_for_all_example_questions(db_path):
    expected = {
        "What are the total sales?": "total_sales",
        "Which region has the highest sales?": "sales_by_region",
        "What are the top-selling products?": "top_products",
        "Compare sales across product categories.": "sales_by_category",
        "Show monthly sales trends.": "monthly_sales",
    }
    for question, intent in expected.items():
        assert analytics.answer_question(question, db_path)["intent"] == intent


@pytest.mark.parametrize(
    "bad_sql",
    [
        "DROP TABLE sales",
        "DELETE FROM sales",
        "UPDATE sales SET quantity = 0",
        "INSERT INTO sales VALUES (1)",
        "ALTER TABLE sales ADD COLUMN x",
        "SELECT * FROM sales; DROP TABLE sales",
        "SELECT 1 -- comment",
    ],
)
def test_destructive_sql_is_rejected(bad_sql, db_path):
    with pytest.raises(analytics.UnsafeSQLError):
        analytics.run_query(bad_sql, db_path=db_path)


def test_destructive_question_is_refused_and_data_unchanged(db_path):
    result = analytics.answer_question("Please delete all sales records", db_path)
    assert result["supported"] is False
    assert analytics.total_sales(db_path)["total_sales"] == 2315.00


def test_connection_is_read_only(db_path):
    conn = db.get_readonly_connection(db_path)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM sales")
    conn.close()


def test_missing_database_raises_clear_error(tmp_path):
    with pytest.raises(db.DatabaseNotReady):
        analytics.total_sales(tmp_path / "nope.db")


# -------------------------------------------------------------------- API
@pytest.fixture()
def client(db_path):
    main.app.dependency_overrides[main.get_db_path] = lambda: db_path
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_api_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database_ready"] is True


def test_api_ask_returns_database_answer(client):
    resp = client.post("/ask", json={"question": "What are the total sales?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["supported"] is True
    assert body["rows"][0]["total_sales"] == 2315.0


def test_api_unsupported_and_blank_questions(client):
    unsupported = client.post("/ask", json={"question": "Tell me a joke"}).json()
    assert unsupported["supported"] is False
    assert client.post("/ask", json={"question": "   "}).status_code == 422
    assert client.post("/ask", json={}).status_code == 422


def test_api_reports_missing_database(tmp_path):
    main.app.dependency_overrides[main.get_db_path] = lambda: tmp_path / "missing.db"
    try:
        resp = TestClient(main.app).post("/ask", json={"question": "total sales"})
        assert resp.status_code == 503
    finally:
        main.app.dependency_overrides.clear()
