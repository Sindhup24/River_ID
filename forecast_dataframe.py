import zarr
import s3fs
import pandas as pd
import boto3

# Define the S3 bucket and Zarr path
bucket_name = 'my-river-flow-bucket'
zarr_path = 'sample.zarr/'  # Path to the Zarr directory in S3

# Define the CSV file paths
csv_file_path = '/Users/sinugp/Downloads/altair_points_with_river_numbers.csv'
output_csv_file_path = '/Users/sinugp/Downloads/river_flow_forecast_data.csv'

# Initialize S3 client and list objects in the bucket to verify
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=zarr_path)
if 'Contents' in response:
    print("Objects in the bucket:")
    for obj in response['Contents']:
        print(obj['Key'])
else:
    print("No objects found in the bucket with the given prefix.")

# Access the Zarr group using s3fs and zarr
try:
    # Use fsspec to map the S3 URL
    url = f's3://my-river-flow-bucket/sample.zarr/'
    print(f"Attempting to access Zarr group at: {url}")
    mapper = s3fs.S3Map(root=url, s3=s3fs.S3FileSystem(), check=False)
    
    # Open the Zarr group
    zarr_group = zarr.open_group(mapper, mode='r')
    print("Zarr group opened successfully")
    print(zarr_group.tree())
except Exception as e:
    print(f"Error opening Zarr group: {e}")

# Read the CSV file to get the list of RiverNumber
try:
    df_rivers = pd.read_csv(csv_file_path)
    river_numbers = df_rivers['RiverNumber'].tolist()
    print(f"Read CSV file: {csv_file_path}")
    print(f"River numbers: {river_numbers}")
except Exception as e:
    print(f"Error reading CSV file: {e}")

# Initialize list to hold the forecast data
forecast_data = []

# Retrieve data for each RiverNumber
if 'zarr_group' in locals():
    for river_number in river_numbers:
        river_str = str(river_number)
        if river_str in zarr_group:
            try:
                river_data = zarr_group[river_str][:]
                forecast_data.append({
                    'RiverNumber': river_number,
                    'ForecastData': river_data.tolist()  # Convert to list for easier handling
                })
                print(f"Retrieved data for RiverNumber: {river_number}")
            except KeyError:
                print(f"No data found for RiverNumber: {river_number}")
else:
    print("Zarr group is not defined")

# Collect the data into a Pandas DataFrame
if forecast_data:
    df_forecast = pd.DataFrame(forecast_data)
    print("Collected forecast data:")
    print(df_forecast)
    
    # Save the DataFrame to a CSV file
    try:
        df_forecast.to_csv(output_csv_file_path, index=False)
        print(f"Forecast data saved to CSV file: {output_csv_file_path}")
    except Exception as e:
        print(f"Error saving forecast data to CSV file: {e}")
else:
    print("No forecast data collected.")
