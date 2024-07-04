import pandas as pd
import folium
from folium.plugins import MarkerCluster
import plotly.graph_objects as go
from datetime import datetime

# Load the uploaded CSV files
forecast_df = pd.read_csv('/Users/sinugp/Downloads/forecast_data.csv')
coordinates_df = pd.read_csv('/Users/sinugp/Downloads/altair_points_with_river_numbers.csv')

# Ensure Date column is in the correct format
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'], format='%Y%m%d%H')

# Filter Data: Select the first 5 RiverNumbers
unique_river_numbers = coordinates_df['RiverNumber'].unique()[:5]
filtered_coordinates_df = coordinates_df[coordinates_df['RiverNumber'].isin(unique_river_numbers)]
filtered_forecast_df = forecast_df[forecast_df['RiverNumber'].isin(unique_river_numbers)]

# Function to create a Plotly graph and convert it to HTML
def create_plotly_graph(river_number):
    # Filter forecast data for the specific RiverNumber
    river_data = filtered_forecast_df[filtered_forecast_df['RiverNumber'] == river_number]
    
    # Create a line plot of the forecast data
    fig = go.Figure()
    for col in river_data.columns[:-2]:  # Exclude RiverNumber and Date columns
        fig.add_trace(go.Scatter(x=river_data['Date'], y=river_data[col], mode='lines', name=col))
    
    # Customize the layout
    fig.update_layout(title=f"Forecast for RiverNumber {river_number}", xaxis_title="Date", yaxis_title="Forecast")
    
    # Convert the plot to HTML
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return graph_html

# Initialize the map with MarkerCluster
m = folium.Map(location=[filtered_coordinates_df['YCoordinate'].mean(), filtered_coordinates_df['XCoordinate'].mean()], zoom_start=6)
marker_cluster = MarkerCluster().add_to(m)

# Add markers to the map with click event to display the forecast plot
for idx, row in filtered_coordinates_df.iterrows():
    iframe = folium.IFrame(html=create_plotly_graph(row['RiverNumber']), width=700, height=500)
    popup = folium.Popup(iframe, max_width=700)
    
    folium.Marker(
        location=[row['YCoordinate'], row['XCoordinate']],
        popup=popup,
        tooltip=row['RiverNumber']
    ).add_to(marker_cluster)

# Save the map to an HTML file
map_file_path = '/Users/sinugp/Downloads/interactive_river_map_fixed.html'
m.save(map_file_path)