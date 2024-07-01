import zarr
import s3fs
import pandas as pd
from tqdm import tqdm

def get_forecast_data(river_number, date):
    # Define the S3 bucket and Zarr path
    s3_bucket_url = f's3://geoglows-v2-forecasts/{date}.zarr/'

    # Initialize S3 filesystem
    s3 = s3fs.S3FileSystem(anon=True)

    try:
        # Use fsspec to map the S3 URL
        mapper = s3fs.S3Map(root=s3_bucket_url, s3=s3, check=False)

        # Open the Zarr group
        zarr_group = zarr.open_group(mapper, mode='r')

        # Locate the river number index
        rivid_array = zarr_group['rivid'][:]
        if river_number in rivid_array:
            river_index = list(rivid_array).index(river_number)
            # Extract the forecast data using the index
            qout_array = zarr_group['Qout'][:, :, river_index]
            time_array = zarr_group['time'][:]
            ensemble_array = zarr_group['ensemble'][:]
            
            # Construct a DataFrame
            forecast_df = pd.DataFrame(qout_array, columns=time_array)
            forecast_df.index = [f"ensemble_{i}" for i in ensemble_array]
            forecast_df.columns = time_array
            forecast_df = forecast_df.transpose()
            
            return forecast_df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error accessing data for RiverNumber {river_number} on {date}: {e}")
        return pd.DataFrame()

def list_s3_contents(bucket_url):
    # Initialize S3 filesystem
    s3 = s3fs.S3FileSystem(anon=True)

    try:
        # List contents of the bucket
        contents = s3.ls(bucket_url)
        return contents
    except Exception as e:
        print(f"Error accessing S3 bucket: {e}")
        return []

# Load the CSV file to get the list of RiverNumber
csv_file_path = '/Users/sinugp/Downloads/altair_points_with_river_numbers.csv'
try:
    df_rivers = pd.read_csv(csv_file_path)
    river_numbers = df_rivers['RiverNumber'].tolist()[:5]  # Limit to the first 5 river numbers
    print(f"Loaded {len(river_numbers)} river numbers from CSV file.")
except Exception as e:
    print(f"Error reading CSV file: {e}")
    river_numbers = []

# Get the list of available dates from the S3 bucket
s3_bucket_url = 's3://geoglows-v2-forecasts/'
dates = [item.split('/')[-1].replace('.zarr', '') for item in list_s3_contents(s3_bucket_url) if item.endswith('.zarr')]

# Take the first date for analysis
selected_date = dates[0]
print(f"Selected date for analysis: {selected_date}")

# Initialize a list to hold the forecast data
forecast_data_list = []

# Retrieve forecast data for each river number for the selected date
for river_number in tqdm(river_numbers, desc="Processing river numbers"):
    print(f"Processing RiverNumber: {river_number}, Date: {selected_date}")
    forecast_df = get_forecast_data(river_number, selected_date)
    if not forecast_df.empty:
        # Add river number and date as columns
        forecast_df['RiverNumber'] = river_number
        forecast_df['Date'] = selected_date
        forecast_data_list.append(forecast_df)

# Combine all the forecast data into a single DataFrame for analysis
if forecast_data_list:
    combined_forecast_data = pd.concat(forecast_data_list, ignore_index=True)
    
    # Clean the DataFrame by removing rows with all NaN values
    cleaned_forecast_data = combined_forecast_data.dropna(how='all')
    
    # Save the cleaned forecast data to a CSV file
    output_csv_file_path = '/Users/sinugp/Downloads/forecast_data.csv'
    cleaned_forecast_data.to_csv(output_csv_file_path, index=False)
    print(f"Forecast data saved to {output_csv_file_path}")
    
    # Display the cleaned forecast data
    print(cleaned_forecast_data.head())
else:
    print("No forecast data collected.")