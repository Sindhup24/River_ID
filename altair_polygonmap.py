import pandas as pd
import solara
import matplotlib.pyplot as plt
import numpy as np
import altair as alt
from vega_datasets import data

# Load the CSV files
file_path = '/Users/sinugp/Downloads/solara-dropdown.csv'
id_file_path = '/Users/sinugp/Downloads/test_longtable_line.csv'
data_df = pd.read_csv(file_path)
id_data = pd.read_csv(id_file_path)

# Extract unique states and IDs from the ID file
unique_ids = id_data['Id'].unique().tolist()

# Merge the dataframes to ensure we have both IDs and other relevant data
merged_data = pd.merge(data_df, id_data, on='Id', how='inner')

# Filter to ensure coordinates fall within Africa's bounding box
# Approximate bounding box for Africa: latitudes [-35, 37], longitudes [-20, 55]
africa_bbox = merged_data[
    (merged_data['YCoordinate_x'] >= -35) & (merged_data['YCoordinate_x'] <= 37) &
    (merged_data['XCoordinate_x'] >= -20) & (merged_data['XCoordinate_x'] <= 55)
]

# Group data by coordinates and aggregate
grouped_data = africa_bbox.groupby(['XCoordinate_x', 'YCoordinate_x']).agg({
    'Id': lambda x: ', '.join(map(str, x)),
    'value': 'mean',
    'Name_x': lambda x: ', '.join(x),
    'state': 'first'  # Assuming 'state' is present in the dataset
}).reset_index().rename(columns={'Id': 'IDs', 'value': 'avg_value'})

# Bin the avg_value to combine points based on color
grouped_data['value_bin'] = pd.cut(grouped_data['avg_value'], bins=[0, 5, 10, 15, 20, 25], labels=['0-5', '5-10', '10-15', '15-20', '20-25'])

# Reactive variables
selected_id = solara.reactive(unique_ids[0])
selected_state = solara.reactive("")
selected_name = solara.reactive("")
generate_trigger = solara.reactive(0)

# Function to update state and name based on selected ID
def update_state_and_name(id):
    filtered_data = merged_data[merged_data['Id'] == id]
    if not filtered_data.empty:
        selected_state.value = filtered_data['state'].iloc[0]
        selected_name.value = filtered_data['Name_x'].iloc[0]
    else:
        selected_state.value = ""
        selected_name.value = ""

# Function to filter data based on selected state and ID
def get_filtered_names(state, id):
    filtered_names = merged_data[(merged_data['state'] == state) & (merged_data['Id'] == id)]['Name_x'].unique().tolist()
    if filtered_names:
        selected_name.value = filtered_names[0]
    return filtered_names

