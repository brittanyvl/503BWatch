# scripts/db_utils.py

import duckdb
import Scripts
from Scripts.data_loader import load_excel_files

DB_PATH = "Database/registry.duckdb"
DATA_DIR = "Data/FDA_503B"

def initialize_db():
    """Create DuckDB and registry table if not exists."""
    con = duckdb.connect(DB_PATH)
    #con.execute("INSTALL if not exists parquet; LOAD parquet;")  # future proofing
    con.close()

def ingest_new_data():
    """Inserts only new files into the DuckDB table."""
    con = duckdb.connect(DB_PATH)
    df = load_excel_files(DATA_DIR)

    if df.empty:
        con.close()
        return

    # Create table on first run with dynamic columns
    cols = df.columns
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS registry AS SELECT * FROM df LIMIT 0;
    """)

    # Avoid re-ingesting files already present
    existing_files = con.execute("SELECT DISTINCT source_file FROM registry").fetchall()
    existing_files = {row[0] for row in existing_files}
    new_df = df[~df["source_file"].isin(existing_files)]

    if not new_df.empty:
        con.execute("INSERT INTO registry SELECT * FROM new_df")

    con.close()

def get_all_data():
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM registry").df()
    con.close()
    return df
