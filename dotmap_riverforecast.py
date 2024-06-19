import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import ast

# Load the CSV file
file_path = '/Users/sinugp/Downloads/merged_river_data.csv'
df = pd.read_csv(file_path)

# Convert ForecastData from string representation of lists to actual lists
df['ForecastData'] = df['ForecastData'].apply(ast.literal_eval)

# Determine the bounds of the map based on the river points
min_lat, max_lat = df['XCoordinate'].min(), df['XCoordinate'].max()
min_lon, max_lon = df['YCoordinate'].min(), df['YCoordinate'].max()

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Graph(
        id='river-points',
        figure={
            'data': [
                go.Scattergeo(
                    lon=df['YCoordinate'],
                    lat=df['XCoordinate'],
                    mode='markers',
                    marker=dict(size=10),
                    text=[f'River {num}' for num in df['RiverNumber']],
                    hoverinfo='text',
                    name='Rivers'
                )
            ],
            'layout': go.Layout(
                title='Interactive River Flow Forecast',
                geo=dict(
                    scope='world',
                    projection=dict(type='equirectangular'),
                    showland=True,
                    lataxis=dict(range=[min_lat - 1, max_lat + 1]),  # Set latitude axis range
                    lonaxis=dict(range=[min_lon - 1, max_lon + 1])   # Set longitude axis range
                ),
            )
        }
    ),
    dcc.Graph(id='forecast-data')
])

# Callback to update the forecast data plot based on the selected river point
@app.callback(
    Output('forecast-data', 'figure'),
    [Input('river-points', 'clickData')]
)
def display_forecast_data(clickData):
    if clickData is None:
        return go.Figure()  # Return an empty figure if no point is clicked

    # Extract latitude and longitude from the clickData
    lon = clickData['points'][0]['lon']
    lat = clickData['points'][0]['lat']
    
    # Find the corresponding RiverNumber
    river_number = df[(df['YCoordinate'] == lon) & (df['XCoordinate'] == lat)]['RiverNumber'].values[0]
    forecast_data = df.loc[df['RiverNumber'] == river_number, 'ForecastData'].values[0]

    return go.Figure(
        data=[go.Scatter(x=list(range(len(forecast_data))), y=forecast_data, mode='lines+markers')],
        layout=go.Layout(title=f'Forecast Data for River {river_number}', xaxis_title='Time', yaxis_title='Flow')
    )

# Run the app with custom host and port
if __name__ == '__main__':
    app.run_server(debug=True, host='localhost', port=8051)
