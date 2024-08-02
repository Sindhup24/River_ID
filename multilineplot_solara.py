import pandas as pd
import solara
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import folium
from folium.plugins import TimestampedGeoJson

# Load the CSV file
file_path = 'fc_geoglows_random_20240429.csv'
data = pd.read_csv(file_path)

# Extract unique IDs
unique_ids = data['Id'].unique().tolist()

# Reactive variables
selected_id = solara.reactive(unique_ids[0])
selected_name = solara.reactive("")
generate_trigger = solara.reactive(0)

# Function to update name based on selected ID
def update_state_and_name(id):
    filtered_data = data[data['Id'] == id]
    if not filtered_data.empty:
        selected_name.value = filtered_data['Name'].iloc[0]
    else:
        selected_name.value = ""

# Function to filter data based on selected ID
def get_filtered_names(id):
    filtered_names = data[data['Id'] == id]['Name'].unique().tolist()
    if filtered_names:
        selected_name.value = filtered_names[0]
    return filtered_names

# Function to plot line chart using matplotlib
def plot_line_chart(df, id):
    filtered_data = df[df['Id'] == id]
    if filtered_data.empty:
        print("No data available for the selected ID.")
        return None

    # Ensure date is in datetime format
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])

    fig, ax1 = plt.subplots(figsize=(12, 8))
    ax2 = ax1.twinx()  # Instantiate a second y-axis that shares the same x-axis

    # Plot 51 lines for each ens_mem value with shortened legend labels
    for ens_mem in range(51):
        ens_mem_data = filtered_data[filtered_data['ens_mem'] == ens_mem]
        ax1.plot(ens_mem_data['date'], ens_mem_data['value'], linestyle='-', alpha=0.5, label=f'em {ens_mem}')

    ax1.set_xlabel('Date', fontweight='bold')
    ax1.set_ylabel('Value', fontweight='bold')
    ax1.set_title(f'Value over Time for ID {id}', fontweight='bold')
    ax1.grid(True)

    # Set major locator and formatter for x-axis
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

    plt.subplots_adjust(right=0.7, top=0.95, bottom=0.35)  # Adjust the top, right, and bottom of the graph

    # Add horizontal lines for ActiveThemeWarningLevelValues with different line styles and colors on secondary y-axis
    warning_levels = {
        'ActiveThemeWarningLevelValues_Normal Flow': ('-', 'green', 'ATWLV_Normal'),
        'ActiveThemeWarningLevelValues_2 years Return Period Flow': ('--', 'red', 'ATWLV_2 years'),
        'ActiveThemeWarningLevelValues_5 years Return Period Flow': ('-.', 'yellow', 'ATWLV_5 years'),
        'ActiveThemeWarningLevelValues_10 years Return Period Flow': (':', 'purple', 'ATWLV_10 years'),
        'ActiveThemeWarningLevelValues_15 years Return Period Flow': ((0, (3, 1, 1, 1)), 'orange', 'ATWLV_15 years'),
        'ActiveThemeWarningLevelValues_20 years Return Period Flow': ((0, (5, 1)), 'cyan', 'ATWLV_20 years')
    }

    for level, (linestyle, color, short_name) in warning_levels.items():
        if level in df.columns:
            value = df[level].unique()[0]
            ax2.axhline(y=value, color=color, linestyle=linestyle, label=short_name)

    # Adjust legend positioning to be horizontal at the bottom
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    combined_handles = handles1 + handles2
    combined_labels = labels1 + labels2

    # Ensure only unique labels are displayed
    unique_labels = {}
    for handle, label in zip(combined_handles, combined_labels):
        if label not in unique_labels:
            unique_labels[label] = handle

    fig.legend(unique_labels.values(), unique_labels.keys(), loc='lower center', ncol=8, bbox_to_anchor=(0.5, -0.15), borderaxespad=0., frameon=False)

    return fig

# Function to add legends to the map
def add_legend(m):
    legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; right: 50px; width: 150px; height: 150px; 
                 border:2px solid grey; z-index:9999; font-size:14px;
                 background-color:white;
                 ">
     &nbsp;<b>Legend</b><br>
     &nbsp;<i class="fa fa-circle" style="color:green"></i>&nbsp; value < 10<br>
     &nbsp;<i class="fa fa-circle" style="color:blue"></i>&nbsp; 10 <= value < 20<br>
     &nbsp;<i class="fa fa-circle" style="color:orange"></i>&nbsp; 20 <= value < 30<br>
     &nbsp;<i class="fa fa-circle" style="color:red"></i>&nbsp; value >= 30
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

# Function to plot map with timeline slider
def plot_map_with_slider(df, highlight_id=None):
    # Create a map centered around the mean coordinates with a specific zoom level
    m = folium.Map(location=[df['YCoordinate'].mean(), df['XCoordinate'].mean()], zoom_start=4)

    # Define a function to determine color based on value
    def get_color(value):
        if value < 10:
            return 'green'
        elif 10 <= value < 20:
            return 'blue'
        elif 20 <= value < 30:
            return 'orange'
        else:
            return 'red'

    # Define a function to determine radius based on value
    def get_radius(value):
        if value < 10:
            return 8
        else:
            return 10

    features = []
    for i, row in df.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['XCoordinate'], row['YCoordinate']]
            },
            'properties': {
                'time': row['date'],
                'popup': f"ID: {row['Id']} - {row['Name']}: ({row['XCoordinate']}, {row['YCoordinate']}) Value: {row['value']}",
                'icon': 'circle',
                'iconstyle': {
                    'color': get_color(row['value']),
                    'fillColor': get_color(row['value']),
                    'fillOpacity': 0.6,
                    'radius': get_radius(row['value'])
                }
            }
        }
        if highlight_id and row['Id'] == highlight_id:
            # Adding blinking effect for the highlighted ID
            feature['properties']['iconstyle']['className'] = 'blinking'
        features.append(feature)

    TimestampedGeoJson({
        'type': 'FeatureCollection',
        'features': features
    }, period='P1D', add_last_point=True, auto_play=False, loop=False).add_to(m)

    # Add legend to the map
    add_legend(m)

    # Add CSS for blinking effect
    blinking_css = '''
    <style>
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
    '''
    m.get_root().html.add_child(folium.Element(blinking_css))

    return m

# Components
@solara.component
def View():
    with solara.VBox() as main:
        if generate_trigger.value > 0 and selected_id.value:
            m = plot_map_with_slider(data, highlight_id=selected_id.value)
            fig = plot_line_chart(data, selected_id.value)
            if fig:
                solara.HTML(tag="div", unsafe_innerHTML=m._repr_html_())
                solara.FigureMatplotlib(fig)
                solara.Info("Map and chart have been updated.")
            else:
                solara.Warning("No data available for the selected ID.")
        else:
            m = plot_map_with_slider(data)
            solara.HTML(tag="div", unsafe_innerHTML=m._repr_html_())
            solara.Warning("Please select an ID.")
    return main

@solara.component
def Controls():
    # Update the options for the Name dropdown based on the selected ID
    update_state_and_name(selected_id.value)
    filtered_names = get_filtered_names(selected_id.value)

    solara.Select('ID', values=unique_ids, value=selected_id)
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
