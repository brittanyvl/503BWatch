"""
Original Data Loader Script
import pandas as pd


def load_data():
    # Read in current raw file

    data = pd.read_excel("Data/FDA_503B/503B_cleaned_2025-06-07.xlsx")

    # Fix the N/As that are still escaping the main scrape
    data['post_inspection_action'] = data['post_inspection_action'].str.strip()
    # Clean file
    #data = FDA.clean_fda_503b_list(data)

    #data.columns = data.columns.str.strip('*').str.strip()

    # Return clean file
    return data
"""
# scripts/data_loader.py

# scripts/data_loader.py

import pandas as pd
import os
import re

def parse_scanned_date_from_filename(filename: str) -> str:
    """Extracts YYYY-MM-DD from filename."""
    match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
    return match.group() if match else "unknown"

def convert_all_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Converts all columns with 'date' in the name to ISO format."""
    for col in df.columns:
        if "date" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            except:
                pass
    return df

def load_excel_files(directory: str) -> pd.DataFrame:
    """Load Excel files with no column normalization. Only add scanned_date."""
    all_data = []
    for file in os.listdir(directory):
        if file.endswith(".xlsx"):
            path = os.path.join(directory, file)
            scanned_date = parse_scanned_date_from_filename(file)
            try:
                df = pd.read_excel(path)
                df['post_inspection_action'] = df['post_inspection_action'].str.strip()
                df = convert_all_dates(df)
                df["scanned_date"] = scanned_date
                df["source_file"] = file
                all_data.append(df)
            except Exception as e:
                print(f"⚠️ Failed to load {file}: {e}")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

