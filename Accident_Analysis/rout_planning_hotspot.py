import geopandas as gpd
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from libpysal.weights import DistanceBand
from libpysal.examples import load_example
from esda.getisord import G_Local
from scipy import stats
from scipy.spatial.distance import cdist
from shapely.ops import nearest_points
import pandas as pd
from rtree import index

# Step 1: It takes road network and convert the MultiLineString to LineString and returns a gdf
def explode_multilinestring(gdf):
    """
    Convert MultiLineString geometries to individual LineString geometries.
    """
    single_lines = []
    for idx, row in gdf.iterrows(): 
        geom = row.geometry     # Gets the Shapely geometry object (e.g., MultiLineString, LineString) from the current row.
        if geom.geom_type == 'MultiLineString':
            for line in geom.geoms:
                new_row = row.copy()
                new_row.geometry = line
                single_lines.append(new_row)
        else:
            single_lines.append(row)
    return gpd.GeoDataFrame(single_lines)

# Step 2: Read the accident data from the shapefile
def read_accident_data(shapefile_path):
    """
    Read accident data from shapefile
    """
    try:
        gdf = gpd.read_file(shapefile_path)
        return gdf
    except Exception as e:
        print(f"Error reading shapefile: {e}")
        return None

# Step 3: Take the gdf from step-2 to fetch the x, y (lat long) from the geometry column for clustering (its fetched and converted to numpy array which a numerical format favourable for DBSCAN clustering)
def prepare_coordinates(gdf):
    """
    Extract coordinates from GeoDataFrame for clustering
    """
    # Extract coordinates from geometry
    coords = np.array([(geom.x, geom.y) for geom in gdf.geometry])
    return coords

#Step 4: Perform DBSCAN- take the coords from previous step-3 with eps value 200 meters and min_samples=5
def perform_clustering(coords, eps=200, min_samples=5):
    """
    Perform DBSCAN clustering on accident points
    eps: maximum distance between samples (in meters)
    min_samples: minimum number of samples in a neighborhood
    """
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(coords)
    return clustering.labels_

#Creates a scatter plot of accident points, coloring them by their cluster labels (from DBSCAN), and saves the visualization as an image.
#Cluster labels from perform_clustering, gdf- The input dataset containing accident points with a geometry column (Provides the x, y coordinates of points to plot.)
def visualize_clusters(gdf, labels):
    """
    Visualize the clustered accident points
    """
    # Create a new column for cluster labels , aligning them with the accident points.
    gdf['cluster'] = labels    
    
    # Plot
    fig, ax = plt.subplots(figsize=(15, 15))
    
    # Plot points colored by cluster
    scatter = ax.scatter(gdf.geometry.x, gdf.geometry.y, 
                        c=labels, cmap='viridis',
                        s=50, alpha=0.6)
    
    # Add legend
    legend1 = ax.legend(*scatter.legend_elements(),
                       loc="upper right", title="Clusters")
    ax.add_artist(legend1)
    
    # Add title and labels
    plt.title('Accident Hotspots Clustering')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    
    # Save the plot
    plt.savefig('accident_clusters.png')
    # plt.show()
    plt.close()


#Step 5 : Analyzes the cluster labels from DBSCAN and prints statistics about the number of accidents in each cluster and noise points. (Provides a quantitative summary of the clustering results, helping users understand how many accidents are in hotspots versus scattered (noise), and their relative proportions.)
def analyze_clusters(labels):
    """
    Analyze the clusters and print statistics
    """
    # Count points in each cluster
    unique_labels, counts = np.unique(labels, return_counts=True)
    
    print("\nCluster Analysis:")
    print("-" * 50)
    for label, count in zip(unique_labels, counts):
        if label == -1:
            print(f"Noise points: {count}")
        else:
            print(f"Cluster {label}: {count} accidents")
    
    # Calculate percentage of points in clusters vs noise
    noise_points = counts[unique_labels == -1][0]
    total_points = len(labels)
    clustered_points = total_points - noise_points
    
    print("\nSummary:")
    print(f"Total accidents: {total_points}")
    print(f"Clustered accidents: {clustered_points} ({clustered_points/total_points*100:.2f}%)")
    print(f"Noise points: {noise_points} ({noise_points/total_points*100:.2f}%)")

