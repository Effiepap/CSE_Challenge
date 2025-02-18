import requests
import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
from datetime import datetime
from zoneinfo import ZoneInfo


# Function to Fetch and Save Fire Data
def fetch_fire_incidents(min_lat, min_lon, max_lat, max_lon, raw_file="fire_incidents.geojson", filtered_file="filtered_fires.json"):
    """
    Fetches wildfire data from the API, saves raw data to GeoJSON, filters based on criteria, and saves filtered data.

    Returns:
    - A Pandas DataFrame with the filtered fire data.
    """

    # API URL & Parameters definition
    API_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query"
    where = (
        "(CreatedOnDateTime_dt >= DATE '2024-06-01' AND CreatedOnDateTime_dt <= DATE '2024-09-30') "
        "AND (POOState = 'US-CO') AND (IncidentSize >= 1)"
    )
    
    params = {
        "geometry": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "where": where,
        "f": "geojson"
    }

    # API Request
    response = requests.get(API_URL, params=params)

    #Check if Request was successful
    if response.status_code != 200:
        print("Error fetching data:", response.text)
        sys.exit(1)

    try:
        fire_data = response.json()
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
        sys.exit(1)

    # Save raw data before filtering
    with open(raw_file, "w") as f:
        json.dump(fire_data, f, indent=4)
    print(f"Raw fire data saved to {raw_file}")

    # Extract Features (list)
    features = fire_data.get("features", [])

    if not features:
        print("No fire data found.")
        sys.exit(1)

    #Intitialize an empty list to store filtered data
    filtered_data = []
    for feature in features:
        props = feature.get("properties", {})
        
        #Extract relevant fields
        fire_info = {
            "IncidentName": props.get("IncidentName", "Unknown"),
            "FireDiscoveryDateTime": props.get("FireDiscoveryDateTime"),
            "FireOutDateTime": props.get("FireOutDateTime"),  # Add fire stop time
            "IncidentSize": props.get("IncidentSize", 0),
            "POOState": props.get("POOState", "Unknown"),
            "Latitude": feature["geometry"]["coordinates"][1] if feature["geometry"] else None,
            "Longitude": feature["geometry"]["coordinates"][0] if feature["geometry"] else None
        }
        
        filtered_data.append(fire_info)

    # Save filtered data
    with open(filtered_file, "w") as f:
        json.dump(filtered_data, f, indent=4)
    print(f"Filtered fire data saved to {filtered_file}")

    # Convert to Pandas DataFrame
    df = pd.DataFrame(filtered_data)
    
    # Convert timestamps to datetime
    df["FireDiscoveryDateTime"] = pd.to_datetime(df["FireDiscoveryDateTime"], errors="coerce", unit="ms")
    df["FireOutDateTime"] = pd.to_datetime(df["FireOutDateTime"], errors="coerce", unit="ms")  # Convert fire stop time
    
    return df


# 1. Function to plot Fire Ignition Time Distribution
def get_hour_distribution(df):
    """
    Extracts fire ignition times, converts them to Mountain Time, and plots the correct distribution.
    """
    #Convert timestamp to MT
    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].dt.tz_localize("UTC").dt.tz_convert("America/Denver")
    df["Hour"] = df["FireDiscoveryDateTime"].dt.strftime("%H:00")

    #Count occurrences of each hour
    fire_counts = df["Hour"].value_counts().reindex([f"{str(h).zfill(2)}:00" for h in range(24)], fill_value=0)

    #Plot histogram
    plt.figure(figsize=(10, 5))
    fire_counts.plot(kind="bar", color="steelblue")
    plt.xticks(rotation=45)
    plt.xlabel("Hour of the Day")
    plt.ylabel("Number of Fires")
    plt.title("Fire Ignition Time Distribution")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()


# 2. Fire Affected Area Distribution
def get_fire_affected_area_distribution(df):
    """
    Categorizes fires based on size and plots their distribution.
    """
    fire_data = []
    
    # Loop through each row in the DataFrame
    for _, row in df.iterrows():
        fire_size = row["IncidentSize"]

        if fire_size < 100:
            category = "Small (<100 acres)"
        elif 100 <= fire_size < 1000:
            category = "Medium (100-1000 acres)"
        else:
            category = "Large (>1000 acres)"

        fire_data.append({"fire_size": fire_size, "category": category})
    #Convert list to DataFrame
    df_fire = pd.DataFrame(fire_data)
    
    #Count occurrences per fire size category
    fire_size_counts = df_fire["category"].value_counts().sort_index()

    #Plot histogram
    plt.figure(figsize=(10, 5))
    ax = fire_size_counts.plot(kind="bar", title="Fire Affected Area Distribution", xlabel="Fire Size Category", ylabel="Number of Fires", color=["green", "orange", "red"])
    
    #Annotate bars with values
    for i, value in enumerate(fire_size_counts):
        ax.text(i, value + 1, str(value), ha='center', fontsize=12, fontweight='bold')
    
    plt.show()


