import requests
import geojson
import matplotlib.pyplot as plt
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from collections import defaultdict
import seaborn as sns
import pandas as pd
import geopandas as gpd
from pylab import rcParams

"""### Data Processing"""

def fetch_fire_incidents_by_bbox(min_lat, min_lon, max_lat, max_lon):
    """
    Fetch fire incidents within a given bounding box (lat/lon).

    Parameters:
        min_lat (float): Minimum latitude (bottom-left corner)
        min_lon (float): Minimum longitude (bottom-left corner)
        max_lat (float): Maximum latitude (top-right corner)
        max_lon (float): Maximum longitude (top-right corner)

    Returns:
        GeoDataFrame: Fire incidents within the bounding box
    """

    # Define Bounding Box Geometry (Envelope)
    bbox_geometry = f"{min_lon},{min_lat},{max_lon},{max_lat}"

    # API Query Parameters
    params = {
        "geometry": bbox_geometry,
        "geometryType": "esriGeometryEnvelope",  # BBOX filtering
        "inSR": "4326",  # Spatial reference (lat/lon)
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "f": "geojson"
    }

    # Fetch Data
    response = requests.get(API_URL, params=params)

    # Debug: Print the response to check for errors
    try:
        response_json = response.json()
        print("API Response:", response_json)
    except Exception as e:
        raise Exception(f"Error reading response: {e}")

    # Check if response contains features
    if "features" not in response_json:
        raise KeyError("Response does not contain 'features'. Check API response.")

    # Convert to GeoDataFrame
    fire_data = gpd.GeoDataFrame.from_features(response_json["features"])

    return fire_data


# fire_incidents = fetch_fire_incidents_by_bbox(36.993076, -109.045223, 41.000659, -102.041524)
# print(fire_incidents.head())

API_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query"
where = "(CreatedOnDateTime_dt >= DATE '2024-05-31' AND CreatedOnDateTime_dt <= DATE '2024-09-29') AND (POOState IN ('US-CO')) AND (IncidentSize >= 1 AND IncidentSize <= 1054153)"

#Fetch data from API
response = requests.get(API_URL,  params={'outFields':'*','where': where,'f':'geojson'})
# Check if request was successful
if response.status_code != 200 :
    print('Error detected')
    sys.exit(1)

json_response = response.json()

#Parses geojson usefull stuff like coordinates
json_response.get('features')[0].get('geometry').get('coordinates')
json_response.get('features')[0].get('properties').get('FireCause')

json_response.get('features')[0]

"""### Starting Fire Hour Distribution"""

def get_hour_distribution(datetime_column):
    fire_data = []
    for feature in json_response.get("features", []):
        properties = feature["properties"]

        # Convert timestamp to datetime (UTC to Mountain Time)
        if properties.get(datetime_column):
            fire_time = datetime.fromtimestamp(properties[datetime_column] / 1000, ZoneInfo("America/Denver"))
            formatted_hour = fire_time.strftime("%H:00")  # Format hour as "HH:00"
            fire_data.append({"hour": formatted_hour})

    # Convert list to pandas DataFrame
    df = pd.DataFrame(fire_data)

    # Check if data is available
    if df.empty:
        print("No fire data available for the given time range.")
        sys.exit(1)

    # Group by formatted hour and count occurrences
    fire_counts = df["hour"].value_counts().sort_index()


    rcParams['figure.figsize'] = 10, 5
    # Generate the histogram using Pandas
    fire_counts.plot(kind="bar", title="Fire Ignition Time Distribution", xlabel="Hour of the Day", ylabel="Number of Fires")
    plt.show()


get_hour_distribution("FireDiscoveryDateTime")

def get_fire_afected_area_distribution(Category_column):
    fire_data = []
    for feature in json_response.get("features", []):
        properties = feature["properties"]

        if properties.get(Category_column):
            fire_size = properties[Category_column]

            # Categorize fire sizes
            if fire_size < 100:
                category = "Small (<100 acres)"
            elif 100 <= fire_size < 1000:
                category = "Medium (100-1000 acres)"
            else:
                category = "Large (>1000 acres)"

            fire_data.append({"fire_size": fire_size, "category": category})

    # Convert list to pandas DataFrame
    df = pd.DataFrame(fire_data)

    # Check if data is available
    if df.empty:
        print("No fire data available for the given time range.")
        sys.exit(1)

    # Group by fire size category and count occurrences
    fire_size_counts = df["category"].value_counts().sort_index()

    # Generate the histogram using Pandas
    ax = fire_size_counts.plot(kind="bar", title="Fire Affected Area Distribution", xlabel="Fire Size Category", ylabel="Number of Fires", color=["green", "orange", "red"])

    # Add data labels on top of bars
    for i, value in enumerate(fire_size_counts):
        ax.text(i, value + 1, str(value), ha='center', fontsize=12, fontweight='bold')
    plt.show()
