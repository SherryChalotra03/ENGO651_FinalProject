# test.py - Calgary Route Risk Analysis Script

## Description
`test.py` is a demonstration script that calculates and visualizes a risk-aware route between two points in Calgary using road network data and risk scores.

## Dependencies
```python
pandas
geopandas
shapely
pyproj
folium
matplotlib
```

## Input Files Required
- `./Datasets/Subset/road_risk_layer_categorized.shp`: Road network shapefile with risk categories
- `./Datasets/Subset/road_network.pkl`: Pickled road network graph
- `find_path.py`: Custom module containing routing algorithms

## Usage Example
```python
# Set start and end coordinates (longitude, latitude)
start_coords = (-114.0962, 51.0289)  # Downtown Calgary
end_coords = (-114.08083, 51.06874)  # West Calgary

# Set routing time
current_time = datetime(2025, 3, 26, 17, 0)  # March 26, 2025, 5 PM

# Adjust route parameters
# alpha=1.0: weight for distance
# beta=1.0: weight for risk
path = dijkstra_path(G, start_node, end_node, current_time, alpha=1.0, beta=1.0)
```

## Output
1. Console Output:
   - Number of nodes in the path
   - Total distance in meters
   - Total adjusted risk score
   - Count of risk categories along the route

2. Generated Files:
   - `./Datasets/Subset/risk_map_hotspot.html`: Interactive map showing:
     - Color-coded road network by risk level
     - Highlighted route in red
     - Start marker (green)
     - End marker (red)
     - Risk category legend

## Risk Category Color Scheme
- Very Low: Green (#2ecc71)
- Low: Yellow (#f1c40f)
- Medium: Red (#e74c3c)
- High: Dark Red (#c0392b)
- Very High: Purple (#8e44ad)

## Coordinate Systems
- Input coordinates: WGS84 (EPSG:4326)
- Internal calculations: UTM Zone 11N (EPSG:32611)
- Output map: WGS84 (EPSG:4326)