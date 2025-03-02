import pandas as pd
import openpyxl
import FDA

def load_data():
    # Read in current raw file
    data = pd.read_excel("Data/FDA_503B/503B_2025-03-01.xlsx", dtype=str)
    # Clean file
    data = FDA.clean_fda_503b_list(data)

    # Return clean file
    return data
