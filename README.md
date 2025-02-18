# Customer Success Engineer Challenge 

This project analyzes wildfire incidents using data from a public fire API and OroraTech's Wildfire Solution (WFS) system. It processes fire incidents, performs spatial analysis, and generates visualizations.

## ** Overview **
- Fetches wildfire incidents from an API within a specified bounding box.
- Saves raw and filtered data in GeoJSON and JSON formats.
- Converts timestamps to local time zones for accurate analysis.
- Performs geospatial matching between the official fire database and WFS-detected fires.
- Generates visualizations:
  - **Fire Ignition Time Distribution**
  - **Fire Affected Area Distribution**
  - **Correlation Between Fire Start Time, Fire Stop Time & Fire Size**
- Compares detection times between WFS and official sources.

## ** Output **
After the execution the script generates:
- Raw fire data saved to fire_incidents.geojson
- Filtered fire data saved to filtered_fires.json
- Charts visualizing fire incident trends
- Comparison results for WFS and Official Fire Incidents API

## ** Install Dependencies **
```bash
- pip install -r requirements.txt