import os
import pandas as pd
import geoglows


os.environ['PYGEOGLOWS_METADATA_TABLE_PATH'] = '/Users/sinugp/.pyenv/versions/3.10.0/lib/python3.10/site-packages/geoglows/data/metadata-tables.parquet'

# Load the CSV file
file_path = '/Users/sinugp/Downloads/altair_points.csv'  
df = pd.read_csv(file_path)

# Function to get river number using GeoGLOWS API
def get_river_number(lat, lon):
    try:
        river_id = geoglows.streams.latlon_to_river(lat, lon)
        return river_id
    except Exception as e:
        print(f"Error fetching river ID for coordinates ({lat}, {lon}): {e}")
        return None

# Add a new column for river numbers
df['RiverNumber'] = df.apply(lambda row: get_river_number(row['YCoordinate'], row['XCoordinate']), axis=1)

# Save the updated dataframe to a new CSV file
output_file_path = '/Users/sinugp/Downloads/altair_points_with_river_numbers.csv'  
df.to_csv(output_file_path, index=False)

# Display the dataframe
print(df.head())