# 3. Correlation Between Fire Start Time, Fire Stop Time & Fire Size
def get_correlation(df):
    """
    Extracts fire start and stop times, calculates duration, and plots the correlation between 
    fire start time, fire size, and duration.
    """
    fire_data = []

    #Loop  through each fire event
    for _, row in df.iterrows():
        try:
            # Ensure timestamps are in datetime format
            start_time = pd.to_datetime(row["FireDiscoveryDateTime"], errors="coerce")
            end_time = pd.to_datetime(row["FireOutDateTime"], errors="coerce")
            fire_size = row["IncidentSize"]

            # Check if timestamps are valid
            if pd.notnull(start_time) and pd.notnull(end_time) and pd.notnull(fire_size):
                
                # Ensure timestamps are timezone-aware
                if start_time.tzinfo is None:
                    start_time = start_time.tz_localize("UTC")  # Localize naive timestamps to UTC
                else:
                    start_time = start_time.tz_convert("UTC")  # Convert if already timezone-aware

                if end_time.tzinfo is None:
                    end_time = end_time.tz_localize("UTC")  # Localize naive timestamps to UTC
                else:
                    end_time = end_time.tz_convert("UTC")  # Convert if already timezone-aware

                # Convert to Mountain Time (America/Denver)
                start_time = start_time.tz_convert("America/Denver")
                end_time = end_time.tz_convert("America/Denver")

                # Format start hour as HH:00
                formatted_hour = start_time.strftime("%H:00")

                # Calculate fire duration in hours
                duration_hours = (end_time - start_time).total_seconds() / 3600  # Convert seconds to hours
                if duration_hours < 0:  # Ignore incorrect negative durations
                    duration_hours = None

                fire_data.append({"hour": formatted_hour, "fire_size": fire_size, "duration_hours": duration_hours})

        except Exception as e:
            print(f"Skipping fire due to error: {e}")

    # Convert list to pandas DataFrame
    df_corr = pd.DataFrame(fire_data)

    # Check if data is available
    if df_corr.empty:
        print("No fire data available for the given time range.")
        sys.exit(1)

    # Sort the hours in order
    df_corr["hour"] = pd.Categorical(df_corr["hour"], categories=[f"{str(h).zfill(2)}:00" for h in range(24)], ordered=True)

    # Create Bubble Chart
    plt.figure(figsize=(12, 6))
    bubble = sns.scatterplot(data=df_corr, x="hour", y="fire_size", size="duration_hours", sizes=(20, 500), alpha=0.6)

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


# Run Everything in lat/lon for Colorado
bbox_min_lat = 36.993076
bbox_min_lon = -109.045223
bbox_max_lat = 41.000659
bbox_max_lon = -102.041524

df_fires = fetch_fire_incidents(bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon)

get_hour_distribution(df_fires)
get_fire_affected_area_distribution(df_fires)
get_correlation(df_fires)



"OroraTech / Fire Incidents API Matching"

# Load WFS data
wfs_data = gpd.read_file("wfs-area-export-Colorado_2024-06-01-2024-09-30.geojson")

# Load official fire incidents
df_fires = fetch_fire_incidents(bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon)

# Convert to GeoDataFrame
official_data = gpd.GeoDataFrame(df_fires, geometry=gpd.points_from_xy(df_fires.Longitude, df_fires.Latitude), crs="EPSG:4326")

# Ensure WFS data has the same CRS
wfs_data = wfs_data.to_crs("EPSG:4326")

# Convert timestamps
official_data["FireDiscoveryDateTime"] = pd.to_datetime(official_data["FireDiscoveryDateTime"], utc=True).dt.tz_convert("America/Denver")
wfs_data["oldest_detection"] = pd.to_datetime(wfs_data["oldest_detection"], utc=True).dt.tz_convert("America/Denver")

# Spatial join to match fires based on location
intersected_fires = gpd.sjoin(official_data, wfs_data, how="inner", predicate="intersects")

# Compare detection times
wfs_earlier_count = (intersected_fires["oldest_detection"] < intersected_fires["FireDiscoveryDateTime"]).sum()

# Calculate percentage
total_intersected_fires = len(intersected_fires)
wfs_earlier_percentage = (wfs_earlier_count / total_intersected_fires) * 100 if total_intersected_fires > 0 else 0

# Print final result only
print(f"Fires first detected by WFS: {wfs_earlier_count}")
print(f"Percentage of fires first detected by WFS: {wfs_earlier_percentage:.2f}%")
