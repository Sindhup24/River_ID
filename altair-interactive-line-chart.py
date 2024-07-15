import pandas as pd
import solara
import altair as alt
from vega_datasets import data as vega_data

# Load the CSV file
file_path = '/Users/sinugp/Downloads/test_longtable_line.csv'  # Adjusted path for your uploaded file
data = pd.read_csv(file_path)

# Convert date column to datetime
data['date'] = pd.to_datetime(data['date'])

# Extract unique IDs from CSV
unique_ids = data['Id'].unique().tolist()

# Reactive variables
selected_id = solara.reactive(unique_ids[0])
selected_name = solara.reactive(None)
generate_trigger = solara.reactive(0)

# Function to generate line chart using Altair
def plot_line_chart(df, selected_id, selected_name):
    filtered_data = df[(df['Id'] == selected_id) & (df['Name'] == selected_name)]
    if filtered_data.empty:
        print("No data available for the selected Id and Name.")
        return None

    # Create the line chart
    lines = alt.Chart(filtered_data).mark_line().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('value:Q', title='Value', scale=alt.Scale(domain=(0, 30), nice=False), axis=alt.Axis(values=list(range(0, 31)))),
        color=alt.value('steelblue'),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('value:Q', title='Value')
        ]
    ).properties(
        width=800,  # adjust the width as needed
        height=400
    )

    # Add points for better tooltip visibility
    points = lines.mark_point().encode(
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('value:Q', title='Value')
        ]
    )

    # Define the horizontal overlay lines
    yrule1 = alt.Chart(pd.DataFrame({'value': [16]})).mark_rule(color="cyan", strokeWidth=2).encode(y='value:Q')
    yrule2 = alt.Chart(pd.DataFrame({'value': [22]})).mark_rule(color="magenta", strokeWidth=2, strokeDash=[5, 5]).encode(y='value:Q')
    yrule3 = alt.Chart(pd.DataFrame({'value': [28]})).mark_rule(color="red", strokeWidth=2).encode(y='value:Q')

    # Create a layered chart
    layer_chart = alt.layer(lines, points, yrule1, yrule2, yrule3).resolve_scale(
        y='shared'
    )

    return layer_chart

# Components
@solara.component
def View():
    if generate_trigger.value > 0 and selected_id.value and selected_name.value:
        chart = plot_line_chart(data, selected_id.value, selected_name.value)
        if chart:
            with solara.VBox() as main:
                solara.FigureAltair(chart)
            solara.Info("Chart has been updated.")
        else:
            solara.Warning("No data available for the selected Id and Name.")
    else:
        solara.Warning("Please select an Id and Name.")

@solara.component
def Controls():
    # Filter the names based on the selected Id
    filtered_names = data[data['Id'] == selected_id.value]['Name'].unique().tolist()
    if selected_name.value not in filtered_names:
        selected_name.value = filtered_names[0] if filtered_names else None

    solara.Select('Id', values=unique_ids, value=selected_id)
    solara.Select('Name', values=filtered_names, value=selected_name)
    
    def generate_chart():
        print(f"Generating chart for Id: {selected_id.value}, Name: {selected_name.value}")
        generate_trigger.value += 1

    solara.Button(label="Generate Chart", on_click=generate_chart, icon_name="mdi-chart-line")

@solara.component
def Page():
    with solara.Sidebar():
        Controls()
    View()

# Display the page
Page()
