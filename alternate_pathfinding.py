# alternate_pathfinding.py (using Yen's algorithm with MultiDiGraph fix)
import osmnx as ox
import networkx as nx
import pandas as pd
from networkx.algorithms.simple_paths import shortest_simple_paths


def find_alternate_paths(G, edges, start_lat, start_lon, end_lat, end_lon, k=3):
    """
    Find up to k alternate paths between two points in the graph using travel time as the weight,
    using Yen's algorithm (shortest_simple_paths).

    Parameters:
    - G: The OSMnx graph (MultiDiGraph) with travel_time attributes.
    - edges: GeoDataFrame of edges (for geometry and properties).
    - start_lat, start_lon: Latitude and longitude of the start point.
    - end_lat, end_lon: Latitude and longitude of the end point.
    - k: Number of alternate paths to find (default = 3)

    Returns:
    - A list of routes, each containing a GeoJSON representation, distance, and travel time.
    """
    print("Starting pathfinding with Yen's algorithm...")

    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
        print(f"Nearest nodes: start={start_node}, end={end_node}")
    except Exception as e:
        raise ValueError(f"Error finding nearest nodes: {str(e)}")

    if start_node not in G.nodes or end_node not in G.nodes:
        raise ValueError("One or both points are outside the Calgary road network")

    print("Converting MultiDiGraph to DiGraph...")
    H = nx.DiGraph()
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'travel_time' not in data:
            continue
        # Always keep the edge with the minimum travel time
        if H.has_edge(u, v):
            if data['travel_time'] < H[u][v].get('travel_time', float('inf')):
                for attr in data:
                    H[u][v][attr] = data[attr]
        else:
            H.add_edge(u, v, **data)

    try:
        path_generator = shortest_simple_paths(H, start_node, end_node, weight='travel_time')
        paths = []
        for i, path in enumerate(path_generator):
            if i >= k:
                break
            paths.append(path)
    except nx.NetworkXNoPath as e:
        raise nx.NetworkXNoPath(f"No path found: {str(e)}")

    routes = []
    for path_idx, path in enumerate(paths):
        features = []
        total_distance = 0
        total_time = 0

        for u, v in zip(path[:-1], path[1:]):
            try:
                edge_data = G.get_edge_data(u, v)
                if not edge_data:
                    continue
                edge_data = edge_data[0]  # take the first edge only
                edge_key = (u, v, 0)
                edge_gdf = edges.loc[edge_key]
                geom = edge_gdf.geometry
                road_name = edge_gdf.get('name', None)

                if isinstance(road_name, list):
                    road_name = road_name[0] if road_name else 'Unnamed Road'
                if pd.isna(road_name):
                    road_name = edge_gdf.get('ref', None)
                if pd.isna(road_name):
                    road_name = edge_gdf.get('highway', 'Unnamed Road').capitalize()

                total_distance += edge_data['length']
                total_time += edge_data['travel_time']

                features.append({
                    "type": "Feature",
                    "geometry": geom.__geo_interface__,
                    "properties": {
                        "osmid": edge_gdf['osmid'],
                        "name": road_name,
                        "maxspeed": edge_data.get('maxspeed', 'N/A'),
                        "length": edge_data['length'],
                        "travel_time": edge_data['travel_time']
                    }
                })
            except Exception as e:
                print(f"Error processing edge ({u}, {v}): {str(e)}")
                continue

        routes.append({
            "route_id": path_idx + 1,
            "geojson": {"type": "FeatureCollection", "features": features},
            "distance_km": round(total_distance / 1000, 2),
            "time_min": round(total_time / 60, 2)
        })

    print(f"Processed {len(routes)} routes")
    return routes
