import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer
from datetime import datetime
import folium
from find_path import find_nearest_node, dijkstra_path, adjust_risk_score
import pickle
from matplotlib.colors import Normalize

routes_gdf = gpd.read_file(r'./Datasets/Subset/road_risk_layer_categorized.shp').set_crs("EPSG:32611")
G = pickle.load(open("./Datasets/Subset/road_network.pkl", "rb"))

# Example usage
start_coords = (-114.0962, 51.0289)  # Downtown Calgary
end_coords = (-114.08083, 51.06874)    # West Calgary

# Convert coordinates from WGS84 to UTM Zone 11N
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)
start_coords_utm = transformer.transform(start_coords[0], start_coords[1])
end_coords_utm = transformer.transform(end_coords[0], end_coords[1])

start_node = find_nearest_node(G, start_coords_utm)
end_node = find_nearest_node(G, end_coords_utm)

# Test with current time
current_time = datetime(2025, 3, 26, 17, 0)  # Example: March 26, 2025, 5 PM
# path = astar_path(G, start_node, end_node, current_time, alpha=1.0, beta=0.0)
path = dijkstra_path(G, start_node, end_node, current_time, alpha=1.0, beta=1.0)


# Extract and visualize the route
if path:
    route_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
    route_gdf = gpd.GeoDataFrame(
        [G[u][v] for u, v in route_edges],
        geometry=[G[u][v]["geometry"] for u, v in route_edges],
        crs=routes_gdf.crs
    )
    
    # route_gdf.plot()
    # plt.show()
    # Calculate total distance and risk
    total_length = sum(G[u][v]["length"] for u, v in route_edges)
    total_risk = sum(adjust_risk_score(G[u][v]["risk_score"], current_time)
                    for u, v in route_edges)
    
    # Count risk categories along the path
    risk_categories = [G[u][v]["risk_category"] for u, v in route_edges]
    risk_category_counts = {}
    for category in risk_categories:
        risk_category_counts[category] = risk_category_counts.get(category, 0) + 1
    
    print(f"Path found: {len(path)} nodes")
    print(f"Total distance: {total_length:.2f} meters") 
    print(f"Total adjusted risk: {total_risk:.2f}")
    print(f"Risk category counts:")
    for category, count in risk_category_counts.items():
        print(f"  {category}: {count}")
else:
    print("No path found.")

# Create a folium map
m = folium.Map(location=[51.0447, -114.0719], zoom_start=12)
routes_gdf_4326 = routes_gdf.to_crs('epsg:4326')

# Define color map for risk categories
risk_category_colors = {
    'Very Low': '#2ecc71',     # Green
    'Low': '#f1c40f',  # Yellow
    'Medium': '#e74c3c',     # Red
    'High': '#c0392b',
    'Very High': '#8e44ad'
}

# Add legend for risk categories
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 50px; 
            border:2px solid grey; z-index:1000;
            background-color:white;
            padding: 10px;
            ">
<p><b>Risk Categories</b></p>
'''
for category, color in risk_category_colors.items():
    legend_html += f'<p><i style="background: {color}; width: 20px; height: 20px; display: inline-block;"></i> {category}</p>'
legend_html += '</div>'

m.get_root().html.add_child(folium.Element(legend_html))
norm = Normalize(vmin=routes_gdf_4326["risk_score"].min(), vmax=routes_gdf_4326["risk_score"].max())

# Add road segments to the map
for _, row in routes_gdf_4326.iterrows():
    risk = row["risk_score"]

    folium.PolyLine(
        locations=[(lat, lon) for lon, lat in row["geometry"].coords],
        color=risk_category_colors[row["risk_categ"]],
        weight=4,
        opacity=0.7,
    ).add_to(m)

route_gdf.to_crs('epsg:4326', inplace=True)
# Add the route path to the map in a different color
if path:
    # print(len(route_gdf))
    # Convert route coordinates to lat/lon for folium
    route_coords = []
    for _, row in route_gdf.iterrows():
        route_coords.extend([(lat, lon) for lon, lat in row["geometry"].coords])

        # Add route line
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in row["geometry"].coords],
            color='red',
            weight=5,
            opacity=0.9,
        ).add_to(m)

    # Add start and end markers
    start_coords = route_coords[0]
    end_coords = route_coords[-1]

    folium.Marker(
        location=start_coords,
        popup='Start',
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

    folium.Marker(
        location=end_coords,
        popup='End', 
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

# Save or display map
m.save("./Datasets/Subset/risk_map_hotspot.html")

# Save the graph (optional)
# nx.write_graphml(G, "calgary_risk_graph.graphml")