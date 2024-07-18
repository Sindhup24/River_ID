import pandas as pd
import solara
import matplotlib.pyplot as plt
import numpy as np
import folium
from folium.plugins import MarkerCluster

# Load the CSV files
file_path = '/Users/sinugp/Downloads/solara-dropdown.csv'
id_file_path = '/Users/sinugp/Downloads/test_longtable_line.csv'
data = pd.read_csv(file_path)
id_data = pd.read_csv(id_file_path)

# Extract unique states and IDs
unique_states = data['state'].unique().tolist()
unique_ids = id_data['Id'].unique().tolist()

# Merge the dataframes to ensure we have both IDs and other relevant data
merged_data = pd.merge(data, id_data, on='Id', how='inner')

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
    filtered_data = df[df['Name_x'] == name].drop_duplicates(subset=['XCoordinate_x', 'YCoordinate_x'])
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

# Function to plot map using folium with blinking marker
def plot_map(df, highlight_name=None):
    unique_locations = df.drop_duplicates(subset=['XCoordinate_x', 'YCoordinate_x'])
    # Create a map centered around the mean coordinates with a specific zoom level
    m = folium.Map(location=[0, 20], zoom_start=4)
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers to the map
    for i, row in unique_locations.iterrows():
        if highlight_name and row['Name_x'] == highlight_name:
            folium.Marker(
                location=[row['YCoordinate_x'], row['XCoordinate_x']],
                popup=f"ID: {row['Id']} - {row['Name_x']}: ({row['XCoordinate_x']}, {row['YCoordinate_x']})",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        else:
            folium.Marker(
                location=[row['YCoordinate_x'], row['XCoordinate_x']],
                popup=f"ID: {row['Id']} - {row['Name_x']}: ({row['XCoordinate_x']}, {row['YCoordinate_x']})"
            ).add_to(marker_cluster)
    
    # Add blinking effect using custom JavaScript
    if highlight_name:
        highlighted_row = unique_locations[unique_locations['Name_x'] == highlight_name].iloc[0]
        blinking_marker = folium.Marker(
            location=[highlighted_row['YCoordinate_x'], highlighted_row['XCoordinate_x']],
            popup=f"ID: {highlighted_row['Id']} - {highlighted_row['Name_x']}: ({highlighted_row['XCoordinate_x']}, {highlighted_row['YCoordinate_x']})",
            icon=folium.DivIcon(html=f"""
                <div style="background-color:rgba(255,0,0,0.5); width:24px; height:24px; border-radius:50%; animation: blinker 1s linear infinite;"></div>
                <style>
                @keyframes blinker {{
                    50% {{ opacity: 0; }}
                }}
                </style>
            """)
        )
        blinking_marker.add_to(m)
    
    # Set explicit bounds for Africa
    africa_bounds = [[-35, -20], [37, 55]]
    m.fit_bounds(africa_bounds)

    return m

# Components
@solara.component
def View():
    with solara.VBox() as main:
        if generate_trigger.value > 0 and selected_name.value:
            m = plot_map(merged_data, highlight_name=selected_name.value)
            fig = plot_bar_chart(merged_data, selected_name.value)
            if fig:
                solara.HTML(tag="div", unsafe_innerHTML=m._repr_html_())
                solara.FigureMatplotlib(fig)
                solara.Info("Map and chart have been updated.")
            else:
                solara.Warning("No data available for the selected state and name.")
        else:
            m = plot_map(merged_data)
            solara.HTML(tag="div", unsafe_innerHTML=m._repr_html_())
            solara.Warning("Please select a state and a name.")
    return main

@solara.component
def Controls():
    # Update the options for the Name dropdown based on the selected state and ID
    update_state_and_name(selected_id.value)
    filtered_names = get_filtered_names(selected_state.value, selected_id.value)
    
    solara.Select('ID', values=unique_ids, value=selected_id)
    solara.Select('State', values=unique_states, value=selected_state)
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
