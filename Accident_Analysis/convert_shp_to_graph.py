import geopandas as gpd
from shapely.geometry import LineString
import numpy as np
import pickle
import networkx as nx


node_id_map = {}
current_node_id = 0

def add_road_to_graph(row):
    global current_node_id
    line = row['geometry']
    if isinstance(line, LineString):
        coords = list(line.coords)
        prev_node_id = None
        for i, coord in enumerate(coords):
            coord = tuple(coord)
            if coord not in node_id_map:
                node_id_map[coord] = current_node_id
                G.add_node(current_node_id, pos=coord)
                current_node_id += 1
            current_node_id_local = node_id_map[coord]
            if prev_node_id is not None:
                segment_length = np.sqrt(
                    (coords[i][0] - coords[i-1][0])**2 +
                    (coords[i][1] - coords[i-1][1])**2
                )
                # G.add_edge(prev_node_id, current_node_id_local,
                #         length=segment_length, road_id=row.get('FID', None),
                #         highway=row.get('highway', None), geometry=row.geometry)
                G.add_edge(prev_node_id, current_node_id_local,
                           name=row['name'],
                           risk_score=row["risk_score"],
                           risk_category=row["risk_categ"],
                           length=segment_length,
                           road_id=row.get('FID', None),
                           maxspeed=row.get('maxspeed', None),
                           oneway=row.get('oneway', None),
                           geometry=row.geometry)
            prev_node_id = current_node_id_local


# Step 1: Load and prepare the shapefile
routes_gdf = gpd.read_file(r'./Datasets/Subset/road_risk_layer_categorized.shp').set_crs("EPSG:32611")

# routes_gdf = routes_gdf.to_crs("EPSG:4326")

# Step 2: Build a directed graph from the shapefile
G = nx.DiGraph()
G.graph['crs'] = 'epsg:32611'
routes_gdf.apply(add_road_to_graph, axis=1)

# Save the road network graph to pickle format
with open("./Datasets/Subset/road_network.pkl", "wb") as f:
    pickle.dump(G, f)
