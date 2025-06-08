"""
Original analysis.py

from Scripts import data_loader
import altair as alt

data = data_loader.load_data()

# Create Data for Metrics at top of the home page
metric_total_pharmacies = len(data['Facility'])

# Round the percentage metrics to 2 decimal places
metric_percent_fda_uninspected = round((data['no_fda_inspections'].mean()) * 100, 2)
metric_percent_483s_issued = round((data['form_483_issued'].mean()) * 100, 2)
metric_percent_recalls_conducted = round((data['fda_recall_conducted'].mean()) * 100, 2)
metric_percent_intend_sterile = round((data['intends_to_compound_sterile'].mean()) * 100, 2)


# Analyze post_inspection_actions
inspections = data.copy()
inspections['post_inspection_action'] = inspections['post_inspection_action'].fillna('No Action')
# Group by the 'post_inspection_action' and count occurrences
action_counts = inspections['post_inspection_action'].value_counts().reset_index()
action_counts.columns = ['Action', 'Count']

# Create a horizontal bar chart using Altair
chart_post_inspection_actions = alt.Chart(action_counts).mark_bar().encode(
    y=alt.Y('Action:N', sort='-x'),  # Sort by count (descending)
    x='Count:Q',
    color='Action:N'
).properties(
    title='Post Inspection Action Distribution'
)

"""

import pandas as pd

def identify_new_and_removed_facilities(df: pd.DataFrame):
    df["week"] = df["source_file"].str.extract(r'(\d{4}-\d{2}-\d{2})')  # Extract date from file
    weeks = sorted(df["week"].unique())

    if len(weeks) < 2:
        return pd.DataFrame(), pd.DataFrame()  # Not enough data to compare

    latest_week = weeks[-1]
    prev_week = weeks[-2]

    current = df[df["week"] == latest_week]
    previous = df[df["week"] == prev_week]

    current_names = set(current["facility_name"])
    previous_names = set(previous["facility_name"])

    new = current[current["facility_name"].isin(current_names - previous_names)]
    removed = previous[previous["facility_name"].isin(previous_names - current_names)]

    return new, removed