#Step 6 : Performs a simplified hotspot analysis on accident points to identify statistically significant clusters (hotspots) and areas with fewer incidents (cold spots) using spatial statistics.
def perform_hotspot_analysis(gdf, distance_threshold=200, p_value_threshold=0.25, z_score_threshold=-0.2):
    """
    Perform hotspot analysis using spatial statistics
    """
    # Get coordinates
    coords = np.array([(geom.x, geom.y) for geom in gdf.geometry])
    
    # Calculate distance matrix
    distances = cdist(coords, coords)
    
    # Create binary neighborhood matrix
    neighborhood = distances <= distance_threshold   #give true or false
    neighborhood = neighborhood.astype(int)             #convert to 1(neighbor) or 0(not a neigbor)
    
    # Calculate local density (sum of neighbors)
    local_density = np.sum(neighborhood, axis=1)  #Measures how "crowded" each point’s neighborhood
    
    # Calculate z-scores
    z_scores = stats.zscore(local_density)
    
    # Add statistics to GeoDataFrame
    gdf['local_density'] = local_density
    gdf['z_score'] = z_scores
    gdf['p_value'] = 1 - stats.norm.cdf(abs(z_scores))
    
    # Classify hotspots based on z-scores and p-values
    gdf['hotspot'] = 'Not Significant'
    # gdf.loc[(gdf['z_score'] > 1.96) & (gdf['p_value'] < 0.05), 'hotspot'] = 'Hot Spot'
    # gdf.loc[(gdf['z_score'] < -1.96) & (gdf['p_value'] < 0.05), 'hotspot'] = 'Cold Spot'
    gdf.loc[(gdf['z_score'] > z_score_threshold) & (gdf['p_value'] > p_value_threshold), 'hotspot'] = 'Hot Spot'
    gdf.loc[(gdf['z_score'] < z_score_threshold) & (gdf['p_value'] < p_value_threshold), 'hotspot'] = 'Cold Spot'

    return gdf

def visualize_hotspots(gdf):
    """
    Visualize the hotspot analysis results
    """
    fig, ax = plt.subplots(figsize=(15, 15))
    
    # Plot points colored by hotspot classification
    scatter = ax.scatter(gdf.geometry.x, gdf.geometry.y,
                        c=gdf['hotspot'].map({'Hot Spot': 'red', 
                                            'Cold Spot': 'blue',
                                            'Not Significant': 'gray'}),
                        s=50, alpha=0.6)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='red', label='Hot Spot', markersize=10),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='blue', label='Cold Spot', markersize=10),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='gray', label='Not Significant', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper right', title='Hotspot Classification')
    
    plt.title('Getis-Ord Gi* Hotspot Analysis')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    
    plt.savefig('accident_hotspots.png')
    # plt.show()
    plt.close()

def analyze_hotspots(gdf):
    """
    Analyze and print hotspot statistics
    """
    hotspot_counts = gdf['hotspot'].value_counts()
    
    print("\nHotspot Analysis:")
    print("-" * 50)
    print(f"Total points: {len(gdf)}")
    print(f"Hot spots: {hotspot_counts.get('Hot Spot', 0)}")
    print(f"Cold spots: {hotspot_counts.get('Cold Spot', 0)}")
    print(f"Not significant: {hotspot_counts.get('Not Significant', 0)}")
    
    # Calculate percentage of significant hotspots
    significant_hotspots = hotspot_counts.get('Hot Spot', 0)
    total_points = len(gdf)
    print(f"\nPercentage of significant hotspots: {(significant_hotspots/total_points)*100:.2f}%")

