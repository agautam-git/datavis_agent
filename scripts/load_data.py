# scripts/load_data.py
import sys
import os

# ── resolve paths relative to project root ────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import duckdb
from pathlib import Path
from config import DB_PATH

def load_csvs_to_duckdb(folder_path: str, db_path: str = DB_PATH):
    folder   = Path(folder_path)
    db_path  = Path(db_path)

    # resolve relative paths from project root
    if not folder.is_absolute():
        folder = Path(PROJECT_ROOT) / folder
    if not db_path.is_absolute():
        db_path = Path(PROJECT_ROOT) / db_path

    print(f"loading CSVs from: {folder}")
    print(f"writing to DB:     {db_path}")

    conn   = duckdb.connect(str(db_path))
    loaded = []
    failed = []

    for csv_file in sorted(folder.glob("*.csv")):
        table_name = csv_file.stem
        try:
            conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{csv_file}')
            """)
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"✅ {table_name} ({count} rows)")
            loaded.append(table_name)
        except Exception as e:
            print(f"❌ {table_name}: {e}")
            failed.append(table_name)

    conn.close()
    print(f"\nloaded: {len(loaded)} tables")
    if failed:
        print(f"failed: {failed}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "data/AdventureWorks"
    load_csvs_to_duckdb(folder)