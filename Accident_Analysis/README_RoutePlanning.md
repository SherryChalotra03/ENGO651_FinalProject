# Route Planning with Hotspot Analysis

This module provides functionality for analyzing accident hotspots and calculating risk scores for road segments to support safer route planning.

## Functions Overview

### Data Processing Functions

#### `explode_multilinestring(gdf)`
Converts MultiLineString geometries to individual LineString geometries.

**Parameters:**
- `gdf`: GeoDataFrame containing road network data

**Returns:**
- GeoDataFrame with exploded LineString geometries

#### `read_accident_data(shapefile_path)`
Reads accident data from a shapefile.

**Parameters:**
- `shapefile_path`: String path to the accident data shapefile

**Returns:**
- GeoDataFrame containing accident data
- Returns None if there's an error reading the file

### Clustering Analysis Functions

#### `prepare_coordinates(gdf)`
Extracts coordinates from GeoDataFrame for clustering analysis.

**Parameters:**
- `gdf`: GeoDataFrame containing accident points

**Returns:**
- Numpy array of coordinates

#### `perform_clustering(coords, eps=200, min_samples=5)`
Performs DBSCAN clustering on accident points.

**Parameters:**
- `coords`: Numpy array of coordinates
- `eps`: Maximum distance between samples (in meters), default=200
- `min_samples`: Minimum number of samples in a neighborhood, default=5

**Returns:**
- Array of cluster labels

#### `visualize_clusters(gdf, labels)`
Visualizes the clustered accident points.

**Parameters:**
- `gdf`: GeoDataFrame containing accident data
- `labels`: Array of cluster labels

**Output:**
- Saves 'accident_clusters.png' visualization

#### `analyze_clusters(gdf, labels)`
Analyzes and prints statistics about the clusters.

**Parameters:**
- `gdf`: GeoDataFrame containing accident data
- `labels`: Array of cluster labels

**Output:**
- Prints cluster analysis statistics to console

### Hotspot Analysis Functions

#### `perform_hotspot_analysis(gdf, distance_threshold=200, p_value_threshold=0.25, z_score_threshold=-0.2)`
Performs hotspot analysis using spatial statistics.

**Parameters:**
- `gdf`: GeoDataFrame containing accident data
- `distance_threshold`: Maximum distance for neighborhood definition (meters), default=200
- `p_value_threshold`: Threshold for statistical significance, default=0.25
- `z_score_threshold`: Threshold for z-score classification, default=-0.2

**Returns:**
- GeoDataFrame with added hotspot classification

#### `visualize_hotspots(gdf)`
Visualizes the hotspot analysis results.

**Parameters:**
- `gdf`: GeoDataFrame containing hotspot analysis results

**Output:**
- Saves 'accident_hotspots.png' visualization

#### `analyze_hotspots(gdf)`
Analyzes and prints hotspot statistics.

**Parameters:**
- `gdf`: GeoDataFrame containing hotspot analysis results

**Output:**
- Prints hotspot analysis statistics to console

### Risk Calculation Functions

#### `calculate_road_risk_(road_gdf, hotspot_gdf, max_distance=500, power=2)`
Calculates risk scores for road segments based on proximity to hotspots using inverse distance weighting (IDW).

**Parameters:**
- `road_gdf`: GeoDataFrame containing road segments
- `hotspot_gdf`: GeoDataFrame containing accident hotspots
- `max_distance`: Maximum distance to consider for risk calculation (meters), default=500
- `power`: Power parameter for IDW, default=2

**Returns:**
- GeoDataFrame with added risk scores

#### `calculate_road_risk(road_geometry, hotspot_gdf, max_distance=500, power=2, max_risk=1.0)`
Calculates risk score for a single road segment.

**Parameters:**
- `road_geometry`: Shapely geometry of the road segment
- `hotspot_gdf`: GeoDataFrame containing accident hotspots
- `max_distance`: Maximum distance to consider (meters), default=500
- `power`: Power parameter for IDW, default=2
- `max_risk`: Maximum risk score, default=1.0

**Returns:**
- Float risk score between 0 and max_risk

### Visualization Functions

#### `visualize_risk_layer(road_risk_gdf)`
Visualizes the risk layer for road segments.

**Parameters:**
- `road_risk_gdf`: GeoDataFrame containing road segments with risk scores

**Output:**
- Saves 'road_risk_visualization.png'

#### `analyze_risk_layer(road_risk_gdf)`
Analyzes and prints statistics about the risk layer.

**Parameters:**
- `road_risk_gdf`: GeoDataFrame containing road segments with risk scores

**Output:**
- Prints risk layer analysis statistics to console

## Usage Example

```python
# Read accident data
accident_data = read_accident_data('accidents.shp')

# Perform clustering analysis
coords = prepare_coordinates(accident_data)
labels = perform_clustering(coords)
visualize_clusters(accident_data, labels)
analyze_clusters(accident_data, labels)

# Perform hotspot analysis
hotspot_data = perform_hotspot_analysis(accident_data)
visualize_hotspots(hotspot_data)
analyze_hotspots(hotspot_data)

# Calculate road risk
road_risk = calculate_road_risk_(road_network, hotspot_data)
visualize_risk_layer(road_risk)
analyze_risk_layer(road_risk)
```

## Dependencies
- geopandas
- numpy
- scikit-learn
- matplotlib
- shapely
- libpysal
- scipy
- rtree
- pandas

## Notes
- All distance parameters are in meters
- Hotspot analysis uses Getis-Ord Gi* statistics
- Spatial indexing is used for efficient risk calculations 