def calculate_road_risk_(road_gdf, hotspot_gdf, max_distance=500, power=2):
    """
    Calculate risk scores for road segments based on proximity to hotspots
    using inverse distance weighting (IDW) with spatial indexing for efficiency
    
    Parameters:
    - road_gdf: GeoDataFrame containing road segments
    - hotspot_gdf: GeoDataFrame containing accident hotspots
    - max_distance: Maximum distance to consider for risk calculation (in meters)
    - power: Power parameter for IDW (higher values give more weight to closer points)
    """
    # Create a copy of the road GeoDataFrame to store results
    road_risk = road_gdf.copy()
    
    # Initialize risk scores
    road_risk['risk_score'] = 0.0
    
    # Get hotspot points
    hotspot_points = hotspot_gdf[hotspot_gdf['hotspot'] == 'Hot Spot']
    
    # Create spatial index for hotspot points- Builds an R-tree spatial index of hotspot bounding boxes. Speeds up queries by quickly identifying hotspots near a road, avoiding exhaustive distance checks. R-tree is efficient for spatial data.
    hotspot_idx = index.Index()
    for idx, row in hotspot_points.iterrows():
        hotspot_idx.insert(idx, row.geometry.bounds)
    
    # Calculate risk for each road segment using spatial indexing
    for idx, road in road_risk.iterrows():
        road_geom = road.geometry
        
        # Create buffer around road segment
        buffer_geom = road_geom.buffer(max_distance) #buffer (polygon) of 500 mt around road segment
        
        # Find potential hotspots using spatial index
        potential_hotspot_indices = list(hotspot_idx.intersection(buffer_geom.bounds))
        
        if not potential_hotspot_indices:
            print('empty hotspot')
            continue
            
        # Calculate distances and weights for potential hotspots
        total_risk = 0
        count = 0
        
        for hotspot_idx in potential_hotspot_indices:
            hotspot = hotspot_points.loc[hotspot_idx].geometry
            
            # Find the nearest point on the road to the hotspot
            nearest_road_point, _ = nearest_points(road_geom, hotspot)
            distance = nearest_road_point.distance(hotspot)
            
            if distance <= max_distance:
                weight = 1 / (distance ** power) #Inverse distance weight power=2
                total_risk += weight
                count += 1
        
        if count > 0:
            road_risk.at[idx, 'risk_score'] = total_risk / count #Normalizes risk by the number of hotspots
    
    # Normalize risk scores to 0-1 range -min max normalization
    road_risk['risk_score'] = (road_risk['risk_score'] - road_risk['risk_score'].min()) / \
                             (road_risk['risk_score'].max() - road_risk['risk_score'].min())
    
    return road_risk


def calculate_road_risk(road_geometry, hotspot_gdf, max_distance=500, power=2, max_risk=1.0):
    """
    Calculate risk score for a road segment based on proximity to hotspots.

    Parameters:
    - road_geometry: Shapely LineString or Point representing the road segment.
    - hotspot_gdf: GeoDataFrame with hotspot locations (geometry column).
    - max_distance: Max distance (meters) to consider hotspots (default: 500).
    - power: Exponent for inverse distance weighting (default: 2).
    - max_risk: Maximum risk score (default: 1.0).

    Returns:
    - Float risk score for the road segment.
    """
    # Get road segment centroid for distance calculation
    if isinstance(road_geometry, LineString):
        centroid = road_geometry.centroid
    else:
        centroid = Point(road_geometry)

    # Calculate distances to all hotspots
    distances = hotspot_gdf.geometry.distance(centroid)

    # Filter hotspots within max_distance
    nearby_hotspots = distances[distances <= max_distance]

    # Calculate risk score using inverse distance weighting (1/d^power)
    risk_score = 0
    for dist in nearby_hotspots:
        if dist > 0:  # Avoid division by zero
            weight = 1 / (dist ** power)  # Inverse distance with specified power
            risk_score += weight * max_risk  # Accumulate risk contribution

    # Cap the risk score at max_risk
    # return min(risk_score, max_risk)
    return risk_score


def visualize_risk_layer(road_risk_gdf):
    """
    Visualize the risk layer
    """
    fig, ax = plt.subplots(figsize=(15, 15))
    
    # Plot road segments colored by risk score
    road_risk_gdf.plot(column='risk_score',
                      cmap='YlOrRd',
                      ax=ax,
                      legend=True,
                      legend_kwds={'label': 'Risk Score'},
                      linewidth=2)
    
    plt.title('Road Network Risk Layer')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    
    plt.savefig('road_risk_layer.png')
    # plt.show()
    plt.close()

