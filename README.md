# **Wildfire Analysis Project**   

# ** Overview **  
This project analyzes wildfire incidents using **public fire data** and **OroraTech WFS detections** to:  
+ Identify fire ignition trends.  
+ Compare fire size distributions.  
+ Detect if WFS identifies fires **before official records**.  

---

## ** Features **  
### **1️.Fetch Fire Data**  
- Retrieves wildfire data from the **public API**.  
- Filters fires **larger than 1 acre** in **Colorado** (or user-defined location).  
- Allows **custom date range & bounding box selection**.  

### **2️. Data Processing & Visualization**  
- **Fire Start Time Analysis** → Histogram of fire ignition times.  
- **Fire Size Classification** → Categorizes fires into **small (<100 acres), medium, large (>1000 acres)**.  
- **Optional - Correlation Analysis** → Checks if fire size and volume is related to start time.  

### **3️. WFS vs. Official Data Comparison**  
- Loads **OroraTech WFS** fire detections.  
- Uses **geospatial matching** to compare datasets.  
- **Identifies fires detected first by WFS** before official records.  

---

## ** Setup & Installation**  
### **1️. Install Dependencies**  
```bash
pip install -r requirements.txt

----

** 2. Run the analysis** 
python fire_analysis.py
---