get_fire_afected_area_distribution("IncidentSize")

"""### Optional:  Correlation between fire start time and fire size|"""

def get_correlation():
    # Extract relevant data into a DataFrame
    fire_data = []
    for feature in json_response.get("features", []):
        properties = feature["properties"]

        if properties.get("FireDiscoveryDateTime") and properties.get("IncidentSize") and properties.get("FireOutDateTime"):
            try:
                # Convert timestamps from milliseconds to datetime
                start_time = datetime.fromtimestamp(properties["FireDiscoveryDateTime"] / 1000, ZoneInfo("America/Denver"))
                end_time = datetime.fromtimestamp(properties["FireOutDateTime"] / 1000, ZoneInfo("America/Denver"))

                # Format start hour as HH:00
                formatted_hour = start_time.strftime("%H:00")

                # Calculate fire duration in hours
                duration_hours = (end_time - start_time).total_seconds() / 3600  # Convert seconds to hours
                if duration_hours < 0:  # Ignore incorrect negative durations
                    duration_hours = None

                fire_size = properties["IncidentSize"]

                fire_data.append({"hour": formatted_hour, "fire_size": fire_size, "duration_hours": duration_hours})

            except Exception as e:
                print(f"Skipping fire due to error: {e}")

    # Convert list to pandas DataFrame
    df = pd.DataFrame(fire_data)

    # Check if data is available
    if df.empty:
        print("No fire data available for the given time range.")
        sys.exit(1)

    # Sort the hours in order
    df["hour"] = pd.Categorical(df["hour"], categories=[f"{str(h).zfill(2)}:00" for h in range(24)], ordered=True)

    # Create Bubble Chart
    plt.figure(figsize=(12, 6))
    bubble = sns.scatterplot(data=df, x="hour", y="fire_size", size="duration_hours", sizes=(20, 500), alpha=0.6)

    # Customize plot
    plt.xlabel("Hour of Fire Start (HH:00)")
    plt.ylabel("Fire Size (Acres)")
    plt.title("Fire Start Time, Size & Duration")
    plt.xticks(rotation=45)

    # *Fix the Legend for Fire Duration*
    handles, labels = bubble.get_legend_handles_labels()

    # Define meaningful custom labels based on real durations
    custom_labels = ["1 Hour", "12 Hours", "24 Hours", "72 Hours", "100+ Hours"]

    # Assign custom labels to the legend
    plt.legend(handles[:6], custom_labels, title="Fire Duration (hours)", loc="upper right")
    plt.show()

get_correlation()

with open('wfs-area-export-Colorado_2024-06-01-2024-09-30.geojson') as f:
    gj = geojson.load(f)
orora_tech_wfs_geojson = gj['features'][0]

wfs_file_path = "wfs-area-export-Colorado_2024-06-01-2024-09-30.geojson"
wfs_data = gpd.read_file(wfs_file_path)
official_data = gpd.GeoDataFrame.from_features(response.json()["features"])
official_data["FireDiscoveryDateTime"] = pd.to_datetime(official_data["FireDiscoveryDateTime"], unit="ms").dt.tz_localize(timezone.utc).dt.tz_convert("America/Denver")

wfs_data.head(5)

wfs_data["oldest_detection"] = pd.to_datetime(wfs_data["oldest_detection"], unit="ms").dt.tz_convert("America/Denver")
# Spatial Intersection - Find common fires in both datasets (Matching by Location and Timeframe)
intersected_fires = gpd.sjoin(official_data, wfs_data, how="inner", predicate="intersects")

# Compare detection times
intersected_fires["DetectedEarlierByWFS"] = intersected_fires["oldest_detection"] < intersected_fires["FireDiscoveryDateTime"]

# Count how many fires were detected earlier by WFS
wfs_earlier_count = intersected_fires["DetectedEarlierByWFS"].sum()
print("Fires first detected by WFS: ", wfs_earlier_count)
