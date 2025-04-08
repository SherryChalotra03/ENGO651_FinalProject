# Accident Analysis and Route Planning System

This project is designed to analyze traffic accidents and provide route planning capabilities using OpenStreetMap (OSM) data. It includes tools for processing road networks, analyzing accident hotspots, and visualizing the results.

## Project Structure
- `get_osm_byName.py`: Utility for retrieving OSM data by location name
- `rout_planning_hotspot.py`: Route planning with accident hotspot consideration
- `find_path.py`: Path finding and routing functionality
- `test.py`:  A sample code and visualization tools for maps and data
- `requirements.txt`: Project dependencies

## Features

- Road network processing and analysis
- Accident hotspot identification
- Route planning with safety considerations
- Interactive map visualization
- OSM data integration and processing
- Geographic data analysis and manipulation

## Dependencies

The project requires several Python packages for data processing, visualization, and geographic analysis. Key dependencies include:

- `psycopg2`: PostgreSQL database adapter
- `pandas>=1.3.0`: Data manipulation
- `sqlalchemy`: SQL toolkit and ORM
- `matplotlib`: Plotting library
- `seaborn`: Statistical visualization
- `folium`: Interactive map creation
- `streamlit`: Web application framework
- `streamlit_folium`: Streamlit component for Folium maps
- `geopandas>=0.9.0`: Geographic data processing
- `shapely>=1.8.0`: Geometric operations

For a complete list of dependencies and installation instructions, see [requirements.txt](requirements.txt).

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Get OSM data:
```bash
python get_osm_byName.py
```

2. Calculate Hotspots (Risk Aware Route Planning):
```bash
python rout_planning_hotspot.py
```

3. Find optimal routes:
```bash
python find_path.py
```

4. Visualize results:
```bash
python test.py
```

## Data Processing Pipeline

1. The system processes OpenStreetMap data to extract road networks
2. Accident data is analyzed and mapped to road segments
3. Hotspots are identified based on accident frequency and severity
4. Route planning takes into account both distance and safety factors
5. Results are visualized using interactive maps

## Route Planning Features

The project supports two path-finding algorithms:
1. A* algorithm (`astar_path`): Uses heuristic-based search for efficient route finding
2. Dijkstra's algorithm (`dijkstra_path`): Guarantees optimal paths based on combined distance and risk factors

### 1. Processed Data Files
- `road_network.shp`: Road network with risk scores, categories and geometries
      - Segment ID
      - Base risk score
      - Temporal risk factors
      - Risk category (Very Low, Low, Medium, High, Very High)

- `accident_clusters.shp`: Results of DBSCAN clustering analysis
- `hotspots.shp`: Identified accident hotspots with significance scores

### 2. Visualization Outputs
- `risk_map_hotspot.html`: Interactive Folium map showing:
  - Road network colored by risk category
  - Accident hotspots
  - Cluster centers
  - Risk category legend


All output files are saved in the `./Datasets/Subset/` directory by default.


## Visualization

The project includes a visualization module that creates interactive maps using Folium and Streamlit. This allows users to:
- View accident hotspots
- Analyze road network characteristics
- Visualize optimal routes with risk categories:
  - Very Low (Green)
  - Low (Yellow)
  - Medium (Red)
  - High (Dark Red)
  - Very High (Purple)
- Interact with geographic data

## Contributing
