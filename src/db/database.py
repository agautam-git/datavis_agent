import duckdb
import pandas as pd
from config import DB_PATH
from observability.logger import logger


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        logger.info(f"database connected: {db_path}")

    # ── Schema discovery ──────────────────────────────────────────
    def get_tables(self) -> list[str]:
        """Return list of all table names."""
        return (
            self.conn.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """)
            .fetchdf()["table_name"]
            .tolist()
        )

    def get_schema(self, table_name: str) -> str:
        """Return schema + row count + one sample row for a table."""
        cols = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        sample = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchdf()

        return (
            f"TABLE: {table_name} | rows: {count}\n"
            f"COLUMNS:\n{cols[['column_name', 'column_type']].to_string(index=False)}\n"
            f"SAMPLE:\n{sample.to_string(index=False)}"
        )

    # ── Query execution ───────────────────────────────────────────
    def execute(self, sql: str) -> pd.DataFrame:
        """Execute SQL and return DataFrame. Raises on error."""
        return self.conn.execute(sql).fetchdf()

    # ── Health check ──────────────────────────────────────────────
    def ping(self) -> bool:
        """Verify connection is alive."""
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def close(self):
        self.conn.close()
        logger.info("database connection closed")