def analyze_risk_layer(road_risk_gdf):
    """
    Analyze and print statistics about the risk layer
    """
    print("\nRisk Layer Analysis:")
    print("-" * 50)
    print(f"Total road segments: {len(road_risk_gdf)}")
    print(f"Average risk score: {road_risk_gdf['risk_score'].mean():.4f}")
    print(f"Maximum risk score: {road_risk_gdf['risk_score'].max():.4f}")
    print(f"Minimum risk score: {road_risk_gdf['risk_score'].min():.4f}")
    # Calculate risk score percentiles for classification
    risk_scores = road_risk_gdf['risk_score']
    percentiles = np.percentile(risk_scores, [20, 40, 60, 80])
    
    def assign_risk_category(score):
        if score <= percentiles[0]:
            return 'Very Low'
        elif score <= percentiles[1]:
            return 'Low'
        elif score <= percentiles[2]:
            return 'Medium' 
        elif score <= percentiles[3]:
            return 'High'
        else:
            return 'Very High'
    
    # Apply the categorization
    road_risk_gdf['risk_category'] = road_risk_gdf['risk_score'].apply(assign_risk_category)

    print("\nRisk Categories Distribution:")
    print(road_risk_gdf['risk_category'].value_counts().sort_index())

def main():
    # Path to your shapefiles

    # A subset of whole area
    # osm_path = r'./Datasets/Subset/OSM.geojson'
    # accident_path = r'./Datasets/Subset/Accident.geojson'

    osm_path = r'./Datasets/Subset/calgary_edges.shp'
    accident_path = r'./Datasets/VectorLayers/accident_weather_clean.shp'

    # Read accident data
    print("Reading accident data...")
    gdf = read_accident_data(accident_path)
    gdf.to_crs('epsg:32611', inplace=True)
    if gdf is None:
        return
    
    # Print available columns to help debug
    print("\nAvailable columns in the dataset:")
    print(gdf.columns.tolist())
    
    # Prepare coordinates for clustering
    print("\nPreparing coordinates for clustering...")
    coords = prepare_coordinates(gdf)
    
    # Perform clustering
    print("Performing clustering...")
    # labels = perform_clustering(coords, eps=50, min_samples=5)
    
    # Visualize clusters
    print("Visualizing clusters...")
    # visualize_clusters(gdf, labels)
    
    # Analyze clusters
    print("Analyzing clusters...")
    # analyze_clusters(labels)
    
    # Perform hotspot analysis
    print("\nPerforming hotspot analysis using spatial statistics...")
    gdf = perform_hotspot_analysis(gdf, distance_threshold=200, p_value_threshold=0.30, z_score_threshold=-0.6)
    
    # Visualize hotspots
    print("Visualizing hotspots...")
    visualize_hotspots(gdf)
    
    # Analyze hotspots
    print("Analyzing hotspots...")
    analyze_hotspots(gdf)
    
    # Save hotspot results
    gdf.to_file(r'./Datasets/Subset/Accident_hotspots.shp', driver='ESRI Shapefile')
    
    # Read road network
    print("\nReading road network...")
    road_gdf = gpd.read_file(osm_path)
    road_gdf.to_crs('epsg:32611', inplace=True)
    road_gdf = explode_multilinestring(road_gdf)
    # Calculate risk layer
    print("Calculating risk layer...")
    # road_risk_gdf = calculate_road_risk(road_gdf, gdf, max_distance=500, power=2)
    road_gdf["risk_score"] = road_gdf["geometry"].apply(
        lambda geom: calculate_road_risk(geom, gdf, max_distance=200, power=2)
    )
    # Visualize risk layer
    print("Visualizing risk layer...")
    # visualize_risk_layer(road_gdf)
    
    # Analyze risk layer
    print("Analyzing risk layer...")
    analyze_risk_layer(road_gdf)
    
    # Save risk layer
    road_gdf.to_file(r'./Datasets/Subset/road_risk_layer_categorized.shp', driver='ESRI Shapefile')
    
    print("\nProcessing complete! Check 'accident_clusters.png', 'accident_hotspots.png', and 'road_risk_layer.png' for visualizations.")

if __name__ == "__main__":
    main()