import pandas as pd
import requests

# Load the CSV file
file_path = '/Users/sinugp/Downloads/altair_points_with_river_numbers.csv'  # File with River Number
df = pd.read_csv(file_path)

# Extract the RiverNumber column
river_numbers = df['RiverNumber'].unique()

# Function to get river flow forecast from GEOGloWS API
def get_river_flow_forecast(river_number):
    url = f"https://geoglows.ecmwf.int/api/ForecastEnsembles/?reach_id={river_number}&return_format=csv"
    response = requests.get(url)
    if response.status_code == 200:
        forecast_df = pd.read_csv(pd.compat.StringIO(response.text))
        return forecast_df
    else:
        print(f"Failed to fetch data for river number {river_number}: Status code {response.status_code}")
        return pd.DataFrame()

# Create a dictionary to store the forecasts for each river number
forecasts_dict = {}

for river_number in river_numbers:
    forecast_df = get_river_flow_forecast(river_number)
    if not forecast_df.empty:
        forecasts_dict[river_number] = forecast_df
    else:
        print(f"No data returned for river number {river_number}")

# Combine all forecasts into a single dataframe
if forecasts_dict:
    all_forecasts = pd.concat(forecasts_dict, names=['RiverNumber'])
    print(all_forecasts.head())
else:
    print("No data available for any river numbers.")
