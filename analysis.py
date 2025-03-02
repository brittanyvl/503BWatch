import data_loader
import altair as alt

data = data_loader.load_data()

# Create Data for Metrics at top of the home page
metric_total_pharmacies = len(data)

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


