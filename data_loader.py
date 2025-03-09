import pandas as pd
import openpyxl
import FDA

def load_data():
    # Read in current raw file

    data = pd.read_excel(r"\Data\FDA_503B\503B_cleaned_2025-03-08.xlsx")
    # Clean file
    #data = FDA.clean_fda_503b_list(data)

    #data.columns = data.columns.str.strip('*').str.strip()

    # Return clean file
    return data