# Function to plot bar chart using matplotlib
def plot_bar_chart(df, name):
    filtered_data = df[df['Name_x'].str.contains(name)].drop_duplicates(subset=['XCoordinate_x', 'YCoordinate_x'])
    if filtered_data.empty:
        print("No data available for the selected filters.")
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    width = 0.3  # Bar width
    x = np.arange(len(filtered_data))  # the label locations
    ax.bar(x - width/2, filtered_data['XCoordinate_x'], width, label='XCoordinate', color='blue')
    ax.bar(x + width/2, filtered_data['YCoordinate_x'], width, label='YCoordinate', color='orange', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(filtered_data['Name_x'], rotation=45, ha='right')
    ax.set_xlabel('Name', fontweight='bold')
    ax.set_ylabel('Coordinate Value', fontweight='bold')
    ax.set_title(f'Bar Chart for {name}', fontweight='bold')
    ax.legend(loc='upper right')
    
    # Add data labels
    for i in range(len(filtered_data)):
        ax.text(i - width/2, filtered_data['XCoordinate_x'].iloc[i] / 2, str(filtered_data['XCoordinate_x'].iloc[i]), ha='center', va='bottom', color='white')
        ax.text(i + width/2, filtered_data['YCoordinate_x'].iloc[i] / 2, str(filtered_data['YCoordinate_x'].iloc[i]), ha='center', va='bottom', color='black')
    
    fig.tight_layout()  # Adjust layout to make room for rotated x-tick labels
    return fig

# Function to plot map using Altair
def plot_map(df, highlight_id=None):
    world = alt.topo_feature(data.world_110m.url, 'countries')

    # Create base map
    map_chart = alt.Chart(world).mark_geoshape(
        stroke='white',
        strokeWidth=0.5
    ).encode(
        color=alt.value('lightgray'),
        tooltip=[alt.Tooltip('id:Q', title='Country')]
    ).properties(
        width=800,
        height=600
    ).project(
        type='mercator',
        center=[20, 0],  # Center on Africa
        scale=300  # Adjust scale to show entire Africa
    )

    # Data points layer
    points = alt.Chart(df).mark_circle().encode(
        longitude='XCoordinate_x:Q',
        latitude='YCoordinate_x:Q',
        size=alt.Size('avg_value:Q', title='Average Value', scale=alt.Scale(range=[50, 500])),
        color=alt.Color('value_bin:N', scale=alt.Scale(domain=['0-5', '5-10', '10-15', '15-20', '20-25'], range=['purple', 'blue', 'green', 'yellow', 'red'])),
        tooltip=[
            alt.Tooltip('XCoordinate_x:Q', title='Longitude'),
            alt.Tooltip('YCoordinate_x:Q', title='Latitude'),
            alt.Tooltip('IDs:N', title='IDs'),
            alt.Tooltip('avg_value:Q', title='Average Value'),
            alt.Tooltip('Name_x:N', title='Names')
        ]
    )

    # Highlighted points layer if an ID is provided
    if highlight_id:
        highlight = df[df['IDs'].str.contains(str(highlight_id))]
        highlight_chart = alt.Chart(highlight).mark_circle(
            size=500
        ).encode(
            longitude='XCoordinate_x:Q',
            latitude='YCoordinate_x:Q',
            color=alt.Color('value_bin:N', scale=alt.Scale(domain=['0-5', '5-10', '10-15', '15-20', '20-25'], range=['purple', 'blue', 'green', 'yellow', 'red'])),
            tooltip=[
                alt.Tooltip('XCoordinate_x:Q', title='Longitude'),
                alt.Tooltip('YCoordinate_x:Q', title='Latitude'),
                alt.Tooltip('IDs:N', title='IDs'),
                alt.Tooltip('avg_value:Q', title='Average Value'),
                alt.Tooltip('Name_x:N', title='Names')
            ]
        )
        map_chart = map_chart + points + highlight_chart
    else:
        map_chart = map_chart + points
    
    return map_chart

# Components
@solara.component
def View():
    with solara.VBox() as main:
        if generate_trigger.value > 0 and selected_name.value:
            map_chart = plot_map(grouped_data, highlight_id=selected_id.value)
            fig = plot_bar_chart(africa_bbox, selected_name.value)
            if fig:
                solara.AltairChart(chart=map_chart)
                solara.FigureMatplotlib(fig)
                solara.Info("Map and chart have been updated.")
            else:
                solara.Warning("No data available for the selected state and name.")
        else:
            map_chart = plot_map(grouped_data)
            solara.AltairChart(chart=map_chart)
            solara.Warning("Please select a state and a name.")
    return main

@solara.component
def Controls():
    # Update the options for the Name dropdown based on the selected state and ID
    update_state_and_name(selected_id.value)
    filtered_names = get_filtered_names(selected_state.value, selected_id.value)
    
    solara.Select('ID', values=unique_ids, value=selected_id)
    solara.Select('State', values=data_df['state'].unique().tolist(), value=selected_state)
    solara.Select('Name', values=filtered_names, value=selected_name)
    
    def generate_chart():
        generate_trigger.value += 1

    solara.Button(label="Generate Chart", on_click=generate_chart, icon_name="mdi-chart-bar")

@solara.component
def Page():
    with solara.Sidebar():
        Controls()
    View()

# Display the page
Page()
