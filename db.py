"""db.py - CSV loading and SQLite database management.

Run `python db.py` to (re)build data/sales.db from data/sales_data.csv.
The CSV is only ever READ; it is never modified or deleted.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = BASE_DIR / "data" / "sales_data.csv"
DEFAULT_DB_PATH = BASE_DIR / "data" / "sales.db"
TABLE_NAME = "sales"

REQUIRED_COLUMNS = [
    "Transaction_Id",
    "Order_date",
    "Product",
    "Category",
    "Region",
    "Sales_channel",
    "Quantity",
    "Unit_price",
    "Discount_amount",
    "Status",
]


class DatabaseNotReady(RuntimeError):
    """Raised when the SQLite database or its `sales` table is missing."""


def _clean_text(series: pd.Series, title_case: bool) -> pd.Series:
    """Trim whitespace; blank/missing values become 'Unknown' (a label, not a number)."""
    s = series.astype("object").where(series.notna(), None)
    s = s.map(lambda v: " ".join(str(v).split()) if v is not None else "")
    if title_case:
        s = s.str.title()
    return s.replace("", "Unknown")


def load_csv(csv_path: Path | str = DEFAULT_CSV_PATH) -> tuple[pd.DataFrame, dict]:
    """Read, validate and clean the CSV. Returns (clean_dataframe, stats)."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    # Case-insensitive column matching, then rename to the canonical names.
    lookup = {c.strip().lower(): c for c in df.columns}
    missing = [c for c in REQUIRED_COLUMNS if c.lower() not in lookup]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    df = df.rename(columns={lookup[c.lower()]: c for c in REQUIRED_COLUMNS})
    df = df[REQUIRED_COLUMNS].copy()
    rows_read = len(df)

    # Text columns
    df["Transaction_Id"] = _clean_text(df["Transaction_Id"], title_case=False)
    df["Product"] = _clean_text(df["Product"], title_case=False)
    for col in ("Category", "Region", "Sales_channel", "Status"):
        df[col] = _clean_text(df[col], title_case=True)

    # Numeric columns: invalid values become NULL. Nothing is invented.
    for col in ("Quantity", "Unit_price", "Discount_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # A missing discount means "no discount recorded"; missing price/quantity stay NULL.
    df["Discount_amount"] = df["Discount_amount"].fillna(0)

    # Dates -> ISO text (YYYY-MM-DD). Unparseable dates become NULL.
    try:
        dates = pd.to_datetime(df["Order_date"], errors="coerce", format="mixed")
    except (TypeError, ValueError):  # older pandas without format="mixed"
        dates = pd.to_datetime(df["Order_date"], errors="coerce")
    df["Order_date"] = dates.dt.strftime("%Y-%m-%d").astype("object")
    df["Order_date"] = df["Order_date"].where(dates.notna(), None)

    # Duplicate transaction ids: keep the first occurrence.
    before = len(df)
    df = df.drop_duplicates(subset="Transaction_Id", keep="first")
    duplicates_removed = before - len(df)

    df.columns = [c.lower() for c in df.columns]
    stats = {
        "rows_read": rows_read,
        "duplicates_removed": duplicates_removed,
        "records_loaded": len(df),
        "missing_unit_price": int(df["unit_price"].isna().sum()),
        "missing_quantity": int(df["quantity"].isna().sum()),
        "invalid_dates": int(df["order_date"].isna().sum()),
    }
    return df, stats


def load_csv_to_db(
    csv_path: Path | str = DEFAULT_CSV_PATH,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> dict:
    """Load the CSV into the SQLite `sales` table (replacing it). Returns load stats."""
    df, stats = load_csv(csv_path)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()
    return stats


def get_readonly_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open the database in read-only mode: any write attempt raises an error."""
    db_path = Path(db_path).resolve()
    if not db_path.exists():
        raise DatabaseNotReady(
            f"Database not found at {db_path}. Run `python db.py` to create it."
        )
    return sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)


if __name__ == "__main__":
    try:
        result = load_csv_to_db()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    print(f"Loaded records: {result['records_loaded']}")
    for key, value in result.items():
        if key != "records_loaded":
            print(f"  {key}: {value}")
